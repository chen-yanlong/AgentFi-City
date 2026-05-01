"""Uniswap Trading API integration.

Two public functions:
- `get_quote(...)` — calls POST /quote, returns the parsed quote + permitData.
- `execute_swap(...)` — signs Permit2 EIP-712 if needed, calls POST /swap to
  build the transaction, signs it with the agent wallet, and broadcasts via web3.

Either function raises `UniswapUnavailable` on any non-success path so the
orchestrator can fall back to fake quote/tx-hash mode when API key, RPC, or
wallet pre-funding aren't configured.

Required prereqs for real-mode execution:
1. UNISWAP_API_KEY set (register at developers.uniswap.org/dashboard)
2. UNISWAP_TOKEN_IN, UNISWAP_TOKEN_OUT set to addresses on the target chain
3. Executor wallet funded with the input token + a tiny amount of native gas
4. Permit2 contract approved by the wallet to spend the input token (one-time)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from backend.config import get_settings

logger = logging.getLogger(__name__)


class UniswapUnavailable(Exception):
    """Raised when real-mode swap can't proceed — orchestrator should fall back."""


@dataclass
class Quote:
    quote_payload: dict[str, Any]
    permit_data: Optional[dict[str, Any]]
    routing: Optional[str]
    raw: dict[str, Any]


@dataclass
class SwapResult:
    tx_hash: str
    explorer_url: str
    chain_id: int


def _explorer_base(chain_id: int) -> str:
    return {
        84532: "https://sepolia.basescan.org",
        8453: "https://basescan.org",
        11155111: "https://sepolia.etherscan.io",
    }.get(chain_id, "")


async def get_quote(
    swapper_address: str,
    token_in: Optional[str] = None,
    token_out: Optional[str] = None,
    amount_wei: Optional[str] = None,
) -> Quote:
    settings = get_settings()
    if not settings.uniswap_api_key:
        raise UniswapUnavailable("UNISWAP_API_KEY not set")

    token_in = token_in or settings.uniswap_token_in
    token_out = token_out or settings.uniswap_token_out
    amount_wei = amount_wei or settings.uniswap_swap_amount_wei
    if not token_in or not token_out:
        raise UniswapUnavailable("Token addresses not configured")

    payload = {
        "tokenIn": token_in,
        "tokenOut": token_out,
        "tokenInChainId": settings.uniswap_chain_id,
        "tokenOutChainId": settings.uniswap_chain_id,
        "type": "EXACT_INPUT",
        "amount": amount_wei,
        "swapper": swapper_address,
        "slippageTolerance": settings.uniswap_slippage_tolerance,
    }
    headers = {
        "x-api-key": settings.uniswap_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{settings.uniswap_api_base_url}/quote",
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError as e:
        raise UniswapUnavailable(f"quote request failed: {e}") from e

    if r.status_code != 200:
        raise UniswapUnavailable(f"quote status {r.status_code}: {r.text[:300]}")

    data = r.json()
    return Quote(
        quote_payload=data.get("quote", {}),
        permit_data=data.get("permitData"),
        routing=data.get("routing"),
        raw=data,
    )


def _sign_permit(permit_data: dict[str, Any], private_key: str) -> str:
    """EIP-712 sign Uniswap's permitData. Returns 0x-prefixed signature."""
    signable = encode_typed_data(
        domain_data=permit_data["domain"],
        message_types=permit_data["types"],
        message_data=permit_data["values"],
    )
    signed = Account.sign_message(signable, private_key=private_key)
    return signed.signature.hex()


async def execute_swap(quote: Quote, private_key: str) -> SwapResult:
    settings = get_settings()
    if not settings.uniswap_api_key:
        raise UniswapUnavailable("UNISWAP_API_KEY not set")

    headers = {
        "x-api-key": settings.uniswap_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body: dict[str, Any] = {"quote": quote.quote_payload}
    if quote.permit_data is not None:
        try:
            body["signature"] = _sign_permit(quote.permit_data, private_key)
            body["permitData"] = quote.permit_data
        except Exception as e:
            raise UniswapUnavailable(f"permit signing failed: {e}") from e

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{settings.uniswap_api_base_url}/swap",
                headers=headers,
                json=body,
            )
    except httpx.HTTPError as e:
        raise UniswapUnavailable(f"swap request failed: {e}") from e

    if r.status_code != 200:
        raise UniswapUnavailable(f"swap status {r.status_code}: {r.text[:300]}")

    swap_data = r.json().get("swap")
    if not swap_data or not swap_data.get("data"):
        raise UniswapUnavailable("swap response missing transaction data")

    # Sign and broadcast
    w3 = Web3(Web3.HTTPProvider(settings.uniswap_rpc_url))
    account = Account.from_key(private_key)

    tx = {
        "to": swap_data["to"],
        "from": account.address,
        "data": swap_data["data"],
        "value": int(swap_data.get("value", "0"), 0)
        if isinstance(swap_data.get("value"), str)
        else int(swap_data.get("value", 0)),
        "chainId": int(swap_data.get("chainId", settings.uniswap_chain_id)),
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": int(swap_data.get("gasLimit", 500_000), 0)
        if isinstance(swap_data.get("gasLimit"), str)
        else int(swap_data.get("gasLimit", 500_000)),
    }
    if "maxFeePerGas" in swap_data:
        tx["maxFeePerGas"] = int(swap_data["maxFeePerGas"], 0)
        tx["maxPriorityFeePerGas"] = int(swap_data["maxPriorityFeePerGas"], 0)
    else:
        tx["gasPrice"] = w3.eth.gas_price

    try:
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except Exception as e:
        raise UniswapUnavailable(f"broadcast failed: {e}") from e

    chain_id = settings.uniswap_chain_id
    base = _explorer_base(chain_id)
    return SwapResult(
        tx_hash=tx_hash.hex(),
        explorer_url=f"{base}/tx/{tx_hash.hex()}" if base else "",
        chain_id=chain_id,
    )
