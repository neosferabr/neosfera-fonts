"""Atualiza e reconstrói as famílias texturizadas da Neosfera:
- Neosfera Dither (Regular, Bold)
- Neosfera Dither Condensed (Regular, Bold)
- Neosfera Glitch (Regular, Bold + estados 1..4)
- Neosfera Glitch Condensed (Regular, Bold + estados 1..4)
Garantindo 100% de cobertura GF_Latin_Core e conformidade com o Google Fonts (FontBakery)."""
import os, sys, copy, random, hashlib
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.otlLib.builder import buildStatTable
import pathops
from pathops import Path, PathOp

VERSION = 'Version 1.000'
FONT_REV = 1.0
COPY = 'Copyright 2026 The Neosfera Project Authors (https://neosfera.com.br). Based on Albert Sans (Copyright 2021 The Albert Sans Project Authors, https://github.com/usted/Albert-Sans).'
OFL_DESC = 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://scripts.sil.org/OFL'
OFL_URL = 'https://scripts.sil.org/OFL'
VENDOR_URL = 'https://neosfera.com.br'

def rect(x0, y0, x1, y1):
    p = Path(); pen = p.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return p

def path_to_glyph(path):
    rec = RecordingPen(); path.draw(rec)
    ap = AreaPen(); rec.replay(ap)
    tt = TTGlyphPen(None)
    pen2 = Cu2QuPen(tt, max_err=1.0, reverse_direction=False)
    rec.replay(ReverseContourPen(pen2) if ap.value > 0 else pen2)
    return tt.glyph()

def ensure_gf_latin_core(font, is_condensed=False):
    """Adiciona uni0237 (dotlessj), uni1E9E (Germandbls) e fl caso ausentes para 100% GF_Latin_Core."""
    glyf = font['glyf']
    hmtx = font['hmtx']
    gs = font.getGlyphSet()
    order = list(font.getGlyphOrder())

    # 1. uni0237 (dotlessj) a partir do 'j' cortando o pingo acima da altura de x
    if 'uni0237' not in glyf:
        pj = Path(); gs['j'].draw(pj.getPen(glyphSet=gs))
        pj.simplify(fix_winding=True, keep_starting_points=False)
        clip_y = round(530 * (1.06 if is_condensed else 1.0))
        res = pathops.op(pj, rect(-1000, -1000, 2000, clip_y), PathOp.INTERSECTION, fix_winding=True)
        glyf['uni0237'] = path_to_glyph(res)
        hmtx['uni0237'] = hmtx['j']
        order.append('uni0237')

    # 2. uni1E9E (ẞ) a partir de 'germandbls'
    if 'uni1E9E' not in glyf:
        glyf['uni1E9E'] = copy.deepcopy(glyf['germandbls'])
        hmtx['uni1E9E'] = hmtx['germandbls']
        order.append('uni1E9E')

    # 3. fl (0xFB02) a partir de 'f' + 'l'
    if 'fl' not in glyf:
        pf = Path(); gs['f'].draw(pf.getPen(glyphSet=gs))
        pl = Path(); gs['l'].draw(pl.getPen(glyphSet=gs))
        adv_f, _ = hmtx['f']
        adv_l, _ = hmtx['l']
        pl = pl.transform(translateX=adv_f)
        out = Path(); out.addPath(pf); out.addPath(pl)
        out.simplify(fix_winding=True)
        glyf['fl'] = path_to_glyph(out)
        hmtx['fl'] = (adv_f + adv_l, hmtx['f'][1])
        order.append('fl')

    font.setGlyphOrder(order)
    glyf.glyphOrder = order

    for n in ('uni0237', 'uni1E9E', 'fl'):
        g = glyf[n]
        g.recalcBounds(glyf)
        hmtx[n] = (hmtx[n][0], getattr(g, 'xMin', 0) if g.numberOfContours else 0)

    for subtable in font['cmap'].tables:
        if subtable.isUnicode():
            subtable.cmap[0x0237] = 'uni0237'
            subtable.cmap[0x1E9E] = 'uni1E9E'
            subtable.cmap[0xFB02] = 'fl'

