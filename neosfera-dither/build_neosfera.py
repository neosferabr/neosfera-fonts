"""Neosfera TTF: Albert Sans Bold + trama dither (Bayer 8x8) intersectada com os contornos.
Replica o algoritmo usado nos frames do Figma (neosfera-regular = celula 6px, neosfera-bold = celula 12px)."""
import sys, math, copy
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import instancer
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.reverseContourPen import ReverseContourPen
import pathops
from pathops import Path, PathOp

S = 400 / 1000.0          # px por unidade de fonte (corpo 400 no Figma, UPM 1000)
TIGHT = float(__import__('os').environ.get('NEOS_TIGHT', '0.35'))   # fracao das margens laterais removida
B = 470                    # linha de base no frame
FW = 640
M = [[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
     [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]
bayer = lambda x, y: (M[y & 7][x & 7] + 0.5) / 64
clamp = lambda v: max(0.0, min(1.0, v))

def js_round(v): return math.floor(v + 0.5)

def pattern_runs(style, bounds, adv_units):
    """retorna lista de (xa, xb, ya, yb) em px do frame."""
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
                    tone = 0.55 * clamp((xc - left) / adv_used) + 0.45 * clamp((B - yc) / 288)
                    on = bayer(cx, cy) >= tone * 0.9
                else:
                    u = clamp((xc - gx0) / gw); v = clamp((gy1 - yc) / gh)
                    tone = clamp(1.3 * (0.5 * u + 0.5 * v) - 0.15)
                    on = bayer(cx, cy) >= tone
            if on and rs is None: rs = cx
            if (not on) and rs is not None:
                runs.append((rs * CELL, cx * CELL, cy * CELL, cy * CELL + CELL)); rs = None
    return runs, left

def build(style, src_path, out_path):
    font = TTFont(src_path)
    font = instancer.instantiateVariableFont(font, {"wght": 700}, inplace=False)
    gs = font.getGlyphSet()
    glyf = font['glyf']; hmtx = font['hmtx']
    names = font.getGlyphOrder()
    stats = {'empty': [], 'n': 0}
    new = {}; newadv = {}; shift = {}
    for name in names:
        adv, lsb = hmtx[name]
        p = Path()
        gs[name].draw(p.getPen(glyphSet=gs))
        p.simplify(fix_winding=True, keep_starting_points=False)
        tb = p.bounds if len(list(p.contours)) else None
        if tb is None:
            new[name] = TTGlyphPen(None).glyph(); newadv[name] = adv; continue
        # aproximacao do espacamento: corta TIGHT dos lados (medidos no contorno cheio)
        cut_l = round(TIGHT * max(0, tb[0])); cut_r = round(TIGHT * max(0, adv - tb[2]))
        newadv[name] = adv - cut_l - cut_r; shift[name] = -cut_l
        runs, left = pattern_runs(style, tb, adv)
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
        out = ReverseContourPen(pen2) if ap.value > 0 else pen2   # TrueType: externos horarios
        rec.replay(out)
        g = tt.glyph()
        if g.numberOfContours and shift.get(name):
            g.coordinates.translate((shift[name], 0))
        new[name] = g
        stats['n'] += 1
        if g.numberOfContours == 0: stats['empty'].append(name)
    for name, g in new.items():
        glyf[name] = g
    for name in names:
        g = glyf[name]
        g.recalcBounds(glyf)
        adv = newadv.get(name, hmtx[name][0])
        hmtx[name] = (adv, getattr(g, 'xMin', 0) if g.numberOfContours else 0)
    # sem hinting
    for t in ('fpgm', 'prep', 'cvt ', 'DSIG', 'STAT', 'MVAR', 'HVAR', 'avar', 'fvar', 'gvar'):
        if t in font: del font[t]
    for name in names:
        g = glyf[name]
        if g.numberOfContours: g.program = __import__('fontTools.ttLib.tables.ttProgram', fromlist=['Program']).Program(); g.program.fromBytecode(b'')
    font['gasp'] = newTable('gasp'); font['gasp'].version = 1; font['gasp'].gaspRange = {65535: 0x000F}
    # nomes e pesos
    bold = style == 'bold'
    sub = 'Bold' if bold else 'Regular'
    nm = font['name']
    for nid in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25):
        nm.removeNames(nameID=nid)
    full = f'Neosfera {sub}'
    ps = f'Neosfera-{sub}'
    ver = 'Version 0.3'
    entries = {1: 'Neosfera', 2: sub, 3: f'0.3;NEOS;{ps}', 4: full, 5: ver, 6: ps,
               0: 'Copyright 2021 The Albert Sans Project Authors (https://github.com/usted/Albert-Sans). Neosfera dither adaptation 2026 Neosfera.'}
    for nid, s in entries.items():
        nm.removeNames(nameID=nid)
        nm.setName(s, nid, 3, 1, 0x409); nm.setName(s, nid, 1, 0, 0)
    os2 = font['OS/2']
    os2.usWeightClass = 700 if bold else 400
    sel = os2.fsSelection & ~(1 | 32 | 64)
    os2.fsSelection = sel | (32 if bold else 64)
    font['head'].macStyle = 1 if bold else 0
    font['head'].flags |= 0
    font['post'].formatType = 2.0
    font.save(out_path)
    return stats

if __name__ == '__main__':
    style, src, out = sys.argv[1:4]
    st = build(style, src, out)
    print(style, 'glifos:', st['n'], 'vazios:', len(st['empty']), st['empty'][:20])
