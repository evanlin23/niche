package main

import "math/rand"

// Cards: 1,2,3,4,5,7,8,10,11,12 and Sorry! (0).
const CSorry = 0

type Rules struct {
	NoExtraOne bool `json:"no_extra_one"` // 1958 pack without the optional fifth 1 (44 cards)
	TwoNoDraw  bool `json:"two_no_draw"`  // 2020 rules: a 2 does not draw again
	SorryFour  bool `json:"sorry_four"`   // 2020 rules: a Sorry! card may instead move a pawn forward 4
	Hand       int  `json:"hand"`         // adult variation: hold this many cards and choose one (0 = draw and play)
}

func newDeck(R *Rules) []int8 {
	d := make([]int8, 0, 45)
	for _, v := range []int8{1, 2, 3, 4, 5, 7, 8, 10, 11, 12, CSorry} {
		for i := 0; i < 4; i++ {
			d = append(d, v)
		}
	}
	if !R.NoExtraOne {
		d = append(d, 1)
	}
	return d
}

// State: everything on the board. Seat s plays colour Col[s].
type State struct {
	Loc [4][4]int16
	Occ [Track]int8 // -1 empty, else seat*4+pawn
	N   int
	Col [4]int
}

func (st *State) init(n int) {
	st.N = n
	cols := map[int][]int{2: {0, 2}, 3: {0, 1, 2}, 4: {0, 1, 2, 3}}[n]
	for s := 0; s < n; s++ {
		st.Col[s] = cols[s]
		for i := 0; i < 4; i++ {
			st.Loc[s][i] = Start
		}
	}
	for i := range st.Occ {
		st.Occ[i] = -1
	}
}

func (st *State) homeCount(s int) int {
	k := 0
	for i := 0; i < 4; i++ {
		if st.Loc[s][i] == HomeSq {
			k++
		}
	}
	return k
}

func (st *State) set(s, i, l int) {
	old := int(st.Loc[s][i])
	if isTrack(old) && int(st.Occ[old]) == s*4+i {
		st.Occ[old] = -1
	}
	st.Loc[s][i] = int16(l)
	if isTrack(l) {
		st.Occ[l] = int8(s*4 + i)
	}
}

func (st *State) bump(sq int) {
	o := int(st.Occ[sq])
	if o >= 0 {
		st.Occ[sq] = -1
		st.Loc[o/4][o%4] = Start
	}
}

// land puts pawn (s,i) on square l after a move: bumps an opponent there, then slides if the square starts a
// slide of another colour (bumping every pawn on the slide, own pawns too). The caller checks own-pawn landings.
func (st *State) land(s, i, l int) {
	if isTrack(l) {
		st.bump(l)
	}
	st.set(s, i, l)
	if isTrack(l) {
		if so := slideOwner[l]; so >= 0 && int(so) != st.Col[s] {
			end := int(slideEnd[l])
			for q := l + 1; q <= end; q++ {
				st.bump(q)
			}
			st.set(s, i, end)
		}
	}
}

// canLand: a pawn may not end on a square held by another of its own pawns (Start and Home excepted).
func (st *State) canLand(s, i, l int) bool {
	if !isTrack(l) && !isSafe(l) {
		return true
	}
	if isSafe(l) {
		for j := 0; j < 4; j++ {
			if j != i && int(st.Loc[s][j]) == l {
				return false
			}
		}
		return true
	}
	o := int(st.Occ[l])
	return o < 0 || o/4 != s || o == s*4+i
}

type Move struct {
	Kind  int8 // 0 forward, 1 start, 2 back, 3 split7, 4 switch11, 5 sorry, 6 pass
	P, P2 int8
	N, N2 int8
	T     int8 // switch/sorry target: seat*4+pawn
}

const (
	MFwd = iota
	MStart
	MBack
	MSplit
	MSwitch
	MSorry
	MPass
)

