// eksim: run Exploding Kittens experiments.
//
//	eksim -players 4 -games 1000000 -test '{...policy...}' -base '{...policy...}' [-seed 1]
//	eksim -players 4 -trace -seed 7 -test ... -base ...      (one game, event log)
//
// One "test" bot sits in a uniformly random seat; the others use the "base" policy.
// Output: JSON on stdout.
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

type Event struct {
	Turn   int    `json:"turn"`
	Player int    `json:"p"`
	Ev     string `json:"ev"`
	Arg    int    `json:"arg"`
	Target int    `json:"target"`
	Deck   int    `json:"deck"`
	Hands  []int  `json:"hands"`
}

type Trace struct{ Events []Event }

func (g *Game) log(p int, ev string, arg, target int) {
	if g.trace == nil {
		return
	}
	h := make([]int, len(g.players))
	for i, q := range g.players {
		if q.alive {
			h[i] = q.nCards()
		} else {
			h[i] = -1
		}
	}
	g.trace.Events = append(g.trace.Events, Event{g.turn, p, ev, arg, target, len(g.deck), h})
}

type Summary struct {
	Players                 int       `json:"players"`
	Games                   int       `json:"games"`
	TestWins                int       `json:"test_wins"`
	TestWinRate             float64   `json:"test_win_rate"`
	CI95                    float64   `json:"ci95"`
	FairShare               float64   `json:"fair_share"`
	SeatWinRate             []float64 `json:"seat_win_rate"` // by seat offset from the first player (0 = goes first)
	TestSeatRate            []float64 `json:"test_seat_win_rate"`
	MeanTurns               float64   `json:"mean_turns"`
	TestDefuses             float64   `json:"test_defuses_per_game"`
	TestFirstOut            float64   `json:"test_first_out_rate"`
	TestPlayed              []float64 `json:"test_cards_played_per_game"`
	ExplodeUnderAttackShare float64   `json:"explode_under_attack_share"`
	DefuseAvailOK           float64   `json:"-"`
}

