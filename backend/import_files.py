import asyncio
import datetime
import sys
from pathlib import Path

from load_plans import get_clients


async def main():
    clients = await get_clients()

    directory = Path(sys.argv[1])

    for file in directory.iterdir():
        school_nr, _date, _timestamp = file.stem.split("_")

        timestamp = datetime.datetime.fromtimestamp(int(_timestamp))

        clients[school_nr].cache.store_plan_file(
            datetime.datetime.strptime(_date, "%Y%m%d").date(),
            timestamp,
            file.read_text("utf-8"),
            "PlanKl.xml"
        )
        clients[school_nr].cache.store_plan_file(
            datetime.datetime.strptime(_date, "%Y%m%d").date(),
            timestamp,
            "",
            ".processed"
        )
        await clients[school_nr].update({f"PlanKl{_date}.xml": timestamp}, no_meta_update=True)

    await asyncio.gather(
        *[client.update_fetch() for client in clients.values()]
    )


if __name__ == "__main__":
    asyncio.run(main())
