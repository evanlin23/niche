package main

import (
	"math/rand"
	"testing"
)

var normal = &Policy{Name: "normal", ColorChoice: "most", Challenge: "p30", JumpProb: 0.5, StackProb: 0.8, PlayDrawn: true}

func pols(n int) []*Policy {
	p := make([]*Policy, n)
	for i := range p {
		p[i] = normal
	}
	return p
}

func TestDeck112(t *testing.T) {
	d := newDeck(&Rules{})
	if len(d) != 112 {
		t.Fatalf("deck %d", len(d))
	}
	var wild, d4, d2 int
	for _, c := range d {
		if c.isWild() {
			wild++
		}
		if c.K == WildD4 {
			d4++
		}
		if c.K == DrawTwo {
			d2++
		}
	}
	if wild != 12 || d4 != 4 || d2 != 8 {
		t.Fatalf("wild %d d4 %d d2 %d", wild, d4, d2)
	}
	if len(newDeck(&Rules{NoShuffle: true, NoCustom: true})) != 108 {
		t.Fatal("classic deck should be 108")
	}
}

func TestDealAndConservation(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	for _, R := range []Rules{{}, {Stack: true}, {SevenZero: true, JumpIn: true}, {DrawUntil: true, Forced: true}, {FreeD4: true, StackMix: true, Stack: true}} {
		for k := 0; k < 3000; k++ {
			g := NewGame(rng, &R, pols(4), 0)
			r := g.Play()
			total := len(g.deck) + len(g.discard)
			for _, h := range g.hands {
				total += len(h)
			}
			if total != 112 && total < 112 {
				t.Fatalf("cards lost: %d (rules %+v)", total, R)
			}
			if r.Winner < 0 {
				t.Fatalf("round didn't finish (rules %+v)", R)
			}
		}
	}
}

func TestNoStackOfficial(t *testing.T) {
	rng := rand.New(rand.NewSource(2))
	g := NewGame(rng, &Rules{}, pols(3), 0)
	g.hands[0] = []Card{{0, DrawTwo}, {0, 5}}
	g.hands[1] = []Card{{1, DrawTwo}, {1, 3}}
	g.cur = 0
	g.color = 0
	g.discard = append(g.discard, Card{0, 4})
	before := len(g.hands[1])
	g.play(0, 0)
	if len(g.hands[1]) != before+2 || g.cur != 2 {
		t.Fatalf("official: victim draws 2 and is skipped; got hand %d cur %d", len(g.hands[1]), g.cur)
	}
}

func TestIllegalD4Challenge(t *testing.T) {
	rng := rand.New(rand.NewSource(3))
	always := &Policy{Challenge: "always", ColorChoice: "most", PlayDrawn: true}
	g := NewGame(rng, &Rules{}, []*Policy{normal, always, normal}, 0)
	g.color = 0
	g.discard = append(g.discard, Card{0, 4})
	g.hands[0] = []Card{{WildCol, WildD4}, {0, 7}, {2, 2}} // has the colour -> illegal
	g.cur = 0
	g.play(0, 0)
	if len(g.hands[0]) != 2+4 {
		t.Fatalf("guilty player should draw 4, hand %d", len(g.hands[0]))
	}
}
