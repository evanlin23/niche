// p10sim: Phase 10 experiments.
//   p10sim -mode game -players 4 -games N -seed S -rules '{}' -base '{policy}' [-test '{policy}']
//   p10sim -mode deal -games N      (engine check: chance a 10-card deal already holds each Phase)
//   p10sim -mode solo -games N      (draws needed to finish each Phase alone, normal discards)
package main

import (
	"encoding/json"
	"flag"
	"math"
	"math/rand"
	"os"
	"runtime"
	"sync"
)

var normalPolicy = Policy{Name: "normal", Take: "improve", Lay: "now", SkipUse: "now", SkipTarget: "leader", Tie: "conn", HitOthers: true}

func parsePolicy(s string) *Policy {
	p := normalPolicy
	if s != "" {
		if err := json.Unmarshal([]byte(s), &p); err != nil {
			panic(err)
		}
	}
	return &p
}

func main() {
	mode := flag.String("mode", "game", "game | deal | solo")
	players := flag.Int("players", 4, "")
	games := flag.Int("games", 10000, "")
	seed := flag.Int64("seed", 1, "")
	rulesJ := flag.String("rules", "{}", "")
	baseJ := flag.String("base", "", "")
	testJ := flag.String("test", "", "")
	flag.Parse()
	var R Rules
	if err := json.Unmarshal([]byte(*rulesJ), &R); err != nil {
		panic(err)
	}
	W := runtime.NumCPU()
	per := (*games + W - 1) / W
	switch *mode {
	case "deal":
		out := runDeal(W, per, *seed)
		json.NewEncoder(os.Stdout).Encode(out)
	case "solo":
		out := runSolo(W, per, *seed, &R)
		json.NewEncoder(os.Stdout).Encode(out)
	default:
		base := parsePolicy(*baseJ)
		var test *Policy
		if *testJ != "" {
			test = parsePolicy(*testJ)
		}
		json.NewEncoder(os.Stdout).Encode(runGames(W, per, *seed, *players, &R, base, test))
	}
}

func runDeal(W, per int, seed int64) map[string]any {
	hits := make([][11]int, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*7919 + int64(w)))
			d := newDeck()
			var h Hand
			for k := 0; k < per; k++ {
				// a 10-card hand from a shuffled deck: the first 10 cards of a fresh shuffle
				for i := 0; i < 10; i++ {
					j := i + rng.Intn(len(d)-i)
					d[i], d[j] = d[j], d[i]
				}
				h.Reset()
				for i := 0; i < 10; i++ {
					h.Add(d[i])
				}
				for ph := 1; ph <= 10; ph++ {
					if Complete(ph, &h) {
						hits[w][ph]++
					}
				}
			}
		}(w)
	}
	wg.Wait()
	n := float64(per * W)
	rate := make([]float64, 10)
	for ph := 1; ph <= 10; ph++ {
		t := 0
		for w := 0; w < W; w++ {
			t += hits[w][ph]
		}
		rate[ph-1] = float64(t) / n
	}
	return map[string]any{"games": per * W, "deal_complete_rate": rate}
}

func runSolo(W, per int, seed int64, R *Rules) map[string]any {
	sums := make([][11]float64, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*104729 + int64(w)))
			pol := normalPolicy
			pol.Take = "never"
			var st Stats
			for k := 0; k < per; k++ {
				for ph := 1; ph <= 10; ph++ {
					g := NewGame(rng, R, []*Policy{&pol}, 0, &st)
					g.P[0].Phase = ph
					g.deal()
					g.disc = g.disc[:0]
					draws := 0
					for !Complete(ph, &g.P[0].H) && draws < 500 {
						c := g.pop()
						if c == 255 {
							break
						}
						g.P[0].H.Add(c)
						draws++
						if Complete(ph, &g.P[0].H) {
							break
						}
						if g.P[0].H.skip > 0 { // a lone player just throws Skips away
							g.P[0].H.RemoveCode(Skip)
							g.disc = append(g.disc, Skip)
							continue
						}
						c2, _ := pol.Discard(g, 0)
						g.P[0].H.RemoveCode(c2)
						g.disc = append(g.disc, c2)
					}
					sums[w][ph] += float64(draws)
				}
			}
		}(w)
	}
	wg.Wait()
	n := float64(per * W)
	mean := make([]float64, 10)
	for ph := 1; ph <= 10; ph++ {
		t := 0.0
		for w := 0; w < W; w++ {
			t += sums[w][ph]
		}
		mean[ph-1] = t / n
	}
	return map[string]any{"games": per * W, "solo_mean_draws": mean}
}

