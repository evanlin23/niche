// Human-like Connect 4 bots and match play.
package main

import (
	"math/rand"
)

type Bot struct {
	Name     string  `json:"name"`
	WinBlock bool    `json:"win_block"` // take an immediate win, block an immediate loss
	Center   bool    `json:"center"`    // prefer central columns
	Careful  bool    `json:"careful"`   // never play right under the opponent's winning cell
	Depth    int     `json:"depth"`     // look-ahead plies with a simple evaluation (0 = none)
	Noise    float64 `json:"noise"`     // prob. of a random (legal) move instead
	FirstCol int     `json:"first_col"` // forced opening column 1-7 when moving first (0 = no rule)
}

var centreW = [W]int{1, 2, 3, 4, 3, 2, 1}

func legal(p *Pos) []int {
	var m []int
	for c := 0; c < W; c++ {
		if p.canPlay(c) {
			m = append(m, c)
		}
	}
	return m
}

// static evaluation from the player-to-move's point of view
func eval(p *Pos) int {
	me, op := p.cur, p.cur^p.mask
	s := 3*popcount(winningCells(me, p.mask)) - 3*popcount(winningCells(op, p.mask))
	for c := 0; c < W; c++ {
		s += centreW[c] * (popcount(me&colMask(c)) - popcount(op&colMask(c))) / 2
	}
	return s
}

func search(p Pos, d, alpha, beta int) int {
	for c := 0; c < W; c++ {
		if p.canPlay(c) && p.isWinningMove(c) {
			return 10000 + d
		}
	}
	if p.moves == W*H {
		return 0
	}
	if d == 0 {
		return eval(&p)
	}
	best := -1000000
	for _, c := range order {
		if !p.canPlay(c) {
			continue
		}
		q := p.after(c)
		v := -search(q, d-1, -beta, -alpha)
		if v > best {
			best = v
		}
		if v > alpha {
			alpha = v
		}
		if alpha >= beta {
			break
		}
	}
	return best
}

func (b *Bot) Move(p *Pos, rng *rand.Rand) int {
	moves := legal(p)
	if b.FirstCol > 0 && p.moves == 0 {
		return b.FirstCol - 1
	}
	if b.WinBlock {
		for _, c := range moves {
			if p.isWinningMove(c) {
				return c
			}
		}
		opp := winningCells(p.cur^p.mask, p.mask) & p.possible()
		if opp != 0 {
			for _, c := range moves {
				if opp&colMask(c) != 0 {
					return c
				}
			}
		}
	}
	cand := moves
	if b.Careful {
		nl := nonLosing(p)
		var safe []int
		for _, c := range moves {
			if nl&colMask(c) != 0 {
				safe = append(safe, c)
			}
		}
		if len(safe) > 0 {
			cand = safe
		}
	}
	if b.Noise > 0 && rng.Float64() < b.Noise {
		return cand[rng.Intn(len(cand))]
	}
	if b.Depth > 0 {
		best, bv := cand[0], -1<<30
		for _, c := range cand {
			q := p.after(c)
			v := -search(q, b.Depth-1, -1<<29, 1<<29) + rng.Intn(2)
			if v > bv {
				bv, best = v, c
			}
		}
		return best
	}
	if b.Center {
		tot := 0
		for _, c := range cand {
			tot += centreW[c] * centreW[c]
		}
		r := rng.Intn(tot)
		for _, c := range cand {
			r -= centreW[c] * centreW[c]
			if r < 0 {
				return c
			}
		}
	}
	return cand[rng.Intn(len(cand))]
}

// play one game; returns 1 if first player wins, -1 second, 0 draw
func Game(a, b *Bot, rng *rand.Rand) (int, int) {
	var p Pos
	players := [2]*Bot{a, b}
	for p.moves < W*H {
		c := players[p.moves%2].Move(&p, rng)
		win := p.isWinningMove(c)
		p.play(c)
		if win {
			if p.moves%2 == 1 {
				return 1, p.moves
			}
			return -1, p.moves
		}
	}
	return 0, p.moves
}
