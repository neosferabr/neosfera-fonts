"""Exporta fontes editáveis padrão UFO v3 + DesignSpace + config.yaml (padrão googlefonts-project-template)
para todas as 8 famílias do Sistema Tipográfico Neosfera em sources/."""
import os, shutil
from fontTools.ttLib import TTFont
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
import ufoLib2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFL_ROOT = os.path.join(ROOT, 'google-fonts', 'ofl')
SRC_ROOT = os.path.join(ROOT, 'sources')

FAMILIES = [
    ('neosferaserif', 'Neosfera Serif', True),
    ('neosferasans', 'Neosfera Sans', True),
    ('neosferadisplay', 'Neosfera Display', False),
    ('neosferacondensedsans', 'Neosfera Condensed Sans', False),
    ('neosferadither', 'Neosfera Dither', False),
    ('neosferadithercondensed', 'Neosfera Dither Condensed', False),
    ('neosferaglitch', 'Neosfera Glitch', False),
    ('neosferaglitchcondensed', 'Neosfera Glitch Condensed', False),
]

def extract_kerning(ttfont):
    kern = {}
    if 'GPOS' not in ttfont:
        return kern
    gpos = ttfont['GPOS'].table
    if not gpos.LookupList:
        return kern
    for lookup in gpos.LookupList.Lookup:
        if lookup.LookupType != 2:
            continue
        for sub in lookup.SubTable:
            if sub.Format == 1:
                for g1, pairset in zip(sub.Coverage.glyphs, sub.PairSet):
                    for pvr in pairset.PairValueRecord:
                        val = pvr.Value1.XAdvance if pvr.Value1 else 0
                        if val:
                            kern[(g1, pvr.SecondGlyph)] = val
            elif sub.Format == 2:
                c1_map = {}
                for g, c in sub.ClassDef1.classDefs.items():
                    c1_map.setdefault(c, []).append(g)
                c2_map = {}
                for g, c in sub.ClassDef2.classDefs.items():
                    c2_map.setdefault(c, []).append(g)
                cov = set(sub.Coverage.glyphs)
                c1_map[0] = [g for g in cov if g not in sub.ClassDef1.classDefs]
                for i, cr1 in enumerate(sub.Class1Record):
                    g1s = [g for g in c1_map.get(i, []) if g in cov]
                    if not g1s:
                        continue
                    for j, cr2 in enumerate(cr1.Class2Record):
                        val = cr2.Value1.XAdvance if cr2.Value1 else 0
                        if not val:
                            continue
                        g2s = c2_map.get(j, [])
                        for g1 in g1s:
                            for g2 in g2s:
                                kern[(g1, g2)] = val
    return kern

def build_features_fea(ttfont, slug):
    lines = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;', '']
    order = set(ttfont.getGlyphOrder())
    if 'fi' in order and 'fl' in order:
        lines += ['feature liga {', '  sub f i by fi;', '  sub f l by fl;', '} liga;', '']
    if 'glitch' in slug and 'GSUB' in ttfont:
        # Exporta ss01..ss04 para Glitch
        gsub = ttfont['GSUB'].table
        if gsub.FeatureList and gsub.LookupList:
            for feat_rec in gsub.FeatureList.FeatureRecord:
                tag = feat_rec.FeatureTag
                if tag.startswith('ss0'):
                    lines.append(f'feature {tag} {{')
                    for li in feat_rec.Feature.LookupListIndex:
                        lkp = gsub.LookupList.Lookup[li]
                        if lkp.LookupType == 1:
                            for sub in lkp.SubTable:
                                for k, v in sorted(sub.mapping.items()):
                                    lines.append(f'  sub {k} by {v};')
                    lines.append(f'}} {tag};')
                    lines.append('')
    return '\n'.join(lines)

