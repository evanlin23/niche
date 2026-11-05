// UNO (Mattel GDJ85, 112 cards) with switchable house rules. Rules: episodes/uno/RULES.md
package main

import "math/rand"

const (
	Skip     = 10
	Reverse  = 11
	DrawTwo  = 12
	Wild     = 13
	WildD4   = 14
	Shuffle  = 15
	Custom   = 16 // blank customizable wild, played as a plain Wild
	WildCol  = 4
	NumKinds = 17
)

type Card struct{ C, K int8 } // colour 0-3 (4 = wild), kind 0-9 numbers or action

func (c Card) isWild() bool { return c.C == WildCol }
func (c Card) points() int {
	switch {
	case c.K <= 9:
		return int(c.K)
	case c.K <= DrawTwo:
		return 20
	case c.K == Shuffle || c.K == Custom:
		return 40 // GDJ85 scoring: Wild Shuffle Hands and Customizable are 40
	default:
		return 50
	}
}

type Rules struct {
	Stack     bool `json:"stack"`         // Draw Two on Draw Two, Wild Draw 4 on Wild Draw 4; penalties add up
	StackMix  bool `json:"stack_mix"`     // also +4 on +2 (and +2 on +4 of matching colour)
	SevenZero bool `json:"seven_zero"`    // 7 swaps hands with a chosen player, 0 rotates all hands
	JumpIn    bool `json:"jump_in"`       // identical card can be played out of turn
	DrawUntil bool `json:"draw_until"`    // draw until you can play (then play it)
	Forced    bool `json:"forced"`        // must play if able
	FreeD4    bool `json:"free_d4"`       // Wild Draw 4 any time, no challenges
	NoShuffle bool `json:"no_shuffle"`    // remove the Wild Shuffle Hands card
	NoCustom  bool `json:"no_custom"`     // remove the 3 blank wilds (older 108-card decks)
	MultiPlay bool `json:"multi"`         // house rule: play several cards of the same NUMBER in one turn; the last one sets the colour
	NoActOut  bool `json:"no_action_out"` // house rule: you can't go out on an action card or a Wild
	UnoCall   bool `json:"uno_call"`      // GDJ85: forget "UNO" and get caught before the next turn -> draw UnoPen
	UnoPen    int  `json:"uno_penalty"`   // 0 = official 2 cards
	Joke      bool `json:"joke_cards"`    // GDJ85 blank-card suggestion: "Tell a joke. If someone laughs, discard down to 1 card. If no one laughs, draw 4" (laugh = coin flip)
	Bounce    bool `json:"bounce"`        // house rule: hit by a Draw Two, play a Reverse of that colour to send it back
	PassEvery bool `json:"pass_every"`    // joke rule: after every turn, everyone passes their whole hand to the next player
}

type Policy struct {
	Name        string  `json:"name"`
	HoldWilds   bool    `json:"hold_wilds"`   // only play a Wild/Wild Draw 4 when nothing else is playable
	AttackSmall int     `json:"attack_small"` // save Skip/Draw cards for when the next player has <= N cards (0 = play any time)
	DumpHigh    bool    `json:"dump_high"`    // prefer high-point cards (for scoring)
	ColorChoice string  `json:"color_choice"` // most | random
	Bluff       float64 `json:"bluff"`        // prob. to play an illegal Wild Draw 4 when it's the only good move
	Challenge   string  `json:"challenge"`    // never | always | smart (challenge when bluff likely) | p30
	JumpProb    float64 `json:"jump_prob"`    // prob. to jump in when able
	StackProb   float64 `json:"stack_prob"`   // prob. to stack when able (vs taking the cards)
	PlayDrawn   bool    `json:"play_drawn"`   // play the drawn card if legal
	Random      float64 `json:"random"`       // prob. of just playing a random legal card
	SwapTarget  string  `json:"swap_target"`  // 7-0: fewest | random
	ChangeColor bool    `json:"change_color"` // prefer switching to my best colour when possible
	Multi       string  `json:"multi"`        // multi-play rule: "" = play every card of that number, "one" = one at a time
	Forget      float64 `json:"forget"`       // prob. of forgetting to say UNO (uno_call rule)
	Catch       float64 `json:"catch"`        // prob. of catching each player who forgot
}