def apply_gf_metadata(font, family, sub, is_condensed=False):
    bold = (sub == 'Bold')
    ps_fam = family.replace(' ', '')
    ps = f'{ps_fam}-{sub}'
    full_name = f'{family} {sub}' if sub != 'Regular' else family

    nm = font['name']
    nm.names = []
    entries = {
        0: COPY,
        1: family,
        2: sub,
        3: f'1.000;NEOS;{ps}',
        4: full_name,
        5: VERSION,
        6: ps,
        8: 'Neosfera',
        9: 'Neosfera',
        11: VENDOR_URL,
        12: VENDOR_URL,
        13: OFL_DESC,
        14: OFL_URL,
    }
    for nid, val in entries.items():
        nm.setName(val, nid, 3, 1, 0x409)

    os2 = font['OS/2']
    os2.version = 4
    os2.fsType = 0
    os2.achVendID = 'NEOS'
    os2.usWeightClass = 700 if bold else 400
    os2.usWidthClass = 3 if is_condensed else 5
    os2.fsSelection = (32 if bold else 64) | 128  # USE_TYPO_METRICS
    os2.recalcUnicodeRanges(font)

    font['head'].macStyle = 1 if bold else 0
    font['head'].fontRevision = FONT_REV
    font['post'].formatType = 2.0
    font['post'].isFixedPitch = 0

    gasp = newTable('gasp')
    gasp.version = 1
    gasp.gaspRange = {65535: 0x000F}
    font['gasp'] = gasp

    for t in ('DSIG', 'fpgm', 'prep', 'cvt '):
        if t in font:
            del font[t]

    axes = [dict(tag='wght', name='Weight', ordering=0, values=[
        dict(value=400, name='Regular', flags=0x2, linkedValue=700),
        dict(value=700, name='Bold'),
    ])]
    buildStatTable(font, axes)
    font['name'].names = [r for r in font['name'].names if r.platformID == 3]

def save_ttf_and_woff2(font, ttf_path, woff2_path=None):
    os.makedirs(os.path.dirname(ttf_path) or '.', exist_ok=True)
    font.flavor = None
    font.save(ttf_path)
    if woff2_path:
        os.makedirs(os.path.dirname(woff2_path) or '.', exist_ok=True)
        font.flavor = 'woff2'
        font.save(woff2_path)
        font.flavor = None

def upgrade_dither_font(src_ttf, family, sub, is_condensed, out_ttf, out_woff2):
    font = TTFont(src_ttf)
    ensure_gf_latin_core(font, is_condensed=is_condensed)
    apply_gf_metadata(font, family, sub, is_condensed=is_condensed)
    save_ttf_and_woff2(font, out_ttf, out_woff2)
    return len(font.getGlyphOrder())

