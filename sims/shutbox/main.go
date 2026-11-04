// Shut the Box: exact solutions (dynamic programming over all 2^N tile states) + Monte Carlo check.
//
//	shutbox -n 9 -mode any|sumsplit [-oneDie] -games N
//
// Prints JSON: exact shut chance and expected leftover (sum of standing tiles) for perfect play
// (two objectives) and for human rules of thumb, plus a Monte Carlo replay of each strategy.
package main

import (
	"encoding/json"
	"flag"
	"math/rand"
	"os"
	"runtime"
	"sync"
)

var N int
var mode string
var oneDie bool

type roll struct {
	a, b int
	p    float64
}

func rollsFor(mask int) []roll {
	if oneDie && !anyHigh(mask) {
		r := make([]roll, 6)
		for d := 1; d <= 6; d++ {
			r[d-1] = roll{d, 0, 1.0 / 6}
		}
		return r
	}
	var r []roll
	for a := 1; a <= 6; a++ {
		for b := 1; b <= 6; b++ {
			r = append(r, roll{a, b, 1.0 / 36})
		}
	}
	return r
}

func anyHigh(mask int) bool {
	for t := 7; t <= N; t++ {
		if mask>>t&1 == 1 {
			return true
		}
	}
	return false
}

func sumTiles(mask int) int {
	s := 0
	for t := 1; t <= N; t++ {
		if mask>>t&1 == 1 {
			s += t
		}
	}
	return s
}

func bits(m int) int {
	c := 0
	for ; m > 0; m &= m - 1 {
		c++
	}
	return c
}

var movesCache = map[[3]int][]int{}
var mcMu sync.Mutex

// legal moves: subsets of open tiles to knock down
func moves(mask, a, b int) []int {
	key := [3]int{mask, a, b}
	mcMu.Lock()
	if m, ok := movesCache[key]; ok {
		mcMu.Unlock()
		return m
	}
	mcMu.Unlock()
	s := a + b
	var out []int
	if mode == "any" {
		for sub := mask; sub > 0; sub = (sub - 1) & mask {
			if sumTiles(sub) == s {
				out = append(out, sub)
			}
		}
	} else {
		if s <= N && mask>>s&1 == 1 {
			out = append(out, 1<<s)
		}
		if b > 0 && a != b && mask>>a&1 == 1 && mask>>b&1 == 1 {
			out = append(out, 1<<a|1<<b)
		}
	}
	mcMu.Lock()
	movesCache[key] = out
	mcMu.Unlock()
	return out
}

type Policy func(mask, a, b int, ms []int, rng *rand.Rand) int

// ---------- exact optimal values
var vShut, vLeft []float64

func solve() {
	full := 1<<(N+1) - 2
	vShut = make([]float64, full+1)
	vLeft = make([]float64, full+1)
	for mask := 0; mask <= full; mask += 2 {
		if mask&full != mask {
			continue
		}
	}
	// process masks in increasing order of popcount (subsets first)
	order := []int{}
	for m := 0; m <= full; m += 2 {
		order = append(order, m)
	}
	for c := 0; c <= N; c++ {
		for _, m := range order {
			if bits(m) != c {
				continue
			}
			if m == 0 {
				vShut[m], vLeft[m] = 1, 0
				continue
			}
			var es, el float64
			for _, r := range rollsFor(m) {
				ms := moves(m, r.a, r.b)
				if len(ms) == 0 {
					el += r.p * float64(sumTiles(m))
					continue
				}
				bs, bl := 0.0, 1e9
				for _, x := range ms {
					if vShut[m&^x] > bs {
						bs = vShut[m&^x]
					}
					if vLeft[m&^x] < bl {
						bl = vLeft[m&^x]
					}
				}
				es += r.p * bs
				el += r.p * bl
			}
			vShut[m], vLeft[m] = es, el
		}
	}
}

func argBest(m int, ms []int, v []float64, maximize bool) int {
	best := ms[0]
	for _, x := range ms[1:] {
		if (maximize && v[m&^x] > v[m&^best]) || (!maximize && v[m&^x] < v[m&^best]) {
			best = x
		}
	}
	return best
}

func highest(x int) int {
	h := 0
	for t := 1; t <= N; t++ {
		if x>>t&1 == 1 {
			h = t
		}
	}
	return h
}

