package main

import (
	"math/rand"
	"testing"
)

func BenchmarkGame4p(b *testing.B) {
	rng := rand.New(rand.NewSource(1))
	pol := normalPolicy
	pols := []*Policy{&pol, &pol, &pol, &pol}
	var st Stats
	for i := 0; i < b.N; i++ {
		g := NewGame(rng, &Rules{}, pols, i%4, &st)
		g.Play()
	}
}
