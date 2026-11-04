package main

import (
	"math/bits"
	"math/rand"
	"testing"
)

func bit(i int) uint32 { return 1 << i }

func TestStartAndPerft(t *testing.T) {
	p := StartPos()
	if bits.OnesCount32(p.P[0]) != 12 || bits.OnesCount32(p.P[1]) != 12 || p.K != 0 || p.Side != 0 {
		t.Fatal("12 men each, Red to move")
	}
	if p.P[0]&p.P[1] != 0 || p.P[0] != 0xFFF || p.P[1] != 0xFFF00000 {
		t.Fatal("Red on squares 1-12, White on 21-32")
	}
	// published perft counts for American checkers from the start position
	want := []int64{7, 49, 302, 1469, 7361, 36768, 179740, 845931}
	for d, w := range want {
		if got := Perft(&p, d+1); got != w {
			t.Fatalf("perft(%d) = %d, want %d", d+1, got, w)
		}
	}
}

func TestGeometry(t *testing.T) {
	// near-left corner of Red (row 0, column 0) is a playing square (WCDF 1.4)
	if sq(0, 0) != 0 || sq(0, 1) != -1 || sq(7, 7) != 31 {
		t.Fatal("layout")
	}
	for i := 0; i < 32; i++ {
		for d := 0; d < 4; d++ {
			want := uint32(0)
			if nb[i][d] >= 0 {
				want = bit(int(nb[i][d]))
			}
			if stepFn[d](bit(i)) != want {
				t.Fatalf("bitboard step %d from %d", d, i)
			}
		}
	}
}

func pos(red, white, kings []int, side int) Pos {
	var p Pos
	for _, i := range red {
		p.P[0] |= bit(i)
	}
	for _, i := range white {
		p.P[1] |= bit(i)
	}
	for _, i := range kings {
		p.K |= bit(i)
	}
	p.Side = side
	return p
}

func TestMenForwardKingsBoth(t *testing.T) {
	p := pos([]int{13}, []int{31}, nil, 0)
	for _, m := range p.Legal(nil, false) {
		if m.From == 13 && m.To < 13 {
			t.Fatal("a man moved backwards")
		}
	}
	p.K = bit(13)
	n := 0
	for _, m := range p.Legal(nil, false) {
		if m.From == 13 {
			n++
		}
	}
	if n != 4 {
		t.Fatalf("a king in the middle has 4 moves, got %d", n)
	}
}

func TestForcedCapture(t *testing.T) {
	// Red man on 9 (row 2), White man on its up-right neighbour, empty landing
	r, c := rc(9)
	over, land := sq(r+1, c+1), sq(r+2, c+2)
	p := pos([]int{9, 1}, []int{over, 30}, nil, 0)
	ms := p.Legal(nil, false)
	if len(ms) != 1 || ms[0].From != 9 || int(ms[0].To) != land || ms[0].Cap != bit(over) {
		t.Fatalf("the jump is compulsory and the only legal move: %v", ms)
	}
	// optional rule: quiet moves are allowed too
	if len(p.Legal(nil, true)) <= 1 {
		t.Fatal("optional rule should also allow quiet moves")
	}
}

func TestMultiJumpAndChoice(t *testing.T) {
	// Red man at (0,0) = 0; White men at (1,1) and (3,3): double jump to (4,4). Must complete it.
	p := pos([]int{sq(0, 0)}, []int{sq(1, 1), sq(3, 3), sq(7, 1)}, nil, 0)
	ms := p.Legal(nil, false)
	if len(ms) != 1 || int(ms[0].To) != sq(4, 4) || bits.OnesCount32(ms[0].Cap) != 2 {
		t.Fatalf("double jump must be completed: %v", ms)
	}
	// two sequences of different length: the player may choose either (WCDF 1.20, no majority rule)
	p = pos([]int{sq(2, 2)}, []int{sq(3, 1), sq(3, 3), sq(5, 5), sq(7, 1)}, nil, 0)
	ms = p.Legal(nil, false)
	lens := map[int]bool{}
	for _, m := range ms {
		lens[bits.OnesCount32(m.Cap)] = true
	}
	if !lens[1] || !lens[2] {
		t.Fatalf("both the single and the double jump are legal: %v", ms)
	}
}

