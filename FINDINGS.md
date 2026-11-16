# Mission YB-42 — findings

## Answer

**Free-fall start: `1795181862000000000` ns UTC** (2026-11-20T13:37:42.000000000Z),
42.000 s after the start of the recording. The window ends at
`1795181862124000000` ns, so it lasts 0.124 s.

Single Mosaico query (`freefall_query.py`):

```python
from mosaicolabs import IMU, MosaicoClient, QueryOntologyCatalog

query = QueryOntologyCatalog(IMU.Q.acceleration.z.between([-1.0, 1.0]))
with MosaicoClient.connect("localhost", 6726) as client:
    for item in client.query(query):
        for topic in item.topics:                 # -> /imu/body
            for cluster in topic.clusterize():
                print(cluster.timerange.start, cluster.timerange.end)
```

The query matches one window only, on `/imu/body`. The drop of the vertical
acceleration from ~11 m/s² to ~0 is a clean step, so the start does not
depend on the ±1 m/s² threshold (`media/fall_42s.png`, top panel).

An accelerometer measures specific force, not acceleration. Standing on
the ground it reads about +9.8 m/s² (the floor pushes up). In free fall
nothing pushes, so it reads about 0. The impact afterwards gives the spike.

## Bonus — what it saw, where it walked

- **Where:** seen from above, the odometry path spells **MOSAICO**
  (`media/path.png`). The fall happens on the left leg of the **A**.
- **What:** at 42 s the front camera is looking at a **"DON'T PANIC"** sign
  with a pink object next to it (`media/camera_fall_39-46s.mp4`; full run in
  `media/camera_front.mp4`, made with `camera_to_mp4.py`).
- **Mission log** (`/robot/status`), 2.5 s before:
  `[WARN] perception: unidentified object ahead (class: towel?)`; after:
  `[WARN] imu: transient on /imu/body, logged for review`, then
  `recovered. don't panic.` The firmware is `4.2.0-hhgttg` and the run ends
  with `so long, and thanks for all the fish`.

So the operator's "nothing happened" is not true: the event was logged, then
filed as an IMU transient.

## Data checks (`fall_checks.py`)

| Check | Result |
|---|---|
| Foot load cells inside the window | all four within ±5 N (vs ~330 N total weight on average): **no foot on the ground** |
| Body height (odom z) inside the window | a parabola with **g = 9.79 m/s²**: gravity was **not** switched off, the body was ballistic |
| Body height overall | rises ~6 cm before 42.0 s, peaks at 42.04 s, lands ~5.8 cm below the start height at 42.24 s |
| Just before (41.88–42.00 s) | feet carry ≤ 60 N in total, yet the body is rising and the IMU reads ~11 m/s² |
| Landing | peak foot loads up to ~9 kN (FL) and ~5.7 kN (HR), many times the body weight |
| Camera | ~8 fps → only **one frame** falls inside the 0.124 s window |

The data is consistent with a real fall, not an accelerometer glitch alone:
the load cells, the IMU and the odometry agree, and the fitted g matches
Earth's.

The pre-fall phase is the odd part. Something other than the legs pushes
the body up with more than 1 g while the feet are almost unloaded, then
lets go at 42.000 s. The mission log mentions at 1.0 s `gantry engaged,
gravity compensation 70%`. An external support (a gantry, or a scripted
force in the simulator) lifting the robot and then releasing it would fit
the data. **This is a hypothesis; the data shows the effect, not the
cause.** The average foot load (~330 N, ~33.6 kg) is roughly the full
weight of a Spot. That does not obviously match a 70 % gravity compensation
during walking, and it is also left open.

## Observations (Federico)

- **The video shows nothing.** Watching the camera, at 42 s nothing seems to
  happen. The check above explains why: the camera runs at ~8 fps and the
  flight lasts 0.124 s, so a single frame covers it. So either the robot fell and
  got back up within a fraction of a second, or there was a software issue.
- **A simulated world.** The yard looks like a game-engine scene (Unity /
  Unreal style). My first idea was that gravity had been removed or lowered
  on purpose to see what happens, or that the accelerometer had a bug. The
  data says gravity was normal during the flight (fit g = 9.79 m/s²) and the
  three sensors agree, which points to a real lift-and-drop rather than to
  either of those.
