import csv
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests


CSV_FILE = "data/leads.csv"

REQUEST_TIMEOUT = 15

BOOKING_KEYWORDS = [
    "book now",
    "book appointment",
    "book online",
    "online booking",
    "book a service",
    "make an appointment",
    "schedule an appointment",
    "appointments",
    "appointment booking",
    "reserve now",
    "reserve an appointment",
    "schedule now",
]

BOOKING_PATH_KEYWORDS = [
    "/book",
    "/booking",
    "/book-now",
    "/booknow",
    "/appointment",
    "/appointments",
    "/reservation",
    "/reservations",
    "/schedule",
]

BOOKING_PLATFORMS = {
    "fresha.com": "Fresha",
    "booksy.com": "Booksy",
    "treatwell": "Treatwell",
    "timify.com": "Timify",
    "mindbodyonline.com": "Mindbody",
    "phorest.com": "Phorest",
    "vagaro.com": "Vagaro",
    "squareup.com": "Square",
    "square.site": "Square",
}


def fetch_page(url):
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
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
            return "", response.url, response.status_code

        return response.text, response.url, response.status_code

    except requests.RequestException as error:
        print(f"  Request error: {error}")
        return "", url, 0


def normalize_text(text):
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    )


def detect_booking_platform(text):
    text_lower = text.lower()

    for domain, platform in BOOKING_PLATFORMS.items():
        if domain in text_lower:
            return platform

    return ""


def find_booking_keyword(text):
    text_lower = normalize_text(text)

    for keyword in BOOKING_KEYWORDS:
        if keyword in text_lower:
            return keyword

    return ""


def extract_links(html, base_url):
    links = []

    hrefs = re.findall(
        r'href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )

    for href in hrefs:

        href = href.strip()

        if not href:
            continue

        absolute_url = urljoin(
            base_url,
            href,
        )

        if absolute_url not in links:
            links.append(absolute_url)

    return links


def find_booking_link(links):
    for link in links:

        link_lower = link.lower()

        for keyword in BOOKING_PATH_KEYWORDS:
            if keyword in link_lower:
                return link

    return ""


def analyze_booking(url):
    html, final_url, status_code = fetch_page(url)

    if not html:
        return {
            "booking_status": "UNKNOWN",
            "booking_url": "",
            "booking_platform": "",
            "booking_evidence": "",
        }

    text = normalize_text(html)

    platform = detect_booking_platform(html)

    if platform:
        return {
            "booking_status": "CONFIRMED_BOOKING",
            "booking_url": final_url,
            "booking_platform": platform,
            "booking_evidence": (
                f"Booking platform detected: {platform}"
            ),
        }

    keyword = find_booking_keyword(text)

    links = extract_links(
        html,
        final_url,
    )

    booking_link = find_booking_link(links)

    if booking_link:
        return {
            "booking_status": "LIKELY_BOOKING",
            "booking_url": booking_link,
            "booking_platform": "",
            "booking_evidence": (
                f"Booking-related URL detected: "
                f"{booking_link}"
            ),
        }

    if keyword:
        return {
            "booking_status": "LIKELY_BOOKING",
            "booking_url": "",
            "booking_platform": "",
            "booking_evidence": (
                f"Booking keyword detected: "
                f"{keyword}"
            ),
        }

    return {
        "booking_status": "NO_BOOKING_FOUND",
        "booking_url": "",
        "booking_platform": "",
        "booking_evidence": "",
    }


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

    new_columns = [
        "booking_status",
        "booking_url",
        "booking_platform",
        "booking_evidence",
    ]

    for column in new_columns:
        if column not in fieldnames:
            fieldnames.append(column)

    today = datetime.now().strftime("%Y-%m-%d")

    print(
        f"Analyzing booking options for "
        f"{len(rows)} businesses..."
    )
    print()

    for index, row in enumerate(
        rows,
        start=1,
    ):

        name = row.get(
            "name",
            "Unknown",
        )

        website = row.get(
            "website",
            "",
        ).strip()

        website_status = row.get(
            "website_status",
            "",
        )

        print(
            f"[{index}/{len(rows)}] {name}"
        )

        if website_status == "NO_WEBSITE":
            row["booking_status"] = "NO_WEBSITE"
            row["booking_url"] = ""
            row["booking_platform"] = ""
            row["booking_evidence"] = (
                "No website listed"
            )

            print(
                "  Booking: NO WEBSITE"
            )
            print()
            continue

        if website_status == "SOCIAL_PROFILE":
            row["booking_status"] = "SOCIAL_ONLY"
            row["booking_url"] = website
            row["booking_platform"] = ""
            row["booking_evidence"] = (
                "Only social profile available"
            )

            print(
                "  Booking: SOCIAL PROFILE ONLY"
            )
            print()
            continue

        if website_status not in {
            "ACCESSIBLE",
        }:
            row["booking_status"] = "UNKNOWN"
            row["booking_url"] = ""
            row["booking_platform"] = ""
            row["booking_evidence"] = (
                f"Website status: {website_status}"
            )

            print(
                f"  Booking: UNKNOWN "
                f"({website_status})"
            )
            print()
            continue

        result = analyze_booking(website)

        row["booking_status"] = (
            result["booking_status"]
        )

        row["booking_url"] = (
            result["booking_url"]
        )

        row["booking_platform"] = (
            result["booking_platform"]
        )

        row["booking_evidence"] = (
            result["booking_evidence"]
        )

        print(
            f"  Booking: "
            f"{result['booking_status']}"
        )

        if result["booking_platform"]:
            print(
                f"  Platform: "
                f"{result['booking_platform']}"
            )

        if result["booking_url"]:
            print(
                f"  Booking URL: "
                f"{result['booking_url']}"
            )

        if result["booking_evidence"]:
            print(
                f"  Evidence: "
                f"{result['booking_evidence']}"
            )

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
    print("Booking analysis complete.")
    print(f"Updated: {CSV_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()