type acc struct {
	testWins, firstWins, games int
	seatWins                   [8]int
	rounds                     int
	st                         Stats
	testScore, otherScore      float64
}

func runGames(W, per int, seed int64, N int, R *Rules, base, test *Policy) map[string]any {
	accs := make([]acc, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*7907 + int64(w)))
			a := &accs[w]
			pols := make([]*Policy, N)
			track := make([]bool, N)
			for k := 0; k < per; k++ {
				ts := -1
				if test != nil {
					ts = (k + w) % N // the test bot rotates through every seat
				}
				for i := range pols {
					pols[i] = base
					track[i] = ts < 0 || i == ts
				}
				if ts >= 0 {
					pols[ts] = test
				}
				dealer := rng.Intn(N)
				g := NewGame(rng, R, pols, dealer, &a.st)
				g.track = track
				win := g.Play()
				a.games++
				a.rounds += g.round
				a.seatWins[win]++
				if win == (dealer+1)%N {
					a.firstWins++
				}
				if ts >= 0 {
					if win == ts {
						a.testWins++
					}
					a.testScore += float64(g.P[ts].Score)
					o := 0.0
					for i := range g.P {
						if i != ts {
							o += float64(g.P[i].Score)
						}
					}
					a.otherScore += o / float64(N-1)
				}
			}
		}(w)
	}
	wg.Wait()
	var t acc
	for _, a := range accs {
		t.testWins += a.testWins
		t.firstWins += a.firstWins
		t.games += a.games
		t.rounds += a.rounds
		t.testScore += a.testScore
		t.otherScore += a.otherScore
		for i := range a.seatWins {
			t.seatWins[i] += a.seatWins[i]
		}
		for i := 0; i < 11; i++ {
			t.st.Attempts[i] += a.st.Attempts[i]
			t.st.Completes[i] += a.st.Completes[i]
			t.st.LayTurn[i] += a.st.LayTurn[i]
		}
		t.st.Rounds += a.st.Rounds
		t.st.Turns += a.st.Turns
		t.st.Unfinished += a.st.Unfinished
	}
	n := float64(t.games)
	seat := make([]float64, N)
	for i := range seat {
		seat[i] = float64(t.seatWins[i]) / n
	}
	rate := make([]float64, 10)
	lay := make([]float64, 10)
	att := make([]int, 10)
	for ph := 1; ph <= 10; ph++ {
		att[ph-1] = t.st.Attempts[ph]
		if t.st.Attempts[ph] > 0 {
			rate[ph-1] = float64(t.st.Completes[ph]) / float64(t.st.Attempts[ph])
		}
		if t.st.Completes[ph] > 0 {
			lay[ph-1] = float64(t.st.LayTurn[ph]) / float64(t.st.Completes[ph])
		}
	}
	out := map[string]any{
		"games": t.games, "players": N, "fair_share": 1 / float64(N),
		"seat_win": seat, "first_player_win": float64(t.firstWins) / n,
		"mean_rounds": float64(t.rounds) / n,
		"mean_turns_per_round": float64(t.st.Turns) / float64(t.st.Rounds),
		"unfinished_rounds": float64(t.st.Unfinished) / float64(t.st.Rounds),
		"phase_attempts": att, "phase_complete_rate": rate, "phase_mean_lay_turn": lay,
	}
	if test != nil {
		p := float64(t.testWins) / n
		out["test_win"] = p
		out["ci95"] = 1.96 * math.Sqrt(p*(1-p)/n)
		out["test_mean_score"] = t.testScore / n
		out["others_mean_score"] = t.otherScore / n
	}
	return out
}
