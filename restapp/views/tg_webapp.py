import hashlib
import hmac
import urllib.parse
from typing import Dict, Tuple


def _parse_init_data(init_data: str) -> Dict[str, str]:
    decoded = urllib.parse.unquote(init_data)
    pairs = urllib.parse.parse_qsl(decoded, keep_blank_values=True)
    return dict(pairs)


def verify_webapp_init_data(init_data: str, bot_token: str) -> Tuple[bool, Dict[str, str]]:
    """
    Telegram WebApp initData verify (official algorithm):
      secret_key = HMAC_SHA256("WebAppData", bot_token)
      data_check_string = "\n".join(sorted(k=v)) (hashsiz)
      calc_hash = HMAC_SHA256(secret_key, data_check_string)
    """
    data = _parse_init_data(init_data)
    recv_hash = data.pop("hash", "")

    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    calc_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(calc_hash, recv_hash), data