# ======================== GLITCH ENGINE ========================
def glitch_path(p, rng, amp):
    xmin, ymin, xmax, ymax = p.bounds
    h = ymax - ymin
    n = 1 if h < 60 else min(rng.choice([3, 4, 4, 5]), max(2, int(h // 70)))
    cuts = []; tries = 0
    while len(cuts) < n - 1 and tries < 80:
        tries += 1
        c = rng.uniform(ymin + 0.12 * h, ymax - 0.12 * h)
        if all(abs(c - o) > 0.1 * h for o in cuts): cuts.append(c)
    cuts.sort()
    edges = [ymin - 5] + cuts + [ymax + 5]
    w = xmax - xmin
    hi = min(115 * amp, 0.28 * w)
    lo = min(28 * amp, hi * 0.4)
    bands = []
    for _ in range(len(edges) - 1):
        r = rng.random()
        if r < 0.32: bands.append([0])
        elif r < 0.91: bands.append([rng.choice([-1, 1]) * rng.uniform(lo, hi)])
        elif r < 0.95: bands.append([])
        else:
            s = rng.choice([-1, 1]) * rng.uniform(lo, hi)
            bands.append([s, -s * rng.uniform(0.5, 1.0)])
    if all(b in ([0], []) for b in bands):
        bands[rng.randrange(len(bands))] = [rng.choice([-1, 1]) * rng.uniform(lo, hi)]
    if all(b == [] for b in bands): bands[0] = [0]
    out = Path()
    for i, shifts in enumerate(bands):
        for s in shifts:
            band = rect(xmin - 800, edges[i], xmax + 800, edges[i + 1])
            sl = pathops.op(p, band, PathOp.INTERSECTION, fix_winding=True, keep_starting_points=False)
            if s: sl = sl.transform(translateX=s)
            out.addPath(sl)
    out.simplify(fix_winding=True, keep_starting_points=False)
    return add_lines(out, rng)

def add_lines(out, rng):
    if not len(list(out.contours)): return out
    xmin, ymin, xmax, ymax = out.bounds
    w, h = xmax - xmin, ymax - ymin
    r1, r2 = rng.random(), rng.random()
    if w < 70 or h < 90: return out
    if r1 < 0.42:
        for _ in range(1 if rng.random() < 0.65 else 2):
            t = rng.uniform(8, 15)
            y = rng.uniform(ymin + 0.08 * h, ymax - 0.08 * h)
            L = rng.uniform(0.45, 1.1) * w
            if rng.random() < 0.5:
                x0 = xmax - rng.uniform(0.1, 0.4) * w; x1 = x0 + L
            else:
                x1 = xmin + rng.uniform(0.1, 0.4) * w; x0 = x1 - L
            out.addPath(rect(x0, y - t / 2, x1, y + t / 2))
        out.simplify(fix_winding=True, keep_starting_points=False)
    if r2 < 0.22:
        t = rng.uniform(7, 12)
        y = rng.uniform(ymin + 0.15 * h, ymax - 0.15 * h)
        cut = rect(xmin - 50, y - t / 2, xmax + 50, y + t / 2)
        out = pathops.op(out, cut, PathOp.DIFFERENCE, fix_winding=True, keep_starting_points=False)
    return out

def make_glitch_glyph(font, gs, name, state, key, amp):
    g0 = font['glyf'][name]
    if state == 0 or g0.numberOfContours == 0:
        return copy.deepcopy(g0)
    p = Path(); gs[name].draw(p.getPen(glyphSet=gs))
    p.simplify(fix_winding=True, keep_starting_points=False)
    if not len(list(p.contours)): return copy.deepcopy(g0)
    seed = int(hashlib.md5(f'{key}|{name}|{state}'.encode()).hexdigest()[:12], 16)
    return path_to_glyph(glitch_path(p, random.Random(seed), amp))

def extend_gpos(font, alt_map):
    if 'GPOS' not in font: return
    for lk in font['GPOS'].table.LookupList.Lookup:
        for st in lk.SubTable:
            if hasattr(st, 'ExtSubTable'): st = st.ExtSubTable
            if hasattr(st, 'ClassDef1') and hasattr(st, 'Coverage'):
                cov = st.Coverage.glyphs; c1 = st.ClassDef1.classDefs; c2 = st.ClassDef2.classDefs
                cs = set(cov)
                for base, alts in alt_map.items():
                    for alt in alts:
                        if base in cs: cov.append(alt)
                        if base in c1: c1[alt] = c1[base]
                        if base in c2: c2[alt] = c2[base]

def finalize_glyf(font):
    glyf = font['glyf']; hmtx = font['hmtx']
    for name in font.getGlyphOrder():
        g = glyf[name]; g.recalcBounds(glyf)
        hmtx[name] = (hmtx[name][0], getattr(g, 'xMin', 0) if g.numberOfContours else 0)

def build_glitch_state(base_path, key, amp, state, family, sub, is_condensed, out_ttf, out_woff2):
    font = TTFont(base_path); gs = font.getGlyphSet()
    glyf = font['glyf']
    new = {n: make_glitch_glyph(font, gs, n, state, key, amp) for n in font.getGlyphOrder()}
    for n, g in new.items(): glyf[n] = g
    finalize_glyf(font)
    apply_gf_metadata(font, family, sub, is_condensed=is_condensed)
    save_ttf_and_woff2(font, out_ttf, out_woff2)

def build_glitch_combined(base_path, key, amp, family, sub, is_condensed, out_ttf, out_woff2):
    font = TTFont(base_path); gs = font.getGlyphSet()
    glyf = font['glyf']; hmtx = font['hmtx']
    order = list(font.getGlyphOrder())
    inked = [n for n in order if glyf[n].numberOfContours]
    states = {1: None, 2: '.g2', 3: '.g3', 4: '.g4', 0: '.clean'}
    new = {}; alt_map = {n: [] for n in inked}
    for state, suf in states.items():
        for n in order:
            g = make_glitch_glyph(font, gs, n, state, key, amp)
            if suf is None: new[n] = g
            elif n in alt_map:
                an = n + suf; new[an] = g; hmtx[an] = hmtx[n]; alt_map[n].append(an)
    newnames = [a for n in inked for a in alt_map[n]]
    font.setGlyphOrder(order + newnames); glyf.glyphOrder = order + newnames
    for n, g in new.items(): glyf[n] = g
    finalize_glyf(font)
    extend_gpos(font, alt_map)
    ss = {'ss01': '.g2', 'ss02': '.g3', 'ss03': '.g4', 'ss04': '.clean'}
    fea = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;']
    for tag, suf in ss.items():
        fea.append(f'feature {tag} {{')
        for n in inked: fea.append(f'  sub {n} by {n}{suf};')
        fea.append(f'}} {tag};')
    addOpenTypeFeaturesFromString(font, '\n'.join(fea), tables=['GSUB'])
    apply_gf_metadata(font, family, sub, is_condensed=is_condensed)
    save_ttf_and_woff2(font, out_ttf, out_woff2)
    return len(font.getGlyphOrder())
