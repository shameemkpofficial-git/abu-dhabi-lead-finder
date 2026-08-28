import csv
from datetime import datetime
import json
import os

import requests


API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GOOGLE_MAPS_API_KEY is not set."
    )


TEXT_SEARCH_URL = (
    "https://maps.googleapis.com/maps/api/place/textsearch/json"
)

PLACE_DETAILS_URL = (
    "https://maps.googleapis.com/maps/api/place/details/json"
)

CSV_FILE = "data/leads.csv"
SEARCH_INFO_FILE = "data/last_search.json"

# ============================================================
# SEARCH ROTATION CONFIGURATION
# ============================================================

SEARCH_GROUPS = [
    {
        "category": "salon",
        "search_types": [
            "salons",
            "ladies salons",
            "beauty salons",
            "beauty lounges",
            "hair salons",
            "nail salons",
        ],
    },
    {
        "category": "spa",
        "search_types": [
            "spas",
            "day spas",
            "beauty spas",
            "wellness spas",
            "ladies spas",
        ],
    },
    {
        "category": "beauty_studio",
        "search_types": [
            "beauty studios",
            "beauty centers",
            "beauty lounges",
            "beauty clinics",
        ],
    },
    {
        "category": "nail_salon",
        "search_types": [
            "nail salons",
            "nail studios",
            "nail lounges",
            "manicure pedicure salons",
        ],
    },
    {
        "category": "hair_salon",
        "search_types": [
            "hair salons",
            "ladies hair salons",
            "hair studios",
            "hairdressers",
        ],
    },
    {
        "category": "barber",
        "search_types": [
            "barbers",
            "barber shops",
            "men's salons",
            "mens grooming",
        ],
    },
]


AREAS = [
    "Al Reem Island",
    "Khalifa City",
    "Yas Island",
    "Al Raha",
    "Saadiyat Island",
    "Abu Dhabi City",
]


def build_searches():

    searches = []

    # Search-type-first rotation.
    #
    # Example:
    #
    # Day 1  → Al Reem → salons
    # Day 2  → Khalifa → salons
    # Day 3  → Yas → salons
    # Day 4  → Al Raha → salons
    # Day 5  → Saadiyat → salons
    # Day 6  → Abu Dhabi → salons
    #
    # Then:
    #
    # Day 7  → Al Reem → ladies salons
    # Day 8  → Khalifa → ladies salons
    # etc.

    for group in SEARCH_GROUPS:

        category = group["category"]

        for search_type in group["search_types"]:

            for area in AREAS:

                searches.append(
                    {
                        "area": area,
                        "category": category,
                        "search_type": search_type,
                        "query": (
                            f"{search_type} "
                            f"in {area}, Abu Dhabi"
                        ),
                    }
                )

    return searches


SEARCHES = build_searches()


def get_todays_search():

    rotation_start = datetime(
        2026,
        8,
        28,
    ).date()

    today = datetime.now().date()

    days_since_start = (
        today - rotation_start
    ).days

    index = (
        days_since_start
        % len(SEARCHES)
    )

    return SEARCHES[index], index

    rotation_start = datetime(
        2026,
        8,
        28,
    ).date()

    today = datetime.now().date()

    days_since_start = (
        today - rotation_start
    ).days

    index = (
        days_since_start
        % len(SEARCHES)
    )

    return SEARCHES[index], index


