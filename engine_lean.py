import sys, os, random
from json import dumps, loads
from urllib.request import Request, urlopen
EMPT, WP, WN, WB, WR, WQ, WK = 0, 1, 2, 3, 4, 5, 6
BP, BN, BB, BR, BQ, BK = 9, 10, 11, 12, 13, 14
VAL = [0, 100, 320, 330, 500, 900, 20000, 0, 0, 100, 320, 330, 500, 900, 20000]
MATE = 1000000
KD = (33, 31, 18, 14, -33, -31, -18, -14)
BD = (17, 15, -17, -15)
RD = (16, -16, 1, -1)
KGD = (17, 16, 15, 1, -1, -15, -16, -17)
ND = 150000

RG = random.Random(20261123)
ZP = [[RG.getrandbits(64) for _ in range(128)] for _ in range(15)]
ZC = [RG.getrandbits(64) for _ in range(16)]
ZE = [RG.getrandbits(64) for _ in range(16)]
ZS = RG.getrandbits(64)

def pf(fen):
    b = [0] * 128; q = fen.split(); r = 7; f = 0
    for c in q[0]:
        if c == '/': r -= 1; f = 0
        elif c.isdigit(): f += int(c)
        else: b[16 * r + f] = " PNBRQK".index(c) if c.isupper() else 8 + " PNBRQK".index(c.upper()); f += 1
    side = 0 if q[1] == 'w' else 1
    cast = sum({'K': 1, 'Q': 2, 'k': 4, 'q': 8}.get(x, 0) for x in (q[2] if len(q) > 2 else '-'))
    ep = -1 if len(q) < 4 or q[3] == '-' else (ord(q[3][0]) - 97) + 16 * (int(q[3][1]) - 1)
    return b, side, cast, ep

def usq(s): return chr(97 + (s & 7)) + str((s >> 4) + 1)
def psq(t): return 16 * int(t[1]) + ord(t[0]) - 113

kings = [0x04, 0x74]
KEY = [0]

def atk(b, s, bw):
    o = 0 if bw else 8
    for d in (-15, -17) if bw else (15, 17):
        t = s + d
        if not t & 0x88 and b[t] == o + 1: return True
    for pc, dirs, sl in ((o + 2, KD, 0), (o + 6, KGD, 0), (o + 3, BD, 1), (o + 4, RD, 1), (o + 5, KGD, 1)):
        for d in dirs:
            t = s + d
            if sl:
                while not t & 0x88:
                    if b[t]:
                        if b[t] == pc: return True
                        break
                    t += d
            elif not t & 0x88 and b[t] == pc: return True
    return False

def gm(b, side, cast, ep, co=False):
    mv = []
    lo, hi = (1, 6) if side == 0 else (9, 14)
    fwd = 16 if side == 0 else -16
    for s in range(128):
        if s & 0x88: continue
        p = b[s]
        if not (lo <= p <= hi): continue
        if p == WP or p == BP:
            t = s + fwd
            if not t & 0x88:
                if co:
                    if t == ep: mv.append((s, t, 0))
                elif b[t] == EMPT:
                    if (t >> 4) in (7, 0):
                        for pr in (5, 4, 3, 2): mv.append((s, t, pr))
                    else: mv.append((s, t, 0))
                    r2 = s + 2 * fwd
                    if (s >> 4) == (1 if side == 0 else 6) and b[r2] == EMPT:
                        mv.append((s, r2, 0))
            for d in (fwd + 1, fwd - 1):
                t = s + d
                if t & 0x88: continue
                tp = b[t]
                if tp and (tp ^ p) & 8:
                    if (t >> 4) in (7, 0):
                        for pr in (5, 4, 3, 2): mv.append((s, t, pr))
                    else: mv.append((s, t, 0))
                elif t == ep != -1:
                    mv.append((s, t, 0))
        elif p & 7 in (2, 6):
            for d in KD if p & 7 == 2 else KGD:
                t = s + d
                if t & 0x88: continue
                tp = b[t]
                if (tp == EMPT and not co) or (tp and (tp ^ p) & 8):
                    mv.append((s, t, 0))
            if not co:
                white = p == WK
                home = 0x04 if white else 0x74
                if s == home and not atk(b, s, not white):
                    rk = WR if white else BR
                    if cast & (1 if white else 4) and b[home+3] == rk and b[home+1] == EMPT and b[home+2] == EMPT \
                       and not atk(b, home+1, not white) and not atk(b, home+2, not white):
                        mv.append((s, home+2, 0))
                    if cast & (2 if white else 8) and b[home-4] == rk and b[home-1] == EMPT and b[home-2] == EMPT and b[home-3] == EMPT \
                       and not atk(b, home-1, not white) and not atk(b, home-2, not white):
                        mv.append((s, home-2, 0))
        else:
            dirs = BD if p in (WB, BB) else RD if p in (WR, BR) else KGD
            for d in dirs:
                t = s + d
                while not t & 0x88:
                    tp = b[t]
                    if tp == EMPT:
                        if not co: mv.append((s, t, 0))
                    else:
                        if (tp ^ p) & 8: mv.append((s, t, 0))
                        break
                    t += d
    return mv

