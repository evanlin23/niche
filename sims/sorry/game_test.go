package main

import (
	"math/rand"
	"testing"
)

func TestDeck(t *testing.T) {
	d := newDeck(&Rules{})
	if len(d) != 45 {
		t.Fatalf("deck %d, want 45", len(d))
	}
	cnt := map[int8]int{}
	for _, c := range d {
		cnt[c]++
	}
	if cnt[1] != 5 || cnt[CSorry] != 4 || cnt[6] != 0 || cnt[9] != 0 {
		t.Fatalf("five 1s, four Sorry!, no 6 or 9: %v", cnt)
	}
	for _, v := range []int8{2, 3, 4, 5, 7, 8, 10, 11, 12} {
		if cnt[v] != 4 {
			t.Fatalf("card %d: %d copies", v, cnt[v])
		}
	}
	if len(newDeck(&Rules{NoExtraOne: true})) != 44 {
		t.Fatal("1958 pack without the optional 1 has 44 cards")
	}
}

func TestGeometry(t *testing.T) {
	for c := 0; c < 4; c++ {
		if progress(c, exitSq(c)) != 1 || progress(c, Start) != 0 || progress(c, HomeSq) != 65 {
			t.Fatal("progress endpoints")
		}
		// 64 forward moves from the Start exit reach Home exactly, via the entry square and 5 safety squares
		l := exitSq(c)
		for k := 1; k <= 64; k++ {
			nl, ok := fwd(c, l, 1)
			if !ok {
				t.Fatalf("colour %d blocked at step %d", c, k)
			}
			l = nl
			if k == 58 && l != entrySq(c) {
				t.Fatalf("step 58 should be the entry square, got %d", l)
			}
			if k > 58 && k < 64 && l != Safe1+(k-59) {
				t.Fatalf("step %d should be safety %d", k, k-58)
			}
		}
		if l != HomeSq {
			t.Fatal("did not reach Home in 64 moves")
		}
		if _, ok := fwd(c, Safe1+4, 2); ok {
			t.Fatal("overshot Home")
		}
	}
	// slides: two per side, lengths 4 and 5
	n4, n5 := 0, 0
	for q := 0; q < Track; q++ {
		if slideOwner[q] >= 0 {
			switch int(slideEnd[q]) - q + 1 {
			case 4:
				n4++
			case 5:
				n5++
			default:
				t.Fatal("slide length")
			}
		}
	}
	if n4 != 4 || n5 != 4 {
		t.Fatal("four short and four long slides")
	}
}

func fresh(n int) *State {
	var st State
	st.init(n)
	return &st
}

func TestStartRules(t *testing.T) {
	st := fresh(4)
	R := &Rules{}
	for _, v := range []int8{3, 4, 5, 7, 8, 10, 11, 12} {
		if len(st.legal(0, v, R, nil)) != 0 {
			t.Fatalf("card %d started a pawn", v)
		}
	}
	if len(st.legal(0, CSorry, R, nil)) != 0 {
		t.Fatal("Sorry! with no opponent on the board")
	}
	ms := st.legal(0, 1, R, nil)
	if len(ms) != 1 || ms[0].Kind != MStart {
		t.Fatal("a 1 starts a pawn")
	}
	st.apply(0, ms[0])
	if st.Loc[0][0] != int16(exitSq(0)) {
		t.Fatal("started pawn goes to the Start exit circle")
	}
	// no two own pawns on the exit circle: a 2 can't start another, it moves the first pawn
	for _, m := range st.legal(0, 2, R, nil) {
		if m.Kind == MStart {
			t.Fatal("started onto own pawn")
		}
	}
	// an opponent on your exit circle gets bumped when you start
	st2 := fresh(4)
	st2.set(1, 0, exitSq(0))
	st2.apply(0, Move{Kind: MStart, P: 0})
	if st2.Loc[1][0] != Start || st2.Loc[0][0] != int16(exitSq(0)) {
		t.Fatal("starting should bump an opponent on the exit circle")
	}
}

func TestBumpJumpOwnBlock(t *testing.T) {
	st := fresh(4)
	st.set(0, 0, 20)
	st.set(0, 1, 22)
	st.set(1, 0, 23)
	// jumping over pawns counts them as squares: 20 + 3 = 23, bumps the opponent
	st.apply(0, Move{Kind: MFwd, P: 0, N: 3})
	if st.Loc[0][0] != 23 || st.Loc[1][0] != Start {
		t.Fatal("jump and bump")
	}
	// landing on your own pawn is illegal
	st.set(0, 2, 19)
	cp := *st
	if cp.apply(0, Move{Kind: MFwd, P: 2, N: 3}) {
		t.Fatal("landed on own pawn")
	}
}

