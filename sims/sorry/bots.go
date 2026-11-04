package main

import "math"

// Policy: how a bot picks among the legal moves for the card it drew. It sees only the board and its card.
type Policy struct {
	Name      string  `json:"name"`
	Random    bool    `json:"random"`     // pick any legal move
	Rush      float64 `json:"rush"`       // >1: favour the lead pawn (progress^rush); <1: favour back pawns
	Hurt      float64 `json:"hurt"`       // weight on opponents' progress (normal 1; 0 = plays its own race)
	Danger    float64 `json:"danger"`     // weight on the chance an opponent bumps you next turn (normal 0)
	NoSplit   bool    `json:"no_split"`   // never split a 7
	NoBack10  bool    `json:"no_back10"`  // never use a 10 to go back 1 (when forward 10 is possible)
	NoSwitch  bool    `json:"no_switch"`  // never use the 11 to switch
	SwitchLead bool   `json:"switch_lead"` // with an 11, always switch with the most advanced opponent pawn if you can
	SorryLead bool    `json:"sorry_lead"` // with a Sorry!, always bump the most advanced opponent pawn
	StartLate bool    `json:"start_late"` // don't start a new pawn while one is already on the track (if another move exists)
	SafeFirst bool    `json:"safe_first"` // prefer moves that get a pawn into the Safety Zone
	Lead      bool    `json:"lead"`       // always move your front pawn forward when it can
	RandTie   bool    `json:"rand_tie"`   // break exact ties at random (default: first in board order, as in the big run)
	LeadBump  bool    `json:"lead_bump"`  // ...unless another move bumps an opponent
}

func (b *Policy) pv(p int) float64 {
	x := float64(p)
	if b.Rush != 0 && b.Rush != 1 {
		return 65 * pow(x/65, b.Rush)
	}
	return x
}

func pow(x, e float64) float64 {
	if x <= 0 {
		return 0
	}
	switch e {
	case 2:
		return x * x
	case 3:
		return x * x * x
	}
	return math.Pow(x, e)
}

// hit chance from one opponent pawn d squares behind (forward cards) or ahead (4 back, 10 back 1).
var hitBehind [13]float64

func init() {
	for _, d := range []int{1, 2, 3, 5, 7, 8, 10, 11, 12} {
		hitBehind[d] = 4.0 / 45
	}
	hitBehind[1] = 5.0 / 45
}

func (b *Policy) Value(st *State, s int) float64 {
	c := st.Col[s]
	own := 0.0
	for i := 0; i < 4; i++ {
		own += b.pv(progress(c, int(st.Loc[s][i])))
	}
	opp := 0.0
	for q := 0; q < st.N; q++ {
		if q == s {
			continue
		}
		for i := 0; i < 4; i++ {
			opp += float64(progress(st.Col[q], int(st.Loc[q][i])))
		}
	}
	hurt := 1.0
	if b.Hurt != 0 {
		hurt = b.Hurt
	}
	if b.Hurt < 0 {
		hurt = 0
	}
	v := own - hurt*opp/float64(st.N-1)
	if b.Danger > 0 {
		risk := 0.0
		for i := 0; i < 4; i++ {
			l := int(st.Loc[s][i])
			if !isTrack(l) {
				continue
			}
			p := 0.0
			for d := 1; d <= 12; d++ {
				o := st.Occ[(l-d+Track)%Track]
				if o >= 0 && int(o)/4 != s {
					p += hitBehind[d]
				}
			}
			for _, d := range [2]int{4, 1} {
				o := st.Occ[(l+d)%Track]
				if o >= 0 && int(o)/4 != s {
					p += 4.0 / 45
				}
			}
			risk += p * float64(progress(c, l))
		}
		v -= b.Danger * risk
	}
	return v
}

