from config.settings import settings
from database.db import db, now_str
from database.models import DexDiscovery
from dex.dexscreener import DexscreenerClient
from dex.security import SecurityChecker

dex_client = DexscreenerClient()
security_checker = SecurityChecker()


def calculate_dex_score(pair_info: dict) -> float:
    score = 0

    liquidity = pair_info["liquidity_usd"]
    volume = pair_info["volume_24h_usd"]
    buys = pair_info["buys_24h"] or 0
    sells = pair_info["sells_24h"] or 1

    score += min(30, liquidity / 1000)
    score += min(30, volume / 1000)

    buy_sell_ratio = buys / sells
    score += min(20, buy_sell_ratio * 10)

    age = pair_info.get("age_hours") or 0
    if 2 <= age <= 240:
        score += 20
    elif age > 240:
        score += 10

    return round(min(100, score), 1)


def passes_initial_filters(pair_info: dict) -> bool:
    if pair_info["liquidity_usd"] < settings.min_liquidity_usd:
        return False
    if pair_info["volume_24h_usd"] < settings.min_volume_24h_usd:
        return False
    if not pair_info["token_address"]:
        return False
    return True


def scan_network(network: str):
    discoveries = []
    raw_pairs = dex_client.get_pairs_for_network(network)

    for raw_pair in raw_pairs:
        pair_info = dex_client.extract_pair_info(raw_pair)

        if pair_info["network"] != network:
            continue

        if not passes_initial_filters(pair_info):
            continue

        if db.token_exists("dex_discoveries", pair_info["token_symbol"]):
            continue

        security_data = security_checker.check_token(network, pair_info["token_address"])
        sec_score, sec_reasons, sec_risks = SecurityChecker.score_security(security_data)

        if sec_score < 50:
            continue

        dex_score = calculate_dex_score(pair_info)

        record = DexDiscovery(
            token=pair_info["token_symbol"],
            network=network,
            date_found=now_str(),
            security_score=sec_score,
            dex_score=dex_score,
            price_found=pair_info["price_usd"],
            liquidity=pair_info["liquidity_usd"],
            volume=pair_info["volume_24h_usd"],
            status="WATCHLIST",
        )

        db.insert("dex_discoveries", record.to_dict())

        discoveries.append({
            "record": record,
            "reasons": sec_reasons,
            "risks": sec_risks,
            "pair_info": pair_info,
        })

    return discoveries


def run_full_scan():
    all_discoveries = []
    for network in settings.dex_networks:
        print(f"[GemScanner] در حال اسکن شبکه: {network}")
        found = scan_network(network)
        all_discoveries.extend(found)
    return all_discoveries
