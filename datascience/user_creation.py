import json
import datetime

from bson import ObjectId
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcyberpunk

from utils import creds, users, meta

DATABASES = {
    "creds": creds,
    "users": users,
    "meta": meta
}
USE_ONLINE = False

plt.style.use("cyberpunk")


def json_default(value):
    if isinstance(value, ObjectId):
        return str(value)  # Convert ObjectId to a string
    raise TypeError(f"Type {type(value)} is not JSON serializable")


def download_databases():
    for name in DATABASES:
        with open(f"{name}.json", "w+") as f:
            json.dump(list(DATABASES[name].find({})), f, default=json_default)


def load_database(database):
    if not USE_ONLINE:
        with open(f"{database}.json", "r") as f:
            return json.load(f)
    return list(DATABASES[database].find({}))


def plot_user_times():
    user_data = load_database("users")
    times = [datetime.datetime.fromtimestamp(user["time_joined"]) for user in user_data if user.get("time_joined")]
    month_counts = {}
    for dt in times:
        month = dt.strftime("%Y-%m")  # Group by year and month
        if month in month_counts:
            month_counts[month] += 1
        else:
            month_counts[month] = 1
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


def plot_users_by_time():
    user_data = load_database("users")
    times = [datetime.datetime.fromtimestamp(user["time_joined"]) for user in user_data if user.get("time_joined")]
    count = [i for i in range(len(times))]

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


if __name__ == "__main__":
    download_databases()
    plot_user_times()
    plot_users_by_time()
    plot_school_counts()
    ...