type Game struct {
	rng            *rand.Rand
	R              *Rules
	deck           []Card
	discard        []Card
	hands          [][]Card
	pols           []*Policy
	cur, dir       int
	color          int8
	pending        int  // stacked draw penalty waiting for the current player
	pendKind       int8 // DrawTwo or WildD4
	turns          int
	drawn          []int
	maxHit         int // biggest single penalty taken
	lastD4Ill      bool
	lastD4Who      int
	dry            int // times a draw found no cards left anywhere
	unoCaught      int // forgotten UNO calls that were caught
	multiPlays     int
	jokes, bounces int
}

func newDeck(r *Rules) []Card {
	var d []Card
	for c := int8(0); c < 4; c++ {
		d = append(d, Card{c, 0})
		for k := int8(1); k <= 9; k++ {
			d = append(d, Card{c, k}, Card{c, k})
		}
		for _, k := range []int8{Skip, Reverse, DrawTwo} {
			d = append(d, Card{c, k}, Card{c, k})
		}
	}
	for i := 0; i < 4; i++ {
		d = append(d, Card{WildCol, Wild}, Card{WildCol, WildD4})
	}
	if !r.NoShuffle {
		d = append(d, Card{WildCol, Shuffle})
	}
	if !r.NoCustom {
		d = append(d, Card{WildCol, Custom}, Card{WildCol, Custom}, Card{WildCol, Custom})
	}
	return d
}

func NewGame(rng *rand.Rand, r *Rules, pols []*Policy, dealer int) *Game {
	g := &Game{rng: rng, R: r, pols: pols, dir: 1}
	g.deck = newDeck(r)
	rng.Shuffle(len(g.deck), func(i, j int) { g.deck[i], g.deck[j] = g.deck[j], g.deck[i] })
	n := len(pols)
	g.hands = make([][]Card, n)
	g.drawn = make([]int, n)
	for k := 0; k < 7; k++ {
		for p := 0; p < n; p++ {
			g.hands[p] = append(g.hands[p], g.pop())
		}
	}
	// starting card (Wild Draw 4 goes back in)
	for {
		c := g.pop()
		if c.K == WildD4 {
			g.deck = append([]Card{c}, g.deck...)
			g.rng.Shuffle(len(g.deck), func(i, j int) { g.deck[i], g.deck[j] = g.deck[j], g.deck[i] })
			continue
		}
		g.discard = append(g.discard, c)
		g.color = c.C
		g.cur = (dealer + 1) % n
		switch {
		case c.isWild():
			g.color = g.bestColor(g.cur) // any Wild turned up (incl. Shuffle Hands): player left of dealer picks the colour, no shuffle
		case c.K == DrawTwo:
			g.give(g.cur, 2)
			g.cur = g.next(g.cur)
		case c.K == Skip:
			g.cur = g.next(g.cur)
		case c.K == Reverse:
			g.dir = -1
			g.cur = dealer
		}
		break
	}
	return g
}

func (g *Game) canDraw() bool { return len(g.deck) > 0 || len(g.discard) > 1 }

func (g *Game) pop() Card {
	if len(g.deck) == 0 { // reshuffle the discard pile (all but the top card) into a new draw pile
		top := g.discard[len(g.discard)-1]
		g.deck = append(g.deck, g.discard[:len(g.discard)-1]...)
		g.discard = []Card{top}
		g.rng.Shuffle(len(g.deck), func(i, j int) { g.deck[i], g.deck[j] = g.deck[j], g.deck[i] })
	}
	c := g.deck[len(g.deck)-1]
	g.deck = g.deck[:len(g.deck)-1]
	return c
}

// give draws up to k cards for p. If every card is in someone's hand there is nothing left to draw
// (rare; the real table would be stuck the same way), so the draw just stops. Returns cards drawn.
func (g *Game) give(p, k int) int {
	n := 0
	for ; n < k && g.canDraw(); n++ {
		g.hands[p] = append(g.hands[p], g.pop())
	}
	if n < k {
		g.dry++
	}
	g.drawn[p] += n
	if n > g.maxHit {
		g.maxHit = n
	}
	return n
}

