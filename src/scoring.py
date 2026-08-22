import csv
import os


CSV_FILE = "data/leads.csv"


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def calculate_score(row):
    score = 0

    website_status = row.get(
        "website_status",
        "",
    )

    booking_status = row.get(
        "booking_status",
        "",
    )

    booking_platform = row.get(
        "booking_platform",
        "",
    )

    rating = to_float(
        row.get("rating")
    )

    reviews = to_int(
        row.get("reviews")
    )

    # ---------------------------------
    # WEBSITE SIGNAL
    # ---------------------------------

    if website_status == "NO_WEBSITE":
        score += 25

    elif website_status == "SOCIAL_PROFILE":
        score += 15

    # ---------------------------------
    # BOOKING SIGNAL
    # ---------------------------------

    if booking_status == "NO_WEBSITE":
        score += 35

    elif booking_status == "NO_BOOKING_FOUND":
        score += 30

    elif booking_status == "SOCIAL_ONLY":
        score += 30

    elif booking_status == "LIKELY_BOOKING":
        score -= 20

    elif booking_status == "CONFIRMED_BOOKING":
        score -= 30

    elif booking_status == "UNKNOWN":
        score += 10

    # ---------------------------------
    # BOOKING PLATFORM
    # ---------------------------------

    if booking_platform:
        score -= 10

    # ---------------------------------
    # GOOGLE REVIEWS
    # ---------------------------------

    if reviews >= 100:
        score += 10

    elif reviews >= 50:
        score += 5

    # ---------------------------------
    # GOOGLE RATING
    # ---------------------------------

    if rating >= 4.5:
        score += 5

    # ---------------------------------
    # CAP SCORE
    # ---------------------------------

    score = max(
        0,
        min(score, 100),
    )

    # ---------------------------------
    # PRIORITY
    # ---------------------------------

    if score >= 75:
        priority = "HOT"

    elif score >= 60:
        priority = "HIGH"

    elif score >= 40:
        priority = "MEDIUM"

    else:
        priority = "LOW"

    return score, priority


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

        fieldnames = (
            reader.fieldnames or []
        )

    if "score" not in fieldnames:
        fieldnames.append("score")

    if "priority" not in fieldnames:
        fieldnames.append("priority")

    print(
        f"Scoring {len(rows)} leads..."
    )
    print()

    for index, row in enumerate(
        rows,
        start=1,
    ):

        score, priority = (
            calculate_score(row)
        )

        row["score"] = str(score)

        row["priority"] = priority

        print(
            f"[{index}/{len(rows)}] "
            f"{row.get('name', 'Unknown')}"
        )

        print(
            f"  Score: {score}"
        )

        print(
            f"  Priority: {priority}"
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
    print("Lead scoring complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()