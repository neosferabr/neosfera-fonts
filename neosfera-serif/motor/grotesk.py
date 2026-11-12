"""Neosfera Type System — Motor Paramétrico Unificado (Serif, Sans, Display).
Esqueleto (linha central) -> traço monolinear com corte reto -> meia-serifa opcional
(topo para trás, pé para frente) -> cantos levemente arredondados.
Suporte completo a GF Latin Core + Latin-1 + Latin Extended-A."""
import math
import pathops
from pathops import Path, PathOp, LineCap, LineJoin

XH, ASC, DSC, CAP = 520, 730, -200, 700
OV = 10
SX = 0.90
SX_BASE, CAPS_SX = 0.90, 0.84
SX_BONUS = {}
SERIFS = True
ITALIC_ANGLE = 10.0
ITALIC_SINGLE_A = False

WEIGHTS = {
    'Light':   dict(W=60,  thick=30, slen=50, rv=10, rc=6,  diag=52,  bar=56,  G=54),
    'Regular': dict(W=84,  thick=40, slen=56, rv=14, rc=8,  diag=70,  bar=78,  G=58),
    'Bold':    dict(W=116, thick=54, slen=60, rv=18, rc=10, diag=98,  bar=106, G=64),
    'Black':   dict(W=134, thick=60, slen=62, rv=19, rc=10, diag=116, bar=122, G=82),
}
P = {}
W = HW = DIAG = BAR = 0

def set_weight(name):
    global W, HW, DIAG, BAR, P
    P = dict(WEIGHTS[name])
    W = P['W']; HW = W / 2; DIAG = P['diag']; BAR = P['bar']

# ---------------------------------------------------------------- primitivas
def skel(cmds, sx=None):
    s = SX if sx is None else sx
    p = Path()
    f = lambda v: [v[i] * s if i % 2 == 0 else v[i] for i in range(len(v))]
    for c in cmds:
        if c[0] == 'M': p.moveTo(*f(c[1:]))
        elif c[0] == 'L': p.lineTo(*f(c[1:]))
        elif c[0] == 'C': p.cubicTo(*f(c[1:]))
        elif c[0] == 'Z': p.close()
    return p

def stroke(p, w=None, cap=LineCap.BUTT_CAP, join=LineJoin.MITER_JOIN):
    q = Path(); q.addPath(p); q.stroke(W if w is None else w, cap, join, 4)
    q.convertConicsToQuads(); q.simplify(fix_winding=True); return q

def rect(x0, y0, x1, y1):
    p = Path(); p.moveTo(x0, y0); p.lineTo(x1, y0); p.lineTo(x1, y1); p.lineTo(x0, y1); p.close(); return p

def union(paths):
    out = Path()
    for p in paths: out.addPath(p)
    out.simplify(fix_winding=True); return out

def op(a, b, o): return pathops.op(a, b, o, fix_winding=True)

def ring(cx, cy, rx, ry, k=0.6, sx=None):
    kx, ky = rx * k, ry * k
    return skel([('M', cx + rx, cy), ('C', cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry),
                 ('C', cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy),
                 ('C', cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry),
                 ('C', cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy), ('Z',)], sx=sx)

def round_corners(p, rv, rc):
    for scale in (1.0, 0.8, 0.6, 0.0):
        if scale == 0.0:
            return p
        try:
            q = Path(); q.addPath(p)
            rv_s, rc_s = rv * scale, rc * scale
            if rv_s:
                e = op(q, stroke(q, 2 * rv_s, LineCap.BUTT_CAP, LineJoin.ROUND_JOIN), PathOp.DIFFERENCE)
                if len(list(e.contours)):
                    q = union([e, stroke(e, 2 * rv_s, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN)])
            if rc_s:
                d = union([q, stroke(q, 2 * rc_s, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN)])
                res = op(d, stroke(d, 2 * rc_s, LineCap.BUTT_CAP, LineJoin.ROUND_JOIN), PathOp.DIFFERENCE)
                if len(list(res.contours)):
                    q = res
            return q
        except Exception:
            continue
    return p

def clip(path, lo, hi, w=None):
    if w is None:
        bx0, by0, bx1, by1 = path.bounds
        L = math.hypot(bx1 - bx0, by1 - by0)
        cos_t = max(0.55, (by1 - by0) / L) if L > 0 else 1.0
        w = W * (cos_t ** 0.85)
    return op(stroke(path, w), rect(-900, lo, 1900, hi), PathOp.INTERSECTION)

def dline(x0, y0, x1, y1, lo, hi, scale=1.0, up_boost=0.0):
    dx = (x1 - x0) * SX
    dy = y1 - y0
    L = math.hypot(dx, dy)
    cos_t = max(0.55, abs(dy) / L) if L > 0 else 1.0
    mult = (1.0 + up_boost) if (dx * dy > 0) else (1.0 - up_boost * 0.3)
    w = W * scale * (cos_t ** 0.85) * mult
    return op(stroke(skel([('M', x0, y0), ('L', x1, y1)]), w), rect(-900, lo, 1900, hi), PathOp.INTERSECTION)

def hbar(x0, x1, y, w=None): return stroke(skel([('M', x0, y), ('L', x1, y)]), BAR if w is None else w)
def dot(x, y0):  # pingo quadrado (o "pixel")
    s = W + 8; xc = x * SX
    return rect(xc - s / 2, y0, xc + s / 2, y0 + s)

def serif(x, y, side, kind):
    s, t = P['slen'], P['thick']; xc = x * SX
    if side == 'b': s = s * 0.72
    x0 = xc - HW - (s if side in 'bl' else 0); x1 = xc + HW + (s if side in 'br' else 0)
    return rect(x0, y, x1, y + t) if kind == 'foot' else rect(x0, y - t, x1, y)

def G(sk=(), solid=(), top=(), foot=(), full_top=(), full_foot=(), ws=1.0):
    return dict(sk=list(sk), solid=list(solid), top=list(top), foot=list(foot), full_top=list(full_top), full_foot=list(full_foot), ws=ws)

# medidas que dependem do peso
def T_(): return XH - HW + OV           # centro do topo de curva (x-height)
def B_(): return HW - OV                # centro do fundo de curva
def TC(): return CAP - HW + OV          # centro do topo de curva (versal)
def FB(): return BAR / 2                # centro de barra apoiada na base
def FT(h=CAP): return h - BAR / 2       # centro de barra encostada no topo

# ================================================================= minúsculas
def _bowl_r():
    t, b = T_(), B_()
    return skel([('M', 0, 400), ('C', 28, 466, 98, t, 194, t), ('C', 312, t, 400, 400, 400, 258), ('C', 400, 110, 312, b, 194, b), ('C', 98, b, 28, 56, 0, 120)])
def _bowl_l():
    t, b = T_(), B_()
    return skel([('M', 400, 400), ('C', 372, 466, 302, t, 206, t), ('C', 88, t, 0, 400, 0, 258), ('C', 0, 110, 88, b, 206, b), ('C', 302, b, 372, 56, 400, 120)])
def _bowl_g():
    t = T_()
    return skel([('M', 400, 400), ('C', 372, 466, 302, t, 206, t), ('C', 88, t, 0, 400, 0, 266), ('C', 0, 126, 88, 50, 206, 50), ('C', 310, 50, 380, 70, 400, 112)])
def _arch(x0, w):
    t = T_()
    return skel([('M', x0, 360), ('C', x0 + 28 * w / 400, 452, x0 + 110 * w / 400, t, x0 + 210 * w / 400, t), ('C', x0 + 330 * w / 400, t, x0 + w, 440, x0 + w, 330), ('L', x0 + w, 0)])
def _stem(x, y0, y1): return skel([('M', x, y0), ('L', x, y1)])

def g_a():
    t, b = T_(), B_()
    return G(sk=[skel([('M', 380, 0), ('L', 380, 336), ('C', 380, 446, 305, t, 196, t), ('C', 102, t, 40, 456, 22, 392)]),
                 skel([('M', 380, 286), ('C', 250, 286, 26, 276, 26, 148), ('C', 26, 72, 86, b, 168, b), ('C', 270, b, 340, 96, 380, 128)])],
             foot=[(380, 0)])
def g_a_ital():
    return G(sk=[_stem(400, 0, XH), _bowl_l()], foot=[(400, 0)])
def g_b(): return G(sk=[_stem(0, 0, ASC), _bowl_r()], top=[(0, ASC)])
def g_c():
    t, b = T_(), B_()
    return G(sk=[skel([('M', 420, 362), ('C', 400, 448, 330, t, 218, t), ('C', 92, t, 0, 400, 0, 258), ('C', 0, 110, 92, b, 220, b), ('C', 330, b, 400, 72, 420, 158)])])
def g_d(): return G(sk=[_stem(400, 0, ASC), _bowl_l()], top=[(400, ASC)], foot=[(400, 0)])
def g_e():
    t, b = T_(), B_(); yb = 268
    y0 = yb if SERIFS else yb - BAR / 2
    return G(sk=[skel([('M', 0, yb), ('L', 436, yb)]),
                 skel([('M', 436, y0), ('L', 436, yb), ('C', 436, 420, 345, t, 218, t), ('C', 92, t, 0, 400, 0, 258), ('C', 0, 110, 92, b, 222, b), ('C', 325, b, 400, 78, 424, 158)])])
def g_f():
    return G(sk=[skel([('M', 0, 0), ('L', 0, 580), ('C', 0, 664, 46, ASC - HW, 134, ASC - HW), ('L', 214, ASC - HW)]),
                 skel([('M', -78 if SERIFS else -125, XH - HW + 2), ('L', 168, XH - HW + 2)])], foot=[(0, 0)])
def g_g():
    return G(sk=[skel([('M', 400, XH + OV), ('L', 400, -70), ('C', 400, -130, 372, DSC + HW, 300, DSC + HW), ('L', 40, DSC + HW)]), _bowl_g()])
def g_h(): return G(sk=[_stem(0, 0, ASC), _arch(0, 400)], top=[(0, ASC)], foot=[(0, 0), (400, 0)])
def g_dotlessi(): return G(sk=[_stem(0, 0, XH)], top=[(0, XH)], foot=[(0, 0)])
def g_i():
    g = g_dotlessi(); g['solid'].append(dot(0, ASC - W - 8)); return g
def g_dotlessj():
    return G(sk=[skel([('M', 0, XH), ('L', 0, -70), ('C', 0, -130, -28, DSC + HW, -100, DSC + HW), ('L', -190, DSC + HW)])],
             top=[(0, XH)])
def g_j():
    g = g_dotlessj(); g['solid'].append(dot(0, ASC - W - 8)); return g