func (g *Game) next(p int) int { n := len(g.hands); return ((p+g.dir)%n + n) % n }

func (g *Game) top() Card { return g.discard[len(g.discard)-1] }

func (g *Game) legal(c Card) bool {
	t := g.top()
	return c.isWild() || c.C == g.color || (c.K == t.K && !t.isWild())
}

func (g *Game) hasColor(p int, col int8) bool {
	for _, c := range g.hands[p] {
		if c.C == col {
			return true
		}
	}
	return false
}

func (g *Game) bestColor(p int) int8 {
	var cnt [4]int
	for _, c := range g.hands[p] {
		if !c.isWild() {
			cnt[c.C]++
		}
	}
	if g.pols[p].ColorChoice == "random" {
		return int8(g.rng.Intn(4))
	}
	best := int8(g.rng.Intn(4))
	for c := int8(0); c < 4; c++ {
		if cnt[c] > cnt[best] {
			best = c
		}
	}
	return best
}

func (g *Game) remove(p, i int) Card {
	c := g.hands[p][i]
	h := g.hands[p]
	h[i] = h[len(h)-1]
	g.hands[p] = h[:len(h)-1]
	return c
}

func (g *Game) shuffleHands(player int) {
	var all []Card
	for p := range g.hands {
		all = append(all, g.hands[p]...)
		g.hands[p] = g.hands[p][:0]
	}
	g.rng.Shuffle(len(all), func(i, j int) { all[i], all[j] = all[j], all[i] })
	p := g.next(player)
	for _, c := range all {
		g.hands[p] = append(g.hands[p], c)
		p = g.next(p)
	}
}

// ---------------------------------------------------------------- decisions
func (g *Game) choose(p int) int { // index into hand, -1 = draw
	pol := g.pols[p]
	h := g.hands[p]
	var legalIdx []int
	for i, c := range h {
		if g.legal(c) {
			if c.K == WildD4 && !g.R.FreeD4 && g.hasColor(p, g.color) {
				continue // illegal Wild Draw 4 handled by bluff below
			}
			if !g.canOut(p, c) {
				continue
			}
			legalIdx = append(legalIdx, i)
		}
	}
	if len(legalIdx) == 0 {
		if pol.Bluff > 0 && !g.R.FreeD4 {
			for i, c := range h {
				if c.K == WildD4 && g.rng.Float64() < pol.Bluff {
					return i
				}
			}
		}
		return -1
	}
	if pol.Random > 0 && g.rng.Float64() < pol.Random {
		return legalIdx[g.rng.Intn(len(legalIdx))]
	}
	nextN := len(g.hands[g.next(p)])
	best, bestS := -1, -1e9
	for _, i := range legalIdx {
		c := h[i]
		s := g.rng.Float64() * 0.5
		if c.isWild() && pol.HoldWilds {
			s -= 10
		}
		if (c.K == Skip || c.K == DrawTwo || c.K == WildD4) && pol.AttackSmall > 0 {
			if nextN <= pol.AttackSmall {
				s += 5
			} else {
				s -= 3
			}
		}
		if pol.DumpHigh {
			s += float64(c.points()) / 10
		}
		if pol.ChangeColor && !c.isWild() && c.C != g.color {
			if g.countColor(p, c.C) > g.countColor(p, g.color) {
				s += 2
			}
		}
		if s > bestS {
			bestS, best = s, i
		}
	}
	if g.R.Forced || best >= 0 {
		return best
	}
	return -1
}

func (g *Game) countColor(p int, col int8) int {
	n := 0
	for _, c := range g.hands[p] {
		if c.C == col {
			n++
		}
	}
	return n
}

func (g *Game) wantsChallenge(victim, player int) bool {
	switch g.pols[victim].Challenge {
	case "always":
		return true
	case "smart": // bluffs happen when the player had the colour: more likely with bigger hands
		return len(g.hands[player]) >= 4
	case "p30":
		return g.rng.Float64() < 0.3
	}
	return false
}

// ---------------------------------------------------------------- play
type Result struct {
	Winner, Turns, MaxHit, Points, Dry, UnoCaught, Multi int
	Drawn                                                []int
}

