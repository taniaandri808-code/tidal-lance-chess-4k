import sys, json, os, urllib.request
EMPT, WP, WN, WB, WR, WQ, WK = 0, 1, 2, 3, 4, 5, 6
BP, BN, BB, BR, BQ, BK = 9, 10, 11, 12, 13, 14
VAL = [0, 100, 320, 330, 500, 900, 20000, 0,
 0, 100, 320, 330, 500, 900, 20000]
MATE = 1000000
N, S, E, W = 16, -16, 1, -1
KNIGHT_D = (33, 31, 18, 14, -33, -31, -18, -14)
BISHOP_D = (17, 15, -17, -15)
ROOK_D = (16, -16, 1, -1)
KING_D = (17, 16, 15, 1, -1, -15, -16, -17)
def sq0x88(f, r):  # file 0-7, rank 0-7 (rank0 = rank1)
 return 16 * r + f
START = ("rnbqkbnr" "pppppppp" "." * 32 + "PPPPPPPP" "RNBQKBNR")
def mk_start():
 b = [EMPT] * 128
 i = 0
 for r in range(7, -1, -1):
  for f in range(8):
   c = START[i]; i += 1
   if c == '.': continue
   p = " PNBRQK".index(c) if c.isupper() else 8 + " PNBRQK".index(c.upper())
   b[16 * r + f] = p
 return b
def parse_fen(fen):
 b = [EMPT] * 128
 parts = fen.split()
 rows = parts[0].split('/')
 for ri, row in enumerate(rows):
  r = 7 - ri
  f = 0
  for c in row:
   if c.isdigit(): f += int(c)
   else:
    p = " PNBRQK".index(c) if c.isupper() else 8 + " PNBRQK".index(c.upper())
    b[16 * r + f] = p; f += 1
 side = 0 if parts[1] == 'w' else 1
 cast = 0
 if len(parts) > 2 and parts[2] != '-':
  for c in parts[2]:
   cast |= {'K': 1, 'Q': 2, 'k': 4, 'q': 8}.get(c, 0)
 ep = -1
 if len(parts) > 3 and parts[3] != '-':
  ep = sq0x88(ord(parts[3][0]) - 97, int(parts[3][1]) - 1)
 return b, side, cast, ep
def uci_sq(s):
 return chr(97 + (s & 7)) + str((s >> 4) + 1)
def parse_sq(t):
 return sq0x88(ord(t[0]) - 97, int(t[1]) - 1)
def attacked(b, s, by_white):
 if by_white:
  for d in (-15, -17):
   t = s + d
   if not t & 0x88 and b[t] == WP: return True
 else:
  for d in (15, 17):
   t = s + d
   if not t & 0x88 and b[t] == BP: return True
 kn = WN if by_white else BN
 for d in KNIGHT_D:
  t = s + d
  if not t & 0x88 and b[t] == kn: return True
 k = WK if by_white else BK
 for d in KING_D:
  t = s + d
  if not t & 0x88 and b[t] == k: return True
 bq = ((WB, BISHOP_D), (WR, ROOK_D), (WQ, KING_D)) if by_white else ((BB, BISHOP_D), (BR, ROOK_D), (BQ, KING_D))
 for pc, dirs in bq:
  for d in dirs:
   t = s + d
   while not t & 0x88:
    if b[t]:
     if b[t] == pc: return True
     break
    t += d
 return False
def king_sq(b, white):
 k = WK if white else BK
 for s in range(128):
  if not s & 0x88 and b[s] == k: return s
 return -1
