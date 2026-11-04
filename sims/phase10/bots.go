package main

// Policy: how a bot plays. Every decision uses only what a real player can see: its own hand, the discard
// pile, the Phases on the table, each player's Phase number, hand sizes, and which cards players took from
// the discard pile.
type Policy struct {
	Name       string `json:"name"`
	Take       string `json:"take"`        // "improve" (normal): take the discard if it gets you closer; "never"; "loose": also if it pairs up
	Lay        string `json:"lay"`         // "now" (normal) or "late": hold a finished Phase until you can go out the same turn
	SkipUse    string `json:"skip_use"`    // "now" (normal): play Skips right away; "hold": keep them until an opponent has laid down; "last": only as your final card
	SkipTarget string `json:"skip_target"` // "leader" (normal): the player furthest ahead; "next": the player on your left; "random"; "laid"
	Tie        string `json:"tie"`         // "conn" (normal): throw the loosest card; "points": throw the highest-scoring card first
	Watch      bool   `json:"watch"`       // don't throw a number the next player picked up, or a card they could hit
	HitOthers  bool   `json:"hit_others"`  // hit on other players' Phases (normal: true)
	KeepHigh   bool   `json:"keep_high"`   // after laying down, throw the lowest card instead of the highest
}

func (b *Policy) TakeDiscard(g *Game, s int, top uint8) bool {
	p := &g.P[s]
	if b.Take == "never" {
		return false
	}
	if p.Laid {
		if top == Wild {
			return true
		}
		for i := range g.table {
			gr := &g.table[i]
			if (gr.Owner == s || b.HitOthers) && CanHit(top, gr) {
				return true
			}
		}
		return false
	}
	if p.Phase > g.maxPhase() {
		return false
	}
	if top == Wild {
		return true
	}
	h := &p.H
	d0 := Deficit(p.Phase, h)
	addTemp(h, top, 1)
	d1 := Deficit(p.Phase, h)
	addTemp(h, top, -1)
	if d1 < d0 {
		return true
	}
	if b.Take == "loose" && d1 == d0 {
		return conn(p.Phase, h, top) >= 3
	}
	return false
}

// addTemp changes only the counts (not the card list): enough for Missing/Deficit.
func addTemp(h *Hand, c uint8, d int8) {
	switch {
	case c == Wild:
		h.wild += d
	case c == Skip:
		h.skip += d
	default:
		h.cnt[num(c)] += d
		h.col[color(c)] += d
	}
}

// conn: how well a card fits the rest of the hand for this Phase (higher = keep).
func conn(ph int, h *Hand, c uint8) int {
	if !isNum(c) {
		return 100
	}
	n := num(c)
	switch Phases[ph].Kind {
	case KSets:
		return 3 * int(h.cnt[n])
	case KColor:
		return int(h.col[color(c)])
	}
	v := 3 * int(h.cnt[n])
	if Phases[ph].Kind == KRun && h.cnt[n] > 1 {
		v = 3 // duplicates are dead weight in a pure run
	}
	if n > 1 && h.cnt[n-1] > 0 {
		v += 2
	}
	if n < 12 && h.cnt[n+1] > 0 {
		v += 2
	}
	if n > 2 && h.cnt[n-2] > 0 {
		v++
	}
	if n < 11 && h.cnt[n+2] > 0 {
		v++
	}
	return v
}

func (b *Policy) LayNow(g *Game, s int) bool {
	if b.Lay != "late" {
		return true
	}
	p := &g.P[s]
	cp := p.H
	gs := Arrange(p.Phase, &cp, s)
	tab := append(append([]Group(nil), g.table...), gs...)
	for changed := true; changed; {
		changed = false
		for i := 0; i < cp.n; i++ {
			c := cp.cards[i]
			for gi := range tab {
				if (tab[gi].Owner == s || b.HitOthers) && CanHit(c, &tab[gi]) {
					Hit(c, &tab[gi])
					cp.RemoveCode(c)
					changed = true
					break
				}
			}
			if changed {
				break
			}
		}
	}
	return cp.n <= 1
}

func (b *Policy) wantsSkipNow(g *Game, s int) bool {
	p := &g.P[s]
	switch b.SkipUse {
	case "hold":
		if p.Laid || p.H.n <= 2 {
			return true
		}
		for j := range g.P {
			if j != s && g.P[j].Laid {
				return true
			}
		}
		return false
	case "last":
		return p.H.n == int(p.H.skip)
	}
	return true
}

