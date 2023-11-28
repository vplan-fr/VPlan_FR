import asyncio
import datetime
import sys
from pathlib import Path

from .load_plans import get_crawlers


async def main():
    clients = await get_crawlers()

    directory = Path(sys.argv[1])

    for file in directory.iterdir():
        school_nr, _date, _timestamp = file.stem.split("_")

        timestamp = datetime.datetime.fromtimestamp(int(_timestamp))

        clients[school_nr].plan_downloader.cache.store_plan_file(
            datetime.datetime.strptime(_date, "%Y%m%d").date(),
            timestamp,
            file.read_text("utf-8"),
            "PlanKl.xml"
        )
        clients[school_nr].plan_downloader.cache.store_plan_file(
            datetime.datetime.strptime(_date, "%Y%m%d").date(),
            timestamp,
            "",
            ".processed"
        )

    await asyncio.gather(
        *[client.plan_processor.do_full_update() for client in clients.values()]
    )


if __name__ == "__main__":
    asyncio.run(main())
