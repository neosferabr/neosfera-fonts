"""Gera os estilos da família Neosfera (Serif, Sans, Display): contornos posicionados + métricas + kerning automático."""
import json, sys
import numpy as np
import grotesk as g
from pathops import PathOp

FIG = {'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'}
PUNCT_SB = {
    'period': (0.9, 0.9), 'comma': (0.9, 0.9), 'colon': (0.9, 0.9), 'semicolon': (0.9, 0.9),
    'exclam': (0.9, 0.9), 'exclamdown': (0.9, 0.9), 'question': (0.6, 0.6), 'questiondown': (0.6, 0.6),
    'hyphen': (0.6, 0.6), 'uni00AD': (0.6, 0.6), 'endash': (0.5, 0.5), 'emdash': (0.4, 0.4), 'underscore': (0.3, 0.3),
    'quotesingle': (0.9, 0.9), 'quotedbl': (0.9, 0.9), 'quoteright': (0.9, 0.9), 'quoteleft': (0.9, 0.9),
    'quotedblright': (0.9, 0.9), 'quotedblleft': (0.9, 0.9), 'quotesinglbase': (0.9, 0.9), 'quotedblbase': (0.9, 0.9),
    'parenleft': (1.0, 0.4), 'parenright': (0.4, 1.0),
    'bracketleft': (1.0, 0.45), 'bracketright': (0.45, 1.0),
    'braceleft': (0.85, 0.45), 'braceright': (0.45, 0.85),
    'slash': (0.15, 0.15), 'backslash': (0.15, 0.15), 'fraction': (0.1, 0.1),
    'bar': (1.1, 1.1), 'brokenbar': (1.1, 1.1),
    'periodcentered': (1.1, 1.1), 'bullet': (0.9, 0.9), 'ellipsis': (0.7, 0.7),
    'numbersign': (0.55, 0.55), 'asterisk': (0.65, 0.65),
    'plus': (0.65, 0.65), 'minus': (0.65, 0.65), 'plusminus': (0.65, 0.65),
    'equal': (0.65, 0.65), 'less': (0.55, 0.55), 'greater': (0.55, 0.55),
    'asciicircum': (0.6, 0.6), 'asciitilde': (0.6, 0.6), 'logicalnot': (0.65, 0.65),
    'multiply': (0.65, 0.65), 'divide': (0.65, 0.65),
    'guilsinglleft': (0.65, 0.55), 'guilsinglright': (0.55, 0.65),
    'guillemotleft': (0.65, 0.55), 'guillemotright': (0.55, 0.65),
    'dagger': (0.65, 0.65), 'daggerdbl': (0.65, 0.65),
    'degree': (0.65, 0.65), 'ordfeminine': (0.65, 0.65), 'ordmasculine': (0.65, 0.65),
    'uni00B9': (0.65, 0.65), 'uni00B2': (0.65, 0.65), 'uni00B3': (0.65, 0.65),
    'uni2070': (0.65, 0.65), 'uni2074': (0.65, 0.65),
    'onequarter': (0.55, 0.55), 'onehalf': (0.55, 0.55), 'threequarters': (0.55, 0.55),
    'paragraph': (0.7, 0.7), 'section': (0.65, 0.65), 'trademark': (0.55, 0.55),
    'grave': (0.8, 0.8), 'acute': (0.8, 0.8), 'circumflex': (0.6, 0.6), 'tilde': (0.6, 0.6),
    'dieresis': (0.7, 0.7), 'macron': (0.6, 0.6), 'breve': (0.6, 0.6), 'dotaccent': (0.9, 0.9),
    'ring': (0.75, 0.75), 'caron': (0.6, 0.6), 'hungarumlaut': (0.65, 0.65),
    'cedilla': (0.8, 0.8), 'ogonek': (0.8, 0.8),
}
K, DMAX = 0.78, 96
NAMES = list(g.BASE) + [n for n in g.ACCENTED if n not in g.BASE]

def zone(n):
    base = g.ACCENTED.get(n, (n,))[0]
    t = int(g.P['thick'] + 6) if g.SERIFS else 4
    is_tall = base[0].isupper() or base in g.UPPER_SPECIAL or base in FIG or base in g.SYMS
    return (t, g.CAP - t) if is_tall else (t, g.XH - t)

def profile(p, lo, hi):
    body = g.op(p, g.rect(-2000, lo, 3000, hi), PathOp.INTERSECTION)
    if not len(list(body.contours)):
        body = p
    xmin, _, xmax, _ = body.bounds; fx0, _, fx1, _ = p.bounds
    L, R = [], []
    for y in range(lo, hi, 12):
        band = g.op(p, g.rect(-2000, y, 3000, y + 4), PathOp.INTERSECTION)
        if not len(list(band.contours)): L.append(DMAX); R.append(DMAX); continue
        bx0, _, bx1, _ = band.bounds
        L.append(min(DMAX, bx0 - xmin)); R.append(min(DMAX, xmax - bx1))
    return sum(L) / len(L), sum(R) / len(R), max(0, xmin - fx0), max(0, fx1 - xmax)

