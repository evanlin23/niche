package main

import (
	"encoding/json"
	"flag"
	"math/rand"
	"os"
	"runtime"
	"sync"
)

func main() {
	hJ := flag.String("hunter", `{"mode":"random"}`, "")
	pJ := flag.String("placer", `{"mode":"random"}`, "")
	h2J := flag.String("hunter2", "", "opponent hunter for head-to-head (default same)")
	p2J := flag.String("placer2", "", "opponent placer for head-to-head (default same)")
	games := flag.Int("games", 20000, "")
	seed := flag.Int64("seed", 1, "")
	flag.Parse()
	var H, H2 Hunter
	var P, P2 Placer
	json.Unmarshal([]byte(*hJ), &H)
	json.Unmarshal([]byte(*pJ), &P)
	H2, P2 = H, P
	if *h2J != "" {
		json.Unmarshal([]byte(*h2J), &H2)
	}
	if *p2J != "" {
		json.Unmarshal([]byte(*p2J), &P2)
	}
	W := runtime.NumCPU()
	per := *games / W
	type acc struct {
		shots, shots2    int
		hist             [101]int
		firstWins, aWins int
	}
	accs := make([]acc, W)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(*seed*7907 + int64(w)))
			a := &accs[w]
			for k := 0; k < per; k++ {
				// A = (H hunting P2's fleet), B = (H2 hunting P's fleet)
				shipsB, _ := P2.Place(rng)
				sa := H.Play(shipsB, rng)
				shipsA, _ := P.Place(rng)
				sb := H2.Play(shipsA, rng)
				a.shots += sa
				a.shots2 += sb
				a.hist[sa]++
				if k%2 == 0 { // A moves first: wins if sa <= sb
					if sa <= sb {
						a.aWins++
						a.firstWins++
					}
				} else { // B moves first: B wins if sb <= sa
					if sa < sb {
						a.aWins++
					} else {
						a.firstWins++
					}
				}
			}
		}(w)
	}
	wg.Wait()
	var t acc
	for _, a := range accs {
		t.shots += a.shots
		t.shots2 += a.shots2
		t.firstWins += a.firstWins
		t.aWins += a.aWins
		for i := range a.hist {
			t.hist[i] += a.hist[i]
		}
	}
	n := float64(per * W)
	median := 0
	cum := 0
	for i, c := range t.hist {
		cum += c
		if float64(cum) >= n/2 {
			median = i
			break
		}
	}
	json.NewEncoder(os.Stdout).Encode(map[string]any{"games": per * W, "mean_shots_a": float64(t.shots) / n,
		"mean_shots_b": float64(t.shots2) / n, "median_shots_a": median, "a_win": float64(t.aWins) / n,
		"first_player_win": float64(t.firstWins) / n})
}
