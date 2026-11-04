package main

import (
	"math/rand"
	"testing"
)

func hand(cards ...uint8) *Hand {
	var h Hand
	for _, c := range cards {
		h.Add(c)
	}
	return &h
}

// N(number, colour) card code
func N(n, c int) uint8 { return uint8((n-1)*4 + c) }

func TestDeck108(t *testing.T) {
	d := newDeck()
	if len(d) != 108 {
		t.Fatalf("deck has %d cards, want 108", len(d))
	}
	var byNum [13]int
	var byCode [NCodes]int
	wild, skip := 0, 0
	for _, c := range d {
		byCode[c]++
		switch {
		case c == Wild:
			wild++
		case c == Skip:
			skip++
		default:
			byNum[num(c)]++
		}
	}
	if wild != 8 || skip != 4 {
		t.Fatalf("wild %d skip %d", wild, skip)
	}
	for n := 1; n <= 12; n++ {
		if byNum[n] != 8 {
			t.Fatalf("number %d appears %d times, want 8 (2 per colour)", n, byNum[n])
		}
		for c := 0; c < 4; c++ {
			if byCode[N(n, c)] != 2 {
				t.Fatalf("%d of colour %d: %d copies", n, c, byCode[N(n, c)])
			}
		}
	}
}

func TestPoints(t *testing.T) {
	if points(N(1, 0)) != 5 || points(N(9, 3)) != 5 || points(N(10, 1)) != 10 || points(N(12, 2)) != 10 || points(Skip) != 15 || points(Wild) != 25 {
		t.Fatal("scoring: 5 for 1-9, 10 for 10-12, 15 Skip, 25 Wild")
	}
}

func TestDeal(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	for n := 2; n <= 6; n++ {
		pols := make([]*Policy, n)
		for i := range pols {
			pols[i] = &normalPolicy
		}
		var st Stats
		g := NewGame(rng, &Rules{}, pols, 0, &st)
		g.deal()
		for i := range g.P {
			if g.P[i].H.n != 10 {
				t.Fatalf("player %d got %d cards", i, g.P[i].H.n)
			}
		}
		if len(g.disc) != 1 || len(g.draw) != 108-10*n-1 {
			t.Fatalf("%d players: discard %d draw %d", n, len(g.disc), len(g.draw))
		}
	}
}

