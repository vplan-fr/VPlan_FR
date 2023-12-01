# coding=utf-8
from __future__ import annotations

import argparse
import concurrent.futures
import aiohttp
import asyncio
import logging
from pathlib import Path

from stundenplan24_py import (
    IndiwareStundenplanerClient, Hosting, proxies
)

from . import events
from shared.creds_provider import creds_provider_factory
from .plan_downloader import PlanDownloader
from shared.cache import Cache
from .plan_processor import PlanProcessor


class PlanCrawler:
    school_number: str

    def __init__(self, school_number: str, plan_downloader: PlanDownloader, plan_processor: PlanProcessor):
        self.school_number = school_number
        self.plan_downloader = plan_downloader
        self.plan_processor = plan_processor
        self._plan_compute_executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)

    async def check_infinite(self, interval: int = 60, *, once: bool = False, ignore_exceptions: bool = False):
        self.plan_downloader.migrate_all()
        self.plan_processor.do_full_update()

        while True:
            _t1 = events.now()
            try:
                updated_dates = await self.plan_downloader.update_fetch()

                if updated_dates:
                    self.plan_processor._logger.debug("* Processing plans...")
                    self.plan_processor.meta_extractor.invalidate_cache()
                else:
                    self.plan_processor._logger.debug("* No plans to process.")

                for date in updated_dates:
                    self._plan_compute_executor.submit(
                        self.plan_processor.update_day_plans, date
                    )

                if updated_dates:
                    self.plan_processor.update_after_plan_processing()

            except Exception as e:
                if not ignore_exceptions:
                    raise
                else:
                    self.plan_processor._logger.error("An error occurred.", exc_info=e)
            else:
                _t2 = events.now()
                events.submit_event(
                    events.PlanCrawlCycle(
                        school_number=self.school_number,
                        start_time=_t1,
                        end_time=_t2,
                    )
                )

            if once:
                break

            self.plan_downloader._logger.debug(f"* Waiting {interval} s.")
            await asyncio.sleep(interval)


async def get_crawlers(session: aiohttp.ClientSession | None = None,
                       proxy_provider: proxies.ProxyProvider | None = None,
                       create_clients: bool = True) -> dict[str, PlanCrawler]:
    creds_provider = creds_provider_factory(Path("creds.json"))
    _creds = creds_provider.get_creds()

    crawlers = {}

    for school_name, data in _creds.items():
        specifier = data['school_number'] if 'school_number' in data else school_name
        logger = logging.getLogger(specifier)
        cache = Cache(Path(f".cache/{specifier}").absolute())

        if create_clients:
            data["hosting"]["creds"] = data["hosting"]["creds"].get(
                "teachers", data["hosting"]["creds"].get("students")
            )
            hosting = Hosting.deserialize(data["hosting"])

            if hosting.creds is not None and hosting.creds.username == "schueler":
                logger.warning("* Disabling room and teacher plans because only student creds are available.")
                # avoid trying to fetch room and teacher plans if no creds are available
                hosting.indiware_mobil.rooms = None
                hosting.indiware_mobil.teachers = None
                hosting.substitution_plan.teachers = None

            client = IndiwareStundenplanerClient(hosting, session)

            for plan_client in client.substitution_plan_clients:
                plan_client.proxy_provider = proxy_provider
                plan_client.no_delay = True

            for plan_client in client.indiware_mobil_clients:
                # plan_client.proxy_provider = proxy_provider
                plan_client.no_delay = True
        else:
            client = None

        plan_downloader = PlanDownloader(specifier, client, cache, logger=logger)
        plan_processor = PlanProcessor(cache, specifier, logger=logger)

        # create crawler
        p = PlanCrawler(specifier, plan_downloader, plan_processor)

        crawlers[school_name] = p

    return crawlers


async def main():
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--only-download", action="store_true",
                                 help="Only download plans, do not parse them.")
    argument_parser.add_argument("--once", action="store_true",
                                 help="Only download once, then exit.")
    argument_parser.add_argument("--only-process", action="store_true",
                                 help="Do not download plans, only parse existing.")
    argument_parser.add_argument("--ignore-exceptions", action="store_true",
                                 help="Don't raise exceptions and crash the program, instead, print them and continue.")
    argument_parser.add_argument("--never-raise-out-of-proxies", action="store_true",
                                 help="Never crash the program if no more proxies seem to be available. "
                                      "Keep trying instead.")
    argument_parser.add_argument("-interval", "-i", type=int, default=60,
                                 help="Interval in seconds between each download cycle.")
    argument_parser.add_argument("-loglevel", "-l", default="INFO")

    args = argument_parser.parse_args()

    try:
        args.loglevel = int(args.loglevel)
    except ValueError:
        pass

    logging.basicConfig(level=args.loglevel, format="[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S", force=True)

    proxy_provider = proxies.ProxyProvider(Path("proxies.json").absolute(),
                                           never_raise_out_of_proxies=args.never_raise_out_of_proxies)
    # list(proxy_provider.fetch_proxies())

    crawlers = await get_crawlers(proxy_provider=proxy_provider, create_clients=not args.only_process)
    try:
        if args.only_process:
            for crawler in crawlers.values():
                crawler.plan_downloader.migrate_all()
                crawler.plan_processor.do_full_update()
        elif args.only_download:
            if args.once:
                for crawler in crawlers.values():
                    crawler.plan_downloader.migrate_all()
                await asyncio.gather(
                    *[crawler.plan_downloader.update_fetch() for crawler in crawlers.values()]
                )
            else:
                await asyncio.gather(
                    *[crawler.plan_downloader.check_infinite(ignore_exceptions=args.ignore_exceptions,
                                                             interval=args.interval)
                      for crawler in crawlers.values()]
                )
        else:
            await asyncio.gather(
                *[crawler.check_infinite(once=args.once, ignore_exceptions=args.ignore_exceptions,
                                         interval=args.interval)
                  for crawler in crawlers.values()]
            )
    finally:
        logging.info("Exit.")
        logging.debug("Closing clients...")
        for crawler in crawlers.values():
            crawler.plan_processor._logger.debug("Closing plan compute executor...")
            crawler._plan_compute_executor.shutdown(wait=True)

        logging.debug("Closed all executors.")

        if not args.only_process:
            await asyncio.gather(*(client.plan_downloader.client.close() for client in crawlers.values()),
                                 return_exceptions=True)
            proxy_provider.store_proxies()

        for crawler in crawlers.values():
            crawler.plan_processor.store_teachers()


if __name__ == "__main__":
    asyncio.run(main())
