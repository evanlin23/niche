// Battleship (Hasbro classic): 10x10, fleet 5,4,3,3,2. Placement strategies vs hunting strategies.
package main

import "math/rand"

const N = 10

var Fleet = []int{5, 4, 3, 3, 2}

type Board [2]uint64 // 100 cells: cell i -> word i/64, bit i%64

func (b *Board) set(i int)        { b[i>>6] |= 1 << uint(i&63) }
func (b Board) has(i int) bool    { return b[i>>6]>>uint(i&63)&1 == 1 }
func (b Board) and(o Board) Board { return Board{b[0] & o[0], b[1] & o[1]} }
func (b Board) or(o Board) Board  { return Board{b[0] | o[0], b[1] | o[1]} }
func (b Board) empty() bool       { return b[0] == 0 && b[1] == 0 }

// all placements of a ship of length L
var placements = map[int][]Board{}
var cellsOf = map[int][][]int{}

func init() {
	for _, L := range []int{2, 3, 4, 5} {
		for r := 0; r < N; r++ {
			for c := 0; c+L <= N; c++ {
				var b Board
				var cs []int
				for k := 0; k < L; k++ {
					b.set(r*N + c + k)
					cs = append(cs, r*N+c+k)
				}
				placements[L] = append(placements[L], b)
				cellsOf[L] = append(cellsOf[L], cs)
				var v Board
				var vs []int
				for k := 0; k < L; k++ {
					v.set((c+k)*N + r)
					vs = append(vs, (c+k)*N+r)
				}
				placements[L] = append(placements[L], v)
				cellsOf[L] = append(cellsOf[L], vs)
			}
		}
	}
}

// ---------------------------------------------------------------- placement strategies
type Placer struct {
	Name string  `json:"name"`
	Mode string  `json:"mode"` // random | edges | center | cluster | spread | corners
	Bias float64 `json:"bias"` // strength of preference (0 = uniform)
}

func edgeScore(cs []int) float64 {
	s := 0.0
	for _, i := range cs {
		r, c := i/N, i%N
		d := min4(r, c, N-1-r, N-1-c)
		s += float64(4 - min(d, 4))
	}
	return s / float64(len(cs))
}
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
func min4(a, b, c, d int) int { return min(min(a, b), min(c, d)) }

func (p *Placer) Place(rng *rand.Rand) ([]Board, Board) {
	for {
		var occ Board
		ships := make([]Board, len(Fleet))
		ok := true
		for si, L := range Fleet {
			ps, cs := placements[L], cellsOf[L]
			// weighted choice among non-overlapping placements
			var cand []int
			var w []float64
			tot := 0.0
			for k, b := range ps {
				if !b.and(occ).empty() {
					continue
				}
				if p.Mode == "spread" && touches(cs[k], occ) {
					continue
				}
				wt := 1.0
				switch p.Mode {
				case "edges":
					wt = 1 + p.Bias*edgeScore(cs[k])
				case "center":
					wt = 1 + p.Bias*(4-edgeScore(cs[k]))
				case "corners":
					r, c := cs[k][0]/N, cs[k][0]%N
					if (r < 3 || r > 6) && (c < 3 || c > 6) {
						wt = 1 + p.Bias
					}
				case "cluster":
					if si > 0 && touches(cs[k], occ) {
						wt = 1 + p.Bias
					}
				}
				cand = append(cand, k)
				w = append(w, wt)
				tot += wt
			}
			if len(cand) == 0 {
				ok = false
				break
			}
			x := rng.Float64() * tot
			pick := cand[len(cand)-1]
			for j, k := range cand {
				x -= w[j]
				if x <= 0 {
					pick = k
					break
				}
			}
			ships[si] = ps[pick]
			occ = occ.or(ps[pick])
		}
		if ok {
			return ships, occ
		}
	}
}

func touches(cs []int, occ Board) bool {
	for _, i := range cs {
		r, c := i/N, i%N
		for _, d := range [][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}} {
			rr, cc := r+d[0], c+d[1]
			if rr >= 0 && rr < N && cc >= 0 && cc < N && occ.has(rr*N+cc) {
				return true
			}
		}
	}
	return false
}

// ---------------------------------------------------------------- hunting strategies
type Hunter struct {
	Name   string `json:"name"`
	Mode   string `json:"mode"`   // random | hunt_target | parity | density
	Labels bool   `json:"labels"` // official rule: told which ship was hit
}

