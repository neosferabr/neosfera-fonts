"""Reconstrói todas as famílias do Sistema Tipográfico Neosfera, atualiza pastas de trabalho
e gera o pacote completo de submissão para o Google Fonts (google-fonts/ofl/*)."""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontTools.ttLib import TTFont
import build_ttf
import build_dither_glitch as bdg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OFL_BODY = """
This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is copied below, and is also available with a FAQ at:
https://scripts.sil.org/OFL


-----------------------------------------------------------
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
-----------------------------------------------------------

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide
development of collaborative font projects, to support the font creation
efforts of academic and linguistic communities, and to provide a free and
open framework in which fonts may be shared and improved in partnership
with others.

The OFL allows the licensed fonts to be used, studied, modified and
redistributed freely as long as they are not sold by themselves. The
fonts, including any derivative works, can be bundled, embedded, 
redistributed and/or sold with any software provided that any reserved
names are not used by derivative works. The fonts and derivatives,
however, cannot be released under any other type of license. The
requirement for fonts to remain under this license does not apply
to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright
Holder(s) under this license and clearly marked as such. This may
include source files, build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the
copyright statement(s).

"Original Version" refers to the collection of Font Software components as
distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting,
or substituting -- in part or in whole -- any of the components of the
Original Version, by changing formats or by porting the Font Software to a
new environment.

"Author" refers to any designer, engineer, programmer, technical
writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining
a copy of the Font Software, to use, study, copy, merge, embed, modify,
redistribute, and sell modified and unmodified copies of the Font
Software, subject to the following conditions:

1) Neither the Font Software nor any of its individual components,
in Original or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled,
redistributed and/or sold with any software, provided that each copy
contains the above copyright notice and this license. These can be
included either as stand-alone text files, human-readable headers or
in the appropriate machine-readable metadata fields within text or
binary files as long as those fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font
Name(s) unless explicit written permission is granted by the corresponding
Copyright Holder. This restriction only applies to the primary font name as
presented to the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
Software shall not be used to promote, endorse or advertise any
Modified Version, except to acknowledge the contribution(s) of the
Copyright Holder(s) and the Author(s) or with their explicit written
permission.

5) The Font Software, modified or unmodified, in part or in whole,
must be distributed entirely under this license, and must not be
distributed under any other license. The requirement for fonts to
remain under this license does not apply to any document created
using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are
not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
OTHER DEALINGS IN THE FONT SOFTWARE.
""".lstrip()

def write_ofl(path, copyright_line):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(copyright_line + '\n\n' + OFL_BODY)

def write_metadata_pb(ofl_dir, family_name, category, ttf_files):
    lines = [
        f'name: "{family_name}"',
        'designer: "Neosfera"',
        'license: "OFL"',
        f'category: "{category}"',
        'date_added: "2026-11-12"',
    ]
    for fn in ttf_files:
        f = TTFont(os.path.join(ofl_dir, fn))
        ps = f['name'].getDebugName(6)
        full = f['name'].getDebugName(4)
        copy_str = f['name'].getDebugName(0)
        wclass = f['OS/2'].usWeightClass
        is_italic = bool(f['OS/2'].fsSelection & 1)
        style_str = 'italic' if is_italic else 'normal'
        lines += [
            'fonts {',
            f'  name: "{family_name}"',
            f'  style: "{style_str}"',
            f'  weight: {wclass}',
            f'  filename: "{fn}"',
            f'  post_script_name: "{ps}"',
            f'  full_name: "{full}"',
            f'  copyright: "{copy_str}"',
            '}',
        ]
    for sub in ('latin', 'latin-ext', 'menu'):
        lines.append(f'subsets: "{sub}"')
    lines.append('source {')
    lines.append('  repository_url: "https://github.com/neosferabr/neosfera-fonts"')
    lines.append('}')
    with open(os.path.join(ofl_dir, 'METADATA.pb'), 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(lines) + '\n')