def spacing(n, p):
    Gs = g.P['G']
    if n in PUNCT_SB:
        a, b = PUNCT_SB[n]; return round(Gs * a), round(Gs * b)
    lo, hi = zone(n)
    dl, dr, ol, orr = profile(p, lo, hi)
    k_val = 0.56 if not g.SERIFS else K
    lsb, rsb = round(Gs - k_val * dl - ol), round(Gs - k_val * dr - orr)
    fix = {'f': ('rsb', -30), 'j': ('lsb', -40), 'uni0237': ('lsb', -40), 'r': ('rsb', 6)}
    if n in fix:
        side, v = fix[n]
        if side == 'rsb': rsb = max(rsb, v)
        else: lsb = max(lsb, v)
    if n in ('I', 'one') and g.SERIFS:
        lsb = max(lsb, round(g.P['slen'] * 0.62)); rsb = max(rsb, round(g.P['slen'] * 0.62))
    if n == 'I' and not g.SERIFS:
        lsb = max(lsb, round(Gs * 0.95)); rsb = max(rsb, round(Gs * 0.95))
    if n == 'z': lsb = rsb = round(Gs * 0.48)
    if n == 'Z': lsb = rsb = round(Gs * 0.55)
    return lsb, rsb

def build_style(weight, italic):
    g.set_weight(weight)
    out = {}
    raw = {n: g.build_glyph(n, italic=False) for n in NAMES}
    for n in NAMES:
        p = g.finish(g.build_glyph(n, italic=italic) if italic else raw[n])
        if n in g.COMBINING_MARKS:
            bx0, _, bx1, _ = p.bounds
            q = p.transform(1, 0, 0, 1, -(bx0 + bx1) / 2 - 140, 0)
            if italic: q = g.shear(q)
            out[n] = dict(path=q, adv=0)
            continue
        mb = g.ACCENTED.get(n, (None,))[0]
        ref = g.finish(raw[mb]) if mb else (p if not italic else g.finish(raw[n]))
        if mb and italic and mb == 'a': ref = g.finish(g.build_glyph('a', italic=True))
        if italic and n == 'a': ref = p
        lsb, rsb = spacing(mb or n, ref)
        rx0, _, rx1, _ = ref.bounds
        xoff = lsb - rx0
        adv = round(lsb + (rx1 - rx0) + rsb)
        q = p.transform(1, 0, 0, 1, xoff, 0)
        if italic: q = g.shear(q)
        out[n] = dict(path=q, adv=adv)
    sp_adv = round(g.P['G'] * 3.9)
    out['space'] = dict(path=None, adv=sp_adv)
    out['uni00A0'] = dict(path=None, adv=sp_adv)
    return out

YS = list(range(-200, 800, 16))
def prof_full(st, n):
    v = st[n]; p = v['path']; adv = v['adv']
    L = np.full(len(YS), np.nan); R = np.full(len(YS), np.nan)
    if p is None: return L, R
    for i, y in enumerate(YS):
        band = g.op(p, g.rect(-2000, y, 3000, y + 6), PathOp.INTERSECTION)
        if len(list(band.contours)):
            bx0, _, bx1, _ = band.bounds; L[i] = bx0; R[i] = adv - bx1
    return L, R

_ACC_A = {k for k, (b, _) in g.ACCENTED.items() if b == 'A'}
_ACC_ROUND = {k for k, (b, _) in g.ACCENTED.items() if b in ('o', 'e', 'a', 'c', 'd', 'q', 'g', 's', 'O', 'C', 'G', 'Q')}
_ACC_STRAIGHT = {k for k, (b, _) in g.ACCENTED.items() if b in ('i', 'dotlessi', 'u', 'E', 'I', 'U', 'L', 'N', 'R', 'H', 'K')}

KL = set('TVWYAPFLKXRvwyxkfrt7') | {'quoteright', 'quotedblright', 'period', 'comma', 'one', 'seven'} | _ACC_A
KR = set('TVWYAJXvwyxjo') | {'period', 'comma', 'hyphen', 'quoteright', 'quotedblright', 'quoteleft', 'quotedblleft'} | _ACC_A
KR_ROUND = set('oeacdqgsOCGQ') | {'ae', 'oe', 'OE', 'oslash', 'Oslash'} | _ACC_ROUND
KL_ROUND = set('ODQCGSPBRU0235689') | _ACC_ROUND
QUOTES = {'quoteright', 'quotedblright', 'quoteleft', 'quotedblleft', 'quotesingle', 'quotedbl'}
L_OK = set('TVWYvwy') | QUOTES
TOPHANG = set('TFPVWY') | {'seven', 'quoteright', 'quotedblright'}
STRAIGHT_L = set('bhiklmnpruBDEFHIKLMNPRU') | {'dotlessi'} | _ACC_STRAIGHT