type View struct {
	shot, hit  Board
	hitShip    [100]int8 // ship index for labelled hits (-1 unknown)
	sunk       []bool
	sunkCells  Board
	unresolved []int // hit cells not part of a sunk ship
}

// shots to sink the whole fleet
func (h *Hunter) Play(ships []Board, rng *rand.Rand) int {
	var v View
	v.sunk = make([]bool, len(ships))
	for i := range v.hitShip {
		v.hitShip[i] = -1
	}
	remaining := make([]int, len(ships))
	for i, L := range Fleet {
		remaining[i] = L
	}
	sunkCount, shots := 0, 0
	for sunkCount < len(ships) && shots < 100 {
		c := h.next(&v, rng)
		shots++
		v.shot.set(c)
		hitIdx := -1
		for i, b := range ships {
			if b.has(c) {
				hitIdx = i
				break
			}
		}
		if hitIdx < 0 {
			continue
		}
		v.hit.set(c)
		if h.Labels {
			v.hitShip[c] = int8(hitIdx)
		}
		v.unresolved = append(v.unresolved, c)
		remaining[hitIdx]--
		if remaining[hitIdx] == 0 { // sunk: announced
			v.sunk[hitIdx] = true
			sunkCount++
			v.sunkCells = v.sunkCells.or(ships[hitIdx])
			var keep []int
			for _, u := range v.unresolved {
				if !ships[hitIdx].has(u) {
					keep = append(keep, u)
				}
			}
			v.unresolved = keep
		}
	}
	return shots
}

func (h *Hunter) next(v *View, rng *rand.Rand) int {
	if h.Mode == "density" {
		return h.density(v, rng)
	}
	if h.Mode != "random" && len(v.unresolved) > 0 {
		// target mode: neighbours of unresolved hits (prefer extending a line)
		var cand []int
		for _, u := range v.unresolved {
			r, c := u/N, u%N
			for _, d := range [][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}} {
				rr, cc := r+d[0], c+d[1]
				if rr >= 0 && rr < N && cc >= 0 && cc < N && !v.shot.has(rr*N+cc) {
					cand = append(cand, rr*N+cc)
				}
			}
		}
		if len(cand) > 0 {
			return cand[rng.Intn(len(cand))]
		}
	}
	var open []int
	for i := 0; i < 100; i++ {
		if !v.shot.has(i) && (h.Mode != "parity" || (i/N+i%N)%2 == 0) {
			open = append(open, i)
		}
	}
	if len(open) == 0 {
		for i := 0; i < 100; i++ {
			if !v.shot.has(i) {
				open = append(open, i)
			}
		}
	}
	return open[rng.Intn(len(open))]
}

// probability density: count placements of unsunk ships consistent with what we know
func (h *Hunter) density(v *View, rng *rand.Rand) int {
	var score [100]float64
	misses := Board{v.shot[0] &^ v.hit[0], v.shot[1] &^ v.hit[1]}
	var unres Board
	for _, u := range v.unresolved {
		unres.set(u)
	}
	for si, L := range Fleet {
		if v.sunk[si] {
			continue
		}
		for k, b := range placements[L] {
			if !b.and(misses).empty() || !b.and(v.sunkCells).empty() {
				continue
			}
			cover := 0
			okLabel := true
			for _, c := range cellsOf[L][k] {
				if unres.has(c) {
					if h.Labels && int(v.hitShip[c]) != si {
						okLabel = false
						break
					}
					cover++
				}
			}
			if !okLabel {
				continue
			}
			if h.Labels { // a labelled ship must cover all of its known hits
				need := 0
				for _, u := range v.unresolved {
					if int(v.hitShip[u]) == si {
						need++
					}
				}
				if cover < need {
					continue
				}
			}
			w := 1.0
			if cover > 0 {
				w = 1 + 50*float64(cover)
			}
			for _, c := range cellsOf[L][k] {
				if !v.shot.has(c) {
					score[c] += w
				}
			}
		}
	}
	best, bs := -1, -1.0
	for i := 0; i < 100; i++ {
		if v.shot.has(i) {
			continue
		}
		s := score[i] + rng.Float64()*1e-6
		if s > bs {
			bs, best = s, i
		}
	}
	return best
}
