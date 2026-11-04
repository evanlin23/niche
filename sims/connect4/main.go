package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"runtime"
	"sync"
	"time"
)

func main() {
	opening := flag.Bool("openings", false, "solve every first move (the 1988 result)")
	onlyCol := flag.Int("col", 0, "with -openings: solve only this first column (1-7)")
	aJ := flag.String("a", "", "bot A json")
	bJ := flag.String("b", "", "bot B json")
	games := flag.Int("games", 100000, "games per seat order")
	seed := flag.Int64("seed", 1, "")
	flag.Parse()
	if *aJ != "" {
		var A, B Bot
		json.Unmarshal([]byte(*aJ), &A)
		json.Unmarshal([]byte(*bJ), &B)
		Wk := runtime.NumCPU()
		type acc struct{ aw1, d1, ad2, aw2, d2, len int }
		accs := make([]acc, Wk)
		var wg sync.WaitGroup
		per := *games / Wk
		for w := 0; w < Wk; w++ {
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				rng := rand.New(rand.NewSource(*seed*31337 + int64(w)))
				a := &accs[w]
				for k := 0; k < per; k++ {
					r, l := Game(&A, &B, rng) // A moves first
					if r == 1 {
						a.aw1++
					} else if r == 0 {
						a.d1++
					}
					a.len += l
					r, l = Game(&B, &A, rng) // A moves second
					if r == -1 {
						a.aw2++
					} else if r == 0 {
						a.d2++
					}
					a.len += l
				}
			}(w)
		}
		wg.Wait()
		var t acc
		for _, a := range accs {
			t.aw1 += a.aw1
			t.d1 += a.d1
			t.aw2 += a.aw2
			t.d2 += a.d2
			t.len += a.len
		}
		n := float64(per * Wk)
		json.NewEncoder(os.Stdout).Encode(map[string]any{"games_per_seat": per * Wk,
			"a_win_first": float64(t.aw1) / n, "draw_a_first": float64(t.d1) / n,
			"a_win_second": float64(t.aw2) / n, "draw_a_second": float64(t.d2) / n,
			"a_win_overall": float64(t.aw1+t.aw2) / (2 * n), "mean_moves": float64(t.len) / (2 * n)})
		return
	}
	if *opening {
		res := map[string]any{}
		for c := 0; c < W; c++ {
			if *onlyCol > 0 && c != *onlyCol-1 {
				continue
			}
			var p Pos
			p.play(c)
			s := NewSolver()
			t0 := time.Now()
			v := -s.Solve(p) // score from the first player's point of view
			res[fmt.Sprint(c+1)] = map[string]any{"score": v, "nodes": s.nodes, "seconds": time.Since(t0).Seconds()}
			fmt.Fprintf(os.Stderr, "column %d: %+d (%s, %d nodes)\n", c+1, v, time.Since(t0).Round(time.Second), s.nodes)
		}
		json.NewEncoder(os.Stdout).Encode(res)
	}
}