KERN_ELIGIBLE = (
    set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    | {'dotlessi', 'uni0237', 'AE', 'ae', 'OE', 'oe', 'Oslash', 'oslash', 'Lslash', 'lslash',
       'Eth', 'eth', 'Dcroat', 'dcroat', 'Thorn', 'thorn', 'germandbls', 'uni1E9E', 'Eng', 'eng', 'IJ', 'ij'}
    | FIG
    | {'period', 'comma', 'hyphen', 'endash', 'quoteright', 'quotedblright', 'quoteleft', 'quotedblleft', 'quotesingle', 'quotedbl'}
)

def _is_cap_like(n):
    base = g.ACCENTED.get(n, (n,))[0]
    return base[0].isupper() or base in g.UPPER_SPECIAL or base in FIG

def autokern_base(st):
    core_names = [n for n in g.BASE if n in KERN_ELIGIBLE and st[n]['path'] is not None]
    pr = {n: prof_full(st, n) for n in core_names}
    Ln, Rn = pr['n'][1], pr['n'][0]
    m = ~np.isnan(Ln) & ~np.isnan(Rn); nom_lc = float(np.mean(Ln[m] + Rn[m]))
    LH, RH = pr['H'][1], pr['H'][0]
    mH = ~np.isnan(LH) & ~np.isnan(RH); nom_cap = float(np.mean(LH[mH] + RH[mH]))
    ys = np.array(YS)
    base_kern = {}
    for a in core_names:
        for b in core_names:
            if not (a in KL or b in KR or (a in KL_ROUND and b in KR) or (a in KL and b in KR_ROUND)): continue
            ra = pr[a][1]; lb = pr[b][0]
            mm = ~np.isnan(ra) & ~np.isnan(lb)
            mm2 = mm & (ys > -40) & (ys < 740)
            if mm2.sum() < 3: continue
            nominal = nom_cap if (_is_cap_like(a) and _is_cap_like(b)) else nom_lc
            gaps = ra[mm2] + lb[mm2]
            avg = float(np.mean(np.minimum(gaps, 2.2 * nominal)))
            if not g.SERIFS:
                p25 = float(np.percentile(gaps, 25))
                eff = 0.45 * p25 + 0.55 * avg
                k = (nominal - eff) * 0.85
            else:
                k = (nominal - avg) * 0.65
            mingap = float(np.min(ra[mm] + lb[mm]))
            if b in ('hyphen', 'endash') or a in ('hyphen', 'endash'):
                floor = 0.50
            elif a in set('AVWYTLF7') and b in set('AVWYTJ47'):
                floor = 0.24
            elif a in KR_ROUND or b in KR_ROUND:
                floor = 0.34
            else:
                floor = 0.36
            k = max(k, -(mingap - floor * nominal))
            k = int(round(max(-150, min(20, k)) / 2) * 2)
            if a == 'L' and b not in L_OK: continue
            if b in STRAIGHT_L and a not in TOPHANG: k = max(k, -20)
            if abs(k) >= 8: base_kern[(a, b)] = k
    children = {b: [b] for b in core_names}
    for acc, (b, _) in g.ACCENTED.items():
        if b in children and acc not in children[b]:
            children[b].append(acc)
    return base_kern, children

def autokern(st):
    base_kern, children = autokern_base(st)
    kern = {}
    for (a, b), v in base_kern.items():
        for ca in children.get(a, [a]):
            for cb in children.get(b, [b]):
                kern[(ca, cb)] = v
    return kern

def kern_fea_lines(st):
    base_kern, children = autokern_base(st)
    used_bases = {a for a, _ in base_kern} | {b for _, b in base_kern}
    lines = []
    for b in sorted(used_bases):
        grp = children.get(b, [b])
        if len(grp) > 1:
            lines.append(f'@kc_{b} = [{" ".join(grp)}];')
    lines.append('feature kern {')
    for (a, b), v in sorted(base_kern.items()):
        ta = f'@kc_{a}' if len(children.get(a, [a])) > 1 else a
        tb = f'@kc_{b}' if len(children.get(b, [b])) > 1 else b
        lines.append(f'  pos {ta} {tb} {v};')
    lines.append('} kern;')
    total_expanded = sum(len(children.get(a, [a])) * len(children.get(b, [b])) for (a, b) in base_kern)
    return lines, len(base_kern), total_expanded
