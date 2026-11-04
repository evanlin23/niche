package main

import "math/bits"

// Cards 0..51: card = suit*13 + rank, rank 0 = ace ... 12 = king. Ace is low (A-2-3 is a run, Q-K-A is not).
// A hand is a 52-bit mask.

func rankOf(c int) int  { return c % 13 }
func suitOf(c int) int  { return c / 13 }
func value(c int) int {
	r := rankOf(c) + 1
	if r > 10 {
		return 10
	}
	return r
}

var rankVal = [13]int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10}

// runBest[m]: for one suit's 13-bit mask, the most card value covered by disjoint runs of 3+ consecutive ranks.
var runBest [1 << 13]int16

func init() {
	for m := 0; m < 1<<13; m++ {
		runBest[m] = int16(bestRuns(m, 0))
	}
}

func bestRuns(m, from int) int {
	// classic DP over ranks: either rank `from` is not in a run, or a run starts here with length >= 3
	if from >= 13 {
		return 0
	}
	best := bestRuns(m, from+1)
	v := 0
	for e := from; e < 13 && m&(1<<e) != 0; e++ {
		v += rankVal[e]
		if e-from+1 >= 3 {
			if t := v + bestRunsMemo(m, e+1); t > best {
				best = t
			}
		}
	}
	return best
}

func bestRunsMemo(m, from int) int {
	if from >= 13 {
		return 0
	}
	// runBest is filled in increasing m order, but the suffix of m from `from` is a smaller-or-equal mask only
	// after masking; compute directly (cheap, init only).
	return bestRuns(m&^((1<<from)-1), from)
}

func suitMasks(h uint64) [4]int {
	return [4]int{int(h & 0x1FFF), int(h >> 13 & 0x1FFF), int(h >> 26 & 0x1FFF), int(h >> 39 & 0x1FFF)}
}

var suitVal [1 << 13]int16 // total card value of a suit mask

func init() {
	for m := 0; m < 1<<13; m++ {
		v := 0
		for r := 0; r < 13; r++ {
			if m&(1<<r) != 0 {
				v += rankVal[r]
			}
		}
		suitVal[m] = int16(v)
	}
}

func handValue(h uint64) int {
	return int(suitVal[h&0x1FFF] + suitVal[h>>13&0x1FFF] + suitVal[h>>26&0x1FFF] + suitVal[h>>39&0x1FFF])
}

// Deadwood: the smallest total value of unmatched cards over every way to arrange the hand in melds
// (sets of 3-4 of a rank, runs of 3+ in a suit; a card is in at most one meld).
func Deadwood(h uint64) int {
	total := handValue(h)
	r0, r1, r2, r3 := h&0x1FFF, h>>13&0x1FFF, h>>26&0x1FFF, h>>39&0x1FFF
	three := (r0 & r1 & r2) | (r0 & r1 & r3) | (r0 & r2 & r3) | (r1 & r2 & r3) // ranks held 3+ times
	if three == 0 {
		return total - runsValue(h)
	}
	// ranks with 3+ cards could form a set; for each such rank the options are: no set, all of them,
	// or (with four) any three, leaving one card free for a run
	var opts [4][6]uint64 // cards removed by each option
	var optv [4][6]int
	var nopt [4]int
	n := 0
	for t := three; t != 0; t &= t - 1 {
		r := bits.TrailingZeros64(t)
		b := uint64(1) << r
		cnt := 0
		var m uint64
		if r0&b != 0 {
			cnt++
			m |= b
		}
		if r1&b != 0 {
			cnt++
			m |= b << 13
		}
		if r2&b != 0 {
			cnt++
			m |= b << 26
		}
		if r3&b != 0 {
			cnt++
			m |= b << 39
		}
		k := 0
		opts[n][k], optv[n][k] = 0, 0
		k++
		opts[n][k], optv[n][k] = m, cnt*rankVal[r]
		k++
		if cnt == 4 {
			for x := m; x != 0; x &= x - 1 {
				opts[n][k], optv[n][k] = m&^(x&-x), 3*rankVal[r]
				k++
			}
		}
		nopt[n] = k
		n++
	}
	best := 0
	switch n {
	case 0:
		best = runsValue(h)
	case 1:
		for i := 0; i < nopt[0]; i++ {
			if v := optv[0][i] + runsValue(h&^opts[0][i]); v > best {
				best = v
			}
		}
	default:
		var idx [4]int
		for {
			rm, v := uint64(0), 0
			for j := 0; j < n; j++ {
				rm |= opts[j][idx[j]]
				v += optv[j][idx[j]]
			}
			if t := v + runsValue(h&^rm); t > best {
				best = t
			}
			j := 0
			for ; j < n; j++ {
				idx[j]++
				if idx[j] < nopt[j] {
					break
				}
				idx[j] = 0
			}
			if j == n {
				break
			}
		}
	}
	return total - best
}

func runsValue(h uint64) int {
	return int(runBest[h&0x1FFF] + runBest[h>>13&0x1FFF] + runBest[h>>26&0x1FFF] + runBest[h>>39&0x1FFF])
}

// Melds returns one best arrangement: the melded cards (as one mask per meld) and the deadwood mask.
func Melds(h uint64) ([]uint64, uint64) {
	target := Deadwood(h)
	// search arrangements explicitly (only called when a hand is shown: knock or gin)
	var cands []uint64
	for r := 0; r < 13; r++ {
		m := uint64(0)
		for s := 0; s < 4; s++ {
			if h&(1<<(s*13+r)) != 0 {
				m |= 1 << (s*13 + r)
			}
		}
		c := bits.OnesCount64(m)
		if c >= 3 {
			cands = append(cands, m)
			if c == 4 {
				for x := m; x != 0; x &= x - 1 {
					cands = append(cands, m&^(x&-x))
				}
			}
		}
	}
	for s := 0; s < 4; s++ {
		for a := 0; a < 13; a++ {
			run := uint64(0)
			for e := a; e < 13 && h&(1<<(s*13+e)) != 0; e++ {
				run |= 1 << (s*13 + e)
				if e-a+1 >= 3 {
					cands = append(cands, run)
				}
			}
		}
	}
	var best []uint64
	var dfs func(i int, used uint64, chosen []uint64) bool
	dfs = func(i int, used uint64, chosen []uint64) bool {
		if handValue(h&^used) == target {
			best = append([]uint64(nil), chosen...)
			return true
		}
		for j := i; j < len(cands); j++ {
			if cands[j]&used == 0 && dfs(j+1, used|cands[j], append(chosen, cands[j])) {
				return true
			}
		}
		return false
	}
	dfs(0, 0, nil)
	used := uint64(0)
	for _, m := range best {
		used |= m
	}
	return best, h &^ used
}
