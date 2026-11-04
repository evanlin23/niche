package main

import "math/rand"

type Rules struct {
	FixedRounds bool `json:"fixed_rounds"` // Variation 1: 10 rounds, everyone advances, lowest score wins
	MaxPhase    int  `json:"max_phase"`    // Variation 2: shorter game (0 = 10)
	PerGroupNat bool `json:"per_group_natural"` // house rule: every set/run needs a numbered card (affects nothing for bots that never lay all-Wild groups)
}

type Player struct {
	H       Hand
	Phase   int // phase being attempted (1..10), 11 = done
	Laid    bool
	Score   int
	Skipped bool // a Skip card sits in front of this player
	Pol     *Policy
	Took    [14]bool // numbers this player took from the discard pile this round (public)
	LaidTurn int
	JustTook uint8 // card taken from the discard pile this turn (255 = drew from the pile)
}

type Stats struct {
	Attempts  [11]int // rounds started on each phase
	Completes [11]int
	Rounds    int
	Turns     int
	Unfinished int
	LayTurn   [11]int // sum of the player's own turn number when the phase was laid
}

type Game struct {
	R       *Rules
	rng     *rand.Rand
	P       []Player
	draw    []uint8
	disc    []uint8
	table   []Group
	dealer  int
	round   int
	cur     int
	skipFromStart bool
	St      *Stats
	track   []bool // which seats feed Stats (nil = all)
}

func NewGame(rng *rand.Rand, R *Rules, pols []*Policy, dealer int, st *Stats) *Game {
	g := &Game{R: R, rng: rng, dealer: dealer, St: st}
	g.P = make([]Player, len(pols))
	for i := range g.P {
		g.P[i].Phase = 1
		g.P[i].Pol = pols[i]
	}
	g.draw = make([]uint8, 0, 108)
	g.disc = make([]uint8, 0, 108)
	g.table = make([]Group, 0, 16)
	return g
}

func (g *Game) maxPhase() int {
	if g.R.MaxPhase > 0 {
		return g.R.MaxPhase
	}
	return 10
}

func (g *Game) n() int { return len(g.P) }

func (g *Game) deal() {
	g.draw = g.draw[:0]
	g.draw = append(g.draw, newDeckCached...)
	g.rng.Shuffle(len(g.draw), func(i, j int) { g.draw[i], g.draw[j] = g.draw[j], g.draw[i] })
	g.disc = g.disc[:0]
	g.table = g.table[:0]
	n := g.n()
	for i := range g.P {
		p := &g.P[i]
		p.H.Reset()
		p.Laid = false
		p.Skipped = false
		p.Took = [14]bool{}
		p.LaidTurn = 0
	}
	for k := 0; k < 10; k++ { // one at a time, starting left of the dealer
		for j := 1; j <= n; j++ {
			p := &g.P[(g.dealer+j)%n]
			p.H.Add(g.pop())
		}
	}
	top := g.pop()
	g.disc = append(g.disc, top)
	g.skipFromStart = top == Skip
}

var newDeckCached = newDeck()

func (g *Game) pop() uint8 {
	if len(g.draw) == 0 {
		g.reshuffle()
		if len(g.draw) == 0 {
			return 255
		}
	}
	c := g.draw[len(g.draw)-1]
	g.draw = g.draw[:len(g.draw)-1]
	return c
}

// Not in the sheet: when the draw pile runs out, shuffle the discards (except the top card) into a new pile.
func (g *Game) reshuffle() {
	if len(g.disc) <= 1 {
		return
	}
	top := g.disc[len(g.disc)-1]
	g.draw = append(g.draw[:0], g.disc[:len(g.disc)-1]...)
	g.disc = append(g.disc[:0], top)
	g.rng.Shuffle(len(g.draw), func(i, j int) { g.draw[i], g.draw[j] = g.draw[j], g.draw[i] })
}

func (g *Game) topDiscard() (uint8, bool) {
	if len(g.disc) == 0 {
		return 0, false
	}
	return g.disc[len(g.disc)-1], true
}

// PlayRound plays one round; returns the seat that went out (-1 if the round was abandoned).
func (g *Game) PlayRound() int {
	g.deal()
	n := g.n()
	g.round++
	for i := range g.P {
		if g.P[i].Phase <= g.maxPhase() && g.tracked(i) {
			g.St.Attempts[g.P[i].Phase]++
		}
	}
	g.cur = (g.dealer + 1) % n
	if g.skipFromStart {
		g.P[g.cur].Skipped = true
	}
	turnNo := make([]int, n)
	out := -1
	for t := 0; t < 4000; t++ {
		p := &g.P[g.cur]
		if p.Skipped {
			p.Skipped = false
			if g.skipFromStart {
				g.skipFromStart = false // the starting Skip is already on the discard pile
			} else {
				g.disc = append(g.disc, Skip)
			}
		} else {
			turnNo[g.cur]++
			if g.turn(g.cur, turnNo[g.cur]) {
				out = g.cur
				break
			}
		}
		g.St.Turns++
		g.cur = (g.cur + 1) % n
	}
	g.St.Rounds++
	if out < 0 {
		g.St.Unfinished++
		g.dealer = (g.dealer + 1) % n
		return -1
	}
	for i := range g.P {
		p := &g.P[i]
		if i != out {
			p.Score += p.H.Points()
		}
		if g.R.FixedRounds {
			if p.Laid && g.tracked(i) {
				g.St.Completes[p.Phase]++
				g.St.LayTurn[p.Phase] += p.LaidTurn
			}
			p.Phase++
			continue
		}
		if p.Laid {
			if g.tracked(i) {
				g.St.Completes[p.Phase]++
				g.St.LayTurn[p.Phase] += p.LaidTurn
			}
			p.Phase++
		}
	}
	g.dealer = (g.dealer + 1) % n
	return out
}

