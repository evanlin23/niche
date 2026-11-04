# Episode backlog (Buh Simulates)

Game-strategy episodes are the main format now; the list below is the older "systems" backlog.

Each: the sim → the hook (first 2 s). Every episode ends by changing one rule to show the fix.

1. ✅ Why Traffic Jams Appear From Nowhere — IDM ring road, brake tap → backward wave; fixes: lower density, one smoother car. Hook: "No accident. No construction. Still stuck."
2. Why Crowds Crush — social-force model at a bottleneck; density heatmap; "faster is slower". Hook: "Pushing makes everyone slower." (needs `sims/socialforce.py`)
3. How Birds Flock Without a Leader — boids, toggle the 3 rules one at a time. Hook: "Three rules. No leader." (`sims/boids.py`)
4. How One Sick Person Becomes a City Outbreak — SEIR on a commuter network; masks / isolation / vaccines. Hook: "Patient zero just got on a train." (`sims/seir.py`)
5. Why the Other Line Always Moves Faster — queue sim, single line vs multiple lines. Hook: "It's not bad luck. It's math."
6. How Ants Find the Shortest Path — pheromone ant-colony optimisation on a maze. Hook: "No ant knows the way." (`sims/pathfinding.py` for the grid)
7. Why the Rich Get Richer (Even When Everything's Fair) — random-exchange money model. Hook: "Everyone starts equal. Watch."
8. Why Cities Segregate — Schelling model, mild preferences → strong segregation. Hook: "Nobody wanted this."
9. Why Forest Fires Are Unpredictable — percolation, critical density ~59%. Hook: "59% trees. Everything burns." (`sims/ca.py`)
10. Why Bubbles Burst — agent-based market with momentum traders. Hook: "Everyone's buying. That's the problem."

Cadence: 1 long-form (8–15 min, ≥8:00 for mid-rolls) per week + 3–4 Shorts cut from it.
