---
name: shot-prompt
description: Design a scene into production-ready cinematic shots and write their image/video prompts. Establishes the scene's spatial layout once (cast, seating, facing, anchors, light, asset IDs), then writes each shot as labeled blocks that reference that layout instead of re-describing the room. Use whenever building, reviewing, or fixing shots, shot lists, storyboard frames, frame prompts, or video prompts — in Cinematec or any shot-by-shot AI film pipeline — and whenever a generated frame stages characters or props in the wrong place or a character drifts between shots.
revision: 3.3.1
---

# shot-prompt — scene layout first, then shots

A shot prompt is a **staging instruction for a machine**, not a paragraph of film writing.
Think like a cinematographer; write like a stage manager.

> **Revision 3.2.0 (2026-10-10, Cinematec v1.0.98) - the prompt writer decides purpose and picture first.**
> Writing a frame prompt (step 3, "Write prompts") has its own instructions, `prompts/frame-prompt.md`, instead of
> borrowing `reshot.md`, whose ~400 words on re-cutting a shot told a writer that may not change the fields how to
> change them (rules 2,248 -> 1,599 words). It gets the director's camera/cutting/tension notes only
> (`director_for_shots`), not the screenwriting half. Before writing, it decides in order:
>
> 1. **Purpose** - why the director cuts to this shot here; what the audience must notice or feel that the last
>    shot did not give them. Everything else serves this.
> 2. **The instant** - the first frame, before the action.
> 3. **The camera** - where it must stand in the layout for this size, angle and lens: facing the important face,
>    on the established side of the axis.
> 4. **The picture** - what the eye lands on first, what is nearest the lens, what is left empty, what closes the
>    frame. Wide lenses keep the place around people; long lenses isolate a face.
>
> **Revision 3.4.0 (2026-10-10, Cinematec v1.0.101) - plain words, and the diagram is not repeated.**
> Shot 1.1's prompt could not be read ("the ritual geometry of predator trailing prey across a dead-flat grid").
> - `MOMENT` is <= 90 words in **plain words**: short sentences (<= 20 words), everyday language, no metaphors
>   or film-theory terms. Purpose sentence like "This shot shows that Denny is following Hector."
> - `BACKGROUND` and the layout's `LIGHT` go to the image model as written: name things in words ("the pink
>   neon sign above the store"), never by anchor id, and describe light, not story.
> - **With the diagram attached, the image prompt does not say where the camera stands** (`CAMERA POS` is not
>   sent). Words carry size, angle and lens; the diagram carries every position. Two descriptions of the
>   same geometry are two chances to disagree. `CAMERA POS` is still written - the diagram and checks use it.
> - The fixed sentences the app adds are rewritten plainly; their meaning (first-instant guard, no invented
>   backdrop, copy looks not framing) is unchanged.

> `MOMENT` (was <= 110, now <= 90 words, plain words, rev 3.4.0): **purpose sentence** -> the first instant -> **one sentence on how the picture is
> built** (eye first, nearest the lens, empty space) - in plain words, still no sides, feet or compass; the diagram
> carries geometry. This is not the removed `COMPOSITION` block: that restated positions; this states intent.
>
> Not adopted, on purpose: a 100-180 word target for the image prompt (deciding by length broke four shots -
> lessons doc section 3), "concise / detailed / custom" prompt modes, and new fields in step 2.

> **Revision 3.1.0 (2026-10-10, Cinematec v1.0.95) - shot planning is three separate steps.**
> One call used to write the layout, the shot list and a full frame prompt per shot from ~5,000 words of
> input; nothing reached the screen for 3+ minutes. Now:
>
> 1. **Layout** - its own job (`plan_layout`, `prompts/layout.md` + `scene-layout-rule.md`). Required first:
>    shot planning refuses a scene without one.
> 2. **Shot list** - `plan_shots`, `prompts/shots.md`, ~1,000 words in total. It is sent ONLY: the director's
>    philosophy + camera, editing and tension sections (`director_for_shots`), the scene's script, the layout cut
>    to LOCATION / CAST / ANCHORS / POSITIONS / SCREEN DIRECTION (`planner_layout`), and the asset names. It
>    returns per shot: size, angle, movement, lens, duration, a 1-2 sentence action, dialogue, visible assets,
>    sound. **No frame prompt, no layout, no cinematographer skill, no visual style, no asset sheets.**
> 3. **Frame prompts** - "Write prompts" on the scene (`rewrite_shot` promptOnly, 4 at a time), which gets the
>    full asset sheets and writes the Tier 2 blocks below.
>
> When asked to make shot planning better, add to step 3, not step 2. Less text in step 2 is the point: every
> rule added there is read for every shot and slows the first shot reaching the screen.
>
> The exact last planning request is saved to `docs/review/last-shot-plan-prompt.md`.

> **Revision 3.0.0 (2026-10-10, Cinematec v1.0.81) - read this first; it overrides the older detail below.**
> The labeled blocks are for the *machine* (diagram, video model, checks). The image model reads a
> short, readable prompt. Sending every block made shot 1.6's prompt 1,800 words that neither the
> filmmaker nor the model could follow.
>
> - Each Shot Block now **opens with `MOMENT`**: one line, <= 90 words, plain film language - one
>   sentence of story context, then exactly what the camera sees at the FIRST instant (who, where in
>   plain words, how they stand to each other and the camera, posture, hands, key props). No anchor
>   ids, feet, compass or "screen left"; no looks; never the outcome.
> - **Removed:** `SIGHTLINE` (run the check silently), `PROP PLACEMENT`, `COMPOSITION`, `LIGHT NOTE`.
> - **Capped:** `WORLD STATE` <= 20 words a line; `CAMERA POS` one line; `BACKGROUND` one sentence;
>   `SHOT PROJECTION` <= 10 words a person; `NOT IN FRAME` a bare list of anchor ids.
> - `COORDS` (shot and scene layout) is mandatory - without it no staging diagram is sent.
> - Tier 3 is rewritten below: the image model gets story + MOMENT + camera + place + light + style
>   + one-line reference list (~300 words), the diagram, and **one** reference picture per person.
>
> Where the sections and worked example below still show the removed blocks, they are the pre-3.0
> format - kept for the measurement, anchor and screen-direction rules, which all still apply.

