# TODO — Mosaico challenge YB-42 (deadline 2026-11-19)

## Environment (checked 2026-11-16)
- Local PC cannot host `mosaicod`: Windows 10 LTSC 2019 (build 17763, updates
  frozen by IT) → no WSL2 / Docker Desktop; virtualization off in firmware.
- Official binaries are Linux-only; the install script needs systemd.
- Native Windows build failed (no MinGW `dlltool`); abandoned.
- Python SDK `pip install mosaicolabs` (0.7.0) installs fine on Windows.
- Decision: run everything in **GitHub Codespaces** (120 core-h/month free,
  resets monthly; blocked, not billed, without a payment method).
- The `devcontainers/python` image breaks the docker-in-docker feature (yarn
  apt key, exit 100 → recovery mode); `universal:2` works.

## Result (2026-11-16)
- Query: `QueryOntologyCatalog(IMU.Q.acceleration.z.between([-1.0, 1.0]))`
- One window on `/imu/body`: 1795181862000000000 → 1795181862124000000 ns
  (0.124 s, 42.000 s after recording start, 2026-11-20T13:37:42Z).
- Answer, bonus and fact-checked observations: `FINDINGS.md`.
- Form files (PDF per bonus field) prepared outside the repo, in
  `_debug/2026-11-16_mosaico_challenge_form/`.

## Next
- [ ] Submit via the form (same email as Luma) before 2026-11-19.
- [ ] After the deadline: decide whether to make the repo public.
- [ ] Open question: what lifts the body before 42.0 s (not a jump, not a
      turn aid; log mentions a gantry with 70 % gravity compensation).
- [ ] Possible exercise: optimal lean in turns vs v·ω, load transfer on the
      feet, disturbances (wind, payload) found with Mosaico queries.