func (b *Policy) Choose(g *Game, s int, v int8, ms []Move, sts []State) (int, bool) {
	st := &g.St
	if b.Random {
		return g.rng.Intn(len(ms)), true
	}
	canFwd := false
	for _, m := range ms {
		if m.Kind == MFwd {
			canFwd = true
		}
	}
	// rule-of-thumb overrides (each one is a single habit)
	if (v == 11 && b.SwitchLead) || (v == CSorry && b.SorryLead) {
		best, bp := -1, -1
		for k, m := range ms {
			if m.Kind == MSwitch || m.Kind == MSorry {
				ts, ti := int(m.T)/4, int(m.T)%4
				if p := progress(st.Col[ts], int(st.Loc[ts][ti])); p > bp {
					best, bp = k, p
				}
			}
		}
		if best >= 0 {
			return best, true
		}
	}
	lead := -1
	if b.Lead { // the pawn furthest along that isn't Home
		bp := -1
		for i := 0; i < 4; i++ {
			l := int(st.Loc[s][i])
			if l != Start && l != HomeSq {
				if p := progress(st.Col[s], l); p > bp {
					lead, bp = i, p
				}
			}
		}
	}
	allowed := func(m Move) bool {
		switch {
		case b.NoSplit && m.Kind == MSplit:
			return false
		case b.NoBack10 && v == 10 && m.Kind == MBack && canFwd:
			return false
		case b.NoSwitch && m.Kind == MSwitch:
			return false
		case b.StartLate && m.Kind == MStart:
			for i := 0; i < 4; i++ {
				if isTrack(int(st.Loc[s][i])) || isSafe(int(st.Loc[s][i])) {
					return false
				}
			}
		}
		return true
	}
	if lead >= 0 && b.LeadBump { // a bump beats the rule
		oppNow := 0
		for q := 0; q < st.N; q++ {
			if q != s {
				oppNow += st.score(q)
			}
		}
		for k := range ms {
			o := 0
			for q := 0; q < st.N; q++ {
				if q != s {
					o += sts[k].score(q)
				}
			}
			if o < oppNow {
				lead = -1
				break
			}
		}
	}
	if lead >= 0 { // move the lead pawn forward if it can
		for pass := 0; pass < 1; pass++ {
			bk, bv := -1, -1e18
			for k, m := range ms {
				if m.Kind == MFwd && int(m.P) == lead && allowed(m) {
					if val := b.Value(&sts[k], s); val > bv {
						bk, bv = k, val
					}
				}
			}
			if bk >= 0 {
				return bk, true
			}
		}
	}
	bestK, bestV, ties := -1, -1e18, 0
	for k, m := range ms {
		if !allowed(m) {
			continue
		}
		val := b.Value(&sts[k], s)
		if b.SafeFirst && entersSafety(st, &sts[k], s) {
			val += 1000
		}
		if val > bestV+1e-9 {
			bestK, bestV, ties = k, val, 1
		} else if b.RandTie && val > bestV-1e-9 {
			ties++
			if g.rng.Intn(ties) == 0 {
				bestK = k
			}
		}
	}
	if bestK < 0 { // every legal move was ruled out by the habit: still must move
		for k := range ms {
			if val := b.Value(&sts[k], s); val > bestV {
				bestK, bestV = k, val
			}
		}
	}
	if v == 11 && !canFwd { // may decline to switch when it can't go forward 11
		if b.NoSwitch || b.Value(st, s) > bestV {
			return 0, false
		}
	}
	return bestK, true
}

func entersSafety(a, b *State, s int) bool {
	na, nb := 0, 0
	for i := 0; i < 4; i++ {
		if isSafe(int(a.Loc[s][i])) || a.Loc[s][i] == HomeSq {
			na++
		}
		if isSafe(int(b.Loc[s][i])) || b.Loc[s][i] == HomeSq {
			nb++
		}
	}
	return nb > na
}

// adult variation helpers
func (b *Policy) keepValue(h []int8, k int) float64 { return 0 }

func (b *Policy) dumpCard(h []int8) int {
	// throw a plain forward card if there is one, keep Sorry!, 11, 1, 2, 4
	pri := map[int8]int{3: 0, 5: 1, 8: 2, 12: 3, 7: 4, 10: 5, 4: 6, 2: 7, 1: 8, 11: 9, CSorry: 10}
	best := 0
	for k, v := range h {
		if pri[v] < pri[h[best]] {
			best = k
		}
	}
	return best
}
