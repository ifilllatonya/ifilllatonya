#!/usr/bin/env python3
"""Generate assets/banner.svg: the animated profile banner.

GitHub strips <script> from README images but renders SMIL, which is how
animated SVG badges work. Everything here is plain SMIL plus an embedded,
subset copy of Inter so the typography is identical on every machine.

    python3 scripts/make_banner.py
"""
import base64
import io
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "banner.svg"
FONT_DIR = pathlib.Path("/usr/share/fonts/opentype/inter")

W, H = 1280, 400
CYCLE = 12.0          # full loop, seconds
FADE_A, FADE_B = 10.4, 11.2   # phones fade out here, then the loop restarts

PINK, PINK_2, VIOLET = "#FF2E9A", "#FF7AC6", "#7B3DFF"
GREEN = "#2BD576"


# --------------------------------------------------------------- fonts
def embed(path, weight, family="Brand"):
    """Subset a font to printable ASCII and return an @font-face rule."""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.desubroutinize = True
    opts.layout_features = ["kern", "liga"]
    sub = subset.Subsetter(options=opts)
    sub.populate(text="".join(chr(c) for c in range(32, 127)))
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


def fonts():
    faces = [
        (FONT_DIR / "InterDisplay-ExtraBold.otf", 800),
        (FONT_DIR / "Inter-SemiBold.otf", 600),
        (FONT_DIR / "Inter-Regular.otf", 400),
    ]
    out = []
    for path, weight in faces:
        if not path.exists():
            print(f"missing {path}, falling back to system fonts", file=sys.stderr)
            return ""
        out.append(embed(path, weight))
    return "".join(out)


# ----------------------------------------------------- SMIL helpers
def _kt(pairs):
    """pairs: [(time_seconds, value), ...] -> keyTimes/values attribute pair."""
    times = ";".join(f"{max(0.0, min(1.0, t / CYCLE)):.5f}" for t, _ in pairs)
    vals = ";".join(str(v) for _, v in pairs)
    return f'keyTimes="{times}" values="{vals}"'


def loop(attr, pairs, extra=""):
    return (f'<animate attributeName="{attr}" dur="{CYCLE}s" '
            f'repeatCount="indefinite" calcMode="spline" '
            f'keySplines="{";".join([".25 .1 .25 1"] * (len(pairs) - 1))}" '
            f'{_kt(pairs)} {extra}/>')


def loop_linear(attr, pairs, extra=""):
    return (f'<animate attributeName="{attr}" dur="{CYCLE}s" '
            f'repeatCount="indefinite" {_kt(pairs)} {extra}/>')


def fade_in(t, d=0.45):
    """Appear at t, stay up for the rest of the cycle."""
    return loop("opacity", [(0, 0), (t, 0), (t + d, 1), (CYCLE, 1)])


def slide_in(t, d, dx, dy=0):
    pairs = [(0, f"{dx} {dy}"), (t, f"{dx} {dy}"), (t + d, "0 0"), (CYCLE, "0 0")]
    return (f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{CYCLE}s" repeatCount="indefinite" calcMode="spline" '
            f'keySplines="{";".join([".16 .84 .3 1"] * 3)}" {_kt(pairs)}/>')


def once(attr, frm, to, begin, dur, extra=""):
    return (f'<animate attributeName="{attr}" from="{frm}" to="{to}" '
            f'begin="{begin}s" dur="{dur}s" fill="freeze" '
            f'calcMode="spline" keySplines=".2 .7 .3 1" {extra}/>')


def once_shift(dx, dy, begin, dur):
    return (f'<animateTransform attributeName="transform" type="translate" '
            f'from="{dx} {dy}" to="0 0" begin="{begin}s" dur="{dur}s" '
            f'fill="freeze" calcMode="spline" keySplines=".16 .84 .3 1"/>')


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


# ------------------------------------------------------------- phone
PHONE_W, PHONE_H = 184, 272
PERIM = 2 * (PHONE_W + PHONE_H) - 8 * 30 + 2 * 3.1416 * 30  # rounded rect


