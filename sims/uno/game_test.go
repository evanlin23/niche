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
			if total != 112 {
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

// ---- rules from the GDJ85 sheet + each house rule (added in the episode audit)

func fresh(t *testing.T, R Rules, n int) *Game {
	t.Helper()
	g := NewGame(rand.New(rand.NewSource(7)), &R, pols(n), 0)
	g.cur, g.dir, g.pending = 0, 1, 0
	g.color = 0
	g.discard = append(g.discard, Card{0, 4})
	return g
}

func TestScoring(t *testing.T) {
	want := map[Card]int{{0, 7}: 7, {1, Skip}: 20, {2, Reverse}: 20, {3, DrawTwo}: 20, {WildCol, Wild}: 50,
		{WildCol, WildD4}: 50, {WildCol, Shuffle}: 40, {WildCol, Custom}: 40}
	for c, p := range want {
		if c.points() != p {
			t.Fatalf("%+v scores %d, sheet says %d", c, c.points(), p)
		}
	}
}

func TestStartingCards(t *testing.T) {
	// dealer 0, 4 players: Skip -> seat 2 starts; Reverse -> dealer starts going right; Draw Two -> seat 1 draws 2, seat 2 starts
	for k := 0; k < 4000; k++ {
		rng := rand.New(rand.NewSource(int64(k)))
		g := NewGame(rng, &Rules{}, pols(4), 0)
		top := g.discard[0]
		switch {
		case top.K == WildD4:
			t.Fatal("Wild Draw 4 must go back into the deck")
		case top.K == Skip && g.cur != 2:
			t.Fatalf("Skip start: cur %d", g.cur)
		case top.K == Reverse && (g.cur != 0 || g.dir != -1):
			t.Fatalf("Reverse start: cur %d dir %d", g.cur, g.dir)
		case top.K == DrawTwo && (g.cur != 2 || len(g.hands[1]) != 9):
			t.Fatalf("Draw Two start: cur %d hand1 %d", g.cur, len(g.hands[1]))
		case top.isWild() && (g.cur != 1 || len(g.hands[1]) != 7):
			t.Fatalf("Wild start: seat 1 picks the colour, no shuffle: cur %d hand %d", g.cur, len(g.hands[1]))
		case top.K <= 9 && g.cur != 1:
			t.Fatalf("number start: cur %d", g.cur)
		}
	}
}

func TestTwoPlayerReverseActsLikeSkip(t *testing.T) {
	g := fresh(t, Rules{}, 2)
	g.hands[0] = []Card{{0, Reverse}, {0, 5}}
	g.play(0, 0)
	if g.cur != 0 {
		t.Fatalf("2 players: Reverse should give the same player another turn, cur %d", g.cur)
	}
}

func TestStackingAddsUp(t *testing.T) {
	g := fresh(t, Rules{Stack: true}, 3)
	always := &Policy{ColorChoice: "most", StackProb: 1, PlayDrawn: true}
	g.pols = []*Policy{always, always, always}
	g.hands[0] = []Card{{0, DrawTwo}, {0, 5}}
	g.hands[1] = []Card{{1, DrawTwo}, {1, 3}}
	g.hands[2] = []Card{{2, 1}, {2, 2}}
	g.play(0, 0)
	if g.pending != 2 || g.cur != 1 {
		t.Fatalf("pending %d cur %d", g.pending, g.cur)
	}
	g.turns = 0
	// seat 1 stacks, seat 2 can't and takes 4, then seat 0 plays
	p := g.cur
	idx := 0
	g.play(p, idx)
	if g.pending != 4 || g.cur != 2 {
		t.Fatalf("after stack: pending %d cur %d", g.pending, g.cur)
	}
	before := len(g.hands[2])
	g.give(2, g.pending)
	if len(g.hands[2]) != before+4 {
		t.Fatal("victim should take the whole stack")
	}
}

func TestDrawUntilPlayable(t *testing.T) {
	for k := 0; k < 300; k++ {
		g := NewGame(rand.New(rand.NewSource(int64(k))), &Rules{DrawUntil: true}, pols(3), 0)
		g.cur, g.dir, g.pending, g.color = 0, 1, 0, 0
		g.discard = append(g.discard, Card{0, 4})
		g.hands[0] = []Card{{1, 9}} // nothing playable
		disc := len(g.discard)
		// run exactly one turn
		g.turns = 4999
		g.Play()
		if len(g.discard) != disc+1 && g.canDraw() {
			t.Fatalf("draw-until: player should keep drawing and then play (discard %d -> %d)", disc, len(g.discard))
		}
	}
}

func TestOfficialDrawOne(t *testing.T) {
	g := fresh(t, Rules{}, 3)
	g.hands[0] = []Card{{1, 9}}
	g.turns = 4999
	g.Play()
	if g.drawn[0] != 1 {
		t.Fatalf("official: draw exactly one card, drew %d", g.drawn[0])
	}
}

func TestSevenZero(t *testing.T) {
	g := fresh(t, Rules{SevenZero: true}, 3)
	g.hands[0] = []Card{{0, 7}, {0, 1}, {0, 2}}
	g.hands[1] = []Card{{1, 1}}
	g.hands[2] = []Card{{2, 1}, {2, 2}, {2, 3}, {2, 4}}
	g.play(0, 0)
	if len(g.hands[0]) != 1 || len(g.hands[1]) != 2 {
		t.Fatalf("7 should swap with the smallest hand: %d %d", len(g.hands[0]), len(g.hands[1]))
	}
	g = fresh(t, Rules{SevenZero: true}, 3)
	g.hands[0] = []Card{{0, 0}, {0, 1}}
	g.hands[1] = []Card{{1, 1}, {1, 2}, {1, 3}}
	g.hands[2] = []Card{{2, 1}, {2, 2}, {2, 3}, {2, 4}}
	g.play(0, 0)
	if len(g.hands[1]) != 1 || len(g.hands[2]) != 3 || len(g.hands[0]) != 4 {
		t.Fatalf("0 should pass every hand along the direction of play: %d %d %d", len(g.hands[0]), len(g.hands[1]), len(g.hands[2]))
	}
}

func TestJumpIn(t *testing.T) {
	g := fresh(t, Rules{JumpIn: true}, 3)
	eager := &Policy{ColorChoice: "most", JumpProb: 1, PlayDrawn: true}
	g.pols = []*Policy{eager, eager, eager}
	g.hands[0] = []Card{{0, 6}, {0, 1}}
	g.hands[2] = []Card{{0, 6}, {3, 3}}
	g.play(0, 0)
	q, _ := g.jumpIn()
	if q != 2 || len(g.hands[2]) != 1 || g.cur != 0 {
		t.Fatalf("seat 2 holds the identical card and jumps in; play continues from them: q %d hand %d cur %d", q, len(g.hands[2]), g.cur)
	}
}

func TestDrawRunsDry(t *testing.T) {
	g := fresh(t, Rules{}, 2)
	g.deck = nil
	g.discard = []Card{{0, 4}}
	if g.give(1, 2) != 0 || g.dry != 1 {
		t.Fatal("with no cards anywhere, nothing can be drawn")
	}
}

func TestMultiPlaySameNumber(t *testing.T) {
	g := fresh(t, Rules{MultiPlay: true}, 3)
	g.hands[0] = []Card{{0, 2}, {1, 2}, {3, 2}, {2, 9}}
	g.play(0, 0)
	if len(g.hands[0]) != 1 || g.hands[0][0] != (Card{2, 9}) {
		t.Fatalf("all three 2s should go down together, hand %v", g.hands[0])
	}
	if g.top().K != 2 || g.color != g.top().C {
		t.Fatal("the last card played sets the colour")
	}
	g = fresh(t, Rules{MultiPlay: true}, 3)
	g.pols[0] = &Policy{ColorChoice: "most", PlayDrawn: true, Multi: "one"}
	g.hands[0] = []Card{{0, 2}, {1, 2}, {2, 9}}
	g.play(0, 0)
	if len(g.hands[0]) != 2 {
		t.Fatal("multi: one plays a single card")
	}
	g = fresh(t, Rules{}, 3)
	g.hands[0] = []Card{{0, 2}, {1, 2}, {2, 9}}
	g.play(0, 0)
	if len(g.hands[0]) != 2 {
		t.Fatal("official: one card per turn")
	}
}

func TestNoActionOut(t *testing.T) {
	g := fresh(t, Rules{NoActOut: true}, 3)
	g.hands[0] = []Card{{0, Skip}}
	if g.choose(0) != -1 {
		t.Fatal("can't go out on a Skip under the house rule")
	}
	g.hands[0] = []Card{{0, 3}}
	if g.choose(0) != 0 {
		t.Fatal("a number card is fine")
	}
	g = fresh(t, Rules{}, 3)
	g.hands[0] = []Card{{0, Skip}}
	if g.choose(0) != 0 {
		t.Fatal("official: going out on a Skip is fine")
	}
}

func TestUnoCall(t *testing.T) {
	forget := &Policy{ColorChoice: "most", PlayDrawn: true, Forget: 1}
	catcher := &Policy{ColorChoice: "most", PlayDrawn: true, Catch: 1}
	g := fresh(t, Rules{UnoCall: true}, 3)
	g.pols = []*Policy{forget, catcher, catcher}
	g.hands[0] = []Card{{0, 3}, {0, 5}}
	g.play(0, 0)
	if len(g.hands[0]) != 3 {
		t.Fatalf("forgot UNO and caught: 1 + 2 penalty cards, got %d", len(g.hands[0]))
	}
	g = fresh(t, Rules{UnoCall: true, UnoPen: 4}, 3)
	g.pols = []*Policy{forget, catcher, catcher}
	g.hands[0] = []Card{{0, 3}, {0, 5}}
	g.play(0, 0)
	if len(g.hands[0]) != 5 {
		t.Fatalf("house penalty 4, got %d", len(g.hands[0]))
	}
	g = fresh(t, Rules{UnoCall: true}, 3)
	g.pols = []*Policy{forget, normal, normal}
	g.hands[0] = []Card{{0, 3}, {0, 5}}
	g.play(0, 0)
	if len(g.hands[0]) != 1 {
		t.Fatal("nobody catches: no penalty")
	}
}