- **The path is not random.** From the front camera the robot seems to
  wander around the yard without a goal. Seen from above it does not: the
  path spells **MOSAICO** (`media/path.png`), letter by letter, from the M
  at x ≈ −1 m to the final O at x ≈ 13 m.
- **Leaning into turns.** When it turns it leans slightly toward the inside,
  like an F1 driver's head against lateral g. The data confirms the
  direction: the roll correlates with the centripetal acceleration v·ω with
  r = −0.47 over 2025 turning samples. With ROS axes, negative means the
  robot leans **into** the turn. The slope is about −5° per m/s².
- **Maybe it jumped.** Another option for the rise-and-drop is that the robot
  made a small jump.
  - *Fact check — not supported by the load cells.* A jump needs the legs
    to push harder than the body weight (~330 N) during take-off. While
    the body is rising and the IMU reads 11–12 m/s² (net upward push
    larger than gravity), the total foot load is lower than the weight,
    not higher: mean 121 N (max 184 N) in 41.80–41.88 s and 3 N (max 44 N)
    in 41.88–42.00 s. In 41.70–41.80 s it is around the weight (mean
    314 N, max 461 N), with no take-off peak. The push that lifts the body
    does not come from the feet. A jump would fit only if the load cells
    were wrong at that moment, while they read about the full weight over
    the rest of the run.
- **The fall may go unseen because only one frame covers it.** Watching the
  video, nothing seems to happen at 42 s. The likely reason is that the
  camera catches a single frame of the flight.
  - *Fact check — confirmed.* Camera timestamps around the event are
    41.912, **42.036**, 42.160, 42.284 s: exactly one frame (42.036 s) falls
    inside the 0.124 s window. Measuring the change between consecutive
    frames (mean absolute grey-level difference), the frames around the
    take-off and the flight change by 22–23, the 64th–65th percentile of
    the whole run. At the landing (42.160 → 42.284 → 42.408 s) the change
    goes up to 33–34, the 89th–90th percentile, with a vertical image
    shift of 8–11 px. That is a visible jolt, but within the range of
    normal walking (95th percentile: 37). So the event is in the video,
    but at 8 fps it looks like an ordinary step.
- **Maybe a lift to turn 180° at the top of the A.** The external lift
  could be an artifact of the simulation to turn the robot around at the
  tip of the A, the sharpest point of the path, where the robot may not be
  able to reverse in so little space without help.
  - *Fact check — not supported.* (1) At the moment of the lift the robot
    is not turning: from 41.9 to 43.1 s it walks straight up the left leg
    of the A, heading steady at 69–73°, speed ~0.85 m/s; the previous turn
    at the bottom of the leg is already over. (2) The turn at the tip of
    the A (~145°, at (6.31, 3.79) m) happens at 43.3–44.5 s, more than a
    second after the landing: the robot slows down, steps backwards
    (v ≈ −0.35 m/s) and rotates on its own. (3) It is not the only sharp
    reversal: the path has six more where the direction of motion turns
    by 150–178° (top of the S at 33.2 s; bottom of the A's right leg at
    46.0 s; the A's crossbar at 48.3 s; the bar of the I at 55.3 and
    56.3 s; top of the C at 65.3 s). The Mosaico query finds a single
    free-fall window in the whole run, so all of those were done without
    a lift. The data shows the lift is not tied to a turn; its purpose
    stays unknown.
- **Can it fall again?** Ask a forecasting model whether the IMU signal
  points to another fall: Mistral's Timestral (time-series foundation
  model, 209M, run locally on CPU) on `/imu/body` acceleration z, 8 s of
  context, 0.5 s horizon, one cut every 0.25 s (`timestral_check.py`).
  - *Fact check — no second fall in the data; the model would not have
    seen the first one coming either.* (1) Outside 42.00–42.14 s, acc_z
    never goes below 1 m/s²; below 3 m/s² there are only three single
    samples (4 ms each) at 43.89, 57.52 and 66.67 s, against 35
    consecutive samples for the real fall. (2) Backtest: at the two cuts
    whose horizon contains the fall (41.67 and 41.92 s) the forecast's
    1 % quantile stays above 5 m/s², while the real minimum is −0.74.
    In none of the 316 cuts does the 5 % quantile go below 1 m/s². (3)
    The lower tail widens only *after* the fall, when the fall is inside
    the context (1 % quantile down to −6.1 m/s² at 42.42 s). The model
    learns "falls happen" from the event; it does not predict it. (4)
    Past the end of the run (4 s) the 1 % quantile stays above 5.2 m/s²:
    no fall forecast. This fits the earlier checks: the fall is caused
    by an external push, which the IMU history alone does not contain.
    Whether it can happen again depends on that cause, which stays unknown.