func TestSheetExamples(t *testing.T) {
	// Phase 1: three 7s and three 10s; or three 10s and three more 10s
	if !Complete(1, hand(N(7, 0), N(7, 1), N(7, 2), N(10, 0), N(10, 1), N(10, 3))) {
		t.Fatal("phase 1: 777 + 10 10 10")
	}
	if !Complete(1, hand(N(10, 0), N(10, 1), N(10, 2), N(10, 3), N(10, 0), N(10, 1))) {
		t.Fatal("phase 1: two sets of the same number are allowed")
	}
	if Complete(1, hand(N(7, 0), N(7, 1), N(7, 2), N(10, 0), N(10, 1), N(11, 3))) {
		t.Fatal("phase 1 false positive")
	}
	// Phase 2 needs a run of 4 like 3,4,5,6; a Wild can be the 5
	if !Complete(2, hand(N(9, 0), N(9, 1), N(9, 2), N(3, 0), N(4, 1), Wild, N(6, 3))) {
		t.Fatal("phase 2 with a Wild in the run")
	}
	// a card can't be in the set and the run at once: 5,5,5 + 3,4,5,6 needs four 5s
	if Complete(2, hand(N(5, 0), N(5, 1), N(5, 2), N(3, 0), N(4, 1), N(6, 3))) {
		t.Fatal("phase 2 reused a card")
	}
	if !Complete(2, hand(N(5, 0), N(5, 1), N(5, 2), N(5, 3), N(3, 0), N(4, 1), N(6, 3))) {
		t.Fatal("phase 2: 555 + 3456 with four 5s")
	}
	// runs don't wrap around 12 -> 1
	if Complete(4, hand(N(9, 0), N(10, 0), N(11, 0), N(12, 0), N(1, 0), N(2, 0), N(3, 0))) {
		t.Fatal("run wrapped around")
	}
	if !Complete(4, hand(N(6, 0), N(7, 1), N(8, 2), N(9, 3), N(10, 0), N(11, 1), N(12, 2))) {
		t.Fatal("run of 7")
	}
	// Phase 8: six greens and a Wild
	if !Complete(8, hand(N(1, 2), N(4, 2), N(6, 2), N(7, 2), N(9, 2), N(12, 2), Wild)) {
		t.Fatal("phase 8 with a Wild")
	}
	if Complete(8, hand(N(1, 2), N(4, 2), N(6, 2), N(7, 2), N(9, 2), N(12, 1), N(3, 0))) {
		t.Fatal("phase 8 false positive")
	}
	// at least one numbered card: seven Wilds are not a run of 7
	if Complete(4, hand(Wild, Wild, Wild, Wild, Wild, Wild, Wild)) || Complete(1, hand(Wild, Wild, Wild, Wild, Wild, Wild)) {
		t.Fatal("a Phase of only Wilds")
	}
	if !Complete(4, hand(Wild, Wild, Wild, Wild, Wild, Wild, N(2, 0))) {
		t.Fatal("six Wilds and one numbered card make a run of 7")
	}
	// Skips never count
	if Complete(9, hand(N(4, 0), N(4, 1), N(4, 2), N(4, 3), Skip, N(8, 0), N(8, 1))) {
		t.Fatal("a Skip was used in a Phase")
	}
	if !Complete(10, hand(N(4, 0), N(4, 1), N(4, 2), N(4, 3), N(4, 0), N(8, 0), Wild, N(8, 2))) {
		t.Fatal("phase 10: five 4s + 8,W,8")
	}
}

// brute force: try every way to split the cards into the Phase's groups.
func bruteComplete(ph int, cards []uint8) bool {
	d := Phases[ph]
	k := len(cards)
	ngroups := 2
	if d.Kind == KRun || d.Kind == KColor {
		ngroups = 1
	}
	assign := make([]int, k) // 0 = unused, 1 = group A, 2 = group B
	var rec func(i, na, nb int) bool
	rec = func(i, na, nb int) bool {
		if na > d.A || (ngroups == 2 && nb > d.B) {
			return false
		}
		if i == k {
			var ga, gb []uint8
			for j, a := range assign {
				if a == 1 {
					ga = append(ga, cards[j])
				} else if a == 2 {
					gb = append(gb, cards[j])
				}
			}
			nat := 0
			for _, c := range append(append([]uint8{}, ga...), gb...) {
				if isNum(c) {
					nat++
				}
			}
			if nat == 0 {
				return false
			}
			switch d.Kind {
			case KSets:
				return isSet(ga, d.A) && isSet(gb, d.B)
			case KSetRun:
				return isSet(ga, d.A) && isRun(gb, d.B)
			case KRun:
				return isRun(ga, d.A)
			case KColor:
				return isColor(ga, d.A)
			}
		}
		for a := 0; a <= ngroups; a++ {
			assign[i] = a
			na2, nb2 := na, nb
			if a == 1 {
				na2++
			} else if a == 2 {
				nb2++
			}
			if rec(i+1, na2, nb2) {
				return true
			}
		}
		return false
	}
	return rec(0, 0, 0)
}

func isSet(g []uint8, k int) bool {
	if len(g) != k {
		return false
	}
	n := 0
	for _, c := range g {
		if c == Skip {
			return false
		}
		if isNum(c) {
			if n != 0 && num(c) != n {
				return false
			}
			n = num(c)
		}
	}
	return true
}

func isRun(g []uint8, L int) bool {
	if len(g) != L {
		return false
	}
	for s := 1; s+L-1 <= 12; s++ { // some start s where the naturals are distinct and inside s..s+L-1
		var used [13]bool
		ok := true
		for _, c := range g {
			if c == Skip {
				return false
			}
			if isNum(c) {
				n := num(c)
				if n < s || n > s+L-1 || used[n] {
					ok = false
					break
				}
				used[n] = true
			}
		}
		if ok {
			return true
		}
	}
	return false
}

