package main

import "math/bits"

// 32 playing squares, 0..31 = WCDF squares 1..32. Row r = i/4 (row 0 = Red's back row); in even rows the playing
// squares are columns 0,2,4,6, in odd rows 1,3,5,7 (so each player has a playing square on their near left,
// WCDF rule 1.4). Red (moves first, WCDF 1.13) starts on 0..11 and moves up; White starts on 20..31.

const (
	UL = iota // up-left  (towards White)
	UR
	DL
	DR
)

var nb [32][4]int8 // neighbour square, -1 if off the board
var jp [32][4]int8 // landing square two steps away, -1 if off the board

func sq(r, c int) int {
	if r < 0 || r > 7 || c < 0 || c > 7 || (r+c)%2 != 0 {
		return -1
	}
	return r*4 + c/2
}

func rc(i int) (int, int) {
	r := i / 4
	c := (i % 4) * 2
	if r%2 == 1 {
		c++
	}
	return r, c
}

func init() {
	d := [4][2]int{{1, -1}, {1, 1}, {-1, -1}, {-1, 1}}
	for i := 0; i < 32; i++ {
		r, c := rc(i)
		for k := 0; k < 4; k++ {
			nb[i][k] = int8(sq(r+d[k][0], c+d[k][1]))
			jp[i][k] = int8(sq(r+2*d[k][0], c+2*d[k][1]))
		}
	}
}

const (
	RedKingRow   uint32 = 0xF0000000 // squares 28..31
	WhiteKingRow uint32 = 0x0000000F // squares 0..3
)

// Pos: the pieces. Side 0 = Red, 1 = White.
type Pos struct {
	P    [2]uint32 // pieces of each side
	K    uint32    // kings (either side)
	Side int
}

func StartPos() Pos {
	return Pos{P: [2]uint32{0x00000FFF, 0xFFF00000}}
}

type Move struct {
	From, To int8
	Cap      uint32 // squares of captured pieces
}

var dirsTab = [2][2][]int{{{UL, UR}, {UL, UR, DL, DR}}, {{DL, DR}, {UL, UR, DL, DR}}}

func kingRow(side int) uint32 {
	if side == 0 {
		return RedKingRow
	}
	return WhiteKingRow
}

// overM/landM[d][i]: bit of the square jumped over / landed on from square i in direction d (0 if off board).
var overM, landM [4][32]uint32

func init() {
	for i := 0; i < 32; i++ {
		for d := 0; d < 4; d++ {
			if jp[i][d] >= 0 {
				overM[d][i] = 1 << nb[i][d]
				landM[d][i] = 1 << jp[i][d]
			}
		}
	}
}

// canJump: can the piece on square i jump right now?
func (p *Pos) canJump(i int, opp, empty uint32) bool {
	if p.K&(1<<i) != 0 {
		return (opp&overM[0][i] != 0 && empty&landM[0][i] != 0) || (opp&overM[1][i] != 0 && empty&landM[1][i] != 0) ||
			(opp&overM[2][i] != 0 && empty&landM[2][i] != 0) || (opp&overM[3][i] != 0 && empty&landM[3][i] != 0)
	}
	if p.Side == 0 {
		return (opp&overM[0][i] != 0 && empty&landM[0][i] != 0) || (opp&overM[1][i] != 0 && empty&landM[1][i] != 0)
	}
	return (opp&overM[2][i] != 0 && empty&landM[2][i] != 0) || (opp&overM[3][i] != 0 && empty&landM[3][i] != 0)
}

// Whole-board diagonal steps (row parity decides the shift; see the layout note at the top).
const (
	evenRows uint32 = 0x0F0F0F0F
	oddRows  uint32 = 0xF0F0F0F0
	col0     uint32 = 0x11111111 // k = 0 in each row
	col3     uint32 = 0x88888888 // k = 3 in each row
)

func stepUL(x uint32) uint32 { return (x&evenRows&^col0)<<3 | (x&oddRows)<<4 }
func stepUR(x uint32) uint32 { return (x&evenRows)<<4 | (x&oddRows&^col3)<<5 }
func stepDL(x uint32) uint32 { return (x&evenRows&^col0)>>5 | (x&oddRows)>>4 }
func stepDR(x uint32) uint32 { return (x&evenRows)>>4 | (x&oddRows&^col3)>>3 }

