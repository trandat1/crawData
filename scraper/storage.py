from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Tuple


def _update_sets_from_items(
    items: Iterable[dict[str, Any]],
    scraped_pids: set[str],
    scraped_hrefs: set[str],
) -> None:
    for it in items:
        pid = it.get("pid")
        href = it.get("href")
        if pid:
            scraped_pids.add(pid)
        if href:
            scraped_hrefs.add(href)


def load_previous_results(
    output_dir: str,
    today: datetime,
) -> Tuple[set[str], set[str], list[dict[str, Any]]]:
    scraped_pids: set[str] = set()
    scraped_hrefs: set[str] = set()
    all_results: list[dict[str, Any]] = []

    if not os.path.isdir(output_dir):
        return scraped_pids, scraped_hrefs, all_results

    for month in os.listdir(output_dir):
        month_path = os.path.join(output_dir, month)
        if not os.path.isdir(month_path):
            continue

        for file in os.listdir(month_path):
            if not file.endswith(".json"):
                continue

            file_date_str = file[:-5]  # remove .json
            try:
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
            except ValueError:
                continue

            if file_date > today:  
                continue

            try:
                with open(os.path.join(month_path, file), "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    _update_sets_from_items(data, scraped_pids, scraped_hrefs)
                    all_results.extend(data)

            except Exception:
                continue

    return scraped_pids, scraped_hrefs, all_results



def load_today_results(
    results_file: str,
    scraped_pids: set[str],
    scraped_hrefs: set[str],
) -> list[dict[str, Any]]:
    if not os.path.exists(results_file):
        return []
    try:
        with open(results_file, "r", encoding="utf-8") as f:
            today_data = json.load(f)
            if isinstance(today_data, list):
                _update_sets_from_items(today_data, scraped_pids, scraped_hrefs)
                return today_data
    except Exception:
        pass
    return []

def convert_paths(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: convert_paths(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_paths(x) for x in obj]
    return obj


def save_results(
    results: list[dict[str, Any]],
    results_file: str,
    scraped_pids: set[str],
    scraped_hrefs: set[str],
) -> None:
    unique: dict[str, dict[str, Any]] = {}
    for item in results:
        key = item.get("pid") or item.get("href")
        if not key:
            # fallback to object id to avoid overwriting
            key = f"tmp-{id(item)}"
        unique[key] = item

    final = list(unique.values())
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    _update_sets_from_items(final, scraped_pids, scraped_hrefs)
    print(f"Saved {len(final)} items to {results_file}")