def _leg_from_arm(a0, a1, l0, l1, lo, hi, w):
    ax, ay = a1[0] - a0[0], a1[1] - a0[1]; lx, ly = l1[0] - l0[0], l1[1] - l0[1]
    start = (l0[0] - 0.45 * lx, l0[1] - 0.45 * ly)
    leg = stroke(skel([('M', *start), ('L', *l1)]), w)
    P1 = (a0[0] - 3 * ax, a0[1] - 3 * ay); P2 = (a0[0] + 4 * ax, a0[1] + 4 * ay)
    half = skel([('M', *P1), ('L', *P2), ('L', P2[0] + 4000, P2[1] - 4000), ('L', P1[0] + 4000, P1[1] - 4000), ('Z',)])
    leg = op(leg, half, PathOp.INTERSECTION)
    return op(leg, rect(-900, lo, 1900, hi), PathOp.INTERSECTION)

def g_k():
    arm = dline(400, 600, -14, 146, 0, XH, 1.0, 0.03)
    leg = _leg_from_arm((44, 210), (400, 600), (150, 318), (420, -56), 0, XH, W * 0.96)
    return G(sk=[_stem(0, 0, ASC)], solid=[arm, leg], top=[(0, ASC)], foot=[(0, 0)])
def g_l(): return G(sk=[_stem(0, 0, ASC)], top=[(0, ASC)], foot=[(0, 0)])
def g_m(): return G(sk=[_stem(0, 0, XH), _arch(0, 330), _arch(330, 330)], top=[(0, XH)], foot=[(0, 0), (330, 0), (660, 0)])
def g_n(): return G(sk=[_stem(0, 0, XH), _arch(0, 400)], top=[(0, XH)], foot=[(0, 0), (400, 0)])
def g_o(): return G(sk=[ring(218, 260, 218, 260 - HW + OV)])
def g_p(): return G(sk=[_stem(0, DSC, XH), _bowl_r()], top=[(0, XH)], foot=[(0, DSC)])
def g_q(): return G(sk=[_stem(400, DSC, XH), _bowl_l()], foot=[(400, DSC)])
def g_r():
    t = T_()
    return G(sk=[_stem(0, 0, XH), skel([('M', 0, 360), ('C', 28, 452, 108, t, 200, t), ('C', 246, t, 280, XH - HW + 2, 300, XH - HW - 8)])],
             top=[(0, XH)], foot=[(0, 0)])
def g_s():
    t, b = T_(), B_()
    return G(sk=[skel([('M', 388, 392), ('C', 372, 462, 305, t, 200, t), ('C', 95, t, 30, 440, 30, 378),
                       ('C', 30, 300, 105, 284, 205, 266), ('C', 318, 246, 396, 218, 396, 140),
                       ('C', 396, 66, 318, b, 200, b), ('C', 85, b, 16, 66, 2, 146)])])
def g_t():
    return G(sk=[skel([('M', 0, 660), ('L', 0, 120), ('C', 0, 52, 40, HW - 2, 110, HW - 2), ('L', 176, HW - 2)]),
                 skel([('M', -78 if SERIFS else -125, XH - HW + 2), ('L', 158, XH - HW + 2)])])
def g_u():
    b = B_()
    return G(sk=[skel([('M', 0, XH), ('L', 0, 190), ('C', 0, 80, 80, b, 195, b), ('C', 300, b, 372, 68, 400, 160)]), _stem(400, 0, XH)],
             top=[(0, XH), (400, XH)], foot=[(400, 0)])
def g_v():
    return G(solid=[dline(-22, 640, 224, -40, 0, XH, 1.0, 0.04),
                    dline(482, 640, 236, -40, 0, XH, 1.0, 0.04)])
def g_w():
    pts = [(0, 620), (152, -30), (310, 595), (468, -30), (620, 620)]
    return G(solid=[dline(*pts[i], *pts[i + 1], 0, XH, 0.94, 0.03) for i in range(4)])
def g_x():
    return G(solid=[dline(-43, 600, 491, -80, 0, XH, 0.96, 0.03),
                    dline(491, 600, -43, -80, 0, XH, 0.96, 0.03)])
def g_y():
    tail = op(stroke(skel([('M', 482, 640), ('L', 214, -76), ('C', 196, -126, 176, DSC + HW, 130, DSC + HW), ('L', 20, DSC + HW)]), W * 0.95), rect(-900, DSC - 10, 1900, XH), PathOp.INTERSECTION)
    return G(solid=[dline(-22, 640, 236, -50, 0, XH, 0.96, 0.02), tail])
def g_z():
    diag = dline(444, XH + 40, 16, -40, 20, XH - 20, 0.96, 0.02)
    return G(solid=[hbar(24, 432, XH - BAR / 2), hbar(20, 440, BAR / 2), diag])

# ================================================================= maiúsculas
def g_A():
    return G(solid=[dline(318, 725, 0, -40, 0, CAP, 1.0, 0.02),
                    dline(342, 725, 660, -40, 0, CAP, 1.0, 0.02),
                    hbar(130, 530, 195, BAR * 0.94)])
def _B_bowls():
    m = 382; t, b = CAP - HW, HW
    return [skel([('M', 0, t), ('L', 250, t), ('C', 360, t, 420, 620, 420, 530), ('C', 420, 440, 360, m, 250, m), ('L', 0, m)]),
            skel([('M', 0, m), ('L', 270, m), ('C', 396, m, 460, 310, 460, 210), ('C', 460, 100, 396, b, 270, b), ('L', 0, b)])]
def g_B(): return G(sk=[_stem(0, 0, CAP)] + _B_bowls())
def g_C():
    t, b = TC(), B_()
    return G(sk=[skel([('M', 560, 520), ('C', 530, 640, 440, t, 318, t), ('C', 140, t, 30, 560, 30, 350),
                       ('C', 30, 140, 140, b, 318, b), ('C', 440, b, 530, 60, 560, 180)])])
def g_D():
    return G(sk=[_stem(0, 0, CAP), skel([('M', 0, CAP - HW), ('L', 220, CAP - HW), ('C', 430, CAP - HW, 540, 540, 540, 350), ('C', 540, 160, 430, HW, 220, HW), ('L', 0, HW)])])
def g_E(): return G(sk=[_stem(0, 0, CAP)], solid=[hbar(-HW / SX + 4, 430, FT()), hbar(0, 390, 362), hbar(-HW / SX + 4, 440, FB())])
def g_F(): return G(sk=[_stem(0, 0, CAP)], solid=[hbar(-HW / SX + 4, 430, FT()), hbar(0, 390, 352)], foot=[(0, 0)])
def g_G():
    t, b = TC(), B_()
    return G(sk=[skel([('M', 560, 520), ('C', 530, 640, 440, t, 318, t), ('C', 140, t, 30, 560, 30, 350),
                       ('C', 30, 140, 140, b, 318, b), ('C', 430, b, 520, 50, 560, 120), ('L', 560, 330)])],
             solid=[hbar(330, 560 + HW / SX, 330)])
def g_H(): return G(sk=[_stem(0, 0, CAP), _stem(480, 0, CAP)], solid=[hbar(0, 480, 362)], top=[(0, CAP), (480, CAP)], foot=[(0, 0), (480, 0)])
def g_I(): return G(sk=[_stem(0, 0, CAP)], full_top=[(0, CAP)], full_foot=[(0, 0)])
def g_J():
    return G(sk=[skel([('M', 300, CAP), ('L', 300, 150), ('C', 300, 86, 272, HW, 200, HW), ('L', 24, HW)])], top=[(300, CAP)])
def g_K():
    arm = dline(520, 780, -10, 182, 0, CAP, 0.98, 0.03)
    leg = _leg_from_arm((50, 250), (520, 780), (190, 410), (560, -60), 0, CAP, W * 0.94)
    return G(sk=[_stem(0, 0, CAP)], solid=[arm, leg], top=[(0, CAP)], foot=[(0, 0)])
def g_L(): return G(sk=[_stem(0, 0, CAP)], solid=[hbar(-HW / SX + 4, 430, FB())], top=[(0, CAP)])
def g_M():
    return G(solid=[
        stroke(_stem(0, 0, CAP), W * 0.97),
        stroke(_stem(680, 0, CAP), W * 0.97),
        dline(28, 720, 340, 60, 60, CAP, 0.93, 0.03),
        dline(652, 720, 340, 60, 60, CAP, 0.93, 0.03),
    ], foot=[(0, 0), (680, 0)])
def g_N():
    return G(sk=[_stem(0, 0, CAP), _stem(520, 0, CAP)],
             solid=[dline(-10, 760, 530, -60, 0, CAP, 0.96, 0.0)],
             foot=[(0, 0)], top=[(520, CAP)])
def g_O(): return G(sk=[ring(320, 350, 300, 350 - HW + OV)])
def g_P():
    m = 330
    return G(sk=[_stem(0, 0, CAP), skel([('M', 0, CAP - HW), ('L', 260, CAP - HW), ('C', 390, CAP - HW, 460, 610, 460, 515), ('C', 460, 420, 390, m, 260, m), ('L', 0, m)])],
             foot=[(0, 0)])
def g_Q():
    g = g_O(); g['solid'].append(clip(skel([('M', 360, 210), ('L', 640, -110)]), -100, 300)); return g
def g_R():
    g = g_P(); g['solid'].append(dline(210, 340, 500, -60, 0, 330, 0.98, 0.0)); return g
def g_S():
    t, b = TC(), B_()
    return G(sk=[skel([('M', 500, 540), ('C', 480, 640, 400, t, 270, t), ('C', 140, t, 50, 630, 50, 530),
                       ('C', 50, 420, 140, 390, 270, 362), ('C', 410, 332, 510, 290, 510, 190),
                       ('C', 510, 90, 410, b, 270, b), ('C', 120, b, 30, 80, 14, 180)])])
def g_T(): return G(sk=[_stem(270, 0, FT())], solid=[hbar(0, 540, FT())], foot=[(270, 0)])
def g_U():
    b = B_()
    return G(sk=[skel([('M', 0, CAP), ('L', 0, 250), ('C', 0, 110, 100, b, 255, b), ('C', 410, b, 510, 110, 510, 250), ('L', 510, CAP)])],
             top=[(0, CAP), (510, CAP)])
def g_V():
    return G(solid=[dline(0, 740, 298, -15, 0, CAP, 1.0, 0.04),
                    dline(620, 740, 322, -15, 0, CAP, 1.0, 0.04)])
def g_W():
    pts = [(0, 720), (195, -15), (410, 690), (625, -15), (820, 720)]
    return G(solid=[dline(*pts[i], *pts[i + 1], 0, CAP, 0.94, 0.03) for i in range(4)])
