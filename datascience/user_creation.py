import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcyberpunk

from utils import users, creds
from datascience.helpers import load_database, download_databases


def get_monthly_signups():
    times = users.find({"time_joined": {"$exists": True}}, {"time_joined": 1})
    times = [datetime.datetime.fromtimestamp(user_time["time_joined"]) for user_time in times]
    month_counts = {}
    for dt in times:
        month = dt.strftime("%Y-%m")  # Group by year and month
        if month in month_counts:
            month_counts[month] += 1
        else:
            month_counts[month] = 1
    return month_counts


def plot_user_times():
    month_counts = get_monthly_signups()
    months = list(month_counts.keys())
    counts = list(month_counts.values())

    fig, ax = plt.subplots()
    ax.bar(months, counts, edgecolor='k', alpha=0.7)
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of new Users")
    ax.tick_params(axis='x', labelrotation=30)
    for i, count in enumerate(counts):
        ax.text(i, count, str(count), ha='center', va='bottom', fontsize=10, color='white')

    plt.tight_layout()
    plt.show()


def get_users_by_time():
    times = users.find({"time_joined": {"$exists": True}}, {"time_joined": 1})
    times = [datetime.datetime.fromtimestamp(user_time["time_joined"]) for user_time in times]
    count = [i for i in range(len(times))]
    return times, count


def plot_users_by_time():
    times, count = get_users_by_time()

    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.plot(times, count, marker="o", markersize=.5)
    mplcyberpunk.add_glow_effects()
    ax.set_xlabel("Time")
    ax.set_ylabel("Number of users")
    ax.tick_params(axis='x', labelrotation=30)

    plt.tight_layout()
    plt.show()


def plot_school_counts():
    user_data = load_database("users")
    schools = []
    for user in user_data:
        if user.get("authorized_schools"):
            schools += user["authorized_schools"]
    schools = [school for school in schools if len(school) > 1]
    entry_counts = {creds.find_one({"_id": school_id}).get("short_name"): schools.count(school_id) for school_id in set(schools)}
    sorted_counts = sorted(entry_counts.items(), key=lambda x: x[1], reverse=True)
    total_count = len(schools)

    main_entries = []
    other_count = 0
    for entry, count in sorted_counts:
        percentage = (count / total_count) * 100
        if percentage < 2:
            other_count += count
        else:
            main_entries.append((entry, count))
    main_entries.append(("other", other_count))

    distinct_entries, entry_counts = zip(*main_entries)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(entry_counts, labels=distinct_entries, autopct=lambda p: f'{p * total_count / 100:.0f}', textprops={"color": "black"})
    ax.set_title("Authorized Schools")
    ax.axis('equal')
    plt.show()


def get_settings_usage():
    excluded = ["favorite"]
    settings = users.find({"settings": {"$exists": True}}, {"settings": 1})
    settings = [user_settings["settings"] for user_settings in settings]
    settings_counts = {}
    for setting in settings:
        for key in setting:
            if key in excluded:
                continue
            if key not in settings_counts:
                settings_counts[key] = {}
            if setting[key] in settings_counts[key]:
                settings_counts[key][setting[key]] += 1
            else:
                settings_counts[key][setting[key]] = 1
    return settings_counts


if __name__ == "__main__":
    plot_user_times()
    plot_users_by_time()
    plot_school_counts()
    ...