// canOut: house rule "no going out on an action card or a Wild" (only matters for a player's last card).
func (g *Game) canOut(p int, c Card) bool {
	return !(g.R.NoActOut && len(g.hands[p]) == 1 && c.K > 9)
}

// play = the card play itself, then the UNO call (house/official penalty when forgotten and caught).
func (g *Game) play(p, i int) (won bool) {
	if g.playCore(p, i) {
		return true
	}
	if g.R.UnoCall && len(g.hands[p]) == 1 && g.rng.Float64() < g.pols[p].Forget {
		for q := range g.hands {
			if q != p && g.rng.Float64() < g.pols[q].Catch {
				pen := g.R.UnoPen
				if pen == 0 {
					pen = 2
				}
				g.give(p, pen)
				g.unoCaught++
				break
			}
		}
	}
	return false
}

func (g *Game) playCore(p, i int) (won bool) {
	c := g.remove(p, i)
	illegalD4 := c.K == WildD4 && !g.R.FreeD4 && g.hasColor(p, g.color)
	if g.R.MultiPlay && c.K <= 9 && g.pols[p].Multi != "one" {
		// every other card of the same number goes down too; the last one played sets the colour
		group := []Card{c}
		for k := len(g.hands[p]) - 1; k >= 0; k-- {
			if g.hands[p][k].K == c.K && !g.hands[p][k].isWild() {
				group = append(group, g.remove(p, k))
			}
		}
		if len(group) > 1 {
			last := g.rng.Intn(len(group))
			if g.pols[p].ChangeColor { // finish on the colour I hold the most of
				best := -1
				for k, x := range group {
					if n := g.countColor(p, x.C); n > best {
						best, last = n, k
					}
				}
			}
			group[last], group[len(group)-1] = group[len(group)-1], group[last]
			g.discard = append(g.discard, group[:len(group)-1]...)
			c = group[len(group)-1]
			g.multiPlays++
		}
	}
	g.discard = append(g.discard, c)
	if c.isWild() {
		g.color = g.bestColor(p)
	} else {
		g.color = c.C
	}
	if c.K == Shuffle {
		g.shuffleHands(p)
	}
	if g.R.Joke && c.K == Custom && len(g.hands[p]) > 0 {
		if g.rng.Intn(2) == 0 { // somebody laughed: discard down to one card (under the top card)
			keep := g.rng.Intn(len(g.hands[p]))
			top := g.discard[len(g.discard)-1]
			g.discard = g.discard[:len(g.discard)-1]
			for k, x := range g.hands[p] {
				if k != keep {
					g.discard = append(g.discard, x)
				}
			}
			g.discard = append(g.discard, top)
			g.hands[p] = []Card{g.hands[p][keep]}
		} else {
			g.give(p, 4)
		}
		g.jokes++
	}
	if len(g.hands[p]) == 0 {
		// a final Draw Two / Draw 4 still makes the next player draw (affects points)
		if c.K == DrawTwo {
			g.give(g.next(p), 2+g.pending)
		} else if c.K == WildD4 {
			g.give(g.next(p), 4+g.pending)
		}
		return true
	}
	if g.R.SevenZero && !c.isWild() {
		if c.K == 7 {
			t := g.swapTarget(p)
			g.hands[p], g.hands[t] = g.hands[t], g.hands[p]
		} else if c.K == 0 {
			n := len(g.hands)
			nh := make([][]Card, n)
			for q := 0; q < n; q++ {
				nh[g.nextFrom(q)] = g.hands[q]
			}
			g.hands = nh
		}
	}
	nx := g.next(p)
	switch c.K {
	case Skip:
		g.cur = g.next(nx)
	case Reverse:
		g.dir = -g.dir
		if len(g.hands) == 2 {
			g.cur = p
		} else {
			g.cur = g.next(p)
		}
	case DrawTwo, WildD4:
		amt := 2
		if c.K == WildD4 {
			amt = 4
		}
		if g.R.Stack {
			g.pending += amt
			g.pendKind = c.K
			g.cur = nx
			return false
		}
		if c.K == WildD4 && !g.R.FreeD4 && g.wantsChallenge(nx, p) {
			if illegalD4 {
				g.give(p, 4) // guilty: player draws instead, victim plays normally
				g.cur = nx
				return false
			}
			g.give(nx, 6)
			g.cur = g.next(nx)
			return false
		}
		if g.R.Bounce && c.K == DrawTwo && len(g.hands[nx]) > 1 && g.rng.Float64() < g.pols[nx].StackProb {
			for k, x := range g.hands[nx] {
				if x.K == Reverse && x.C == c.C { // bounce it back: direction flips, the player who played it draws and loses the turn
					g.discard = append(g.discard, g.remove(nx, k))
					g.dir = -g.dir
					g.give(p, amt)
					g.cur = g.next(p)
					g.bounces++
					return false
				}
			}
		}
		g.give(nx, amt)
		g.cur = g.next(nx)
	default:
		g.cur = nx
	}
	return false
}