def g_X():
    return G(solid=[dline(0, 760, 560, -60, 0, CAP, 0.98, 0.03),
                    dline(560, 760, 0, -60, 0, CAP, 0.98, 0.03)])
def g_Y():
    return G(sk=[_stem(290, 0, 330)],
             solid=[dline(-10, 780, 300, 300, 300, CAP, 1.0, 0.03),
                    dline(590, 780, 280, 300, 300, CAP, 1.0, 0.03)],
             foot=[(290, 0)])
def g_Z():
    diag = dline(520, CAP + 40, 20, -40, 30, CAP - 30, 0.98, 0.02)
    return G(solid=[hbar(26, 510, FT()), hbar(20, 530, FB()), diag])

# ================================================================= letras especiais Latin-1 / Extended-A
def g_AE():
    return G(sk=[_stem(380, 0, CAP)],
             solid=[clip(skel([('M', 380, 760), ('L', 0, -40)]), 0, CAP),
                    hbar(90, 380, 230),
                    hbar(380 - HW / SX + 4, 680, FT()),
                    hbar(380, 640, 362),
                    hbar(380 - HW / SX + 4, 690, FB())])
def g_ae():
    t, b = T_(), B_(); yb = 268
    return G(sk=[skel([('M', 350, 336), ('C', 350, 446, 280, t, 180, t), ('C', 96, t, 36, 456, 20, 392)]),
                 skel([('M', 350, 286), ('C', 230, 286, 20, 276, 20, 148), ('C', 20, 72, 76, b, 156, b), ('C', 245, b, 310, 96, 350, 140)]),
                 skel([('M', 350, yb), ('L', 690, yb)]),
                 skel([('M', 690, yb), ('C', 690, 420, 610, t, 505, t), ('C', 400, t, 350, 400, 350, 258), ('C', 350, 110, 415, b, 515, b), ('C', 605, b, 668, 78, 684, 158)])])
def g_OE():
    t, b = TC(), B_()
    return G(sk=[skel([('M', 380, CAP - HW), ('L', 310, t), ('C', 140, t, 30, 560, 30, 350), ('C', 30, 140, 140, b, 310, b), ('L', 380, HW)]),
                 _stem(380, 0, CAP)],
             solid=[hbar(380 - HW / SX + 4, 680, FT()),
                    hbar(380, 630, 362),
                    hbar(380 - HW / SX + 4, 690, FB())])
def g_oe():
    t, b = T_(), B_(); yb = 268
    return G(sk=[ring(200, 260, 200, 260 - HW + OV),
                 skel([('M', 360, yb), ('L', 720, yb)]),
                 skel([('M', 720, yb), ('C', 720, 420, 640, t, 535, t), ('C', 420, t, 360, 400, 360, 258), ('C', 360, 110, 430, b, 540, b), ('C', 630, b, 695, 78, 712, 158)])])
def g_Oslash():
    g = g_O()
    g['solid'].append(clip(skel([('M', 40, -60), ('L', 600, CAP + 60)]), -40, CAP + 40, DIAG * 0.9))
    return g
def g_oslash():
    g = g_o()
    g['solid'].append(clip(skel([('M', 10, -50), ('L', 426, XH + 50)]), -30, XH + 30, DIAG * 0.9))
    return g
def g_Lslash():
    g = g_L()
    g['solid'].append(stroke(skel([('M', -110, 280), ('L', 160, 430)]), BAR * 0.88))
    return g
def g_lslash():
    g = g_l()
    g['solid'].append(stroke(skel([('M', -110, 300), ('L', 120, 430)]), BAR * 0.88))
    return g
def g_Eth():
    g = g_D()
    g['solid'].append(hbar(-110, 220, 355, BAR * 0.9))
    return g
def g_Dcroat():
    return g_Eth()
def g_eth():
    t, b = T_(), B_()
    return G(sk=[ring(218, 250, 205, 250 - HW + OV),
                 skel([('M', 405, 280), ('C', 415, 480, 310, 630, 140, ASC - HW)])],
             solid=[stroke(skel([('M', 110, 540), ('L', 390, 670)]), BAR * 0.85)])
def g_dcroat():
    g = g_d()
    g['solid'].append(hbar(250, 510, 600, BAR * 0.88))
    return g
def g_Thorn():
    return G(sk=[_stem(0, 0, CAP),
                 skel([('M', 0, 540), ('L', 230, 540), ('C', 360, 540, 430, 470, 430, 355), ('C', 430, 240, 360, 170, 230, 170), ('L', 0, 170)])],
             top=[(0, CAP)], foot=[(0, 0)])
def g_thorn():
    return G(sk=[_stem(0, DSC, ASC), _bowl_r()], top=[(0, ASC)], foot=[(0, DSC)])
def g_germandbls():
    b = B_()
    return G(sk=[skel([('M', 0, 0), ('L', 0, 520), ('C', 0, 645, 78, ASC - HW, 205, ASC - HW),
                       ('C', 325, ASC - HW, 395, 640, 395, 545), ('C', 395, 455, 325, 400, 195, 380),
                       ('C', 350, 365, 435, 300, 435, 185), ('C', 435, 75, 345, b, 215, b), ('L', 120, b)])],
             foot=[(0, 0)])
def g_Germandbls():
    b = B_()
    return G(sk=[skel([('M', 0, 0), ('L', 0, 500), ('C', 0, 625, 85, CAP - HW, 225, CAP - HW),
                       ('C', 360, CAP - HW, 435, 620, 435, 525), ('C', 435, 435, 360, 382, 215, 365),
                       ('C', 380, 350, 475, 285, 475, 175), ('C', 475, 70, 380, b, 235, b), ('L', 120, b)])],
             foot=[(0, 0)])
def g_Hbar():
    g = g_H(); g['solid'].append(hbar(-80, 560, 520, BAR * 0.85)); return g
def g_hbar_glyph():
    g = g_h(); g['solid'].append(hbar(-90, 180, 590, BAR * 0.85)); return g
def g_Tbar():
    g = g_T(); g['solid'].append(hbar(110, 430, 350, BAR * 0.85)); return g
def g_tbar():
    g = g_t(); g['solid'].append(hbar(-78, 140, 260, BAR * 0.85)); return g
def g_Eng():
    return G(sk=[_stem(0, 0, CAP),
                 skel([('M', 520, CAP), ('L', 520, -70), ('C', 520, -130, 492, DSC + HW, 420, DSC + HW), ('L', 310, DSC + HW)])],
             solid=[clip(skel([('M', -10, 760), ('L', 530, -60)]), 0, CAP, DIAG * 1.12)],
             foot=[(0, 0)], top=[(520, CAP)])
def g_eng():
    t = T_()
    return G(sk=[_stem(0, 0, XH),
                 skel([('M', 0, 360), ('C', 28, 452, 110, t, 210, t), ('C', 330, t, 400, 440, 400, 330),
                       ('L', 400, -70), ('C', 400, -130, 372, DSC + HW, 300, DSC + HW), ('L', 190, DSC + HW)])],
             top=[(0, XH)], foot=[(0, 0)])
def g_Ldot():
    g = g_L(); g['solid'].append(dot(240, 320)); return g
def g_ldot():
    g = g_l(); g['solid'].append(dot(160, 260)); return g
def g_IJ():
    return G(sk=[_stem(0, 0, CAP),
                 skel([('M', 420, CAP), ('L', 420, 150), ('C', 420, 86, 392, HW, 320, HW), ('L', 160, HW)])],
             full_top=[(0, CAP)], full_foot=[(0, 0)], top=[(420, CAP)])
def g_ij():
    return G(sk=[_stem(0, 0, XH),
                 skel([('M', 240, XH), ('L', 240, -70), ('C', 240, -130, 212, DSC + HW, 140, DSC + HW), ('L', 50, DSC + HW)])],
             solid=[dot(0, ASC - W - 8), dot(240, ASC - W - 8)],
             top=[(0, XH), (240, XH)], foot=[(0, 0)])
def g_fi():
    return G(sk=[skel([('M', 0, 0), ('L', 0, 580), ('C', 0, 664, 46, ASC - HW, 140, ASC - HW), ('L', 280, ASC - HW)]),
                 skel([('M', -78 if SERIFS else -115, XH - HW + 2), ('L', 280, XH - HW + 2)]),
                 _stem(280, 0, XH)],
             foot=[(0, 0), (280, 0)])
def g_fl():
    return G(sk=[skel([('M', 0, 0), ('L', 0, 580), ('C', 0, 664, 46, ASC - HW, 140, ASC - HW), ('L', 230, ASC - HW)]),
                 skel([('M', -78 if SERIFS else -115, XH - HW + 2), ('L', 180, XH - HW + 2)]),
                 _stem(280, 0, ASC)],
             top=[(280, ASC)], foot=[(0, 0), (280, 0)])
def g_florin():
    return G(sk=[skel([('M', -130, DSC + HW), ('L', -40, DSC + HW), ('C', 32, DSC + HW, 60, -130, 60, -60),
                       ('L', 60, 560), ('C', 60, 650, 108, CAP - HW, 196, CAP - HW), ('L', 280, CAP - HW)]),
                 skel([('M', -60, XH - HW + 2), ('L', 220, XH - HW + 2)])])

# ================================================================= números
def g_zero(): return G(sk=[ring(250, 350, 230, 350 - HW + OV, 0.62)])
def g_one():
    return G(sk=[_stem(290, 0, CAP)], solid=[clip(skel([('M', 330, CAP + 20), ('L', 90, 520)]), 480, CAP)], full_foot=[(290, 0)])
def g_two():
    t = TC()
    top2 = stroke(skel([('M', 32, 510), ('C', 52, 630, 140, t, 250, t), ('C', 372, t, 450, 624, 450, 520), ('C', 450, 450, 418, 398, 355, 340)]), W * 0.96)
    diag2 = dline(395, 390, 42, FB(), FB(), 440, 0.97, 0.0)
    return G(solid=[top2, diag2, hbar(30 if SERIFS else -4, 470, FB())])
def g_three():
    t, b = TC(), B_()
    return G(sk=[skel([('M', 40, 570), ('C', 70, 650, 150, t, 250, t), ('C', 370, t, 436, 630, 436, 540), ('C', 436, 446, 360, 392, 230, 392)]),
                 skel([('M', 230, 392), ('C', 380, 392, 460, 330, 460, 222), ('C', 460, 100, 370, b, 248, b), ('C', 130, b, 50, 66, 28, 150)])])
def g_four():
    return G(sk=[_stem(360, 0, CAP)], solid=[clip(skel([('M', 380, CAP + 40), ('L', -10, 170)]), 190, CAP), hbar(0, 490, 210)], foot=[(360, 0)])
