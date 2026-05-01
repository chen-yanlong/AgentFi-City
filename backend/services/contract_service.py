"""Smart contract interaction service for TaskMarket.

Reads the deployment record produced by `contracts/scripts/deploy.ts` and
provides typed methods for createTask / joinTask / completeTask / distributeReward.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from eth_account import Account
from web3 import Web3
from web3.types import TxReceipt


REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENTS_DIR = REPO_ROOT / "contracts" / "deployments"


@dataclass
class TaskMarketDeployment:
    network: str
    chain_id: int
    address: str
    abi: list[dict[str, Any]]
    block_number: Optional[int] = None
    tx_hash: Optional[str] = None


def load_deployment(network: str = "localhost") -> TaskMarketDeployment:
    path = DEPLOYMENTS_DIR / f"{network}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No deployment record at {path}. Run `npm run deploy:local` in contracts/."
        )
    data = json.loads(path.read_text())
    return TaskMarketDeployment(
        network=data["network"],
        chain_id=data["chainId"],
        address=data["address"],
        abi=data["abi"],
        block_number=data.get("blockNumber"),
        tx_hash=data.get("txHash"),
    )


class TaskMarketService:
    """Wraps TaskMarket contract calls with typed Python methods."""

    def __init__(self, rpc_url: str, deployment: TaskMarketDeployment):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC at {rpc_url}")
        self.deployment = deployment
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(deployment.address),
            abi=deployment.abi,
        )

    def _send(self, fn, private_key: str, value_wei: int = 0) -> TxReceipt:
        account = Account.from_key(private_key)
        nonce = self.w3.eth.get_transaction_count(account.address)
        tx = fn.build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "value": value_wei,
                "chainId": self.deployment.chain_id,
            }
        )
        signed = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def create_task(
        self, creator_private_key: str, description: str, reward_wei: int
    ) -> tuple[str, int]:
        """Returns (tx_hash, task_id)."""
        receipt = self._send(
            self.contract.functions.createTask(description),
            creator_private_key,
            value_wei=reward_wei,
        )
        # Parse TaskCreated event for taskId
        events = self.contract.events.TaskCreated().process_receipt(receipt)
        if not events:
            raise RuntimeError("TaskCreated event not found in receipt")
        task_id = events[0]["args"]["taskId"]
        return receipt["transactionHash"].hex(), task_id

    def join_task(self, agent_private_key: str, task_id: int) -> str:
        receipt = self._send(
            self.contract.functions.joinTask(task_id), agent_private_key
        )
        return receipt["transactionHash"].hex()

    def complete_task(self, creator_private_key: str, task_id: int) -> str:
        receipt = self._send(
            self.contract.functions.completeTask(task_id), creator_private_key
        )
        return receipt["transactionHash"].hex()

    def distribute_reward(self, creator_private_key: str, task_id: int) -> tuple[str, int]:
        """Returns (tx_hash, reward_per_agent_wei)."""
        receipt = self._send(
            self.contract.functions.distributeReward(task_id), creator_private_key
        )
        events = self.contract.events.RewardDistributed().process_receipt(receipt)
        per_agent = events[0]["args"]["rewardPerAgent"] if events else 0
        return receipt["transactionHash"].hex(), per_agent

    def get_task(self, task_id: int) -> dict[str, Any]:
        task = self.contract.functions.tasks(task_id).call()
        participants = self.contract.functions.getParticipants(task_id).call()
        # Tuple order matches Solidity struct: id, creator, description, reward, status
        return {
            "id": task[0],
            "creator": task[1],
            "description": task[2],
            "reward": task[3],
            "status": task[4],
            "participants": participants,
        }