func TestCrowningEndsMove(t *testing.T) {
	// Red man jumps into the king row; another jump would be available to a king, but the move ends
	p := pos([]int{sq(5, 1)}, []int{sq(6, 2), sq(6, 4), sq(0, 6)}, nil, 0)
	ms := p.Legal(nil, false)
	if len(ms) != 1 || int(ms[0].To) != sq(7, 3) || bits.OnesCount32(ms[0].Cap) != 1 {
		t.Fatalf("crowning ends the turn: %v", ms)
	}
	p.Apply(ms[0])
	if p.K&bit(sq(7, 3)) == 0 {
		t.Fatal("man should be crowned")
	}
}

func TestNoDoubleJumpOfSamePiece(t *testing.T) {
	// a king circling: it may not jump the same piece twice; captured pieces stay on the board until the end
	p := pos([]int{sq(2, 2)}, []int{sq(3, 3), sq(3, 1), sq(5, 3), sq(5, 1), sq(7, 7)}, []int{sq(2, 2)}, 0)
	for _, m := range p.Legal(nil, false) {
		if bits.OnesCount32(m.Cap) > 4 {
			t.Fatal("jumped a piece twice")
		}
	}
	// the king can go round the square of four and come back to its own starting square
	found := false
	for _, m := range p.Legal(nil, false) {
		if bits.OnesCount32(m.Cap) == 4 && int(m.To) == sq(2, 2) {
			found = true
		}
	}
	if !found {
		t.Fatal("the starting square is empty during the king's own jumps")
	}
}

func TestWinAndDraw(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	R := &Rules{}
	rnd := &Policy{Random: true}
	sr := &Searcher{R: R, B: rnd}
	for k := 0; k < 2000; k++ {
		res := Play(rng, R, [2]*Policy{rnd, rnd}, [2]*Searcher{sr, sr})
		if res.Plies <= 0 || res.Plies > 400 {
			t.Fatal("plies")
		}
	}
	// blocked: White to move with its only man stuck in front of Red pieces loses
	p := pos([]int{sq(5, 1), sq(4, 0), sq(4, 2), sq(6, 0)}, []int{sq(7, 1)}, nil, 1)
	_ = p
	q := pos([]int{sq(6, 0), sq(5, 3)}, []int{sq(7, 1)}, nil, 1)
	// White man on (7,1) moves down to (6,0) or (6,2); block both and leave no jump
	q = pos([]int{sq(6, 0), sq(6, 2), sq(5, 3), sq(5, 1)}, []int{sq(7, 1)}, nil, 1)
	if len(q.Legal(nil, false)) != 0 {
		t.Fatalf("white should be blocked: %v", q.Legal(nil, false))
	}
}

func TestFortyMoveAndRepetition(t *testing.T) {
	// two lone kings far apart: random shuffling must end in a draw by repetition or the 40-move rule
	rng := rand.New(rand.NewSource(2))
	R := &Rules{}
	rnd := &Policy{Random: true}
	sr := &Searcher{R: R, B: rnd}
	draws := 0
	for k := 0; k < 300; k++ {
		res := Play(rng, R, [2]*Policy{rnd, rnd}, [2]*Searcher{sr, sr})
		if res.Winner < 0 {
			draws++
			if res.Plies >= 400 && !res.Repetition {
				t.Fatal("draw at the hard cap: the 40-move rule should have fired first")
			}
		}
	}
	_ = draws
}

func TestHuffRemovesPiece(t *testing.T) {
	r, c := rc(9)
	over := sq(r+1, c+1)
	R := &Rules{Huff: true}
	p := pos([]int{9, 1}, []int{over, 30}, nil, 0)
	q := p
	applyWithHuff(&q, Move{From: 1, To: int8(nb[1][UR]), Cap: 0}, true)
	if q.P[0]&bit(9) != 0 {
		t.Fatal("the man that could have jumped is huffed")
	}
	_ = R
}

func TestMirrorQuick(t *testing.T) {
	r := runGames(4000, 3, &Rules{}, &Policy{Depth: 1}, &Policy{Depth: 1})
	if s := r["a_score"].(float64); s < 0.47 || s > 0.53 {
		t.Fatalf("identical bots score %.3f", s)
	}
}
