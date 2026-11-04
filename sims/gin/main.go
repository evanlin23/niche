// ginsim: gin rummy experiments.
//   ginsim -games N -seed S -rules '{}' -a '{policy}' -b '{policy}'   (full games to 100; a and b alternate first deal)
//   ginsim -mode deal -games N   (engine check: share of 10-card deals that already hold a meld)
package main

import (
	"encoding/json"
	"flag"
	"math"
	"math/bits"
	"math/rand"
	"os"
	"runtime"
	"sync"
)

func parsePolicy(s string) *Policy {
	p := Policy{Name: "normal", Knock: 10, Take: "meld", Tie: "keep"}
	if s != "" {
		if err := json.Unmarshal([]byte(s), &p); err != nil {
			panic(err)
		}
	}
	return &p
}

func hasMeld(h uint64) bool { return Deadwood(h) < handValue(h) }

func main() {
	mode := flag.String("mode", "game", "game | deal")
	games := flag.Int("games", 10000, "")
	seed := flag.Int64("seed", 1, "")
	rulesJ := flag.String("rules", "{}", "")
	aJ := flag.String("a", "", "")
	bJ := flag.String("b", "", "")
	flag.Parse()
	var R Rules
	json.Unmarshal([]byte(*rulesJ), &R)
	W := runtime.NumCPU()
	per := (*games + W - 1) / W
	enc := json.NewEncoder(os.Stdout)
	if *mode == "deal" {
		hits, knock := make([]int, W), make([]int, W)
		var wg sync.WaitGroup
		for w := 0; w < W; w++ {
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				rng := rand.New(rand.NewSource(*seed*7919 + int64(w)))
				var d [52]int
				for i := range d {
					d[i] = i
				}
				for k := 0; k < per; k++ {
					var h uint64
					for i := 0; i < 10; i++ {
						j := i + rng.Intn(52-i)
						d[i], d[j] = d[j], d[i]
						h |= 1 << d[i]
					}
					if hasMeld(h) {
						hits[w]++
					}
					if Deadwood(h) <= 10 {
						knock[w]++
					}
				}
			}(w)
		}
		wg.Wait()
		a, b := 0, 0
		for w := 0; w < W; w++ {
			a += hits[w]
			b += knock[w]
		}
		n := float64(per * W)
		enc.Encode(map[string]any{"games": per * W, "deal_has_meld": float64(a) / n, "deal_deadwood_le10": float64(b) / n})
		return
	}
	A, B := parsePolicy(*aJ), parsePolicy(*bJ)
	enc.Encode(runGames(W, per, *seed, &R, A, B))
}

func runGames(W, per int, seed int64, R *Rules, A, B *Policy) map[string]any {
	type acc struct {
		aWin, hands, aFirstDealWin, aFirst int
		st                                 Stats
		aHandWins, handsDecided            int
	}
	accs := make([]acc, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*7907 + int64(w)))
			a := &accs[w]
			g := &Game{R: R, rng: rng}
			for k := 0; k < per; k++ {
				aSeat := (k + w) % 2 // A plays seat 0 or 1; seat 0 always deals first, so A deals first half the time
				if aSeat == 0 {
					g.P[0].Pol, g.P[1].Pol = A, B
				} else {
					g.P[0].Pol, g.P[1].Pol = B, A
				}
				win, hands := g.PlayGame(0, &a.st)
				a.hands += hands
				if win == aSeat {
					a.aWin++
				}
				if aSeat == 1 { // A was the non-dealer in the first hand, so A played first
					a.aFirst++
					if win == aSeat {
						a.aFirstDealWin++
					}
				}
			}
		}(w)
	}
	wg.Wait()
	var t acc
	for _, a := range accs {
		t.aWin += a.aWin
		t.hands += a.hands
		t.aFirst += a.aFirst
		t.aFirstDealWin += a.aFirstDealWin
		t.st.Hands += a.st.Hands
		t.st.Void += a.st.Void
		t.st.Gins += a.st.Gins
		t.st.Knocks += a.st.Knocks
		t.st.KnockDW += a.st.KnockDW
		t.st.Undercuts += a.st.Undercuts
		t.st.Turns += a.st.Turns
	}
	n := float64(per * W)
	p := float64(t.aWin) / n
	dec := float64(t.st.Hands - t.st.Void)
	return map[string]any{
		"games": per * W, "a_win": p, "ci95": 1.96 * math.Sqrt(p*(1-p)/n),
		"hands": t.st.Hands, "mean_hands_per_game": float64(t.hands) / n,
		"void_rate": float64(t.st.Void) / float64(t.st.Hands), "gin_rate": float64(t.st.Gins) / dec,
		"undercut_rate_of_knocks": float64(t.st.Undercuts) / math.Max(1, float64(t.st.Knocks)),
		"mean_knock_deadwood":     float64(t.st.KnockDW) / math.Max(1, float64(t.st.Knocks)),
		"mean_turns_per_hand":     float64(t.st.Turns) / float64(t.st.Hands),
		"a_win_when_a_plays_first": float64(t.aFirstDealWin) / math.Max(1, float64(t.aFirst)),
	}
}

var _ = bits.OnesCount64
