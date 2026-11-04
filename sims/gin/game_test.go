package main

import (
	"math/bits"
	"math/rand"
	"testing"
)

// C(rank 1..13, suit 0..3)
func C(r, s int) int { return s*13 + r - 1 }

func hand(cs ...int) uint64 {
	var h uint64
	for _, c := range cs {
		h |= 1 << c
	}
	return h
}

func TestValues(t *testing.T) {
	if value(C(1, 0)) != 1 || value(C(7, 2)) != 7 || value(C(10, 1)) != 10 || value(C(11, 3)) != 10 || value(C(13, 0)) != 10 {
		t.Fatal("ace 1, pips face value, J/Q/K 10")
	}
}

func TestDeadwoodExamples(t *testing.T) {
	cases := []struct {
		h    uint64
		want int
	}{
		// 7-7-7, 3-4-5 clubs, 9-10-J hearts, plus a king: deadwood 10
		{hand(C(7, 0), C(7, 1), C(7, 2), C(3, 3), C(4, 3), C(5, 3), C(9, 1), C(10, 1), C(11, 1), C(13, 0)), 10},
		// A-2-3 is a run (ace low)
		{hand(C(1, 0), C(2, 0), C(3, 0)), 0},
		// Q-K-A is not
		{hand(C(12, 0), C(13, 0), C(1, 0)), 21},
		// four 5s + 3,4 of clubs: 5-5-5 set and 3-4-5 clubs run, nothing left
		{hand(C(5, 0), C(5, 1), C(5, 2), C(5, 3), C(3, 3), C(4, 3)), 0},
		// a card can't be in two melds: 5-5-5 or 5-6-7 of spades, not both (run is better: 5+5 left)
		{hand(C(5, 0), C(5, 1), C(5, 2), C(6, 0), C(7, 0)), 10},
		// two-card pairs are not melds
		{hand(C(9, 0), C(9, 1), C(4, 2)), 22},
	}
	for i, c := range cases {
		if got := Deadwood(c.h); got != c.want {
			t.Fatalf("case %d: deadwood %d, want %d", i, got, c.want)
		}
	}
}

// brute force: every meld (sets of 3/4, every run of 3+), every set of disjoint melds.
func bruteDeadwood(h uint64) int {
	var ms []uint64
	for r := 0; r < 13; r++ {
		var m uint64
		for s := 0; s < 4; s++ {
			if h&(1<<(s*13+r)) != 0 {
				m |= 1 << (s*13 + r)
			}
		}
		if bits.OnesCount64(m) >= 3 {
			// every subset of size >= 3
			for sub := m; sub != 0; sub = (sub - 1) & m {
				if bits.OnesCount64(sub) >= 3 {
					ms = append(ms, sub)
				}
			}
		}
	}
	for s := 0; s < 4; s++ {
		for a := 0; a < 13; a++ {
			for e := a + 2; e < 13; e++ {
				var m uint64
				ok := true
				for q := a; q <= e; q++ {
					if h&(1<<(s*13+q)) == 0 {
						ok = false
						break
					}
					m |= 1 << (s*13 + q)
				}
				if ok {
					ms = append(ms, m)
				}
			}
		}
	}
	best := 0
	var rec func(i int, used uint64)
	rec = func(i int, used uint64) {
		if v := handValue(used); v > best {
			best = v
		}
		for j := i; j < len(ms); j++ {
			if ms[j]&used == 0 {
				rec(j+1, used|ms[j])
			}
		}
	}
	rec(0, 0)
	return handValue(h) - best
}

func TestDeadwoodBruteForce(t *testing.T) {
	rng := rand.New(rand.NewSource(3))
	for k := 0; k < 30000; k++ {
		n := 10 + k%2
		var h uint64
		if k%3 == 0 { // clustered hands: few ranks/suits so melds are common
			for bits.OnesCount64(h) < n {
				h |= 1 << (rng.Intn(2)*13 + rng.Intn(7))
				h |= 1 << (rng.Intn(4)*13 + rng.Intn(5))
				if bits.OnesCount64(h) > n {
					h &^= 1 << bits.TrailingZeros64(h)
				}
			}
		} else {
			for bits.OnesCount64(h) < n {
				h |= 1 << rng.Intn(52)
			}
		}
		if a, b := Deadwood(h), bruteDeadwood(h); a != b {
			t.Fatalf("hand %x: deadwood %d, brute force %d", h, a, b)
		}
		ms, dead := Melds(h)
		var used uint64
		for _, m := range ms {
			if used&m != 0 {
				t.Fatal("melds overlap")
			}
			used |= m
		}
		if handValue(dead) != Deadwood(h) || used|dead != h {
			t.Fatal("Melds arrangement doesn't match Deadwood")
		}
	}
}

