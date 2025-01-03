import argparse
import asyncio
import datetime
import logging
from pathlib import Path

from backend import meta_extractor
from backend.load_plans import get_crawlers
from shared import cache


async def main():
    logging.basicConfig(level="DEBUG", format="[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    argparser = argparse.ArgumentParser(description="The cache is always the .cache directory.")

    subparsers = argparser.add_subparsers(dest="subcommand", required=True)

    migrate_all = subparsers.add_parser("migrate-all")
    migrate_all.add_argument("--since", type=str, help="Only migrate plans since this date (YYYY-MM-DD).")
    migrate_all.add_argument("--school-number", action="append", help="Only migrate plans for this school number.",
                             default=[])
    migrate_all.add_argument("--just-newest-revision", action="store_true", help="Only migrate the newest revision.")

    extract_all_teachers = subparsers.add_parser("extract-all-teachers")

    import_plankl_files = subparsers.add_parser("import-plankl-files")
    import_plankl_files.add_argument("directory", type=str, help="Directory containing the PlanKl.xml files to import.")

    merge_cache = subparsers.add_parser("merge-cache",
                                        description="Merge another directory of school caches into the current one.")
    merge_cache.add_argument("foreign_cache_dir", type=str)

    clean_cache = subparsers.add_parser("clean-cache", description="Remove technically redundant .json-files from the cache.")

    clean_teachers = subparsers.add_parser("clean-teachers")

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
                def __setitem__(self, key, value):
                    date, rev = key
                    crawler.plan_processor._logger.info(f"Date: {date!s} Revision: {rev!s}")

            extractor = meta_extractor.MetaExtractor(
                cache=crawler.plan_processor.cache,
                num_last_days=None,
                logger=crawler.plan_processor._logger
            )
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

    elif args.subcommand == "merge-cache":
        for folder in Path(args.foreign_cache_dir).iterdir():
            if not folder.is_dir():
                continue

            school_num = folder.stem

            print(f"=> {school_num!r}")
            foreign_cache = cache.Cache(folder)
            try:
                this_cache = crawlers[school_num].plan_downloader.cache
            except KeyError as e:
                print(" -> Not in local cache. Not implemented. Skipping.")
                continue

            for day in foreign_cache.get_days():
                for rev in foreign_cache.get_timestamps(day):
                    path = foreign_cache.get_plan_path(day, rev)

                    for file in path.iterdir():
                        if file.name.endswith(".xml"):
                            if not this_cache.plan_file_exists(day, rev, file.name):
                                print(f" --> {day!s} {rev!s} {file.name!r}")
                                this_cache.store_plan_file(
                                    day,
                                    rev,
                                    foreign_cache.get_plan_file(day, rev, file.name),
                                    file.name
                                )

    elif args.subcommand == "clean-teachers":
        for crawler in crawlers.values():
            wrong_teachers = []
            for key, teacher in crawler.plan_processor.teachers.teachers.items():
                if teacher.plan_short is None:
                    print(f"- {key!r}: plan_short is None")
                    wrong_teachers.append(key)
                    continue

                if " " in teacher.plan_short:
                    print(f"- {key!r}: plan_short contains space")
                    wrong_teachers.append(key)

                if not any(char.isalpha() for char in teacher.plan_short):
                    print(f"- {key!r}: plan_short contains no letters")
                    wrong_teachers.append(key)

            print(f"=> Removing {len(wrong_teachers)} teachers...")
            for teacher in wrong_teachers:
                del crawler.plan_processor.teachers.teachers[teacher]

            crawler.plan_processor.store_teachers()

    elif args.subcommand == "clean-cache":
        for crawler in crawlers.values():
            if args.school_number and crawler.school_number not in args.school_number:
                continue

            for day in crawler.plan_processor.cache.get_days():
                if since is not None and day < since:
                    continue

                for file in crawler.plan_processor.cache.get_plan_path(day, None).iterdir():
                    if "xml" not in file.name:
                        print(f"=> Removing {file!s}")
                        file.unlink(missing_ok=True)


if __name__ == '__main__':
    asyncio.run(main())