def phone(idx, x, y, rot, scale, opacity, title, rows, cta, t0, accent=False):
    """One phone that draws itself, fills in, then lights up its button."""
    hw, hh = PHONE_W / 2, PHONE_H / 2
    s = [f'<g transform="translate({x} {y}) rotate({rot} {hw} {hh}) '
         f'translate({hw} {hh}) scale({scale}) translate({-hw} {-hh})" '
         f'opacity="{opacity}">']

    # group-level exit so nothing snaps when the loop restarts
    s.append(f'<g>{loop_linear("opacity", [(0,1),(FADE_A,1),(FADE_B,0),(CYCLE,0)])}')

    stroke = f"url(#edge{idx})" if accent else "rgba(255,255,255,.14)"

    # 1. the outline draws itself
    s.append(f'<rect width="{PHONE_W}" height="{PHONE_H}" rx="30" fill="none" '
             f'stroke="{stroke}" stroke-width="2" stroke-dasharray="{PERIM:.0f}" '
             f'stroke-linecap="round">'
             f'{loop("stroke-dashoffset", [(0, f"{PERIM:.0f}"), (t0, f"{PERIM:.0f}"), (t0+1.0, 0), (CYCLE, 0)])}'
             f'</rect>')

    # 2. the body fills in behind it
    s.append(f'<rect width="{PHONE_W}" height="{PHONE_H}" rx="30" fill="#0E1120" '
             f'opacity="0">{fade_in(t0 + 0.75, 0.45)}</rect>')
    s.append(f'<rect width="{PHONE_W}" height="{PHONE_H}" rx="30" fill="none" '
             f'stroke="{stroke}" stroke-width="2" opacity="0">{fade_in(t0 + 0.9, 0.3)}</rect>')
    s.append(f'<rect x="66" y="9" width="52" height="14" rx="8" fill="#000" opacity="0">'
             f'{fade_in(t0 + 0.9, 0.3)}</rect>')

    # 3. title and its underline
    s.append(f'<g opacity="0">{fade_in(t0 + 1.05, 0.35)}'
             f'<text x="15" y="48" font-size="12.5" font-weight="800" fill="#fff">{esc(title)}</text>'
             f'</g>')
    s.append(f'<rect x="15" y="56" height="2.5" rx="1.5" fill="{PINK}" width="0">'
             f'{loop("width", [(0,0),(t0+1.15,0),(t0+1.5,22),(CYCLE,22)])}</rect>')

    # 4. rows slide in one at a time
    ry = 72
    for i, (t1, t2) in enumerate(rows):
        at = t0 + 1.35 + i * 0.3
        s.append(f'<g opacity="0">{fade_in(at, 0.3)}'
                 f'<g>{slide_in(at, 0.55, 26)}'
                 f'<rect x="15" y="{ry}" width="154" height="38" rx="9" fill="#161B2E" '
                 f'stroke="#242B42"/>'
                 f'<rect x="15" y="{ry}" width="2.5" height="38" rx="1.5" fill="{PINK}"/>'
                 f'<circle cx="33" cy="{ry+19}" r="8.5" fill="{PINK}" opacity=".18"/>'
                 f'<circle cx="33" cy="{ry+19}" r="3" fill="{PINK}"/>'
                 f'<text x="48" y="{ry+16}" font-size="8.6" font-weight="600" fill="#E9EEFB">{esc(t1)}</text>'
                 f'<text x="48" y="{ry+27}" font-size="7" fill="#8794B2">{esc(t2)}</text>'
                 f'</g></g>')
        ry += 45

    # 5. the call to action pops in
    bt = t0 + 2.45
    py = ry + 15
    s.append(f'<g opacity="0">{fade_in(bt, 0.3)}'
             f'<g transform="translate(92 {py})">'
             f'<g><animateTransform attributeName="transform" type="scale" dur="{CYCLE}s" '
             f'repeatCount="indefinite" calcMode="spline" '
             f'keySplines=".2 1.6 .4 1;.2 1.6 .4 1;0 0 1 1" '
             f'{_kt([(0,.82),(bt,.82),(bt+0.45,1),(CYCLE,1)])}/>'
             f'<g transform="translate(-92 {-py})">'
             f'<rect x="15" y="{ry+2}" width="154" height="26" rx="9" fill="url(#cta{idx})"/>'
             f'<text x="92" y="{ry+19}" text-anchor="middle" font-size="9.5" '
             f'font-weight="800" fill="#12020A">{esc(cta)}</text>'
             f'</g></g></g></g>')

    # 6. a light sweeps down the finished screen
    s.append(f'<g clip-path="url(#clip{idx})" opacity="0">{fade_in(t0 + 2.7, 0.2)}'
             f'<rect x="0" y="-70" width="{PHONE_W}" height="70" fill="url(#scan)">'
             f'{loop_linear("y", [(0,-70),(t0+2.7,-70),(t0+3.9,PHONE_H),(CYCLE,PHONE_H)])}'
             f'</rect></g>')

    s.append("</g></g>")
    return "".join(s)