def gen_moves(b, side, cast, ep, caps_only=False):
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
    if caps_only:
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
    if tp and ((tp > 8) != (p > 8)):
     if (t >> 4) in (7, 0):
      for pr in (5, 4, 3, 2): mv.append((s, t, pr))
     else: mv.append((s, t, 0))
    elif t == ep and ep >= 0:
     mv.append((s, t, 0))
  elif p == WN or p == BN:
   for d in KNIGHT_D:
    t = s + d
    if t & 0x88: continue
    tp = b[t]
    if (tp == EMPT and not caps_only) or (tp and (tp > 8) != (p > 8)):
     mv.append((s, t, 0))
  elif p == WK or p == BK:
   for d in KING_D:
    t = s + d
    if t & 0x88: continue
    tp = b[t]
    if (tp == EMPT and not caps_only) or (tp and (tp > 8) != (p > 8)):
     mv.append((s, t, 0))
   if not caps_only:
    white = p == WK
    home = 0x04 if white else 0x74
    if s == home and not attacked(b, s, not white):
     rk = WR if white else BR
     if cast & (1 if white else 4) and b[home+3] == rk and b[home+1] == EMPT and b[home+2] == EMPT \
     and not attacked(b, home+1, not white) and not attacked(b, home+2, not white):
      mv.append((s, home+2, 0))
     if cast & (2 if white else 8) and b[home-4] == rk and b[home-1] == EMPT and b[home-2] == EMPT and b[home-3] == EMPT \
     and not attacked(b, home-1, not white) and not attacked(b, home-2, not white):
      mv.append((s, home-2, 0))
  else:
   dirs = BISHOP_D if p in (WB, BB) else ROOK_D if p in (WR, BR) else KING_D
   for d in dirs:
    t = s + d
    while not t & 0x88:
     tp = b[t]
     if tp == EMPT:
      if not caps_only: mv.append((s, t, 0))
     else:
      if (tp > 8) != (p > 8): mv.append((s, t, 0))
      break
     t += d
 return mv
def mk_move(b, side, cast, ep, m):
 s, t, pr = m
 nb = b[:]
 p = nb[s]
 cap = nb[t]
 ncast = cast
 nep = -1
 nb[t] = p
 nb[s] = EMPT
 if p == WP or p == BP:
  if t == ep and ep >= 0:
   nb[t - (16 if p == WP else -16)] = EMPT
  if abs(t - s) == 32:
   nep = (s + t) // 2
  if pr: nb[t] = pr if p == WP else pr + 8
 elif p == WK:
  ncast &= ~3
  if t - s == 2:
   nb[t-1] = nb[t+1]; nb[t+1] = EMPT
  elif t - s == -2:
   nb[t+1] = nb[t-2]; nb[t-2] = EMPT
 elif p == BK:
  ncast &= ~12
  if t - s == 2:
   nb[t-1] = nb[t+1]; nb[t+1] = EMPT
  elif t - s == -2:
   nb[t+1] = nb[t-2]; nb[t-2] = EMPT
 if s == 0x00 or t == 0x00 or s == 0x07 or t == 0x07: ncast &= ~3
 if s == 0x70 or t == 0x70 or s == 0x77 or t == 0x77: ncast &= ~12
 if s == 0x00: ncast &= ~2
 if s == 0x07: ncast &= ~1
 if s == 0x70: ncast &= ~8
 if s == 0x77: ncast &= ~4
 return nb, 1 - side, ncast, nep, cap
def apply(b, side, cast, ep, m):
 s, t, pr = m
 undo = []
 def put(i, v):
  undo.append((i, b[i])); b[i] = v
 p = b[s]
 cap = b[t]
 put(t, p)
 put(s, EMPT)
 ncast = cast
 nep = -1
 if p == WP or p == BP:
  if t == ep and ep >= 0:
   csq = t - (16 if p == WP else -16)
   put(csq, EMPT)
  if abs(t - s) == 32:
   nep = (s + t) // 2
  if pr: put(t, pr if p == WP else pr + 8)
 elif p == WK:
  ncast &= ~3
  if t - s == 2:
   put(t-1, b[t+1]); put(t+1, EMPT)
  elif t - s == -2:
   put(t+1, b[t-2]); put(t-2, EMPT)
 elif p == BK:
  ncast &= ~12
  if t - s == 2:
   put(t-1, b[t+1]); put(t+1, EMPT)
  elif t - s == -2:
   put(t+1, b[t-2]); put(t-2, EMPT)
 for sq, bit in ((0, 2), (7, 1), (0x70, 8), (0x77, 4)):
  if s == sq or t == sq: ncast &= ~bit
 return 1 - side, ncast, nep, cap, undo
def unapply(b, undo):
 for i, v in reversed(undo):
  b[i] = v
