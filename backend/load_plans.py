# coding=utf-8
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
import json

from stundenplan24_py import (
    IndiwareStundenplanerClient, Hosting, proxies
)
import aiohttp

from .plan_downloader import PlanDownloader
from .plan_processor import PlanProcessor
from .cache import Cache


class PlanCrawler:
    def __init__(self, plan_downloader: PlanDownloader, plan_processor: PlanProcessor):
        self.plan_downloader = plan_downloader
        self.plan_processor = plan_processor

    async def check_infinite(self, interval: int = 60, once: bool = False):
        self.plan_downloader.migrate_all()
        self.plan_processor.update_all()

        while True:
            downloaded_files = await self.plan_downloader.update_fetch()

            self.plan_processor._logger.debug("* Processing plans...")

            if downloaded_files:
                self.plan_processor.meta_extractor.invalidate_cache()

            for (date, revision), downloaded_files_metadata in downloaded_files.items():
                self.plan_processor.update_plans(date, revision)

            if downloaded_files:
                self.plan_processor.store_teachers()
                self.plan_processor.update_meta()

            if once:
                break

            await asyncio.sleep(interval)


async def get_clients(session: aiohttp.ClientSession | None = None,
                      proxy_provider: proxies.ProxyProvider | None = None) -> dict[str, PlanCrawler]:
    # parse credentials
    with open("creds.json", "r", encoding="utf-8") as f:
        _creds = json.load(f)

    clients = {}

    for school_name, data in _creds.items():
        specifier = data['school_number'] if 'school_number' in data else school_name
        logger = logging.getLogger(specifier)
        cache = Cache(Path(f".cache/{specifier}").absolute())

        data["hosting"]["creds"] = data["hosting"]["creds"].get("teachers", data["hosting"]["creds"].get("students"))
        hosting = Hosting.deserialize(data["hosting"])
        client = IndiwareStundenplanerClient(hosting, session)

        for plan_client in client.substitution_plan_clients:
            plan_client.proxy_provider = proxy_provider
            plan_client.no_delay = True

        for plan_client in client.indiware_mobil_clients:
            plan_client.proxy_provider = proxy_provider
            plan_client.no_delay = True

        plan_downloader = PlanDownloader(client, cache, logger=logger)
        plan_processor = PlanProcessor(cache, specifier, logger=logger)

        # create crawler
        p = PlanCrawler(plan_downloader, plan_processor)

        clients |= {school_name: p}

    return clients


async def main():
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--only-download", action="store_true",
                                 help="Only download plans, do not parse them.")
    argument_parser.add_argument("--once", action="store_true",
                                 help="Only download once, then exit.")
    argument_parser.add_argument("--only-process", action="store_true",
                                 help="Do not download plans, only parse existing.")
    argument_parser.add_argument("-loglevel", "-l", default="INFO")

    args = argument_parser.parse_args()

    try:
        args.loglevel = int(args.loglevel)
    except ValueError:
        pass

    logging.basicConfig(level=args.loglevel, format="[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    proxy_provider = proxies.ProxyProvider(Path("proxies.json").absolute())

    clients = await get_clients(proxy_provider=proxy_provider)
    try:
        if args.only_process:
            for client in clients.values():
                client.plan_downloader.migrate_all()
                client.plan_processor.update_all()
        elif args.only_download:
            if args.once:
                for client in clients.values():
                    client.plan_downloader.migrate_all()
                await asyncio.gather(
                    *[client.plan_downloader.update_fetch() for client in clients.values()]
                )
            else:
                await asyncio.gather(
                    *[client.plan_downloader.check_infinite() for client in clients.values()]
                )
        else:
            await asyncio.gather(
                *[client.check_infinite(once=args.once) for client in clients.values()]
            )
    finally:
        logging.debug("Closing clients...")
        await asyncio.gather(*(client.plan_downloader.client.close() for client in clients.values()),
                             return_exceptions=True)
        proxy_provider.store_proxies()

if __name__ == "__main__":
    asyncio.run(main())
