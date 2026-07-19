from dataclasses import dataclass, asdict



@dataclass
class DexDiscovery:

    token: str
    network: str
    date_found: str
    security_score: float
    dex_score: float
    price_found: float
    liquidity: float
    volume: float
    status: str


    def to_dict(self):

        return asdict(self)




@dataclass
class CryptoReport:

    token: str
    date_found: str
    total_score: float
    security: float
    fundamental: float
    news: float
    technical: float
    community: float
    status: str


    def to_dict(self):

        return asdict(self)




@dataclass
class PerformanceTracking:

    token: str
    initial_price: float
    price_7d: float = None
    price_30d: float = None
    result: str = "pending"


    def to_dict(self):

        return asdict(self)





@dataclass
class ActiveSignal:

    symbol: str

    signal_type: str


    entry_price: float


    tp1: float = None
    tp2: float = None
    tp3: float = None
    tp4: float = None


    stop_loss: float = None


    telegram_chat_id: str = ""

    telegram_message_id: int = 0


    status: str = "active"


    hit_tp1: bool = False
    hit_tp2: bool = False
    hit_tp3: bool = False
    hit_tp4: bool = False

    hit_stop: bool = False


    date_found: str = ""



    def to_dict(self):

        return asdict(self)





@dataclass
class ClosedTrade:

    symbol: str
    signal_type: str

    entry_price: float
    exit_price: float

    stop_loss: float = None
    highest_tp_hit: str = None

    result_pct: float = 0
    risk_reward: float = None

    close_reason: str = ""

    date_opened: str = ""
    date_closed: str = ""
    duration_hours: float = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class TelegramMessageLog:

    message_type: str
    symbol: str

    telegram_chat_id: str = ""
    telegram_message_id: int = 0
    reply_to_message_id: int = None

    content_preview: str = ""

    date_sent: str = ""

    def to_dict(self):
        return asdict(self)