- **So the fall was put in artificially.** The forecasting test makes me
  think the fall was inserted into the world on purpose, by removing
  gravity, or that it comes from an accelerometer error.
  - *Fact check — the two mechanisms are refuted, the "artificial" part
    is supported.* (1) *Gravity removed:* no. During the flight the body
    height follows a parabola with g = 9.79 m/s²: gravity is there. What
    defies physics is the phase *before*: the body rises at more than 1 g
    while the feet are almost unloaded. (2) *Accelerometer error only:*
    no. The load cells (all four feet within ±5 N) and the odometry (the
    parabola) show the same event as the IMU. (3) *Artificial:* yes,
    several signs that the event was written into the data rather than
    lived by a robot (`fall_checks.py`, `artifact_report`):
    - acc z jumps from 11.08 to −0.74 m/s² in **one sample** (41.996 →
      42.000 s), and the window starts at exactly **42.000 s** (42, the
      Hitchhiker's Guide answer, like the "towel?" in the log, "don't panic" and
      firmware `4.2.0-hhgttg`; the metadata says "nothing happened at
      42s. probably.");
    - in flight the IMU noise is std 0.10 m/s², 13× lower than the
      high-frequency noise over the run (1.37);
    - the parabola on odom z fits with an RMS residual of 6e-7 m, against
      2–5e-4 m on 0.124 s walking stretches. Weak sign: odometry is 25 Hz,
      so only 4 points;
    - the legs keep walking through the flight as if nothing happened:
      the joints repeat the previous gait cycle (period 1.128 s) with a
      mean difference of 0.027 rad, no larger than in normal walking
      (0.037–0.044). No reaction to losing ground contact.
  - *What else it could be (lateral, not verified):* (a) the most likely:
    the challenge authors scripted a ballistic hop into a synthetic log,
    with all sensors generated consistently; (b) a physics-engine
    "depenetration" pop: when a body intersects an object, the solver
    pushes it out with a large force, which would lift the body with the
    feet unloaded. The "unidentified object (towel?)" logged 2.5 s
    earlier, about 2 m ahead at 0.85 m/s, could be that object. Not
    checkable: the log has no object pose; (c) the gantry of the log
    lifting and releasing the robot (see above). The data cannot tell
    these apart.

## Closing note

The whole recording is a Hitchhiker's Guide to the Galaxy reference: the
fall at exactly 42 s, the "(class: towel?)" in the mission log, "DON'T PANIC", firmware `4.2.0-hhgttg`,
"so long, and thanks for all the fish". The checks above (load cells,
odometry, joints, camera, a forecasting model) were a way to put the data
to the test with different tools, not an attempt to find a physical cause
for a scripted event. The answer is 42; working out the question is left
to a computer with 7.5 million years to spare.

## Proposed follow-up exercise

Recover from the data the lean angle the controller considers optimal for
a given turn, and find when it does or does not compensate enough:

1. Model the lean target as a function of v·ω (the ideal for a rigid body
   is atan(v·ω / g)) and estimate what the controller actually commands.
2. Use the foot load cells to measure the left/right load transfer in
   turns: good compensation keeps it balanced, under-compensation shifts
   load to the outer feet.
3. Repeat in the simulator with disturbances (side wind, payload changes,
   different inertia) and use Mosaico queries to find the moments where the
   load transfer exceeds a threshold, i.e. where the robot under-compensates.

## Reproduce

```bash
./run.sh                        # Codespace: start mosaicod, ingest, run the query
python camera_to_mp4.py         # front camera -> MP4, read from Mosaico
python fall_checks.py           # numbers above + media/*.png (reads the .mcap)
python timestral_check.py       # "can it fall again?" with Timestral (torch, ~840 MB weights)
```
