package main

import (
	"math/bits"
	"math/rand"
)

type Rules struct {
	Optional bool `json:"optional"` // house rule: jumping is optional
	Huff     bool `json:"huff"`     // old house rule: jumping optional, but the opponent may "huff" (remove) a piece that could have jumped
}

// Policy: search depth plus evaluation habits. Sees the whole board (checkers has no hidden information).
type Policy struct {
	Name    string  `json:"name"`
	Random  bool    `json:"random"`
	Depth   int     `json:"depth"`    // plies searched (captures are always searched out)
	KingVal float64 `json:"king_val"` // value of a king (a man = 100); normal 130
	BackRow float64 `json:"back_row"` // bonus per man still on your own back row
	Center  float64 `json:"center"`   // bonus per piece on the 8 centre squares
	Edge    float64 `json:"edge"`     // bonus per piece on the side columns
	Advance float64 `json:"advance"`  // bonus per row a man has advanced
	Trade   float64 `json:"trade"`    // when ahead, bonus per piece traded off (simplify when winning)
	NoHuff  bool    `json:"no_huff"`  // under the huffing rule, never huff
}

var centerMask, edgeMask uint32

func init() {
	for i := 0; i < 32; i++ {
		r, c := rc(i)
		if r >= 2 && r <= 5 && c >= 2 && c <= 5 {
			centerMask |= 1 << i
		}
		if c == 0 || c == 7 {
			edgeMask |= 1 << i
		}
	}
}

const backRed, backWhite uint32 = 0x0000000F, 0xF0000000

func (b *Policy) eval(p *Pos) float64 {
	s := p.Side
	kv := 130.0
	if b.KingVal != 0 {
		kv = b.KingVal
	}
	me, op := p.P[s], p.P[1-s]
	mk, ok := bits.OnesCount32(me&p.K), bits.OnesCount32(op&p.K)
	mm, om := bits.OnesCount32(me)-mk, bits.OnesCount32(op)-ok
	v := 100*float64(mm-om) + kv*float64(mk-ok)
	if b.BackRow != 0 {
		myBack, opBack := backRed, backWhite
		if s == 1 {
			myBack, opBack = backWhite, backRed
		}
		v += b.BackRow * float64(bits.OnesCount32(me&^p.K&myBack)-bits.OnesCount32(op&^p.K&opBack))
	}
	if b.Center != 0 {
		v += b.Center * float64(bits.OnesCount32(me&centerMask)-bits.OnesCount32(op&centerMask))
	}
	if b.Edge != 0 {
		v += b.Edge * float64(bits.OnesCount32(me&edgeMask)-bits.OnesCount32(op&edgeMask))
	}
	if b.Advance != 0 {
		v += b.Advance * (advance(me&^p.K, s) - advance(op&^p.K, 1-s))
	}
	if b.Trade != 0 {
		lead := float64(mm-om) + float64(mk-ok)
		if lead != 0 {
			v += b.Trade * lead * float64(24-bits.OnesCount32(me|op))
		}
	}
	return v
}

func advance(men uint32, side int) float64 {
	t := 0
	for x := men; x != 0; x &= x - 1 {
		r := bits.TrailingZeros32(x) / 4
		if side == 0 {
			t += r
		} else {
			t += 7 - r
		}
	}
	return float64(t)
}

const Win = 100000.0

type Searcher struct {
	R    *Rules
	B    *Policy
	bufs [64][]Move
	Nodes int
}

func (s *Searcher) moves(p *Pos, ply int) []Move {
	if s.bufs[ply] == nil {
		s.bufs[ply] = make([]Move, 0, 32)
	}
	s.bufs[ply] = p.Legal(s.bufs[ply], s.R.Optional || s.R.Huff)
	return s.bufs[ply]
}

// negamax with alpha-beta; at depth 0 it keeps searching while captures are on (quiescence).
// Move lists live in per-ply buffers, so the search doesn't allocate.
func (s *Searcher) search(p *Pos, depth, ply int, alpha, beta float64) float64 {
	s.Nodes++
	opt := s.R.Optional || s.R.Huff
	if depth <= 0 {
		if !p.HasCapture() || ply > 50 {
			if !p.HasSimple() && !p.HasCapture() {
				return -Win + float64(ply)
			}
			return s.B.eval(p)
		}
		s.bufs[ply] = p.Captures(s.buf(ply))
		best := -1e18
		if opt { // captures optional: standing pat is allowed
			best = s.B.eval(p)
			if best >= beta {
				return best
			}
			if best > alpha {
				alpha = best
			}
		}
		for i := 0; i < len(s.bufs[ply]); i++ {
			q := *p
			q.Apply(s.bufs[ply][i])
			v := -s.search(&q, 0, ply+1, -beta, -alpha)
			if v > best {
				best = v
			}
			if v > alpha {
				alpha = v
			}
			if alpha >= beta {
				break
			}
		}
		return best
	}
	s.bufs[ply] = p.Legal(s.buf(ply), opt)
	if len(s.bufs[ply]) == 0 {
		return -Win + float64(ply)
	}
	huffable := s.R.Huff && p.HasCapture()
	best := -1e18
	for i := 0; i < len(s.bufs[ply]); i++ {
		q := *p
		applyWithHuff(&q, s.bufs[ply][i], huffable)
		v := -s.search(&q, depth-1, ply+1, -beta, -alpha)
		if v > best {
			best = v
		}
		if v > alpha {
			alpha = v
		}
		if alpha >= beta {
			break
		}
	}
	return best
}

