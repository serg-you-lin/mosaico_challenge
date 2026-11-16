# TODO — Mosaico challenge YB-42 (deadline 2026-11-19)

## Environment (checked 2026-11-16)
- Local PC cannot host `mosaicod`: Windows 10 LTSC 2019 (build 17763, updates
  frozen by IT) → no WSL2 / Docker Desktop; virtualization off in firmware.
- Official binaries are Linux-only; the install script needs systemd.
- Native Windows build failed (no MinGW `dlltool`); abandoned.
- Python SDK `pip install mosaicolabs` (0.7.0) installs fine on Windows.
- Decision: run everything in **GitHub Codespaces** (120 core-h/month free,
  resets monthly; blocked, not billed, without a payment method).

## Next
- [ ] Create a private GitHub repo with CHALLENGE.md, mcap, metadata.
- [ ] Add `.devcontainer/` (Python + docker-in-docker) and the compose file
      from docs.mosaico.dev/getting_started (postgres:18 + mosaicod).
- [ ] In the Codespace: `docker compose up -d`, `pip install mosaicolabs`,
      run `mosaicolabs.ros_injector` as in CHALLENGE.md.
- [ ] Single query: IMU vertical acceleration ≈ 0 → start timestamp (UTC ns).
- [ ] Bonus: camera frames and odometry/tf around that window.
- [ ] Submit via the form (same email as Luma).
