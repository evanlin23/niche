package main

import (
	"math/bits"
	"math/rand"
)

type Rules struct {
	NoLayoffOnGin bool `json:"no_layoff_on_gin"` // Pagat/house rule: no laying off against Gin (Bicycle allows it)
	Target        int  `json:"target"`           // game target (100)
	KnockMax      int  `json:"knock_max"`        // most deadwood you may knock with (10)
	UndercutBonus int  `json:"undercut_bonus"`   // 10 (Bicycle); Pagat lists 25 as a common variant
	GinBonus      int  `json:"gin_bonus"`        // 20 (Bicycle); 25 is a common variant
}

type Player struct {
	H      uint64
	Pol    *Policy
	Picked uint64 // cards this player took from the discard pile this hand (public)
	Thrown uint64 // cards this player discarded this hand (public)
}

type HandResult struct {
	Winner   int // -1 void hand
	Points   int
	Gin      bool
	Undercut bool
	Knocker  int
	Turns    int
	KnockDW  int
}

type Game struct {
	R    *Rules
	rng  *rand.Rand
	P    [2]Player
	deck []int8
	disc []int8
}

func (g *Game) knockMax() int {
	if g.R.KnockMax > 0 {
		return g.R.KnockMax
	}
	return 10
}

func (g *Game) pop() int {
	c := g.deck[len(g.deck)-1]
	g.deck = g.deck[:len(g.deck)-1]
	return int(c)
}

func (g *Game) top() int { return int(g.disc[len(g.disc)-1]) }

// PlayHand deals and plays one hand. The dealer's opponent plays first.
func (g *Game) PlayHand(dealer int) HandResult {
	if g.deck == nil {
		g.deck = make([]int8, 52)
		g.disc = make([]int8, 0, 52)
	}
	g.deck = g.deck[:52]
	for i := range g.deck {
		g.deck[i] = int8(i)
	}
	g.rng.Shuffle(52, func(i, j int) { g.deck[i], g.deck[j] = g.deck[j], g.deck[i] })
	g.disc = g.disc[:0]
	for s := 0; s < 2; s++ {
		g.P[s].H, g.P[s].Picked, g.P[s].Thrown = 0, 0, 0
	}
	for k := 0; k < 10; k++ { // dealt one at a time, non-dealer first
		g.P[1-dealer].H |= 1 << g.pop()
		g.P[dealer].H |= 1 << g.pop()
	}
	g.disc = append(g.disc, int8(g.pop())) // the upcard
	nd := 1 - dealer
	turns := 0
	var cur int
	// the upcard: the non-dealer may take it, then the dealer; if both pass, the non-dealer draws from the stock
	switch {
	case g.P[nd].Pol.WantDiscard(g, nd, g.top()):
		turns++
		if r, done := g.turn(nd, true, false); done {
			r.Turns = turns
			return r
		}
		cur = dealer
	case g.P[dealer].Pol.WantDiscard(g, dealer, g.top()):
		turns++
		if r, done := g.turn(dealer, true, false); done {
			r.Turns = turns
			return r
		}
		cur = nd
	default:
		turns++
		if r, done := g.turn(nd, false, true); done {
			r.Turns = turns
			return r
		}
		cur = dealer
	}
	for {
		if len(g.deck) <= 2 { // stock down to two cards and nobody knocked: the hand is void (Pagat; Bicycle is silent)
			return HandResult{Winner: -1, Turns: turns}
		}
		turns++
		if r, done := g.turn(cur, false, false); done {
			r.Turns = turns
			return r
		}
		cur = 1 - cur
	}
}

// turn: draw (forced take / forced stock / bot's choice), discard, maybe knock.
func (g *Game) turn(s int, forceTake, forceStock bool) (HandResult, bool) {
	p := &g.P[s]
	taken := -1
	if forceTake || (!forceStock && p.Pol.WantDiscard(g, s, g.top())) {
		taken = g.top()
		g.disc = g.disc[:len(g.disc)-1]
		p.H |= 1 << taken
		p.Picked |= 1 << taken
	} else {
		p.H |= 1 << g.pop()
	}
	c, knock := p.Pol.Discard(g, s, taken)
	p.H &^= 1 << c
	p.Thrown |= 1 << c
	g.disc = append(g.disc, int8(c))
	if knock {
		return g.showdown(s), true
	}
	return HandResult{}, false
}