func TestSlides(t *testing.T) {
	// colour 1's short slide starts on square 16 and ends on 19
	st := fresh(4)
	st.set(0, 0, 13)
	st.set(0, 1, 18) // own pawn on the slide: bumped too
	st.set(2, 0, 19) // opponent at the end: bumped
	st.apply(0, Move{Kind: MFwd, P: 0, N: 3})
	if st.Loc[0][0] != 19 || st.Loc[0][1] != Start || st.Loc[2][0] != Start {
		t.Fatalf("slide: got %v", st.Loc)
	}
	// passing over a triangle doesn't slide
	st = fresh(4)
	st.set(0, 0, 14)
	st.apply(0, Move{Kind: MFwd, P: 0, N: 3})
	if st.Loc[0][0] != 17 {
		t.Fatal("slid without landing on the triangle")
	}
	// your own colour's slide: stay put
	st = fresh(4)
	st.set(0, 0, 58)
	st.apply(0, Move{Kind: MFwd, P: 0, N: 3}) // 58 -> 59 -> 0 -> 1 (own triangle)
	if st.Loc[0][0] != 1 {
		t.Fatalf("slid on own colour: %d", st.Loc[0][0])
	}
	// long slide (5 squares): colour 2 triangle 39 -> 43
	st = fresh(4)
	st.set(0, 0, 35)
	st.apply(0, Move{Kind: MFwd, P: 0, N: 4})
	if st.Loc[0][0] != 43 {
		t.Fatal("long slide")
	}
}

func TestBackwardShortcutAndSafety(t *testing.T) {
	st := fresh(4)
	st.set(0, 0, exitSq(0))
	st.apply(0, Move{Kind: MBack, P: 0, N: 4})
	if st.Loc[0][0] != 0 {
		t.Fatal("4 back from the exit lands on the corner")
	}
	if progress(0, 0) != 65-8 {
		t.Fatal("corner is 8 moves from Home for colour 0")
	}
	st.apply(0, Move{Kind: MFwd, P: 0, N: 3}) // 0 -> 1 -> 2 (entry) -> safety 1
	if st.Loc[0][0] != Safe1 {
		t.Fatalf("shortcut into safety: %d", st.Loc[0][0])
	}
	// backward out of the Safety Zone is allowed, backward into it is not
	st.apply(0, Move{Kind: MBack, P: 0, N: 4}) // safety 1 -> entry (2) -> 1 -> 0 -> 59
	if st.Loc[0][0] != 59 {
		t.Fatalf("back out of safety: %d", st.Loc[0][0])
	}
	// only your own colour enters your Safety Zone: colour 1 passes square 2 normally
	st = fresh(4)
	st.set(1, 0, 1)
	st.apply(1, Move{Kind: MFwd, P: 0, N: 2})
	if st.Loc[1][0] != 3 {
		t.Fatal("another colour entered the safety zone")
	}
}