def legal_moves(b, side, cast, ep):
 out = []
 ks = king_sq(b, side == 0)
 for m in gen_moves(b, side, cast, ep):
  ns, nc, ne, cap, u = apply(b, side, cast, ep, m)
  ksq = ks if b[ks] else king_sq(b, side == 0)
  bad = attacked(b, ksq, ns == 0)
  unapply(b, u)
  if not bad:
   out.append(m)
 return out
def poskey(b, side, cast, ep):
 return (bytes(b), side, cast, ep)
from base64 import b64decode as _b64
PST = [_b64(t) for t in ("MjIyMjIyMjJkZGRkZGRkZDw8RlBQRjw8Nzc8S0s8NzcyMjJGRjIyMjctKDIyKC03Nzw8Hh48PDcyMjIyMjIyMg==","AAoUFBQUCgAKHjIyMjIeChQyPEFBPDIUFDdBRkZBNxQUMkFGRkEyFBQ3PEFBPDcUCh4yNzcyHgoAChQUFBQKAA==","HigoKCgoKB4oMjIyMjIyKCgyNzw8NzIoKDc3PDw3NygoMjw8PDwyKCg8PDw8PDwoKDcyMjIyNygeKCgoKCgoHg==","MjIyMjIyMjI3PDw8PDw8Ny0yMjIyMjItLTIyMjIyMi0tMjIyMjIyLS0yMjIyMjItLTIyMjIyMi0yMjI3NzIyMg==","HigoLS0oKB4oMjIyMjIyKCgyNzc3NzIoLTI3Nzc3Mi0yMjc3NzcyLSg3Nzc3NzIoKDI3MjIyMigeKCgtLSgoHg==","FAoKAAAKChQUCgoAAAoKFBQKCgAACgoUFAoKAAAKChQeFBQKChQUHigeHh4eHh4oRkYyMjIyRkZGUDwyMjxQRg==")]
def pst(p, s):
 f = s & 7; r = s >> 4
 i = (7 - r) * 8 + f if p < 8 else r * 8 + f
 return PST[(p & 7) - 1][i] - 50
def evaluate(b, side):
 sc = 0
 wb = bb = 0
 for s in range(128):
  if s & 0x88: continue
  p = b[s]
  if not p: continue
  v = VAL[p] + pst(p, s)
  if p < 8: sc += v
  else: sc -= v
  if p == WB: wb += 1
  elif p == BB: bb += 1
 if wb >= 2: sc += 30
 if bb >= 2: sc -= 30
 return sc if side == 0 else -sc