func main() {
	players := flag.Int("players", 4, "number of players")
	games := flag.Int("games", 100000, "games")
	seed := flag.Int64("seed", 1, "seed")
	testJ := flag.String("test", "", "test policy JSON")
	baseJ := flag.String("base", "", "base policy JSON")
	trace := flag.Bool("trace", false, "emit one game's event log")
	allSame := flag.Bool("allsame", false, "everyone uses base policy (seat study)")
	tableJ := flag.String("table", "", "JSON array of policies, one per seat (seats shuffled each game): ranking mode")
	check := flag.Bool("check", false, "sanity check: fraction of games whose first drawn card is a Kitten")
	flag.Parse()

	if *check {
		rng := rand.New(rand.NewSource(*seed))
		p := &Policy{AvoidRisk: 2, FutureRisk: 2, Placement: "top", StealWhen: 2}
		hits := 0
		for k := 0; k < *games; k++ {
			pols := make([]*Policy, *players)
			for i := range pols {
				pols[i] = p
			}
			g := NewGame(rng, pols)
			if g.deck[len(g.deck)-1] == EK {
				hits++
			}
		}
		must(json.NewEncoder(os.Stdout).Encode(map[string]any{"games": *games, "first_draw_kitten": float64(hits) / float64(*games)}))
		return
	}
	if *tableJ != "" {
		var tp []Policy
		must(json.Unmarshal([]byte(*tableJ), &tp))
		n := len(tp)
		workers := runtime.NumCPU()
		per := (*games + workers - 1) / workers
		wins := make([][]int, workers)
		var wg sync.WaitGroup
		for w := 0; w < workers; w++ {
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				rng := rand.New(rand.NewSource(*seed*7919 + int64(w)))
				wins[w] = make([]int, n)
				for k := 0; k < per; k++ {
					perm := rng.Perm(n)
					pols := make([]*Policy, n)
					for seat, pi := range perm {
						pols[seat] = &tp[pi]
					}
					r := NewGame(rng, pols).Play()
					wins[w][perm[r.Winner]]++
				}
			}(w)
		}
		wg.Wait()
		out := []map[string]any{}
		for i := 0; i < n; i++ {
			t := 0
			for w := range wins {
				t += wins[w][i]
			}
			out = append(out, map[string]any{"name": tp[i].Name, "win": float64(t) / float64(per*workers)})
		}
		must(json.NewEncoder(os.Stdout).Encode(map[string]any{"games": per * workers, "table": out}))
		return
	}
	var test, base Policy
	must(json.Unmarshal([]byte(*baseJ), &base))
	if *testJ != "" {
		must(json.Unmarshal([]byte(*testJ), &test))
	} else {
		test = base
	}

	if *trace {
		rng := rand.New(rand.NewSource(*seed))
		pols := make([]*Policy, *players)
		for i := range pols {
			b := base
			pols[i] = &b
		}
		t := test
		pols[0] = &t
		g := NewGame(rng, pols)
		g.trace = &Trace{}
		g.log(-1, "start", g.cur, -1)
		r := g.Play()
		out := map[string]any{"result": r, "events": g.trace.Events, "players": *players}
		must(json.NewEncoder(os.Stdout).Encode(out))
		return
	}

	workers := runtime.NumCPU()
	per := (*games + workers - 1) / workers
	type acc struct {
		wins, n       int
		seat          []int
		tseat, tseen  []int
		turns         int
		defuses       int
		firstOut      int
		played        [NCard]int
		expl, explAtt int
	}
	accs := make([]acc, workers)
	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(*seed*1000003 + int64(w)))
			a := &accs[w]
			a.seat = make([]int, *players)
			a.tseat = make([]int, *players)
			a.tseen = make([]int, *players)
			for k := 0; k < per; k++ {
				pols := make([]*Policy, *players)
				for i := range pols {
					pols[i] = &base
				}
				ts := rng.Intn(*players)
				if !*allSame {
					pols[ts] = &test
				}
				g := NewGame(rng, pols)
				r := g.Play()
				a.n++
				off := (r.Winner - r.FirstPlayer + *players) % *players
				a.seat[off]++
				toff := (ts - r.FirstPlayer + *players) % *players
				a.tseen[toff]++
				if r.Winner == ts {
					a.wins++
					a.tseat[toff]++
				}
				a.turns += r.Turns
				a.expl += r.Explosions
				a.explAtt += r.ExplodeUnderAttack
				tp := g.players[ts]
				a.defuses += tp.stats.Defused[EK]
				if len(r.Order) > 0 && r.Order[0] == ts {
					a.firstOut++
				}
				for c := range tp.stats.Played {
					a.played[c] += tp.stats.Played[c]
				}
			}
		}(w)
	}
	wg.Wait()
	var s Summary
	s.Players = *players
	seat := make([]int, *players)
	tseat := make([]int, *players)
	tseen := make([]int, *players)
	var played [NCard]int
	turns, defuses, firstOut, expl, explAtt := 0, 0, 0, 0, 0
	for _, a := range accs {
		s.Games += a.n
		s.TestWins += a.wins
		turns += a.turns
		expl += a.expl
		explAtt += a.explAtt
		defuses += a.defuses
		firstOut += a.firstOut
		for i := range seat {
			seat[i] += a.seat[i]
			tseat[i] += a.tseat[i]
			tseen[i] += a.tseen[i]
		}
		for c := range played {
			played[c] += a.played[c]
		}
	}
	n := float64(s.Games)
	s.TestWinRate = float64(s.TestWins) / n
	s.CI95 = 1.96 * math.Sqrt(s.TestWinRate*(1-s.TestWinRate)/n)
	s.FairShare = 1 / float64(*players)
	for i := range seat {
		s.SeatWinRate = append(s.SeatWinRate, float64(seat[i])/n)
		if tseen[i] > 0 {
			s.TestSeatRate = append(s.TestSeatRate, float64(tseat[i])/float64(tseen[i]))
		} else {
			s.TestSeatRate = append(s.TestSeatRate, 0)
		}
	}
	s.MeanTurns = float64(turns) / n
	if expl > 0 {
		s.ExplodeUnderAttackShare = float64(explAtt) / float64(expl)
	}
	s.TestDefuses = float64(defuses) / n
	s.TestFirstOut = float64(firstOut) / n
	for c := range played {
		s.TestPlayed = append(s.TestPlayed, float64(played[c])/n)
	}
	must(json.NewEncoder(os.Stdout).Encode(s))
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
