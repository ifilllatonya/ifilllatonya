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
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "banner.svg"
FONT_DIR = pathlib.Path("/usr/share/fonts/opentype/inter")

W, H = 1280, 400
CYCLE = 14.0
FADE_A, FADE_B = 12.1, 12.9

PINK, PINK_2, VIOLET = "#FF2E9A", "#FF7AC6", "#7B3DFF"
GREEN = "#2BD576"
PHONE_W, PHONE_H = 150, 325
PERIM = 1000


# --------------------------------------------------------------- fonts
def embed(path, weight, family="Brand"):
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
    faces = [(FONT_DIR / "InterDisplay-ExtraBold.otf", 800),
             (FONT_DIR / "Inter-SemiBold.otf", 600),
             (FONT_DIR / "Inter-Regular.otf", 400)]
    out = []
    for path, weight in faces:
        if not path.exists():
            print(f"missing {path}, using system fonts", file=sys.stderr)
            return ""
        out.append(embed(path, weight))
    return "".join(out)


def screen_uri(name):
    """Inline a screenshot. SVG loaded as an image cannot fetch external files."""
    raw = (ROOT / "assets" / "screens" / name).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()

# ----------------------------------------------------- SMIL helpers
def _kt(pairs):
    times = ";".join(f"{max(0.0, min(1.0, t / CYCLE)):.5f}" for t, _ in pairs)
    vals = ";".join(str(v) for _, v in pairs)
    return f'keyTimes="{times}" values="{vals}"'


def loop(attr, pairs):
    sp = ";".join([".25 .1 .25 1"] * (len(pairs) - 1))
    return (f'<animate attributeName="{attr}" dur="{CYCLE}s" repeatCount="indefinite" '
            f'calcMode="spline" keySplines="{sp}" {_kt(pairs)}/>')


def loop_lin(attr, pairs):
    return (f'<animate attributeName="{attr}" dur="{CYCLE}s" repeatCount="indefinite" '
            f'{_kt(pairs)}/>')


def loop_tx(pairs, kind="translate"):
    sp = ";".join([".16 .84 .3 1"] * (len(pairs) - 1))
    return (f'<animateTransform attributeName="transform" type="{kind}" dur="{CYCLE}s" '
            f'repeatCount="indefinite" calcMode="spline" keySplines="{sp}" {_kt(pairs)}/>')


def fade_in(t, d=0.45):
    return loop("opacity", [(0, 0), (t, 0), (t + d, 1), (CYCLE, 1)])


def slide_in(t, d, dx, dy=0):
    return loop_tx([(0, f"{dx} {dy}"), (t, f"{dx} {dy}"), (t + d, "0 0"), (CYCLE, "0 0")])


def once(attr, frm, to, begin, dur):
    return (f'<animate attributeName="{attr}" from="{frm}" to="{to}" begin="{begin}s" '
            f'dur="{dur}s" fill="freeze" calcMode="spline" keySplines=".2 .7 .3 1"/>')


def once_shift(dx, dy, begin, dur):
    return (f'<animateTransform attributeName="transform" type="translate" from="{dx} {dy}" '
            f'to="0 0" begin="{begin}s" dur="{dur}s" fill="freeze" calcMode="spline" '
            f'keySplines=".16 .84 .3 1"/>')


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


