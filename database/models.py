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
