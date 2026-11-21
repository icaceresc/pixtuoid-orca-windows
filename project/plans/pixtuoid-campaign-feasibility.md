# Fantasy campaign: feasibility map and engine design

Base studied: `origin/fantasy/prototype` @ `931f106e` (worktree branch `icaceresc/campaign-feasibility`, read-only; no commits).
Visual evidence produced while studying (uncommitted): `scratch/base_6.png` (floating window, dark-fantasy, 6 agents),
`scratch/floor3_lounge_night.png` (cutaway, wall-free "Lounge" floor variant at 23:00).

Size scale used throughout (agent work, rough): **S** ≤ 2 h · **M** 2–6 h · **L** 6–16 h · **XL** > 16 h.

## Headline

1. **ART ONLY (a):** about 25 items. Most are **M**. Three are **L**: the dungeon set, the camp set and the per-class attacks. Nearly every camp or dungeon piece is a *stand-in* drawn on an existing piece's canvas, so it needs no new layout code. The one prerequisite is that floor 0 and the other floors draw from different art ("role packs", engine B1).
2. **RUST ENGINE (b), the five slice items:**
   - B1 role packs: M
   - B2 campaign seating, so idle agents go to floor 0 and working agents to floor 1 and up: M–L
   - B3 camp layout variant: S
   - B4 per-role look (theme, a dungeon without windows, night): M
   - B5 class to attack animation: M

   That is about 25 h of engine work. Optional items: B6 floor labels (S), B7 auto-follow (S–M), B8 walk-out between floors (M), B9 monster variety (S–M).
3. **NOT WORTH IT (c):** genuinely new furniture kinds, a bespoke camp layout generator, per-class body frames, per-(class × tool) animations, a split view with two floors, opaque stone partitions, subagents drawn as familiars. Each has a cheaper stand-in (see (c)).
4. **Recommended criteria:**
   - Class: a stable hash per agent. This is already free, because the pack's hairstyle pick is a rendezvous hash.
   - Tools: colour only. The existing per-tool glow lights the monster's eyes and runes.
   - Dungeon floors: one fight zone, overflowing to more floors by capacity.
5. **Slice order:**
   - First, in parallel: B2 (core crate) and B1 (scene and binary crates).
   - Then B3, B4 and B6, while the art workers draw the camp and dungeon packs.
   - Then B5 and the per-class attack art.
   - The owlbear needs only a config change: `[[pets]]` with the cat redrawn as the owlbear, listed first so it lands on floor 0.

---

## 1. Floors (how they work today)

**Desks are assigned in core, first come first served, floor 0 first, and are permanent.**
- A desk is `FloorDesk { floor, index }` (`crates/pixtuoid-core/src/state/mod.rs:83`); `AgentSlot.desk: Option<FloorDesk>` (`state/mod.rs:340`).
- `SceneState::seat_unseated` (`state/mod.rs:813-839`) lists free desks floor-major, `(0..MAX_FLOORS).flat_map(|floor| 0..cap[floor])`. It sorts the unseated agents by `(created_at, agent_id)` and zips the two lists. Every seated agent gets `arrived_at = now`, which drives its walk-in.
- **Overflow** is therefore implicit: floor 1 fills only after floor 0 is full. An agent never moves while it keeps its desk. Only a capacity change (`set_capacities` / `take_capacities`, `state/mod.rs:796-810`) or the agent's exit frees a desk.
- `claims_a_desk` (`state/mod.rs:384`) stops an exiting agent from taking a new desk.
- Callers of `seat_unseated`: the reducer at session start, at the exit sweep, and at `set_capacities` (`reducer/mod.rs:1307,1387,1710`), and the remote office (`crates/pixtuoid-core/src/remote.rs:835`). `MAX_FLOORS = 10` (`state/mod.rs:23`).

**Capacities come from the layout of each floor.**
- `floor_capacity(viewport, floor_seed)` = `home_desks.len()` of `SceneLayout::compute` (`crates/pixtuoid-scene/src/floor/mod.rs:43`).
- `floor_seed(i) = i * GOLDEN_GAMMA` (`floor/mod.rs:36`).
- The floating window publishes `floor_caps_for_buffer` (`crates/pixtuoid/src/floating/geometry.rs:268`). Measured: the default 480×320 window seats 6 desks at 1.0× scale factor, 30 at 2.0× (`geometry.rs:589-595`), and 30 in `scratch/base_6.png`.
- The layout is procedural. `FloorVariant` (`crates/pixtuoid-scene/src/layout/compute.rs:1306`) has five variants: Standard, OpenPlan, Dense, Senior, Lounge.
  - The variant is picked from the seed (`compute.rs:1340`). Computed: floor 0 = Standard, 1 = Senior, 2 = OpenPlan, 3 = Lounge, 4 = Dense.
  - The desks are 2×2 pods (`compute_pod_desks`, `compute.rs:1416`). Pod row 0 faces South, row 1 faces North (`compute.rs:1410`).