# ------------------------------------------------------------- phone
def phone(idx, x, y, rot, scale, opacity, shot, t0,
          accent=False, bob=5.0, phase=0.0, tap=False):
    """A device that draws its own outline, then wakes up showing a real screen."""
    hw, hh = PHONE_W / 2, PHONE_H / 2
    s = []
    # continuous float, so nothing on the canvas is ever completely still
    s.append(f'<g><animateTransform attributeName="transform" type="translate" '
             f'values="0 0;0 -7;0 0;0 5;0 0" dur="{bob}s" begin="{-phase}s" '
             f'repeatCount="indefinite" calcMode="spline" '
             f'keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/>')
    s.append(f'<g transform="translate({x} {y}) rotate({rot} {hw} {hh}) '
             f'translate({hw} {hh}) scale({scale}) translate({-hw} {-hh})" opacity="{opacity}">')
    s.append(f'<g>{loop_lin("opacity", [(0,1),(FADE_A,1),(FADE_B,0),(CYCLE,0)])}')

    stroke = f"url(#edge{idx})" if accent else "rgba(255,255,255,.16)"

    # 1. the outline draws itself
    s.append(f'<rect width="{PHONE_W}" height="{PHONE_H}" rx="26" fill="none" stroke="{stroke}" '
             f'stroke-width="2" stroke-dasharray="{PERIM}" stroke-linecap="round">'
             f'{loop("stroke-dashoffset", [(0,PERIM),(t0,PERIM),(t0+1.0,0),(CYCLE,0)])}</rect>')
    # 2. dark glass behind the screen
    s.append(f'<rect width="{PHONE_W}" height="{PHONE_H}" rx="26" fill="#0B0E18" opacity="1">'
             f'{fade_in(t0+0.7, 0.4)}</rect>')
    # 3. the real screen wipes down into place
    s.append(f'<g clip-path="url(#wipe{idx})">'
             f'<image href="{screen_uri(shot)}" x="3" y="3" width="{PHONE_W-6}" height="{PHONE_H-6}" '
             f'preserveAspectRatio="xMidYMin slice" clip-path="url(#inner{idx})"/></g>')
    # 4. the frame sits on top
    s.append(f'<rect width="{PHONE_W}" height="{PHONE_H}" rx="26" fill="none" stroke="{stroke}" '
             f'stroke-width="2.5" opacity="1">{fade_in(t0+0.9, 0.3)}</rect>')
    s.append(f'<rect x="{hw-22}" y="{PHONE_H-11}" width="44" height="3.5" rx="2" fill="#fff" '
             f'opacity=".4">{loop("opacity",[(0,0),(t0+1.4,0),(t0+1.7,.4),(CYCLE,.4)])}</rect>')
    # 5. a finger taps the screen
    if tap:
        tt, ty = t0 + 3.1, PHONE_H - 72
        s.append(f'<circle cx="{hw}" cy="{ty}" r="6" fill="none" stroke="#fff" stroke-width="2.5" opacity="0">'
                 f'{loop_lin("r", [(0,6),(tt,6),(tt+0.8,52),(CYCLE,52)])}'
                 f'{loop_lin("opacity", [(0,0),(tt,.8),(tt+0.8,0),(CYCLE,0)])}</circle>')
        s.append(f'<g opacity="0">{loop_lin("opacity",[(0,0),(tt-0.7,0),(tt-0.45,1),(tt+0.5,1),(tt+0.8,0),(CYCLE,0)])}'
                 f'<g>{loop_tx([(0,"44 46"),(tt-0.7,"44 46"),(tt,"0 0"),(CYCLE,"0 0")])}'
                 f'<circle cx="{hw}" cy="{ty}" r="12" fill="#fff" opacity=".16"/>'
                 f'<circle cx="{hw}" cy="{ty}" r="5.5" fill="#fff" opacity=".92"/></g></g>')
    # 6. light sweeps the woken screen
    s.append(f'<g clip-path="url(#inner{idx})" opacity="0">{fade_in(t0+2.0, 0.2)}'
             f'<rect x="0" y="-80" width="{PHONE_W}" height="80" fill="url(#scan)">'
             f'{loop_lin("y", [(0,-80),(t0+2.0,-80),(t0+3.4,PHONE_H),(CYCLE,PHONE_H)])}</rect></g>')
    s.append("</g></g></g>")
    return "".join(s)


