import csv
import os
from datetime import datetime

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

SEARCH_QUERY = "salons in Al Reem Island, Abu Dhabi"
CATEGORY = "salon"
AREA = "Al Reem Island"


def search_places():
    params = {
        "query": SEARCH_QUERY,
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

def main():
    print("Searching Google Places...")
    print(f"Query: {SEARCH_QUERY}")
    print()

    search_results = search_places()

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
                "category": CATEGORY,
                "area": AREA,
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