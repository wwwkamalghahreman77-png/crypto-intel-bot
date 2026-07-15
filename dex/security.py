import requests

BASE_URL = "https://api.gopluslabs.io/api/v1/token_security"

CHAIN_ID_MAP = {
    "ethereum": "1",
    "bsc": "56",
    "base": "8453",
    "arbitrum": "42161",
}


class SecurityChecker:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def check_token(self, network: str, token_address: str) -> dict:
        chain_id = CHAIN_ID_MAP.get(network)
        if not chain_id:
            return {
                "supported": False,
                "reason": f"شبکه '{network}' توسط بررسی امنیتی GoPlus در این نسخه پشتیبانی نمی‌شود",
            }

        url = f"{BASE_URL}/{chain_id}"
        try:
            resp = requests.get(url, params={"contract_addresses": token_address}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            result = (data.get("result") or {}).get(token_address.lower(), {})
            if not result:
                return {"supported": True, "found": False}
            return {"supported": True, "found": True, **result}
        except requests.RequestException as e:
            print(f"[GoPlus] خطا در بررسی امنیت {token_address}: {e}")
            return {"supported": True, "found": False, "error": str(e)}

    @staticmethod
    def score_security(security_data: dict):
        if not security_data.get("supported") or not security_data.get("found"):
            return 0, [], ["اطلاعات امنیتی در دسترس نیست - این توکن باید Reject شود"]

        reasons = []
        risks = []
        score = 100

        def is_true(key):
            return str(security_data.get(key, "0")) == "1"

        if is_true("is_honeypot"):
            score -= 100
            risks.append("Honeypot تشخیص داده شد ⚠️")
        else:
            reasons.append("Honeypot شناسایی نشد ✅")

        if is_true("is_mintable"):
            score -= 30
            risks.append("قابلیت Mint نامحدود فعال است ⚠️")
        else:
            reasons.append("Mint Function غیرفعال ✅")

        if is_true("can_take_back_ownership") or is_true("hidden_owner"):
            score -= 25
            risks.append("مالکیت قرارداد مشکوک/پنهان است ⚠️")

        if is_true("is_freezable") if "is_freezable" in security_data else False:
            score -= 20
            risks.append("قابلیت Freeze دارایی کاربران وجود دارد ⚠️")

        buy_tax = float(security_data.get("buy_tax") or 0)
        sell_tax = float(security_data.get("sell_tax") or 0)
        if buy_tax > 10 or sell_tax > 10:
            score -= 20
            risks.append(f"مالیات معامله بالا (خرید {buy_tax}% / فروش {sell_tax}%) ⚠️")
        else:
            reasons.append("مالیات خرید/فروش معقول ✅")

        holder_count = int(security_data.get("holder_count") or 0)
        if holder_count and holder_count < 50:
            score -= 15
            risks.append(f"تعداد هولدرها بسیار کم است ({holder_count}) ⚠️")

        lp_holders = security_data.get("lp_holders") or []
        if isinstance(lp_holders, list) and len(lp_holders) == 1:
            score -= 15
            risks.append("نقدینگی فقط در دست یک کیف‌پول است (ریسک Rug Pull) ⚠️")

        score = max(0, min(100, score))
        return score, reasons, risks
