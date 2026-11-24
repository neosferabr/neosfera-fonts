"""Monta os TTFs e WOFF2s das famílias paramétricas da Neosfera (Serif, Sans, Display)
seguindo 100% das especificações técnicas do Google Fonts (FontBakery googlefonts profile)."""
import os, sys, math
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.otlLib.builder import buildStatTable
import grotesk as g, family as F

VERSION = 'Version 1.000'
FONT_REV = 1.0
COPY = 'Copyright 2026 The Neosfera Project Authors (https://neosfera.com.br)'
OFL_DESC = 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://scripts.sil.org/OFL'
OFL_URL = 'https://scripts.sil.org/OFL'
VENDOR_URL = 'https://neosfera.com.br'

DISPLAY_STYLES = {
    'Regular': dict(p=dict(W=92,  thick=44, slen=0, rv=15, rc=8,  diag=86,  bar=86,  G=52), sxb=0.70, sxc=0.64, wclass=400),
    'Bold':    dict(p=dict(W=112, thick=52, slen=0, rv=17, rc=9,  diag=104, bar=105, G=56), sxb=0.73, sxc=0.67, wclass=700),
    'Black':   dict(p=dict(W=134, thick=60, slen=0, rv=19, rc=10, diag=124, bar=124, G=60), sxb=0.76, sxc=0.70, wclass=900),
}
CONDENSED_SANS_STYLES = {
    'Regular': dict(p=dict(W=92,  thick=44, slen=0, rv=15, rc=8,  diag=78,  bar=84,  G=74), sxb=0.70, sxc=0.64, wclass=400),
    'Bold':    dict(p=dict(W=112, thick=52, slen=0, rv=17, rc=9,  diag=96,  bar=102, G=78), sxb=0.73, sxc=0.67, wclass=700),
    'Black':   dict(p=dict(W=134, thick=60, slen=0, rv=19, rc=10, diag=116, bar=122, G=82), sxb=0.76, sxc=0.70, wclass=900),
}
DISPLAY_BONUS = dict(v=.08, w=.10, x=.08, y=.08, z=.06, V=.08, W=.11, X=.08, Y=.07, Z=.06, A=.06, K=.05, M=.07, k=.04)
CONDENSED_SANS_BONUS = dict(v=.08, w=.10, x=.08, y=.08, z=.06, V=.07, W=.09, X=.07, Y=.06, Z=.05, A=.05, K=.05, M=.04, k=.04)

STD_WEIGHTS = {
    'Light':   dict(W=60,  thick=30, slen=50, rv=10, rc=6,  diag=52,  bar=56,  G=54),
    'Regular': dict(W=84,  thick=40, slen=56, rv=14, rc=8,  diag=70,  bar=78,  G=58),
    'Bold':    dict(W=116, thick=54, slen=60, rv=18, rc=10, diag=98,  bar=106, G=64),
    'Black':   dict(W=134, thick=60, slen=62, rv=19, rc=10, diag=116, bar=122, G=82),
}

def to_glyph(path):
    tt = TTGlyphPen(None)
    if path is None:
        return tt.glyph()
    rec = RecordingPen(); path.draw(rec)
    ap = AreaPen(); rec.replay(ap)
    pen = Cu2QuPen(tt, max_err=0.8, reverse_direction=False)
    rec.replay(ReverseContourPen(pen) if ap.value > 0 else pen)
    return tt.glyph()

def notdef():
    p = g.op(g.rect(60, 0, 440, 700), g.rect(110, 50, 390, 650), g.PathOp.DIFFERENCE)
    return to_glyph(p)

def configure_engine(family_kind, weight):
    if family_kind == 'serif':
        g.SERIFS = True
        g.DISPLAY_MODE = False
        g.SX_BASE, g.CAPS_SX = 0.90, 0.84
        g.SX = g.SX_BASE
        g.SX_BONUS = {}
        g.WEIGHTS[weight] = dict(STD_WEIGHTS[weight])
        return 'Neosfera Serif', 5, {'Light': 300, 'Regular': 400, 'Bold': 700}[weight], True
    elif family_kind == 'sans':
        g.SERIFS = False
        g.DISPLAY_MODE = False
        g.SX_BASE, g.CAPS_SX = 0.90, 0.84
        g.SX = g.SX_BASE
        g.SX_BONUS = {}
        g.WEIGHTS[weight] = dict(STD_WEIGHTS[weight])
        return 'Neosfera Sans', 5, {'Light': 300, 'Regular': 400, 'Bold': 700}[weight], True
    elif family_kind == 'display':
        S = DISPLAY_STYLES[weight]
        g.SERIFS = False
        g.DISPLAY_MODE = True
        g.SX_BASE, g.CAPS_SX = S['sxb'], S['sxc']
        g.SX = g.SX_BASE
        g.SX_BONUS = dict(DISPLAY_BONUS)
        g.WEIGHTS[weight] = dict(S['p'])
        return 'Neosfera Display', 3, S['wclass'], False
    elif family_kind == 'condensed_sans':
        S = CONDENSED_SANS_STYLES[weight]
        g.SERIFS = False
        g.DISPLAY_MODE = False
        g.SX_BASE, g.CAPS_SX = S['sxb'], S['sxc']
        g.SX = g.SX_BASE
        g.SX_BONUS = dict(CONDENSED_SANS_BONUS)
        g.WEIGHTS[weight] = dict(S['p'])
        return 'Neosfera Condensed Sans', 3, S['wclass'], False
    else:
        raise ValueError(f'Unknown family_kind: {family_kind}')

