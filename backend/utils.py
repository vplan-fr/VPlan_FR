import argparse
import asyncio
import logging

from backend import meta_extractor
from backend.load_plans import get_crawlers


async def main():
    logging.basicConfig(level="DEBUG", format="[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    argparser = argparse.ArgumentParser()

    subparsers = argparser.add_subparsers(dest="subcommand")

    migrate_all = subparsers.add_parser("migrate-all")
    extract_all_teachers = subparsers.add_parser("extract-all-teachers")

    args = argparser.parse_args()

    crawlers = await get_crawlers(create_clients=False)

    if args.subcommand == "migrate-all":
        for crawler in crawlers.values():
            for day in crawler.plan_processor.cache.get_days():
                crawler.plan_processor.cache.update_newest(day)

                for revision in crawler.plan_processor.cache.get_timestamps(day):
                    crawler.plan_processor._logger.info(f"Computing plans for {day} {revision}...")
                    crawler.plan_processor.compute_plans(day, revision)

            crawler.plan_processor.update_meta()
            crawler.plan_processor.update_default_plan()
            crawler.plan_processor.store_teachers()

    elif args.subcommand == "extract-all-teachers":
        logging.basicConfig(level="DEBUG", format="[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S", force=True)

        for crawler in crawlers.values():
            crawler.plan_processor._logger.info("Extracting teachers...")

            class NullDict(dict):
                def __setattr__(self, key, value):
                    pass

            extractor = meta_extractor.MetaExtractor(crawler.plan_processor.cache, num_last_days=None,
                                                     logger=crawler.plan_processor._logger)
            extractor._daily_extractors = NullDict()
            crawler.plan_processor.teachers.add_teachers(*extractor.teachers())
            crawler.plan_processor.store_teachers()


if __name__ == '__main__':
    asyncio.run(main())