// apply returns false if the move is illegal in this state.
func (st *State) apply(s int, m Move) bool {
	c := st.Col[s]
	switch m.Kind {
	case MFwd:
		l := int(st.Loc[s][m.P])
		if l == Start || l == HomeSq {
			return false
		}
		to, ok := fwd(c, l, int(m.N))
		if !ok || !st.canLand(s, int(m.P), to) {
			return false
		}
		st.land(s, int(m.P), to)
	case MStart:
		if st.Loc[s][m.P] != Start {
			return false
		}
		e := exitSq(c)
		if !st.canLand(s, int(m.P), e) {
			return false
		}
		st.land(s, int(m.P), e)
	case MBack:
		l := int(st.Loc[s][m.P])
		if l == Start || l == HomeSq {
			return false
		}
		to := back(c, l, int(m.N))
		if !st.canLand(s, int(m.P), to) {
			return false
		}
		st.land(s, int(m.P), to)
	case MSplit:
		if !st.apply(s, Move{Kind: MFwd, P: m.P, N: m.N}) {
			return false
		}
		return st.apply(s, Move{Kind: MFwd, P: m.P2, N: m.N2})
	case MSwitch:
		a := int(st.Loc[s][m.P])
		ts, ti := int(m.T)/4, int(m.T)%4
		b := int(st.Loc[ts][ti])
		if !isTrack(a) || !isTrack(b) || ts == s {
			return false
		}
		st.Occ[a], st.Occ[b] = -1, -1
		st.Loc[ts][ti] = int16(a)
		st.Occ[a] = int8(ts*4 + ti)
		st.Loc[s][m.P] = int16(b)
		st.Occ[b] = int8(s*4 + int(m.P))
		if so := slideOwner[b]; so >= 0 && int(so) != c { // "if your switch landed you on a triangle ... slide"
			end := int(slideEnd[b])
			for q := b + 1; q <= end; q++ {
				st.bump(q)
			}
			st.set(s, int(m.P), end)
		}
	case MSorry:
		if st.Loc[s][m.P] != Start {
			return false
		}
		ts, ti := int(m.T)/4, int(m.T)%4
		b := int(st.Loc[ts][ti])
		if !isTrack(b) || ts == s {
			return false
		}
		st.land(s, int(m.P), b)
	}
	return true
}

// legal lists every legal move for card v (classic rules; SorryFour adds the 2020 option).
func (st *State) legal(s int, v int8, R *Rules, out []Move) []Move {
	out = out[:0]
	try := func(m Move) {
		cp := *st
		if cp.apply(s, m) {
			out = append(out, m)
		}
	}
	startDone := false
	for i := int8(0); i < 4; i++ {
		l := st.Loc[s][i]
		if l == HomeSq {
			continue
		}
		if l == Start {
			if (v == 1 || v == 2) && !startDone {
				try(Move{Kind: MStart, P: i})
				startDone = true // pawns in Start are interchangeable
			}
			continue
		}
		switch v {
		case 1, 2, 3, 5, 8, 12:
			try(Move{Kind: MFwd, P: i, N: v})
		case 4:
			try(Move{Kind: MBack, P: i, N: 4})
		case 10:
			try(Move{Kind: MFwd, P: i, N: 10})
			try(Move{Kind: MBack, P: i, N: 1})
		case 7:
			try(Move{Kind: MFwd, P: i, N: 7})
			for j := int8(0); j < 4; j++ {
				lj := st.Loc[s][j]
				if j == i || lj == Start || lj == HomeSq {
					continue
				}
				for a := int8(1); a <= 6; a++ {
					try(Move{Kind: MSplit, P: i, N: a, P2: j, N2: 7 - a})
				}
			}
		case 11:
			try(Move{Kind: MFwd, P: i, N: 11})
		case CSorry:
			if R.SorryFour {
				try(Move{Kind: MFwd, P: i, N: 4})
			}
		}
	}
	if v == 11 {
		for i := int8(0); i < 4; i++ {
			if !isTrack(int(st.Loc[s][i])) {
				continue
			}
			for q := 0; q < Track; q++ {
				o := st.Occ[q]
				if o >= 0 && int(o)/4 != s {
					try(Move{Kind: MSwitch, P: i, T: o})
				}
			}
		}
	}
	if v == CSorry {
		for i := int8(0); i < 4; i++ {
			if st.Loc[s][i] != Start {
				continue
			}
			for q := 0; q < Track; q++ {
				o := st.Occ[q]
				if o >= 0 && int(o)/4 != s {
					try(Move{Kind: MSorry, P: i, T: o})
				}
			}
			break // any pawn from Start will do
		}
	}
	return out
}

type Game struct {
	R     *Rules
	rng   *rand.Rand
	St    State
	Pols  []*Policy
	deck  []int8
	disc  []int8
	hands [4][]int8
	Turns int
	Cards int
	buf   []Move
	CS    *CardStats
	trackSeats []bool
}

// CardStats: how much each card moves the race (own progress gained + opponents' progress lost), per draw.
type CardStats struct {
	Draws [13]int
	Swing [13]float64
	Forfeit [13]int
	Shortcut int // backward moves that put a pawn 1-3 squares from its own Safety entry
	Bumps, Slides int
}