func isColor(g []uint8, k int) bool {
	if len(g) != k {
		return false
	}
	col := -1
	for _, c := range g {
		if c == Skip {
			return false
		}
		if isNum(c) {
			if col >= 0 && color(c) != col {
				return false
			}
			col = color(c)
		}
	}
	return true
}

func TestPhaseDetectorMatchesBruteForce(t *testing.T) {
	rng := rand.New(rand.NewSource(7))
	d := newDeck()
	for ph := 1; ph <= 10; ph++ {
		pos, n := 0, 0
		for trial := 0; trial < 800; trial++ {
			rng.Shuffle(len(d), func(i, j int) { d[i], d[j] = d[j], d[i] })
			k := 9 + rng.Intn(3) // 9-11 cards
			// bias some hands towards completion so both answers get tested
			cards := append([]uint8{}, d[:k]...)
			if trial%2 == 0 {
				cards = biased(rng, ph, k)
			}
			h := hand(cards...)
			want := bruteComplete(ph, cards)
			if got := Complete(ph, h); got != want {
				t.Fatalf("phase %d hand %v: detector %v, brute force %v", ph, cards, got, want)
			}
			if want {
				pos++
				cp := *h
				gs := Arrange(ph, &cp, 0)
				used := 0
				for _, g := range gs {
					used += g.N
				}
				if used != Phases[ph].Size() || cp.n != h.n-used {
					t.Fatalf("phase %d: arranged %d cards, hand %d -> %d", ph, used, h.n, cp.n)
				}
			}
			n++
		}
		if pos < 100 {
			t.Fatalf("phase %d: only %d complete hands tested", ph, pos)
		}
	}
}

// biased: a hand built around the Phase's shape, with noise, so the brute force sees many near-misses.
func biased(rng *rand.Rand, ph, k int) []uint8 {
	d := Phases[ph]
	var out []uint8
	add := func(n int) { out = append(out, N(n, rng.Intn(4))) }
	switch d.Kind {
	case KSets:
		a, b := 1+rng.Intn(12), 1+rng.Intn(12)
		for i := 0; i < d.A-rng.Intn(2); i++ {
			add(a)
		}
		for i := 0; i < d.B-rng.Intn(2); i++ {
			add(b)
		}
	case KSetRun:
		a, s := 1+rng.Intn(12), 1+rng.Intn(12-d.B+1)
		for i := 0; i < d.A-rng.Intn(2); i++ {
			add(a)
		}
		for x := s; x < s+d.B; x++ {
			if rng.Intn(5) > 0 {
				add(x)
			}
		}
	case KRun:
		s := 1 + rng.Intn(12-d.A+1)
		for x := s; x < s+d.A; x++ {
			if rng.Intn(6) > 0 {
				add(x)
			}
		}
	case KColor:
		c := rng.Intn(4)
		for i := 0; i < d.A-rng.Intn(2); i++ {
			out = append(out, N(1+rng.Intn(12), c))
		}
	}
	for len(out) < k {
		r := rng.Intn(108)
		switch {
		case r < 8:
			out = append(out, Wild)
		case r < 12:
			out = append(out, Skip)
		default:
			out = append(out, N(1+rng.Intn(12), rng.Intn(4)))
		}
	}
	return out[:k]
}

