// sorrysim: Sorry! experiments.
//   sorrysim -players 4 -games N -seed S -rules '{}' -base '{policy}' [-test '{policy}']
//   sorrysim -mode check -games N   (engine check: nobody gets a pawn out in the first round of a 4-player game)
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

var normalPolicy = Policy{Name: "normal"}

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
	mode := flag.String("mode", "game", "game | check")
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
	enc := json.NewEncoder(os.Stdout)
	if *mode == "check" {
		enc.Encode(runCheck(W, per, *seed, &R))
		return
	}
	base := parsePolicy(*baseJ)
	var test *Policy
	if *testJ != "" {
		test = parsePolicy(*testJ)
	}
	enc.Encode(runGames(W, per, *seed, *players, &R, base, test))
}

// runCheck plays the first round of real 4-player games and records how often nobody got a pawn out,
// and how often the first player got one out on their first turn.
func runCheck(W, per int, seed int64, R *Rules) map[string]any {
	none := make([]int, W)
	first := make([]int, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(seed*7919 + int64(w)))
			pols := []*Policy{&normalPolicy, &normalPolicy, &normalPolicy, &normalPolicy}
			for k := 0; k < per; k++ {
				g := NewGame(rng, R, pols)
				out := 0
				for s := 0; s < 4; s++ {
					g.turn(s)
					for i := 0; i < 4; i++ {
						if g.St.Loc[s][i] != Start {
							out++
							if s == 0 {
								first[w]++
							}
							break
						}
					}
				}
				if out == 0 {
					none[w]++
				}
			}
		}(w)
	}
	wg.Wait()
	n, a, b := float64(per*W), 0, 0
	for w := 0; w < W; w++ {
		a += none[w]
		b += first[w]
	}
	return map[string]any{"games": per * W, "nobody_out_after_round1": float64(a) / n, "first_player_out_turn1": float64(b) / n}
}

type acc struct {
	testWins, firstWins, games, turns, cards int
	seatWins                                 [4]int
	cs                                       CardStats
	testHome, otherHome                      float64
	unfinished                               int
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
			for k := 0; k < per; k++ {
				ts := -1
				if test != nil {
					ts = (k + w) % N // the test bot rotates through every seat
				}
				for i := range pols {
					pols[i] = base
				}
				if ts >= 0 {
					pols[ts] = test
				}
				g := NewGame(rng, R, pols)
				if test == nil {
					g.CS = &a.cs
				}
				first := rng.Intn(N)
				win := g.Play(first)
				a.games++
				a.turns += g.Turns
				a.cards += g.Cards
				if win < 0 {
					a.unfinished++
					continue
				}
				a.seatWins[win]++
				if win == first {
					a.firstWins++
				}
				if ts >= 0 {
					if win == ts {
						a.testWins++
					}
					a.testHome += float64(g.St.homeCount(ts))
					o := 0.0
					for i := 0; i < N; i++ {
						if i != ts {
							o += float64(g.St.homeCount(i))
						}
					}
					a.otherHome += o / float64(N-1)
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
		t.turns += a.turns
		t.cards += a.cards
		t.unfinished += a.unfinished
		t.testHome += a.testHome
		t.otherHome += a.otherHome
		for i := range a.seatWins {
			t.seatWins[i] += a.seatWins[i]
		}
		for i := 0; i < 13; i++ {
			t.cs.Draws[i] += a.cs.Draws[i]
			t.cs.Swing[i] += a.cs.Swing[i]
			t.cs.Forfeit[i] += a.cs.Forfeit[i]
		}
		t.cs.Shortcut += a.cs.Shortcut
	}
	n := float64(t.games)
	seat := make([]float64, N)
	for i := range seat {
		seat[i] = float64(t.seatWins[i]) / n
	}
	out := map[string]any{
		"games": t.games, "players": N, "fair_share": 1 / float64(N), "seat_win": seat,
		"first_player_win": float64(t.firstWins) / n, "mean_turns": float64(t.turns) / n,
		"mean_cards": float64(t.cards) / n, "unfinished": float64(t.unfinished) / n,
	}
	if test == nil {
		swing := map[string]float64{}
		forfeit := map[string]float64{}
		names := map[int]string{0: "sorry", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 7: "7", 8: "8", 10: "10", 11: "11", 12: "12"}
		for i, nm := range names {
			if t.cs.Draws[i] > 0 {
				swing[nm] = t.cs.Swing[i] / float64(t.cs.Draws[i])
				forfeit[nm] = float64(t.cs.Forfeit[i]) / float64(t.cs.Draws[i])
			}
		}
		out["card_swing"] = swing
		out["card_forfeit"] = forfeit
		out["shortcuts_per_game"] = float64(t.cs.Shortcut) / n
	} else {
		p := float64(t.testWins) / n
		out["test_win"] = p
		out["ci95"] = 1.96 * math.Sqrt(p*(1-p)/n)
		out["test_mean_home"] = t.testHome / n
		out["others_mean_home"] = t.otherHome / n
	}
	return out
}