## The two-tier rule

> Describe the room **once**, at scene level. Every shot then references that layout instead of
> re-inventing it.

Re-describing the space in every shot is how a scene falls apart: shot 3 says the table is round,
shot 7 implies it is long, shot 9 moves the door. Each shot is generated independently, so any
detail restated in prose is a detail free to drift. Say it once, send it unchanged with every shot,
and the geography holds.

| Tier | Written | Contains |
|---|---|---|
| **1. Scene Sheet** | once per scene | cast, asset IDs, spatial layout, seating + facing, anchors, light, mood |
| **2. Shot Block** | once per shot | purpose, camera position *relative to the anchors*, who is visible and where in frame, action, dialogue, start/end state |
| **3. Composed prompt** | at generation | Scene Sheet (verbatim) + Shot Block + asset descriptions + reference images |

The Scene Sheet is **identical text on every shot of the scene**. That repetition is the point —
it is what keeps the room the same room.

---

## Tier 1 — the Scene Sheet

```
SCENE: <number> - <slug line>
LOCATION: <Name> [<asset-id>] - <the room in one clause>
DIMENSIONS: <width>ft east-west x <depth>ft north-south; origin at <ANCHOR_ID>, <where that is>
TIME: <DAY / NIGHT / CONTINUOUS>
CAST: <NAME> [<id>], <NAME> [<id>], ...
PROPS: <Name> [<id>], <Name> [<id>], ...
ANCHORS:
- <ANCHOR_01>: <w>ft wide x <d>ft deep, <what it is>, <n>ft <direction> of the origin
- <ANCHOR_02>: <w>ft wide x <d>ft deep, <what it is>, <n>ft <direction> of the origin
BACKDROP:
- <DIRECTION>: <what closes this side>, <n>ft out, <and what lies beyond it to the horizon>
- NOTHING ELSE: <what does not exist in or around this location at all>
POSITIONS:
- <compass/seat slot>: <NAME> [<id>] - faces <direction>, <posture / what they are doing at rest>
- <compass/seat slot>: <NAME> [<id>] - faces <direction>, <posture / what they are doing at rest>
LIGHT: <practical sources, where they hang, direction, color, falloff>
SCREEN DIRECTION: <the anchor axis the coverage is cut on>
MOOD: <one clause>
```

### Measurement

A layout with no numbers is a layout the image model re-scales at every cut. Give the location a
footprint and an origin, then measure everything against it — anchors, characters, cameras,
backdrops — in feet.

The failure it prevents is quiet, because every individual frame looks fine. A shot decides on its
own that the store front is *"thirty meters behind him"* and renders a bright wall at his back. The
next shot, pointed a different way and given no number either, decides the far plane is empty and
renders black. Both obey their prompts. Neither is wrong on its own. But the same man in the same
ten seconds now stands in two different places, and no check downstream can tell which one is the
location, because nothing ever said how big it was.

```
DIMENSIONS: 150ft east-west x 90ft north-south of asphalt; origin at CENTERLINE_01, the centre of the lot
ANCHORS:
- STORE_01: 80ft wide x 20ft deep, the shuttered store front, face on the north edge, 45ft north of the origin
- SIGN_01:  12ft wide, SAVE-RITE neon on STORE_01's parapet, 18ft above the asphalt, 45ft north of the origin
BACKDROP:
- NORTH: STORE_01's face 45ft out, SIGN_01 above it at 18ft; nothing over the parapet but black sky
- SOUTH: ruled asphalt for 45ft to EXIT_01, then chain-link and a dead field, blue-black past 65ft
```

Three rules follow from it:

- **A distance belongs to the location, not to the shot.** `BACKGROUND` copies the number off the
  `BACKDROP` line for the direction it looks. It never picks its own.
- **`CAMERA POS` says how far, not just which side.** *"south of TABLE_01"* is true from one foot
  away and from fifty, and those are different shot sizes.
- **Size and offset are separate facts and both are needed.** An anchor with no size gets re-scaled;
  an anchor with no offset gets re-placed.

Metres are accepted everywhere feet are, but pick one and keep the scene in it.

### Anchors

Name the fixed furniture and openings — `TABLE_01`, `DOOR_01`, `WINDOW_02`, `BULB_01` — and place
each one in the room. Everything afterwards (camera positions, seating, who is behind whom) is
stated **relative to an anchor**, never in free-floating description. Anchors are what make a
camera position reproducible.

### Backdrop

Anchors say what is *in* the location. `BACKDROP` says what closes it — one line per direction the
camera can be pointed, out to the horizon, including the empty directions. *"SOUTH: bare asphalt
falling off to black"* is a real answer and a necessary one.

An unstated background is not an empty background. The image model fills it, and what it reaches
for is a city skyline, a second storey, lit windows, traffic. So the block ends with an explicit
`NOTHING ELSE:` line naming what this location does not contain.

It also pins each landmark to **one** place. A sign described in an asset MD is described just as
vividly for a shot whose camera has its back to it, and a model given a magenta sign and no rule
about where it lives will put one behind the subject in every shot of the scene — the reverse angle
then shows the same backdrop as the shot it reverses, and the cut dies.

### Positions, not prose

Give every character a slot on a compass (`N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`) or a clock
face around the primary anchor, plus the direction they face. This is the single highest-value
block in the whole skill: from a seating map the model can derive who lands screen left and screen
right from *any* camera position, and reverse angles stay honest.

```
POSITIONS:
- N:  ARBEL [arbel] - dealer's chair, faces S toward DOOR_01, leaning back
- NE: NISSIM [nissim] - faces SW, elbows on the cloth
- S:  AVI [avi] - faces N, directly across from ARBEL, hunched over his chips
```

### Screen direction

State the axis the scene is cut on — *"coverage is cut on the ARBEL(N)↔AVI(S) axis; camera stays
on the west side of TABLE_01"*. That one line is the 180-degree line, written down, so every shot
can be checked against it.