func TestHitting(t *testing.T) {
	set := Group{Kind: 0, Num: 4, N: 3}
	if !CanHit(N(4, 2), &set) || !CanHit(Wild, &set) || CanHit(N(5, 0), &set) || CanHit(Skip, &set) {
		t.Fatal("set hits: same number or Wild only")
	}
	run := Group{Kind: 1, Lo: 3, Hi: 6, N: 4}
	if !CanHit(N(2, 0), &run) || !CanHit(N(7, 0), &run) || CanHit(N(8, 0), &run) || CanHit(N(5, 0), &run) {
		t.Fatal("run hits: only the next number at either end")
	}
	Hit(N(7, 1), &run)
	if !CanHit(N(8, 0), &run) || run.Hi != 7 || run.N != 5 {
		t.Fatal("after hitting a 7 the run takes an 8 (sheet example)")
	}
	full := Group{Kind: 1, Lo: 1, Hi: 12, N: 12}
	if CanHit(Wild, &full) {
		t.Fatal("a 1-12 run can't grow")
	}
	col := Group{Kind: 2, Col: 1, N: 7}
	if !CanHit(N(11, 1), &col) || CanHit(N(11, 0), &col) || !CanHit(Wild, &col) {
		t.Fatal("colour hits: same colour or Wild")
	}
}

func newTestGame(n int, seed int64) *Game {
	pols := make([]*Policy, n)
	for i := range pols {
		pols[i] = &normalPolicy
	}
	var st Stats
	return NewGame(rand.New(rand.NewSource(seed)), &Rules{}, pols, n-1, &st)
}

func TestSkipRules(t *testing.T) {
	g := newTestGame(3, 1)
	g.deal()
	g.disc = []uint8{N(3, 0)}
	// player 0 discards a Skip at player 1
	g.P[0].H = *hand(Skip, N(1, 0), N(2, 1), N(5, 2), N(7, 3), N(9, 0), N(11, 1), N(12, 2), N(4, 3), N(6, 0))
	c, target := g.P[0].Pol.Discard(g, 0)
	if c != Skip {
		t.Fatalf("normal bot plays its Skip right away, threw %d", c)
	}
	g.P[0].H.RemoveCode(c)
	g.P[target].Skipped = true
	// the Skip is placed in front of the player, not on the discard pile
	if len(g.disc) != 1 {
		t.Fatal("Skip went on the discard pile")
	}
	// can't Skip someone who already has one in front of them
	var buf [8]int
	ts := g.skipTargets(2, buf[:])
	for _, x := range ts {
		if x == target {
			t.Fatal("targeted a player who already has a Skip")
		}
		if x == 2 {
			t.Fatal("skipped yourself")
		}
	}
	// a Skip can never be taken from the discard pile
	g.disc = append(g.disc, Skip)
	g.draw = append(g.draw, N(1, 3)) // known top of the draw pile
	g.turn(2, 1)
	if len(g.disc) < 2 || g.disc[1] != Skip {
		t.Fatal("the Skip on the discard pile was taken")
	}
}

func TestSkippedPlayerOnlyMovesTheSkip(t *testing.T) {
	g := newTestGame(2, 3)
	g.R = &Rules{}
	g.deal()
	g.P[1].Skipped = true
	h0, h1 := g.P[0].H.n, g.P[1].H.n
	// emulate the turn loop: seat 1 skipped -> Skip card goes to the discard, nothing else
	g.cur = 1
	p := &g.P[1]
	if p.Skipped {
		p.Skipped = false
		g.disc = append(g.disc, Skip)
	}
	if g.P[1].H.n != h1 || g.P[0].H.n != h0 || g.disc[len(g.disc)-1] != Skip {
		t.Fatal("skipped turn changed hands")
	}
}

func TestStartingCards(t *testing.T) {
	// a Skip turned up to start: the first player's first turn is skipped
	skipped := 0
	for seed := int64(0); seed < 3000; seed++ {
		g := newTestGame(3, seed)
		g.deal()
		if g.skipFromStart {
			skipped++
			if g.disc[0] != Skip {
				t.Fatal("skipFromStart without a Skip on the pile")
			}
		}
	}
	if skipped == 0 {
		t.Fatal("never saw a starting Skip")
	}
	// a Wild turned up to start can be taken by the first player
	g := newTestGame(2, 1)
	g.deal()
	g.disc = []uint8{Wild}
	if !g.P[1].Pol.TakeDiscard(g, 1, Wild) {
		t.Fatal("first player should take a starting Wild")
	}
}

