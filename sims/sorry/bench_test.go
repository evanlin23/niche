package main

import (
	"math/rand"
	"testing"
)

func BenchmarkGame4p(b *testing.B) {
	rng := rand.New(rand.NewSource(1))
	pols := []*Policy{&normalPolicy, &normalPolicy, &normalPolicy, &normalPolicy}
	for i := 0; i < b.N; i++ {
		g := NewGame(rng, &Rules{}, pols)
		g.Play(i % 4)
	}
}
