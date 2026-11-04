package main

// A Policy is a bot. Every strategic choice is a parameter so experiments can vary one at a time.
type Policy struct {
	Name string `json:"name"`

	// --- avoiding the Kitten
	AvoidRisk    float64 `json:"avoid_risk"`    // play Skip/Attack when P(top is Kitten) >= this (1 = only when sure)
	PreferAttack bool    `json:"prefer_attack"` // when avoiding: Attack before Skip
	FutureRisk   float64 `json:"future_risk"`   // play See the Future when risk >= this and top unknown (2 = never)
	ShuffleIfEK  bool    `json:"shuffle_if_ek"` // known Kitten on top and no Skip/Attack -> Shuffle
	AttackFree   float64 `json:"attack_free"`   // prob. of using a spare Attack even when safe (aggression)

	// --- after defusing
	Placement string `json:"placement"` // top | second | bottom | random | middle | next (smart top)

	// --- stealing
	PairSteal    bool    `json:"pair_steal"`    // play matching cat pairs to steal
	PairNonCats  bool    `json:"pair_noncats"`  // also pair duplicate action cards (e.g. 2 Futures)
	TripleDefuse bool    `json:"triple_defuse"` // with 3 of a kind, name Defuse
	FavorUse     bool    `json:"favor_use"`     // play Favor
	StealTarget  string  `json:"steal_target"`  // most | random | next
	StealWhen    float64 `json:"steal_when"`    // only steal when risk >= this (0 = any time)

	// --- Nope
	NopeDefend   float64 `json:"nope_defend"`    // prob. to Nope an Attack/Favor/steal aimed at me
	NopeSkipSeen bool    `json:"nope_skip_seen"` // Nope someone's Skip/Shuffle when I know the top card is a Kitten
	Yup          float64 `json:"yup"`            // prob. to Nope back when my action is Noped

	// --- casual noise
	RandomPlay float64 `json:"random_play"` // prob. per step of playing a random playable card
	GiveWorst  bool    `json:"give_worst"`  // Favor: give least valuable card (else random)
}

var value = [NCard]int{EK: 0, Defuse: 100, Nope: 40, Attack: 35, Skip: 30, Future: 20, Shuffle: 18, Favor: 15,
	Cat1: 5, Cat2: 5, Cat3: 5, Cat4: 5, Cat5: 5}

func (pol *Policy) opponents(g *Game, p *Player) []*Player {
	var o []*Player
	for _, q := range g.players {
		if q != p && q.alive {
			o = append(o, q)
		}
	}
	return o
}

func (pol *Policy) pickTarget(g *Game, p *Player) int {
	opp := pol.opponents(g, p)
	if len(opp) == 0 {
		return -1
	}
	switch pol.StealTarget {
	case "random":
		return opp[g.rng.Intn(len(opp))].id
	case "next":
		return g.nextAlive(p.id)
	default: // most cards
		best := opp[0]
		for _, q := range opp {
			if q.nCards() > best.nCards() {
				best = q
			}
		}
		if best.nCards() == 0 {
			return -1
		}
		return best.id
	}
}