var policies = map[string]Policy{
	"perfect (shut)":      func(m, a, b int, ms []int, r *rand.Rand) int { return argBest(m, ms, vShut, true) },
	"perfect (low score)": func(m, a, b int, ms []int, r *rand.Rand) int { return argBest(m, ms, vLeft, false) },
	"biggest tile first": func(m, a, b int, ms []int, r *rand.Rand) int {
		best := ms[0]
		for _, x := range ms[1:] {
			if highest(x) > highest(best) || (highest(x) == highest(best) && bits(x) < bits(best)) {
				best = x
			}
		}
		return best
	},
	"fewest tiles": func(m, a, b int, ms []int, r *rand.Rand) int {
		best := ms[0]
		for _, x := range ms[1:] {
			if bits(x) < bits(best) || (bits(x) == bits(best) && highest(x) > highest(best)) {
				best = x
			}
		}
		return best
	},
	"most tiles": func(m, a, b int, ms []int, r *rand.Rand) int {
		best := ms[0]
		for _, x := range ms[1:] {
			if bits(x) > bits(best) || (bits(x) == bits(best) && highest(x) > highest(best)) {
				best = x
			}
		}
		return best
	},
	"smallest tiles first": func(m, a, b int, ms []int, r *rand.Rand) int {
		best := ms[0]
		for _, x := range ms[1:] {
			if highest(x) < highest(best) {
				best = x
			}
		}
		return best
	},
	"random": func(m, a, b int, ms []int, r *rand.Rand) int { return ms[r.Intn(len(ms))] },
}

// exact evaluation of a deterministic policy
func evaluate(pol Policy, avg bool) (float64, float64) {
	full := 1<<(N+1) - 2
	vs := make([]float64, full+1)
	vl := make([]float64, full+1)
	rng := rand.New(rand.NewSource(1))
	for c := 0; c <= N; c++ {
		for m := 0; m <= full; m += 2 {
			if bits(m) != c {
				continue
			}
			if m == 0 {
				vs[m] = 1
				continue
			}
			var es, el float64
			for _, r := range rollsFor(m) {
				ms := moves(m, r.a, r.b)
				if len(ms) == 0 {
					el += r.p * float64(sumTiles(m))
					continue
				}
				if avg { // random policy: exact expectation over all legal moves
					for _, x := range ms {
						es += r.p / float64(len(ms)) * vs[m&^x]
						el += r.p / float64(len(ms)) * vl[m&^x]
					}
					continue
				}
				x := pol(m, r.a, r.b, ms, rng)
				es += r.p * vs[m&^x]
				el += r.p * vl[m&^x]
			}
			vs[m], vl[m] = es, el
		}
	}
	return vs[full], vl[full]
}

func montecarlo(pol Policy, games int, seed int64) (float64, float64) {
	W := runtime.NumCPU()
	per := games / W
	shut := make([]int, W)
	left := make([]float64, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*7919 + int64(w)))
			full := 1<<(N+1) - 2
			for k := 0; k < per; k++ {
				m := full
				for m != 0 {
					var a, b int
					if oneDie && !anyHigh(m) {
						a = 1 + rng.Intn(6)
					} else {
						a, b = 1+rng.Intn(6), 1+rng.Intn(6)
					}
					ms := moves(m, a, b)
					if len(ms) == 0 {
						break
					}
					m &^= pol(m, a, b, ms, rng)
				}
				if m == 0 {
					shut[w]++
				}
				left[w] += float64(sumTiles(m))
			}
		}(w)
	}
	wg.Wait()
	s, l := 0, 0.0
	for w := range shut {
		s += shut[w]
		l += left[w]
	}
	return float64(s) / float64(per*W), l / float64(per*W)
}

func main() {
	flag.IntVar(&N, "n", 9, "tiles 1..n")
	flag.StringVar(&mode, "mode", "any", "any | sumsplit")
	flag.BoolVar(&oneDie, "oneDie", false, "roll one die once 7+ are down")
	games := flag.Int("games", 1000000, "Monte Carlo games per strategy")
	seed := flag.Int64("seed", 1, "")
	flag.Parse()
	solve()
	full := 1<<(N+1) - 2
	out := map[string]any{"tiles": N, "mode": mode, "one_die": oneDie, "games_per_strategy": *games,
		"perfect_shut_exact": vShut[full], "perfect_low_score_exact_left": vLeft[full]}
	strat := map[string]any{}
	for name, pol := range policies {
		es, el := evaluate(pol, name == "random")
		ms, ml := 0.0, 0.0
		if *games > 0 {
			ms, ml = montecarlo(pol, *games, *seed)
		}
		strat[name] = map[string]float64{"shut_exact": es, "left_exact": el, "shut_sim": ms, "left_sim": ml}
	}
	out["strategies"] = strat
	json.NewEncoder(os.Stdout).Encode(out)
}
