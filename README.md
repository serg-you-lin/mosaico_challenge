# mosaico_challenge

Mission YB-42 (see `CHALLENGE.md`), run in GitHub Codespaces.

Opening the Codespace installs the `mosaicolabs` SDK and starts `mosaicod`
+ Postgres with `docker compose` (`compose.yaml`). Then:

```bash
docker compose ps                     # mosaicod up on :6726
mosaicolabs.ros_injector spot_yb42.mcap --name spot_yb42 --metadata sequence_metadata.json
```