def g_five():
    b = B_()
    x5 = 80 if SERIFS else 92 - HW / SX
    return G(solid=[hbar(x5, 440, FT()), stroke(skel([('M', 92, FT() if SERIFS else CAP), ('L', 72, 370 if SERIFS else 394)]))],
             sk=[skel([('M', 72, 384), ('C', 120, 420, 190, 440, 262, 440), ('C', 392, 440, 470, 360, 470, 228), ('C', 470, 96, 380, b, 250, b), ('C', 136, b, 56, 66, 30, 150)])])
def g_six():
    t = TC()
    return G(sk=[ring(255, 228, 220, 228 - HW + OV), skel([('M', 35, 236), ('C', 35, 520, 150, t, 280, t), ('C', 372, t, 432, 650, 452, 582)])], ws=0.95)
def g_seven():
    return G(solid=[hbar(20, 470, FT()), dline(480, FT() + 20, 160, -60, 0, FT(), 0.98, 0.02)])
def g_eight():
    return G(sk=[ring(250, 530, 182, 170 - HW + OV), ring(250, 200, 214, 200 - HW + OV)], ws=0.95)
def g_nine():
    b = B_()
    return G(sk=[ring(245, 472, 220, 228 - HW + OV), skel([('M', 465, 464), ('C', 465, 180, 350, b, 220, b), ('C', 128, b, 68, 50, 48, 118)])], ws=0.95)

# ================================================================= pontuação e símbolos ASCII/Latin-1
def g_period(): return G(solid=[dot(0, 0)])
def _tail(y): return stroke(skel([('M', HW * 0.5 / SX, y + 30), ('L', -HW * 0.6 / SX, y - 120)]), W * 0.72)
def g_comma(): return G(solid=[dot(0, 0), _tail(0)])
def g_colon(): return G(solid=[dot(0, 0), dot(0, XH - W - 8)])
def g_semicolon(): return G(solid=[dot(0, 0), _tail(0), dot(0, XH - W - 8)])
def g_exclam(): return G(sk=[_stem(0, 220, CAP)], solid=[dot(0, 0)])
def g_exclamdown():
    p = assemble(g_exclam())
    return G(solid=[p.transform(1, 0, 0, -1, 0, XH)])
def g_question():
    t = TC()
    return G(sk=[skel([('M', 30, 560), ('C', 50, 650, 130, t, 236, t), ('C', 356, t, 436, 630, 436, 530), ('C', 436, 430, 370, 390, 300, 352), ('C', 250, 326, 236, 296, 236, 220)])],
             solid=[dot(236, 0)])
def g_questiondown():
    p = assemble(g_question())
    bx0, _, bx1, _ = p.bounds
    return G(solid=[p.transform(-1, 0, 0, -1, bx0 + bx1, XH)])
def g_hyphen(): return G(solid=[hbar(0, 240, 292, BAR * 0.92)])
def g_uni00AD(): return g_hyphen()
def g_endash(): return G(solid=[hbar(0, 520, 292, BAR * 0.92)])
def g_emdash(): return G(solid=[hbar(0, 900, 292, BAR * 0.92)])
def g_underscore(): return G(solid=[hbar(0, 480, -120, BAR * 0.92)])
def g_quotesingle(): return G(sk=[_stem(0, 500, CAP + 20)])
def g_quotedbl(): return G(sk=[_stem(0, 500, CAP + 20), _stem(170, 500, CAP + 20)])
def g_quoteright(): return G(solid=[dot(0, 600), _tail(600)])
def g_quoteleft():
    q = union([dot(0, 600), _tail(600)]); q = q.transform(-1, 0, 0, -1, 0, 2 * (600 + (W + 8) / 2))
    return G(solid=[q])
def g_quotedblright(): return G(solid=[dot(0, 600), _tail(600), dot(150, 600), stroke(skel([('M', 150 + HW * 0.5 / SX, 630), ('L', 150 - HW * 0.6 / SX, 480)]), W * 0.72)])
def g_quotedblleft():
    q = union(g_quotedblright()['solid']); return G(solid=[q.transform(-1, 0, 0, -1, 0, 2 * (600 + (W + 8) / 2))])
def g_quotesinglbase(): return g_comma()
def g_quotedblbase():
    return G(solid=[dot(0, 0), _tail(0), dot(150, 0), stroke(skel([('M', 150 + HW * 0.5 / SX, 30), ('L', 150 - HW * 0.6 / SX, -120)]), W * 0.72)])
def g_parenleft(): return G(sk=[skel([('M', 210, 790), ('C', 90, 640, 46, 470, 46, 290), ('C', 46, 110, 90, -60, 210, -210)])])
def g_parenright(): return G(sk=[skel([('M', 0, 790), ('C', 120, 640, 164, 470, 164, 290), ('C', 164, 110, 120, -60, 0, -210)])])
def g_bracketleft():
    return G(sk=[_stem(0, -180, 760)], solid=[hbar(-HW / SX + 2, 190, 760 - BAR * 0.45, BAR * 0.9), hbar(-HW / SX + 2, 190, -180 + BAR * 0.45, BAR * 0.9)])
def g_bracketright():
    return G(sk=[_stem(190, -180, 760)], solid=[hbar(0, 190 + HW / SX - 2, 760 - BAR * 0.45, BAR * 0.9), hbar(0, 190 + HW / SX - 2, -180 + BAR * 0.45, BAR * 0.9)])
def g_braceleft():
    w = BAR * 0.88
    p = skel([('M', 210, 750), ('L', 145, 750), ('C', 95, 750, 75, 710, 75, 640),
              ('L', 75, 390), ('C', 75, 325, 45, 290, 0, 290),
              ('C', 45, 290, 75, 255, 75, 190), ('L', 75, -60),
              ('C', 75, -130, 95, -170, 145, -170), ('L', 210, -170)])
    return G(solid=[stroke(p, w)])
def g_braceright():
    q = union(g_braceleft()['solid'])
    bx0, _, bx1, _ = q.bounds
    return G(solid=[q.transform(-1, 0, 0, 1, bx0 + bx1, 0)])
def g_periodcentered(): return G(solid=[dot(0, 292 - (W + 8) / 2)])
def g_bullet():
    r = W * 1.15
    return G(solid=[rect(-r, 292 - r, r, 292 + r)])
def g_ellipsis():
    return G(solid=[dot(0, 0), dot(210, 0), dot(420, 0)])
def g_slash(): return G(solid=[clip(skel([('M', 0, -160), ('L', 360, 820)]), -140, 800)])
def g_backslash(): return G(solid=[clip(skel([('M', 360, -160), ('L', 0, 820)]), -140, 800)])
def g_fraction(): return G(solid=[clip(skel([('M', -30, -40), ('L', 350, CAP + 40)]), 0, CAP, DIAG * 0.85)])
def g_bar(): return G(sk=[_stem(0, -180, 780)])
def g_brokenbar(): return G(sk=[_stem(0, -180, 230), _stem(0, 350, 780)])
def g_numbersign():
    w = BAR * 0.82
    return G(solid=[clip(skel([('M', 110, -20), ('L', 190, CAP + 20)]), 0, CAP, w),
                    clip(skel([('M', 310, -20), ('L', 390, CAP + 20)]), 0, CAP, w),
                    hbar(0, 500, 235, w), hbar(0, 500, 465, w)])
def g_asterisk():
    cx, cy, r, w = 180, 540, 155, BAR * 0.72
    arms = []
    for ang in (90, 30, 150):
        dx = r * math.cos(math.radians(ang)) / SX
        dy = r * math.sin(math.radians(ang))
        arms.append(stroke(skel([('M', cx - dx, cy - dy), ('L', cx + dx, cy + dy)]), w))
    return G(solid=arms)
def g_plus():
    w = BAR * 0.88
    return G(solid=[hbar(0, 440, 292, w), stroke(skel([('M', 220, 72), ('L', 220, 512)]), w)])
def g_minus():
    return G(solid=[hbar(0, 440, 292, BAR * 0.88)])
def g_plusminus():
    w = BAR * 0.84
    return G(solid=[hbar(0, 440, 380, w), stroke(skel([('M', 220, 195), ('L', 220, 565)]), w), hbar(0, 440, 85, w)])
def g_equal():
    w = BAR * 0.88
    return G(solid=[hbar(0, 440, 200, w), hbar(0, 440, 384, w)])
def g_less():
    w = BAR * 0.86
    p = skel([('M', 400, 492), ('L', 50, 292), ('L', 400, 92)])
    return G(solid=[stroke(p, w)])
def g_greater():
    w = BAR * 0.86
    p = skel([('M', 50, 492), ('L', 400, 292), ('L', 50, 92)])
    return G(solid=[stroke(p, w)])
def g_asciicircum():
    w = BAR * 0.86
    p = skel([('M', 20, 440), ('L', 210, 680), ('L', 400, 440)])
    return G(solid=[stroke(p, w)])
def g_asciitilde():
    w = BAR * 0.85
    p = skel([('M', 15, 260), ('C', 80, 370, 155, 370, 225, 292), ('C', 295, 214, 370, 214, 435, 324)])
    return G(solid=[stroke(p, w)])
def g_logicalnot():
    w = BAR * 0.88
    return G(solid=[hbar(0, 420, 340, w), stroke(skel([('M', 420 - w * 0.5 / SX, 340 + w / 2), ('L', 420 - w * 0.5 / SX, 150)]), w)])
def g_multiply():
    w = BAR * 0.85
    return G(solid=[stroke(skel([('M', 45, 117), ('L', 395, 467)]), w),
                    stroke(skel([('M', 395, 117), ('L', 45, 467)]), w)])
def g_divide():
    w = BAR * 0.88
    return G(solid=[hbar(0, 440, 292, w), dot(220, 430), dot(220, 65)])
def g_guilsinglleft():
    w = BAR * 0.84
    return G(solid=[stroke(skel([('M', 220, 430), ('L', 45, 260), ('L', 220, 90)]), w)])
def g_guilsinglright():
    w = BAR * 0.84
    return G(solid=[stroke(skel([('M', 45, 430), ('L', 220, 260), ('L', 45, 90)]), w)])
def g_guillemotleft():
    s = union(g_guilsinglleft()['solid'])
    return G(solid=[s, s.transform(1, 0, 0, 1, 175 * SX, 0)])
def g_guillemotright():
    s = union(g_guilsinglright()['solid'])
    return G(solid=[s, s.transform(1, 0, 0, 1, 175 * SX, 0)])
def g_dagger():
    w = BAR * 0.84
    return G(solid=[stroke(skel([('M', 180, 120), ('L', 180, CAP)]), w), hbar(20, 340, 520, w)])
