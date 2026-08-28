import csv
import html
import json
import os

import requests


CSV_FILE = "data/leads.csv"
LAST_SEARCH_FILE = "data/last_search.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_API_URL = "https://api.telegram.org/bot"


def get_leads():
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
        return list(csv.DictReader(file))


def get_todays_leads(rows, search_info):
    search_date = search_info.get(
        "date",
        "",
    )

    return [
        row
        for row in rows
        if row.get("last_seen", "") == search_date
    ]


def get_last_search():
    if not os.path.exists(LAST_SEARCH_FILE):
        raise FileNotFoundError(
            f"{LAST_SEARCH_FILE} does not exist."
        )

    with open(
        LAST_SEARCH_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_report(rows, search_info):
    hot = []
    high = []
    medium = []
    low = []
    unknown = []
    for row in rows:
        priority = row.get("priority", "").strip().upper()

        if priority == "HOT":
            hot.append(row)

        elif priority == "HIGH":
            high.append(row)

        elif priority == "MEDIUM":
            medium.append(row)

        elif priority == "LOW":
            low.append(row)
            
        else:
            unknown.append(row)

    # Highest score first
    hot.sort(
        key=lambda x: to_int(x.get("score")),
        reverse=True,
    )

    high.sort(
        key=lambda x: to_int(x.get("score")),
        reverse=True,
    )

    lines = []

    lines.append("🔥 <b>DAILY LEAD REPORT</b>")
    lines.append(
        f"❓ UNKNOWN: <b>{len(unknown)}</b>"
    )

    area = html.escape(
        search_info.get(
            "area",
            "Unknown area",
        )
    )

    category = html.escape(
        search_info.get(
            "category",
            "Unknown",
        )
    )

    search_type = html.escape(
        search_info.get(
            "search_type",
            "Unknown",
        )
    )

    search_index = search_info.get(
        "search_index",
        0,
    )

    total_searches = search_info.get(
        "total_searches",
        0,
    )

    lines.append(
        f"📍 <b>{area}, Abu Dhabi</b>"
    )

    lines.append(
        f"🏷️ Category: <b>{category}</b>"
    )

    lines.append(
        f"🔎 Search: <b>{search_type}</b>"
    )

    lines.append(
        f"🔄 Rotation: "
        f"<b>{int(search_index) + 1}/{total_searches}</b>"
    )

    lines.append("")

    lines.append(
        f"📊 Today's results: <b>{len(rows)}</b>"
    )

    lines.append(
        f"🔥 HOT: <b>{len(hot)}</b>"
    )

    lines.append(
        f"🟠 HIGH: <b>{len(high)}</b>"
    )

    lines.append(
        f"🟡 MEDIUM: <b>{len(medium)}</b>"
    )

    lines.append(
        f"⚪ LOW: <b>{len(low)}</b>"
    )

    lines.append("")

    # --------------------------------
    # HOT LEADS
    # --------------------------------

    if hot:
        lines.append("🔥 <b>HOT LEADS</b>")
        lines.append("")

        for index, lead in enumerate(
            hot[:10],
            start=1,
        ):
            lines.extend(
                format_lead(
                    index,
                    lead,
                )
            )

    # --------------------------------
    # HIGH LEADS
    # --------------------------------

    if high:
        lines.append("🟠 <b>HIGH PRIORITY</b>")
        lines.append("")

        for index, lead in enumerate(
            high[:10],
            start=1,
        ):
            lines.extend(
                format_lead(
                    index,
                    lead,
                )
            )

    return "\n".join(lines)


def format_lead(index, lead):
    name = html.escape(
        lead.get(
            "name",
            "Unknown",
        )
    )

    score = lead.get(
        "score",
        "0",
    )

    rating = lead.get(
        "rating",
        "",
    )

    reviews = lead.get(
        "reviews",
        "",
    )

    phone = html.escape(
        lead.get(
            "phone",
            "",
        )
    )

    website_status = html.escape(
        lead.get(
            "website_status",
            "",
        )
    )

    booking_status = html.escape(
        lead.get(
            "booking_status",
            "",
        )
    )

    booking_platform = html.escape(
        lead.get(
            "booking_platform",
            "",
        )
    )

    maps_url = lead.get(
        "google_maps_url",
        "",
    )

    lines = []

    lines.append(
        f"<b>{index}. {name}</b>"
    )

    lines.append(
        f"🎯 Score: <b>{score}</b>"
    )

    if rating or reviews:
        lines.append(
            f"⭐ {rating} "
            f"({reviews} reviews)"
        )

    if website_status:
        lines.append(
            f"🌐 Website: {website_status}"
        )

    if booking_status:
        lines.append(
            f"📅 Booking: {booking_status}"
        )

    if booking_platform:
        lines.append(
            f"🔧 Platform: {booking_platform}"
        )

    if phone:
        lines.append(
            f"📞 {phone}"
        )

    if maps_url:
        lines.append(
            f'<a href="{html.escape(maps_url)}">'
            f"📍 Google Maps</a>"
        )

    lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    return lines


def send_message(message):
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set."
        )

    if not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID is not set."
        )

    url = (
        TELEGRAM_API_URL
        + TELEGRAM_BOT_TOKEN
        + "/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {data}"
        )

    return data


def main():
    print(
        "Preparing Telegram lead report..."
    )

    all_rows = get_leads()

    print(
        f"Loaded {len(all_rows)} total leads."
    )

    search_info = get_last_search()

    rows = get_todays_leads(
        all_rows,
        search_info,
    )

    print(
        f"Today's search returned "
        f"{len(rows)} tracked leads."
    )

    print(
        f"Search area: "
        f"{search_info.get('area', 'Unknown')}"
    )

    print(
        f"Search category: "
        f"{search_info.get('category', 'Unknown')}"
    )

    print(
        f"Search type: "
        f"{search_info.get('search_type', 'Unknown')}"
    )

    report = build_report(
        rows,
        search_info,
    )

    print(
        "Sending report to Telegram..."
    )

    send_message(report)

    print(
        "Telegram report sent successfully."
    )


if __name__ == "__main__":
    main()