def apl(b, side, cast, ep, m, nul=False):
    if nul:
        undo = [KEY[0], kings[0], kings[1]]
        k = KEY[0] ^ ZS ^ (ZE[ep & 15] if ep != -1 else 0)
        KEY[0] = k
        return 1 - side, cast, -1, undo
    s, t, pr = m
    undo = [KEY[0], kings[0], kings[1], s, b[s], t, b[t], cast, ep]
    p = b[s]
    k = KEY[0] ^ ZS ^ (ZE[ep & 15] if ep != -1 else 0)
    cap = b[t]
    if p: k ^= ZP[p][s]
    if cap: k ^= ZP[cap][t]
    b[t] = p; b[s] = EMPT
    k ^= ZP[p][t]
    nep = -1
    ncast = cast
    if p == WP or p == BP:
        if t == ep != -1:
            csq = t - (16 if p == WP else -16)
            undo += [csq, b[csq]]
            k ^= ZP[b[csq]][csq]
            b[csq] = EMPT
        if abs(t - s) == 32:
            nep = (s + t) // 2
        if pr: b[t] = pr if p == WP else pr + 8; k ^= ZP[p][t] ^ ZP[b[t]][t]
    elif p & 7 == 6:
        ncast &= 12 if p == WK else 3
        kings[p == BK] = t
        if abs(t - s) == 2:
            rf, rt = (t + 1, t - 1) if t > s else (t - 2, t + 1)
            r0 = b[rf]
            undo += [rf, r0, rt, b[rt]]
            b[rt] = r0; b[rf] = EMPT
            k ^= ZP[r0][rf] ^ ZP[r0][rt]
    if cast:
        for sq, bit in ((0, 2), (7, 1), (0x70, 8), (0x77, 4)):
            if s == sq or t == sq: ncast &= ~bit
    k ^= ZC[ncast] ^ ZC[cast]
    if nep >= 0: k ^= ZE[nep & 15]
    KEY[0] = k
    return 1 - side, ncast, nep, undo

def unp(b, side, cast, ep, m, undo):
    if len(undo) == 3:
        KEY[0] = undo[0]; kings[0] = undo[1]; kings[1] = undo[2]
        return
    s, t, pr = m
    (k0, w0, b0, us, up, ut, ucap, ucast, uep) = undo[:9]
    b[us] = up; b[ut] = ucap
    for i in range(9, len(undo), 2):
        b[undo[i]] = undo[i + 1]
    kings[0] = w0; kings[1] = b0
    KEY[0] = k0

from base64 import b64decode
import zlib
PST = zlib.decompress(b64decode("eNqFUC0aQzEIq0aj0RgMBoOpwcz0ELv/GRbaVzGxbxFNAyT9cT94P8istSozIl8vrGhVYQlTdzWUUwTtx+aDGKBB0kqIPedMZ45ZNYPZm1t3PRhzCBW6PtEN0ROn6tHpqn1SBHQC0LmBeo+FXt+9R5x+2JH2j9vSUcgx+z4fwEsPmz+scero77nrY6IxCI/5wdI7ZlHZ0P2Z+NJa6Z6rPs4TQ5A="))


