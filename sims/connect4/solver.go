// Exact solver: negamax + alpha-beta, transposition table, centre-first move ordering, null-window search.
// Score > 0: player to move wins (bigger = sooner), < 0 loses, 0 = draw.
package main

var order = []int{3, 2, 4, 1, 5, 0, 6}

type TT struct {
	keys []uint64
	vals []int8
}

func newTT(bits uint) *TT          { n := 1 << bits; return &TT{make([]uint64, n), make([]int8, n)} }
func (t *TT) put(k uint64, v int8) { i := k % uint64(len(t.keys)); t.keys[i], t.vals[i] = k, v }
func (t *TT) get(k uint64) int8 {
	i := k % uint64(len(t.keys))
	if t.keys[i] == k {
		return t.vals[i]
	}
	return 0
}

type Solver struct {
	tt    *TT
	nodes int64
}

func NewSolver() *Solver { return &Solver{tt: newTT(24)} }

const minScore = -(W*H)/2 + 3
const maxScore = (W*H+1)/2 - 3

func (s *Solver) negamax(p Pos, alpha, beta int) int {
	s.nodes++
	next := nonLosing(&p)
	if next == 0 { // every move lets the opponent win
		return -(W*H - p.moves) / 2
	}
	if p.moves >= W*H-2 {
		return 0
	}
	min := -(W*H - 2 - p.moves) / 2
	if alpha < min {
		alpha = min
		if alpha >= beta {
			return alpha
		}
	}
	maxv := (W*H - 1 - p.moves) / 2
	if v := s.tt.get(p.cur + p.mask); v != 0 {
		maxv = int(v) + minScore - 1
	}
	if beta > maxv {
		beta = maxv
		if alpha >= beta {
			return beta
		}
	}
	// order: more winning cells created first, centre as tie-break
	var cand [W]int
	var sc [W]int
	n := 0
	for i := W - 1; i >= 0; i-- {
		c := order[i]
		mv := next & colMask(c)
		if mv == 0 {
			continue
		}
		k := popcount(winningCells(p.cur|mv, p.mask))
		j := n
		for j > 0 && sc[j-1] > k {
			cand[j], sc[j] = cand[j-1], sc[j-1]
			j--
		}
		cand[j], sc[j] = c, k
		n++
	}
	for i := n - 1; i >= 0; i-- {
		q := p.after(cand[i])
		v := -s.negamax(q, -beta, -alpha)
		if v >= beta {
			return v
		}
		if v > alpha {
			alpha = v
		}
	}
	s.tt.put(p.cur+p.mask, int8(alpha-minScore+1))
	return alpha
}

// moves that don't let the opponent win immediately (Pons' possibleNonLosingMoves)
func nonLosing(p *Pos) uint64 {
	poss := p.possible()
	opp := winningCells(p.cur^p.mask, p.mask)
	forced := poss & opp
	if forced != 0 {
		if forced&(forced-1) != 0 {
			return 0 // two threats at once: lost
		}
		poss = forced
	}
	return poss &^ (opp >> 1) // don't play directly below an opponent's winning cell
}

func (s *Solver) Solve(p Pos) int {
	for c := 0; c < W; c++ {
		if p.canPlay(c) && p.isWinningMove(c) {
			return (W*H + 1 - p.moves) / 2
		}
	}
	min, max := -(W*H-p.moves)/2, (W*H+1-p.moves)/2
	for min < max {
		med := min + (max-min)/2
		if med <= 0 && min/2 < med {
			med = min / 2
		} else if med >= 0 && max/2 > med {
			med = max / 2
		}
		r := s.negamax(p, med, med+1)
		if r <= med {
			max = r
		} else {
			min = r
		}
	}
	return min
}
