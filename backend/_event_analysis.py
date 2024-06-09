import collections
import itertools
import typing
from collections import defaultdict
import datetime

import matplotlib.pyplot as plt

from . import events
from shared import creds_provider


def main():
    plt.style.use('Solarize_Light2')

    SINCE = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=14), datetime.time.min)

    creds = creds_provider.get_creds_provider(None).get_creds(ignore_disabled=True)

    creds = {
        v["_id"]: v["display_name"] for v in creds.values()
    }

    cutoff = datetime.datetime(2023, 11, 30, tzinfo=datetime.timezone.utc)

    def plot_basic(is_log: bool, data, title: str, unit: typing.Literal["seconds", None] = "seconds"):
        fig, ax = plt.subplots(layout='constrained')

        for school_number, points in data.items():
            data[school_number] = filter(lambda x: x[0] > cutoff, points)

        for school_number, points in data.items():
            ax.plot(*zip(*points), label=school_number, marker="x", linestyle="solid", alpha=0.5, linewidth=1,
                    markersize=5)

        for l, marker_type, line_style in zip(ax.lines, itertools.cycle('o><v^1*'),
                                              itertools.cycle(["dotted", "dashed", "dashdot", "solid"])):
            l.set_marker(marker_type)
            l.set_linestyle(line_style)

        # ax.set_ylim(bottom=0, top=max(max(y for x, y in points) for points in data.values()) * 1.1)

        if unit == "seconds":
            ax.set_ylabel('Sekunden')
            ax.set_xlabel('Datum/Uhrzeit')
            ax2 = ax.twinx()
            if is_log:
                ax2.set_yscale('log')
            mn, mx = ax.get_ylim()
            ax2.set_ylim(mn / 60, mx / 60)
            ax2.set_ylabel('Minuten')

        elif unit is None:
            ax.set_ylabel("Anzahl")

        if is_log:
            ax.set_yscale('log')

        fig.legend(loc='outside right upper')
        plt.title(title)
        plt.show()

    def plan_size(is_log: bool = False):
        data: dict[str, list[tuple[datetime.datetime, float]]] = defaultdict(list)
        for event in events.iterate_events(events.PlanDownload, since=SINCE):
            if event.file_length is None or event.plan_type != "PlanKl.xml":
                continue
            y = event.file_length
            x = event.start_time

            data[creds[event.school_number]].append((x, y))

        title = "Größe des heruntergeladenen Plans"

        plot_basic(is_log, data, title, unit=None)

    def time_from_upload_till_available(is_log: bool = False):
        title = "Zeit von Planupload bis Bereitstellung auf VPlan.fr"

        data: dict[str, list[tuple[datetime.datetime, float]]] = defaultdict(list)
        for event in events.iterate_events(events.StudentsRevisionProcessed, since=SINCE):
            y = (event.start_time - event.revision).total_seconds()
            x = event.start_time

            data[creds[event.school_number]].append((x, y))

        plot_basic(is_log, data, title)

    def time_from_upload_till_download(is_log: bool = False):
        data: dict[str, list[tuple[datetime.datetime, float]]] = defaultdict(list)
        for event in events.iterate_events(events.PlanDownload, since=SINCE):
            # TODO: Differentiate PlanKl and VplanKl
            if not event.plan_type == "PlanKl.xml":
                continue
            y = (event.start_time - event.last_modified).total_seconds()
            x = event.start_time

            data[creds[event.school_number]].append((x, y))

        title = "Zeit von Planupload bis Download vom Crawler"

        plot_basic(is_log, data, title)

    def duration_of(event_type, is_log: bool = False):
        data: dict[str, list[tuple[datetime.datetime, float]]] = defaultdict(list)
        for event in events.iterate_events(event_type, since=SINCE):
            y = (event.end_time - event.start_time).total_seconds()
            x = event.start_time

            data[creds[event.school_number]].append((x, y))

        title = f"Dauer von: {event_type.__name__}"

        plot_basic(is_log, data, title)

    def num_proxies(is_log: bool = False):
        data: dict[str, list[tuple[datetime.datetime, int]]] = defaultdict(list)
        for event in events.iterate_events(events.PlanDownload, since=SINCE):
            y = event.proxies_used
            if y is None:
                continue
            x = event.start_time

            data[creds[event.school_number]].append((x, y))

        title = f"Anzahl benutzer Proxies pro Download"
        plot_basic(is_log, data.copy(), title, unit=None)

        counts = collections.Counter()
        for points in data.values():
            for _, num in points:
                counts[num] += 1

        fig, ax = plt.subplots()
        ax.bar(counts.keys(), counts.values())
        # add data labels
        for i, v in counts.items():
            ax.text(i, v + 10, str(v), ha='center', va='bottom')
        # ax.set_yscale('log')
        ax.set_xlabel('Anzahl benutzer Proxies')
        plt.show()

    # plan_size(is_log=True)
    # time_from_upload_till_available(is_log=True)
    # time_from_upload_till_download(is_log=True)
    # duration_of(events.PlanCrawlCycle, is_log=True)
    # duration_of(events.StudentsRevisionProcessed, is_log=True)
    # duration_of(events.TeacherScrape, is_log=True)
    # duration_of(events.MetaUpdate, is_log=True)
    num_proxies(is_log=True)


if __name__ == '__main__':
    main()
