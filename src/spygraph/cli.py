import argparse
import json
import sys

from rich import print as rprint

from spygraph.__about__ import __version__
from spygraph.core.telegraph.grapher import Grapher
from spygraph.workers import main as run_api_with_logger


def main() -> None:
    rprint(r"""[bold magenta]
   _________    ____  ____  _  _  ___  ____   __   ____  _  _ 
  /__ _ _ _/   / ___)(  _ \( \/ )/ __)(  _ \ / _\ (  _ \/ )( \
  \_ __ __ \   \___ \ ) __/ )  /( (_ \ )   //    \ ) __/) __ (
  (________)   (____/(__)  (__/  \___/(__\_)\_/\_/(__)  \_)(_/ [/bold magenta]""")
    
    parser = argparse.ArgumentParser(
        description="SpyGraph - IP address revelation tool using Telegraph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    create_account_parser = subparsers.add_parser(
        "create_account",
        help="Create a new Telegraph account"
    )
    create_account_parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Account short name (5-32 characters)"
    )
    create_account_parser.add_argument(
        "--author-name",
        type=str,
        default=None,
        help="Optional author name"
    )
    create_account_parser.add_argument(
        "--author-url",
        type=str,
        default=None,
        help="Optional author URL"
    )
    create_account_parser.add_argument(
        "--domain-graph",
        type=str,
        default="telegra.ph",
        help="Telegraph domain or mirror (default: telegra.ph)"
    )
    
    run_parser = subparsers.add_parser(
        "run",
        help="Start API server with Telegraph logging"
    )
    run_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server listen address (default: 0.0.0.0)"
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server listen port (default: 8000)"
    )
    run_parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="Custom tracking domain (your domain bound to API IP)"
    )
    run_parser.add_argument(
        "--telegraph-token",
        type=str,
        default=None,
        help="Telegraph access token (if not provided, will create new account)"
    )
    run_parser.add_argument(
        "--domain-graph",
        type=str,
        default="telegra.ph",
        help="Telegraph domain or mirror (default: telegra.ph)"
    )
    run_parser.add_argument(
        "--account-name",
        type=str,
        default="SpyGraph",
        help="Account name for new Telegraph account (default: SpyGraph)"
    )
    run_parser.add_argument(
        "--title",
        type=str,
        default="SpyGraph Target",
        help="Title for the Telegraph page (default: SpyGraph Target)"
    )
    run_parser.add_argument(
        "--content",
        type=str,
        default=None,
        help="Path to HTML/TXT content file for Telegraph page"
    )
    run_parser.add_argument(
        "--author_name",
        type=str,
        default="SpyGraph",
        help="Author name for Telegraph page (default: SpyGraph)"
    )
    run_parser.add_argument(
        "--ssl-cert",
        type=str,
        default=None,
        help="Path to SSL certificate file (certbot: /etc/letsencrypt/live/domain/fullchain.pem)"
    )
    run_parser.add_argument(
        "--ssl-key",
        type=str,
        default=None,
        help="Path to SSL private key file (certbot: /etc/letsencrypt/live/domain/privkey.pem)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    if args.command == "create_account":
        try:
            rprint("[cyan]Creating Telegraph account...[/cyan]")
            result = Grapher.create_account(
                short_name=args.name,
                author_name=args.author_name,
                author_url=args.author_url,
                domain_graph=args.domain_graph
            )
            
            rprint("\n[green]Account created successfully![/green]")
            rprint(f"[yellow]Access Token:[/yellow] {result['access_token']}")
            if result.get('auth_url'):
                rprint(f"[yellow]Auth URL:[/yellow] {result['auth_url']}")
            rprint(f"[yellow]Account Name:[/yellow] {result['user']['short_name']}")
            if result['user'].get('author_name'):
                rprint(f"[yellow]Author Name:[/yellow] {result['user']['author_name']}")
            if result['user'].get('author_url'):
                rprint(f"[yellow]Author URL:[/yellow] {result['user']['author_url']}")
            
            rprint("\n[dim]JSON Output:[/dim]")
            rprint(json.dumps(result, indent=2))
            
        except KeyboardInterrupt:
            rprint("\n[yellow]Cancelled[/yellow]")
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    elif args.command == "run":
        try:
            telegraph_token = args.telegraph_token
            
            if not telegraph_token:
                rprint("[cyan]Creating Telegraph account (no token provided)...[/cyan]")
                result = Grapher.create_account(
                    short_name=args.account_name,
                    domain_graph=args.domain_graph
                )
                telegraph_token = result['access_token']
                rprint(f"[green]Account created![/green] Token: [yellow]{telegraph_token}[/yellow]\n")
            
            rprint("[cyan]Initializing SpyGraph server...[/cyan]")
            rprint(f"[dim]Domain: {args.domain} | Graph Domain: {args.domain_graph}[/dim]\n")
            
            if args.ssl_cert or args.ssl_key:
                if not args.ssl_cert or not args.ssl_key:
                    rprint("[red]Error: Both --ssl-cert and --ssl-key must be provided together[/red]")
                    sys.exit(1)
                
                import os
                if not os.path.isfile(args.ssl_cert):
                    rprint(f"[red]Error: SSL certificate file not found: {args.ssl_cert}[/red]")
                    sys.exit(1)
                if not os.path.isfile(args.ssl_key):
                    rprint(f"[red]Error: SSL private key file not found: {args.ssl_key}[/red]")
                    sys.exit(1)
                
                rprint(f"[dim]SSL Certificate: {args.ssl_cert}[/dim]")
                rprint(f"[dim]SSL Private Key: {args.ssl_key}[/dim]\n")
            
            run_api_with_logger(
                host=args.host,
                port=args.port,
                telegraph_token=telegraph_token,
                tracking_domain=args.domain,
                domain_graph=args.domain_graph,
                page_title=args.title,
                page_content_path=args.content,
                page_author=args.author_name,
                ssl_cert=args.ssl_cert,
                ssl_key=args.ssl_key
            )
        except KeyboardInterrupt:
            rprint("\n[yellow]Server stopped[/yellow]")
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")
            sys.exit(1)