// showdown: knocker s shows melds; the opponent shows theirs and lays off deadwood on the knocker's melds.
func (g *Game) showdown(s int) HandResult {
	o := 1 - s
	kmelds, kdead := Melds(g.P[s].H)
	kdw := handValue(kdead)
	gin := kdw == 0
	odw := Deadwood(g.P[o].H)
	if !gin || !g.R.NoLayoffOnGin {
		odw = layoffDeadwood(g.P[o].H, kmelds)
	}
	gb, ub := 20, 10
	if g.R.GinBonus > 0 {
		gb = g.R.GinBonus
	}
	if g.R.UndercutBonus > 0 {
		ub = g.R.UndercutBonus
	}
	switch {
	case gin:
		return HandResult{Winner: s, Points: gb + odw, Gin: true, Knocker: s, KnockDW: 0}
	case odw <= kdw: // undercut (a tie goes to the defender)
		return HandResult{Winner: o, Points: ub + kdw - odw, Undercut: true, Knocker: s, KnockDW: kdw}
	default:
		return HandResult{Winner: s, Points: odw - kdw, Knocker: s, KnockDW: kdw}
	}
}

// layoffDeadwood: the defender arranges their own melds, then lays off deadwood cards on the knocker's melds
// (extending runs at either end, or a fourth card on a set), repeatedly. Also tries each of the defender's best
// arrangements' leftovers only (keeps it simple: own melds first, as most players do).
func layoffDeadwood(h uint64, kmelds []uint64) int {
	_, dead := Melds(h)
	ms := append([]uint64(nil), kmelds...)
	for changed := true; changed; {
		changed = false
		for x := dead; x != 0; x &= x - 1 {
			c := bits.TrailingZeros64(x)
			for i, m := range ms {
				if fits(c, m) {
					ms[i] |= 1 << c
					dead &^= 1 << c
					changed = true
					break
				}
			}
		}
	}
	return handValue(dead)
}

// fits: can card c be added to meld m?
func fits(c int, m uint64) bool {
	first := bits.TrailingZeros64(m)
	if bits.OnesCount64(m) >= 2 && rankOf(first) == rankOf(bits.TrailingZeros64(m&(m-1))) { // a set
		return rankOf(c) == rankOf(first) && m&(1<<c) == 0
	}
	// a run: same suit, one past either end
	if suitOf(c) != suitOf(first) {
		return false
	}
	lo := rankOf(first)
	hi := rankOf(63 - bits.LeadingZeros64(m))
	r := rankOf(c)
	return r == lo-1 || r == hi+1
}

// PlayGame: hands until someone reaches the target (100). Returns the game winner and the hands played.
// The winner of a hand deals the next one (Bicycle); a void hand is redealt by the same dealer.
func (g *Game) PlayGame(firstDealer int, st *Stats) (int, int) {
	target := 100
	if g.R.Target > 0 {
		target = g.R.Target
	}
	score := [2]int{}
	dealer := firstDealer
	hands := 0
	for k := 0; k < 200; k++ {
		r := g.PlayHand(dealer)
		hands++
		if st != nil {
			st.add(r, g)
		}
		if r.Winner < 0 {
			continue
		}
		score[r.Winner] += r.Points
		dealer = r.Winner
		if score[r.Winner] >= target {
			return r.Winner, hands
		}
	}
	if score[0] >= score[1] {
		return 0, hands
	}
	return 1, hands
}

type Stats struct {
	Hands, Void, Gins, Undercuts, Knocks int
	KnockDW                              int
	Turns                                int
	Seat                                 [2]int // hand wins by seat role? (unused)
}

func (st *Stats) add(r HandResult, g *Game) {
	st.Hands++
	st.Turns += r.Turns
	if r.Winner < 0 {
		st.Void++
		return
	}
	if r.Gin {
		st.Gins++
	} else {
		st.Knocks++
		st.KnockDW += r.KnockDW
	}
	if r.Undercut {
		st.Undercuts++
	}
}
