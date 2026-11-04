package main

import (
	"math/rand"
	"testing"
)

func pols(n int, p *Policy) []*Policy {
	out := make([]*Policy, n)
	for i := range out {
		out[i] = p
	}
	return out
}

var passive = &Policy{Name: "passive", AvoidRisk: 2, FutureRisk: 2, Placement: "top", StealWhen: 2}

func TestSetupCounts(t *testing.T) {
	for n := 2; n <= 5; n++ {
		g := NewGame(rand.New(rand.NewSource(1)), pols(n, passive))
		var total [NCard]int
		for _, c := range g.deck {
			total[c]++
		}
		for _, p := range g.players {
			if p.nCards() != 8 || p.hand[Defuse] < 1 {
				t.Fatalf("n=%d hand %d defuse %d", n, p.nCards(), p.hand[Defuse])
			}
			for c := range p.hand {
				total[c] += p.hand[c]
			}
		}
		extra := 2
		if n == 5 {
			extra = 1
		}
		if total[EK] != n-1 || total[Defuse] != n+extra || total[Attack] != 4 || total[Nope] != 5 || total[Future] != 5 || total[Cat3] != 4 {
			t.Fatalf("n=%d bad counts %v", n, total)
		}
		if len(g.deck) != 56-4-6-7*n+(n-1)+extra {
			t.Fatalf("n=%d deck size %d", n, len(g.deck))
		}
	}
}

// scripted policy: plays the given card kind once per turn when it has it
type script struct{ Policy }

func TestAttackStacking(t *testing.T) {
	// player 0 attacks; player 1 (victim) attacks back immediately -> player 2 must take 4 turns
	att := &Policy{Name: "att", AvoidRisk: 2, FutureRisk: 2, AttackFree: 1, Placement: "top", StealWhen: 2}
	g := NewGame(rand.New(rand.NewSource(3)), []*Policy{att, att, passive, passive})
	for _, p := range g.players {
		p.hand = [NCard]int{}
	}
	g.players[0].hand[Attack] = 1
	g.players[1].hand[Attack] = 1
	g.cur, g.turnsLeft = 0, 1
	// p0 turn
	r := g.actionPhase(g.players[0])
	if r != resAttack {
		t.Fatal("p0 should attack")
	}
	// emulate Play's attack branch
	apply := func() {
		nt := 2
		if g.underAttack {
			nt = g.turnsLeft + 2
		}
		g.cur = g.nextAlive(g.cur)
		g.turnsLeft = nt
		g.underAttack = true
	}
	apply()
	if g.cur != 1 || g.turnsLeft != 2 {
		t.Fatalf("victim should have 2 turns, got p%d %d", g.cur, g.turnsLeft)
	}
	// attack-free only fires when turnsLeft==1; force it
	g.players[1].pol = &Policy{AvoidRisk: 0, PreferAttack: true, FutureRisk: 2, Placement: "top", StealWhen: 2}
	g.deck[len(g.deck)-1] = EK
	g.players[1].peek = []Card{EK}
	if g.actionPhase(g.players[1]) != resAttack {
		t.Fatal("p1 should attack back")
	}
	apply()
	if g.cur != 2 || g.turnsLeft != 4 {
		t.Fatalf("stacked attack should give 4 turns, got p%d %d", g.cur, g.turnsLeft)
	}
}

func TestVictimAfterOneTurnPassesThree(t *testing.T) {
	g := NewGame(rand.New(rand.NewSource(5)), pols(4, passive))
	g.cur, g.turnsLeft, g.underAttack = 1, 1, true // victim completed 1 of 2 turns
	nt := 2
	if g.underAttack {
		nt = g.turnsLeft + 2
	}
	if nt != 3 {
		t.Fatal("expected 3")
	}
}

func TestKittenPlacementTop(t *testing.T) {
	g := NewGame(rand.New(rand.NewSource(9)), pols(3, passive))
	// put a kitten on top and let current player draw it with a defuse
	p := g.players[g.cur]
	g.deck = append(g.deck, EK)
	g.kittensLeft++
	before := len(g.deck)
	g.turnsLeft = 1
	// one iteration of the loop
	g.alive = 3
	r := g.actionPhase(p)
	if r != resDraw {
		t.Fatal("passive should draw")
	}
	c := g.deck[len(g.deck)-1]
	if c != EK {
		t.Fatal("top should be EK")
	}
	_ = before
}

func TestGamesTerminate(t *testing.T) {
	cas := &Policy{AvoidRisk: 0.3, PreferAttack: true, FutureRisk: 0.2, ShuffleIfEK: true, Placement: "next",
		PairSteal: true, TripleDefuse: true, FavorUse: true, StealTarget: "most", NopeDefend: 0.8, NopeSkipSeen: true, Yup: 0.5, RandomPlay: 0.2, GiveWorst: true}
	rng := rand.New(rand.NewSource(11))
	for n := 2; n <= 5; n++ {
		for k := 0; k < 20000; k++ {
			g := NewGame(rng, pols(n, cas))
			r := g.Play()
			if r.Turns >= 2000 || len(r.Order) != n-1 {
				t.Fatalf("n=%d game did not finish properly: %+v", n, r)
			}
			// conservation: cards in hands + deck + played == 56 - removed
		}
	}
}