// HasCapture: does the side to move have a jump?
func (p *Pos) HasCapture() bool {
	me, opp := p.P[p.Side], p.P[1-p.Side]
	empty := ^(me | opp)
	up, down := me, me&p.K // Red men move up; White men move down; kings both ways
	if p.Side == 1 {
		up, down = me&p.K, me
	}
	return stepUL(stepUL(up)&opp)&empty != 0 || stepUR(stepUR(up)&opp)&empty != 0 ||
		stepDL(stepDL(down)&opp)&empty != 0 || stepDR(stepDR(down)&opp)&empty != 0
}

// HasSimple: is there any non-capturing move?
func (p *Pos) HasSimple() bool {
	me := p.P[p.Side]
	empty := ^(me | p.P[1-p.Side])
	up, down := me, me&p.K
	if p.Side == 1 {
		up, down = me&p.K, me
	}
	return (stepUL(up)|stepUR(up)|stepDL(down)|stepDR(down))&empty != 0
}

var stepFn = [4]func(uint32) uint32{stepUL, stepUR, stepDL, stepDR}
var backFn = [4]func(uint32) uint32{stepDR, stepDL, stepUR, stepUL} // the opposite step

// Captures appends every complete jump sequence for the side to move.
func (p *Pos) Captures(out []Move) []Move {
	me, opp := p.P[p.Side], p.P[1-p.Side]
	empty := ^(me | opp)
	up, down := me, me&p.K
	if p.Side == 1 {
		up, down = me&p.K, me
	}
	for d := 0; d < 4; d++ {
		movers := up
		if d >= 2 {
			movers = down
		}
		land := stepFn[d](stepFn[d](movers)&opp) & empty
		for l := land; l != 0; l &= l - 1 {
			lb := l & -l
			ob := backFn[d](lb)
			fb := backFn[d](ob)
			from := bits.TrailingZeros32(fb)
			king := p.K&fb != 0
			at := bits.TrailingZeros32(lb)
			occ := (me | opp) &^ fb
			if !king && lb&kingRow(p.Side) != 0 {
				out = appendUnique(out, Move{int8(from), int8(at), ob})
				continue
			}
			out = p.jumpDFS(out, from, at, king, opp, occ, ob)
		}
	}
	return out
}

func (p *Pos) jumpDFS(out []Move, from, at int, king bool, opp, occ, capd uint32) []Move {
	found := false
	ki := 0
	if king {
		ki = 1
	}
	for _, d := range dirsTab[p.Side][ki] {
		over, land := nb[at][d], jp[at][d]
		if land < 0 {
			continue
		}
		ob, lb := uint32(1)<<over, uint32(1)<<land
		if opp&ob == 0 || capd&ob != 0 || occ&lb != 0 {
			continue
		}
		found = true
		nc := capd | ob
		if !king && lb&kingRow(p.Side) != 0 { // a man that reaches the king row stops there (WCDF 1.19)
			out = appendUnique(out, Move{int8(from), land, nc})
			continue
		}
		out = p.jumpDFS(out, from, int(land), king, opp, occ, nc)
	}
	if !found && capd != 0 {
		out = appendUnique(out, Move{int8(from), int8(at), capd})
	}
	return out
}

func appendUnique(out []Move, m Move) []Move {
	for _, x := range out {
		if x == m {
			return out
		}
	}
	return append(out, m)
}

// Simple appends the non-capturing moves.
func (p *Pos) Simple(out []Move) []Move {
	me := p.P[p.Side]
	empty := ^(me | p.P[1-p.Side])
	up, down := me, me&p.K
	if p.Side == 1 {
		up, down = me&p.K, me
	}
	for d := 0; d < 4; d++ {
		movers := up
		if d >= 2 {
			movers = down
		}
		for t := stepFn[d](movers) & empty; t != 0; t &= t - 1 {
			tb := t & -t
			out = append(out, Move{int8(bits.TrailingZeros32(backFn[d](tb))), int8(bits.TrailingZeros32(tb)), 0})
		}
	}
	return out
}

// Legal: captures are compulsory unless optional is set.
func (p *Pos) Legal(out []Move, optional bool) []Move {
	out = p.Captures(out[:0])
	if len(out) > 0 && !optional {
		return out
	}
	return p.Simple(out)
}

// Apply makes the move and passes the turn.
func (p *Pos) Apply(m Move) {
	s := p.Side
	fb, tb := uint32(1)<<m.From, uint32(1)<<m.To
	king := p.K&fb != 0
	p.P[s] = p.P[s]&^fb | tb
	p.P[1-s] &^= m.Cap
	p.K &^= m.Cap | fb
	if king || tb&kingRow(s) != 0 {
		p.K |= tb
	}
	p.Side = 1 - s
}

func (p *Pos) IsManMove(m Move) bool { return p.K&(1<<m.From) == 0 }