def g_daggerdbl():
    w = BAR * 0.84
    return G(solid=[stroke(skel([('M', 180, 60), ('L', 180, CAP)]), w), hbar(20, 340, 530, w), hbar(20, 340, 240, w)])
def g_degree():
    w = min(BAR * 0.76, 62)
    return G(solid=[stroke(ring(140, CAP - 115, 105, 105), w)])
def g_ordfeminine():
    p = assemble(g_a()).transform(0.56, 0, 0, 0.56, 0, CAP - 520 * 0.56)
    bx0, _, bx1, _ = p.bounds
    return G(solid=[p, rect(bx0, CAP - 390, bx1, CAP - 390 + BAR * 0.65)])
def g_ordmasculine():
    p = assemble(g_o()).transform(0.56, 0, 0, 0.56, 0, CAP - 520 * 0.56)
    bx0, _, bx1, _ = p.bounds
    return G(solid=[p, rect(bx0, CAP - 390, bx1, CAP - 390 + BAR * 0.65)])
def _sup_digit(fn):
    p = assemble(fn())
    sc = 0.58
    q = p.transform(sc, 0, 0, sc, 0, CAP - CAP * sc)
    return union([q, stroke(q, W * 0.16, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN)])
def g_uni00B9(): return G(solid=[_sup_digit(g_one)])
def g_uni00B2(): return G(solid=[_sup_digit(g_two)])
def g_uni00B3(): return G(solid=[_sup_digit(g_three)])
def g_zerosuperior(): return G(solid=[_sup_digit(g_zero)])
def g_foursuperior(): return G(solid=[_sup_digit(g_four)])
def _frac(n_fn, d_fn):
    num = _sup_digit(n_fn)
    den = _sup_digit(d_fn).transform(1, 0, 0, 1, 340 * SX, -(CAP - CAP * 0.58))
    sl = clip(skel([('M', 150, -20), ('L', 470, CAP + 20)]), 0, CAP, DIAG * 0.76)
    return G(solid=[num, sl, den])
def g_onequarter(): return _frac(g_one, g_four)
def g_onehalf(): return _frac(g_one, g_two)
def g_threequarters(): return _frac(g_three, g_four)
def g_uni00B5():
    b = B_()
    return G(sk=[_stem(0, DSC, XH),
                 skel([('M', 0, 190), ('C', 0, 80, 80, b, 195, b), ('C', 300, b, 372, 68, 400, 160)]),
                 _stem(400, 0, XH)],
             top=[(0, XH), (400, XH)], foot=[(0, DSC), (400, 0)])
def g_paragraph():
    w = BAR * 0.85
    bowl = rect(40 * SX, 350, 230 * SX, CAP)
    c = stroke(ring(160, 525, 140, 175 - w / 2), w)
    return G(solid=[c, bowl,
                    stroke(skel([('M', 230, -140), ('L', 230, CAP)]), w),
                    stroke(skel([('M', 360, -140), ('L', 360, CAP)]), w),
                    hbar(140, 420, CAP - w / 2, w)])
def g_section():
    w = min(BAR * 0.78, 68)
    s1 = skel([('M', 380, 620), ('C', 360, 690, 290, 720, 200, 720), ('C', 100, 720, 40, 670, 40, 600),
               ('C', 40, 520, 120, 490, 260, 440), ('C', 380, 400, 430, 350, 430, 270),
               ('C', 430, 190, 360, 140, 240, 140)])
    s2 = skel([('M', 220, 420), ('C', 100, 420, 30, 370, 30, 290),
               ('C', 30, 210, 80, 160, 200, 120), ('C', 340, 70, 420, 40, 420, -40),
               ('C', 420, -110, 360, -160, 260, -160), ('C', 170, -160, 100, -130, 80, -60)])
    return G(solid=[stroke(s1, w), stroke(s2, w)])
def g_copyright():
    w = min(BAR * 0.72, 58)
    outer = stroke(ring(320, 350, 300, 300), w)
    inner = assemble(g_C()).transform(0.46, 0, 0, 0.46, 175 * SX, 188)
    return G(solid=[outer, inner])
def g_registered():
    w = min(BAR * 0.72, 58)
    outer = stroke(ring(320, 350, 300, 300), w)
    inner = assemble(g_R()).transform(0.44, 0, 0, 0.44, 205 * SX, 195)
    return G(solid=[outer, inner])
def g_trademark():
    sc = 0.46
    t_gl = assemble(g_T()).transform(sc, 0, 0, sc, 0, CAP - CAP * sc)
    m_gl = assemble(g_M()).transform(sc, 0, 0, sc, 290 * SX, CAP - CAP * sc)
    return G(solid=[t_gl, m_gl])

# ================================================================= moedas e símbolos comerciais
SYMS = ('ampersand', 'at', 'percent', 'perthousand', 'dollar', 'Euro', 'cent', 'sterling', 'yen', 'currency', 'copyright', 'registered')
def _ws(cap): return 1.0 if SERIFS else min(1.0, cap / W)
def g_percent():
    ws = _ws(100); hw = HW * ws
    r, ry = (100, 96) if SERIFS else (140, 100); cyT = CAP - hw + OV - ry; cyB = hw - OV + ry
    x1, x2 = (125, 565) if SERIFS else (150, 640)
    return G(sk=[ring(x1, cyT, r, ry), ring(x2, cyB, r, ry)],
             solid=[clip(skel([('M', 60, -30), ('L', 630, CAP + 30)]), -20, CAP + 20, DIAG * 0.8)], ws=ws)
def g_perthousand():
    ws = _ws(90); hw = HW * ws
    r, ry = 88, 86; cyT = CAP - hw + OV - ry; cyB = hw - OV + ry
    return G(sk=[ring(115, cyT, r, ry), ring(490, cyB, r, ry), ring(750, cyB, r, ry)],
             solid=[clip(skel([('M', 50, -30), ('L', 590, CAP + 30)]), -20, CAP + 20, DIAG * 0.78)], ws=ws)
def g_dollar():
    g = g_S(); cx = 280
    g['solid'].append(stroke(skel([('M', cx, CAP - HW), ('L', cx, CAP + 70)]), BAR * 0.8))
    g['solid'].append(stroke(skel([('M', cx, HW), ('L', cx, -70)]), BAR * 0.8))
    return g
def g_cent():
    g = g_c(); cx = 215
    g['solid'].append(stroke(skel([('M', cx, -80), ('L', cx, XH + 80)]), BAR * 0.78))
    return g
def g_sterling():
    t = TC()
    return G(sk=[skel([('M', 110, 0), ('L', 110, 490), ('C', 110, 620, 190, t, 300, t), ('C', 395, t, 455, 635, 470, 555)])],
             solid=[hbar(20, 470, FB()), hbar(0, 350, 340, BAR * 0.85)])
def g_yen():
    g = g_Y()
    bw = BAR * 0.82
    g['solid'] += [hbar(70, 510, 270, bw), hbar(70, 510, 155, bw)]
    return g
def g_currency():
    w = BAR * 0.82
    cx, cy, r = 240, 292, 145
    ticks = []
    for sx_d, sy_d in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        x0 = cx + sx_d * r * 0.68; y0 = cy + sy_d * r * 0.68
        x1 = cx + sx_d * r * 1.45; y1 = cy + sy_d * r * 1.45
        ticks.append(stroke(skel([('M', x0, y0), ('L', x1, y1)]), w))
    return G(solid=[stroke(ring(cx, cy, r, r), w)] + ticks)
def g_Euro():
    g = g_C(); bw = BAR * 0.78
    if SERIFS: g['solid'] += [hbar(-50, 390, 300, bw), hbar(-50, 390, 410, bw)]
    else:
        bw = min(bw, 72); g['solid'] += [hbar(-50, 390, 280, bw), hbar(-50, 390, 420, bw)]
    return g
def g_ampersand():
    ws = _ws(106); hw = HW * ws
    t, b = CAP - hw + OV, hw - OV; ry = 118; cy = t - ry
    return G(sk=[ring(225 if SERIFS else 235, cy, 128 if SERIFS else 150, ry),
                 skel([('M', 580, 0), ('L', 215, cy - ry + 20)]),
                 skel([('M', 225, cy - ry), ('C', 110, 400, 20, 330, 20, 220), ('C', 20, 100, 100, b, 235, b), ('C', 340, b, 440, 90, 540, 270)])], ws=ws)
def g_at():
    ws = _ws(100); hw = HW * ws
    ob = [('M', 705, 230), ('L', 705, 300), ('C', 705, 481, 557, 635, 370, 635), ('C', 183, 635, 30, 481, 30, 300),
          ('C', 30, 119, 183, -35, 370, -35), ('C', 470, -35, 580, 0, 660, 60)]
    R = 158 - hw * 0.9; sx = 345 + R
    return G(sk=[skel(ob), ring(345, 290, R, R - 4),
                 skel([('M', sx, 420), ('L', sx, 205), ('C', sx, 110, 705, 90, 705, 230)])], ws=ws)

# ================================================================= acentos
ACC_TOP_U = 890
def _abar(): return min(BAR, 106)
def acc_band(upper):
    ab = _abar()
    H = ab + 70; gap = max(48, 0.55 * min(W, 116))
    if upper:
        lo = CAP + gap; return lo, lo + H
    lo = XH + gap; top = max(ASC, lo + H)
    return top - H, top

def _seg(x0, y0, x1, y1, lo, hi, w):
    dx, dy = x1 - x0, y1 - y0; L = (dx * dx + dy * dy) ** 0.5; ux, uy = dx / L * 80, dy / L * 80
    return op(stroke(skel([('M', x0 - ux, y0 - uy), ('L', x1 + ux, y1 + uy)], sx=SX_BASE), w), rect(-900, lo, 1900, hi), PathOp.INTERSECTION)

ACC_HALF = 150
def m_acute(upper):
    lo, hi = acc_band(upper); run = (hi - lo) * 0.62
    return _seg(-run / 2, lo, run / 2, hi, lo, hi, _abar())
def m_grave(upper):
    lo, hi = acc_band(upper); run = (hi - lo) * 0.62
    return _seg(run / 2, lo, -run / 2, hi, lo, hi, _abar())
def m_circ(upper):
    lo, hi = acc_band(upper); S = ACC_HALF; ab = _abar()
    return union([_seg(-S, lo, 0, hi, lo, hi, ab), _seg(S, lo, 0, hi, lo, hi, ab)])
def m_caron(upper):
    lo, hi = acc_band(upper); S = ACC_HALF; ab = _abar()
    return union([_seg(-S, hi, 0, lo, lo, hi, ab), _seg(S, hi, 0, lo, lo, hi, ab)])
