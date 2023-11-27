import itertools
from collections import defaultdict
import datetime

import matplotlib.pyplot as plt

from . import events
from shared import creds_provider


def main():
    plt.style.use('Solarize_Light2')

    creds = creds_provider.creds_provider_factory(None).get_creds()

    creds = {
        v["_id"]: v["display_name"] for v in creds.values()
    }

    data: dict[str, list[tuple[datetime.datetime, float]]] = defaultdict(list)

    for event in events.iterate_events(events.PlanCrawlCycle):
        y = (event.end_time - event.start_time).total_seconds()
        x = event.start_time
        data[creds[event.school_number]].append((x, y))

    fig, ax = plt.subplots(layout='constrained')

    for school_number, points in data.items():
        # average hourly
        # points = sorted(points, key=lambda p: p[0].hour)
        #
        # points = [
        #     (datetime.datetime(1990, 1, 1, hour), np.mean(list(y for x, y in group)))
        #     for hour, group in itertools.groupby(points, key=lambda p: p[0].hour)
        # ]

        # line opacity
        ax.plot(*zip(*points), label=school_number, marker="x", linestyle="solid", alpha=0.5, linewidth=1,
                markersize=5)

    for l, marker_type, line_style in zip(ax.lines, itertools.cycle('o><v^1*'), itertools.cycle(["dotted", "dashed", "dashdot", "solid"])):
        l.set_marker(marker_type)
        l.set_linestyle(line_style)
        #

    # ax.set_yscale('log')
    ax.set_ylim(bottom=0, top=max(max(y for x, y in points) for points in data.values()) * 1.1)

    ax.set_ylabel('Sekunden')
    ax.set_xlabel('Datum/Uhrzeit')
    ax2 = ax.twinx()
    mn, mx = ax.get_ylim()
    ax2.set_ylim(mn / 60, mx / 60)
    ax2.set_ylabel('Minuten')

    fig.legend(loc='outside right upper')

    plt.show()


if __name__ == '__main__':
    main()