def pstv(p, s):
    r = s >> 4
    return PST[((p & 7) - 1) * 64 + ((7 - r) * 8 + (s & 7) if p < 8 else r * 8 + (s & 7))] - 50

def ev(b, side):
    sc = 0
    wb = bb = 0
    for s in SQS:
        p = b[s]
        if not p: continue
        v = VAL[p] + pstv(p, s)
        if p < 8: sc += v
        else: sc -= v
        if p == WB: wb += 1
        elif p == BB: bb += 1
    if wb >= 2: sc += 30
    if bb >= 2: sc -= 30
    return sc if side == 0 else -sc

class NL(Exception): pass

def search(b, side, cast, ep, hist_keys, max_nodes):
    nodes = [0]
    tt = {}
    HK = list(hist_keys)
    def qs(alpha, beta, side, cast, ep, ply):
        nodes[0] += 1
        if nodes[0] > max_nodes: raise NL()
        if ply > 40: return ev(b, side)
        if atk(b, kings[side], side == 1):
            best = -MATE * 2
            for m in gm(b, side, cast, ep):
                ns, nc, ne, u = apl(b, side, cast, ep, m)
                if atk(b, kings[side], ns == 0):
                    unp(b, side, cast, ep, m, u); continue
                sc = -qs(-beta, -alpha, ns, nc, ne, ply + 1)
                unp(b, side, cast, ep, m, u)
                if sc > best:
                    best = sc
                    if sc > alpha: alpha = sc
                    if alpha >= beta: break
            return best if best > -MATE * 2 else (-MATE + ply if atk(b, kings[side], side == 0) else 0)
        st = ev(b, side)
        if st >= beta: return beta
        if st > alpha: alpha = st
        for m in gm(b, side, cast, ep, True):
            if b[m[1]] == 0 and m[1] != ep: continue
            ns, nc, ne, u = apl(b, side, cast, ep, m)
            if atk(b, kings[side], ns == 0):
                unp(b, side, cast, ep, m, u); continue
            sc = -qs(-beta, -alpha, ns, nc, ne, ply + 1)
            unp(b, side, cast, ep, m, u)
            if sc >= beta: return beta
            if sc > alpha: alpha = sc
        return alpha
    def ab(depth, alpha, beta, side, cast, ep, ply, nm):
        nodes[0] += 1
        if nodes[0] > max_nodes: raise NL()
        k0 = KEY[0]
        e = tt.get(k0)
        if e is not None and e[3] >= depth and ply > 1 and abs(e[1]) < MATE - 1000:
            fl, sc, _, _ = e
            if fl == 0: return sc
            if fl == 1 and sc >= beta: return sc
            if fl == 2 and sc <= alpha: return sc
        incheck = atk(b, kings[side], side == 1)
        if depth <= 0: return qs(alpha, beta, side, cast, ep, ply)
        if ply > 0 and k0 in HK:
            return 0
        if not incheck and not nm and depth >= 3 and any(
                not s & 0x88 and 2 <= b[s] & 7 <= 5 for s in range(0 if side == 0 else 8, 8 if side == 0 else 16)):
                ns, nc, ne, u = apl(b, side, cast, ep, (0, 0, 0), nul=True)
                sc = -ab(depth - 3, -beta, -beta + 1, ns, nc, ne, ply + 1, True)
                unp(b, side, cast, ep, (0, 0, 0), u)
                if sc >= beta: return beta
        best = -MATE * 2; fl = 1; bm = None
        moves = gm(b, side, cast, ep)
        def mkey(m):
            s, t, pr = m
            cap = b[t]
            k = 1000000 + VAL[cap if cap < 8 else cap - 8] * 10 - VAL[b[s] if b[s] < 8 else b[s] - 8] // 10 if cap else 0
            if pr: k = 1000000 + VAL[pr] * 10
            if e is not None and e[2] == m: k += 10 ** 7
            return k
        moves.sort(key=mkey, reverse=True)
        legal = 0
        for m in moves:
            s, t, pr = m
            cap = b[t]
            quiet = cap == 0 and pr == 0 and t != ep
            ns, nc, ne, u = apl(b, side, cast, ep, m)
            if atk(b, kings[side], ns == 0):
                unp(b, side, cast, ep, m, u); continue
            legal += 1
            sc = -ab(depth - 1, -beta, -alpha, ns, nc, ne, ply + 1, False)
            unp(b, side, cast, ep, m, u)
            if sc > best:
                best = sc
                if sc > alpha:
                    alpha = sc; fl = 0; bm = m
                    if alpha >= beta:
                        fl = 1
                        break
        if legal == 0:
            return (-MATE + ply) if incheck else 0
        if abs(best) < MATE - 1000 and bm is not None:
            tt[k0] = (fl, best, bm, depth)
        return best
    best_m = None
    root = None
    try:
        for d in range(1, 64):
            a = -MATE * 2
            bm2 = None
            moves = gm(b, side, cast, ep)
            def rkey(m):
                cap = b[m[1]]
                k = 1000000 + VAL[cap if cap < 8 else cap - 8] if cap else 0
                if root and root[0] == m: k += 10 ** 9
                return k
            moves.sort(key=rkey, reverse=True)
            for m in moves:
                ns, nc, ne, u = apl(b, side, cast, ep, m)
                if atk(b, kings[side], ns == 0):
                    unp(b, side, cast, ep, m, u); continue
                sc = -ab(d - 1, -MATE * 2, -a, ns, nc, ne, 1, False)
                unp(b, side, cast, ep, m, u)
                if sc > a:
                    a = sc; bm2 = m
            if bm2 is not None:
                best_m = bm2
                root = (bm2,)
            if a > MATE - 100 or a < -MATE + 100:
                break
    except NL:
        pass
    if best_m is None:
        for m in gm(b, side, cast, ep):
            ns, nc, ne, u = apl(b, side, cast, ep, m)
            ok = not atk(b, kings[side], ns == 0)
            unp(b, side, cast, ep, m, u)
            if ok: best_m = m; break
    return best_m