DESCRIPTIONS = {
    'neosferaserif': """<p>
Neosfera Serif is an original contemporary hybrid typeface designed by Neosfera. Built on a parametric monolinear skeleton with lightly rounded corners, it features distinctive unilateral half-serifs on vertical stems (top serifs pointing left, foot serifs pointing right), clean unserifed diagonals, a two-story lowercase 'a' across both Roman and Italic styles, straight horizontal hooks on 'g', 'j', 'y', and 'J', and crisp square punctuation dots.
</p>
<p>
Available in Light, Regular, and Bold weights with matching Italics, Neosfera Serif balances editorial authority with digital precision across headlines, interfaces, and brand communications. To contribute, visit <a href="https://github.com/neosferabr/neosfera-fonts">github.com/neosferabr/neosfera-fonts</a>.
</p>""",
    'neosferasans': """<p>
Neosfera Sans is the clean grotesque companion to Neosfera Serif, generated from the same parametric design engine without half-serifs. It preserves the signature Neosfera DNA: lightly rounded corners, a geometric-humanist two-story 'a' in both Roman and Italic, flat horizontal hooks on 'g', 'j', 'y', and 'J', and square pixel-inspired dots.
</p>
<p>
Spanning six styles from Light to Bold with matching Italics, Neosfera Sans is engineered for UI systems, editorial layouts, and contemporary digital branding. To contribute, visit <a href="https://github.com/neosferabr/neosfera-fonts">github.com/neosferabr/neosfera-fonts</a>.
</p>""",
    'neosferadisplay': """<p>
Neosfera Display is a condensed sans-serif headline typeface built from the Neosfera parametric engine. Designed with compact horizontal proportions, vertical presence, and optically compensated counter spaces in heavier weights, it delivers high-impact typography for posters, social media, and hero displays.
</p>
<p>
Available in Regular (400), Bold (700), and Black (900), Neosfera Display pairs seamlessly with Neosfera Serif and Neosfera Sans. To contribute, visit <a href="https://github.com/neosferabr/neosfera-fonts">github.com/neosferabr/neosfera-fonts</a>.
</p>""",
    'neosferadither': """<p>
Neosfera Dither is an experimental display typeface that intersects bold grotesque letterforms with an ordered 8x8 Bayer halftone dither matrix. Regular uses a fine 6px halftone grid with directional tonal gradients, while Bold uses a coarser 12px cellular matrix for striking brutalist and retro-digital textures.
</p>
<p>
To contribute or explore the Neosfera type system, visit <a href="https://github.com/neosferabr/neosfera-fonts">github.com/neosferabr/neosfera-fonts</a>.
</p>""",
    'neosferadithercondensed': """<p>
Neosfera Dither Condensed is the narrow, high-density companion to Neosfera Dither. It combines condensed grotesque proportions and optically compensated vertical stems with an ordered 8x8 Bayer halftone dither matrix in Regular (6px grid) and Bold (12px grid).
</p>
<p>
To contribute or explore the Neosfera type system, visit <a href="https://github.com/neosferabr/neosfera-fonts">github.com/neosferabr/neosfera-fonts</a>.
</p>""",
    'neosferaglitch': """<p>
Neosfera Glitch is a procedural display typeface that slices Bayer-dithered letterforms into displaced horizontal scanbands, echo fragments, and micro-slits. It includes four OpenType stylistic sets (ss01 to ss03 for alternate deterministic glitch seeds, and ss04 for the clean unglitched dither state) so designers can mix multiple glitch states within a single word.
</p>
<p>
To contribute or explore the Neosfera type system, visit <a href="https://github.com/neosferabr/neosfera-fonts">github.com/neosferabr/neosfera-fonts</a>.
</p>""",
    'neosferaglitchcondensed': """<p>
Neosfera Glitch Condensed combines narrow headline proportions, ordered Bayer 8x8 halftone dithering, and procedural horizontal glitch slicing. Equipped with OpenType stylistic sets ss01 through ss04, it enables dynamic multi-state glitch typography in compact vertical layouts.
</p>
<p>
To contribute or explore the Neosfera type system, visit <a href="https://github.com/neosferabr/neosfera-fonts">github.com/neosferabr/neosfera-fonts</a>.
</p>""",
}

