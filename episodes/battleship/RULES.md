# Battleship: rules digest used by the simulator

Source: official Hasbro instructions, Battleship classic A3264
(https://instructions.hasbro.com/en-in/instruction/battleship -> A32643480_Battleship_INST_RC_FAR.pdf), checked 2026-11-04.
A 4-ship value edition (B1817) also exists; the simulator uses the classic 5-ship fleet.

- 10x10 ocean grid (A-J, 1-10). Fleet: Carrier 5, Battleship 4, Destroyer 3, Submarine 3, Patrol Boat 2.
- Ships horizontal or vertical, never diagonal, no overlapping. (Touching is not forbidden.)
- Players alternate, one shot per turn. On a hit, **the opponent tells you which ship you hit**. When every hole of
  a ship is hit, the owner announces which ship was sunk. First to sink the whole fleet wins.
- Salvo variant: one shot per ship still afloat, fired together.

House rule tested: only say "hit" (not which ship), still announcing sinks.
Head-to-head: shooting at different fleets doesn't interact, so the first player wins if they need no more shots
than the second player.
