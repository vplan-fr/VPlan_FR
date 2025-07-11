# coding=utf-8
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import asyncio
import logging
from pathlib import Path

import pipifax_proxy_manager
import pipifax_proxy_manager.config

from stundenplan24_py import (
    IndiwareStundenplanerClient, Hosting
)

from . import events
from shared.creds_provider import get_creds_provider
from .plan_downloader import PlanDownloader
from shared.cache import Cache
from .plan_processor import PlanProcessor


class PlanCrawler:
    school_number: str

    def __init__(self, school_number: str, plan_downloader: PlanDownloader, plan_processor: PlanProcessor):
        self.school_number = school_number
        self.plan_downloader = plan_downloader
        self.plan_processor = plan_processor
        self._plan_compute_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._plan_compute_awaiter_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    async def check_infinite(self, interval: int = 60, *, once: bool = False, ignore_exceptions: bool = False):
        try:
            self.plan_downloader.update_all_newest()
            self.plan_processor.do_full_update()
        except Exception as e:
            if not ignore_exceptions:
                raise
            else:
                self.plan_processor._logger.error("An error occurred.", exc_info=e)

        while True:
            _t1 = events.now()
            try:
                updated_dates = await self.plan_downloader.update_fetch()

                def _process_plans(t_start: datetime.datetime):
                    try:
                        self._plan_compute_executor.map(
                            self.plan_processor.update_day_plans, updated_dates
                        )
                        self.plan_processor.update_after_plan_processing()
                        events.submit_event(
                            events.PlanCrawlCycle(
                                school_number=self.school_number,
                                start_time=t_start,
                                end_time=events.now(),
                            )
                        )
                    except Exception:
                        if not ignore_exceptions:
                            raise
                        else:
                            self.plan_processor._logger.error("An error occurred (_process_plans).", exc_info=True)

                if updated_dates:
                    self.plan_processor._logger.debug("* Processing plans...")
                    self.plan_processor.meta_extractor.invalidate_cache()
                    self._plan_compute_awaiter_executor.submit(_process_plans, t_start=_t1)
                else:
                    self.plan_processor._logger.debug("* No plans to process.")
            except Exception:
                if not ignore_exceptions:
                    raise
                else:
                    self.plan_processor._logger.error("An error occurred.", exc_info=True)

            if once:
                break

            self.plan_downloader._logger.debug(f"* Waiting {interval} s.")
            await asyncio.sleep(interval)


async def get_crawlers(
    proxied_session: pipifax_proxy_manager.ProxiedSession | None = None,
    create_clients: bool = True
) -> dict[str, PlanCrawler]:
    creds_provider = get_creds_provider(Path("creds.json"))
    _creds = creds_provider.get_creds()

    request_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

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

            client = IndiwareStundenplanerClient(hosting)

            for plan_client in client.substitution_plan_clients:
                plan_client.proxied_session = proxied_session
                plan_client.request_executor = request_executor

            for plan_client in client.indiware_mobil_clients:
                plan_client.proxied_session = proxied_session
                plan_client.request_executor = request_executor
        else:
            client = None

        plan_downloader = PlanDownloader(specifier, client, cache, logger=logger)
        plan_processor = PlanProcessor(cache, specifier, logger=logger)

        # create crawler
        p = PlanCrawler(specifier, plan_downloader, plan_processor)

        crawlers[specifier] = p

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

    logging.getLogger("pymongo").setLevel(logging.WARNING)

    proxied_session = pipifax_proxy_manager.config.build_proxied_session(Path("proxy-config.toml"))
    proxied_session.ignore_ssl = False

    crawlers = await get_crawlers(proxied_session=proxied_session, create_clients=not args.only_process)
    try:
        if args.only_process:
            for crawler in crawlers.values():
                crawler.plan_downloader.update_all_newest()
                crawler.plan_processor.do_full_update()
        elif args.only_download:
            if args.once:
                for crawler in crawlers.values():
                    crawler.plan_downloader.update_all_newest()
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
        proxied_session.proxy_provider.close()
        if not args.only_process:
            await asyncio.gather(*(client.plan_downloader.client.close() for client in crawlers.values()),
                                 return_exceptions=True)
            proxied_session.proxy_provider.store_proxies()

        for crawler in crawlers.values():
            crawler.plan_processor.store_teachers()


if __name__ == "__main__":
    asyncio.run(main())
