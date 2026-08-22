import csv
import html
import os

import requests


CSV_FILE = "data/leads.csv"

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
)

TELEGRAM_API_URL = (
    "https://api.telegram.org/bot"
)


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

        return list(
            csv.DictReader(file)
        )


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_report(rows):
    hot = []
    high = []
    medium = []
    low = []

    for row in rows:

        priority = (
            row.get("priority", "")
            .strip()
            .upper()
        )

        if priority == "HOT":
            hot.append(row)

        elif priority == "HIGH":
            high.append(row)

        elif priority == "MEDIUM":
            medium.append(row)

        elif priority == "LOW":
            low.append(row)

    # Highest score first
    hot.sort(
        key=lambda x: to_int(
            x.get("score")
        ),
        reverse=True,
    )

    high.sort(
        key=lambda x: to_int(
            x.get("score")
        ),
        reverse=True,
    )

    lines = []

    lines.append(
        "🔥 <b>DAILY LEAD REPORT</b>"
    )

    lines.append(
        "📍 Al Reem Island, Abu Dhabi"
    )

    lines.append("")

    lines.append(
        f"📊 Total leads: <b>{len(rows)}</b>"
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

        lines.append(
            "🔥 <b>HOT LEADS</b>"
        )

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

        lines.append(
            "🟠 <b>HIGH PRIORITY</b>"
        )

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
        lead.get("name", "Unknown")
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
        lead.get("phone", "")
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
            f'📍 <a href="{html.escape(maps_url)}">'
            f"Google Maps</a>"
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

    rows = get_leads()

    print(
        f"Loaded {len(rows)} leads."
    )

    report = build_report(rows)

    print(
        "Sending report to Telegram..."
    )

    send_message(report)

    print(
        "Telegram report sent successfully."
    )


if __name__ == "__main__":
    main()