func NewGame(rng *rand.Rand, R *Rules, pols []*Policy) *Game {
	g := &Game{R: R, rng: rng, Pols: pols, buf: make([]Move, 0, 256)}
	g.St.init(len(pols))
	g.deck = newDeck(R)
	rng.Shuffle(len(g.deck), func(i, j int) { g.deck[i], g.deck[j] = g.deck[j], g.deck[i] })
	g.disc = make([]int8, 0, 45)
	if R.Hand > 0 {
		for s := range pols {
			for k := 0; k < R.Hand; k++ {
				g.hands[s] = append(g.hands[s], g.draw())
			}
		}
	}
	return g
}

func (g *Game) draw() int8 {
	if len(g.deck) == 0 {
		g.deck, g.disc = g.disc, g.deck[:0]
		g.rng.Shuffle(len(g.deck), func(i, j int) { g.deck[i], g.deck[j] = g.deck[j], g.deck[i] })
	}
	c := g.deck[len(g.deck)-1]
	g.deck = g.deck[:len(g.deck)-1]
	g.Cards++
	return c
}

func cardIdx(v int8) int { return int(v) } // Sorry! = 0

// Play: seats take turns starting with seat `first`; returns the winner.
func (g *Game) Play(first int) int {
	s := first
	for t := 0; t < 5000; t++ {
		g.Turns++
		if g.turn(s) {
			return s
		}
		s = (s + 1) % g.St.N
	}
	return -1
}

// turn: draw, move (a 2 draws again under the classic rules). Returns true if seat s has won.
func (g *Game) turn(s int) bool {
	for {
		var v int8
		if g.R.Hand > 0 {
			v = g.playFromHand(s)
		} else {
			v = g.draw()
			g.move(s, v)
		}
		g.disc = append(g.disc, v)
		if g.St.homeCount(s) == 4 {
			return true
		}
		if v != 2 || g.R.TwoNoDraw {
			return false
		}
	}
}

func (g *Game) move(s int, v int8) {
	ms := g.St.legal(s, v, g.R, g.buf)
	g.buf = ms
	var before [4]int
	if g.CS != nil {
		for q := 0; q < g.St.N; q++ {
			before[q] = g.St.score(q)
		}
		g.CS.Draws[cardIdx(v)]++
	}
	if len(ms) == 0 {
		if g.CS != nil {
			g.CS.Forfeit[cardIdx(v)]++
		}
		return
	}
	m, ok := g.Pols[s].Choose(g, s, v, ms)
	if !ok { // optional pass (only the 11 when it can't go forward)
		return
	}
	if g.CS != nil && m.Kind == MBack {
		cp := g.St
		cp.apply(s, m)
		p := progress(g.St.Col[s], int(cp.Loc[s][m.P]))
		if p >= 59-3 && p <= 58 && progress(g.St.Col[s], int(g.St.Loc[s][m.P])) < 30 {
			g.CS.Shortcut++
		}
	}
	g.St.apply(s, m)
	if g.CS != nil {
		sw := float64(g.St.score(s) - before[s])
		for q := 0; q < g.St.N; q++ {
			if q != s {
				sw -= float64(g.St.score(q)-before[q]) / float64(g.St.N-1)
			}
		}
		g.CS.Swing[cardIdx(v)] += sw
	}
}

// score: total progress of a seat's four pawns (0..260).
func (st *State) score(s int) int {
	t := 0
	for i := 0; i < 4; i++ {
		t += progress(st.Col[s], int(st.Loc[s][i]))
	}
	return t
}

// adult variation: choose the best card in hand; if none can move, discard one and draw.
func (g *Game) playFromHand(s int) int8 {
	h := g.hands[s]
	bestK, bestV, found := -1, -1e18, false
	var bestM Move
	for k, v := range h {
		ms := g.St.legal(s, v, g.R, g.buf)
		g.buf = ms
		if len(ms) == 0 {
			continue
		}
		m, ok := g.Pols[s].Choose(g, s, v, ms)
		if !ok {
			continue
		}
		cp := g.St
		cp.apply(s, m)
		val := g.Pols[s].Value(&cp, s) + g.Pols[s].keepValue(h, k)
		if !found || val > bestV {
			bestK, bestV, bestM, found = k, val, m, true
		}
	}
	var v int8
	if !found {
		k := g.Pols[s].dumpCard(h)
		v = h[k]
		h[k] = g.draw()
		return v
	}
	v = h[bestK]
	g.St.apply(s, bestM)
	h[bestK] = g.draw()
	return v
}
