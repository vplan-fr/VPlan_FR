import datetime
import matplotlib.pyplot as plt

from helpers import load_database


def plot_slash_times():
    base_url_visits = [elem["time"] for elem in load_database("meta") if elem.get("path") == "/?"]
    date_counts = {}
    for dt in base_url_visits:
        date = datetime.datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
        if date in date_counts:
            date_counts[date] += 1
        else:
            date_counts[date] = 1

    dates = list(date_counts.keys())
    counts = list(date_counts.values())

    plt.plot(dates, counts)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_slash_times()

