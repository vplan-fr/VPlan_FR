import argparse
import asyncio
import datetime
import logging
from pathlib import Path

from backend import meta_extractor
from backend.load_plans import get_crawlers


async def main():
    logging.basicConfig(level="DEBUG", format="[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    argparser = argparse.ArgumentParser(epilog="The cache is always the .cache directory.")

    subparsers = argparser.add_subparsers(dest="subcommand")

    migrate_all = subparsers.add_parser("migrate-all")
    migrate_all.add_argument("--since", type=str, help="Only migrate plans since this date (YYYY-MM-DD).")
    migrate_all.add_argument("--school-number", action="append", help="Only migrate plans for this school number.", default=[])
    migrate_all.add_argument("--just-newest-revision", action="store_true", help="Only migrate the newest revision.")

    extract_all_teachers = subparsers.add_parser("extract-all-teachers")

    import_plankl_files = subparsers.add_parser("import-plankl-files")
    import_plankl_files.add_argument("directory", type=str, help="Directory containing the PlanKl.xml files to import.")

    args = argparser.parse_args()

    crawlers = await get_crawlers(create_clients=False)

    if args.subcommand == "migrate-all":
        since = datetime.datetime.strptime(args.since, "%Y-%m-%d").date() if args.since else None

        for crawler in crawlers.values():
            if args.school_number and crawler.school_number not in args.school_number:
                continue

            for day in crawler.plan_processor.cache.get_days():
                if since is not None and day < since:
                    continue

                crawler.plan_processor.cache.update_newest(day)

                for revision in crawler.plan_processor.cache.get_timestamps(day):
                    crawler.plan_processor._logger.info(f"Computing plans for {day} {revision}...")
                    crawler.plan_processor.compute_plan_revision(day, revision)

                    if args.just_newest_revision:
                        break

            crawler.plan_processor.update_after_plan_processing()

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

    elif args.subcommand == "import-plank-files":
        directory = Path(args.directory)

        for file in directory.iterdir():
            school_nr, _date, _timestamp = file.stem.split("_")

            timestamp = datetime.datetime.fromtimestamp(int(_timestamp))

            crawlers[school_nr].plan_downloader.cache.store_plan_file(
                datetime.datetime.strptime(_date, "%Y%m%d").date(),
                timestamp,
                file.read_text("utf-8"),
                "PlanKl.xml"
            )
            crawlers[school_nr].plan_downloader.cache.store_plan_file(
                datetime.datetime.strptime(_date, "%Y%m%d").date(),
                timestamp,
                "",
                ".processed"
            )

        await asyncio.gather(
            *[client.plan_processor.do_full_update() for client in crawlers.values()]
        )


if __name__ == '__main__':
    asyncio.run(main())
