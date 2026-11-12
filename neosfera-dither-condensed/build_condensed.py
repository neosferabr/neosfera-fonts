"""Neosfera Condensed: Albert Sans Bold estreitada (x) e alongada (y), haste compensada,
depois a mesma trama dither (Bayer 8x8) dos frames Regular (celula 6px) e Bold (celula 12px)."""
import sys, os, math
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import instancer
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.ttLib.tables.ttProgram import Program
import pathops
from pathops import Path, PathOp

SX = float(os.environ.get('NEOS_SX', '0.58'))      # largura
SY = float(os.environ.get('NEOS_SY', '1.06'))      # altura
STEM = float(os.environ.get('NEOS_STEM', '0.86'))  # haste final em relacao a Albert Sans Bold
TIGHT = float(os.environ.get('NEOS_TIGHT', '0.25'))
S = 400 / 1000.0
B = 470
FW = 640
M = [[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
     [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]
bayer = lambda x, y: (M[y & 7][x & 7] + 0.5) / 64
clamp = lambda v: max(0.0, min(1.0, v))
js_round = lambda v: math.floor(v + 0.5)

def pattern_runs(style, bounds, adv_units):
    xmin, ymin, xmax, ymax = bounds
    adv_px = adv_units * S
    left = js_round((FW - adv_px) / 2)
    adv_used = js_round(adv_px)
    CELL = 6 if style == 'regular' else 12
    gx0 = left + xmin * S; gx1 = left + xmax * S
    gy0 = B - ymax * S;    gy1 = B - ymin * S
    gw, gh = gx1 - gx0, gy1 - gy0
    cx0 = math.floor(gx0 / CELL) - 1; cx1 = math.ceil(gx1 / CELL) + 1
    cy0 = math.floor(gy0 / CELL) - 1; cy1 = math.ceil(gy1 / CELL) + 1
    runs = []
    for cy in range(cy0, cy1):
        rs = None
        for cx in range(cx0, cx1 + 1):
            on = False
            if cx < cx1:
                xc = (cx + 0.5) * CELL; yc = (cy + 0.5) * CELL
                if style == 'regular':
                    tone = 0.55 * clamp((xc - left) / adv_used) + 0.45 * clamp((B - yc) / (288 * SY))
                    on = bayer(cx, cy) >= tone * 0.9
                else:
                    u = clamp((xc - gx0) / gw); v = clamp((gy1 - yc) / gh)
                    tone = clamp(1.3 * (0.5 * u + 0.5 * v) - 0.15)
                    on = bayer(cx, cy) >= tone
            if on and rs is None: rs = cx
            if (not on) and rs is not None:
                runs.append((rs * CELL, cx * CELL, cy * CELL, cy * CELL + CELL)); rs = None
    return runs, left

def condense(p, d):
    """estreita/alonga e engrossa so as hastes verticais (uniao do contorno deslocado em x)."""
    copies = [p.transform(scaleX=SX, scaleY=SY, translateX=t) for t in (-d, -d / 2, 0, d / 2, d)] if d else [p.transform(scaleX=SX, scaleY=SY)]
    out = Path()
    for c in copies: out.addPath(c)
    out.simplify(fix_winding=True, keep_starting_points=False)
    return out

def scale_gpos(font):
    """escala kerning e ancoras do GPOS para a nova largura/altura."""
    if 'GPOS' not in font: return
    seen = set()
    def walk(o):
        if id(o) in seen: return
        seen.add(id(o))
        cn = type(o).__name__
        if cn == 'ValueRecord':
            for a in ('XPlacement', 'XAdvance'):
                if getattr(o, a, None): setattr(o, a, round(getattr(o, a) * SX))
            for a in ('YPlacement', 'YAdvance'):
                if getattr(o, a, None): setattr(o, a, round(getattr(o, a) * SY))
            return
        if cn == 'Anchor':
            o.XCoordinate = round(o.XCoordinate * SX); o.YCoordinate = round(o.YCoordinate * SY); return
        if isinstance(o, (list, tuple)):
            for i in o: walk(i)
        elif hasattr(o, '__dict__'):
            for v in list(o.__dict__.values()):
                if isinstance(v, (list, tuple)) or hasattr(v, '__dict__'): walk(v)
    walk(font['GPOS'].table)

def build(style, src_path, out_path):
    font = TTFont(src_path)
    font = instancer.instantiateVariableFont(font, {"wght": 700}, inplace=False)
    gs = font.getGlyphSet(); glyf = font['glyf']; hmtx = font['hmtx']
    names = font.getGlyphOrder(); cmap = font.getBestCmap()
    # haste da Albert Sans Bold medida no "l"
    pl = Path(); gs[cmap[ord('l')]].draw(pl.getPen(glyphSet=gs)); pl.simplify(fix_winding=True)
    stem = pl.bounds[2] - pl.bounds[0]
    d = max(0, round((STEM - SX) * stem / 2))
    print(f'haste original {stem:.0f}u, deslocamento {d}u (+{2*d}u por haste)')
    new = {}; newadv = {}; shift = {}; stats = {'n': 0, 'empty': []}
    for name in names:
        adv, lsb = hmtx[name]
        adv_c = round(adv * SX)
        p = Path(); gs[name].draw(p.getPen(glyphSet=gs))
        p.simplify(fix_winding=True, keep_starting_points=False)
        if not len(list(p.contours)):
            new[name] = TTGlyphPen(None).glyph(); newadv[name] = adv_c; continue
        p = condense(p, d)
        tb = p.bounds
        cut_l = round(TIGHT * max(0, tb[0])); cut_r = round(TIGHT * max(0, adv_c - tb[2]))
        newadv[name] = adv_c - cut_l - cut_r; shift[name] = -cut_l
        runs, left = pattern_runs(style, tb, adv_c)
        pat = Path(); pen = pat.getPen()
        for xa, xb, ya, yb in runs:
            X0 = (xa - left) / S; X1 = (xb - left) / S; Y0 = (B - yb) / S; Y1 = (B - ya) / S
            pen.moveTo((round(X0), round(Y0))); pen.lineTo((round(X1), round(Y0)))
            pen.lineTo((round(X1), round(Y1))); pen.lineTo((round(X0), round(Y1))); pen.closePath()
        pat.simplify(fix_winding=True, keep_starting_points=False)
        res = pathops.op(p, pat, PathOp.INTERSECTION, fix_winding=True, keep_starting_points=False)
        rec = RecordingPen(); res.draw(rec)
        ap = AreaPen(); rec.replay(ap)
        tt = TTGlyphPen(None)
        pen2 = Cu2QuPen(tt, max_err=1.0, reverse_direction=False)
        rec.replay(ReverseContourPen(pen2) if ap.value > 0 else pen2)
        g = tt.glyph()
        if g.numberOfContours and shift.get(name): g.coordinates.translate((shift[name], 0))
        new[name] = g; stats['n'] += 1
        if g.numberOfContours == 0: stats['empty'].append(name)
    for name, g in new.items(): glyf[name] = g
    for name in names:
        g = glyf[name]; g.recalcBounds(glyf)
        hmtx[name] = (newadv.get(name, hmtx[name][0]), getattr(g, 'xMin', 0) if g.numberOfContours else 0)
    scale_gpos(font)
    for t in ('fpgm', 'prep', 'cvt ', 'DSIG', 'STAT', 'MVAR', 'HVAR', 'avar', 'fvar', 'gvar'):
        if t in font: del font[t]
    for name in names:
        g = glyf[name]
        if g.numberOfContours: g.program = Program(); g.program.fromBytecode(b'')
    font['gasp'] = newTable('gasp'); font['gasp'].version = 1; font['gasp'].gaspRange = {65535: 0x000F}
    # metricas verticais
    hh, os2 = font['hhea'], font['OS/2']
    hh.ascent = round(hh.ascent * SY); hh.descent = round(hh.descent * SY); hh.lineGap = 0
    os2.sTypoAscender = round(os2.sTypoAscender * SY); os2.sTypoDescender = round(os2.sTypoDescender * SY); os2.sTypoLineGap = 0
    os2.usWinAscent = round(os2.usWinAscent * SY); os2.usWinDescent = round(os2.usWinDescent * SY)
    for a in ('sxHeight', 'sCapHeight'):
        if hasattr(os2, a): setattr(os2, a, round(getattr(os2, a) * SY))
    os2.usWidthClass = 3
    # nomes
    bold = style == 'bold'; sub = 'Bold' if bold else 'Regular'
    nm = font['name']
    for nid in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25): nm.removeNames(nameID=nid)
    fam = 'Neosfera Condensed'; ps = f'NeosferaCondensed-{sub}'
    entries = {1: fam, 2: sub, 3: f'0.1;NEOS;{ps}', 4: f'{fam} {sub}', 5: 'Version 0.1', 6: ps,
               0: 'Copyright 2021 The Albert Sans Project Authors (https://github.com/usted/Albert-Sans). Neosfera dither adaptation 2026 Neosfera.'}
    for nid, s in entries.items():
        nm.removeNames(nameID=nid)
        nm.setName(s, nid, 3, 1, 0x409); nm.setName(s, nid, 1, 0, 0)
    os2.usWeightClass = 700 if bold else 400
    os2.fsSelection = (os2.fsSelection & ~(1 | 32 | 64)) | (32 if bold else 64)
    font['head'].macStyle = 1 if bold else 0
    font['post'].formatType = 2.0
    font.save(out_path)
    return stats

if __name__ == '__main__':
    style, src, out = sys.argv[1:4]
    st = build(style, src, out)
    print(style, 'glifos:', st['n'], 'vazios:', len(st['empty']), st['empty'][:20])