**Floors are projections.**
- `num_floors` = highest occupied floor + 1 (`floor/mod.rs:1202`).
- `floor_agents` keeps the agents whose `desk.floor == idx` (`floor/mod.rs:1212`).
- `project_floor_scene` (`floor/mod.rs:1262`) clones those slots into a per-floor `SceneState`. This is stateless; everything downstream reads the projection.

**The window shows ONE floor at a time, switched manually.**
- `OfficeSession` (`floor/office.rs:301`) holds one `FloorView` per floor plus `FloorNav { current, transition }` (`office.rs:147`).
- `render` draws only `nav.current()`, or both floors during a 900 ms slide (`office.rs:470-560`, `TRANSITION_DURATION_MS` at `floor/mod.rs:1158`).
- Navigation:
  - PageUp / Up / `k` go one floor up; PageDown / Down / `j` go one floor down (`crates/pixtuoid/src/panels/mod.rs:997-1010`).
  - The dashboard's Enter jumps to the selected agent's floor (`panels/mod.rs:1106`).
  - The floating window routes keys through the same dispatch (`floating/input.rs:194,214-219`).
- There is **no auto-follow**. When a floor empties, `settle` clamps the view down to the top occupied floor without a slide (`office.rs:183-195`).

**The elevator.**
- It is the `door` sprite in the north wall's last window slot (`compute.rs:433-447`), `ELEVATOR_W/H = 16×14` (`layout/mod.rs:496-499`), with 3 frames (closed / half / open) chosen from entry/exit progress (`pack.toml` door comment; `FloorCtx::recompute_door_anim_max_ms`, `floor/mod.rs:284`).
- Agents walk in from and out to `door_threshold` (`compute.rs:444-447`; pose code at `pose/mod.rs:262-412`). The OpenClaw lobster mascot uses it too (`creatures.rs:547`).

**The floor indicator** is text above the door, `▲ F{n} ▼`, with hollow arrows where there is no floor that way (`layout::floor_indicator`, `layout/mod.rs:514-524`).
- The arrows are pack icons `floor_up` / `floor_down` (`display/icon.rs:82-83`, `pack.toml [icons]`). Redrawing them is art only.
- The label text (`F{n}`) is code.

## 2. Agent state cycle

**States.** `ActivityState::{Idle, Running{item}, RequiresAction{reason}}` (`state/mod.rs:153`). `ToolKind::{Task, Edit, Read, Bash, Search, Other}` (`state/mod.rs:109`) is derived once per tool call.

**State → pose** (`pose/mod.rs:414-470`) **→ sprite** (`sim/mod.rs:928-1130`):

| State | Pose | On screen |
|---|---|---|
| Running | `SeatedTyping`, always at the desk, never wanders | the `typing` / `typing_back` loop (2 frames × 125 ms; `typing_frame` loops any frame count, `pose/pure.rs:34`). Skin and monitor are tinted by the tool's glow (`colors.rs:378`, `cutaway/paint.rs:1078` relights the pack's screen keys `j` and `J`). |
| RequiresAction | `SeatedIdle` | upright `seated` + the procedural `!` mark (`sim/mod.rs:982`, `effects.rs:79`) |
| Idle | the wander machine (`walk::advance_wander`) | at the desk, **asleep**: `SeatedSleeping` or `SeatedSleepingAlt` chosen by id, plus z's (`sim/mod.rs:913,987`); between naps, trips to waypoints |

Details of the Idle trips:
- Desk dwell is 15–30 s (`layout/decor.rs:741`). Each cycle the agent takes a trip with 25–60 % probability, and the trip is aimless with 0–50 % probability (`pose/pure.rs:105-138`).
- Waypoints: couch (20–40 s), pantry (`holding_coffee`, then `walking_coffee` back and a `desk_cup` that steams), vending, printer, meeting sofa or chair, island, snack shelf, phone booth, standing desk (`WaypointKind`, `decor.rs:14`).
- Chitchat bubbles appear at shared venues.

**Arrival and exit.**
- Arrival is a walk from the door threshold to the desk while `now − arrived_at < ENTRY_ANIMATION_MS = 4000` (`pose/pure.rs:56`; leg planned at `pose/mod.rs:368-412`).
- Exit: `SessionEnd` sets `exiting_at`; the agent walks from wherever it is to the door (`pose/mod.rs:262-342`). The slot is dropped after `EXIT_GRACE_WINDOW = 4.5 s` (`reducer/mod.rs:27`).
- A state flip mid-wander arms a snap-back walk to the desk (`SNAP_BACK_MS = 900`, `pose/mod.rs:129`).
- Other timers:
  - floor slide: 900 ms
  - pet rest: about 25 s (`creatures.rs:106`)
  - vacancy dim debounce: 5 s (`floor/mod.rs:800`)
  - stale reaping: 10 min mid-tool, 30 min idle, 60 min blocked (`reducer/mod.rs:42-46`)

