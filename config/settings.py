import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get_list(env_name: str, default: str):
    raw = os.getenv(env_name, default)
    return [
        item.strip()
        for item in raw.split(",")
        if item.strip()
    ]


@dataclass
class Settings:

    telegram_bot_token: str = os.getenv(
        "TELEGRAM_BOT_TOKEN",
        ""
    )

    telegram_chat_id: str = os.getenv(
        "TELEGRAM_CHAT_ID",
        ""
    )

    telegram_channel_id: str = os.getenv(
        "TELEGRAM_CHANNEL_ID",
        ""
    )

    supabase_url: str = os.getenv(
        "SUPABASE_URL",
        ""
    )

    supabase_key: str = os.getenv(
        "SUPABASE_KEY",
        ""
    )

    dex_networks: list = field(
        default_factory=lambda: _get_list(
            "DEX_NETWORKS",
            "ethereum,bsc,solana,base,arbitrum"
        )
    )

    min_liquidity_usd: float = float(
        os.getenv(
            "MIN_LIQUIDITY_USD",
            "10000"
        )
    )

    min_volume_24h_usd: float = float(
        os.getenv(
            "MIN_VOLUME_24H_USD",
            "5000"
        )
    )

    @property
    def use_supabase(self) -> bool:

        return bool(
            self.supabase_url
            and self.supabase_key
        )

    @property
    def telegram_enabled(self) -> bool:

        return bool(
            self.telegram_bot_token
            and (
                self.telegram_chat_id
                or
                self.telegram_channel_id
            )
        )


settings = Settings()