func (b *Policy) skipTarget(g *Game, s int, ts []int) int {
	switch b.SkipTarget {
	case "next":
		return ts[0]
	case "random":
		return ts[g.rng.Intn(len(ts))]
	case "laid":
		for _, t := range ts {
			if g.P[t].Laid {
				return t
			}
		}
	}
	best := ts[0]
	for _, t := range ts[1:] {
		a, c := &g.P[t], &g.P[best]
		if a.Phase > c.Phase || (a.Phase == c.Phase && (btoi(a.Laid) > btoi(c.Laid) ||
			(a.Laid == c.Laid && a.H.n < c.H.n))) {
			best = t
		}
	}
	return best
}

func btoi(x bool) int {
	if x {
		return 1
	}
	return 0
}

// feeds: would throwing card c help the next player?
func (g *Game) feeds(s int, c uint8) bool {
	nx := &g.P[(s+1)%g.n()]
	if c == Wild {
		return true
	}
	if nx.Laid {
		for i := range g.table {
			if CanHit(c, &g.table[i]) {
				return true
			}
		}
		return false
	}
	return nx.Took[num(c)]
}

// Discard chooses the card to throw (and the Skip target). 255 = nothing can be thrown.
func (b *Policy) Discard(g *Game, s int) (uint8, int) {
	p := &g.P[s]
	h := &p.H
	if h.skip > 0 {
		var buf [8]int
		ts := g.skipTargets(s, buf[:])
		if len(ts) > 0 && (b.wantsSkipNow(g, s) || h.n == int(h.skip)) {
			return Skip, b.skipTarget(g, s, ts)
		}
		if h.n == int(h.skip) {
			return 255, 0
		}
	}
	if p.Laid || p.Phase > g.maxPhase() {
		best, bv := uint8(255), -1
		for i := 0; i < h.n; i++ {
			c := h.cards[i]
			if c == Skip || (c == Wild && h.n > int(h.wild)+int(h.skip)) {
				continue
			}
			v := points(c)*16 + num(c)
			if b.KeepHigh {
				v = 1000 - v
			}
			if b.Watch && g.feeds(s, c) {
				v -= 5000
			}
			if v > bv {
				best, bv = c, v
			}
		}
		return best, 0
	}
	ph := p.Phase
	kind := Phases[ph].Kind
	colorPhase := kind == KColor
	best, bk := uint8(255), 1<<30
	var seen [NCodes]bool
	d0 := Deficit(ph, h)
	c2 := int8(0) // second-highest number count (sets: smaller counts never matter)
	if kind == KSets {
		var c1 int8
		for n := 1; n <= 12; n++ {
			if c := h.cnt[n]; c > c1 {
				c1, c2 = c, c1
			} else if c > c2 {
				c2 = c
			}
		}
	}
	for i := 0; i < h.n; i++ {
		c := h.cards[i]
		if c == Skip || c == Wild {
			continue
		}
		key := c
		if !colorPhase {
			key = uint8((num(c) - 1) * 4) // dedupe by number
		}
		if seen[key] {
			continue
		}
		seen[key] = true
		var d int
		if (kind == KRun && h.cnt[num(c)] >= 2) || (kind == KSets && h.cnt[num(c)] < c2) {
			d = d0 // a spare duplicate in a run, or a number too small to matter for sets
		} else {
			addTemp(h, c, -1)
			d = Deficit(ph, h)
			addTemp(h, c, 1)
		}
		cn := conn(ph, h, c)
		pt := points(c)
		// smaller key = throw this one
		var k int
		if b.Tie == "points" {
			k = d*1000000 + (20-pt)*1000 + cn*10
		} else {
			k = d*1000000 + cn*1000 + (20-pt)*10
		}
		if b.Watch && g.feeds(s, c) {
			k += 500000
		}
		k = k*16 + num(c) - 1 // deterministic final tie-break: lower number thrown... (stable)
		if k < bk {
			best, bk = c, k
		}
	}
	if best == 255 { // only Wilds (and maybe Skips we can't play)
		if h.wild > 0 {
			return Wild, 0
		}
		return 255, 0
	}
	return best, 0
}