**Subagents.**
- A subagent is a slot with `parent_id` (`state/mod.rs:349`). It is seated like everyone else, at the first free desk; nothing keeps it next to its lead.
- It wears a procedural **cap** in its lead's ink (`team_cap`, `sim/mod.rs:893`; `cap_ink(lead)`, `colors.rs:386`).
- There is no cap on the number of children (the "caps" are the hats).

**Team colour.** `agent_overrides` (`character/colors.rs:357`):
- shirt `B` and pants `P` come from `OUTFITS[16]` keyed by the cwd basename, so one project shares one outfit;
- hair `H` and skin `S` come from the agent id.

## 3. Pets

- `PetKind::{Cat, Dog}` (`pet.rs:36`). The OpenClaw lobster is a gateway mascot, not a pet (`creatures.rs`), so it is irrelevant for Orca agents.
- With no `[[pets]]` config, the office gets every kind (`crates/pixtuoid/src/config/mod.rs:609`).
- **One pet per floor:** `select_pet_for_floor(floor_seed, pets) = pets[floor_seed % len]` (`pet.rs:136`). `floor_seed(0) = 0`, so **floor 0 always gets the first configured pet**; floor 1 gets the second.
- Pets walk the people's A* walker on the walkable mask, rest about 25 s, sit, sleep, and can be petted (hearts, frozen for 2 s).
- The cat naps beside idle agents' desks (`sleeps_near_idle`, `pet.rs:101`; `naps_here`, `creatures.rs:35`). In camp, the owlbear would curl up next to resting adventurers.

**Sprite sizes (1x → @4x):**

| Kind | walk | sit | sleep |
|---|---|---|---|
| cat / dog | 8×6 (8 frames, stride 2) | 6×6 (4 frames) | 6×4 (4 frames) |

The lobster walk is 14×12. Facing: walks are drawn facing east and mirrored by the engine.

**Replace by art only: yes.**
- Pets are not in the hover-size table (`pixel_painter/tests.rs:1637`), so their canvas may grow (keep @4x = 4 × 1x and under about 16×16 at 1x for the half-block terminal).
- The name is config: `[[pets]] kind = "cat"  name = "Owlbear"`.
- A *third* kind (raven) needs engine work (enum + 3 pieces + config, S–M), and only one pet per floor is ever shown anyway.

## 4. Pieces and furniture

**`Piece`** (`pack/piece.rs:28`) is a fixed 64-variant enum covering character poses, furniture, fixtures and creatures. It is keyed by snake_case name in `pack.toml [animations]`. `min_frames` is at `piece.rs:114`; walks need `stride` (`piece.rs:145`).

**Geometry has a single owner, `Furniture`** (`layout/decor.rs:283`):
- `furniture_def` (`decor.rs:471`) gives pad, footprint, visual size, occupancy, dwell and approach for each kind.
- Role enums map onto it: `WaypointKind`, `PodDecor` (`decor.rs:1036`), `PlantKind`, `WallDecor` (`decor.rs:933`).
- Placement is hand-written per kind in `layout/compute.rs`. The layout is generated, never data-driven.

**Adding a genuinely new furniture kind end to end:**
1. `Furniture` variant, its `furniture_def` row and `repels_plants` arm (`decor.rs:431`, exhaustive).
2. A role enum, `FixtureKind`, and the compose and paint arms (`display/compose.rs`, `cutaway/paint.rs`, plus the classic painter).
3. The hover label.
4. Placement in `compute.rs`, kept clear of the mask, reachability and plant census.
5. A `Piece` variant, `pack.toml` entries (1x + @4x) and a gen-art function.
6. Tests: the `Furniture::ALL` count, the hover-size table `every_hover_size_is_its_painted_sprite_size` (`pixel_painter/tests.rs:1637`), placement sweeps across sizes and seeds (`layout/placement_sweep.rs`), and `every_bundled_sprite_is_a_frame_the_pack_loads`.

Cost: **M–L per kind (150–300 LOC plus the art)**. The placement sweeps are the expensive, risky part.

**A redraw on the same canvas is far cheaper.**
- The rule that binds every redraw: each furniture frame must equal its `furniture_def(..).visual` size (`pixel_painter/tests.rs:1637-1683`), and the desk's width is pinned (`pack/mod.rs:1256`).
- Holidays already use this pattern: `Occasion::art` swaps plant art for stand-ins on the plant's own canvas (`holiday.rs:154`), "so the layout, its footprints and its reachability never see a holiday".

**Desk contract.** `desk` / `desk_north` / `desk_front` must:
- mark `@mark cup` and `@mark tower`, and draw a lamp bulb in key `9`, or the pack fails to load (`pack/mod.rs:502-536`);
- keep their width.

Art may rise north above the base desk height (`desk_art_top`, `pack/lookup.rs:107`), although the bundled-pack test "only the monitor rises above the wood" (`pack/mod.rs:1246`) would need relaxing for a tall monster. Occupant-conditional props already exist (`DeskProps { cup, token_tier, sheet_fall }`, `sim/mod.rs:218`; `DeskProp`, `pack/mod.rs:410`).