def setup_ofl_package(slug, family_name, category, src_ttf_dir, ttf_filenames, copy_line):
    ofl_dir = os.path.join(ROOT, 'google-fonts', 'ofl', slug)
    os.makedirs(ofl_dir, exist_ok=True)
    for fn in os.listdir(ofl_dir):
        if fn.endswith('.ttf'):
            os.remove(os.path.join(ofl_dir, fn))
    for fn in ttf_filenames:
        shutil.copy2(os.path.join(src_ttf_dir, fn), os.path.join(ofl_dir, fn))
    write_ofl(os.path.join(ofl_dir, 'OFL.txt'), copy_line)
    with open(os.path.join(ofl_dir, 'DESCRIPTION.en_us.html'), 'w', encoding='utf-8') as f:
        f.write(DESCRIPTIONS[slug].strip() + '\n')
    write_metadata_pb(ofl_dir, family_name, category, ttf_filenames)

def clean_dir_exts(d, exts=('.ttf', '.woff2')):
    if not os.path.exists(d):
        return
    for fn in os.listdir(d):
        if fn.endswith(exts):
            os.remove(os.path.join(d, fn))

def main():
    print('=== 1. Construindo famílias paramétricas (Neosfera Serif, Sans, Display) ===')
    six_styles = [
        ('Light', False, 'Light'),
        ('Light', True, 'LightItalic'),
        ('Regular', False, 'Regular'),
        ('Regular', True, 'Italic'),
        ('Bold', False, 'Bold'),
        ('Bold', True, 'BoldItalic'),
    ]

    # 1A. Neosfera Serif
    serif_dir = os.path.join(ROOT, 'neosfera-serif')
    clean_dir_exts(os.path.join(serif_dir, 'ttf'))
    clean_dir_exts(os.path.join(serif_dir, 'woff2'))
    serif_ttfs = []
    for w, it, suf in six_styles:
        fn = f'NeosferaSerif-{suf}.ttf'
        wfn = f'NeosferaSerif-{suf}.woff2'
        ng, nb, nt = build_ttf.build_style_font(
            'serif', w, it,
            os.path.join(serif_dir, 'ttf', fn),
            os.path.join(serif_dir, 'woff2', wfn)
        )
        serif_ttfs.append(fn)
        print(f'  [Neosfera Serif] {fn:32} | glifos={ng} | kern={nb} ({nt} expandidos)')
    write_ofl(os.path.join(serif_dir, 'OFL.txt'), build_ttf.COPY)
    setup_ofl_package('neosferaserif', 'Neosfera Serif', 'SERIF', os.path.join(serif_dir, 'ttf'), serif_ttfs, build_ttf.COPY)

    # 1B. Neosfera Sans
    sans_dir = os.path.join(ROOT, 'neosfera-sans')
    clean_dir_exts(os.path.join(sans_dir, 'ttf'))
    clean_dir_exts(os.path.join(sans_dir, 'woff2'))
    sans_ttfs = []
    for w, it, suf in six_styles:
        fn = f'NeosferaSans-{suf}.ttf'
        wfn = f'NeosferaSans-{suf}.woff2'
        ng, nb, nt = build_ttf.build_style_font(
            'sans', w, it,
            os.path.join(sans_dir, 'ttf', fn),
            os.path.join(sans_dir, 'woff2', wfn)
        )
        sans_ttfs.append(fn)
        print(f'  [Neosfera Sans]  {fn:32} | glifos={ng} | kern={nb} ({nt} expandidos)')
    write_ofl(os.path.join(sans_dir, 'OFL.txt'), build_ttf.COPY)
    setup_ofl_package('neosferasans', 'Neosfera Sans', 'SANS_SERIF', os.path.join(sans_dir, 'ttf'), sans_ttfs, build_ttf.COPY)

    # 1C. Neosfera Display
    disp_dir = os.path.join(ROOT, 'neosfera-display')
    clean_dir_exts(os.path.join(disp_dir, 'ttf'))
    clean_dir_exts(os.path.join(disp_dir, 'woff2'))
    disp_ttfs = []
    for w in ('Regular', 'Bold', 'Black'):
        fn = f'NeosferaDisplay-{w}.ttf'
        wfn = f'NeosferaDisplay-{w}.woff2'
        ng, nb, nt = build_ttf.build_style_font(
            'display', w, False,
            os.path.join(disp_dir, 'ttf', fn),
            os.path.join(disp_dir, 'woff2', wfn)
        )
        disp_ttfs.append(fn)
        print(f'  [Neosfera Display] {fn:30} | glifos={ng} | kern={nb} ({nt} expandidos)')
    write_ofl(os.path.join(disp_dir, 'OFL.txt'), build_ttf.COPY)
    setup_ofl_package('neosferadisplay', 'Neosfera Display', 'DISPLAY', os.path.join(disp_dir, 'ttf'), disp_ttfs, build_ttf.COPY)

    # Sync motor/ into neosfera-serif, neosfera-sans, neosfera-display
    for fam_d in (serif_dir, sans_dir, disp_dir):
        m_dst = os.path.join(fam_d, 'motor')
        os.makedirs(m_dst, exist_ok=True)
        for mf in ('grotesk.py', 'family.py', 'build_ttf.py'):
            shutil.copy2(os.path.join(ROOT, 'motor', mf), os.path.join(m_dst, mf))

    print('\n=== 2. Construindo famílias Dither (Neosfera Dither & Neosfera Dither Condensed) ===')
    # 2A. Neosfera Dither
    dither_dir = os.path.join(ROOT, 'neosfera-dither')
    os.makedirs(os.path.join(dither_dir, 'ttf'), exist_ok=True)
    os.makedirs(os.path.join(dither_dir, 'woff2'), exist_ok=True)
    dither_ttfs = []
    for sub in ('Regular', 'Bold'):
        old_src = os.path.join(dither_dir, f'Neosfera-{sub}.ttf')
        src_path = old_src if os.path.exists(old_src) else os.path.join(dither_dir, 'ttf', f'NeosferaDither-{sub}.ttf')
        out_ttf = os.path.join(dither_dir, 'ttf', f'NeosferaDither-{sub}.ttf')
        out_woff2 = os.path.join(dither_dir, 'woff2', f'NeosferaDither-{sub}.woff2')
        ng = bdg.upgrade_dither_font(src_path, 'Neosfera Dither', sub, False, out_ttf, out_woff2)
        dither_ttfs.append(f'NeosferaDither-{sub}.ttf')
        if os.path.exists(old_src):
            os.remove(old_src)
        old_w = os.path.join(dither_dir, f'Neosfera-{sub}.woff2')
        if os.path.exists(old_w):
            os.remove(old_w)
        print(f'  [Neosfera Dither] NeosferaDither-{sub}.ttf | glifos={ng}')
    write_ofl(os.path.join(dither_dir, 'OFL.txt'), bdg.COPY)
    setup_ofl_package('neosferadither', 'Neosfera Dither', 'DISPLAY', os.path.join(dither_dir, 'ttf'), dither_ttfs, bdg.COPY)

    # 2B. Neosfera Dither Condensed
    ditherc_dir = os.path.join(ROOT, 'neosfera-dither-condensed')
    os.makedirs(os.path.join(ditherc_dir, 'ttf'), exist_ok=True)
    os.makedirs(os.path.join(ditherc_dir, 'woff2'), exist_ok=True)
    ditherc_ttfs = []
    for sub in ('Regular', 'Bold'):
        old_src = os.path.join(ditherc_dir, f'NeosferaCondensed-{sub}.ttf')
        src_path = old_src if os.path.exists(old_src) else os.path.join(ditherc_dir, 'ttf', f'NeosferaDitherCondensed-{sub}.ttf')
        out_ttf = os.path.join(ditherc_dir, 'ttf', f'NeosferaDitherCondensed-{sub}.ttf')
        out_woff2 = os.path.join(ditherc_dir, 'woff2', f'NeosferaDitherCondensed-{sub}.woff2')
        ng = bdg.upgrade_dither_font(src_path, 'Neosfera Dither Condensed', sub, True, out_ttf, out_woff2)
        ditherc_ttfs.append(f'NeosferaDitherCondensed-{sub}.ttf')
        if os.path.exists(old_src):
            os.remove(old_src)
        old_w = os.path.join(ditherc_dir, f'NeosferaCondensed-{sub}.woff2')
        if os.path.exists(old_w):
            os.remove(old_w)
        print(f'  [Neosfera Dither Condensed] NeosferaDitherCondensed-{sub}.ttf | glifos={ng}')
    write_ofl(os.path.join(ditherc_dir, 'OFL.txt'), bdg.COPY)
    setup_ofl_package('neosferadithercondensed', 'Neosfera Dither Condensed', 'DISPLAY', os.path.join(ditherc_dir, 'ttf'), ditherc_ttfs, bdg.COPY)

    print('\n=== 3. Construindo famílias Glitch (Neosfera Glitch & Neosfera Glitch Condensed) ===')
    glitch_dir = os.path.join(ROOT, 'neosfera-glitch')
    clean_dir_exts(glitch_dir)
    clean_dir_exts(os.path.join(glitch_dir, 'ttf'))
    clean_dir_exts(os.path.join(glitch_dir, 'woff2'))
    clean_dir_exts(os.path.join(glitch_dir, 'estados'))
    os.makedirs(os.path.join(glitch_dir, 'ttf'), exist_ok=True)
    os.makedirs(os.path.join(glitch_dir, 'woff2'), exist_ok=True)
    os.makedirs(os.path.join(glitch_dir, 'estados'), exist_ok=True)

    glitch_configs = [
        (os.path.join(dither_dir, 'ttf', 'NeosferaDither-Regular.ttf'), 'nr', 0.50, 'Neosfera Glitch', 'Regular', False),
        (os.path.join(dither_dir, 'ttf', 'NeosferaDither-Bold.ttf'), 'nb', 0.50, 'Neosfera Glitch', 'Bold', False),
        (os.path.join(ditherc_dir, 'ttf', 'NeosferaDitherCondensed-Regular.ttf'), 'cr', 0.32, 'Neosfera Glitch Condensed', 'Regular', True),
        (os.path.join(ditherc_dir, 'ttf', 'NeosferaDitherCondensed-Bold.ttf'), 'cb', 0.32, 'Neosfera Glitch Condensed', 'Bold', True),
    ]
    g_norm_ttfs = []
    g_cond_ttfs = []
    for base_p, key, amp, fam, sub, is_cond in glitch_configs:
        ps_fam = fam.replace(' ', '')
        fn = f'{ps_fam}-{sub}.ttf'
        wfn = f'{ps_fam}-{sub}.woff2'
        out_ttf = os.path.join(glitch_dir, 'ttf', fn)
        out_woff2 = os.path.join(glitch_dir, 'woff2', wfn)
        ng = bdg.build_glitch_combined(base_p, key, amp, fam, sub, is_cond, out_ttf, out_woff2)
        if is_cond:
            g_cond_ttfs.append(fn)
        else:
            g_norm_ttfs.append(fn)
        print(f'  [{fam}] {fn:38} | glifos={ng}')
        for st in (1, 2, 3, 4):
            f_st = f'{fam} {st}'
            ps_st = f_st.replace(' ', '')
            st_ttf = os.path.join(glitch_dir, 'estados', f'{ps_st}-{sub}.ttf')
            st_woff2 = os.path.join(glitch_dir, 'estados', f'{ps_st}-{sub}.woff2')
            bdg.build_glitch_state(base_p, key, amp, st, f_st, sub, is_cond, st_ttf, st_woff2)

    write_ofl(os.path.join(glitch_dir, 'OFL.txt'), bdg.COPY)
    setup_ofl_package('neosferaglitch', 'Neosfera Glitch', 'DISPLAY', os.path.join(glitch_dir, 'ttf'), g_norm_ttfs, bdg.COPY)
    setup_ofl_package('neosferaglitchcondensed', 'Neosfera Glitch Condensed', 'DISPLAY', os.path.join(glitch_dir, 'ttf'), g_cond_ttfs, bdg.COPY)
    print('\n=== Build concluído com sucesso! ===')

if __name__ == '__main__':
    main()

