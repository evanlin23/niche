package main

// Card codes: 0..47 numbered cards, code = (number-1)*4 + colour (colour 0..3).
// 48 = Wild, 49 = Skip. Mattel HHR41 deck: 2 of every number in every colour (96), 8 Wild, 4 Skip = 108.
const (
	Wild   uint8 = 48
	Skip   uint8 = 49
	NCodes       = 50
)

func num(c uint8) int   { return int(c)/4 + 1 }
func color(c uint8) int { return int(c) % 4 }
func isNum(c uint8) bool { return c < 48 }

func points(c uint8) int {
	switch {
	case c == Wild:
		return 25
	case c == Skip:
		return 15
	case num(c) >= 10:
		return 10
	}
	return 5
}

func newDeck() []uint8 {
	d := make([]uint8, 0, 108)
	for code := uint8(0); code < 48; code++ {
		d = append(d, code, code)
	}
	for i := 0; i < 8; i++ {
		d = append(d, Wild)
	}
	for i := 0; i < 4; i++ {
		d = append(d, Skip)
	}
	return d
}

// Hand keeps the cards plus running counts so the phase maths is cheap.
type Hand struct {
	cards [128]uint8
	n     int
	cnt   [14]int8 // by number 1..12 (index 0 and 13 stay 0)
	col   [4]int8  // numbered cards by colour
	code  [NCodes]int8
	wild  int8
	skip  int8
}

func (h *Hand) Add(c uint8) {
	h.cards[h.n] = c
	h.n++
	h.code[c]++
	switch {
	case c == Wild:
		h.wild++
	case c == Skip:
		h.skip++
	default:
		h.cnt[num(c)]++
		h.col[color(c)]++
	}
}

// RemoveCode removes one card with this code (must be present).
func (h *Hand) RemoveCode(c uint8) {
	for i := 0; i < h.n; i++ {
		if h.cards[i] == c {
			h.n--
			h.cards[i] = h.cards[h.n]
			h.code[c]--
			switch {
			case c == Wild:
				h.wild--
			case c == Skip:
				h.skip--
			default:
				h.cnt[num(c)]--
				h.col[color(c)]--
			}
			return
		}
	}
	panic("RemoveCode: card not in hand")
}

func (h *Hand) Reset() { *h = Hand{} }

func (h *Hand) Points() int {
	s := 0
	for i := 0; i < h.n; i++ {
		s += points(h.cards[i])
	}
	return s
}

func (h *Hand) Naturals() int { return h.n - int(h.wild) - int(h.skip) }

// anyCodeWithNumber returns a card code in hand with number n (any colour), or 255.
func (h *Hand) anyCodeWithNumber(n int) uint8 {
	for c := 0; c < 4; c++ {
		code := uint8((n-1)*4 + c)
		if h.code[code] > 0 {
			return code
		}
	}
	return 255
}