func TestGoOutByHittingAllCards(t *testing.T) {
	g := newTestGame(2, 5)
	g.deal()
	g.table = []Group{{Owner: 1, Kind: 0, Num: 9, N: 3}}
	g.P[0].Laid = true
	g.P[0].H = *hand(N(9, 0))
	g.draw = append(g.draw[:0], N(9, 2)) // draws another 9
	g.disc = []uint8{N(2, 0)}
	if !g.turn(0, 1) {
		t.Fatal("hitting the last cards should go out without a discard")
	}
	if g.table[0].N != 5 {
		t.Fatalf("set should have 5 cards, has %d", g.table[0].N)
	}
}

func TestCannotHitBeforeLaying(t *testing.T) {
	g := newTestGame(2, 6)
	g.deal()
	g.table = []Group{{Owner: 1, Kind: 0, Num: 9, N: 3}}
	g.P[0].H = *hand(N(9, 0), N(1, 0), N(2, 0), N(5, 0), N(7, 1), N(11, 2), N(12, 3), N(3, 3), N(6, 2), N(10, 1))
	g.P[0].Phase = 7
	n0 := g.table[0].N
	g.turn(0, 1)
	if g.table[0].N != n0 {
		t.Fatal("hit before laying down a Phase")
	}
}

func TestRoundScoringAndAdvance(t *testing.T) {
	rng := rand.New(rand.NewSource(11))
	for k := 0; k < 300; k++ {
		g := newTestGame(4, int64(k))
		g.rng = rng
		out := g.PlayRound()
		if out < 0 {
			t.Fatal("round never finished")
		}
		for i := range g.P {
			p := &g.P[i]
			if i == out && (p.Score != 0 || !p.Laid || p.H.n != 0) {
				t.Fatal("the player who went out scores 0 and must have laid down")
			}
			if i != out && p.Score != p.H.Points() {
				t.Fatal("others score their hand")
			}
			if p.Laid != (p.Phase == 2) {
				t.Fatal("only players who laid down advance")
			}
		}
	}
}

func TestConservationAndGameEnd(t *testing.T) {
	for _, R := range []Rules{{}, {FixedRounds: true}} {
		for seed := int64(0); seed < 400; seed++ {
			g := newTestGame(2+int(seed%5), seed)
			g.R = &R
			for r := 0; r < 60; r++ {
				g.PlayRound()
				total := len(g.draw) + len(g.disc)
				for i := range g.P {
					total += g.P[i].H.n
					if g.P[i].Skipped {
						total++
					}
				}
				for _, gr := range g.table {
					total += gr.N
				}
				if total != 108 {
					t.Fatalf("cards: %d != 108", total)
				}
				done := false
				for i := range g.P {
					if g.P[i].Phase > 10 {
						done = true
					}
				}
				if done || (R.FixedRounds && g.round >= 10) {
					break
				}
			}
		}
	}
}

func TestWinnerFewestPoints(t *testing.T) {
	g := newTestGame(3, 1)
	g.P[0].Phase, g.P[1].Phase, g.P[2].Phase = 11, 11, 10
	g.P[0].Score, g.P[1].Score, g.P[2].Score = 80, 55, 0
	if w := g.lowest([]int{0, 1}); w != 1 {
		t.Fatal("among players finishing Phase 10, fewest points wins")
	}
	// exact tie -> playoff decides between the tied two only
	g.P[0].Score = 55
	for k := 0; k < 20; k++ {
		if w := g.lowest([]int{0, 1}); w != 0 && w != 1 {
			t.Fatal("playoff winner must be one of the tied players")
		}
	}
}

func TestMirrorQuick(t *testing.T) {
	r := runGames(4, 3000, 9, 4, &Rules{}, &normalPolicy, nil)
	for i, v := range r["seat_win"].([]float64) {
		if v < 0.22 || v > 0.28 {
			t.Fatalf("seat %d wins %.3f with identical bots", i, v)
		}
	}
	if r["unfinished_rounds"].(float64) != 0 {
		t.Fatal("unfinished rounds")
	}
}
