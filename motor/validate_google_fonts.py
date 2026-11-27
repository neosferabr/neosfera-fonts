"""Validador automatizado de conformidade com o Google Fonts (regras equivalentes ao FontBakery googlefonts profile)."""
import os, sys, glob
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFL_ROOT = os.path.join(ROOT, 'google-fonts', 'ofl')

GF_LATIN_CORE = (
    set(range(0x20, 0x7F))
    | set(range(0xA0, 0x100))
    | {
        0x0131, 0x0152, 0x0153, 0x0160, 0x0161, 0x0178, 0x017D, 0x017E, 0x0192, 0x0237,
        0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0306, 0x0307, 0x0308, 0x030A, 0x030B, 0x030C,
        0x0326, 0x0327, 0x0328,
        0x02C6, 0x02C7, 0x02D8, 0x02D9, 0x02DA, 0x02DB, 0x02DC, 0x02DD, 0x1E9E,
        0x2013, 0x2014, 0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E, 0x2020, 0x2021,
        0x2022, 0x2026, 0x2030, 0x2039, 0x203A, 0x2044, 0x20AC, 0x2122, 0x2212, 0xFB01, 0xFB02,
    }
)

REQUIRED_TABLES = ('cmap', 'glyf', 'head', 'hhea', 'hmtx', 'loca', 'maxp', 'name', 'OS/2', 'post', 'gasp', 'STAT')

def check_family_dir(slug_dir):
    slug = os.path.basename(slug_dir)
    errors = []
    warnings = []

    for req_file in ('OFL.txt', 'DESCRIPTION.en_us.html', 'METADATA.pb'):
        p = os.path.join(slug_dir, req_file)
        if not os.path.exists(p):
            errors.append(f'[{slug}] Arquivo obrigatório ausente: {req_file}')

    desc_path = os.path.join(slug_dir, 'DESCRIPTION.en_us.html')
    if os.path.exists(desc_path):
        txt = open(desc_path, encoding='utf-8').read().strip()
        if not (200 <= len(txt) <= 1200):
            warnings.append(f'[{slug}] DESCRIPTION.en_us.html tamanho fora do ideal ({len(txt)} chars)')
        if '<p>' not in txt or '</p>' not in txt:
            errors.append(f'[{slug}] DESCRIPTION.en_us.html deve conter tags <p>...</p>')

    ttfs = sorted(glob.glob(os.path.join(slug_dir, '*.ttf')))
    if not ttfs:
        errors.append(f'[{slug}] Nenhum arquivo .ttf encontrado')
        return errors, warnings, 0

    vmetrics_set = set()
    for ttf_path in ttfs:
        fn = os.path.basename(ttf_path)
        f = TTFont(ttf_path)

        # 1. Required & Forbidden tables
        for tbl in REQUIRED_TABLES:
            if tbl not in f:
                errors.append(f'[{fn}] Tabela obrigatória ausente: {tbl}')
        if 'DSIG' in f:
            errors.append(f'[{fn}] Tabela DSIG obsoleta presente')

        # 2. OS/2 & hhea checks
        os2 = f['OS/2']
        hhea = f['hhea']
        head = f['head']
        post = f['post']

        if os2.fsType != 0:
            errors.append(f'[{fn}] OS/2.fsType deve ser 0 (encontrado {os2.fsType})')
        if not (os2.fsSelection & 0x80):
            errors.append(f'[{fn}] OS/2.fsSelection bit 7 (USE_TYPO_METRICS) não ativado')
        if os2.achVendID.strip() != 'NEOS':
            errors.append(f'[{fn}] OS/2.achVendID inesperado: {os2.achVendID!r}')
        if hhea.ascent != os2.sTypoAscender or hhea.descent != os2.sTypoDescender:
            errors.append(f'[{fn}] hhea ({hhea.ascent}/{hhea.descent}) != OS/2 sTypo ({os2.sTypoAscender}/{os2.sTypoDescender})')
        if hhea.lineGap != 0 or os2.sTypoLineGap != 0:
            errors.append(f'[{fn}] lineGap deve ser 0')

        vmetrics_set.add((hhea.ascent, hhea.descent, os2.usWinAscent, os2.usWinDescent))

        # 3. Version & Revision
        if round(head.fontRevision, 3) != 1.0:
            errors.append(f'[{fn}] head.fontRevision ({head.fontRevision}) != 1.0')
        if post.isFixedPitch != 0:
            errors.append(f'[{fn}] post.isFixedPitch deve ser 0')

        # 4. Name table checks
        nm = f['name']
        platforms = {r.platformID for r in nm.names}
        if platforms != {3}:
            errors.append(f'[{fn}] name table deve conter apenas platformID=3 (encontrado {platforms})')
        for nid in (0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14):
            if not nm.getDebugName(nid):
                errors.append(f'[{fn}] NameID {nid} ausente')

        # 5. Glyphs & GF_Latin_Core coverage
        order = f.getGlyphOrder()
        if order[0] != '.notdef' or f['glyf']['.notdef'].numberOfContours == 0:
            errors.append(f'[{fn}] .notdef inválido ou sem contorno')

        cmap = f.getBestCmap()
        if cmap.get(0x20) != 'space' or cmap.get(0xA0) != 'uni00A0':
            errors.append(f'[{fn}] Mapeamento de espaço (0x20->space, 0xA0->uni00A0) incorreto')
        if f['hmtx']['space'][0] != f['hmtx']['uni00A0'][0]:
            errors.append(f'[{fn}] Largura de space e uni00A0 divergente')

        missing_core = GF_LATIN_CORE - set(cmap.keys())
        if missing_core:
            errors.append(f'[{fn}] Faltam {len(missing_core)} codepoints do GF_Latin_Core: {[hex(u) for u in sorted(missing_core)]}')

    if len(vmetrics_set) > 1:
        errors.append(f'[{slug}] Métricas verticais inconsistentes entre estilos da família: {vmetrics_set}')

    return errors, warnings, len(ttfs)

def main():
    slugs = sorted(os.listdir(OFL_ROOT))
    total_ttfs = 0
    all_errors = []
    all_warnings = []
    print('=== Auditoria Google Fonts QA (Neosfera Type System) ===')
    for s in slugs:
        sdir = os.path.join(OFL_ROOT, s)
        if not os.path.isdir(sdir):
            continue
        errs, warns, n_ttfs = check_family_dir(sdir)
        total_ttfs += n_ttfs
        all_errors.extend(errs)
        all_warnings.extend(warns)
        status = 'PASS (0 erros)' if not errs else f'FAIL ({len(errs)} erros)'
        print(f'  • ofl/{s:26} | {n_ttfs} TTFs | {status}')
    for w in all_warnings:
        print('  WARN:', w)
    for e in all_errors:
        print('  ERROR:', e)
    print(f'\nTotal auditado: {len(slugs)} famílias, {total_ttfs} arquivos TTF, {len(all_errors)} erros, {len(all_warnings)} avisos.')
    sys.exit(1 if all_errors else 0)

if __name__ == '__main__':
    main()