func (g *Game) nextFrom(q int) int { n := len(g.hands); return ((q+g.dir)%n + n) % n }

func (g *Game) swapTarget(p int) int {
	best := -1
	for q := range g.hands {
		if q == p {
			continue
		}
		if g.pols[p].SwapTarget == "random" {
			if best < 0 || g.rng.Intn(2) == 0 {
				best = q
			}
			continue
		}
		if best < 0 || len(g.hands[q]) < len(g.hands[best]) {
			best = q
		}
	}
	return best
}

func (g *Game) jumpIn() (int, bool) { // returns (player who jumped, won?) or (-1,false)
	t := g.top()
	if t.isWild() || t.K > 9 {
		return -1, false
	}
	for q := range g.hands {
		if q == g.cur {
			continue
		}
		for i, c := range g.hands[q] {
			if c == t && g.rng.Float64() < g.pols[q].JumpProb {
				g.cur = q
				return q, g.play(q, i)
			}
		}
	}
	return -1, false
}

func (g *Game) Play() Result {
	n := len(g.hands)
	for g.turns < 5000 {
		g.turns++
		if g.R.PassEvery && g.turns > 1 {
			nh := make([][]Card, len(g.hands))
			for q := range g.hands {
				nh[g.nextFrom(q)] = g.hands[q]
			}
			g.hands = nh
		}
		p := g.cur
		if g.pending > 0 {
			// stacking: may add a matching draw card, otherwise take the lot
			idx := -1
			if g.rng.Float64() < g.pols[p].StackProb {
				for i, c := range g.hands[p] {
					if (c.K == g.pendKind || (g.R.StackMix && (c.K == DrawTwo || c.K == WildD4) && (c.K == WildD4 || c.C == g.color))) && g.canOut(p, c) {
						idx = i
						break
					}
				}
			}
			if idx >= 0 {
				if g.play(p, idx) {
					return g.result(p)
				}
				continue
			}
			g.give(p, g.pending)
			g.pending = 0
			g.cur = g.next(p)
			continue
		}
		i := g.choose(p)
		if i < 0 {
			for {
				if g.give(p, 1) == 0 {
					break // nothing left to draw
				}
				c := g.hands[p][len(g.hands[p])-1]
				ok := g.legal(c) && !(c.K == WildD4 && !g.R.FreeD4 && g.hasColor(p, g.color))
				if ok && (g.pols[p].PlayDrawn || g.R.Forced || g.R.DrawUntil) {
					i = len(g.hands[p]) - 1
					break
				}
				if !g.R.DrawUntil || ok {
					break
				}
			}
			if i < 0 {
				g.cur = g.next(p)
				continue
			}
		}
		if g.play(p, i) {
			return g.result(p)
		}
		if g.R.JumpIn {
			if q, won := g.jumpIn(); q >= 0 && won {
				return g.result(q)
			}
		}
		_ = n
	}
	return g.result(-1)
}

func (g *Game) result(w int) Result {
	pts := 0
	for q, h := range g.hands {
		if q == w {
			continue
		}
		for _, c := range h {
			pts += c.points()
		}
	}
	return Result{Winner: w, Turns: g.turns, MaxHit: g.maxHit, Points: pts, Drawn: g.drawn, Dry: g.dry, UnoCaught: g.unoCaught, Multi: g.multiPlays}
}
