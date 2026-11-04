package main

// Board geometry (Hasbro classic Sorry!): 60 track squares, numbered clockwise. Side c (c = 0..3) runs from corner
// 15c to corner 15c+15. On each side, counted from the corner: a 4-square slide from square 1 to 4, the colour's
// Safety Zone entry at square 2, its Start exit circle at square 4 (end of the short slide), and a 5-square slide
// from square 9 to 13. The slides on side c are colour c. Safety Zone: 5 squares, then Home.
// (Margin squares and Safety Zone length: Hasbro B3218 text; slide lengths/positions: counted on the printed
// board diagram in Hasbro A5065.)

const (
	Track  = 60
	Start  = -1
	Safe1  = 101 // safety squares 101..105
	HomeSq = 106
)

func exitSq(c int) int  { return 15*c + 4 }
func entrySq(c int) int { return 15*c + 2 }

var slideOwner [Track]int8 // colour of the slide that starts on this square, or -1
var slideEnd [Track]int8

func init() {
	for i := range slideOwner {
		slideOwner[i] = -1
	}
	for c := 0; c < 4; c++ {
		slideOwner[15*c+1], slideEnd[15*c+1] = int8(c), int8(15*c+4)
		slideOwner[15*c+9], slideEnd[15*c+9] = int8(c), int8(15*c+13)
	}
}

func isTrack(l int) bool { return l >= 0 && l < Track }
func isSafe(l int) bool  { return l >= Safe1 && l < HomeSq }

// progress: 0 in Start, 65 at Home = 65 minus the forward moves still needed.
func progress(c, l int) int {
	switch {
	case l == Start:
		return 0
	case l == HomeSq:
		return 65
	case isSafe(l):
		return 59 + (l - Safe1 + 1)
	}
	rem := (entrySq(c) - l + Track) % Track // steps to the entry square
	return 65 - (rem + 6)
}

// fwd: square reached moving forward n from l for colour c; ok=false if it would pass Home.
func fwd(c, l, n int) (int, bool) {
	for k := 0; k < n; k++ {
		switch {
		case l == HomeSq:
			return 0, false
		case isSafe(l):
			l++
		case l == entrySq(c):
			l = Safe1
		default:
			l = (l + 1) % Track
		}
	}
	return l, true
}

// back: square reached moving backward n (never into a Safety Zone; out of one is fine).
func back(c, l, n int) int {
	for k := 0; k < n; k++ {
		switch {
		case l == Safe1:
			l = entrySq(c)
		case isSafe(l):
			l--
		default:
			l = (l - 1 + Track) % Track
		}
	}
	return l
}
