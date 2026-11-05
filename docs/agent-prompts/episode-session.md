# Prompt: one session per episode (the creator works with it directly)

Replace `<GAME>` / `<slug>`, then paste as the first message of a new session on this repo.

---

You are producing the next **Buh Simulates** video: **<GAME>** (`episodes/<slug>/`). The creator talks to you
directly in this session; another session is the orchestrator for the channel.

Read first, in order: `docs/PROCESS.md` (the playbook, follow it step by step), `docs/LESSONS.md` (why every rule
exists), then the reference episode `episodes/exploding-kittens/` (scenes.yaml + web/scenes.js show the visual
standard). Then read everything already in `episodes/<slug>/` and `docs/recording-script-<slug>.txt`.

Your job, in order:
1. Audit what exists for <GAME>: rules sources, engine tests, results totals, every script number traced to data.
   Fix gaps. Tell the creator in a few lines what's solid and what you changed.
2. Bring the script to the house standard (8:20+, hook, primer of the rules, mistakes/house rules, payoff,
   argument-starter ending), then produce ONE clean recording sheet and send it to the creator.
3. Visual rule from the creator: "Everything I say, if it can be shown, should get a scene" (one beat per scene,
   ~5-20 s, never one chart for 40+ s).
4. While they record: build the visuals to the EK v3 standard (always moving, word-anchored, player count
   shown, cards square-on, hard cuts). Local stills + contact sheet before any full render.
4. When the recording arrives: voice pipeline (PROCESS.md §4), creator listen, fixes.
5. Full render on Actions, local assemble (ask the creator to upload the three music mp3s from YouTube Audio
   Library into `music/`), QA, send 1080p + 720p.
6. Upload kit as a GitHub issue (same shape as issue #1), with 3 thumbnails.

Rules: everything in PROCESS.md "Ground rules". Times to the creator in **US Central time**. Commit and push
small commits to your branch; never commit voice audio, music or out/. Make production decisions yourself and
explain briefly; ask only for things only the creator can do (record, upload files, taste calls).
