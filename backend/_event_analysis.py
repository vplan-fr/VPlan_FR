import itertools
from collections import defaultdict
import datetime

import matplotlib.pyplot as plt
import numpy as np

from . import events, creds_provider


def main():
    plt.style.use('Solarize_Light2')

    creds = creds_provider.creds_provider_factory(None).get_creds()

    creds = {
        v["_id"]: v["display_name"] for v in creds.values()
    }

    data: dict[str, list[tuple[datetime.datetime, float]]] = defaultdict(list)

    for event in events.iterate_events(events.PlanCrawlCycle):
        y = (event.end_time - event.start_time).total_seconds() / 60
        x = event.start_time
        data[creds[event.school_number]].append((x, y))

    for school_number, points in data.items():
        # average hourly
        # points = sorted(points, key=lambda p: p[0].hour)
        #
        # points = [
        #     (datetime.datetime(1990, 1, 1, hour), np.mean(list(y for x, y in group)))
        #     for hour, group in itertools.groupby(points, key=lambda p: p[0].hour)
        # ]

        plt.plot(*zip(*points), label=school_number)

    plt.legend()

    plt.show()

    print(max(data, key=lambda k: data[k][0][1]))


if __name__ == '__main__':
    main()
