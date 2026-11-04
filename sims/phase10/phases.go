package main

// The ten Phases (Mattel HHR41 sheet):
//  1. 2 sets of 3            6. 1 run of 9
//  2. 1 set of 3 + 1 run of 4  7. 2 sets of 4
//  3. 1 set of 4 + 1 run of 4  8. 7 cards of 1 colour
//  4. 1 run of 7             9. 1 set of 5 + 1 set of 2
//  5. 1 run of 8             10. 1 set of 5 + 1 set of 3
// Sets: 2+ cards of one number (any colours; two sets may share a number).
// Runs: 4+ consecutive numbers, any colours, 1..12 (no wrap). Wilds stand in for anything,
// and a Phase needs at least one numbered card.

const (
	KSets  = iota // two sets: A, B sizes
	KSetRun       // set of A + run of B
	KRun          // run of A
	KColor        // A cards of one colour
)

type PhaseDef struct {
	Kind int
	A, B int
}

var Phases = [11]PhaseDef{
	{},
	{KSets, 3, 3},
	{KSetRun, 3, 4},
	{KSetRun, 4, 4},
	{KRun, 7, 0},
	{KRun, 8, 0},
	{KRun, 9, 0},
	{KSets, 4, 4},
	{KColor, 7, 0},
	{KSets, 5, 2},
	{KSets, 5, 3},
}

func (p PhaseDef) Size() int { return p.A + p.B }

func pos(x int) int {
	if x > 0 {
		return x
	}
	return 0
}

// Missing returns how many natural cards the best arrangement still lacks (before wilds).
func Missing(ph int, h *Hand) int {
	d := Phases[ph]
	switch d.Kind {
	case KSets:
		c1, c2 := 0, 0
		for n := 1; n <= 12; n++ {
			c := int(h.cnt[n])
			if c > c1 {
				c1, c2 = c, c1
			} else if c > c2 {
				c2 = c
			}
		}
		same := pos(d.A + d.B - c1)
		diff := pos(d.A-c1) + pos(d.B-c2)
		if alt := pos(d.A-c2) + pos(d.B-c1); alt < diff {
			diff = alt
		}
		if same < diff {
			return same
		}
		return diff
	case KRun:
		return runMissing(h, d.A)
	case KSetRun:
		// for each run window the best set number is the highest-count number outside the window,
		// or the highest-count number inside it (then it needs one extra copy).
		var pre, suf [14]int8
		for n := 1; n <= 12; n++ {
			pre[n] = pre[n-1]
			if h.cnt[n] > pre[n] {
				pre[n] = h.cnt[n]
			}
		}
		for n := 12; n >= 1; n-- {
			suf[n] = suf[n+1]
			if h.cnt[n] > suf[n] {
				suf[n] = h.cnt[n]
			}
		}
		best := 99
		L := d.B
		for s := 1; s+L-1 <= 12; s++ {
			e := s + L - 1
			gaps, in := 0, int8(0)
			for x := s; x <= e; x++ {
				if h.cnt[x] == 0 {
					gaps++
				} else if h.cnt[x] > in {
					in = h.cnt[x]
				}
			}
			out := pre[s-1]
			if suf[e+1] > out {
				out = suf[e+1]
			}
			if m := gaps + pos(d.A-int(out)); m < best {
				best = m
			}
			if in > 0 {
				if m := gaps + pos(d.A+1-int(in)); m < best {
					best = m
				}
			}
		}
		return best
	case KColor:
		best := 99
		for c := 0; c < 4; c++ {
			if m := pos(d.A - int(h.col[c])); m < best {
				best = m
			}
		}
		return best
	}
	return 99
}

func runMissing(h *Hand, L int) int {
	gaps := 0
	for x := 1; x <= L; x++ {
		if h.cnt[x] == 0 {
			gaps++
		}
	}
	best := gaps
	for s := 2; s+L-1 <= 12; s++ {
		if h.cnt[s-1] == 0 {
			gaps--
		}
		if h.cnt[s+L-1] == 0 {
			gaps++
		}
		if gaps < best {
			best = gaps
		}
	}
	return best
}

// Deficit = cards still needed after using every Wild; a Phase needs at least one numbered card.
func Deficit(ph int, h *Hand) int {
	m := Missing(ph, h)
	d := m - int(h.wild)
	if d < 0 {
		d = 0
	}
	if d == 0 && Phases[ph].Size()-m <= 0 {
		return 1 // only Wilds: needs a numbered card
	}
	return d
}

func Complete(ph int, h *Hand) bool { return Deficit(ph, h) == 0 }

// Group on the table.
type Group struct {
	Owner int
	Kind  int // 0 set, 1 run, 2 colour
	Num   int // set number
	Lo, Hi int // run
	Col   int  // colour group
	N     int  // cards in it
}

