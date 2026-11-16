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
- **Leaning into turns.** The robot keeps walking around the yard without
  an apparent goal, and when it turns it leans slightly toward the inside,
  like an F1 driver's head against lateral g. The data confirms the
  direction: the roll correlates with the centripetal acceleration v·ω with
  r = −0.47 over 2025 turning samples. With ROS axes, negative means the
  robot leans **into** the turn. The slope is about −5° per m/s².

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
```