def build_stat(font, has_italic, weights_list):
    w_values = []
    for wname, wval in weights_list:
        entry = dict(value=wval, name=wname)
        if wname == 'Regular':
            entry['flags'] = 0x2
            if 700 in dict(weights_list).values():
                entry['linkedValue'] = 700
        w_values.append(entry)
    axes = [dict(tag='wght', name='Weight', ordering=0, values=w_values)]
    if has_italic:
        axes.append(dict(tag='ital', name='Italic', ordering=1, values=[
            dict(value=0, name='Roman', flags=0x2, linkedValue=1),
            dict(value=1, name='Italic'),
        ]))
    buildStatTable(font, axes)

def build_style_font(family_kind, weight, italic, ttf_out, woff2_out=None):
    fam_name, width_class, wclass, has_italic = configure_engine(family_kind, weight)
    st = F.build_style(weight, italic)
    kern_lines, n_base_kern, n_total_kern = F.kern_fea_lines(st)

    order = ['.notdef', 'space', 'uni00A0'] + [n for n in F.NAMES]
    glyphs = {
        '.notdef': notdef(),
        'space': to_glyph(None),
        'uni00A0': to_glyph(None),
    }
    adv = {
        '.notdef': 500,
        'space': st['space']['adv'],
        'uni00A0': st['uni00A0']['adv'],
    }
    for n in F.NAMES:
        glyphs[n] = to_glyph(st[n]['path'])
        adv[n] = st[n]['adv']

    cmap = {g.UNI[n]: n for n in F.NAMES if n in g.UNI}
    cmap[0x20] = 'space'
    cmap[0xA0] = 'uni00A0'

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    glyf = fb.font['glyf']
    metrics = {}
    for n in order:
        gl = glyf[n]
        gl.recalcBounds(glyf)
        metrics[n] = (adv[n], getattr(gl, 'xMin', 0) if gl.numberOfContours else 0)
    fb.setupHorizontalMetrics(metrics)

    asc, desc = 960, -260
    win_asc, win_desc = 980, 260
    run = round(1000 * math.tan(math.radians(g.ITALIC_ANGLE))) if italic else 0
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0, caretSlopeRise=1000, caretSlopeRun=run)

    ribbi = weight in ('Regular', 'Bold')
    sub = ('Bold ' if weight == 'Bold' else '') + ('Italic' if italic else ('' if weight == 'Bold' else 'Regular'))
    sub = sub.strip() or 'Regular'
    typo_sub = (weight if weight != 'Regular' else '') + (' Italic' if italic else '')
    typo_sub = typo_sub.strip() or 'Regular'
    fam1 = fam_name if ribbi else f'{fam_name} {weight}'
    if not ribbi:
        sub = 'Italic' if italic else 'Regular'

    ps_fam = fam_name.replace(' ', '')
    ps_sub = typo_sub.replace(' ', '')
    ps = f'{ps_fam}-{ps_sub}'
    full_name = f'{fam_name} {typo_sub}' if typo_sub != 'Regular' else fam_name

    names = dict(
        copyright=COPY,
        familyName=fam1,
        styleName=sub,
        uniqueFontIdentifier=f'1.000;NEOS;{ps}',
        fullName=full_name,
        psName=ps,
        version=VERSION,
        manufacturer='Neosfera',
        designer='Neosfera',
        vendorURL=VENDOR_URL,
        designerURL=VENDOR_URL,
        licenseDescription=OFL_DESC,
        licenseInfoURL=OFL_URL,
    )
    if not ribbi:
        names.update(typographicFamily=fam_name, typographicSubfamily=typo_sub)
    fb.setupNameTable(names, windows=True, mac=False)

    fs = (1 if italic else 0) | (32 if weight == 'Bold' else 0)
    if fs == 0:
        fs = 64
    fs |= 128  # USE_TYPO_METRICS

    fb.setupOS2(
        version=4,
        fsType=0,
        usWeightClass=wclass,
        usWidthClass=width_class,
        fsSelection=fs,
        achVendID='NEOS',
        sTypoAscender=asc,
        sTypoDescender=desc,
        sTypoLineGap=0,
        usWinAscent=win_asc,
        usWinDescent=win_desc,
        sxHeight=g.XH,
        sCapHeight=g.CAP,
        ulCodePageRange1=0b11,
    )
    fb.font['OS/2'].recalcUnicodeRanges(fb.font)
    fb.setupPost(italicAngle=-g.ITALIC_ANGLE if italic else 0.0, underlinePosition=-120, underlineThickness=round(g.W * 0.7), isFixedPitch=0)
    fb.font['head'].macStyle = (1 if weight == 'Bold' else 0) | (2 if italic else 0)
    fb.font['head'].fontRevision = FONT_REV

    gasp = newTable('gasp')
    gasp.version = 1
    gasp.gaspRange = {65535: 0x000F}
    fb.font['gasp'] = gasp

    weights_list = [('Regular', 400), ('Bold', 700), ('Black', 900)] if family_kind in ('display', 'condensed_sans') else [('Light', 300), ('Regular', 400), ('Bold', 700)]
    build_stat(fb.font, has_italic, weights_list)
    fb.font['name'].names = [r for r in fb.font['name'].names if r.platformID == 3]

    fea = [
        'languagesystem DFLT dflt;',
        'languagesystem latn dflt;',
        'feature liga {',
        '  sub f i by fi;',
        '  sub f l by fl;',
        '} liga;',
    ] + kern_lines
    addOpenTypeFeaturesFromString(fb.font, '\n'.join(fea))

    os.makedirs(os.path.dirname(ttf_out) or '.', exist_ok=True)
    fb.save(ttf_out)

    if woff2_out:
        os.makedirs(os.path.dirname(woff2_out) or '.', exist_ok=True)
        fb.font.flavor = 'woff2'
        fb.font.save(woff2_out)

    return len(order), n_base_kern, n_total_kern