def m_tilde(upper):
    lo, hi = acc_band(upper); top = hi; S = ACC_HALF; ab = _abar()
    a, b = lo + ab / 2, top - ab / 2; m = (a + b) / 2; d = (b - a) * 0.35
    p = skel([('M', -S - 10, a - 4), ('C', -S * 0.62, b + d, -S * 0.25, b, 0, m), ('C', S * 0.25, a, S * 0.62, a - d, S + 10, b + 4)], sx=SX_BASE)
    return op(stroke(p, ab), rect(-900, lo, 1900, top), PathOp.INTERSECTION)
def m_dieresis(upper):
    lo, hi = acc_band(upper)
    s = BAR + 6
    ym = lo + (hi - lo - s) * 0.35
    dx = max(92 * SX_BASE, s * 0.95)
    return union([rect(-dx - s / 2, ym, -dx + s / 2, ym + s),
                  rect(dx - s / 2, ym, dx + s / 2, ym + s)])
def m_dotaccent(upper):
    lo, hi = acc_band(upper)
    s = BAR + 6
    ym = lo + (hi - lo - s) * 0.35
    return rect(-s / 2, ym, s / 2, ym + s)
def m_ring(upper):
    lo, hi = acc_band(upper)
    w = min(BAR * 0.72, 62)
    r = (hi - lo) * 0.44
    cy = (lo + hi) / 2
    return stroke(ring(0, cy, r, r, sx=1.0), w)
def m_macron(upper):
    lo, hi = acc_band(upper)
    ym = lo + (hi - lo) * 0.45
    S = ACC_HALF * SX_BASE
    return rect(-S, ym - BAR * 0.45, S, ym + BAR * 0.45)
def m_breve(upper):
    lo, hi = acc_band(upper)
    S = ACC_HALF * 0.92
    b = lo + BAR * 0.48; t = hi
    p = skel([('M', -S, t + 20), ('C', -S * 0.85, b, -S * 0.35, b, 0, b), ('C', S * 0.35, b, S * 0.85, b, S, t + 20)], sx=SX_BASE)
    return op(stroke(p, BAR * 0.88), rect(-900, lo, 1900, hi), PathOp.INTERSECTION)
def m_hungarumlaut(upper):
    lo, hi = acc_band(upper)
    run = (hi - lo) * 0.56
    dx = 76 * SX_BASE
    w = BAR * 0.84
    s1 = _seg(-run / 2, lo, run / 2, hi, lo, hi, w).transform(1, 0, 0, 1, -dx, 0)
    s2 = _seg(-run / 2, lo, run / 2, hi, lo, hi, w).transform(1, 0, 0, 1, dx, 0)
    return union([s1, s2])
def m_cedilla(y=0):
    hb = BAR / 2
    return stroke(skel([('M', 0, 30), ('L', 0, -60), ('C', 0, -110, -22, -150 + hb, -72, -150 + hb), ('L', -130, -150 + hb)], sx=SX_BASE), BAR)
def m_ogonek(y=0):
    hb = BAR / 2
    return stroke(skel([('M', 0, 30), ('L', -15, -55), ('C', -25, -110, 5, -150 + hb, 65, -150 + hb), ('L', 125, -150 + hb)], sx=SX_BASE), BAR * 0.9)
def m_commabelow(y=0):
    s = BAR + 4; y0 = -140
    return union([rect(-s / 2, y0, s / 2, y0 + s),
                  stroke(skel([('M', s * 0.2, y0 + 25), ('L', -s * 0.35, y0 - 65)], sx=1.0), BAR * 0.72)])

# Marcas espaçadoras avulsas (Spacing Modifier Letters)
def g_grave_mod(): return G(solid=[m_grave(True)])
def g_acute_mod(): return G(solid=[m_acute(True)])
def g_circumflex_mod(): return G(solid=[m_circ(True)])
def g_tilde_mod(): return G(solid=[m_tilde(True)])
def g_dieresis_mod(): return G(solid=[m_dieresis(True)])
def g_macron_mod(): return G(solid=[m_macron(True)])
def g_breve_mod(): return G(solid=[m_breve(True)])
def g_dotaccent_mod(): return G(solid=[m_dotaccent(True)])
def g_ring_mod(): return G(solid=[m_ring(True)])
def g_caron_mod(): return G(solid=[m_caron(True)])
def g_hungarumlaut_mod(): return G(solid=[m_hungarumlaut(True)])
def g_cedilla_mod(): return G(solid=[m_cedilla()])
def g_ogonek_mod(): return G(solid=[m_ogonek()])

MARKS = {
    'acute': m_acute, 'grave': m_grave, 'circumflex': m_circ, 'tilde': m_tilde,
    'dieresis': m_dieresis, 'ring': m_ring, 'macron': m_macron, 'breve': m_breve,
    'dotaccent': m_dotaccent, 'caron': m_caron, 'hungarumlaut': m_hungarumlaut,
}
BELOW_MARKS = {
    'cedilla': m_cedilla, 'ogonek': m_ogonek, 'commabelow': m_commabelow,
}

ACCENTED = {
    # Latin-1 Supplement
    'Agrave': ('A', 'grave'), 'Aacute': ('A', 'acute'), 'Acircumflex': ('A', 'circumflex'),
    'Atilde': ('A', 'tilde'), 'Adieresis': ('A', 'dieresis'), 'Aring': ('A', 'ring'),
    'Ccedilla': ('C', 'cedilla'),
    'Egrave': ('E', 'grave'), 'Eacute': ('E', 'acute'), 'Ecircumflex': ('E', 'circumflex'), 'Edieresis': ('E', 'dieresis'),
    'Igrave': ('I', 'grave'), 'Iacute': ('I', 'acute'), 'Icircumflex': ('I', 'circumflex'), 'Idieresis': ('I', 'dieresis'),
    'Ntilde': ('N', 'tilde'),
    'Ograve': ('O', 'grave'), 'Oacute': ('O', 'acute'), 'Ocircumflex': ('O', 'circumflex'),
    'Otilde': ('O', 'tilde'), 'Odieresis': ('O', 'dieresis'),
    'Ugrave': ('U', 'grave'), 'Uacute': ('U', 'acute'), 'Ucircumflex': ('U', 'circumflex'), 'Udieresis': ('U', 'dieresis'),
    'Yacute': ('Y', 'acute'), 'Ydieresis': ('Y', 'dieresis'),
    'agrave': ('a', 'grave'), 'aacute': ('a', 'acute'), 'acircumflex': ('a', 'circumflex'),
    'atilde': ('a', 'tilde'), 'adieresis': ('a', 'dieresis'), 'aring': ('a', 'ring'),
    'ccedilla': ('c', 'cedilla'),
    'egrave': ('e', 'grave'), 'eacute': ('e', 'acute'), 'ecircumflex': ('e', 'circumflex'), 'edieresis': ('e', 'dieresis'),
    'igrave': ('dotlessi', 'grave'), 'iacute': ('dotlessi', 'acute'),
    'icircumflex': ('dotlessi', 'circumflex'), 'idieresis': ('dotlessi', 'dieresis'),
    'ntilde': ('n', 'tilde'),
    'ograve': ('o', 'grave'), 'oacute': ('o', 'acute'), 'ocircumflex': ('o', 'circumflex'),
    'otilde': ('o', 'tilde'), 'odieresis': ('o', 'dieresis'),
    'ugrave': ('u', 'grave'), 'uacute': ('u', 'acute'), 'ucircumflex': ('u', 'circumflex'), 'udieresis': ('u', 'dieresis'),
    'yacute': ('y', 'acute'), 'ydieresis': ('y', 'dieresis'),

    # Latin Extended-A & Central/Eastern European
    'Amacron': ('A', 'macron'), 'amacron': ('a', 'macron'),
    'Abreve': ('A', 'breve'), 'abreve': ('a', 'breve'),
    'Aogonek': ('A', 'ogonek'), 'aogonek': ('a', 'ogonek'),
    'Cacute': ('C', 'acute'), 'cacute': ('c', 'acute'),
    'Ccircumflex': ('C', 'circumflex'), 'ccircumflex': ('c', 'circumflex'),
    'Cdotaccent': ('C', 'dotaccent'), 'cdotaccent': ('c', 'dotaccent'),
    'Ccaron': ('C', 'caron'), 'ccaron': ('c', 'caron'),
    'Dcaron': ('D', 'caron'), 'dcaron': ('d', 'caron'),
    'Emacron': ('E', 'macron'), 'emacron': ('e', 'macron'),
    'Ebreve': ('E', 'breve'), 'ebreve': ('e', 'breve'),
    'Edotaccent': ('E', 'dotaccent'), 'edotaccent': ('e', 'dotaccent'),
    'Eogonek': ('E', 'ogonek'), 'eogonek': ('e', 'ogonek'),
    'Ecaron': ('E', 'caron'), 'ecaron': ('e', 'caron'),
    'Gcircumflex': ('G', 'circumflex'), 'gcircumflex': ('g', 'circumflex'),
    'Gbreve': ('G', 'breve'), 'gbreve': ('g', 'breve'),
    'Gdotaccent': ('G', 'dotaccent'), 'gdotaccent': ('g', 'dotaccent'),
    'uni0122': ('G', 'commabelow'), 'uni0123': ('g', 'commabelow'),
    'Hcircumflex': ('H', 'circumflex'), 'hcircumflex': ('h', 'circumflex'),
    'Itilde': ('I', 'tilde'), 'itilde': ('dotlessi', 'tilde'),
    'Imacron': ('I', 'macron'), 'imacron': ('dotlessi', 'macron'),
    'Ibreve': ('I', 'breve'), 'ibreve': ('dotlessi', 'breve'),
    'Iogonek': ('I', 'ogonek'), 'iogonek': ('i', 'ogonek'),
    'Idotaccent': ('I', 'dotaccent'),
    'Jcircumflex': ('J', 'circumflex'), 'jcircumflex': ('uni0237', 'circumflex'),
    'uni0136': ('K', 'commabelow'), 'uni0137': ('k', 'commabelow'),
    'Lacute': ('L', 'acute'), 'lacute': ('l', 'acute'),
    'uni013B': ('L', 'commabelow'), 'uni013C': ('l', 'commabelow'),
    'Lcaron': ('L', 'caron'), 'lcaron': ('l', 'caron'),
    'Nacute': ('N', 'acute'), 'nacute': ('n', 'acute'),
    'uni0145': ('N', 'commabelow'), 'uni0146': ('n', 'commabelow'),
    'Ncaron': ('N', 'caron'), 'ncaron': ('n', 'caron'),
    'Omacron': ('O', 'macron'), 'omacron': ('o', 'macron'),
    'Obreve': ('O', 'breve'), 'obreve': ('o', 'breve'),
    'Ohungarumlaut': ('O', 'hungarumlaut'), 'ohungarumlaut': ('o', 'hungarumlaut'),
    'Racute': ('R', 'acute'), 'racute': ('r', 'acute'),
    'uni0156': ('R', 'commabelow'), 'uni0157': ('r', 'commabelow'),
    'Rcaron': ('R', 'caron'), 'rcaron': ('r', 'caron'),
    'Sacute': ('S', 'acute'), 'sacute': ('s', 'acute'),
    'Scircumflex': ('S', 'circumflex'), 'scircumflex': ('s', 'circumflex'),
    'Scedilla': ('S', 'cedilla'), 'scedilla': ('s', 'cedilla'),
    'Scaron': ('S', 'caron'), 'scaron': ('s', 'caron'),
    'uni0218': ('S', 'commabelow'), 'uni0219': ('s', 'commabelow'),
    'uni0162': ('T', 'cedilla'), 'uni0163': ('t', 'cedilla'),
    'Tcaron': ('T', 'caron'), 'tcaron': ('t', 'caron'),
    'uni021A': ('T', 'commabelow'), 'uni021B': ('t', 'commabelow'),
    'Utilde': ('U', 'tilde'), 'utilde': ('u', 'tilde'),
    'Umacron': ('U', 'macron'), 'umacron': ('u', 'macron'),
    'Ubreve': ('U', 'breve'), 'ubreve': ('u', 'breve'),
    'Uring': ('U', 'ring'), 'uring': ('u', 'ring'),
    'Uhungarumlaut': ('U', 'hungarumlaut'), 'uhungarumlaut': ('u', 'hungarumlaut'),
    'Uogonek': ('U', 'ogonek'), 'uogonek': ('u', 'ogonek'),
    'Wcircumflex': ('W', 'circumflex'), 'wcircumflex': ('w', 'circumflex'),
    'Wgrave': ('W', 'grave'), 'wgrave': ('w', 'grave'),
    'Wacute': ('W', 'acute'), 'wacute': ('w', 'acute'),
    'Wdieresis': ('W', 'dieresis'), 'wdieresis': ('w', 'dieresis'),
    'Ycircumflex': ('Y', 'circumflex'), 'ycircumflex': ('y', 'circumflex'),
    'Ygrave': ('Y', 'grave'), 'ygrave': ('y', 'grave'),
    'Zacute': ('Z', 'acute'), 'zacute': ('z', 'acute'),
    'Zdotaccent': ('Z', 'dotaccent'), 'zdotaccent': ('z', 'dotaccent'),
    'Zcaron': ('Z', 'caron'), 'zcaron': ('z', 'caron'),
}

