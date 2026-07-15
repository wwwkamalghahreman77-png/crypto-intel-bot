import time
import requests

BASE_URL = "https://api.dexscreener.com/latest/dex"
SEARCH_URL = f"{BASE_URL}/search"


class DexscreenerClient:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def search_pairs(self, query: str):
        try:
            resp = requests.get(SEARCH_URL, params={"q": query}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("pairs", []) or []
        except requests.RequestException as e:
            print(f"[Dexscreener] خطا در دریافت داده برای '{query}': {e}")
            return []

    def get_pairs_for_network(self, network: str):
        return self.search_pairs(network)

    def get_pair_details(self, chain_id: str, pair_address: str):
        url = f"{BASE_URL}/pairs/{chain_id}/{pair_address}"
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            pairs = data.get("pairs") or []
            return pairs[0] if pairs else None
        except requests.RequestException as e:
            print(f"[Dexscreener] خطا در دریافت جزئیات جفت: {e}")
            return None

    @staticmethod
    def extract_pair_info(pair: dict) -> dict:
        created_at_ms = pair.get("pairCreatedAt", 0)
        age_hours = None
        if created_at_ms:
            age_hours = round((time.time() * 1000 - created_at_ms) / (1000 * 3600), 1)

        return {
            "token_symbol": pair.get("baseToken", {}).get("symbol"),
            "token_address": pair.get("baseToken", {}).get("address"),
            "network": pair.get("chainId"),
            "pair_address": pair.get("pairAddress"),
            "price_usd": float(pair.get("priceUsd") or 0),
            "liquidity_usd": float((pair.get("liquidity") or {}).get("usd") or 0),
            "volume_24h_usd": float((pair.get("volume") or {}).get("h24") or 0),
            "buys_24h": (pair.get("txns") or {}).get("h24", {}).get("buys", 0),
            "sells_24h": (pair.get("txns") or {}).get("h24", {}).get("sells", 0),
            "fdv": float(pair.get("fdv") or 0),
            "age_hours": age_hours,
            "url": pair.get("url"),
        }
