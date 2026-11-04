// Exploding Kittens (Original Edition) game engine.
// Rules: episodes/exploding-kittens/RULES.md (official rulebook, 2025 printing).
package main

import "math/rand"

type Card int8

const (
	EK Card = iota
	Defuse
	Attack
	Skip
	Favor
	Shuffle
	Nope
	Future
	Cat1
	Cat2
	Cat3
	Cat4
	Cat5
	NCard
)

var cardNames = [NCard]string{"Exploding Kitten", "Defuse", "Attack", "Skip", "Favor", "Shuffle", "Nope",
	"See the Future", "Cat A", "Cat B", "Cat C", "Cat D", "Cat E"}

func (c Card) String() string { return cardNames[c] }
func (c Card) isCat() bool    { return c >= Cat1 }

// Action kinds that can be Noped
type Kind int8

const (
	KAttack Kind = iota
	KSkip
	KFavor
	KShuffle
	KFuture
	KPair
	KTriple
)

type Player struct {
	id       int
	hand     [NCard]int
	alive    bool
	pol      *Policy
	peek     []Card // known top cards (peek[0] = top) from See the Future; nil = unknown
	kittenAt int    // known position (from top) of a Kitten this player placed; -1 unknown
	stats    PStats
}

type PStats struct {
	Defused, Exploded, Played [NCard]int
	Turns                     int
}

func (p *Player) nCards() int {
	n := 0
	for _, k := range p.hand {
		n += k
	}
	return n
}

type Game struct {
	rng         *rand.Rand
	deck        []Card // deck[len-1] is the TOP
	players     []*Player
	cur         int
	turnsLeft   int
	underAttack bool
	alive       int
	turn        int // global turn counter
	trace       *Trace
	kittensLeft int
}

func NewGame(rng *rand.Rand, pols []*Policy) *Game {
	n := len(pols)
	g := &Game{rng: rng}
	g.players = make([]*Player, n)
	for i := range pols {
		g.players[i] = &Player{id: i, alive: true, pol: pols[i], kittenAt: -1}
	}
	// deck without kittens & defuses
	var deck []Card
	add := func(c Card, k int) {
		for i := 0; i < k; i++ {
			deck = append(deck, c)
		}
	}
	add(Attack, 4)
	add(Skip, 4)
	add(Favor, 4)
	add(Shuffle, 4)
	add(Nope, 5)
	add(Future, 5)
	for c := Cat1; c <= Cat5; c++ {
		add(c, 4)
	}
	// 1 defuse each; extras back in: 2 (only 1 if 5 players)
	for _, p := range g.players {
		p.hand[Defuse]++
	}
	extra := 6 - n
	if extra > 2 {
		extra = 2
	}
	add(Defuse, extra)
	g.shuffleSlice(deck)
	for _, p := range g.players { // deal 7 each
		for k := 0; k < 7; k++ {
			c := deck[len(deck)-1]
			deck = deck[:len(deck)-1]
			p.hand[c]++
		}
	}
	add(EK, n-1)
	g.kittensLeft = n - 1
	g.shuffleSlice(deck)
	g.deck = deck
	g.alive = n
	g.cur = rng.Intn(n)
	g.turnsLeft = 1
	return g
}

func (g *Game) shuffleSlice(d []Card) {
	g.rng.Shuffle(len(d), func(i, j int) { d[i], d[j] = d[j], d[i] })
}

func (g *Game) nextAlive(i int) int {
	n := len(g.players)
	for k := 1; k <= n; k++ {
		j := (i + k) % n
		if g.players[j].alive {
			return j
		}
	}
	return i
}

// ---------------------------------------------------------------- knowledge
func (g *Game) onDraw() {
	for _, p := range g.players {
		if len(p.peek) > 0 {
			p.peek = p.peek[1:]
		}
		if p.kittenAt == 0 {
			p.kittenAt = -1
		} else if p.kittenAt > 0 {
			p.kittenAt--
		}
	}
}