---

## Tier 2 — the Shot Block

A Shot Block is **four layers**, and keeping them apart is what lets one scene survive many cameras:

1. **Where things really are** — `WORLD STATE`, `END STATE`. Measured from anchors, facings as
   compass directions. Objective: every camera in the scene agrees with them.
2. **Where the camera is** — `CAMERA POS`, `CAMERA`.
3. **How that looks from here** — `IN FRAME`, `NOT IN FRAME`, `BACKGROUND`, `FOCUS`,
   `SHOT PROJECTION`, `PROP PLACEMENT`, `COMPOSITION`. True for this setup alone, thrown away at the cut.
4. **When things change** — `BEATS`, the clip's timeline.

Never write a layer-1 fact in layer-3 terms. *"DENNY frame left"* is not where Denny is, it is where
this lens happens to put him; the next camera contradicts it, and the shot after that inherits the
contradiction. Layer 3 is **derived** from layer 1 plus the camera — never invented, and never the
other way round.

```
SHOT: <SC##_SH##> - <short name>
PURPOSE: <why this shot exists in one clause>
DURATION: <seconds>
WORLD STATE:
- <NAME> [<id>]: <n>ft <direction> of <ANCHOR>, facing <compass direction>, <posture, what is in which hand>
- <NAME> [<id>]: <n>ft <direction> of <ANCHOR>, facing <compass direction>, <posture, what is in which hand>
- <Prop> [<id>]: <where it is in the room>
CAMERA POS: <n>ft <direction> of <ANCHOR>, at <camera height>ft, looking <direction>
IN FRAME: <NAME> [<id>], <NAME> [<id>]
NOT IN FRAME: <ANCHOR/asset> - <why this camera cannot see it>, ...
BACKGROUND: <what closes this frame behind the subjects, from the BACKDROP line for this direction>
FOCUS: <at most 2 names from IN FRAME whose faces are sharp, the speaker first>
SHOT PROJECTION:
- <NAME> [<id>]: <lateral>, <depth>, <which side of them this lens gets>, <how readable the face is>, <what wardrobe and props are doing>
- <NAME> [<id>]: <lateral>, <depth>, <which side of them this lens gets>, <how readable the face is>
- others: <how the unnamed rest of the room reads>
PROP PLACEMENT:
- <Name> [<id>]: <where it sits in the frame>
COMPOSITION: <foreground / midground / background, depth, what the frame is built around>
LIGHT NOTE: <only what differs from the Scene Sheet, or omit>
ACTION: <beat → beat → beat>
DIALOGUE: <NAME: line, or none>
AUDIO: <ambience, foley, music, or silence>
BEATS:
- 0.0s <what starts moving>
- <t>s <what lands>
- <t>-<t>s <what runs across a stretch>
- <NAME>: motionless for the whole shot
- CAMERA: <locked / the move, for the whole shot>
END STATE:
- <NAME> [<id>]: <same measured, compass form as WORLD STATE — the next shot inherits this>
```

`WORLD STATE` is the previous shot's `END STATE` carried forward, **and it is the exact instant the
storyboard frame draws**. Write the shot's first moment there, never its outcome: *"knees giving,
still on his feet"*, not *"settling onto his back"*; *"hand closing on the grip"*, not *"gun drawn"*;
and none of the marks the action is about to leave. A `WORLD STATE` written as the outcome is the one
fault the video model cannot recover from — handed a frame where the fall has already landed and a
clip that has to contain the fall, it plays the fall **backwards**, and the film shows the man lying
down and getting up, his face re-invented through a rotation nothing in the frame supports.

### Block rules

| Block | Rule |
|---|---|
| `WORLD STATE` | **Layer 1, written first**, because every other block is measured against it. One `- NAME [id]:` line per body and per prop that matters, each a distance and a compass direction from an anchor, each facing a compass direction. The shot's **first instant**, never its outcome. |
| `CAMERA POS` | A **distance in feet** and a direction from an anchor (*"8ft south of TABLE_01, lens resting on the cloth"*), with a real camera height, plus the direction it looks. Never "a low angle nearby", and never a side without a distance. |
| **Sightline** | You see the front of a character only from the side they face. If `CAMERA POS` looks the same direction the character faces, the lens is behind their head — they cannot be in `FOCUS`, pushed in on, or given a line. See *Sightline* below. |
| *(camera fields)* | Size, angle, lens and **one** move are the shot's own fields, not a block. Cinematec dropped the `CAMERA` block in v1.0.99: it repeated the dropdowns in words and drifted from them. The image prompt's camera line and the video move are built from the fields. One move per shot. |
| `IN FRAME` | Character IDs visible in this frame, nothing else. Everyone here gets a `SHOT PROJECTION` line. |
| `NOT IN FRAME` | Everything behind the lens or cropped out, each with its reason. Derived from where `CAMERA POS` looks. A shot facing one end of the location always has entries; only a frame seeing the whole space says `none`. Nothing may sit on both lists. |
| `BACKGROUND` | What closes the frame, read off the Scene Sheet's `BACKDROP` for this direction, **with that line's distance copied, not re-invented** — stated even when the answer is darkness. |
| `FOCUS` | At most 2 names from `IN FRAME` whose faces are sharp and readable, the speaker first. Only a character the sightline check puts in front of this lens. |
| `SHOT PROJECTION` | **Layer 3.** One `- NAME [id]:` line per character, in the order the camera reads them, giving what *this lens* makes of their `WORLD STATE`: lateral, depth, which side of them the lens gets, how readable the face is. Nobody appears who is not in `IN FRAME`. Derived, never invented — a character facing north, seen by a camera looking north, gives the back of a head. |
| `PROP PLACEMENT` | One `- Name [id]:` line per prop that must sit somewhere specific. Atmosphere-only props can be skipped. |
| `LIGHT NOTE` | **Deltas only.** The Scene Sheet already carried the lighting; repeat nothing. |
| `ACTION` | Chronological beats joined by `→`. No vague verbs. |
| `DIALOGUE` | **One speaker, whose face is in this frame, saying no more words than the seconds hold.** See *Dialogue* below — this is the rule broken most often. |
| `BEATS` | **Layer 4: the clip's timeline**, and the one thing the two states cannot say. One line per beat in time order, stamped with the second it happens, starting at `0.0s` and running to the shot's full duration. Close with a line for each thing that does *not* move — a body the timeline never mentions is a body the model feels free to move, and beats that stop at 2s of a 6s clip leave four seconds it fills with invention. |
| `END STATE` | Layer 1 at the last moment, in the same measured, compass form as `WORLD STATE`. Concrete and inheritable — position, what is in whose hands, doors, damage, blood. `"unchanged from WORLD STATE"` is a real answer; *"the tension holds"* is not. |

