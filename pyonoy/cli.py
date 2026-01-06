"""
Command-line interface for Byonoy Absorbance 96 SiLA2 utilities.
"""

import argparse
from pathlib import Path

from .launcher import SiLAConfig, launch_sila_server
from .client import Absorbance96Client, ConnectionConfig, ExportFormat


def launch_main():
    """Entry point for byonoy-launch command."""
    parser = argparse.ArgumentParser(
        description="Launch Byonoy Absorbance 96 App with SiLA2 server"
    )
    parser.add_argument(
        "--app-path",
        type=Path,
        help="Path to Absorbance 96 App (auto-detected if not specified)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=50051,
        help="SiLA server port (default: 50051)"
    )
    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="SiLA server bind IP (default: 127.0.0.1, use 0.0.0.0 for network access)"
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Run without TLS encryption (not for production!)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI window"
    )
    parser.add_argument(
        "--uuid",
        help="Server UUID (generated automatically if not specified)"
    )
    parser.add_argument(
        "--cert",
        type=Path,
        help="Server certificate file (PEM format)"
    )
    parser.add_argument(
        "--key",
        type=Path,
        help="Server private key file (PEM format)"
    )
    parser.add_argument(
        "--ca-cert",
        type=Path,
        help="CA certificate file (PEM format)"
    )
    parser.add_argument(
        "--out-cert",
        type=Path,
        help="Output file for self-signed certificate"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for application to exit"
    )
    
    args = parser.parse_args()
    
    config = SiLAConfig(
        port=args.port,
        ip=args.ip,
        insecure=args.insecure,
        headless=args.headless,
        uuid=args.uuid,
        ca_cert=args.ca_cert,
        cert=args.cert,
        key=args.key,
        out_cert=args.out_cert,
    )
    
    try:
        process = launch_sila_server(config, args.app_path, args.wait)
        print(f"Started Absorbance 96 App with PID: {process.pid}")
        print(f"SiLA2 server: {config.ip}:{config.port}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


def client_main():
    """Entry point for byonoy-client command."""
    parser = argparse.ArgumentParser(
        description="Byonoy Absorbance 96 SiLA2 Client"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run an assay")
    run_parser.add_argument(
        "protocol",
        type=Path,
        help="Path to protocol file (.byop)"
    )
    run_parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output path for results"
    )
    run_parser.add_argument(
        "--format", "-f",
        choices=["csv", "xlsx", "json", "xml"],
        default="csv",
        help="Output format (default: csv)"
    )
    
    # Quit command
    subparsers.add_parser("quit", help="Quit the application")
    
    # Common arguments
    for subparser in [run_parser, subparsers.choices["quit"]]:
        subparser.add_argument(
            "--host",
            default="127.0.0.1",
            help="SiLA2 server host (default: 127.0.0.1)"
        )
        subparser.add_argument(
            "--port",
            type=int,
            default=50051,
            help="SiLA2 server port (default: 50051)"
        )
        subparser.add_argument(
            "--insecure",
            action="store_true",
            help="Use insecure connection (no TLS)"
        )
    
    args = parser.parse_args()
    config = ConnectionConfig(
        host=args.host,
        port=args.port,
        insecure=args.insecure,
    )
    
    if args.command == "run":
        from .client import run_assay
        
        results = run_assay(
            protocol_path=args.protocol,
            output_path=args.output,
            output_format=ExportFormat(args.format),
            host=args.host,
            port=args.port,
            insecure=args.insecure,
        )
        
        if results:
            print(f"\nResults ({len(results)} bytes):")
            print(results.decode('utf-8', errors='replace')[:2000])
    
    elif args.command == "quit":
        with Absorbance96Client(config) as client:
            with client.lock():
                client.quit_application()
        print("Application quit command sent.")


if __name__ == "__main__":
    launch_main()
