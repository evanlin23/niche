// cksim: checkers experiments.
//   cksim -games N -seed S -rules '{}' -a '{policy}' -b '{policy}'   (a and b swap colours every game)
//   cksim -mode perft -depth D           (move-generator check: number of move sequences)
//   cksim -mode randcheck -games N       (both sides random: chance a capture has happened within 6 plies)
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"math/rand"
	"os"
	"runtime"
	"sync"
)

func parsePolicy(s string) *Policy {
	p := Policy{Name: "normal", Depth: 2}
	if s != "" {
		if err := json.Unmarshal([]byte(s), &p); err != nil {
			panic(err)
		}
	}
	return &p
}

func Perft(p *Pos, d int) int64 {
	if d == 0 {
		return 1
	}
	ms := p.Legal(nil, false)
	if d == 1 {
		return int64(len(ms))
	}
	var n int64
	for _, m := range ms {
		q := *p
		q.Apply(m)
		n += Perft(&q, d-1)
	}
	return n
}

func main() {
	mode := flag.String("mode", "game", "game | perft | randcheck")
	games := flag.Int("games", 1000, "")
	seed := flag.Int64("seed", 1, "")
	depth := flag.Int("depth", 6, "")
	rulesJ := flag.String("rules", "{}", "")
	aJ := flag.String("a", "", "")
	bJ := flag.String("b", "", "")
	flag.Parse()
	var R Rules
	json.Unmarshal([]byte(*rulesJ), &R)
	enc := json.NewEncoder(os.Stdout)
	switch *mode {
	case "perft":
		p := StartPos()
		out := []int64{}
		for d := 1; d <= *depth; d++ {
			out = append(out, Perft(&p, d))
		}
		enc.Encode(map[string]any{"perft": out})
		return
	case "randcheck":
		enc.Encode(randCheck(*games, *seed))
		return
	}
	A, B := parsePolicy(*aJ), parsePolicy(*bJ)
	enc.Encode(runGames(*games, *seed, &R, A, B))
}

// randCheck: both sides pick uniformly among legal moves (official rules); share of games with at least one
// capture in the first 6 plies.
func randCheck(games int, seed int64) map[string]any {
	W := runtime.NumCPU()
	per := (games + W - 1) / W
	hits := make([]int, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*7919 + int64(w)))
			buf := make([]Move, 0, 32)
			for k := 0; k < per; k++ {
				p := StartPos()
				for ply := 0; ply < 6; ply++ {
					ms := p.Legal(buf, false)
					m := ms[rng.Intn(len(ms))]
					if m.Cap != 0 {
						hits[w]++
						break
					}
					p.Apply(m)
				}
			}
		}(w)
	}
	wg.Wait()
	t := 0
	for _, h := range hits {
		t += h
	}
	return map[string]any{"games": per * W, "capture_within_6_plies": float64(t) / float64(per*W)}
}

func runGames(games int, seed int64, R *Rules, A, B *Policy) map[string]any {
	W := runtime.NumCPU()
	per := (games + W - 1) / W
	type acc struct{ aWin, bWin, draw, redWin, whiteWin, plies, caps, huffs, aRedWin, aRed int }
	accs := make([]acc, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*7907 + int64(w)))
			sa, sb := &Searcher{R: R, B: A}, &Searcher{R: R, B: B}
			a := &accs[w]
			for k := 0; k < per; k++ {
				aRed := (k+w)%2 == 0
				pol := [2]*Policy{A, B}
				sr := [2]*Searcher{sa, sb}
				if !aRed {
					pol = [2]*Policy{B, A}
					sr = [2]*Searcher{sb, sa}
				}
				r := Play(rng, R, pol, sr)
				a.plies += r.Plies
				a.caps += r.Captures
				a.huffs += r.Huffs
				if aRed {
					a.aRed++
				}
				switch {
				case r.Winner < 0:
					a.draw++
				case (r.Winner == 0) == aRed:
					a.aWin++
					if aRed {
						a.aRedWin++
					}
				default:
					a.bWin++
				}
				if r.Winner == 0 {
					a.redWin++
				} else if r.Winner == 1 {
					a.whiteWin++
				}
			}
		}(w)
	}
	wg.Wait()
	var t acc
	for _, a := range accs {
		t.aWin += a.aWin
		t.bWin += a.bWin
		t.draw += a.draw
		t.redWin += a.redWin
		t.whiteWin += a.whiteWin
		t.plies += a.plies
		t.caps += a.caps
		t.huffs += a.huffs
	}
	n := float64(per * W)
	pa := float64(t.aWin) / n
	return map[string]any{
		"games": per * W, "a_win": pa, "b_win": float64(t.bWin) / n, "draw": float64(t.draw) / n,
		"a_score": (float64(t.aWin) + 0.5*float64(t.draw)) / n, "ci95": 1.96 * math.Sqrt(pa*(1-pa)/n),
		"first_player_win": float64(t.redWin) / n, "second_player_win": float64(t.whiteWin) / n,
		"mean_plies": float64(t.plies) / n, "mean_captures": float64(t.caps) / n, "mean_huffs": float64(t.huffs) / n,
	}
}

var _ = fmt.Sprintf