**1x canvas sizes** (@4x = ×4): desk 14×9, desk_north 14×11, desk_front 14×9, desk_chair 8×5, door 16×14 (3 frames), floor_lamp 4×12, side_table 7×4, phone_booth 7×15, meeting_sofa 20×7, meeting_table 11×5, pantry 32×10, pantry_small 20×8, kitchen_island 20×7, vending 7×13, printer 7×8, bookshelf 8×12, whiteboard 14×11, tv_stand 10×10, plants 6×7, 6×10, 6×6, 5×4, water_cooler 4×9, coat_rack 5×12, fish_tank 14×11, desk_cup 2×2, token_tower 4×4, token_sheet 3×1.

## 5. Character art

- Every agent shares the body frames. The 1x frames are 8×12 (standing) and 8×11 (typing); @4x they are 32×48 and 32×44.
- On top, it wears one **hairstyle** chosen per agent by rendezvous hash over the pack's `[hairstyles]` (`character/hair.rs:22`). The pick is stable, and adding a style moves only the agents that prefer it.
- Today: `HAIRSTYLES = {knight_helm}` (`scripts/gen-art.py:1525`), registered at `pack.toml:763`. The modern styles are kept as `UNWORN_HAIRSTYLES`.

**Can a layer cover the body (cloak, robe, fur mantle)? Yes, with limits** (`hair.rs:100-117,152-215`):
- The layer canvas is the full figure: `LAYER_H = 12*S + headroom` = 32×54 at 4x (`gen-art.py:593`).
- It is laid mark-on-mark at the head, so it follows the head's bob.
- It is cut at the body's width and the dressed frame's bottom.
- It is **one static frame per view** (front, back, side, crown), shared by every pose of that view: seated, typing, walking and standing all use the front view.
- Layers take the body's recolour, so a garment drawn in `B` / `P` **wears the team colour**.

Consequences:
- A mantle, hood, helm or shoulder cape works well.
- A long robe as an `over` layer hides the walking legs (the mage glides); draw the hem short so the feet still show.
- A cape works as `behind` in front view and `over` in back view.
- Weapons must **not** live in layers: they would be static and carried in every pose. They belong to the attack frames.
- The crown view (sleeping) and the side view need layers too, or those poses are drawn bare.

**Per-agent body variants (class bodies)** would need either about 13 character pieces plus 3 walks × 8 frames multiplied by 4 classes, or a new "body set" pack dimension threaded through sim, compose and paint caches. Engine M–L, art XL. **Not worth it** (see (c)).

**Per-class attack instead of typing.**
- Typing is 2 frames today, but `typing_frame` loops any frame count, so a longer generic attack is **art only**.
- Per-class attacks are engine B5: 8 new pieces (4 classes × front/back), chosen by class at `sim/mod.rs:996`, with the back views in `SEATED_BACK_VIEWS` (`sim/seat.rs:19,168`).

## 6. Theme and backdrop

**Theme** (`theme/mod.rs`) is colours only. `DARK_FANTASY` (`theme/dark_fantasy.rs`) already has stone-grey walls and flagstone tiles. There is one theme per frame, for the whole office.

**North wall band** (`cutaway/paint.rs:807 paint_wall`):
- The wall is a theme-coloured slab with window posts.
- Windows are list pieces (`display/compose.rs:1517 push_windows`) showing sky, clouds, sun, moon, stars and the **pack's** skyline.
- The skyline is `[city]` + `[buildings.*]` (`pack.toml:773`): one-frame sprites in seven material keys, coloured by depth and sky. Glass pixels become windows that light at night.
- Skyline buildings → pines, mountains, ruined watchtowers is **art only**.

**Ground** is the carpet in theme tones with a tile seam grid (`paint.rs:879`). It reads as flagstones in dark-fantasy.

**The sky follows the viewer's real clock** (`look.rs:766`). The snapshot examples can override the hour (`cutaway_snapshot --now-hour`), but the runtime cannot.

**Dungeon walls on floors 1..N and an open camp on floor 0** need:
- (i) a per-floor theme: grass or earth for the camp, wood palisade, firelight;
- (ii) no windows on dungeon floors: skip `push_windows` and the posts;
- (iii) optionally a pinned night;
- (iv) per-floor art for the skyline and decor.

All four are engine B1 + B4. Caveat: the office-wide raster cache resets whenever the pack or theme changes (`look.rs:340-377,727`). Steady state draws one floor and is fine, but a 900 ms slide would rebuild every frame unless the cache is kept per role.

---

## (a) ART ONLY

All of these keep the existing canvases. Items marked † need role packs (B1) only because the camp and the dungeon would otherwise share one drawing. Everything else works with today's engine.

