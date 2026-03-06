import json
import platform
import re
import time
from collections.abc import Callable

import httpx
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

from spygraph.utils import get_fingerprint


def api_security_headers() -> dict[str, str]:
    headers = {
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "*=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "X-XSS-Protection": "0",
    }
    headers.update(get_fingerprint())
    return headers


def parse_user_agent(ua: str | None) -> dict:
    if not ua:
        return {
            "raw_user_agent": "",
            "browser": None,
            "browser_version": None,
            "os": None,
            "os_version": None,
            "device": None,
            "is_bot": False,
            "is_mobile": False,
        }

    result = {
        "raw_user_agent": ua,
        "browser": None,
        "browser_version": None,
        "os": None,
        "os_version": None,
        "device": None,
        "is_bot": False,
        "is_mobile": False,
    }

    browser_patterns = {
        "Chrome": r"Chrome/([0-9\.]+)",
        "Firefox": r"Firefox/([0-9\.]+)",
        "Safari": r"Version/([0-9\.]+).*Safari",
        "Edge": r"Edg/([0-9\.]+)",
        "Opera": r"OPR/([0-9\.]+)",
        "IE": r"MSIE ([0-9\.]+)|Trident.*rv:([0-9\.]+)",
    }

    for browser, pattern in browser_patterns.items():
        match = re.search(pattern, ua)
        if match:
            version = match.group(1) if match.group(1) else (match.group(2) if len(match.groups()) > 1 else None)
            result["browser"] = browser
            result["browser_version"] = version
            break

    os_patterns = {
        "Windows": {
            "pattern": r"Windows NT ([0-9\.]+)",
            "versions": {
                "10.0": "Windows 10/11",
                "6.3": "Windows 8.1",
                "6.2": "Windows 8",
                "6.1": "Windows 7",
                "6.0": "Windows Vista",
            },
        },
        "macOS": {"pattern": r"Mac OS X ([0-9_\.]+)", "process": lambda v: f"macOS {v.replace('_', '.')}"},
        "Linux": {"pattern": r"Linux", "versions": {"": "Linux"}},
        "Android": {"pattern": r"Android ([0-9\.]+)", "process": lambda v: f"Android {v}"},
        "iOS": {"pattern": r"iPhone|iPad|iPod", "versions": {"": "iOS"}},
    }

    for os_name, os_config in os_patterns.items():
        match = re.search(os_config["pattern"], ua)
        if match:
            result["os"] = os_name

            if "process" in os_config:
                version_str = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
                result["os_version"] = os_config["process"](version_str)
            elif "versions" in os_config and match.lastindex and match.lastindex >= 1:
                version_num = match.group(1)
                result["os_version"] = os_config["versions"].get(version_num, f"{os_name} {version_num}")
            else:
                result["os_version"] = os_name
            break

    mobile_keywords = ["mobile", "android", "iphone", "ipad", "ipod", "blackberry", "windows phone"]
    is_mobile = any(k in ua.lower() for k in mobile_keywords)
    result["is_mobile"] = is_mobile

    if is_mobile:
        if any(x in ua.lower() for x in ["iphone", "ipad", "ipod"]):
            result["device"] = "iOS"
        elif "android" in ua.lower():
            result["device"] = "Android"
        else:
            result["device"] = "Mobile"
    else:
        result["device"] = "Desktop"

    bot_keywords = [
        "bot",
        "crawler",
        "spider",
        "python-requests",
        "httpx",
        "aiohttp",
        "scrapy",
        "wget",
        "curl",
        "postman",
        "googlebot",
        "bingbot",
    ]
    if any(k in ua.lower() for k in bot_keywords):
        result["is_bot"] = True

    return result


