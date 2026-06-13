from __future__ import annotations

import argparse
from pathlib import Path

from tvu_scraper.config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tvu-scraper",
        description="TamilVU literary corpus scraper tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser(
        "inspect-config",
        help="Validate and print a crawl configuration summary without scraping",
    )
    inspect.add_argument("config", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect-config":
        config = load_config(args.config)
        print(f"site: {config.site.name}")
        print(f"seed: {config.site.seed_url}")
        print(f"crawl enabled: {config.crawl.enabled}")
        print(f"allowed hosts: {', '.join(config.crawl.allowed_hosts)}")
        print(f"raw dir: {config.storage.raw_dir}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2