func (s *Searcher) buf(ply int) []Move {
	if s.bufs[ply] == nil {
		s.bufs[ply] = make([]Move, 0, 32)
	}
	return s.bufs[ply][:0]
}

// Choose: best move by search, ties broken at random.
func (s *Searcher) Choose(p *Pos, ms []Move, rng *rand.Rand) Move {
	if s.B.Random || len(ms) == 1 {
		return ms[rng.Intn(len(ms))]
	}
	d := s.B.Depth
	if d == 0 {
		d = 2
	}
	best, bv, ties := 0, -1e18, 0
	huffable := s.R.Huff && p.HasCapture()
	for k, m := range ms {
		q := *p
		applyWithHuff(&q, m, huffable)
		v := -s.search(&q, d-1, 1, -1e18, 1e18)
		if v > bv+1e-9 {
			best, bv, ties = k, v, 1
		} else if v > bv-1e-9 {
			ties++
			if rng.Intn(ties) == 0 {
				best = k
			}
		}
	}
	return ms[best]
}

type Result struct {
	Winner   int // 0 Red, 1 White, -1 draw
	Plies    int
	Captures int
	Huffs    int
	Repetition bool
}

var zob [4][32]uint64 // red man, white man, red king, white king

func init() {
	r := rand.New(rand.NewSource(12345))
	for i := range zob {
		for j := range zob[i] {
			zob[i][j] = r.Uint64()
		}
	}
}

func (p *Pos) Hash() uint64 {
	var h uint64
	for s := 0; s < 2; s++ {
		for b := p.P[s]; b != 0; b &= b - 1 {
			i := bits.TrailingZeros32(b)
			t := s
			if p.K&(1<<i) != 0 {
				t += 2
			}
			h ^= zob[t][i]
		}
	}
	if p.Side == 1 {
		h = ^h
	}
	return h
}

// Play one game. pol[0] plays Red (moves first).
func Play(rng *rand.Rand, R *Rules, pol [2]*Policy, srch [2]*Searcher) Result {
	p := StartPos()
	quiet := 0
	var res Result
	buf := make([]Move, 0, 32)
	hist := make([]uint64, 0, 128) // positions since the last man move or capture (repetition check)
	for ply := 0; ply < 400; ply++ {
		h := p.Hash()
		reps := 0
		for _, x := range hist {
			if x == h {
				reps++
			}
		}
		if reps >= 2 { // the same position for the third time (WCDF 1.32.1)
			res.Winner = -1
			res.Plies = ply
			res.Repetition = true
			return res
		}
		hist = append(hist, h)
		buf = p.Legal(buf, R.Optional || R.Huff)
		ms := buf
		if len(ms) == 0 {
			res.Winner = 1 - p.Side
			res.Plies = ply
			return res
		}
		s := p.Side
		m := srch[s].Choose(&p, ms, rng)
		hadCapture := false
		if R.Huff && m.Cap == 0 {
			caps := p.Captures(nil)
			hadCapture = len(caps) > 0
			if hadCapture && !pol[1-s].NoHuff {
				// the opponent huffs: removes one piece that could have jumped (a king if possible)
				var cand uint32
				for _, c := range caps {
					if c.From != m.From {
						cand |= 1 << c.From
					}
				}
				if cand == 0 { // the piece that could jump was the one that moved: it now sits on m.To
					cand = 1 << m.To
					p.Apply(m)
					huff(&p, cand, s)
					res.Huffs++
					quiet = 0
					hist = hist[:0]
					continue
				}
				p.Apply(m)
				huff(&p, cand, s)
				res.Huffs++
				quiet = 0
				hist = hist[:0]
				continue
			}
		}
		if m.Cap != 0 || p.IsManMove(m) {
			quiet = 0
			hist = hist[:0]
		} else {
			quiet++
		}
		if m.Cap != 0 {
			res.Captures++
		}
		p.Apply(m)
		if quiet >= 80 { // 40 moves each with no man advanced and no capture (WCDF 1.32.2)
			res.Winner = -1
			res.Plies = ply + 1
			return res
		}
	}
	res.Winner = -1
	res.Plies = 400
	return res
}

// applyWithHuff: Apply, and if this quiet move ignored an available jump under the huff rule, the opponent
// removes a piece that could have jumped (the search assumes they always do).
func applyWithHuff(q *Pos, m Move, huffable bool) {
	if !huffable || m.Cap != 0 {
		q.Apply(m)
		return
	}
	s := q.Side
	caps := q.Captures(nil)
	var cand uint32
	for _, c := range caps {
		if c.From != m.From {
			cand |= 1 << c.From
		}
	}
	q.Apply(m)
	if cand == 0 {
		cand = 1 << m.To
	}
	huff(q, cand, s)
}

func huff(p *Pos, cand uint32, owner int) {
	pick := cand & p.K
	if pick == 0 {
		pick = cand
	}
	b := pick & -pick
	p.P[owner] &^= b
	p.K &^= b
}