# -------------------------------------------------------------- build
def build():
    css = fonts()
    F = "Brand, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{F}">']

    s.append("<defs>")
    if css:
        s.append(f"<style>{css}</style>")
    s.append(f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_2}"/></linearGradient>')
    s.append(f'<linearGradient id="hair" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{PINK}"/><stop offset=".32" stop-color="{PINK_2}"/>'
             f'<stop offset=".62" stop-color="{VIOLET}"/><stop offset=".94" stop-color="{VIOLET}" stop-opacity="0"/>'
             f'</linearGradient>')
    s.append(f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="#fff" stop-opacity=".85"/>'
             f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    s.append(f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{PINK}" stop-opacity="0"/>'
             f'<stop offset=".82" stop-color="{PINK}" stop-opacity=".16"/>'
             f'<stop offset="1" stop-color="{PINK_2}" stop-opacity=".5"/></linearGradient>')
    for i in range(3):
        s.append(f'<linearGradient id="cta{i}" x1="0" y1="0" x2="1" y2="0">'
                 f'<stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_2}"/></linearGradient>')
        s.append(f'<linearGradient id="edge{i}" x1="0" y1="0" x2="1" y2="1">'
                 f'<stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_2}"/></linearGradient>')
        s.append(f'<clipPath id="clip{i}"><rect width="{PHONE_W}" height="{PHONE_H}" rx="30"/></clipPath>')
    s.append(f'<radialGradient id="glowA"><stop offset="0" stop-color="{PINK}" stop-opacity=".30"/>'
             f'<stop offset=".45" stop-color="{PINK}" stop-opacity=".07"/>'
             f'<stop offset="1" stop-color="{PINK}" stop-opacity="0"/></radialGradient>')
    s.append(f'<radialGradient id="glowB"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".22"/>'
             f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>')
    s.append('<pattern id="grid" width="38" height="38" patternUnits="userSpaceOnUse">'
             '<path d="M38 0H0V38" fill="none" stroke="rgba(255,255,255,.04)" stroke-width="1"/></pattern>')
    s.append(f'<linearGradient id="gridmask" x1="0" y1="0" x2="1" y2=".55">'
             f'<stop offset=".14" stop-color="#fff"/><stop offset=".72" stop-color="#000"/></linearGradient>')
    s.append('<mask id="gm"><rect width="100%" height="100%" fill="url(#gridmask)"/></mask>')
    s.append("</defs>")

    # backdrop
    s.append(f'<rect width="{W}" height="{H}" fill="#06070C"/>')
    s.append(f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gm)"/>')
    s.append(f'<ellipse cx="1140" cy="20" rx="470" ry="440" fill="url(#glowA)">'
             f'<animate attributeName="opacity" values=".75;1;.75" dur="6s" repeatCount="indefinite"/></ellipse>')
    s.append(f'<ellipse cx="80" cy="400" rx="330" ry="310" fill="url(#glowB)">'
             f'<animate attributeName="opacity" values="1;.6;1" dur="7.5s" repeatCount="indefinite"/></ellipse>')

    # ---- left column, animates in once and stays ----
    s.append('<g>')
    s.append(f'<g opacity="0">{once("opacity",0,1,0.15,0.6)}<g>{once_shift(-22,0,0.15,0.7)}'
             f'<circle cx="76" cy="105" r="3.6" fill="{PINK}"/>'
             f'<circle cx="76" cy="105" r="3.6" fill="{PINK}" opacity=".55">'
             f'<animate attributeName="r" values="3.6;9;3.6" dur="2.6s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values=".55;0;.55" dur="2.6s" repeatCount="indefinite"/></circle>'
             f'<text x="92" y="110" font-size="12.5" font-weight="800" letter-spacing="3.4" '
             f'fill="#FF6FBE">TEMPLATE CRAFT LLC</text></g></g>')

    s.append(f'<g opacity="0">{once("opacity",0,1,0.35,0.7)}<g>{once_shift(0,26,0.35,0.85)}'
             f'<text x="72" y="208" font-size="67" font-weight="800" letter-spacing="-2.4" '
             f'fill="#fff">Latonya Ifill</text></g></g>')

    s.append(f'<rect x="72" y="232" height="5" rx="2.5" fill="url(#bar)" width="0">'
             f'{once("width",0,92,0.75,0.6)}</rect>')

    tag = [("Mobile apps and websites for churches,", "#AEB8D0", 400),
           ("businesses and creators. I design it, I code it,", "#F2F5FF", 600),
           ("and I ship it to the store myself.", "#F2F5FF", 600)]
    for i, (line, col, wt) in enumerate(tag):
        s.append(f'<g opacity="0">{once("opacity",0,1,0.95 + i*0.12,0.6)}<g>{once_shift(0,12,0.95+i*0.12,0.7)}'
                 f'<text x="72" y="{282 + i*30}" font-size="20" font-weight="{wt}" fill="{col}">{esc(line)}</text>'
                 f'</g></g>')

    chips = ["React Native", "Expo", "TypeScript", "NestJS", "PostgreSQL", "Stripe"]
    cx = 72
    for i, c in enumerate(chips):
        w = 15 + len(c) * 7.3
        s.append(f'<g opacity="0">{once("opacity",0,1,1.35 + i*0.07,0.5)}<g>{once_shift(0,10,1.35+i*0.07,0.6)}'
                 f'<rect x="{cx:.0f}" y="358" width="{w:.0f}" height="29" rx="14.5" '
                 f'fill="rgba(255,255,255,.045)" stroke="rgba(255,255,255,.1)"/>'
                 f'<text x="{cx + w/2:.0f}" y="377" text-anchor="middle" font-size="11.5" '
                 f'font-weight="600" fill="#C9D2E6">{esc(c)}</text></g></g>')
        cx += w + 8
    s.append("</g>")

    # ---- the three phones, each building itself, then looping ----
    s.append(phone(0, 694, 70, -8, 0.88, 0.74, "Jesus Camp Resort",
                   [("Book a stay", "Pick your dates"), ("Pay a deposit", "Secure checkout"),
                    ("Your trip", "All in one place")], "Reserve", 0.5))
    s.append(phone(1, 856, 56, -2, 0.96, 0.90, "COGTB Temple",
                   [("This week", "Events and news"), ("Give", "Secure, one tap"),
                    ("Watch live", "Sunday service")], "Open", 1.25))
    s.append(phone(2, 1018, 44, 5, 1.0, 1.0, "JCCOGTB District",
                   [("Members", "Directory and chat"), ("Livestream", "Watch from anywhere"),
                    ("Announcements", "Push to every phone")], "Enter", 2.0, accent=True))

    # ---- the stamp: LIVE IN THE APP STORE ----
    st = 5.5
    s.append(f'<g opacity="0">{loop_linear("opacity",[(0,0),(st,0),(st+0.25,1),(FADE_A,1),(FADE_B,0),(CYCLE,0)])}'
             f'<g transform="translate(1105 356)"><g>'
             f'<animateTransform attributeName="transform" type="scale" dur="{CYCLE}s" '
             f'repeatCount="indefinite" calcMode="spline" keySplines=".1 1.9 .4 1;0 0 1 1;0 0 1 1" '
             f'{_kt([(0,1.5),(st,1.5),(st+0.5,1),(CYCLE,1)])}/>'
             f'<g transform="translate(-1105 -356)">'
             f'<rect x="968" y="338" width="274" height="36" rx="18" fill="rgba(43,213,118,.1)" '
             f'stroke="rgba(43,213,118,.45)" stroke-width="1.5"/>'
             f'<circle cx="992" cy="356" r="4.5" fill="{GREEN}">'
             f'<animate attributeName="opacity" values="1;.25;1" dur="1.8s" repeatCount="indefinite"/></circle>'
             f'<text x="1008" y="361" font-size="12.5" font-weight="800" letter-spacing="2.1" '
             f'fill="#8FE9B7">LIVE IN THE APP STORE</text></g></g></g></g>')

    # ---- bottom hairline with a travelling highlight ----
    s.append(f'<rect y="{H-3}" width="{W}" height="3" fill="url(#hair)"/>')
    s.append(f'<rect y="{H-3}" width="260" height="3" fill="url(#shine)" opacity=".9">'
             f'<animate attributeName="x" values="-260;{W}" dur="4.5s" repeatCount="indefinite"/></rect>')

    s.append("</svg>")
    return "".join(s)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT}  {OUT.stat().st_size // 1024} KB")