def muci(m):
    s, t, pr = m
    u = usq(s) + usq(t)
    if pr: u += "nbrq"[pr - 2]
    return u

SQS = tuple(s for s in range(128) if not s & 0x88)

def rkey(b, side, cast, ep):
    k = 0
    for s in SQS:
        if b[s]: k ^= ZP[b[s]][s]
    k ^= ZC[cast]
    if ep >= 0: k ^= ZE[ep & 15]
    if side: k ^= ZS
    KEY[0] = k
    kings[0] = next(s for s in SQS if b[s] == WK)
    kings[1] = next(s for s in SQS if b[s] == BK)

def bmv(fen, moves, hist=None, budget=ND):
    b, side, cast, ep = pf(fen)
    rkey(b, side, cast, ep)
    hk = list(hist or [])
    hk.append(KEY[0])
    m = search(b, side, cast, ep, hk, budget)
    return muci(m) if m else ""

def post(url, path, payload):
    req = Request(url + path, data=dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return loads(urlopen(req).read())

if __name__ == "__main__":
    url = os.environ.get("MAKEFUN_ENV_URL", "")
    if not url: sys.exit(0)
    g = 0
    while True:
        try:
            r = post(url, "/game", {})
        except Exception:
            sys.exit(0)
        g = r.get("game", g)
        opp = r.get("opponent", "?")
        st = r.get("status")
        hist = []
        while st == "your_move":
            uci = bmv(r["fen"], r.get("moves", []), hist)
            if not uci:
                print(f"game {g}: no move"); sys.exit(1)
            r = post(url, "/move", {"game": g, "move": uci})
            st = r.get("status")
            g = r.get("game", g)
            if st == "your_move" and "fen" in r:
                b2, s2, c2, e2 = pf(r["fen"])
                rkey(b2, s2, c2, e2)
                hist = (hist + [KEY[0]])[-32:]
        if st == "over":
            print(g, opp, r.get("result"), r.get("outcome"))
            continue
        if st == "done":
            print(r); sys.exit(0)