### Screen position vocabulary

Facing is a **world** fact and lives in `WORLD STATE` as a compass direction. What that facing
*shows this lens* is a **screen** fact and lives in `SHOT PROJECTION`. Every projection line needs
both axes, plus what the lens gets of them and their eye line:

- **lateral** — `screen left`, `screen center`, `screen right`
- **depth** — `foreground`, `midground`, `background`
- **what the lens gets** — full front / three-quarter / profile / three-quarter back / back of the head
- **eye line** — where they are actually looking

```
WORLD STATE:
- AVI [avi]: 3ft south of TABLE_01, facing north up the table, thumb on his chips
SHOT PROJECTION:
- AVI [avi]: screen right, foreground, back and right shoulder to the lens, no readable face, eyes down on his chips
```

That stages. *"Avi looms nearby"* does not — and `AVI: frame left, facing screen left` states
nothing a second camera could use.

### Unnamed extras

If the room holds people this shot does not name, close `SHOT PROJECTION` with one `- others:` line saying
how they read — *cut by the frame edge, out of focus, backs to camera, no faces*. Never let a
group summary stand in for a named character's own line.

### Never re-describe faces

A character's look comes from their reference images and their asset markdown. Give position,
facing, eye line, expression, action, and continuity state — never face, hair, build, or wardrobe
design. Re-describing a face is how the model invents a second person.

What the wardrobe is **doing**, though, is continuity, not design, and leaving it out costs you the
shot: a mask on or pulled off, a hood up, gloves on, a coat bloodied, what is in which hand. Say it
on the character's own `SHOT PROJECTION` line, **and say it again from behind** — a masked man shot from the
back is staged as *the back of the mask, smooth black knit, no hair*, because a head the prompt does
not mention comes back bare, hooded, or in a hat the film has never seen.

---

## Tier 3 — what actually gets sent

### Image prompt (the first frame) - revision 3.0

Not the Scene Sheet plus the Shot Block. A short prompt, ~300 words, in this order:

1. one-line frame spec (16:9 still, no text or borders)
2. **STORY (context only)** - film title, genre, the scene summary
3. **THIS FRAME** - the shot's `MOMENT`, plus one sentence: draw this instant only, never what happens after
4. **CAMERA** - size, angle, lens; the one-line `CAMERA POS` only when no diagram is attached (rev 3.4.0)
5. **STAGING** - the attached diagram (plan + frame box + horizon = camera height); follow it, never draw it
6. **PLACE** - heading + `BACKGROUND` + "invent no buildings, skylines, lit windows or traffic"
7. **LIGHT** - the Scene Sheet's `LIGHT`
8. **STYLE**, a one-line **REFERENCE IMAGES** list ("match looks, never framing, pose or lighting"), **AVOID**

Pictures carry what words did badly: geometry -> the diagram (from `COORDS`); looks -> one reference
picture per person (full body for Medium and wider, face for Medium Close-Up and tighter) plus the
location view looking the camera's way and the props that have images. No asset descriptions are sent.

Decide what is sent **by role, never by length**: a block is sent whole or not at all.

**The image model is not given `BEATS` or `END STATE`.** It draws one instant, and an instant is all
it can draw: handed the clip's timeline and the shot's last frame as well, it splits the difference
and returns the action half-done or already finished. Those two blocks belong to the video prompt.

### Video prompt (the clip from that frame)

The first frame already fixed the appearance. **Do not re-describe what is visible in it.** Cover
only what changes:

- character movement and facial performance
- camera movement, with speed
- environmental movement (smoke, curtains, traffic)
- the beats in `BEATS` order, at their stamped seconds — this is the clip's motion trajectory, and
  handing it over is the difference between describing an event and timing one
- the end state

**Time runs forward only.** The frame is the clip's first moment. If it already shows the action
finished — the man already down, the gun already drawn, the door already open — that event is over
and the clip may not contain it: write only what still moves from here, and say the frame came back
on the wrong side of the action. Never ask for an event whose result is already in the picture; the
model can only satisfy that by undoing it. **The same goes for sound:** drop any cue for an event
that has already happened, because these engines stage what the sound describes — a body-fall named
over a body that has already landed buys you the fall played backwards.

### Negative constraints

State what must **not** change. Carry a standing set and add per-shot ones:

```
NEGATIVE: do not change character identity, hairstyle, or wardrobe; do not add people;
do not move furniture or change room architecture; do not change time of day or light source;
no camera movement beyond the one specified; no morphing; no extra fingers or limbs;
no text, captions, or watermarks.
```

---

## Worked example

### Scene Sheet — written once