def ttf_to_ufo(ttf_path, ufo_path, family_name, slug):
    tt = TTFont(ttf_path)
    ufo = ufoLib2.Font()

    head = tt['head']
    hhea = tt['hhea']
    os2 = tt['OS/2']
    post = tt['post']
    nm = tt['name']

    style_name = nm.getDebugName(17) or nm.getDebugName(2) or 'Regular'
    ufo.info.familyName = family_name
    ufo.info.styleName = style_name
    ufo.info.unitsPerEm = head.unitsPerEm
    ufo.info.ascender = os2.sTypoAscender
    ufo.info.descender = os2.sTypoDescender
    ufo.info.xHeight = os2.sxHeight
    ufo.info.capHeight = os2.sCapHeight
    ufo.info.italicAngle = float(post.italicAngle)
    ufo.info.versionMajor = 1
    ufo.info.versionMinor = 0
    ufo.info.copyright = nm.getDebugName(0) or ''
    ufo.info.openTypeNameDesigner = nm.getDebugName(9) or 'Neosfera'
    ufo.info.openTypeNameDesignerURL = nm.getDebugName(12) or 'https://neosfera.com.br'
    ufo.info.openTypeNameManufacturer = nm.getDebugName(8) or 'Neosfera'
    ufo.info.openTypeNameManufacturerURL = nm.getDebugName(11) or 'https://neosfera.com.br'
    ufo.info.openTypeNameLicense = nm.getDebugName(13) or ''
    ufo.info.openTypeNameLicenseURL = nm.getDebugName(14) or 'https://scripts.sil.org/OFL'
    ufo.info.openTypeNamePreferredFamilyName = family_name
    ufo.info.openTypeNamePreferredSubfamilyName = style_name
    ufo.info.openTypeOS2WeightClass = os2.usWeightClass
    ufo.info.openTypeOS2WidthClass = os2.usWidthClass
    ufo.info.openTypeOS2VendorID = 'NEOS'
    ufo.info.openTypeOS2TypoAscender = os2.sTypoAscender
    ufo.info.openTypeOS2TypoDescender = os2.sTypoDescender
    ufo.info.openTypeOS2TypoLineGap = 0
    ufo.info.openTypeHheaAscender = hhea.ascent
    ufo.info.openTypeHheaDescender = hhea.descent
    ufo.info.openTypeHheaLineGap = 0
    ufo.info.openTypeOS2WinAscent = os2.usWinAscent
    ufo.info.openTypeOS2WinDescent = os2.usWinDescent
    ufo.info.postscriptUnderlinePosition = post.underlinePosition
    ufo.info.postscriptUnderlineThickness = post.underlineThickness

    cmap = tt.getBestCmap() or {}
    rev_cmap = {}
    for cp, gn in cmap.items():
        rev_cmap.setdefault(gn, []).append(cp)

    order = list(tt.getGlyphOrder())
    gs = tt.getGlyphSet()
    hmtx = tt['hmtx']

    for gn in order:
        g = ufo.newGlyph(gn)
        g.width = hmtx[gn][0]
        g.unicodes = sorted(rev_cmap.get(gn, []))
        gs[gn].draw(Qu2CuPen(g.getPen(), max_err=0.5))

    ufo.lib['public.glyphOrder'] = order
    ufo.features.text = build_features_fea(tt, slug)

    kern = extract_kerning(tt)
    if kern:
        ufo.kerning.update(kern)

    if os.path.exists(ufo_path):
        shutil.rmtree(ufo_path)
    ufo.save(ufo_path, overwrite=True)
    return style_name, os2.usWeightClass, abs(float(post.italicAngle)) > 0

def main():
    if os.path.exists(SRC_ROOT):
        shutil.rmtree(SRC_ROOT)
    os.makedirs(SRC_ROOT, exist_ok=True)

    for slug, fam_name, has_italic in FAMILIES:
        ofl_dir = os.path.join(OFL_ROOT, slug)
        fam_src_dir = os.path.join(SRC_ROOT, slug)
        os.makedirs(fam_src_dir, exist_ok=True)

        ds = DesignSpaceDocument()
        ax_w = AxisDescriptor(tag='wght', name='Weight', minimum=300 if has_italic else 400, default=400, maximum=900 if ('Display' in fam_name or 'Condensed Sans' in fam_name) else 700)
        ds.addAxis(ax_w)
        if has_italic:
            ax_i = AxisDescriptor(tag='ital', name='Italic', minimum=0, default=0, maximum=1)
            ds.addAxis(ax_i)

        ttfs = sorted(f for f in os.listdir(ofl_dir) if f.endswith('.ttf'))
        for fn in ttfs:
            stem = fn[:-4]
            ufo_name = f'{stem}.ufo'
            ufo_path = os.path.join(fam_src_dir, ufo_name)
            style_name, wclass, is_ital = ttf_to_ufo(os.path.join(ofl_dir, fn), ufo_path, fam_name, slug)
            loc = {'Weight': wclass}
            if has_italic:
                loc['Italic'] = 1 if is_ital else 0
            src = SourceDescriptor(
                path=ufo_path,
                filename=ufo_name,
                familyName=fam_name,
                styleName=style_name,
                location=loc,
            )
            ds.addSource(src)
            inst = InstanceDescriptor(
                familyName=fam_name,
                styleName=style_name,
                location=loc,
                filename=f'instance_ttf/{stem}.ttf',
            )
            ds.addInstance(inst)

        ps_fam = fam_name.replace(' ', '')
        ds_path = os.path.join(fam_src_dir, f'{ps_fam}.designspace')
        ds.write(ds_path)

        cfg_path = os.path.join(SRC_ROOT, f'config-{slug}.yaml')
        with open(cfg_path, 'w', encoding='utf-8') as fp:
            fp.write(f'sources:\n  - {slug}/{ps_fam}.designspace\nbuildVariable: false\nbuildStatic: true\nfamilyName: "{fam_name}"\n')
        print(f'  [UFO+DS] {slug:26} | {len(ttfs)} UFOs -> sources/{slug}/{ps_fam}.designspace')

    makefile_path = os.path.join(ROOT, 'Makefile')
    with open(makefile_path, 'w', encoding='utf-8') as fp:
        fp.write(
            ".PHONY: build test clean\n\n"
            "build:\n"
            "\t.venv/bin/python3 motor/build_all.py\n\n"
            "test:\n"
            "\t.venv/bin/python3 motor/validate_google_fonts.py\n\n"
            "clean:\n"
            "\trm -rf __pycache__ motor/__pycache__\n"
        )
    print('\n=== Exportação UFO v3 + DesignSpace concluída! ===')

if __name__ == '__main__':
    main()