BASE = {
    'a': g_a, 'b': g_b, 'c': g_c, 'd': g_d, 'e': g_e, 'f': g_f, 'g': g_g, 'h': g_h, 'i': g_i, 'j': g_j, 'k': g_k, 'l': g_l, 'm': g_m,
    'n': g_n, 'o': g_o, 'p': g_p, 'q': g_q, 'r': g_r, 's': g_s, 't': g_t, 'u': g_u, 'v': g_v, 'w': g_w, 'x': g_x, 'y': g_y, 'z': g_z,
    'dotlessi': g_dotlessi, 'uni0237': g_dotlessj,
    'A': g_A, 'B': g_B, 'C': g_C, 'D': g_D, 'E': g_E, 'F': g_F, 'G': g_G, 'H': g_H, 'I': g_I, 'J': g_J, 'K': g_K, 'L': g_L, 'M': g_M,
    'N': g_N, 'O': g_O, 'P': g_P, 'Q': g_Q, 'R': g_R, 'S': g_S, 'T': g_T, 'U': g_U, 'V': g_V, 'W': g_W, 'X': g_X, 'Y': g_Y, 'Z': g_Z,
    'AE': g_AE, 'ae': g_ae, 'OE': g_OE, 'oe': g_oe, 'Oslash': g_Oslash, 'oslash': g_oslash,
    'Lslash': g_Lslash, 'lslash': g_lslash, 'Eth': g_Eth, 'eth': g_eth, 'Dcroat': g_Dcroat, 'dcroat': g_dcroat,
    'Thorn': g_Thorn, 'thorn': g_thorn, 'germandbls': g_germandbls, 'uni1E9E': g_Germandbls,
    'Hbar': g_Hbar, 'hbar': g_hbar_glyph, 'Tbar': g_Tbar, 'tbar': g_tbar,
    'Eng': g_Eng, 'eng': g_eng, 'Ldot': g_Ldot, 'ldot': g_ldot, 'IJ': g_IJ, 'ij': g_ij,
    'fi': g_fi, 'fl': g_fl, 'florin': g_florin,
    'zero': g_zero, 'one': g_one, 'two': g_two, 'three': g_three, 'four': g_four, 'five': g_five, 'six': g_six, 'seven': g_seven,
    'eight': g_eight, 'nine': g_nine,
    'uni00B9': g_uni00B9, 'uni00B2': g_uni00B2, 'uni00B3': g_uni00B3, 'uni2070': g_zerosuperior, 'uni2074': g_foursuperior,
    'onequarter': g_onequarter, 'onehalf': g_onehalf, 'threequarters': g_threequarters,
    'period': g_period, 'comma': g_comma, 'colon': g_colon, 'semicolon': g_semicolon, 'exclam': g_exclam, 'exclamdown': g_exclamdown,
    'question': g_question, 'questiondown': g_questiondown,
    'hyphen': g_hyphen, 'uni00AD': g_uni00AD, 'endash': g_endash, 'emdash': g_emdash, 'underscore': g_underscore,
    'quotesingle': g_quotesingle, 'quotedbl': g_quotedbl, 'quoteright': g_quoteright,
    'quoteleft': g_quoteleft, 'quotedblright': g_quotedblright, 'quotedblleft': g_quotedblleft,
    'quotesinglbase': g_quotesinglbase, 'quotedblbase': g_quotedblbase,
    'parenleft': g_parenleft, 'parenright': g_parenright, 'bracketleft': g_bracketleft, 'bracketright': g_bracketright,
    'braceleft': g_braceleft, 'braceright': g_braceright,
    'slash': g_slash, 'backslash': g_backslash, 'fraction': g_fraction, 'bar': g_bar, 'brokenbar': g_brokenbar,
    'periodcentered': g_periodcentered, 'bullet': g_bullet, 'ellipsis': g_ellipsis,
    'numbersign': g_numbersign, 'asterisk': g_asterisk, 'plus': g_plus, 'minus': g_minus, 'plusminus': g_plusminus,
    'equal': g_equal, 'less': g_less, 'greater': g_greater, 'asciicircum': g_asciicircum, 'asciitilde': g_asciitilde,
    'logicalnot': g_logicalnot, 'multiply': g_multiply, 'divide': g_divide,
    'guilsinglleft': g_guilsinglleft, 'guilsinglright': g_guilsinglright, 'guillemotleft': g_guillemotleft, 'guillemotright': g_guillemotright,
    'dagger': g_dagger, 'daggerdbl': g_daggerdbl, 'degree': g_degree, 'ordfeminine': g_ordfeminine, 'ordmasculine': g_ordmasculine,
    'uni00B5': g_uni00B5, 'paragraph': g_paragraph, 'section': g_section,
    'copyright': g_copyright, 'registered': g_registered, 'trademark': g_trademark,
    'ampersand': g_ampersand, 'at': g_at, 'percent': g_percent, 'perthousand': g_perthousand,
    'dollar': g_dollar, 'Euro': g_Euro, 'cent': g_cent, 'sterling': g_sterling, 'yen': g_yen, 'currency': g_currency,
    'grave': g_grave_mod, 'acute': g_acute_mod, 'circumflex': g_circumflex_mod, 'tilde': g_tilde_mod,
    'dieresis': g_dieresis_mod, 'macron': g_macron_mod, 'breve': g_breve_mod, 'dotaccent': g_dotaccent_mod,
    'ring': g_ring_mod, 'caron': g_caron_mod, 'hungarumlaut': g_hungarumlaut_mod, 'cedilla': g_cedilla_mod, 'ogonek': g_ogonek_mod,
}