```
SCENE: 1 - INT. APARTMENT - KITCHEN TABLE - NIGHT
LOCATION: Apartment - Kitchen Table [apartment-kitchen-table] - low-ceilinged 1960s tenement kitchen, one room, brown linoleum
DIMENSIONS: 16ft east-west x 13ft north-south, ceiling 8ft; origin at TABLE_01, the centre of the room
TIME: NIGHT
CAST: ARBEL [arbel], AVI [avi], YOED [yoed], NISSIM [nissim], ZOHAR [zohar], TAMIR [tamir], ZVIKA [zvika]
PROPS: Deck of Playing Cards [deck-of-playing-cards], Poker Chips [poker-chips], Seashell Ashtray [seashell-ashtray], Bowl of Pistachio Shells [bowl-of-pistachio-shells], Tray of Stuffed Peppers [tray-of-stuffed-peppers], Lipstick-Stained Glasses [lipstick-stained-glasses], Turntable and Organ Record [turntable-and-organ-record], Tablecloth [tablecloth], Cigarette Smoke Haze [cigarette-smoke-haze], Yellow Bulb Over Table [yellow-bulb-over-table]
ANCHORS:
- TABLE_01: 4ft across, round kitchen table, red floral Tablecloth, seats seven, on the origin
- DOOR_01: 3ft wide, apartment entry door, in the south wall, 6.5ft south of the origin
- BULB_01: 1ft shade, Yellow Bulb Over Table, dented tin, hung 2.6ft above TABLE_01, on the origin
- TURNTABLE_01: 2.5ft wide, Turntable and Organ Record on a sideboard, against the west wall, 8ft west of the origin
POSITIONS:
- N:  ARBEL [arbel] - dealer's chair, faces S toward DOOR_01, leaning back, deals from his own deck
- NE: NISSIM [nissim] - faces SW, elbows on the cloth
- SE: TAMIR [tamir] - faces NW, chair tipped onto its back legs
- S:  AVI [avi] - faces N, directly across from ARBEL, hunched over a short stack of chips
- SW: ZVIKA [zvika] - faces NE, notebook beside his glass
- W:  YOED [yoed] - faces E, closest to TURNTABLE_01
- NW: ZOHAR [zohar] - faces SE
LIGHT: BULB_01 is the only source — hard yellow toplight in a two-meter pool over TABLE_01, hard falloff to pure black past its edge. Cigarette Smoke Haze lies in flat blue-grey layers through the amber beam.
SCREEN DIRECTION: coverage is cut on the ARBEL(N) ↔ AVI(S) axis. Camera stays on the west side of TABLE_01. ARBEL reads screen left of AVI in every westside setup.
MOOD: sticky, smoke-cool swagger in a room sealed shut.
```

### Shot Block — one per shot, referencing the sheet

```
SHOT: SC01_SH04 - Arbel deals, Avi's hands
PURPOSE: establish Arbel's ownership of the table and bury Avi in the dark at the other end.
DURATION: 6s
WORLD STATE:
- AVI [avi]: in the south chair at TABLE_01, 3ft south of the table centre, facing north up the table, right thumb pressing a stack of chips flat, suit cuff on the cloth.
- ARBEL [arbel]: in the dealer's chair 3ft north of the table centre, facing south, leaning back with one arm over the chair back, squaring the deck.
- Poker Chips [poker-chips]: stacked on the cloth under AVI's right hand.
- DOOR_01: closed.
CAMERA POS: 3ft south of TABLE_01 just past AVI's shoulder, lens resting on the Tablecloth, camera height 2.7ft, looking north
IN FRAME: AVI [avi], ARBEL [arbel]
FOCUS: ARBEL [arbel]
SHOT PROJECTION:
- AVI [avi]: screen right, foreground, back and right shoulder to the lens, no face at all - his head is above the frame line, in black. Huge and out of focus; only his right hand and suit cuff in frame.
- ARBEL [arbel]: screen center, background, full front to the lens, face sharp and fully lit, eyes sweeping the room not the cards.
- others: extreme left and right frame edges, cut-off dark forearms and shoulders only. No faces visible.
PROP PLACEMENT:
- Poker Chips [poker-chips]: near foreground, screen right, under AVI's hand.
- Seashell Ashtray [seashell-ashtray]: low foreground, screen left, towering in the lens, heaped with butts.
- Bowl of Pistachio Shells [bowl-of-pistachio-shells]: low foreground, screen right of the ashtray.
- Lipstick-Stained Glasses [lipstick-stained-glasses]: one tumbler midground, screen right, rim toward camera.
- Turntable and Organ Record [turntable-and-organ-record]: far background, screen left, glimmering faintly in the black.
COMPOSITION: chips and ashtray tower in the low foreground, the cloth runs the length of the frame, ARBEL small and lit at the far end — depth built on the table itself.
LIGHT NOTE: BULB_01 carves ARBEL's face out of the dark with shadowed eye sockets; AVI gets no light at all.
ACTION: ARBEL squares the deck → releases a card skimming toward the lens → AVI's thumb presses his stack flat.
DIALOGUE: ARBEL: "Again? You want to lose it twice in one night?"
AUDIO: organ record thin under the room, cards on cloth, one chair creak.
BEATS:
- 0.0s ARBEL squares the deck and taps it once on the cloth
- 1.4s he releases a card, low and flat toward the lens
- 1.4-2.6s the card skims the length of the table
- 2.6s it lands 6in short of AVI's stack
- 3.0s AVI's thumb presses his stack flat
- 3.0-6.0s ARBEL holds the look, nobody else moves
- CAMERA: the slow push in runs for the whole shot
END STATE:
- AVI [avi]: unchanged in the south chair, facing north, right hand still on the chips.
- ARBEL [arbel]: unchanged in the dealer's chair, facing south, arm over the chair back.
- one card: face down on the cloth, 6in short of AVI's stack.
- DOOR_01: closed.
```

