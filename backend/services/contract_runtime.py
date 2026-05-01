"""Runtime helpers for resolving the TaskMarket contract service and agent wallets.

When USE_REAL_CONTRACT is true and a deployment file exists, returns a live
TaskMarketService bound to the configured RPC. Otherwise returns None and the
orchestrator falls back to fake tx hashes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from eth_account import Account

from backend.config import get_settings
from backend.services.contract_service import TaskMarketService, load_deployment


# Hardhat deterministic test accounts — used only when env keys are unset and
# we're talking to a local node. Never use these on a real network.
_HARDHAT_KEYS = {
    "task_creator": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "planner": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "researcher": "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    "critic": "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    "executor": "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
}


@dataclass
class AgentWallet:
    private_key: str
    address: str


@dataclass
class ContractRuntime:
    service: TaskMarketService
    task_creator: AgentWallet
    planner: AgentWallet
    researcher: AgentWallet
    critic: AgentWallet
    executor: AgentWallet


def _wallet(env_key: str, fallback_role: str) -> AgentWallet:
    pk = env_key or _HARDHAT_KEYS[fallback_role]
    return AgentWallet(private_key=pk, address=Account.from_key(pk).address)


def get_contract_runtime() -> Optional[ContractRuntime]:
    """Returns a ContractRuntime if real-contract mode is enabled and ready,
    otherwise None (orchestrator should fall back to fake tx hashes)."""
    settings = get_settings()
    if not settings.use_real_contract:
        return None

    try:
        deployment = load_deployment(settings.contract_network)
    except FileNotFoundError:
        return None

    service = TaskMarketService(settings.rpc_url, deployment)

    return ContractRuntime(
        service=service,
        task_creator=_wallet(settings.task_creator_private_key, "task_creator"),
        planner=_wallet(settings.planner_private_key, "planner"),
        researcher=_wallet(settings.researcher_private_key, "researcher"),
        critic=_wallet(settings.critic_private_key, "critic"),
        executor=_wallet(settings.executor_private_key, "executor"),
    )
