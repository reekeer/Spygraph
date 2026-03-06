import json
from datetime import datetime
from multiprocessing import Queue

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_json_output(data: dict) -> None:
    if data.get("status") == "started":
        content = Text()
        content.append("\n  ◆ Status      : ", style="magenta")
        content.append("RUNNING", style="bold magenta")
        content.append("\n  ◆ Token       : ", style="magenta")
        api_token = data.get("api_token", "N/A")
        token_short = api_token[:16] + "..." if len(str(api_token)) > 16 else api_token
        content.append(token_short, style="bold magenta")
        content.append("\n  ◆ Base URL    : ", style="magenta")
        content.append(data.get("base_url", "N/A"), style="bold magenta")
        content.append("\n\n  ◆ UUID\n  ", style="magenta")
        uuid = data.get("uuid", "N/A")
        content.append(uuid, style="bold magenta")
        content.append("\n\n  ◆ Timestamp   : ", style="magenta")
        content.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="bold magenta")

        panel = Panel(content, title="API SERVER STARTED", box=box.ROUNDED, border_style="magenta", expand=False)
        console.print(panel)
        console.print()

    elif data.get("status") == "stopped":
        panel = Panel(
            Text("\n  API Server stopped\n", style="bold magenta"),
            title="API SERVER STOPPED",
            box=box.ROUNDED,
            border_style="magenta",
            expand=False,
        )
        console.print(panel)
        console.print()

    elif "timestamp" in data and "http" in data:
        http_info = data.get("http", {})
        method = http_info.get("method", "?")
        path = http_info.get("path", "?")

        client_info = data.get("client", {})
        fingerprint = client_info.get("fingerprint", {})
        headers = client_info.get("headers", {})

        network = data.get("network", {})
        security = data.get("security", {})
        perf = data.get("performance", {})

        response_time = perf.get("response_time_ms", 0)

        content = Text()
        content.append(f"\n  ◦ {method} {path}\n", style="bold magenta")

        content.append("  • NETWORK\n", style="magenta")
        content.append(f"    ◆ IP: {network.get('ip', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Port: {network.get('port', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Host: {network.get('host', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Referer: {network.get('referer', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Origin: {network.get('origin', 'N/A')}\n\n", style="magenta")

        if network.get("ipwhois"):
            ipwhois = network["ipwhois"]
            content.append("    ◆ IPWHOIS\n", style="magenta")
            content.append(f"      ◦ Type: {ipwhois.get('type', 'N/A')}\n", style="magenta")
            content.append(f"      ◦ Country: {ipwhois.get('country', 'N/A')}\n", style="magenta")
            content.append(f"      ◦ Region: {ipwhois.get('region', 'N/A')}\n", style="magenta")
            content.append(f"      ◦ City: {ipwhois.get('city', 'N/A')}\n", style="magenta")
            content.append(f"      ◦ Latitude: {ipwhois.get('latitude', 'N/A')}\n", style="magenta")
            content.append(f"      ◦ Longitude: {ipwhois.get('longitude', 'N/A')}\n", style="magenta")
            content.append(f"      ◦ ISP: {ipwhois.get('isp', 'N/A')}\n", style="magenta")
            content.append(f"      ◦ ASN: {ipwhois.get('asn', 'N/A')}\n\n", style="magenta")

        content.append("  • CLIENT\n", style="magenta")
        content.append(
            f"    ◆ Browser: {fingerprint.get('browser', 'Unknown')} {fingerprint.get('browser_version', '')}\n", style="magenta"
        )  # noqa: E501
        content.append(f"    ◆ OS: {fingerprint.get('os', 'Unknown')} {fingerprint.get('os_version', '')}\n", style="magenta")
        content.append(f"    ◆ Device: {fingerprint.get('device', 'Unknown')}\n", style="magenta")
        content.append(f"    ◆ Mobile: {str(fingerprint.get('is_mobile', False))}\n", style="magenta")
        content.append(f"    ◆ Bot: {str(fingerprint.get('is_bot', False))}\n\n", style="magenta")

        content.append("  • HTTP DATA\n", style="magenta")
        content.append(f"    ◆ Method: {method}\n", style="magenta")
        content.append(f"    ◆ Path: {path}\n", style="magenta")
        content.append(f"    ◆ Query: {http_info.get('query', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Scheme: {http_info.get('scheme', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ HTTP: {http_info.get('http_version', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Response: {response_time}ms\n\n", style="magenta")

        content.append("  • ACCEPT\n", style="magenta")
        content.append(f"    ◆ Content: {headers.get('accept', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Language: {headers.get('accept_language', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Encoding: {headers.get('accept_encoding', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Charset: {headers.get('accept_charset', 'N/A')}\n\n", style="magenta")

        content.append("  • SECURITY\n", style="magenta")
        content.append(f"    ◆ X-Requested: {security.get('x_requested_with', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ UpgradeHTTPS: {security.get('upgrade_insecure_requests', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ X-Client-IP: {security.get('x_client_ip', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ CF-IP: {security.get('cf_connecting_ip', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ True-Client: {security.get('true_client_ip', 'N/A')}\n\n", style="magenta")

        content.append("  • HINTS\n", style="magenta")
        content.append(f"    ◆ Sec-CH-UA: {headers.get('sec_ch_ua', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ UA-Mobile: {headers.get('sec_ch_ua_mobile', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ UA-Platform: {headers.get('sec_ch_ua_platform', 'N/A')}\n\n", style="magenta")

        content.append("  • FETCH\n", style="magenta")
        content.append(f"    ◆ Dest: {headers.get('sec_fetch_dest', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Mode: {headers.get('sec_fetch_mode', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ Site: {headers.get('sec_fetch_site', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ User: {headers.get('sec_fetch_user', 'N/A')}\n\n", style="magenta")

        content.append("  • CONNECTION\n", style="magenta")
        content.append(f"    ◆ Connection: {headers.get('connection', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ DNT: {headers.get('dnt', 'N/A')}\n", style="magenta")
        content.append(f"    ◆ CacheCtrl: {headers.get('cache_control', 'N/A')}\n\n", style="magenta")

        content.append("  • USER AGENT\n", style="magenta")
        ua = fingerprint.get("raw_user_agent", "N/A")
        content.append(f"    {ua}\n", style="dim magenta")

        panel = Panel(content, title="REQUEST", box=box.ROUNDED, border_style="magenta", expand=False)
        console.print(panel)

    else:
        content = Text()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        content.append(json_str, style="magenta")
        panel = Panel(content, title="EVENT", box=box.ROUNDED, border_style="magenta", expand=False)
        console.print(panel)


def process_logs(queue: Queue) -> None:
    panel = Panel(
        Text("  ◦ Waiting for requests...\n", style="bold magenta"),
        title="TELEMETRY LOGGER",
        box=box.ROUNDED,
        border_style="magenta",
        expand=False,
    )
    console.print(panel)
    console.print()

    try:
        while True:
            message = queue.get()

            if message is None:
                break

            try:
                data = json.loads(message)
                format_json_output(data)
            except json.JSONDecodeError:
                console.print(f"[dim magenta]{message}[/dim magenta]")

    except KeyboardInterrupt:
        panel = Panel(
            Text("  Shutdown complete", style="bold magenta"), title="LOGGER STOPPED", box=box.ROUNDED, border_style="magenta", expand=False
        )
        console.print(panel)