```
SHOT: SC01_SH05 - Avi, reverse
PURPOSE: first clean look at what the mockery is doing to Avi's face.
DURATION: 4s
WORLD STATE:
- AVI [avi]: in the south chair at TABLE_01, facing north, jaw set, both hands flat on the cloth either side of his chips.
- ARBEL [arbel]: in the dealer's chair 3ft north of the table centre, facing south, arm over the chair back.
- one card: face down on the cloth, 6in short of AVI's stack, where SH04 left it.
- DOOR_01: closed.
CAMERA POS: 3ft north of TABLE_01 over ARBEL's left shoulder, camera height 3.6ft (seated eye level), looking south
IN FRAME: AVI [avi], ARBEL [arbel]
FOCUS: AVI [avi]
SHOT PROJECTION:
- ARBEL [arbel]: screen left, foreground, back of his shoulder and ear only, out of focus. Reverse of SH04, so he now reads screen LEFT.
- AVI [avi]: screen center-right, midground, full front to the lens, face sharp, eyes fixed on ARBEL, not blinking.
- others: soft dark shapes at the frame edges, no faces.
PROP PLACEMENT:
- Poker Chips [poker-chips]: midground, screen right, between AVI's hands.
LIGHT NOTE: BULB_01 now rakes AVI's face from above; ARBEL's shoulder is a black mass in the foreground.
ACTION: AVI watches the card land → does not reach for it → lifts his eyes to ARBEL.
DIALOGUE: none
AUDIO: room laughter dropping away, the record continuing.
BEATS:
- 0.0s AVI's eyes stay down on the landed card
- 1.2s he still does not reach for it
- 2.0s he lifts his eyes to ARBEL
- 2.0-4.0s he holds the look; his hands leave the cloth and his right drops below the frame line
- ARBEL: motionless for the whole shot
- CAMERA: locked for the whole shot
END STATE:
- AVI [avi]: in the south chair, facing north, hands off the table, right hand below the frame line.
- ARBEL [arbel]: unchanged in the dealer's chair, facing south.
- one card: unmoved on the cloth.
- DOOR_01: closed.
```

Note what SH05 does: it flips the camera to the far side of the axis, and **says so explicitly**
(*"Reverse of SH04, so he now reads screen LEFT"*). Never leave a flip for the model to work out.

---

## Dialogue

The rule broken most often, and the most expensive one to break: a shot that breaks it looks fine on
paper, renders a frame that looks fine, and only fails once the clip has been generated and paid for.
Three conditions, all three on every shot that has a line:

**One speaker.** A clip lip-syncs one mouth. Put two names in a shot's `DIALOGUE` and the pipeline
throws one line away — it fits what it can into the seconds and drops the rest, usually without
saying so anywhere you will look. Two people talking is always two shots: a single or an
over-the-shoulder on the speaker, then the reverse for the answer.

**The line fits the seconds.** Speech runs at about 2.5 words per second, and the first half second
goes to the camera move settling, so a shot of *D* seconds holds roughly `(D - 0.5) × 2.5` words:

| Duration | Words that fit |
|---|---|
| 3s | 6 |
| 4s | 8 |
| 5s | 11 |
| 6s | 13 |
| 8s | 18 |

Count the words before you write the `DURATION`. Over budget, split the speech across consecutive
shots of the same speaker rather than stretching one shot past 8s.

**The speaker has a face in the frame.** A character your `SHOT PROJECTION` line describes as a hand, a
back, a silhouette, off-screen, or cut by the frame edge has no mouth to animate. Either give them a
face in this frame, or move the line to their own shot and leave this one silent. A character who is
*present* can be faceless; a character who *speaks* cannot.

<details>
<summary>What breaking all three at once looks like</summary>

```
DURATION: 5s
IN FRAME: ARBEL [arbel], ZVIKA [zvika]
SHOT PROJECTION:
- ZVIKA [zvika]: screen right, extreme foreground, cut by the frame edge at the wrist, no face, only
  his hand and the ballpoint pen aimed at the bottom of the deck.
DIALOGUE:
ZVIKA: The cards know nothing. The cards are cardboard. What knows things is your thumb on the
bottom of the deck.
ARBEL: My thumb is an honest thumb.
```

Two speakers, 26 words in a 5s shot that holds 11, and the first speaker has no face. The clip came
back with Arbel alone, speaking his six words; Zvika's line was gone. Fixed, it is two shots:

```
SHOT: SC01_SH03A - Zvika accuses        SHOT: SC01_SH03B - Arbel answers
DURATION: 8s                            DURATION: 4s
DIALOGUE: ZVIKA: The cards know         DIALOGUE: ARBEL: My thumb is an
nothing. What knows things is your      honest thumb.
thumb on the bottom of the deck.
```

</details>

---

## Sightline

The one geometry mistake no other block can repair, and the one that ruins a frame silently.

You see the front of a character only from the side they **face**. Take their facing from
`POSITIONS`, the camera's look direction from `CAMERA POS`, and compare:

| Camera looks | Character faces | What the lens sees |
|---|---|---|
| north | south | their face |
| north | north | the back of their head |

A shot built on a face must stand on the side that face is turned toward. Two people talking face
each other, so **their two singles are shot from opposite ends of the axis**: if one looked north up
the line, its reverse looks **south**. A "reverse" written from the same end as the shot it reverses
is not a reverse — and the image model, handed geometry it cannot satisfy, resolves it by quietly
spinning the character round to the lens. The frame then looks acceptable and the eye line is gone:
the two of them are no longer looking at each other, in this frame and in every take cut after it.

This is also why facing lives in `WORLD STATE` as a **compass direction**, not as `facing screen left`. Screen
left is where they sit in the frame; it says nothing about which way the body points, and a facing
written that way cannot be checked against where the camera stands.

## Continuity

- **Start/end state chains.** Each shot's `WORLD STATE` is the previous shot's `END STATE` unless
  the script moves it. If they do not match, the cut will not. Both are written in the same measured,
  compass form, so the match can actually be checked.
- **The previous setup travels with the shot.** A frame is told where the last camera stood and what
  closed its frame, so it knows the angle changed and the location did not. Without it, two
  consecutive shots of one place are free to disagree about the place.
- **Screen sides hold** across shots of a scene unless the action moves someone, or the camera
  crosses the axis — and a crossing is stated.
- **Carry damage forward explicitly** — blood, plaster dust, what is in whose hand — in
  `WORLD STATE` and on the `SHOT PROJECTION` line, not left to the reference images.
- **The 180-degree line** is the `SCREEN DIRECTION` line on the Scene Sheet. Break it only on
  purpose, and write down that you are breaking it.

## Cinematic rules

- Every shot needs a storytelling purpose. If `PURPOSE` is hard to write, the shot should not exist.
- Every camera movement needs a reason. No motion added just to feel cinematic.
- Cut to close-ups when emotional information warrants it; go wide when geography, scale,
  isolation, or a relationship with the environment matters.
