package main

import "testing"

func TestWinDetection(t *testing.T) {
	var p Pos
	for _, c := range []int{0, 1, 0, 1, 0, 1} {
		p.play(c)
	}
	if !p.isWinningMove(0) {
		t.Fatal("vertical four not detected")
	}
	var q Pos
	for _, c := range []int{0, 0, 1, 1, 2, 2} {
		q.play(c)
	}
	if !q.isWinningMove(3) {
		t.Fatal("horizontal four not detected")
	}
}

func TestSolverKnownEndgame(t *testing.T) {
	// first player has three in a row on the bottom with both ends open: wins next move
	var p Pos
	for _, c := range []int{2, 2, 3, 3} {
		p.play(c)
	}
	s := NewSolver()
	if v := s.Solve(p); v <= 0 {
		t.Fatalf("expected a win for the player to move, got %d", v)
	}
}
