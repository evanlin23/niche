// Connect 4 on a 7x6 board, bitboard representation (Pons-style: 7 bits per column, top bit is a sentinel).
package main

const W, H = 7, 6
const H1 = H + 1

type Pos struct {
	cur, mask uint64 // cur = stones of the player to move, mask = all stones
	moves     int
}

func bottom(col int) uint64       { return 1 << (col * H1) }
func topMask(col int) uint64      { return 1 << (H - 1 + col*H1) }
func colMask(col int) uint64      { return ((1 << H) - 1) << (col * H1) }
func (p *Pos) canPlay(c int) bool { return p.mask&topMask(c) == 0 }

func (p *Pos) play(c int) {
	p.cur ^= p.mask
	p.mask |= p.mask + bottom(c)
	p.moves++
}

func (p Pos) after(c int) Pos { q := p; q.play(c); return q }

func won(b uint64) bool {
	m := b & (b >> H1) // horizontal
	if m&(m>>(2*H1)) != 0 {
		return true
	}
	m = b & (b >> H) // diagonal \
	if m&(m>>(2*H)) != 0 {
		return true
	}
	m = b & (b >> (H + 2)) // diagonal /
	if m&(m>>(2*(H+2))) != 0 {
		return true
	}
	m = b & (b >> 1) // vertical
	return m&(m>>2) != 0
}

// would playing column c win immediately for the player to move?
func (p *Pos) isWinningMove(c int) bool {
	b := p.cur | ((p.mask + bottom(c)) & colMask(c))
	return won(b)
}

// lastMoverWon: after play(), the previous player's stones are p.cur ^ p.mask
func (p *Pos) lastMoverWon() bool { return won(p.cur ^ p.mask) }

var boardMask uint64

func init() {
	for c := 0; c < W; c++ {
		boardMask |= colMask(c)
	}
}

func popcount(x uint64) int {
	n := 0
	for ; x != 0; x &= x - 1 {
		n++
	}
	return n
}

// cells where the player with stones b would complete four (Pons' compute_winning_position)
func winningCells(b, mask uint64) uint64 {
	r := (b << 1) & (b << 2) & (b << 3) // vertical
	for _, d := range []uint{H1, H, H + 2} {
		p := (b << d) & (b << (2 * d))
		r |= p & (b << (3 * d))
		r |= p & (b >> d)
		p = (b >> d) & (b >> (2 * d))
		r |= p & (b << d)
		r |= p & (b >> (3 * d))
	}
	return r & (boardMask ^ mask)
}

func (p *Pos) possible() uint64 { return (p.mask + bottomRow) & boardMask }

var bottomRow uint64

func init() {
	for c := 0; c < W; c++ {
		bottomRow |= bottom(c)
	}
}