- Reaction shots are often more important than the speaker.
- Use foreground and depth — flat centered compositions are the default failure of AI frames.
- Do not centre and symmetrize every frame. Vary coverage while preserving continuity.
- Do not change lenses shot to shot without a reason.
- Shots must connect through movement, gaze, composition, screen direction, or story logic.

## Asset consistency

Asset definitions are **authoritative**. Reference by ID everywhere, and never quietly restyle an
established character, location, wardrobe piece, or prop to make a shot work better. If a shot you
want conflicts with an asset, **report the conflict** instead of editing the asset out from under
the rest of the film.

Two further rules keep assets from blurring together:

1. **Characters must be designed apart.** When generating a character's reference images, the
   prompt must also carry the other characters' appearance as contrast — *different build, face
   shape, hair, coloring, wardrobe silhouette; do not reuse or blend in their look*. Two
   similar-looking characters will be swapped by the model somewhere in the scene.
2. **Spell asset names identically everywhere.** `Seashell Ashtray` in one shot and "the ashtray"
   in the next is two props to the model. The `[id]` is what actually pins it.

---

## Where this lives in Cinematec

The rule is enforced in code, and **the app does not read this file** — so a change here is a
change there, by hand:

**Tier 1 — the Scene Sheet**

- `prompts/scene-layout-rule.md` — the `DIMENSIONS` block, the measured `ANCHORS` lines and the
  per-direction `BACKDROP` distances, plus the rest of the Scene Sheet blocks as instructions to the model, included by
  `prompts/layout.md` (the layout job - since v1.0.95 the only writer of a layout; the shot planner no
  longer writes one). It comes back as `layout` on the result and is stored
  as `scene.layout`.
- `production.py` — `plan_shots()` requires `scene.layout` and sends it cut down by `planner_layout()`
  as `<layout>`; `plan_layout()` is the layout job (`layout` kind in `jobs.py`); `location_layouts_text()` hands it the layouts of other
  scenes at the same location as `<location_layouts_elsewhere>`, so a location keeps one set of
  anchors, one backdrop and one `NOTHING ELSE` line across the film.
- `studio.js` — `sceneLayoutPanel()` on the Shots board: the sheet, the plan, an editable text pane
  (`layoutEditorHtml()`, live plan redraw via `refreshLayoutPlan()`), Write / Rebuild layout with AI
  (`planLayout()`), Restore previous layout (`scene.layoutHistory`), and the **Rebuild the scene
  layout too** switch in the shot-count dialog. The layout is part of a frame's signature, so a
  changed layout marks every frame of the scene stale.
- `storyboard.py` — `compose_prompt()` prepends it verbatim as a `SCENE LAYOUT` section on every
  frame of that scene, stated as the authority on the room's size and every distance in it, followed
  by the Tier 3 priority order.
- `storyboard.py` — `previous_setup()` lifts the previous shot's `CAMERA POS` and `BACKGROUND` into a
  `PREVIOUS SETUP` paragraph: the camera moved, the location did not. `inherited_state()` carries
  only what the people and props did, which is why this is separate.
- `blocking.js` — `footprintOf()`, `sizeOf()`, `offsetOf()` and `heightOf()` read the numbers (feet or
  metres, digits or words); `planRoom()` draws the footprint to scale with a `scale` in pixels per foot;
  `anchorPoints()` places each anchor at its own offset and draws it at its own size, resolving
  offsets measured from another anchor in a few passes; the plan carries a scale bar and the footprint
  on its title. A layout with no `DIMENSIONS` falls back to the old fixed box and compass-slot placement,
  unchanged.
- `prompts/reshot.md` — receives it as `<scene_layout>`, fixed and authoritative, and is told not to
  return one of its own.

**Tier 2 — the Shot Block**

- `production.py` — `FRAME_PROMPT_RULE`, shared by `SHOTS_SYSTEM_PROMPT` and
  `RESHOT_SYSTEM_PROMPT`, is the instruction the shot-writing model follows for a shot's `prompt`.
- `storyboard.py` — `excluded_elements()` lifts the shot's `NOT IN FRAME` line into a hard exclusion in
  the composed image prompt, stated as overriding the asset descriptions and reference images below it.
  Without that override the asset MD wins, because it describes a landmark just as fully whether or not
  this camera can see it.
- `storyboard.py` — `background_line()` lifts the shot's `BACKGROUND` line into its own paragraph, so
  an empty far plane is asked for as empty instead of being left for the model to fill.
- `storyboard.py` — the `WORLD STATE` / `SHOT PROJECTION` / `PROP PLACEMENT` blocks beat
  `compose_prompt()`'s default ordering. Where they and the Scene Sheet disagree, the shot wins for
  that frame: the layout fixes the room, the shot fixes the frame.
- `storyboard.py` — `frame_blocks()` strips `BEATS` and `END STATE` before the prompt reaches the
  image model, and a `MOMENT:` block tells it to draw the first instant and never the outcome.
- `blocking.js` — the PLAN and FRAME wireframes drawn from the two tiers: `readLayout()` reads the
  Scene Sheet (anchors, positions, `BACKDROP` per wall, the `SCREEN DIRECTION` axis and the side the
  camera stays on), `readShotPrompt()` reads the Shot Block (`CAMERA POS` look direction, `IN FRAME`,
  `NOT IN FRAME` anchors, `BACKGROUND`, `FOCUS`, `WORLD STATE` for the compass facings, `SHOT PROJECTION`
  for screen side and depth, `BEATS`, the lens). The plan draws the axis with the
  camera's side shaded, fades excluded anchors, widens the view cone to the lens (`lensSpread()`),
  and badges a camera on the wrong side as crossing the line.

**Asset identity**

- `images.py` — `other_characters_direction()` adds the character-distinctness contrast when
  generating an asset's reference images.

**The sightline rule**

- `prompts/frame-prompt-rule.md` — the `SIGHTLINE` paragraph under `CAMERA POS`, and the
  `WORLD STATE` rule that facing is written as a compass direction so the check below has something
  to read.