def search(b, side, cast, ep, hist_keys, max_nodes):
 nodes = [0]
 class NL(Exception): pass
 tt = {}
 def reps(key):
  return hist_keys.count(key) >= 2 or hist_keys[-16:].count(key) >= 2
 def quiesce(b, alpha, beta, side, cast, ep, ply):
  nodes[0] += 1
  if nodes[0] > max_nodes: raise NL()
  if attacked(b, king_sq(b, side == 0), side == 1):
   moves = legal_moves(b, side, cast, ep)
   if not moves: return -MATE + ply
   best = -MATE * 2
   for m in moves:
    nb, ns, nc, ne, cap = mk_move(b, side, cast, ep, m)
    sc = -quiesce(nb, -beta, -alpha, ns, nc, ne, ply + 1)
    if sc > best:
     best = sc
     if sc > alpha: alpha = sc
     if alpha >= beta: break
   return best
  st = evaluate(b, side)
  if st >= beta: return beta
  if st > alpha: alpha = st
  for m in gen_moves(b, side, cast, ep, True):
   nb, ns, nc, ne, cap = mk_move(b, side, cast, ep, m)
   if cap == 0 and m[1] != ep:
    continue
   sc = -quiesce(nb, -beta, -alpha, ns, nc, ne, ply + 1)
   if sc >= beta: return beta
   if sc > alpha: alpha = sc
  return alpha
 def ab(b, depth, alpha, beta, side, cast, ep, ply):
  nodes[0] += 1
  if nodes[0] > max_nodes: raise NL()
  key = poskey(b, side, cast, ep)
  e = tt.get(key)
  if e is not None and e[3] >= depth and ply > 1 and abs(e[1]) < MATE - 1000:
   fl, sc, _, _ = e
   if fl == 0: return sc
   if fl == 1 and sc >= beta: return sc
   if fl == 2 and sc <= alpha: return sc
  if depth <= 0:
   return quiesce(b, alpha, beta, side, cast, ep, ply)
  if reps(key): return 0
  best = -MATE * 2
  fl = 1
  a0 = alpha
  bm = None
  moves = legal_moves(b, side, cast, ep)
  if not moves:
   if attacked(b, king_sq(b, side == 0), side == 1): return -MATE + ply
   return 0
  def mkey(m):
   s, t, pr = m
   cap = b[t]
   k = 0
   if cap: k = 1000 + VAL[cap if cap < 8 else cap - 8]
   if e is not None and e[2] == m: k += 10000
   return k
  moves.sort(key=mkey, reverse=True)
  for m in moves:
   nb, ns, nc, ne, cap = mk_move(b, side, cast, ep, m)
   sc = -ab(nb, depth - 1, -beta, -alpha, ns, nc, ne, ply + 1)
   if sc > best:
    best = sc
    if sc > alpha:
     alpha = sc; fl = 0; bm = m
     if alpha >= beta:
      fl = 1; break
  if abs(best) < MATE - 1000 and bm is not None:
   if alpha >= beta: flag = 1
   elif best > a0: flag = 0
   else: flag = 2
   tt[key] = (flag, best, bm, depth)
  return best
 best_m = None
 try:
  for d in range(1, 64):
   a = -MATE * 2
   bm2 = None
   moves = legal_moves(b, side, cast, ep)
   moves.sort(key=lambda m: (1000 + (10 * VAL[b[m[1]]] if b[m[1]] else 0)), reverse=True)
   if best_m in moves:
    moves.remove(best_m)
    moves.insert(0, best_m)
   for m in moves:
    nb, ns, nc, ne, cap = mk_move(b, side, cast, ep, m)
    sc = -ab(nb, d - 1, -MATE * 2, -a, ns, nc, ne, 1)
    if sc > a:
     a = sc
     bm2 = m
   best_m = bm2
   if a > MATE - 100 or a < -MATE + 100:
    break
 except NL:
  pass
 if best_m is None:
  lm = legal_moves(b, side, cast, ep)
  best_m = lm[0] if lm else None
 return best_m
def move_uci(m):
 s, t, pr = m
 u = uci_sq(s) + uci_sq(t)
 if pr: u += {2: "n", 3: "b", 4: "r", 5: "q"}[pr]
 return u
def bestmove(fen, moves, hist=None, budget=120000):
 b, side, cast, ep = parse_fen(fen)
 hist = list(hist or [])
 hist.append(poskey(b, side, cast, ep))
 m = search(b, side, cast, ep, hist, budget)
 return move_uci(m) if m else ""
def post(url, path, payload):
 req = urllib.request.Request(url + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
 return json.loads(urllib.request.urlopen(req).read())
if __name__ == "__main__":
 url = os.environ.get("MAKEFUN_ENV_URL", "")
 if not url: sys.exit(0)
 g = 0
 while True:
  try:
   r = post(url, "/game", {})
  except Exception:
   print("game ?: connection lost"); sys.exit(0)
  g = r.get("game", g)
  opp = r.get("opponent", "?")
  st = r.get("status")
  hist = []
  while st == "your_move":
   uci = bestmove(r["fen"], r.get("moves", []), hist)
   if not uci:
    print(f"game {g}: no move"); sys.exit(1)
   r = post(url, "/move", {"game": g, "move": uci})
   st = r.get("status")
   if r.get("game") != g: g = r.get("game", g)
   if st == "your_move" and "fen" in r:
    b2, s2, c2, e2 = parse_fen(r["fen"])
    hist.append(poskey(b2, s2, c2, e2))
    if len(hist) > 32: del hist[:-32]
  if st == "over":
   print(f"game {g}: opponent={opp} result={r.get('result')} outcome={r.get('outcome')}")
   continue
  if st == "done":
   print(r); sys.exit(0)