func TestSevenTenElevenSorry(t *testing.T) {
	R := &Rules{}
	st := fresh(4)
	st.set(0, 0, 10)
	st.set(0, 1, 30)
	ms := st.legal(0, 7, R, nil)
	nsplit := 0
	for _, m := range ms {
		if m.Kind == MSplit {
			nsplit++
			if m.N+m.N2 != 7 {
				t.Fatal("split must use all 7")
			}
		}
		if m.Kind == MStart {
			t.Fatal("7 started a pawn")
		}
	}
	if nsplit != 12 {
		t.Fatalf("two pawns, 6 ways each order: %d", nsplit)
	}
	// using part of a 7 to get a pawn Home needs the rest usable: lone pawn 3 from Home can't split
	st = fresh(4)
	st.set(0, 0, Safe1+2) // 3 from Home
	if len(st.legal(0, 7, R, nil)) != 0 {
		t.Fatal("lone pawn near home can't use a 7")
	}
	// 10: forward 10 or back 1
	st = fresh(4)
	st.set(0, 0, 20)
	k := 0
	for _, m := range st.legal(0, 10, R, nil) {
		if m.Kind == MFwd || m.Kind == MBack {
			k++
		}
	}
	if k != 2 {
		t.Fatal("10 = forward 10 or back 1")
	}
	// 11 switch: only on the open track
	st = fresh(4)
	st.set(0, 0, 20)
	st.set(1, 0, 40)
	st.Loc[1][1] = Safe1 // an opponent pawn in their safety zone is untouchable
	sw := 0
	for _, m := range st.legal(0, 11, R, nil) {
		if m.Kind == MSwitch {
			sw++
			cp := *st
			cp.apply(0, m)
			if cp.Loc[0][0] != 40 || cp.Loc[1][0] != 20 {
				t.Fatal("switch swaps the two pawns")
			}
		}
	}
	if sw != 1 {
		t.Fatalf("one switch target, got %d", sw)
	}
	// a switch that lands you on another colour's triangle slides you (colour 1 triangle at 16 -> 19)
	st = fresh(4)
	st.set(0, 0, 30)
	st.set(2, 0, 16)
	st.apply(0, Move{Kind: MSwitch, P: 0, T: 2*4 + 0})
	if st.Loc[0][0] != 19 {
		t.Fatalf("switch onto a triangle should slide: %d", st.Loc[0][0])
	}
	// Sorry!: from Start onto an opponent on the track, bumping it
	st = fresh(4)
	st.set(1, 0, 33)
	ms = st.legal(0, CSorry, R, nil)
	if len(ms) != 1 {
		t.Fatal("one Sorry! target")
	}
	st.apply(0, ms[0])
	if st.Loc[0][0] != 33 || st.Loc[1][0] != Start {
		t.Fatal("Sorry! bump")
	}
	// Sorry! needs a pawn in Start
	st = fresh(4)
	for i := 0; i < 4; i++ {
		st.set(0, i, 5+i)
	}
	st.set(1, 0, 33)
	if len(st.legal(0, CSorry, R, nil)) != 0 {
		t.Fatal("Sorry! without a pawn in Start")
	}
	if len(st.legal(0, CSorry, &Rules{SorryFour: true}, nil)) != 4 {
		t.Fatal("2020 rules: Sorry! may move a pawn forward 4 instead")
	}
}

func TestTwoDrawsAgainAndWin(t *testing.T) {
	g := NewGame(rand.New(rand.NewSource(1)), &Rules{}, []*Policy{&normalPolicy, &normalPolicy})
	g.deck = []int8{3, 2} // draw order: 2 then 3
	g.Cards = 0
	g.turn(0)
	if g.Cards != 2 {
		t.Fatalf("a 2 draws again: drew %d", g.Cards)
	}
	g2 := NewGame(rand.New(rand.NewSource(1)), &Rules{TwoNoDraw: true}, []*Policy{&normalPolicy, &normalPolicy})
	g2.deck = []int8{3, 2}
	g2.Cards = 0
	g2.turn(0)
	if g2.Cards != 1 {
		t.Fatal("2020 rules: no extra draw")
	}
	// winning: last pawn home
	g3 := NewGame(rand.New(rand.NewSource(1)), &Rules{}, []*Policy{&normalPolicy, &normalPolicy})
	for i := 0; i < 3; i++ {
		g3.St.set(0, i, HomeSq)
	}
	g3.St.set(0, 3, Safe1+4)
	g3.deck = []int8{1}
	if !g3.turn(0) {
		t.Fatal("all four home wins")
	}
}

func TestReshuffleAndConservation(t *testing.T) {
	rng := rand.New(rand.NewSource(5))
	for k := 0; k < 3000; k++ {
		n := 2 + k%3
		pols := make([]*Policy, n)
		for i := range pols {
			pols[i] = &normalPolicy
		}
		if k%5 == 0 {
			pols[0] = &Policy{Random: true}
		}
		g := NewGame(rng, &Rules{Hand: 5 * (k % 2)}, pols)
		if w := g.Play(0); w < 0 {
			t.Fatal("game did not finish")
		}
		cards := len(g.deck) + len(g.disc)
		for s := 0; s < n; s++ {
			cards += len(g.hands[s])
		}
		if cards != 45 {
			t.Fatalf("cards %d != 45", cards)
		}
		// Occ agrees with pawn locations
		seen := 0
		for q := 0; q < Track; q++ {
			if o := g.St.Occ[q]; o >= 0 {
				seen++
				if int(g.St.Loc[o/4][o%4]) != q {
					t.Fatal("occupancy out of sync")
				}
			}
		}
		on := 0
		for s := 0; s < n; s++ {
			for i := 0; i < 4; i++ {
				if isTrack(int(g.St.Loc[s][i])) {
					on++
				}
			}
		}
		if on != seen {
			t.Fatal("pawn count mismatch")
		}
	}
}

func TestMirrorQuick(t *testing.T) {
	r := runGames(4, 5000, 3, 4, &Rules{}, &normalPolicy, nil)
	for i, v := range r["seat_win"].([]float64) {
		if v < 0.23 || v > 0.27 {
			t.Fatalf("seat %d wins %.3f", i, v)
		}
	}
}
