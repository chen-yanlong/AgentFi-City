from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Backend
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Wallets
    planner_private_key: str = ""
    researcher_private_key: str = ""
    critic_private_key: str = ""
    executor_private_key: str = ""
    task_creator_private_key: str = ""

    # Chain
    rpc_url: str = "http://localhost:8545"
    chain_id: int = 0
    task_market_contract_address: str = ""
    contract_network: str = "localhost"  # which contracts/deployments/<name>.json to load
    use_real_contract: bool = False  # toggle: real onchain calls vs fake tx hashes

    # Uniswap
    uniswap_api_key: str = ""
    uniswap_api_base_url: str = ""

    # 0G
    og_storage_rpc: str = ""
    og_storage_private_key: str = ""
    og_compute_api_key: str = ""

    # AXL
    axl_planner_url: str = "http://localhost:7001"
    axl_researcher_url: str = "http://localhost:7002"
    axl_critic_url: str = "http://localhost:7003"
    axl_executor_url: str = "http://localhost:7004"

    # LLM
    openai_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