UNI = {
    **{c: ord(c) for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'},
    'zero': 0x30, 'one': 0x31, 'two': 0x32, 'three': 0x33, 'four': 0x34,
    'five': 0x35, 'six': 0x36, 'seven': 0x37, 'eight': 0x38, 'nine': 0x39,
    'exclam': 0x21, 'quotedbl': 0x22, 'numbersign': 0x23, 'dollar': 0x24, 'percent': 0x25,
    'ampersand': 0x26, 'quotesingle': 0x27, 'parenleft': 0x28, 'parenright': 0x29, 'asterisk': 0x2A,
    'plus': 0x2B, 'comma': 0x2C, 'hyphen': 0x2D, 'period': 0x2E, 'slash': 0x2F,
    'colon': 0x3A, 'semicolon': 0x3B, 'less': 0x3C, 'equal': 0x3D, 'greater': 0x3E, 'question': 0x3F, 'at': 0x40,
    'bracketleft': 0x5B, 'backslash': 0x5C, 'bracketright': 0x5D, 'asciicircum': 0x5E, 'underscore': 0x5F, 'grave': 0x60,
    'braceleft': 0x7B, 'bar': 0x7C, 'braceright': 0x7D, 'asciitilde': 0x7E,
    'exclamdown': 0xA1, 'cent': 0xA2, 'sterling': 0xA3, 'currency': 0xA4, 'yen': 0xA5,
    'brokenbar': 0xA6, 'section': 0xA7, 'dieresis': 0xA8, 'copyright': 0xA9, 'ordfeminine': 0xAA,
    'guillemotleft': 0xAB, 'logicalnot': 0xAC, 'uni00AD': 0xAD, 'registered': 0xAE, 'macron': 0xAF,
    'degree': 0xB0, 'plusminus': 0xB1, 'uni00B2': 0xB2, 'uni00B3': 0xB3, 'acute': 0xB4,
    'uni00B5': 0xB5, 'paragraph': 0xB6, 'periodcentered': 0xB7, 'cedilla': 0xB8, 'uni00B9': 0xB9,
    'ordmasculine': 0xBA, 'guillemotright': 0xBB, 'onequarter': 0xBC, 'onehalf': 0xBD, 'threequarters': 0xBE, 'questiondown': 0xBF,
    'Agrave': 0xC0, 'Aacute': 0xC1, 'Acircumflex': 0xC2, 'Atilde': 0xC3, 'Adieresis': 0xC4, 'Aring': 0xC5,
    'AE': 0xC6, 'Ccedilla': 0xC7, 'Egrave': 0xC8, 'Eacute': 0xC9, 'Ecircumflex': 0xCA, 'Edieresis': 0xCB,
    'Igrave': 0xCC, 'Iacute': 0xCD, 'Icircumflex': 0xCE, 'Idieresis': 0xCF, 'Eth': 0xD0, 'Ntilde': 0xD1,
    'Ograve': 0xD2, 'Oacute': 0xD3, 'Ocircumflex': 0xD4, 'Otilde': 0xD5, 'Odieresis': 0xD6, 'multiply': 0xD7,
    'Oslash': 0xD8, 'Ugrave': 0xD9, 'Uacute': 0xDA, 'Ucircumflex': 0xDB, 'Udieresis': 0xDC, 'Yacute': 0xDD,
    'Thorn': 0xDE, 'germandbls': 0xDF,
    'agrave': 0xE0, 'aacute': 0xE1, 'acircumflex': 0xE2, 'atilde': 0xE3, 'adieresis': 0xE4, 'aring': 0xE5,
    'ae': 0xE6, 'ccedilla': 0xE7, 'egrave': 0xE8, 'eacute': 0xE9, 'ecircumflex': 0xEA, 'edieresis': 0xEB,
    'igrave': 0xEC, 'iacute': 0xED, 'icircumflex': 0xEE, 'idieresis': 0xEF, 'eth': 0xF0, 'ntilde': 0xF1,
    'ograve': 0xF2, 'oacute': 0xF3, 'ocircumflex': 0xF4, 'otilde': 0xF5, 'odieresis': 0xF6, 'divide': 0xF7,
    'oslash': 0xF8, 'ugrave': 0xF9, 'uacute': 0xFA, 'ucircumflex': 0xFB, 'udieresis': 0xFC, 'yacute': 0xFD,
    'thorn': 0xFE, 'ydieresis': 0xFF,
    'Amacron': 0x0100, 'amacron': 0x0101, 'Abreve': 0x0102, 'abreve': 0x0103, 'Aogonek': 0x0104, 'aogonek': 0x0105,
    'Cacute': 0x0106, 'cacute': 0x0107, 'Ccircumflex': 0x0108, 'ccircumflex': 0x0109, 'Cdotaccent': 0x010A, 'cdotaccent': 0x010B,
    'Ccaron': 0x010C, 'ccaron': 0x010D, 'Dcaron': 0x010E, 'dcaron': 0x010F, 'Dcroat': 0x0110, 'dcroat': 0x0111,
    'Emacron': 0x0112, 'emacron': 0x0113, 'Ebreve': 0x0114, 'ebreve': 0x0115, 'Edotaccent': 0x0116, 'edotaccent': 0x0117,
    'Eogonek': 0x0118, 'eogonek': 0x0119, 'Ecaron': 0x011A, 'ecaron': 0x011B, 'Gcircumflex': 0x011C, 'gcircumflex': 0x011D,
    'Gbreve': 0x011E, 'gbreve': 0x011F, 'Gdotaccent': 0x0120, 'gdotaccent': 0x0121, 'uni0122': 0x0122, 'uni0123': 0x0123,
    'Hcircumflex': 0x0124, 'hcircumflex': 0x0125, 'Hbar': 0x0126, 'hbar': 0x0127,
    'Itilde': 0x0128, 'itilde': 0x0129, 'Imacron': 0x012A, 'imacron': 0x012B, 'Ibreve': 0x012C, 'ibreve': 0x012D,
    'Iogonek': 0x012E, 'iogonek': 0x012F, 'Idotaccent': 0x0130, 'dotlessi': 0x0131, 'IJ': 0x0132, 'ij': 0x0133,
    'Jcircumflex': 0x0134, 'jcircumflex': 0x0135, 'uni0136': 0x0136, 'uni0137': 0x0137,
    'Lacute': 0x0139, 'lacute': 0x013A, 'uni013B': 0x013B, 'uni013C': 0x013C, 'Lcaron': 0x013D, 'lcaron': 0x013E,
    'Ldot': 0x013F, 'ldot': 0x0140, 'Lslash': 0x0141, 'lslash': 0x0142,
    'Nacute': 0x0143, 'nacute': 0x0144, 'uni0145': 0x0145, 'uni0146': 0x0146, 'Ncaron': 0x0147, 'ncaron': 0x0148,
    'Eng': 0x014A, 'eng': 0x014B, 'Omacron': 0x014C, 'omacron': 0x014D, 'Obreve': 0x014E, 'obreve': 0x014F,
    'Ohungarumlaut': 0x0150, 'ohungarumlaut': 0x0151, 'OE': 0x0152, 'oe': 0x0153,
    'Racute': 0x0154, 'racute': 0x0155, 'uni0156': 0x0156, 'uni0157': 0x0157, 'Rcaron': 0x0158, 'rcaron': 0x0159,
    'Sacute': 0x015A, 'sacute': 0x015B, 'Scircumflex': 0x015C, 'scircumflex': 0x015D, 'Scedilla': 0x015E, 'scedilla': 0x015F,
    'Scaron': 0x0160, 'scaron': 0x0161, 'uni0162': 0x0162, 'uni0163': 0x0163, 'Tcaron': 0x0164, 'tcaron': 0x0165,
    'Tbar': 0x0166, 'tbar': 0x0167, 'Utilde': 0x0168, 'utilde': 0x0169, 'Umacron': 0x016A, 'umacron': 0x016B,
    'Ubreve': 0x016C, 'ubreve': 0x016D, 'Uring': 0x016E, 'uring': 0x016F, 'Uhungarumlaut': 0x0170, 'uhungarumlaut': 0x0171,
    'Uogonek': 0x0172, 'uogonek': 0x0173, 'Wcircumflex': 0x0174, 'wcircumflex': 0x0175,
    'Ycircumflex': 0x0176, 'ycircumflex': 0x0177, 'Ydieresis': 0x0178,
    'Zacute': 0x0179, 'zacute': 0x017A, 'Zdotaccent': 0x017B, 'zdotaccent': 0x017C, 'Zcaron': 0x017D, 'zcaron': 0x017E,
    'florin': 0x0192, 'uni0218': 0x0218, 'uni0219': 0x0219, 'uni021A': 0x021A, 'uni021B': 0x021B,
    'uni0237': 0x0237,
    'circumflex': 0x02C6, 'caron': 0x02C7, 'breve': 0x02D8, 'dotaccent': 0x02D9,
    'ring': 0x02DA, 'ogonek': 0x02DB, 'tilde': 0x02DC, 'hungarumlaut': 0x02DD,
    'Wgrave': 0x1E80, 'wgrave': 0x1E81, 'Wacute': 0x1E82, 'wacute': 0x1E83, 'Wdieresis': 0x1E84, 'wdieresis': 0x1E85,
    'uni1E9E': 0x1E9E, 'Ygrave': 0x1EF2, 'ygrave': 0x1EF3,
    'endash': 0x2013, 'emdash': 0x2014, 'quoteleft': 0x2018, 'quoteright': 0x2019, 'quotesinglbase': 0x201A,
    'quotedblleft': 0x201C, 'quotedblright': 0x201D, 'quotedblbase': 0x201E,
    'dagger': 0x2020, 'daggerdbl': 0x2021, 'bullet': 0x2022, 'ellipsis': 0x2026, 'perthousand': 0x2030,
    'guilsinglleft': 0x2039, 'guilsinglright': 0x203A, 'fraction': 0x2044, 'uni2070': 0x2070, 'uni2074': 0x2074,
    'Euro': 0x20AC, 'trademark': 0x2122, 'minus': 0x2212, 'fi': 0xFB01, 'fl': 0xFB02,
}

def assemble(g):
    parts = [stroke(p, W * g.get('ws', 1.0)) for p in g['sk']] + g['solid']
    if not SERIFS: return union(parts)
    for x, y in g['top']: parts.append(serif(x, y, 'l', 'top'))
    for x, y in g['foot']: parts.append(serif(x, y, 'r', 'foot'))
    for x, y in g['full_top']: parts.append(serif(x, y, 'b', 'top'))
    for x, y in g['full_foot']: parts.append(serif(x, y, 'b', 'foot'))
    return union(parts)

def body_center(p, lo, hi):
    sub = op(p, rect(-2000, lo, 3000, hi), PathOp.INTERSECTION)
    b = sub.bounds if len(list(sub.contours)) else p.bounds
    return (b[0] + b[2]) / 2

UPPER_SPECIAL = {'AE', 'OE', 'Oslash', 'Lslash', 'Eth', 'Dcroat', 'Thorn', 'uni1E9E', 'Hbar', 'Tbar', 'Eng', 'Ldot', 'IJ'}
def _is_caps(name):
    b = ACCENTED.get(name, (name,))[0]
    if b in UPPER_SPECIAL or name in SYMS: return True
    return len(b) == 1 and b.isupper()

def build_glyph(name, italic=False):
    global SX
    base_key = ACCENTED.get(name, (name,))[0]
    SX = (CAPS_SX if _is_caps(name) else SX_BASE) + SX_BONUS.get(base_key, 0)
    try:
        return _build_glyph(name, italic)
    finally:
        SX = SX_BASE

def _build_glyph(name, italic=False):
    if ITALIC_SINGLE_A and italic and name == 'a': return assemble(g_a_ital())
    if name in ACCENTED:
        bn, mk = ACCENTED[name]
        base = assemble(g_a_ital()) if (ITALIC_SINGLE_A and italic and bn == 'a') else assemble(BASE[bn]())
        upper = bn[0].isupper() or bn in UPPER_SPECIAL
        if mk in BELOW_MARKS:
            cx = body_center(base, 0, 140)
            m = BELOW_MARKS[mk]()
            if mk == 'ogonek' and bn in ('A', 'a', 'I', 'i', 'U', 'u'):
                b = op(base, rect(-2000, 0, 3000, 120), PathOp.INTERSECTION).bounds
                cx = b[2] - HW * 0.6
            return union([base, m.transform(1, 0, 0, 1, cx + (10 if mk == 'cedilla' else 0), 0)])
        cx = body_center(base, 0, CAP if upper else XH)
        m = MARKS[mk](upper)
        mb = m.bounds; mcx = (mb[0] + mb[2]) / 2
        return union([base, m.transform(1, 0, 0, 1, cx - mcx, 0)])
    return assemble(BASE[name]())

def finish(p):
    return round_corners(p, P['rv'], P['rc'])

def shear(p, y0=XH / 2):
    t = math.tan(math.radians(ITALIC_ANGLE))
    return p.transform(1, 0, t, 1, -t * y0, 0)