// Arrange picks the cards for a complete Phase (fewest Wilds), removes them from the hand and returns the groups.
func Arrange(ph int, h *Hand, owner int) []Group {
	d := Phases[ph]
	switch d.Kind {
	case KSets:
		bestW, ba, bb := 99, 0, 0
		for a := 1; a <= 12; a++ {
			for b := a; b <= 12; b++ {
				var w int
				if a == b {
					w = pos(d.A + d.B - int(h.cnt[a]))
				} else {
					w1 := pos(d.A-int(h.cnt[a])) + pos(d.B-int(h.cnt[b]))
					w2 := pos(d.A-int(h.cnt[b])) + pos(d.B-int(h.cnt[a]))
					if w2 < w1 {
						w = w2
						if w < bestW || (w == bestW && h.cnt[a]+h.cnt[b] > h.cnt[ba]+h.cnt[bb]) {
							bestW, ba, bb = w, b, a
						}
						continue
					}
					w = w1
				}
				if w < bestW || (w == bestW && h.cnt[a]+h.cnt[b] > h.cnt[ba]+h.cnt[bb]) {
					bestW, ba, bb = w, a, b
				}
			}
		}
		if bestW > int(h.wild) {
			panic("Arrange: phase not complete")
		}
		g1 := takeSet(h, ba, d.A, owner)
		if g1.Num == 0 { // all-Wild set: call it the most common number left
			g1.Num = commonNumber(h)
		}
		g2 := takeSet(h, bb, d.B, owner)
		if g2.Num == 0 {
			g2.Num = commonNumber(h)
		}
		return []Group{g1, g2}
	case KRun:
		s := bestWindow(h, d.A)
		return []Group{takeRun(h, s, d.A, owner)}
	case KSetRun:
		best, ba, bs := 99, 0, 0
		L := d.B
		for s := 1; s+L-1 <= 12; s++ {
			for a := 1; a <= 12; a++ {
				m := 0
				for x := s; x < s+L; x++ {
					if h.cnt[x] == 0 {
						m++
					}
				}
				c := int(h.cnt[a])
				if a >= s && a < s+L && c > 0 {
					m += pos(d.A + 1 - c)
				} else if a >= s && a < s+L {
					m += d.A // gap already counted for the run copy
				} else {
					m += pos(d.A - c)
				}
				if m < best {
					best, ba, bs = m, a, s
				}
			}
		}
		if best > int(h.wild) {
			panic("Arrange: phase not complete")
		}
		run := takeRun(h, bs, L, owner)
		set := takeSet(h, ba, d.A, owner)
		if set.Num == 0 {
			set.Num = commonNumber(h)
		}
		return []Group{set, run}
	case KColor:
		bc := 0
		for c := 1; c < 4; c++ {
			if h.col[c] > h.col[bc] {
				bc = c
			}
		}
		need := d.A
		for n := 1; n <= 12 && need > 0; n++ {
			code := uint8((n-1)*4 + bc)
			for h.code[code] > 0 && need > 0 {
				h.RemoveCode(code)
				need--
			}
		}
		for ; need > 0; need-- {
			h.RemoveCode(Wild)
		}
		return []Group{{Owner: owner, Kind: 2, Col: bc, N: d.A}}
	}
	return nil
}

func commonNumber(h *Hand) int {
	b := 12
	for n := 12; n >= 1; n-- {
		if h.cnt[n] > h.cnt[b] {
			b = n
		}
	}
	return b
}

func takeSet(h *Hand, a, k, owner int) Group {
	g := Group{Owner: owner, Kind: 0, Num: a, N: k}
	used := 0
	for used < k && h.cnt[a] > 0 {
		h.RemoveCode(h.anyCodeWithNumber(a))
		used++
	}
	if used == 0 {
		g.Num = 0
	}
	for ; used < k; used++ {
		h.RemoveCode(Wild)
	}
	return g
}

func bestWindow(h *Hand, L int) int {
	best, bs := 99, 1
	for s := 1; s+L-1 <= 12; s++ {
		m := 0
		for x := s; x < s+L; x++ {
			if h.cnt[x] == 0 {
				m++
			}
		}
		if m < best {
			best, bs = m, s
		}
	}
	return bs
}

func takeRun(h *Hand, s, L, owner int) Group {
	for x := s; x < s+L; x++ {
		if h.cnt[x] > 0 {
			h.RemoveCode(h.anyCodeWithNumber(x))
		} else {
			h.RemoveCode(Wild)
		}
	}
	return Group{Owner: owner, Kind: 1, Lo: s, Hi: s + L - 1, N: L}
}

// CanHit: can card c be added to group g?
func CanHit(c uint8, g *Group) bool {
	if c == Skip {
		return false
	}
	switch g.Kind {
	case 0:
		return c == Wild || num(c) == g.Num
	case 1:
		if c == Wild {
			return g.Lo > 1 || g.Hi < 12
		}
		n := num(c)
		return n == g.Lo-1 || n == g.Hi+1
	case 2:
		return c == Wild || color(c) == g.Col
	}
	return false
}

func Hit(c uint8, g *Group) {
	g.N++
	if g.Kind == 1 {
		if c == Wild {
			if g.Hi < 12 {
				g.Hi++
			} else {
				g.Lo--
			}
			return
		}
		if num(c) == g.Hi+1 {
			g.Hi++
		} else {
			g.Lo--
		}
	}
}
