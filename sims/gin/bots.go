package main

import "math/bits"

// Policy: what a bot does with its own hand, the discard pile, and what it has seen the opponent pick up
// and throw away. It never sees the opponent's hand or the stock.
type Policy struct {
	Name      string `json:"name"`
	Knock     int    `json:"knock"`      // knock as soon as deadwood <= this (normal 10; 0 = Gin only)
	KnockLate int    `json:"knock_late"` // once the stock is down to LateStock cards, knock at <= this instead
	LateStock int    `json:"late_stock"`
	Take      string `json:"take"` // "meld" (normal): take the discard only if it goes into a meld; "lower": if it lowers deadwood; "never"
	Tie       string `json:"tie"`  // "keep" (normal): among equal discards throw the loosest card; "high": the highest card
	Watch     bool   `json:"watch"`
	Random    bool   `json:"random"`
}

// best discard for hand h (11 cards) excluding card `not`: lowest deadwood after the discard, then tie-break.
func (b *Policy) bestDiscard(g *Game, s int, h uint64, not int) (int, int) {
	bestC, bestDW, bestK := -1, 1<<30, 1<<30
	opp := &g.P[1-s]
	for x := h; x != 0; x &= x - 1 {
		c := bits.TrailingZeros64(x)
		if c == not {
			continue
		}
		dw := Deadwood(h &^ (1 << c))
		if dw > bestDW {
			continue
		}
		k := 0
		if b.Tie == "high" {
			k = -value(c) * 100
		} else {
			k = potential(h, c)*100 - value(c)
		}
		if b.Watch {
			k += 1000 * danger(c, opp)
		}
		if dw < bestDW || (dw == bestDW && k < bestK) {
			bestC, bestDW, bestK = c, dw, k
		}
	}
	return bestC, bestDW
}

// potential: how many cards in hand this card could combine with (same rank, or same suit within 2).
func potential(h uint64, c int) int {
	r, s := uint(rankOf(c)), uint(suitOf(c))
	rk := (h>>r)&1 + (h>>(13+r))&1 + (h>>(26+r))&1 + (h>>(39+r))&1 - 1
	sm := (h >> (13 * s)) & 0x1FFF
	near := sm & (0x1F << r >> 2) &^ (1 << r) // ranks r-2..r+2 of the same suit, minus the card itself
	return int(rk) + bits.OnesCount64(near)
}

// danger: would this card help the opponent? (they picked up a card of this rank, or a same-suit neighbour)
func danger(c int, opp *Player) int {
	r, s := rankOf(c), suitOf(c)
	d := 0
	for x := opp.Picked; x != 0; x &= x - 1 {
		q := bits.TrailingZeros64(x)
		if rankOf(q) == r || (suitOf(q) == s && abs(rankOf(q)-r) <= 2) {
			d++
		}
	}
	// a rank they threw away themselves is safer
	for x := opp.Thrown; x != 0; x &= x - 1 {
		if rankOf(bits.TrailingZeros64(x)) == r {
			d--
			break
		}
	}
	if d < 0 {
		d = 0
	}
	return d
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func (b *Policy) WantDiscard(g *Game, s int, top int) bool {
	if b.Take == "never" {
		return false
	}
	h := g.P[s].H
	if b.Take != "lower" && !couldMeld(h, top) {
		return false // no card of its rank twice, no same-suit neighbours: it can't go into a meld
	}
	cur := Deadwood(h)
	_, after := b.bestDiscard(g, s, h|1<<top, top)
	if b.Take == "lower" {
		return after < cur
	}
	// "meld": the card must end up in a meld of the best arrangement after the discard
	if after >= cur {
		return false
	}
	c, _ := b.bestDiscard(g, s, h|1<<top, top)
	h2 := (h | 1<<top) &^ (1 << c)
	return Deadwood(h2) < Deadwood(h2&^(1<<top))+value(top)
}

// Discard picks the card to throw and whether to knock with what's left.
func (b *Policy) Discard(g *Game, s int, taken int) (int, bool) {
	h := g.P[s].H
	var c, dw int
	if b.Random {
		for {
			c = bits.TrailingZeros64(h)
			k := g.rng.Intn(bits.OnesCount64(h))
			x := h
			for i := 0; i < k; i++ {
				x &= x - 1
			}
			c = bits.TrailingZeros64(x)
			if c != taken {
				break
			}
		}
		dw = Deadwood(h &^ (1 << c))
	} else {
		c, dw = b.bestDiscard(g, s, h, taken)
	}
	limit := b.Knock
	if b.KnockLate > 0 && b.LateStock > 0 && len(g.deck) <= b.LateStock {
		limit = b.KnockLate
	}
	if limit > g.knockMax() {
		limit = g.knockMax()
	}
	return c, dw <= limit
}

// couldMeld: is there any meld the card could join with the cards in hand (2 of its rank, or 2 suit neighbours
// making a run of 3 with it)?
func couldMeld(h uint64, c int) bool {
	r, s := rankOf(c), suitOf(c)
	same := 0
	for t := 0; t < 4; t++ {
		if t != s && h&(1<<(t*13+r)) != 0 {
			same++
		}
	}
	if same >= 2 {
		return true
	}
	sm := int(h>>(13*s)) & 0x1FFF
	has := func(q int) bool { return q >= 0 && q < 13 && sm&(1<<q) != 0 }
	return (has(r-1) && has(r-2)) || (has(r-1) && has(r+1)) || (has(r+1) && has(r+2))
}