def extract_telemetry(request: Request) -> dict:
    headers = request.headers
    ua = headers.get("User-Agent", "")

    ua_parsed = parse_user_agent(ua)

    return {
        "timestamp": time.time(),
        "runtime": {
            "server_os": platform.platform(),
            "python_version": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "network": {
            "ip": (headers.get("X-Forwarded-For") or headers.get("X-Real-IP") or (request.client.host if request.client else None)),
            "port": request.client.port if request.client else None,
            "host": headers.get("Host"),
            "referer": headers.get("Referer"),
            "origin": headers.get("Origin"),
        },
        "http": {
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query,
            "scheme": request.url.scheme,
            "http_version": request.headers.get("HTTP_VERSION", "HTTP/1.1"),
        },
        "client": {
            "headers": {
                "user_agent": ua,
                "accept": headers.get("Accept"),
                "accept_language": headers.get("Accept-Language"),
                "accept_encoding": headers.get("Accept-Encoding"),
                "accept_charset": headers.get("Accept-Charset"),
                "connection": headers.get("Connection"),
                "dnt": headers.get("DNT"),
                "cache_control": headers.get("Cache-Control"),
                "pragma": headers.get("Pragma"),
                "sec_fetch_dest": headers.get("Sec-Fetch-Dest"),
                "sec_fetch_mode": headers.get("Sec-Fetch-Mode"),
                "sec_fetch_site": headers.get("Sec-Fetch-Site"),
                "sec_fetch_user": headers.get("Sec-Fetch-User"),
                "sec_ch_ua": headers.get("Sec-CH-UA"),
                "sec_ch_ua_mobile": headers.get("Sec-CH-UA-Mobile"),
                "sec_ch_ua_platform": headers.get("Sec-CH-UA-Platform"),
            },
            "fingerprint": {
                "raw_user_agent": ua_parsed.get("raw_user_agent", ""),
                "browser": ua_parsed.get("browser"),
                "browser_version": ua_parsed.get("browser_version"),
                "os": ua_parsed.get("os"),
                "os_version": ua_parsed.get("os_version"),
                "device": ua_parsed.get("device"),
                "is_mobile": ua_parsed.get("is_mobile"),
                "is_bot": ua_parsed.get("is_bot"),
            },
        },
        "security": {
            "upgrade_insecure_requests": headers.get("Upgrade-Insecure-Requests"),
            "content_security_policy": headers.get("Content-Security-Policy"),
            "x_requested_with": headers.get("X-Requested-With"),
            "x_client_ip": headers.get("X-Client-IP"),
            "cf_connecting_ip": headers.get("CF-Connecting-IP"),
            "true_client_ip": headers.get("True-Client-IP"),
        },
        "encoding": {
            "content_encoding": headers.get("Content-Encoding"),
            "transfer_encoding": headers.get("Transfer-Encoding"),
            "accept_encoding": headers.get("Accept-Encoding"),
        },
        "language": {
            "accept_language": headers.get("Accept-Language"),
        },
    }


async def ipwhois_lookup(ip: str) -> dict:
    if ip.startswith("127.") or ip == "localhost":
        return {
            "type": "local",
            "country": "Localhost",
            "region": "Local",
            "city": "Local",
            "latitude": None,
            "longitude": None,
            "isp": "Local Network",
            "asn": None,
        }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"https://ipwho.is/{ip}")
            data = r.json()

            if not data.get("success", False):
                return {"type": "unknown"}

            return {
                "type": data.get("type"),
                "country": data.get("country"),
                "region": data.get("region"),
                "city": data.get("city"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "isp": data.get("connection", {}).get("isp"),
                "asn": data.get("connection", {}).get("asn"),
            }

    except Exception:
        return {"type": "error"}


class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, uuid: str = "", ipwhois: bool = False):
        super().__init__(app)
        self.uuid = uuid
        self.ipwhois = ipwhois

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        if request.url.path.endswith(f"/{self.uuid}"):
            telemetry = extract_telemetry(request)

            telemetry["performance"] = {"response_time_ms": round((time.time() - start_time) * 1000, 2)}

            if self.ipwhois and telemetry["network"]["ip"]:
                telemetry["network"]["ipwhois"] = await ipwhois_lookup(telemetry["network"]["ip"])

            print(json.dumps(telemetry, indent=2, ensure_ascii=False))

        return response


class SecurityHeadersMiddleware:
    def __init__(self, app: Callable, headers: dict[str, str]):
        self.app = app
        self.headers = headers

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                raw_headers = message.setdefault("headers", [])

                for key, value in self.headers.items():
                    # Пропускаем None значения
                    if value is not None:
                        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

            await send(message)

        await self.app(scope, receive, send_wrapper)
