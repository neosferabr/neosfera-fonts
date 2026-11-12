"""Neosfera Glitch: fatia os contornos (ja com dither) em faixas horizontais deslocadas.
Estados: 1..4 = glitch (sementes diferentes), 0 = limpo.
Fonte combinada: padrao = glitch 1; ss01 = glitch 2; ss02 = glitch 3; ss03 = glitch 4; ss04 = limpo.
Tambem gera cada estado como arquivo avulso (para ferramentas sem recursos OpenType)."""
import sys, os, copy, random, hashlib
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
import pathops
from pathops import Path, PathOp

def rect(x0, y0, x1, y1):
    p = Path(); pen = p.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return p

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
    hi = min(115 * amp, 0.28 * w)                  # desloca no maximo ~28% da largura da letra
    lo = min(28 * amp, hi * 0.4)
    bands = []
    for _ in range(len(edges) - 1):
        r = rng.random()
        if r < 0.32: bands.append([0])
        elif r < 0.91: bands.append([rng.choice([-1, 1]) * rng.uniform(lo, hi)])
        elif r < 0.95: bands.append([])                       # faixa que some
        else:
            s = rng.choice([-1, 1]) * rng.uniform(lo, hi)     # faixa com eco
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
    """linhas horizontais finas (so em parte dos glifos): riscos que saem da letra e fendas que cortam."""
    if not len(list(out.contours)): return out
    xmin, ymin, xmax, ymax = out.bounds
    w, h = xmax - xmin, ymax - ymin
    r1, r2 = rng.random(), rng.random()          # sorteios sempre consumidos
    if w < 70 or h < 90: return out
    if r1 < 0.42:                                  # riscos finos
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
    if r2 < 0.22:                                  # fenda fina que corta a letra
        t = rng.uniform(7, 12)
        y = rng.uniform(ymin + 0.15 * h, ymax - 0.15 * h)
        cut = rect(xmin - 50, y - t / 2, xmax + 50, y + t / 2)
        out = pathops.op(out, cut, PathOp.DIFFERENCE, fix_winding=True, keep_starting_points=False)
    return out

def path_to_glyph(path):
    rec = RecordingPen(); path.draw(rec)
    ap = AreaPen(); rec.replay(ap)
    tt = TTGlyphPen(None)
    pen2 = Cu2QuPen(tt, max_err=1.0, reverse_direction=False)
    rec.replay(ReverseContourPen(pen2) if ap.value > 0 else pen2)
    return tt.glyph()

def make_glyph(font, gs, name, state, key, amp):
    g0 = font['glyf'][name]
    if state == 0 or g0.numberOfContours == 0:
        return copy.deepcopy(g0)
    p = Path(); gs[name].draw(p.getPen(glyphSet=gs))
    p.simplify(fix_winding=True, keep_starting_points=False)
    if not len(list(p.contours)): return copy.deepcopy(g0)
    seed = int(hashlib.md5(f'{key}|{name}|{state}'.encode()).hexdigest()[:12], 16)
    return path_to_glyph(glitch_path(p, random.Random(seed), amp))

def set_names(font, family, sub, ps, version='Version 0.1'):
    nm = font['name']
    for nid in (1, 2, 3, 4, 5, 6, 16, 17, 21, 22, 25): nm.removeNames(nameID=nid)
    entries = {1: family, 2: sub, 3: f'0.1;NEOS;{ps}', 4: f'{family} {sub}', 5: version, 6: ps}
    for nid, s in entries.items():
        nm.setName(s, nid, 3, 1, 0x409); nm.setName(s, nid, 1, 0, 0)

def extend_gpos(font, alt_map):
    """alts herdam o kerning de classe da letra base."""
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

def finalize(font, bold):
    glyf = font['glyf']; hmtx = font['hmtx']
    for name in font.getGlyphOrder():
        g = glyf[name]; g.recalcBounds(glyf)
        hmtx[name] = (hmtx[name][0], getattr(g, 'xMin', 0) if g.numberOfContours else 0)

def build_state(base_path, key, amp, state, family, sub, out_path):
    font = TTFont(base_path); gs = font.getGlyphSet()
    glyf = font['glyf']
    new = {n: make_glyph(font, gs, n, state, key, amp) for n in font.getGlyphOrder()}
    for n, g in new.items(): glyf[n] = g
    finalize(font, sub == 'Bold')
    set_names(font, family, sub, f"{family.replace(' ', '')}-{sub}")
    font.save(out_path)

def build_combined(base_path, key, amp, family, sub, out_path):
    font = TTFont(base_path); gs = font.getGlyphSet()
    glyf = font['glyf']; hmtx = font['hmtx']
    order = list(font.getGlyphOrder())
    inked = [n for n in order if glyf[n].numberOfContours]
    states = {1: None, 2: '.g2', 3: '.g3', 4: '.g4', 0: '.clean'}
    new = {}; alt_map = {n: [] for n in inked}
    for state, suf in states.items():
        for n in order:
            g = make_glyph(font, gs, n, state, key, amp)
            if suf is None: new[n] = g
            elif n in alt_map:
                an = n + suf; new[an] = g; hmtx[an] = hmtx[n]; alt_map[n].append(an)
    newnames = [a for n in inked for a in alt_map[n]]
    font.setGlyphOrder(order + newnames); glyf.glyphOrder = order + newnames
    for n, g in new.items(): glyf[n] = g
    finalize(font, sub == 'Bold')
    extend_gpos(font, alt_map)
    ss = {'ss01': '.g2', 'ss02': '.g3', 'ss03': '.g4', 'ss04': '.clean'}
    fea = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;']
    for tag, suf in ss.items():
        fea.append(f'feature {tag} {{')
        for n in inked: fea.append(f'  sub {n} by {n}{suf};')
        fea.append(f'}} {tag};')
    addOpenTypeFeaturesFromString(font, '\n'.join(fea), tables=['GSUB'])
    set_names(font, family, sub, f"{family.replace(' ', '')}-{sub}")
    font.save(out_path)

BASES = [  # arquivo base, chave, amplitude, familia combinada, estilo
    ('Neosfera-Regular.ttf', 'nr', 0.5, 'Neosfera Glitch', 'Regular'),
    ('Neosfera-Bold.ttf', 'nb', 0.5, 'Neosfera Glitch', 'Bold'),
    ('NeosferaCondensed-Regular.ttf', 'cr', 0.32, 'Neosfera Condensed Glitch', 'Regular'),
    ('NeosferaCondensed-Bold.ttf', 'cb', 0.32, 'Neosfera Condensed Glitch', 'Bold'),
]

if __name__ == '__main__':
    os.makedirs('glitch/estados', exist_ok=True)
    for base, key, amp, fam, sub in BASES:
        out = f"glitch/{fam.replace(' ', '')}-{sub}.ttf"
        build_combined(base, key, amp, fam, sub, out)
        print('combinada', out, os.path.getsize(out) // 1024, 'KB')
        for st in (1, 2, 3, 4):
            f2 = f'{fam} {st}'
            outs = f"glitch/estados/{f2.replace(' ', '')}-{sub}.ttf"
            build_state(base, key, amp, st, f2, sub, outs)
        print('  estados ok')