| # | Item (piece → new look) | Canvas 1x | Size |
|---|---|---|---|
| A1 | Class layers ×4 (`mage`, `knight`, `ranger`, `berserker`): hood/helm + mantle/robe/cape in `B`/`P`, all 4 views. **In progress, other worker.** | 32×54 @4x layer | L (8–12 h) |
| A2 | Owlbear over the cat (walk 8f, sit 4f, sleep 4f; may grow); wolf over the dog. **In progress, other worker.** Config: `[[pets]]` owlbear first. | 8×6 | M + M (4–6 h each) |
| A3 | Generic attack: `typing_0/1` + `typing_back_0/1` → weapon strike, optionally 4 frames. Shared by all classes until B5. | 8×11 | M (3–5 h) |
| A4† | **Dungeon desk = monster lair**: `desk` (monster seen from behind, for South seats), `desk_north` (monster facing agent and viewer), `desk_front` (monster body over the props). Keep `cup`/`tower` marks and a `9` bulb (torch/candle). Draw eyes/runes in `j`/`J` so they glow in the current tool's colour. South view and north view can be two different species for free variety. | 14×9 / 14×11 / 14×9 | L (6–8 h) |
| A5† | `desk_chair` → nothing or a dropped shield (dungeon); log stump (camp) | 8×5 | S |
| A6 | `desk_cup` → potion or flask; `token_tower` → loot pile (grows with tokens); `token_sheet` → falling coin | 2×2, 4×4, 3×1 | S (1–2 h) |
| A7† | `door` → stair archway down (dungeon) / palisade gate (camp), 3 frames | 16×14 ×3 | M (2–4 h each) |
| A8† | **Camp spot = bedroll**: `desk*` → rolled bedroll + pack + lantern bulb (`9`); `seated_sleeping(_alt)` → curled in a blanket (crown view). Lying flat does not fit the 8×10 upright canvas, see (c). | 14×9…, 8×10 | M–L (5–7 h) |
| A9† | Campfire: `side_table` (lounge flank) → stone-ringed fire; `floor_lamp` → torch on a pole (its glow halo becomes firelight) | 7×4, 4×12 | M (2–4 h) |
| A10† | Log benches: `meeting_sofa(_north)` → logs; the couch seats use them in camp | 20×7 | M (2–3 h) |
| A11† | Tent: `phone_booth` (aisle pod decor, stand-at-door waypoint) → pointed tent front | 7×15 | M (2–3 h) |
| A12† | Camp services: `pantry(_small)` → cooking fire and pot; `kitchen_island` → supply cart; `vending` → crate stack; `printer` → anvil or whetstone (has a busy loop); `water_cooler` → water barrel; `coat_rack` → armour stand | various | L (8–10 h) |
| A13† | Dungeon decor: plants ×4 → stalagmite, bones, mushrooms, barrel; `vending` → treasure chest; `printer` → brazier; `bookshelf` → weapon rack; `whiteboard` / `notice_board` / `bulletin_board` → map, wanted posters; `exit_sign` → wall torch | various | L (8–12 h) |
| A14† | Skyline `[buildings]` → pines, mountains, watchtower (camp windows). Fewer buildings is fine. | per building | M (3–5 h) |
| A15† | `holding_coffee` / `walking_coffee` → bowl of stew or flask (camp) | 8×12, 8 walk frames | M (3–4 h) |
| A16† | Horn or banner pose for RequiresAction: the dungeon pack's `seated`. In camp, `seated` must stay "sitting on a log". | 8×10 | S–M (2–3 h) |
| A17 | Raven perched in a decor piece (notice board, tent ridge), as a third "pet" without engine work | host canvas | S (1–2 h) |
| A18 | Icons `floor_up` / `floor_down` → stair glyphs | one text line | S |
| A19 | Per-class attacks after B5: 4 classes × front/back × about 4 frames (@4x + simple 1x) | 8×11 | L (10–14 h) |

## (b) RUST ENGINE

### B1 Floor roles and role packs (prerequisite for every † item) — **M (5–7 h), about 220 LOC with tests, risk medium**

- **Design.** Add `pub enum FloorRole { Camp, Dungeon }` with `FloorPlace::role()`: index 0 → Camp, otherwise Dungeon.
  - Two overlay manifests, `sprites/default/camp.toml` and `dungeon.toml`, list only the keys they replace: `[animations.desk] frames = ["camp_desk.sprite"]`, `[buildings]`, `[icons]`.
  - `build.rs` deep-merges each overlay over `pack.toml` into `bundled_pack_<role>.json`.
  - `pack::load_bundled_role_packs()` returns `EnumMap<FloorRole, Arc<OfficeArt>>`.
  - `OfficeSession::new(packs)` gives each new `FloorView` its role's pack (`office.rs:400`). Each floor's raster already owns its pack, and `look::render` / `step_floor` read only that one (`floor/mod.rs:453`, `look.rs:727-731`), so the sim, compose, paint, lighting and desk-mark paths need **no threading**.
  - Keep `OfficeRaster` per role so slides don't thrash (`look.rs:340`).
  - Characters, hairstyles and icons are inherited, so an agent keeps its class across floors.
