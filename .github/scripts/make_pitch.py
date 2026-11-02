#!/usr/bin/env python3
"""Render a phone mock-up for a visitor's app pitch, then rebuild the wall in README.md.

Input arrives in the environment, set by the workflow:
  PITCH_NUMBER, PITCH_USER, PITCH_BUSINESS, PITCH_DETAIL
Issue text is untrusted, so everything written into the SVG is escaped and
length-capped first.
"""
import html
import os
import pathlib
import re

PINK, PINK_SOFT = "#FF2E9A", "#FF7AC6"
INK, CARD, LINE = "#07080D", "#121626", "#242B3D"
TXT, DIM = "#EEF2FF", "#8795B4"

ROOT = pathlib.Path(__file__).resolve().parents[2]
WALL_START = "<!-- PITCH-WALL:START -->"
WALL_END = "<!-- PITCH-WALL:END -->"
MAX_TILES = 6


def clean(text, limit):
    """Untrusted text -> safe, short, single line."""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return html.escape(text, quote=True)


# Which screen gets drawn, based on what the visitor said they do.
# Checked top to bottom, so the more specific kinds come first.
KINDS = [
    (("salon", "barber", "groom", "clean", "detail", "trainer", "lash", "nail", "spa",
      "massage", "photo", "lawn", "tutor", "repair", "appointment", "booking", "schedule",
      "haircut", "therapist", "dentist", "stylist", "plumb", "electric", "tattoo",
      "car wash", "landscap", "mobile service"),
     ["Book an appointment", "Pick a time that works", "Pay a deposit",
      "Card on file, fewer no shows", "Automatic reminders", "Texted the day before"],
     "Book now"),
    (("restaurant", "food", "cafe", "coffee", "menu", "catering", "truck", "kitchen",
      "takeout", "take out", "diner", "pizza", "bbq", "barbecue", "grill", "deli",
      "bakery", "juice", "soul food", "meal"),
     ["Today's menu", "Updated from your phone", "Order ahead", "Skip the line",
      "Pay in app", "Tips included"],
     "Order"),
    (("church", "ministry", "congregation", "nonprofit", "non profit", "member",
      "community", "club", "school", "daycare", "gym", "team", "chapter", "association"),
     ["This week", "Events and announcements", "Give", "Secure, one tap",
      "Members", "Directory and messages"],
     "Open"),
    (("shop", "store", "sell", "product", "boutique", "candle", "retail", "merch",
      "clothing", "jewelry", "inventory", "ecommerce", "e commerce"),
     ["Browse the shop", "Everything you sell, in hand", "Add to cart",
      "Checkout in two taps", "Order updates", "Ready for pickup"],
     "Checkout"),
]
DEFAULT = (["What you offer", "Clear, on one screen", "Get in touch",
            "Calls, texts, bookings", "Paid in app", "Money in your account"],
           "Get started")


def pick(detail, business):
    hay = f"{detail} {business}".lower()
    for words, rows, cta in KINDS:
        if any(w in hay for w in words):
            return rows, cta
    return DEFAULT


def render(number, user, business, detail):
    rows, cta = pick(detail, business)
    pairs = [(rows[i], rows[i + 1]) for i in range(0, 6, 2)]
    W, H = 300, 480
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"'
         ' font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">']
    s.append(f'<defs><linearGradient id="h{number}" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_SOFT}"/>'
             '</linearGradient></defs>')
    s.append(f'<rect width="{W}" height="{H}" rx="18" fill="#0A0B11"/>')
    s.append(f'<rect x="24" y="22" width="252" height="400" rx="34" fill="#15182A" '
             f'stroke="url(#h{number})" stroke-width="2"/>')
    s.append(f'<rect x="40" y="38" width="220" height="368" rx="26" fill="{INK}"/>')
    s.append('<rect x="120" y="38" width="60" height="17" rx="9" fill="#000"/>')
    s.append(f'<text x="58" y="74" font-size="10.5" fill="{DIM}">9:41</text>')
    s.append(f'<text x="58" y="112" font-size="16" font-weight="700" fill="{TXT}">{business}</text>')
    s.append(f'<rect x="58" y="122" width="34" height="3" rx="1.5" fill="{PINK}"/>')
    y = 148
    for title, sub in pairs:
        s.append(f'<rect x="56" y="{y}" width="188" height="54" rx="12" fill="{CARD}" stroke="{LINE}"/>')
        s.append(f'<rect x="56" y="{y}" width="3" height="54" rx="1.5" fill="{PINK}" opacity=".85"/>')
        s.append(f'<circle cx="80" cy="{y+27}" r="10" fill="{PINK}" opacity=".18"/>')
        s.append(f'<circle cx="80" cy="{y+27}" r="3.5" fill="{PINK}"/>')
        s.append(f'<text x="98" y="{y+23}" font-size="11" fill="{TXT}">{html.escape(title)}</text>')
        s.append(f'<text x="98" y="{y+39}" font-size="9" fill="{DIM}">{html.escape(sub)}</text>')
        y += 64
    s.append(f'<rect x="56" y="{y+6}" width="188" height="40" rx="12" fill="url(#h{number})"/>')
    s.append(f'<text x="150" y="{y+31}" text-anchor="middle" font-size="12" font-weight="700" '
             f'fill="#0A0A0A">{html.escape(cta)}</text>')
    s.append(f'<rect x="125" y="394" width="50" height="4" rx="2" fill="{DIM}" opacity=".5"/>')
    s.append(f'<text x="150" y="444" text-anchor="middle" font-size="10" fill="{DIM}">'
             f'pitched by @{user}</text>')
    s.append(f'<text x="150" y="464" text-anchor="middle" font-size="9.5" fill="{PINK}">'
             'drawn in seconds by Template Craft</text>')
    s.append('</svg>')
    return "\n".join(s)


def rebuild_wall():
    tiles = sorted(
        (ROOT / "pitches").glob("*.svg"),
        key=lambda p: int(p.stem) if p.stem.isdigit() else 0,
        reverse=True,
    )[:MAX_TILES]
    if not tiles:
        return
    cells = " ".join(
        f'<img src="pitches/{t.name}" width="150" alt="app pitch">' for t in tiles
    )
    block = f'{WALL_START}\n<p align="center">{cells}</p>\n{WALL_END}'
    readme = ROOT / "README.md"
    text = readme.read_text()
    if WALL_START in text and WALL_END in text:
        head, rest = text.split(WALL_START, 1)
        _, tail = rest.split(WALL_END, 1)
        readme.write_text(head + block + tail)


def main():
    number = clean(os.environ.get("PITCH_NUMBER", "0"), 8) or "0"
    user = clean(os.environ.get("PITCH_USER", "someone"), 39)
    business = clean(os.environ.get("PITCH_BUSINESS", "Your business"), 26) or "Your business"
    detail = clean(os.environ.get("PITCH_DETAIL", ""), 200)
    out = ROOT / "pitches" / f"{number}.svg"
    out.write_text(render(number, user, business, detail))
    rebuild_wall()
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