func (g *Game) onShuffle() {
	for _, p := range g.players {
		p.peek = nil
		p.kittenAt = -1
	}
}

func (g *Game) onInsert(placer *Player, pos int) {
	for _, p := range g.players {
		if p == placer {
			if p.peek != nil && pos <= len(p.peek) {
				np := make([]Card, 0, len(p.peek)+1)
				np = append(np, p.peek[:pos]...)
				np = append(np, EK)
				np = append(np, p.peek[pos:]...)
				p.peek = np
			}
			p.kittenAt = pos
		} else {
			// others know a Kitten went in, but not where: only cards above an unknown point stay known
			p.peek = nil
			p.kittenAt = -1
		}
	}
}

// P(top card is a Kitten) from player p's point of view
func (g *Game) riskTop(p *Player) float64 {
	if len(p.peek) > 0 {
		if p.peek[0] == EK {
			return 1
		}
		return 0
	}
	if p.kittenAt == 0 {
		return 1
	}
	n := len(g.deck)
	if n == 0 {
		return 0
	}
	k := g.kittensLeft
	if p.kittenAt > 0 {
		k--
		n--
	}
	if n <= 0 || k <= 0 {
		return 0
	}
	return float64(k) / float64(n)
}

// ---------------------------------------------------------------- nope windows
// returns true if the action is cancelled
func (g *Game) nopeWindow(actor *Player, victim *Player, kind Kind) bool {
	noped := false
	var canceller *Player
	for {
		if !noped {
			canceller = nil
			if victim != nil && victim.alive && victim.hand[Nope] > 0 && victim.pol.wantsNope(g, victim, actor, kind) {
				canceller = victim
			} else {
				for k := 1; k < len(g.players); k++ {
					o := g.players[(actor.id+k)%len(g.players)]
					if o == victim || !o.alive || o.hand[Nope] == 0 {
						continue
					}
					if o.pol.wantsThirdPartyNope(g, o, actor, kind) {
						canceller = o
						break
					}
				}
			}
			if canceller == nil {
				return false
			}
			canceller.hand[Nope]--
			canceller.stats.Played[Nope]++
			g.log(canceller.id, "nope", int(kind), actor.id)
			noped = true
		} else {
			if actor.hand[Nope] > 0 && actor.pol.wantsYup(g, actor, kind) {
				actor.hand[Nope]--
				actor.stats.Played[Nope]++
				g.log(actor.id, "yup", int(kind), -1)
				noped = false
				continue
			}
			return true
		}
	}
}

// ---------------------------------------------------------------- turn engine
const (
	resDraw = iota
	resSkip
	resAttack
)

type Action struct {
	Kind   Kind
	Card   Card // card used (for pairs/triples: which title)
	Target int
	Named  Card
	Pass   bool
}

func (g *Game) take(p *Player, c Card, k int) {
	p.hand[c] -= k
	p.stats.Played[c] += k
}

func (g *Game) randomCardFrom(p *Player) (Card, bool) {
	n := p.nCards()
	if n == 0 {
		return 0, false
	}
	r := g.rng.Intn(n)
	for c := Card(0); c < NCard; c++ {
		if r < p.hand[c] {
			return c, true
		}
		r -= p.hand[c]
	}
	return 0, false
}

