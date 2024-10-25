# -*- coding: utf-8 -*-
import json
import os
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm
from tranco import Tranco

cache_dir = os.path.expanduser("~/.tranco")
TRANCO_ = Tranco(cache=True, cache_dir=cache_dir)
LATEST_DATE = TRANCO_.list().date


def date_range(start_date: str, end_date: Optional[str] = None, days: Optional[int] = None) -> List[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    yesterday = datetime.today() - timedelta(days=1)

    if days is not None:
        end = start + timedelta(days=days)
        if days < 0:
            start, end = end, start
    else:
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else yesterday

    dates = []
    current = start

    while current <= min(end, yesterday):
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def get_website_rankings(website_list: list, dates: List[str], filename: Optional[str] = None) -> dict:
    result = {}
    if filename and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            result = json.load(f)

    pbar = tqdm(dates, desc="Processing dates")
    for date in pbar:
        pbar.set_description(f"Processing {date}")

        if date > LATEST_DATE:
            break

        if date in result:
            existing_websites = set(result[date]["websites"])
            if set(website_list).issubset(existing_websites):
                continue

        rank_list = TRANCO_.list(date=date, subdomains=True, full=True)
        if date not in result:
            result[date] = {"id": rank_list.list_id, "websites": {}}

        for website in website_list:
            result[date]["websites"][website] = rank_list.rank(website)

    result = OrderedDict(sorted(result.items()))
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"数据已保存到 {filename}")

    return result


def main():
    current_folder = Path(__file__).resolve().parent.parent
    links_filename = current_folder / "public/data/links.json"
    rankings_filename = current_folder / "public/data/rankings.json"

    with open(links_filename, "r", encoding="utf-8") as f:
        link_dict = json.load(f)

    website_list = []
    for categories in link_dict["categories"].values():
        for website in categories["items"]:
            if "tranco" in website:
                website_list.append(website["tranco"])

    today = datetime.today().strftime("%Y-%m-%d")
    dates = date_range(start_date=today, days=-30)
    get_website_rankings(website_list, dates, filename=rankings_filename)


if __name__ == "__main__":
    main()
