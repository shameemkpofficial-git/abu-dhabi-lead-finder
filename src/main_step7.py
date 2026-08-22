import os
import requests


API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GOOGLE_MAPS_API_KEY is not set."
    )


url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

params = {
    "query": "salons in Al Reem Island, Abu Dhabi",
    "key": API_KEY,
}

response = requests.get(
    url,
    params=params,
    timeout=30,
)

print("HTTP status:", response.status_code)

data = response.json()

if response.status_code != 200:
    print("Google API error:")
    print(data)
    raise SystemExit(1)


status = data.get("status")

print("Google status:", status)

if status != "OK":
    print("Google API returned an error:")
    print(data)
    raise SystemExit(1)


results = data.get("results", [])

print()
print(f"Found {len(results)} businesses")
print("=" * 70)

for index, place in enumerate(results, start=1):

    name = place.get("name", "Unknown")
    address = place.get("formatted_address", "No address")
    rating = place.get("rating", "N/A")
    reviews = place.get("user_ratings_total", 0)
    place_id = place.get("place_id", "N/A")

    print(f"{index}. {name}")
    print(f"   Rating: {rating}")
    print(f"   Reviews: {reviews}")
    print(f"   Address: {address}")
    print(f"   Place ID: {place_id}")
    print("-" * 70)