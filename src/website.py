import csv
import os
from datetime import datetime
from urllib.parse import urlparse

import requests


CSV_FILE = "data/leads.csv"

SOCIAL_DOMAINS = {
    "instagram.com",
    "www.instagram.com",
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "tiktok.com",
    "www.tiktok.com",
    "linkedin.com",
    "www.linkedin.com",
}


def classify_url(url):
    if not url:
        return "NO_WEBSITE"

    try:
        hostname = urlparse(url).hostname

        if not hostname:
            return "INVALID_URL"

        hostname = hostname.lower()

        if hostname in SOCIAL_DOMAINS:
            return "SOCIAL_PROFILE"

        return "REAL_WEBSITE"

    except Exception:
        return "INVALID_URL"


def fetch_website(url):
    if not url:
        return "", "NO_WEBSITE"

    url_type = classify_url(url)

    if url_type == "SOCIAL_PROFILE":
        return "", "SOCIAL_PROFILE"

    if url_type != "REAL_WEBSITE":
        return "", url_type

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0 Safari/537.36"
                )
            },
            allow_redirects=True,
        )

        if response.status_code >= 400:
            return "", f"HTTP_{response.status_code}"

        return response.text, "ACCESSIBLE"

    except requests.RequestException as error:
        print(f"Website error: {url}")
        print(f"  {error}")

        return "", "INACCESSIBLE"


def main():
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(
            f"{CSV_FILE} does not exist."
        )

    with open(
        CSV_FILE,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if "website_status" not in fieldnames:
        fieldnames.append("website_status")

    if "website_checked" not in fieldnames:
        fieldnames.append("website_checked")

    today = datetime.now().strftime("%Y-%m-%d")

    print(f"Checking {len(rows)} businesses...")
    print()

    for index, row in enumerate(rows, start=1):

        name = row.get("name", "Unknown")
        website = row.get("website", "").strip()

        print(f"[{index}/{len(rows)}] {name}")

        html, status = fetch_website(website)

        row["website_status"] = status
        row["website_checked"] = today

        if status == "ACCESSIBLE":
            print(
                f"  Website: ACCESSIBLE "
                f"({len(html)} characters)"
            )

        elif status == "SOCIAL_PROFILE":
            print(
                "  Website field contains "
                "a social profile"
            )

        elif status == "NO_WEBSITE":
            print("  Website: NO WEBSITE")

        else:
            print(f"  Website: {status}")

        print()

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print("=" * 60)
    print("Website checking complete.")
    print(f"Updated: {CSV_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()