func (g *Game) tracked(i int) bool { return g.track == nil || g.track[i] }

// Play runs a whole game and returns the winner's seat.
func (g *Game) Play() int {
	mp := g.maxPhase()
	for r := 0; r < 200; r++ {
		g.PlayRound()
		if g.R.FixedRounds {
			if g.round >= mp {
				return g.lowest(nil)
			}
			continue
		}
		var fin []int
		for i := range g.P {
			if g.P[i].Phase > mp {
				fin = append(fin, i)
			}
		}
		if len(fin) == 1 {
			return fin[0]
		}
		if len(fin) > 1 {
			return g.lowest(fin)
		}
	}
	return g.lowest(nil)
}

// lowest score among seats (nil = everyone); exact ties replay the last Phase among the tied players.
func (g *Game) lowest(seats []int) int {
	if seats == nil {
		for i := range g.P {
			seats = append(seats, i)
		}
	}
	best := []int{}
	for _, s := range seats {
		if len(best) == 0 || g.P[s].Score < g.P[best[0]].Score {
			best = []int{s}
		} else if g.P[s].Score == g.P[best[0]].Score {
			best = append(best, s)
		}
	}
	if len(best) == 1 {
		return best[0]
	}
	return g.playoff(best)
}

// playoff: the tied players replay Phase 10; the first to go out wins.
func (g *Game) playoff(seats []int) int {
	pols := make([]*Policy, len(seats))
	for i, s := range seats {
		pols[i] = g.P[s].Pol
	}
	var st Stats
	for k := 0; k < 50; k++ {
		h := NewGame(g.rng, g.R, pols, g.rng.Intn(len(seats)), &st)
		for i := range h.P {
			h.P[i].Phase = g.maxPhase()
		}
		w := h.PlayRound()
		if w >= 0 {
			return seats[w]
		}
	}
	return seats[g.rng.Intn(len(seats))]
}

// turn plays one full turn for seat s; returns true if the player went out.
func (g *Game) turn(s, turnNo int) bool {
	p := &g.P[s]
	bot := p.Pol
	// 1. draw
	p.JustTook = 255
	if top, ok := g.topDiscard(); ok && top != Skip && bot.TakeDiscard(g, s, top) {
		g.disc = g.disc[:len(g.disc)-1]
		p.H.Add(top)
		p.JustTook = top
		if isNum(top) {
			p.Took[num(top)] = true
		}
	} else {
		c := g.pop()
		if c == 255 { // nothing left anywhere (practically impossible)
			if top, ok := g.topDiscard(); ok && top != Skip {
				g.disc = g.disc[:len(g.disc)-1]
				p.H.Add(top)
			}
		} else {
			p.H.Add(c)
		}
	}
	// 2. lay down the Phase
	if !p.Laid && p.Phase <= g.maxPhase() && Complete(p.Phase, &p.H) && bot.LayNow(g, s) {
		gs := Arrange(p.Phase, &p.H, s)
		g.table = append(g.table, gs...)
		p.Laid = true
		p.LaidTurn = turnNo
	}
	// 3. hit
	if p.Laid {
		g.hitAll(s)
		if p.H.n == 0 {
			return true
		}
	}
	// 4. discard
	c, target := bot.Discard(g, s)
	if c == 255 {
		return false // only an unplayable Skip left
	}
	p.H.RemoveCode(c)
	if c == Skip {
		g.P[target].Skipped = true
	} else {
		g.disc = append(g.disc, c)
	}
	return p.H.n == 0 && p.Laid
}

func (g *Game) hitAll(s int) {
	p := &g.P[s]
	for changed := true; changed; {
		changed = false
		for i := 0; i < p.H.n; i++ {
			c := p.H.cards[i]
			if c == Skip || c == Wild {
				continue
			}
			for gi := range g.table {
				gr := &g.table[gi]
				if gr.Owner != s && !p.Pol.HitOthers {
					continue
				}
				if CanHit(c, gr) {
					Hit(c, gr)
					p.H.RemoveCode(c)
					changed = true
					break
				}
			}
			if changed {
				break
			}
		}
	}
	// Wilds last (they fit anywhere).
	for p.H.wild > 0 {
		hit := false
		for gi := range g.table {
			gr := &g.table[gi]
			if (gr.Owner == s || p.Pol.HitOthers) && CanHit(Wild, gr) {
				Hit(Wild, gr)
				p.H.RemoveCode(Wild)
				hit = true
				break
			}
		}
		if !hit {
			break
		}
	}
}

// legal Skip targets: other players without a Skip already in front of them.
func (g *Game) skipTargets(s int, out []int) []int {
	out = out[:0]
	for j := 1; j < g.n(); j++ {
		t := (s + j) % g.n()
		if !g.P[t].Skipped {
			out = append(out, t)
		}
	}
	return out
}