# -------------------------------------------------------------- build
def build():
    css = fonts()
    F = "Brand, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{F}">']

    s.append("<defs>")
    if css:
        s.append(f"<style>{css}</style>")
    s.append(f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_2}"/></linearGradient>')
    s.append(f'<linearGradient id="hair" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{PINK}"/><stop offset=".32" stop-color="{PINK_2}"/>'
             f'<stop offset=".62" stop-color="{VIOLET}"/>'
             f'<stop offset=".94" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>')
    s.append('<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
             '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#fff" stop-opacity=".85"/>'
             '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    s.append(f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{PINK}" stop-opacity="0"/>'
             f'<stop offset=".82" stop-color="{PINK}" stop-opacity=".16"/>'
             f'<stop offset="1" stop-color="{PINK_2}" stop-opacity=".5"/></linearGradient>')
    s.append(f'<linearGradient id="stampshine" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{GREEN}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="#CFFFE4" stop-opacity=".55"/>'
             f'<stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>')
    for i in range(3):
        s.append(f'<linearGradient id="cta{i}" x1="0" y1="0" x2="1" y2="0">'
                 f'<stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_2}"/></linearGradient>')
        s.append(f'<linearGradient id="edge{i}" x1="0" y1="0" x2="1" y2="1">'
                 f'<stop offset="0" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK_2}"/></linearGradient>')
        s.append(f'<clipPath id="inner{i}"><rect x="3" y="3" width="{PHONE_W-6}" '
                 f'height="{PHONE_H-6}" rx="23"/></clipPath>')
        _t0 = (0.5, 1.25, 2.0)[i]
        s.append(f'<clipPath id="wipe{i}"><rect width="{PHONE_W}" height="{PHONE_H}">'
                 f'{loop("height", [(0,0),(_t0+0.8,0),(_t0+1.7,PHONE_H),(CYCLE,PHONE_H)])}'
                 f'</rect></clipPath>')
    s.append(f'<radialGradient id="glowA"><stop offset="0" stop-color="{PINK}" stop-opacity=".30"/>'
             f'<stop offset=".45" stop-color="{PINK}" stop-opacity=".07"/>'
             f'<stop offset="1" stop-color="{PINK}" stop-opacity="0"/></radialGradient>')
    s.append(f'<radialGradient id="glowB"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".22"/>'
             f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>')
    s.append('<pattern id="grid" width="38" height="38" patternUnits="userSpaceOnUse">'
             '<path d="M38 0H0V38" fill="none" stroke="rgba(255,255,255,.04)" stroke-width="1"/></pattern>')
    s.append('<linearGradient id="gridmask" x1="0" y1="0" x2="1" y2=".55">'
             '<stop offset=".14" stop-color="#fff"/><stop offset=".72" stop-color="#000"/></linearGradient>')
    s.append('<mask id="gm"><rect width="100%" height="100%" fill="url(#gridmask)"/></mask>')
    s.append('<clipPath id="stampclip"><rect x="968" y="9" width="274" height="34" rx="17"/></clipPath>')
    s.append("</defs>")

    s.append(f'<rect width="{W}" height="{H}" fill="#06070C"/>')
    s.append(f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gm)"/>')
    s.append('<ellipse cx="1140" cy="20" rx="470" ry="440" fill="url(#glowA)">'
             '<animate attributeName="opacity" values=".7;1;.7" dur="6s" repeatCount="indefinite"/></ellipse>')
    s.append('<ellipse cx="80" cy="400" rx="330" ry="310" fill="url(#glowB)">'
             '<animate attributeName="opacity" values="1;.55;1" dur="7.5s" repeatCount="indefinite"/></ellipse>')

    # embers drifting up through the glow
    for i, (ex, ey, d, dl, r) in enumerate([(980, 330, 9, 0, 1.8), (1105, 360, 11, 2.5, 1.4),
                                            (1215, 320, 10, 5, 1.6), (900, 370, 12, 7.5, 1.2),
                                            (1050, 345, 8.5, 1.2, 1.3), (1170, 375, 13, 4, 1.5)]):
        s.append(f'<circle cx="{ex}" cy="{ey}" r="{r}" fill="{PINK_2}" opacity="0">'
                 f'<animate attributeName="cy" values="{ey};{ey-300}" dur="{d}s" begin="{dl}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.55;.4;0" dur="{d}s" begin="{dl}s" repeatCount="indefinite"/>'
                 f'</circle>')

    # ---- left column: animates in once, then stays ----
    s.append(f'<g opacity="1">{once("opacity",0,1,0.15,0.6)}<g>{once_shift(-22,0,0.15,0.7)}'
             f'<circle cx="76" cy="105" r="3.6" fill="{PINK}"/>'
             f'<circle cx="76" cy="105" r="3.6" fill="{PINK}" opacity=".55">'
             f'<animate attributeName="r" values="3.6;9;3.6" dur="2.6s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values=".55;0;.55" dur="2.6s" repeatCount="indefinite"/></circle>'
             f'<text x="92" y="110" font-size="12.5" font-weight="800" letter-spacing="3.4" '
             f'fill="#FF6FBE">TEMPLATE CRAFT LLC</text></g></g>')
    s.append(f'<g opacity="1">{once("opacity",0,1,0.35,0.7)}<g>{once_shift(0,26,0.35,0.85)}'
             f'<text x="72" y="208" font-size="67" font-weight="800" letter-spacing="-2.4" '
             f'fill="#fff">Latonya Ifill</text></g></g>')
    s.append(f'<rect x="72" y="232" height="5" rx="2.5" fill="url(#bar)" width="92">'
             f'{once("width",0,92,0.75,0.6)}</rect>')
    for i, (line, col, wt) in enumerate([
            ("Mobile apps and websites for churches,", "#AEB8D0", 400),
            ("businesses and creators. I design it, I code it,", "#F2F5FF", 600),
            ("and I ship it to the store myself.", "#F2F5FF", 600)]):
        s.append(f'<g opacity="1">{once("opacity",0,1,0.95+i*0.12,0.6)}<g>{once_shift(0,12,0.95+i*0.12,0.7)}'
                 f'<text x="72" y="{282+i*30}" font-size="20" font-weight="{wt}" fill="{col}">{esc(line)}</text>'
                 f'</g></g>')
    cx = 72
    for i, c in enumerate(["React Native", "Expo", "TypeScript", "NestJS", "PostgreSQL", "Stripe"]):
        w = 15 + len(c) * 7.3
        s.append(f'<g opacity="1">{once("opacity",0,1,1.35+i*0.07,0.5)}<g>{once_shift(0,10,1.35+i*0.07,0.6)}'
                 f'<rect x="{cx:.0f}" y="356" width="{w:.0f}" height="29" rx="14.5" '
                 f'fill="rgba(255,255,255,.045)" stroke="rgba(255,255,255,.1)"/>'
                 f'<text x="{cx+w/2:.0f}" y="375" text-anchor="middle" font-size="11.5" '
                 f'font-weight="600" fill="#C9D2E6">{esc(c)}</text></g></g>')
        cx += w + 8

    # ---- three phones building themselves, the front one gets used ----
    s.append(phone(0, 742, 62, -7, 0.88, 0.80, "give.jpg", 0.5, bob=5.6, phase=0.0))
    s.append(phone(1, 876, 58, -2, 0.94, 0.92, "announcements.jpg", 1.25, bob=6.4, phase=1.9))
    s.append(phone(2, 1012, 54, 5, 1.0, 1.0, "home.jpg", 2.0,
                   accent=True, bob=5.0, phase=3.4, tap=True))

    # ---- the stamp ----
    st = 7.3
    s.append(f'<g opacity="1">{loop_lin("opacity",[(0,0),(st,0),(st+0.25,1),(FADE_A,1),(FADE_B,0),(CYCLE,0)])}'
             f'<g transform="translate(1105 26)"><g>'
             f'<animateTransform attributeName="transform" type="scale" dur="{CYCLE}s" '
             f'repeatCount="indefinite" calcMode="spline" keySplines=".1 1.9 .4 1;0 0 1 1;0 0 1 1" '
             f'{_kt([(0,1.5),(st,1.5),(st+0.5,1),(CYCLE,1)])}/>'
             f'<g transform="translate(-1105 -26)">'
             f'<rect x="968" y="9" width="274" height="34" rx="17" fill="rgba(43,213,118,.1)" '
             f'stroke="rgba(43,213,118,.45)" stroke-width="1.5"/>'
             f'<g clip-path="url(#stampclip)"><rect y="9" width="120" height="34" fill="url(#stampshine)">'
             f'<animate attributeName="x" values="900;1250" dur="2.4s" begin="{st+0.6}s" '
             f'repeatCount="indefinite"/></rect></g>'
             f'<circle cx="992" cy="26" r="4.5" fill="{GREEN}">'
             f'<animate attributeName="opacity" values="1;.25;1" dur="1.8s" repeatCount="indefinite"/></circle>'
             f'<text x="1008" y="31" font-size="12.5" font-weight="800" letter-spacing="2.1" '
             f'fill="#8FE9B7">LIVE IN THE APP STORE</text></g></g></g></g>')

    s.append(f'<rect y="{H-3}" width="{W}" height="3" fill="url(#hair)"/>')
    s.append(f'<rect y="{H-3}" width="260" height="3" fill="url(#shine)" opacity=".9">'
             f'<animate attributeName="x" values="-260;{W}" dur="4.5s" repeatCount="indefinite"/></rect>')
    s.append("</svg>")
    return "".join(s)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT}  {OUT.stat().st_size // 1024} KB")