def search_places(search_config):
    params = {
        "query": search_config["query"],
        "key": API_KEY,
    }

    response = requests.get(
        TEXT_SEARCH_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "OK":
        raise RuntimeError(
            f"Google Text Search failed: {data}"
        )

    return data.get("results", [])

def get_place_details(place_id):
    params = {
        "place_id": place_id,
        "fields": (
            "name,"
            "formatted_address,"
            "formatted_phone_number,"
            "website,"
            "rating,"
            "user_ratings_total,"
            "url"
        ),
        "key": API_KEY,
    }

    response = requests.get(
        PLACE_DETAILS_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "OK":
        print(
            f"Could not get details for {place_id}: "
            f"{data.get('status')}"
        )

        return {}


    return data.get("result", {})


def load_existing_leads():
    if not os.path.exists(CSV_FILE):
        return {}

    leads = {}

    with open(
        CSV_FILE,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            place_id = row.get("place_id")

            if place_id:
                leads[place_id] = row

    return leads


def save_leads(leads):
    base_fields = [
        "place_id",
        "name",
        "category",
        "area",
        "address",
        "phone",
        "website",
        "rating",
        "reviews",
        "google_maps_url",
        "instagram",
        "online_booking",
        "whatsapp",
        "score",
        "priority",
        "status",
        "first_seen",
        "last_seen",
        "notes",
        "website_status",
        "website_checked",
        "booking_status",
        "booking_url",
        "booking_platform",
        "booking_evidence",
    ]

    # Collect any additional fields that may already exist.
    all_fields = set(base_fields)

    for lead in leads.values():
        all_fields.update(lead.keys())

    # Keep our standard fields first.
    fieldnames = list(base_fields)

    # Add any unexpected/new fields afterward.
    for field in sorted(all_fields):
        if field not in fieldnames:
            fieldnames.append(field)

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for lead in leads.values():
            writer.writerow(lead)




def save_last_search(search_config, search_index):
    data = {
        "area": search_config["area"],
        "category": search_config["category"],
        "search_type": search_config["search_type"],
        "query": search_config["query"],
        "search_index": search_index,
        "total_searches": len(SEARCHES),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    os.makedirs(
        os.path.dirname(SEARCH_INFO_FILE),
        exist_ok=True,
    )

    with open(
        SEARCH_INFO_FILE,
        "w",
        encoding="utf-8",
    ) as file:


        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

def main():

    search_config, search_index = (
        get_todays_search()
    )
    save_last_search(
    search_config,
    search_index,
)

    search_query = search_config["query"]
    category = search_config["category"]
    area = search_config["area"]
    search_type = search_config["search_type"]

    print("==========================================")
    print("Daily Lead Finder")
    print(
        f"Search rotation: "
        f"{search_index + 1}/{len(SEARCHES)}"
    )
    print(f"Area: {area}")
    print(f"Category: {category}")
    print(f"Search type: {search_type}")
    print(f"Query: {search_query}")
    print("==========================================")
    print()

    search_results = search_places(
        search_config
    )
    print(
        f"Google returned "
        f"{len(search_results)} businesses."
    )

    existing_leads = load_existing_leads()

    today = datetime.now().strftime("%Y-%m-%d")

    for index, place in enumerate(
        search_results,
        start=1,
    ):
        place_id = place.get("place_id")

        if not place_id:
            continue

        name = place.get(
            "name",
            "Unknown",
        )

        print(
            f"[{index}/{len(search_results)}] "
            f"Processing: {name}"
        )

        details = get_place_details(place_id)

        if place_id in existing_leads:

            lead = existing_leads[place_id]

            lead["last_seen"] = today

            print("  Existing lead → updated")

        else:

            lead = {
                "place_id": place_id,
                "name": details.get(
                    "name",
                    name,
                ),
                "category": category,
                "area": area,
                "address": details.get(
                    "formatted_address",
                    place.get(
                        "formatted_address",
                        "",
                    ),
                ),
                "phone": details.get(
                    "formatted_phone_number",
                    "",
                ),
                "website": details.get(
                    "website",
                    "",
                ),
                "rating": details.get(
                    "rating",
                    "",
                ),
                "reviews": details.get(
                    "user_ratings_total",
                    "",
                ),
                "google_maps_url": details.get(
                    "url",
                    "",
                ),
                "instagram": "",
                "online_booking": "",
                "whatsapp": "",
                "score": "",
                "priority": "",
                "status": "NEW",
                "first_seen": today,
                "last_seen": today,
                "notes": "",
            }

            existing_leads[place_id] = lead

            print("  NEW lead → added")

    save_leads(existing_leads)

    print()
    print("==========================================")
    print("CSV update complete.")
    print(
        f"Total leads in database: "
        f"{len(existing_leads)}"
    )
    print(
        f"Saved to: {CSV_FILE}"
    )
    print("==========================================")


if __name__ == "__main__":
    main()