func newGame(seed int64, R *Rules) *Game {
	g := &Game{R: R, rng: rand.New(rand.NewSource(seed))}
	p := parsePolicy("")
	g.P[0].Pol, g.P[1].Pol = p, p
	return g
}

func TestDealAndConservation(t *testing.T) {
	g := newGame(1, &Rules{})
	for k := 0; k < 3000; k++ {
		r := g.PlayHand(k % 2)
		total := len(g.deck) + len(g.disc) + bits.OnesCount64(g.P[0].H) + bits.OnesCount64(g.P[1].H)
		if total != 52 {
			t.Fatalf("cards %d != 52", total)
		}
		if g.P[0].H&g.P[1].H != 0 {
			t.Fatal("a card in both hands")
		}
		if r.Winner >= 0 && r.KnockDW > 10 {
			t.Fatal("knocked with more than 10 deadwood")
		}
		if r.Winner < 0 && len(g.deck) > 2 {
			t.Fatal("void hand with more than 2 cards in the stock")
		}
	}
}

func TestScoring(t *testing.T) {
	g := newGame(2, &Rules{})
	// knocker: three melds + 4 of clubs (4 deadwood); defender: deadwood 2+8+9+... includes a 6 of hearts that lays off
	g.P[0].H = hand(C(7, 0), C(7, 1), C(7, 2), C(3, 3), C(4, 3), C(5, 3), C(9, 1), C(10, 1), C(11, 1), C(1, 0))
	g.P[1].H = hand(C(2, 0), C(2, 1), C(2, 2), C(12, 0), C(12, 1), C(12, 2), C(6, 3), C(8, 0), C(9, 2), C(13, 3))
	r := g.showdown(0)
	// knocker deadwood 1 (the ace); defender lays off the 6 of clubs on 3-4-5 clubs: deadwood 8+9+10 = 27
	if r.Winner != 0 || r.Points != 26 || r.KnockDW != 1 {
		t.Fatalf("knock: %+v", r)
	}
	// undercut: defender's deadwood equal or lower wins 10 + difference
	g.P[0].H = hand(C(7, 0), C(7, 1), C(7, 2), C(3, 3), C(4, 3), C(5, 3), C(9, 1), C(10, 1), C(11, 1), C(8, 0))
	g.P[1].H = hand(C(2, 0), C(2, 1), C(2, 2), C(12, 0), C(12, 1), C(12, 2), C(8, 3), C(9, 3), C(10, 3), C(6, 0))
	r = g.showdown(0)
	if r.Winner != 1 || !r.Undercut || r.Points != 10+8-6 {
		t.Fatalf("undercut: %+v", r)
	}
	// gin: 20 + the defender's deadwood after layoffs (Bicycle). Defender melds 2-2-2 and 8-9-10 of clubs;
	// deadwood K hearts, Q spades, A diamonds, 6 spades = 27; the K of hearts lays off on 9-10-J-Q hearts -> 17
	g.P[0].H = hand(C(7, 0), C(7, 1), C(7, 2), C(3, 3), C(4, 3), C(5, 3), C(9, 1), C(10, 1), C(11, 1), C(12, 1))
	g.P[1].H = hand(C(2, 0), C(2, 1), C(2, 2), C(13, 1), C(12, 0), C(1, 2), C(8, 3), C(9, 3), C(10, 3), C(6, 0))
	r = g.showdown(0)
	if r.Winner != 0 || !r.Gin || r.Points != 20+17 {
		t.Fatalf("gin: %+v", r)
	}
	g.R = &Rules{NoLayoffOnGin: true}
	r = g.showdown(0)
	if r.Points != 20+27 {
		t.Fatalf("gin without layoffs: %+v", r)
	}
}

func TestCannotThrowBackPickup(t *testing.T) {
	g := newGame(4, &Rules{})
	for k := 0; k < 2000; k++ {
		g.PlayHand(k % 2)
	}
	// direct check: Discard never returns the card just taken
	p := parsePolicy("")
	g.P[0].H = hand(C(7, 0), C(7, 1), C(9, 2), C(13, 0), C(12, 1), C(11, 2), C(2, 3), C(4, 0), C(6, 1), C(8, 2), C(13, 3))
	c, _ := p.Discard(g, 0, C(13, 3))
	if c == C(13, 3) {
		t.Fatal("threw back the card just picked up")
	}
}

func TestGameToTarget(t *testing.T) {
	g := newGame(5, &Rules{})
	for k := 0; k < 500; k++ {
		w, hands := g.PlayGame(k%2, nil)
		if w < 0 || w > 1 || hands < 1 {
			t.Fatal("game")
		}
	}
}

func TestMirrorQuick(t *testing.T) {
	r := runGames(4, 5000, 9, &Rules{}, parsePolicy(""), parsePolicy(""))
	if p := r["a_win"].(float64); p < 0.47 || p > 0.53 {
		t.Fatalf("identical bots: %.3f", p)
	}
}