- `shotcheck.py` / `shotcheck.js` — the `camera-behind-face` check: `CAMERA POS` look direction
  against each `FOCUS` name's and each speaker's own `WORLD STATE` facing; the faceless-speaker check
  reads their `SHOT PROJECTION` line. Mirrored, word for word.
- `production.drop_back_focus` (v1.0.100) — enforces the rule after every write: a non-speaker whose
  facing matches the camera's look is removed from `FOCUS`, so the check only fires on speakers and hand edits.

**The geometry checks** (`shotcheck.py` / `shotcheck.js`, mirrored, both given `scene.layout`)

- `unknown-anchor` — `CAMERA POS` measured against an anchor the layout's `ANCHORS` never placed.
- `not-in-layout` — a name on `IN FRAME` with no `POSITIONS` slot (and not on `CAST`).
- `crosses-axis` — the camera's standing side (opposite its look direction) is on the far side of
  the `SCREEN DIRECTION` line's "camera stays <dir>" and `CAMERA POS` does not say "crosses the axis".
- `lens-mismatch` — the lens field and an old (pre-v1.0.99) prompt's `CAMERA` block name different
  lenses. New shots have no `CAMERA` block, so this only fires on old ones.
- `camera-unmeasured` — `CAMERA POS` gives a side but no distance, in a scene whose layout is measured.
  Gated on the layout having `DIMENSIONS`, so scenes written before it are not nagged shot by shot.

**The measurement checks** (`shotcheck.py` `layout_problems()` / `shotcheck.js` `layoutProblems()`,
mirrored, run once per scene rather than once per shot, shown on the Shots board's layout panel by
`studio.js` `sceneLayoutPanel()`)

- `layout-unmeasured` — no `DIMENSIONS` line, so nothing in the scene has a scale. Reported alone: every
  other measurement fault is downstream of this one.
- `anchor-unmeasured` — an `ANCHORS` line with no distance, so the shots place it by compass alone.
- `backdrop-unmeasured` — a `BACKDROP` direction with no distance, so how far the frame sees that way is
  re-decided in every shot that looks there.

**The dialogue rules**

- `shotcheck.py` / `shotcheck.js` — the three conditions as code, one rule per check, with the
  message and the fix the filmmaker is shown. Mirrored implementations that must stay word for word
  identical; the Python one is what stamps a warning onto a finished take.
- `prompts/shots.md` (as five short bullets) and `prompts/reshot.md` — the same conditions as instructions
  to the models, so they stop producing shots that break them.
- `production.py` — `_with_faults()` appends a count of unfilmable shots to the plan's notes the
  moment a scene is planned.
- `studio.js` — `shotFaultsHtml()` puts each fault and its fix on the shot card; `sceneFaultsText()`
  tallies them per scene.
- `storyboard.js` — the take panel and the Film confirmation list the same faults before any money
  is spent; `video.py` `suitability()` stamps them onto the take afterwards.

**Tier 3 — what is sent**

- `storyboard.py` — `STANDING_NEGATIVE` is the standing negative-constraint line on every frame prompt.
- `video.py` — `prompt_block()` puts the shot's `END STATE` into the video director's brief and the
  fallback prompt, so the clip ends where the next shot starts, and its `BEATS` in as the clip's
  timeline. It reads both prose blocks and bulleted ones.
- `tools/check-shot-format.py` / `tools/check-shot-format.js` — every reader of the format checked
  against one worked shot, because five files parse it and none of them owns it.

**Still open:** the video prompt and per-shot negative constraints are not separate stored fields yet.
Shot IDs, `PURPOSE`, `BEATS`, `WORLD STATE` and `END STATE` live inside the prompt text rather than as
structured fields.

## Checklists

**Scene Sheet**

- [ ] `DIMENSIONS` gives the footprint in feet and names the origin
- [ ] Every anchor carries a size and an offset in feet from that origin
- [ ] Every `BACKDROP` direction says how far out it sits
- [ ] Every anchor named and placed relative to the room
- [ ] Every cast member has a compass/seat slot *and* a facing direction
- [ ] `BACKDROP` closes every direction and ends with a `NOTHING ELSE:` line
- [ ] Light sources placed relative to an anchor
- [ ] `SCREEN DIRECTION` states the axis coverage is cut on
- [ ] Every asset carries its `[id]`

**Each shot**

- [ ] `PURPOSE` is a real storytelling reason
- [ ] `CAMERA POS` gives a distance in feet from an anchor, and states camera height
- [ ] `BACKGROUND` copies the `BACKDROP` distance rather than inventing one
- [ ] One camera move, written start → end
- [ ] `NOT IN FRAME` lists what this camera is turned away from; `BACKGROUND` says what closes the frame
- [ ] `WORLD STATE` places every body and prop by distance and compass direction from an anchor
- [ ] `WORLD STATE` is the shot's **first instant**, not its outcome — no marks the action has yet to leave
- [ ] Everyone in `IN FRAME` has their own `SHOT PROJECTION` line — nobody summarized into a group
- [ ] Every `SHOT PROJECTION` line gives lateral, depth, what the lens gets of them, eye line
- [ ] No screen-relative word appears in `WORLD STATE`; no compass facing is re-decided in `SHOT PROJECTION`
- [ ] Unnamed people covered by one `- others:` line
- [ ] No face, hair, build, or wardrobe design described anywhere
- [ ] `LIGHT NOTE` carries deltas only — the room's light is already on the Scene Sheet
- [ ] `DIALOGUE` has at most one speaker
- [ ] The line fits the duration at 2.5 words per second
- [ ] The speaker has a face in this frame, not a hand or a back
- [ ] `BEATS` starts at `0.0s`, reaches the full duration, and names what does *not* move
- [ ] `WORLD STATE` matches the previous shot's `END STATE`
- [ ] No beat in the clip replays something the first frame already shows finished
- [ ] Screen sides agree with `SCREEN DIRECTION`; any axis crossing is stated
- [ ] Video prompt describes only change, not appearance
- [ ] Negative constraints attached