func (pol *Policy) decide(g *Game, p *Player) Action {
	risk := g.riskTop(p)
	known := len(p.peek) > 0 || p.kittenAt == 0
	// 1) danger: avoid drawing
	if risk >= pol.AvoidRisk && risk > 0 {
		if pol.PreferAttack && p.hand[Attack] > 0 {
			return Action{Kind: KAttack}
		}
		if p.hand[Skip] > 0 {
			return Action{Kind: KSkip}
		}
		if p.hand[Attack] > 0 {
			return Action{Kind: KAttack}
		}
		if known && risk == 1 && pol.ShuffleIfEK && p.hand[Shuffle] > 0 {
			return Action{Kind: KShuffle}
		}
	}
	// 2) information
	if !known && risk >= pol.FutureRisk && p.hand[Future] > 0 {
		return Action{Kind: KFuture}
	}
	// 3) stealing (prefer triples naming Defuse when we have no spare)
	if risk >= pol.StealWhen {
		if t := pol.pickTarget(g, p); t >= 0 {
			for c := Card(Defuse + 1); c < NCard; c++ {
				if !c.isCat() && !pol.PairNonCats {
					continue
				}
				if pol.TripleDefuse && p.hand[c] >= 3 && (c.isCat() || pol.PairNonCats) {
					return Action{Kind: KTriple, Card: c, Target: t, Named: Defuse}
				}
				if pol.PairSteal && p.hand[c] >= 2 && !(pol.TripleDefuse && p.hand[c] == 3) {
					return Action{Kind: KPair, Card: c, Target: t}
				}
			}
			if pol.FavorUse && p.hand[Favor] > 0 {
				return Action{Kind: KFavor, Target: t}
			}
		}
	}
	// 4) free aggression
	if pol.AttackFree > 0 && p.hand[Attack] > 0 && g.turnsLeft == 1 && g.rng.Float64() < pol.AttackFree {
		return Action{Kind: KAttack}
	}
	// 5) casual noise
	if pol.RandomPlay > 0 && g.rng.Float64() < pol.RandomPlay {
		var opts []Card
		for _, c := range []Card{Attack, Skip, Favor, Shuffle, Future} {
			if p.hand[c] > 0 {
				opts = append(opts, c)
			}
		}
		for c := Cat1; c <= Cat5; c++ {
			if p.hand[c] >= 2 {
				opts = append(opts, c)
			}
		}
		if len(opts) > 0 {
			c := opts[g.rng.Intn(len(opts))]
			opp := pol.opponents(g, p)
			t := opp[g.rng.Intn(len(opp))].id
			switch c {
			case Attack:
				return Action{Kind: KAttack}
			case Skip:
				return Action{Kind: KSkip}
			case Favor:
				if g.players[t].nCards() > 0 {
					return Action{Kind: KFavor, Target: t}
				}
			case Shuffle:
				return Action{Kind: KShuffle}
			case Future:
				if !known {
					return Action{Kind: KFuture}
				}
			default:
				if g.players[t].nCards() > 0 {
					return Action{Kind: KPair, Card: c, Target: t}
				}
			}
		}
	}
	return Action{Pass: true}
}

func (pol *Policy) placeKitten(g *Game, p *Player) int {
	n := len(g.deck)
	// cards I will still draw myself this attack sequence (after this draw)
	own := g.turnsLeft - 1
	if own < 0 {
		own = 0
	}
	switch pol.Placement {
	case "top":
		return 0
	case "second":
		return 1
	case "bottom":
		return n
	case "middle":
		return n / 2
	case "next": // the first card the NEXT player will draw
		if own > n {
			return n
		}
		return own
	case "third":
		return 2
	default:
		return g.rng.Intn(n + 1)
	}
}

func (pol *Policy) giveCard(g *Game, p *Player) Card {
	if !pol.GiveWorst {
		c, _ := g.randomCardFrom(p)
		return c
	}
	best := Card(-1)
	bv := 1 << 30
	for c := Card(0); c < NCard; c++ {
		if p.hand[c] == 0 {
			continue
		}
		v := value[c]
		if c.isCat() && p.hand[c] >= 2 {
			v += 10 // don't break a pair
		}
		if v < bv {
			bv, best = v, c
		}
	}
	return best
}

func (pol *Policy) wantsNope(g *Game, me, actor *Player, k Kind) bool {
	switch k {
	case KAttack, KFavor, KPair, KTriple:
		return g.rng.Float64() < pol.NopeDefend
	}
	return false
}

func (pol *Policy) wantsThirdPartyNope(g *Game, me, actor *Player, k Kind) bool {
	if !pol.NopeSkipSeen {
		return false
	}
	if k == KSkip || k == KShuffle {
		return len(me.peek) > 0 && me.peek[0] == EK
	}
	return false
}

func (pol *Policy) wantsYup(g *Game, me *Player, k Kind) bool {
	return g.rng.Float64() < pol.Yup
}