- **Files.** `crates/pixtuoid-scene/build.rs`, `src/pack/mod.rs` (loader + tests at `:677`, validation over every role pack), `src/floor/{mod.rs,office.rs}`, `src/look.rs`, `crates/pixtuoid/src/floating/{mod.rs:60,offscreen.rs:33}`, `src/tui/tui_renderer/mod.rs:171`, examples.
- **Also.** `floating_snapshot` gets a `--floor N` option for the visual checks.
- **Risk.** The pack test suite assumes one pack (`every_bundled_sprite_is_a_frame_the_pack_loads`, `the_bundled_pack_passes_its_own_validation`, the hover-size table). `pixtuoid-web` uses a `FloorSession` and is unaffected.

### B2 Campaign seating: idle agents to the camp, working agents to the dungeon — **M–L (6–8 h), about 150 LOC + 200 test LOC, risk medium-high**

- **Design (core, the seating owner).** Add `SeatPolicy::{FloorFirst, Campaign}` on `SceneState`; the fork's binary turns on `Campaign`.
- `want(slot, now)` decides where an agent belongs:

  | State | Wants |
  |---|---|
  | Running or RequiresAction | the dungeon |
  | Idle for at least `REST_AFTER` (about 15 s) | the camp |
  | a new session that is idle | the camp |
  | anything else | stays where it is (hysteresis, so turn gaps don't bounce) |

- `reseat_by_role(now)`:
  1. Free every desk whose floor class (0 = camp, 1 and up = dungeon) differs from what its agent wants.
  2. Seat the unseated with a per-slot free-desk iterator: camp → floor 0, overflowing to floors 1 and up; dungeon → floors 1 and up.
  3. Set `arrived_at = now`, so the agent walks in from the stairs.
- Run it at the end of `Reducer::apply` (`reducer/mod.rs:359`), in `Reducer::tick` (`:313`, which expires the hysteresis), and after `RemoteOffice::apply` and `set_capacities` (`remote.rs:829-843`).
- **Required scene fix.** `FloorCtx::evict_missing` keeps walk state for any agent in the *whole* scene (`floor/mod.rs:274-277`), and a finished `WalkState.entry` is kept (`floor/mod.rs:280-283`). An agent coming back to a floor would therefore skip its walk-in (`pose/mod.rs:368` gate).
  - Fix: evict per floor in `OfficeSession::prepare` (`office.rs:396`) for agents not on that floor.
  - Add a continuity test in `pose/tests.rs`, as `crates/pixtuoid-scene/AGENTS.md` asks.
- **Files.** `crates/pixtuoid-core/src/state/mod.rs`, `state/reducer/{mod.rs,tests.rs}`, `remote.rs`; `crates/pixtuoid-scene/src/floor/{mod.rs,office.rs}`, `pose/tests.rs`; `crates/pixtuoid/src/runtime/driver.rs` (turning the policy on).
- **Risk.** Seating invariants, the `SEATINGS` pass-count test, and the remote office.
- **v1 limitation.** The agent leaves the old floor instantly; B8 adds the walk-out.

### B3 Camp layout — **S (1–3 h), 1 LOC + test fallout, risk low-medium**

Reorder `FloorVariant::ALL` (`compute.rs:1328`) to `[Lounge, Standard, Dense, OpenPlan, Senior]`. Floor 0 becomes Lounge (no partition walls, lounge couch, floor lamp, pantry corner; see `scratch/floor3_lounge_night.png`), floor 1 becomes OpenPlan (wall-free dungeon), and floors 2–4 become Standard, Senior and Dense.

Threading a role into `SceneLayout::compute` instead would touch about 52 call sites (most of them tests); not worth it. Snapshots and goldens pinned to floor-0 = Standard need updating.

### B4 Per-role look — **M (3–5 h), about 120 LOC, risk low-medium**

1. A `DARK_FANTASY_CAMP` theme (earth or grass ground, wood palisade wall and posts, warm light), chosen per floor in `OfficeSession::render`'s draw closure (`office.rs:480-498`). The dungeon keeps `DARK_FANTASY`.
2. Dungeon without windows: a `[walls] windows = false` flag in the dungeon overlay. It skips `push_windows` (`compose.rs:1517`) and the posts in `paint_wall` (`paint.rs:807`), with the classic painter's equivalent.
3. In campaign mode, pin the hour to night (`Sky::at` input, `look.rs:766`), so the camp shows moon and stars and the dungeon runs on torchlight (desk-lamp pools = lair torches).

### B5 Class per agent and per-class attack — **M (4–6 h), about 100 LOC + 60 test LOC, risk low-medium**

- `Class::{Mage, Knight, Ranger, Berserker}` comes from the hairstyle name `pick` returns (`hair.rs:22`). Class display is already free with A1; this step only maps it.
- Add `Piece::Attack{Class}` + `Attack{Class}Back` (8 pieces, `piece.rs:28`, `min_frames` = 2), the character list in `validate.rs:30`, back pairs in `SEATED_BACK_VIEWS` (`seat.rs:19`), and the choice at `sim/mod.rs:996` (`TYPING` → class attack). Register 16 `pack.toml` entries and gen-art `POSES`.
- The frames carry `head.*` marks, so the class layers dress them.

### Optional items

| Item | Size | Design |
|---|---|---|
| B6 Role floor labels | S (1 h) | `floor_indicator` (`layout/mod.rs:514`) → ` Camp ` / ` D1 `; goldens in `cutaway/text.rs:298`, `panels/widgets/tooltip.rs:538` |
| B7 Auto-follow the action | S–M (2–4 h, ~70 LOC) | After N s without a key, navigate to the dungeon while anyone fights, else the camp (floating window, `FloorNav`) |
| B8 Walk-out between floors | M (4–6 h, ~80 LOC) | Core `relocating: Option<(FloorDesk, SystemTime)>` keeps the old desk for an exit walk (`pose/mod.rs:262` reads `exiting_at.or(relocating_at)`), then swaps desk and `arrived_at` after `EXIT_GRACE_WINDOW` |
| B9 Monster variety and liveliness | S–M (2–4 h) | Multi-frame `desk` art picked by desk index (marks read from frame 0, `pack/mod.rs:502`; `paint.rs:984` draws frame 0) |
| B9b Monster only on engaged lairs | S–M | A `DeskProp::Foe` shown while the occupant fights, like the cup (`sim/mod.rs:218`, `compose.rs:1152`); empty lairs show only bones and a torch |
| B10 Tool vocabulary | S | Footer/tally words (Edit → "Strike", Bash → "Spell"); optional |

## (c) NOT WORTH IT / TOO COSTLY (and the cheaper alternative)

| Idea | Why not | Cheaper alternative |
|---|---|---|
| New furniture kinds Monster, Campfire, Tent, Bedroll, Stairs | M–L each: `Furniture` + `FixtureKind` + placement + mask + reachability + placement sweeps (§4) | Stand-ins on existing canvases through role packs: desk → lair or bedroll, side_table/floor_lamp → campfire/torch, phone_booth → tent, door → stairs or gate |
| A bespoke camp generator (tents in a ring around the fire) | L–XL: a new layout path, capacity, reachability, about 52 compute callers, most of them tests | Lounge variant for floor 0 (B3) + stand-ins |
| Per-class body frames for every pose | XL art (4 × about 40 frames), M–L engine (body sets through every cache) | Shared body + class layers (A1) + per-class attack only (B5) |
| Per-(class × tool) attacks | XL art | The tool's colour lights the monster's `j`/`J` eyes or runes and the attacker's skin (zero engine); later a procedural hit-spark effect (M) |
| Camp and dungeon visible together (split or stacked window) | L: window geometry, hit-testing, capacity, overlays | B7 auto-follow, or the ↑/↓ keys |
| Opaque, textured stone partitions; a textured north wall | M–L: rewriting `glass.rs` / `paint_wall` per role | Wall-free variants on campaign floors (B3) + theme colours + torch wall decor |
| Subagents drawn as familiars | M–L: sim, seating, hit-tests, tooltips | Keep the person + cap in the lead's ink (the "party token") |
| Raven as a third roaming pet | S–M, and only one pet shows per floor | Perched raven in decor art (A17) |
| Sleepers lying horizontally on bedrolls | New pose anchoring (M); the 8×10 upright canvas can't hold a lying figure | Sleeper curled in a blanket (A8) |
| A monster that reacts to each tool result (dies, respawns) | M–L: event plumbing and effects | Glow colour change per tool (existing) |
| A camp on the real clock vs always night | — | Pin night (B4c, S) |

## Options and trade-offs

**Class criterion**

| Option | Variety | Stability | Engine | Note |
|---|---|---|---|---|
| **Stable hash per agent (rendezvous over styles)** ✔ | high, random mix | stable per session | **0** (B5 just maps names) | A party may draw duplicates |
| By provider (`slot.source`) | low (owner runs mostly 1–2 CLIs) | stable | S | The class means something (codex = mage …) |
| By role (lead / worker / subagent) | medium | stable | M + needs Orca role data (only `parent_id` is known) | Best story, missing data |
| By model family (`slot.model`) | medium | **unstable** (last-seen, `None` at first) | S–M with a first-seen latch | — |
| By team (cwd) | none inside a party | stable | S | Duplicates the team colour |

**Tools → actions**
- Recommended, zero engine: the existing glow per `ToolKind` (`colors.rs:378`, `paint.rs:1078`) tints the monster's eyes and runes plus the attacker's skin.
- Next step: footer vocabulary (S) or a tool-tinted hit spark (M).
- Per-tool animations: no.

**How many dungeon floors**

| Option | Pros | Cons |
|---|---|---|
| **One fight zone, overflow to floor 2+ by capacity** ✔ | Zero extra code beyond B2; typically just floors 0 and 1 | Parties mix on one floor |
| One floor per party (team/cwd) | Party feel | S–M extra in B2; more floor switching; empty space |
| Depth by run time or tokens | Gamified | Re-seats mid-fight (teleports); confusing |

## Minimal vertical slice

**Goal:** in the real floating window, a camp on floor 0 with real resting agents and the owlbear, a dungeon on floor 1 with a working agent fighting a monster, and four classes.

| Step | Work | Who | Depends on | Can run in parallel with |
|---|---|---|---|---|
| 0 | A1 class layers (names exactly `mage`, `knight`, `ranger`, `berserker`; garments in `B`/`P`; **no weapons in layers**); A2 owlbear and wolf | art workers (already running) | — | everything |
| 1a | **B2** campaign seating + per-floor eviction fix | engine worker 1 (core) | — | 1b, art |
| 1b | **B1** role packs (+ `floating_snapshot --floor`) | engine worker 2 (scene and binary) | — | 1a, art |
| 2 | **B3** camp variant, **B4** camp theme / windowless dungeon / night, **B6** labels | engine worker 2 | B1 | art step 3 |
| 3 | A4 monster lair, A5 chairs, A7 stairs and gate, A8 bedroll + sleeper, A9 campfire and torch, A10 log benches, A11 tent, A3 generic attack, A6 props | art worker(s) in gen-art | overlay format of B1 (drawing can start now) | 1a, 2 |
| 4 | **B5** class → attack; A19 per-class attacks | engine worker 1 + art | A1 names | — |
| 5 | Integration: `[[pets]]` owlbear (cat) first, then wolf; release build; check `floating_snapshot --floor 0/1` and the real window | coordinator / any | all | — |

**Cut line if time runs short.** Steps 0–3 already show a camp with sleeping adventurers and the owlbear, and a dungeon with knights, mages, rangers and berserkers fighting lair monsters, using one shared attack. B5 and A19 make the attacks class-specific.

**After the slice:**
- B8 walk-out (the slice pops an agent out of the camp, then walks it in down the dungeon stairs);
- B7 auto-follow (the slice needs ↑/PageUp to look at the dungeon);
- B9 / B9b monster variety, plus A12/A13 for the rest of the decor (the slice may keep a few office pieces in the dark theme).

**Verification each step:**
- `cargo test -p pixtuoid-scene` (0 failures) and core's reducer and seating tests;
- `cargo clippy --workspace --all-targets -- -D warnings`;
- `py -3 scripts/gen-art.py --selftest` and `--check`;
- the visual check through `floating_snapshot` / `cutaway_snapshot --now-hour 23 --floor N`.

---

## Resumen para el dueño (español)

**Qué es posible.** Casi todo lo que pediste se puede hacer reutilizando lo que Pixtuoid ya tiene. El truco es "disfrazar" las piezas de oficina sin cambiar sus medidas:
- en la mazmorra, el escritorio con su monitor pasa a ser un monstruo, y el aventurero que "teclea" en realidad lo ataca;
- en el campamento, el escritorio es un saco de dormir, la cabina telefónica una tienda, la lámpara una antorcha, la mesita una fogata y el sofá un tronco para sentarse;
- el ascensor pasa a ser una escalera o la entrada del campamento;
- el gato pasa a ser el oso-lechuza (y descansa junto a los aventureros dormidos), y el perro el lobo.

Todo eso es **solo dibujo**.

**Lo que necesita programación (5 piezas, unas 25 horas de agente):**
1. Que cada piso tenga su propio "paquete de dibujos", para que el piso 0 sea campamento y los demás mazmorra.
2. Que los agentes que trabajan bajen a la mazmorra y los que descansan suban al campamento. Hoy cada agente se queda fijo en su escritorio, y esto es lo más delicado.
3. Usar para el campamento el plano de oficina que no tiene paredes de vidrio.
4. Pasto y madera en el campamento, sin ventanas en la mazmorra y siempre de noche.
5. Que cada clase (maga, caballero, arquero, berserker) tenga su propio ataque.

La clase de cada agente sale gratis: el programa ya reparte un "peinado" fijo a cada agente, y basta con que los peinados sean las cuatro clases.

**Lo que no conviene.**
- Muebles realmente nuevos con su propia lógica de ubicación.
- Un plano de campamento hecho a medida (tiendas en círculo).
- Cuerpos distintos por clase en todas las poses.
- Una animación distinta por cada herramienta.
- Ver los dos pisos a la vez.

En cada caso hay una alternativa barata que se ve casi igual.

**Orden recomendado.**
- Ahora y en paralelo: los dibujantes siguen con las clases y las mascotas; un programador hace el "quién va a qué piso" y otro los paquetes por piso.
- Después: el estilo de cada piso, mientras se dibujan el monstruo, el saco de dormir, la fogata y la tienda.
- Al final: el ataque propio de cada clase.

**Una limitación de la primera versión.** La ventana muestra un piso a la vez. Para ver la pelea se pulsa ↑ (o RePág). Más adelante puede seguir sola a la acción.
