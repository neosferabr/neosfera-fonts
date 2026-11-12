"""Neosfera Condensed Sans Display — Regular / Bold / Black. Mesmo motor da Grotesk Serif, sem serifa, mais vertical."""
import sys, os
import grotesk as g
STYLES = {
    'Regular': dict(p=dict(W=92,  thick=44, slen=0, rv=15, rc=8,  diag=78,  bar=84,  G=74), sxb=0.70, sxc=0.64, wclass=400),
    'Bold':    dict(p=dict(W=112, thick=52, slen=0, rv=17, rc=9,  diag=96,  bar=102, G=78), sxb=0.73, sxc=0.67, wclass=700),
    'Black':   dict(p=dict(W=134, thick=60, slen=0, rv=19, rc=10, diag=116, bar=122, G=82), sxb=0.76, sxc=0.70, wclass=900),
}
style = sys.argv[1] if len(sys.argv) > 1 else 'Regular'
S = STYLES[style]
g.SERIFS = False; g.SX_BASE = S['sxb']; g.CAPS_SX = S['sxc']; g.SX = S['sxb']
g.WEIGHTS[style] = dict(S['p'])
g.SX_BONUS = dict(v=.08, w=.10, x=.08, y=.08, z=.06, V=.07, W=.09, X=.07, Y=.06, Z=.05, A=.05, K=.05, M=.04, k=.04)
import build_ttf, family as F
build_ttf.FAM = 'Neosfera Condensed Sans Display'
meta = dict(ps=f'NeosferaCondensedSansDisplay-{style}', wclass=S['wclass'], wwidth=3)
out = sys.argv[2] if len(sys.argv) > 2 else f'ttf/NeosferaCondensedSansDisplay-{style}.ttf'
os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
print(out, 'kern', build_ttf.build(style, False, out, meta))
