// unosim: UNO experiments.  unosim -players 4 -games N -rules '{...}' -base '{...}' [-test '{...}'] [-allsame]
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"math/rand"
	"os"
	"runtime"
	"sort"
	"sync"
)

type Summary struct {
	Games        int     `json:"games"`
	TestWinRate  float64 `json:"test_win_rate"`
	CI95         float64 `json:"ci95"`
	Fair         float64 `json:"fair_share"`
	MeanTurns    float64 `json:"mean_turns"`
	MedianTurns  float64 `json:"median_turns"`
	P90Turns     float64 `json:"p90_turns"`
	FirstSeatWin float64 `json:"first_seat_win"` // player left of the dealer (moves first)
	MeanMaxHit   float64 `json:"mean_max_hit"`
	BigHit10     float64 `json:"share_rounds_with_10plus_draw"`
	MeanPoints   float64 `json:"mean_round_points"`
	Unfinished   float64 `json:"unfinished"`
}

func main() {
	players := flag.Int("players", 4, "")
	games := flag.Int("games", 100000, "")
	seed := flag.Int64("seed", 1, "")
	rulesJ := flag.String("rules", "{}", "")
	baseJ := flag.String("base", "{}", "")
	testJ := flag.String("test", "", "")
	allSame := flag.Bool("allsame", false, "")
	check := flag.Bool("check", false, "engine check: share of opening hands with at least one Wild card")
	flag.Parse()
	if *check {
		rng := rand.New(rand.NewSource(*seed))
		var R0 Rules
		hit := 0
		for k := 0; k < *games; k++ {
			d := newDeck(&R0) // the 7 cards as dealt, before the starting card does anything
			rng.Shuffle(len(d), func(i, j int) { d[i], d[j] = d[j], d[i] })
			hand := []Card{}
			for i := 0; i < 7; i++ {
				hand = append(hand, d[len(d)-1-4*i]) // dealt one at a time to 4 players
			}
			for _, c := range hand {
				if c.isWild() {
					hit++
					break
				}
			}
		}
		fmt.Printf("{\"games\": %d, \"opening_hand_has_wild\": %.5f}\n", *games, float64(hit)/float64(*games))
		return
	}
	var R Rules
	var base, test Policy
	must(json.Unmarshal([]byte(*rulesJ), &R))
	must(json.Unmarshal([]byte(*baseJ), &base))
	test = base
	if *testJ != "" {
		must(json.Unmarshal([]byte(*testJ), &test))
	}
	W := runtime.NumCPU()
	per := (*games + W - 1) / W
	type acc struct {
		wins, firstWins, unfinished, big10 int
		turns                              []int
		maxHit, points                     float64
	}
	accs := make([]acc, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(*seed*104729 + int64(w)))
			a := &accs[w]
			for k := 0; k < per; k++ {
				pols := make([]*Policy, *players)
				for i := range pols {
					pols[i] = &base
				}
				ts := rng.Intn(*players)
				if !*allSame {
					pols[ts] = &test
				}
				dealer := rng.Intn(*players)
				g := NewGame(rng, &R, pols, dealer)
				first := g.cur
				r := g.Play()
				if r.Winner < 0 {
					a.unfinished++
					continue
				}
				if r.Winner == ts {
					a.wins++
				}
				if r.Winner == first {
					a.firstWins++
				}
				if r.MaxHit >= 10 {
					a.big10++
				}
				a.turns = append(a.turns, r.Turns)
				a.maxHit += float64(r.MaxHit)
				a.points += float64(r.Points)
			}
		}(w)
	}
	wg.Wait()
	var s Summary
	var all []int
	wins, first, unf, big := 0, 0, 0, 0
	mh, pts := 0.0, 0.0
	for _, a := range accs {
		wins += a.wins
		first += a.firstWins
		unf += a.unfinished
		big += a.big10
		all = append(all, a.turns...)
		mh += a.maxHit
		pts += a.points
	}
	n := float64(len(all))
	s.Games = per * W
	s.TestWinRate = float64(wins) / n
	s.CI95 = 1.96 * math.Sqrt(s.TestWinRate*(1-s.TestWinRate)/n)
	s.Fair = 1 / float64(*players)
	sort.Ints(all)
	sum := 0
	for _, t := range all {
		sum += t
	}
	s.MeanTurns = float64(sum) / n
	s.MedianTurns = float64(all[len(all)/2])
	s.P90Turns = float64(all[len(all)*9/10])
	s.FirstSeatWin = float64(first) / n
	s.MeanMaxHit = mh / n
	s.BigHit10 = float64(big) / n
	s.MeanPoints = pts / n
	s.Unfinished = float64(unf) / float64(s.Games)
	must(json.NewEncoder(os.Stdout).Encode(s))
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
