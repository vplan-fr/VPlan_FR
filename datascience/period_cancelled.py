from shared.cache import Cache
from backend.models import Plan, Lessons, PlanLesson
from backend.teacher import Teachers

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as mpatches

from stundenplan24_py import indiware_mobil

from xml.etree import ElementTree
import datetime
from pathlib import Path
from collections import defaultdict
import json
import numpy as np


def main():
    cache = Cache(Path(".cache/10000000"))

    out: dict[int, dict[int, list[int, int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))

    for day in cache.get_days():
        print(f"{day!s}")
        if day <= datetime.date(2023, 8, 20):
            continue

        revisions = cache.get_timestamps(day)

        try:
            xml_file = cache.get_plan_file(day, revisions[0], filename="PlanKl.xml", newest_before=True)
        except FileNotFoundError:
            continue

        indiware_plan = indiware_mobil.IndiwareMobilPlan.from_xml(ElementTree.fromstring(xml_file))

        plan = Plan.from_form_plan(indiware_plan)

        plan_lessons = plan.lessons.make_plan("forms", plan_type="forms")

        for form, lessons in plan_lessons.items():
            lessons_by_period = Lessons(lessons).filter(lambda l: not l.is_internal).group_by("periods")

            for period, period_lessons in lessons_by_period.items():
                for l in period_lessons.lessons:
                    out[day.weekday()][period][0] += 1
                    out[day.weekday()][period][1] += not l.takes_place

    with open("testout.json", "w") as f:
        json.dump(out, f)


def plot():
    with open("testout.json", "r") as f:
        out = json.load(f)
    
    data = np.zeros((11, 5))
    alpha = np.zeros(data.shape)

    for weekday, asd in out.items():
        for period, (total, cancelled) in asd.items():
            data[int(period), int(weekday)] = cancelled / total
            alpha[int(period), int(weekday)] = 1
        
    plt.imshow(data, cmap='viridis_r', interpolation='nearest', alpha=alpha)
    cbar = plt.colorbar()
    cbar.ax.invert_yaxis()

    ax = plt.gca()
    ax.xaxis.tick_top()
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels(['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'])
    plt.xticks(rotation=90)
    plt.ylabel('Stunde')

    for (i, j), val in np.ndenumerate(data):
        # print(i, j)
        if alpha[i, j]:
            text = ax.text(j, i, f"{val:.2%}", ha="center", va="center", color="k", size=5)

    plt.title(f"Ausfallwahrscheinlichkeit")

    plt.tight_layout()
    plt.savefig(f'heatmap.png', bbox_inches='tight', dpi=300)


if __name__ == "__main__":
    main()
    plot()