func (g *Game) actionPhase(p *Player) int {
	for steps := 0; steps < 40; steps++ {
		a := p.pol.decide(g, p)
		if a.Pass {
			return resDraw
		}
		switch a.Kind {
		case KFuture:
			g.take(p, Future, 1)
			g.log(p.id, "future", -1, -1)
			if !g.nopeWindow(p, nil, KFuture) {
				k := 3
				if len(g.deck) < k {
					k = len(g.deck)
				}
				p.peek = make([]Card, k)
				for i := 0; i < k; i++ {
					p.peek[i] = g.deck[len(g.deck)-1-i]
				}
			}
		case KShuffle:
			g.take(p, Shuffle, 1)
			g.log(p.id, "shuffle", -1, -1)
			if !g.nopeWindow(p, nil, KShuffle) {
				g.shuffleSlice(g.deck)
				g.onShuffle()
			}
		case KSkip:
			g.take(p, Skip, 1)
			g.log(p.id, "skip", -1, -1)
			if !g.nopeWindow(p, nil, KSkip) {
				return resSkip
			}
		case KAttack:
			g.take(p, Attack, 1)
			v := g.players[g.nextAlive(p.id)]
			g.log(p.id, "attack", -1, v.id)
			if !g.nopeWindow(p, v, KAttack) {
				return resAttack
			}
		case KFavor:
			g.take(p, Favor, 1)
			t := g.players[a.Target]
			g.log(p.id, "favor", -1, t.id)
			if !g.nopeWindow(p, t, KFavor) && t.nCards() > 0 {
				c := t.pol.giveCard(g, t)
				t.hand[c]--
				p.hand[c]++
			}
		case KPair:
			g.take(p, a.Card, 2)
			t := g.players[a.Target]
			g.log(p.id, "pair", int(a.Card), t.id)
			if !g.nopeWindow(p, t, KPair) {
				if c, ok := g.randomCardFrom(t); ok {
					t.hand[c]--
					p.hand[c]++
				}
			}
		case KTriple:
			g.take(p, a.Card, 3)
			t := g.players[a.Target]
			g.log(p.id, "triple", int(a.Named), t.id)
			if !g.nopeWindow(p, t, KTriple) && t.hand[a.Named] > 0 {
				t.hand[a.Named]--
				p.hand[a.Named]++
			}
		}
	}
	return resDraw
}

type Result struct {
	Winner      int
	Turns       int
	Order       []int // elimination order (first out first)
	FirstPlayer int
}

func (g *Game) Play() Result {
	res := Result{FirstPlayer: g.cur}
	for g.alive > 1 && g.turn < 2000 {
		p := g.players[g.cur]
		g.turn++
		p.stats.Turns++
		r := g.actionPhase(p)
		switch r {
		case resAttack:
			nt := 2
			if g.underAttack {
				nt = g.turnsLeft + 2
			}
			g.cur = g.nextAlive(p.id)
			g.turnsLeft = nt
			g.underAttack = true
			continue
		case resSkip:
			g.turnsLeft--
		case resDraw:
			c := g.deck[len(g.deck)-1]
			g.deck = g.deck[:len(g.deck)-1]
			g.onDraw()
			if c == EK {
				if p.hand[Defuse] > 0 {
					p.hand[Defuse]--
					p.stats.Defused[EK]++
					pos := p.pol.placeKitten(g, p)
					if pos < 0 {
						pos = 0
					}
					if pos > len(g.deck) {
						pos = len(g.deck)
					}
					idx := len(g.deck) - pos
					g.deck = append(g.deck, 0)
					copy(g.deck[idx+1:], g.deck[idx:])
					g.deck[idx] = EK
					g.onInsert(p, pos)
					g.log(p.id, "defuse", pos, -1)
				} else {
					p.alive = false
					p.stats.Exploded[EK]++
					g.alive--
					g.kittensLeft--
					res.Order = append(res.Order, p.id)
					g.log(p.id, "explode", -1, -1)
					g.cur = g.nextAlive(p.id)
					g.turnsLeft = 1
					g.underAttack = false
					continue
				}
			} else {
				p.hand[c]++
				g.log(p.id, "draw", int(c), -1)
			}
			g.turnsLeft--
		}
		if g.turnsLeft <= 0 {
			g.cur = g.nextAlive(p.id)
			g.turnsLeft = 1
			g.underAttack = false
		}
	}
	for _, p := range g.players {
		if p.alive {
			res.Winner = p.id
		}
	}
	res.Turns = g.turn
	return res
}
