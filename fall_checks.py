"""
fall_checks.py
---------
Controlli sui dati attorno alla caduta libera e sull'inclinazione in curva,
letti direttamente da spot_yb42.mcap. Stampa i numeri citati in FINDINGS.md
e salva i grafici in media/.

Dipendenze: pip install mcap mcap-ros2-support numpy matplotlib
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

HERE = Path(__file__).resolve().parent
MCAP_PATH = HERE / "spot_yb42.mcap"
MEDIA = HERE / "media"
# Finestra trovata da freefall_query.py, in secondi dall'inizio della registrazione
FALL_S = (42.0, 42.124)


@dataclass
class Recording:
    t0_ns:      int
    imu:        np.ndarray                    # t, acc_z
    odom:       np.ndarray                    # t, x, y, z, v_x, omega_z, roll, yaw
    feet:       dict[str, np.ndarray] = field(default_factory=dict)  # t, F_z
    status:     list[tuple[float, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def load(mcap_path: Path = MCAP_PATH) -> Recording:
    """Legge i topic che servono ai controlli; tempi in secondi dall'inizio."""
    with open(mcap_path, "rb") as f:
        reader = make_reader(f, decoder_factories=[DecoderFactory()])
        t0 = reader.get_summary().statistics.message_start_time
        imu, odom, feet, status = [], [], {}, []
        for _, ch, msg, m in reader.iter_decoded_messages():
            t = (msg.log_time - t0) / 1e9
            if ch.topic == "/imu/body":
                imu.append((t, m.linear_acceleration.z))
            elif ch.topic == "/robot/odom":
                p, q, v = m.pose.pose.position, m.pose.pose.orientation, m.twist.twist
                odom.append((t, p.x, p.y, p.z, v.linear.x, v.angular.z, _roll(q), _yaw(q)))
            elif ch.topic.startswith("/contact/"):
                feet.setdefault(ch.topic.rsplit("/", 1)[-1], []).append((t, m.wrench.force.z))
            elif ch.topic == "/robot/status":
                status.append((t, m.data))
    return Recording(t0, np.array(imu), np.array(odom),
                     {k: np.array(v) for k, v in sorted(feet.items())}, status)


def fall_report(rec: Recording) -> None:
    """Carico dei piedi e quota del corpo prima, durante e dopo la finestra."""
    lo, hi = FALL_S
    print(f"Foot load F_z [N]   before (40-41.9 s) | during ({lo}-{hi} s) | peak after")
    for name, a in rec.feet.items():
        before = _between(a, 40.0, 41.9)[:, 1].mean()
        during = _between(a, lo, hi)[:, 1]
        after = _between(a, hi, 42.5)[:, 1].max()
        print(f"  {name}: {before:7.1f} | {during.min():6.1f} .. {during.max():5.1f} | {after:7.1f}")
    total = sum(a[:, 1].mean() for a in rec.feet.values())
    print(f"Mean total foot load over the run: {total:.0f} N (~{total / 9.81:.1f} kg)")
    z = rec.odom
    z_before = _between(z, 41.0, 41.9)[:, 3].mean()
    z_min = _between(z, lo, 42.4)[:, 3].min()
    print(f"Body height (odom z): {z_before:.3f} m before, min {z_min:.3f} m after "
          f"(drop {100 * (z_before - z_min):.1f} cm); free fall over "
          f"{hi - lo:.3f} s would be {100 * 0.5 * 9.81 * (hi - lo) ** 2:.1f} cm")
    # Se la gravità fosse stata tolta la quota non seguirebbe una parabola con g ~ 9.81
    w = _between(z, lo - 1e-3, hi + 1e-3)
    c = np.polyfit(w[:, 0] - lo, w[:, 3], 2)
    print(f"Parabola fit on odom z inside the window ({len(w)} points): "
          f"g = {-2 * c[0]:.2f} m/s^2, initial vertical speed {c[1]:.2f} m/s")
    # Prima della finestra: piedi quasi scarichi ma corpo che sale -> spinta esterna
    pre = (41.88, lo)
    feet_max = sum(_between(a, *pre)[:, 1].max() for a in rec.feet.values())
    acc = _between(rec.imu, *pre)[:, 1].mean()
    print(f"Just before ({pre[0]}-{pre[1]} s): sum of foot loads <= {feet_max:.0f} N, "
          f"IMU acc z mean {acc:.1f} m/s^2, body rising")
    print(f"Camera at ~8 fps -> {(hi - lo) * 8.06:.1f} frames inside the window")


def lean_report(rec: Recording, min_omega: float = 0.05) -> None:
    """Correla il roll con l'accelerazione centripeta v*omega nelle curve."""
    o = rec.odom
    turning = (np.abs(o[:, 5]) > min_omega) & (np.abs(o[:, 5]) < 3.0)
    centripetal = o[turning, 4] * o[turning, 5]
    roll_deg = np.degrees(o[turning, 6])
    corr = np.corrcoef(centripetal, roll_deg)[0, 1]
    slope = np.polyfit(centripetal, roll_deg, 1)[0]
    print(f"Turning samples: {turning.sum()}  corr(roll, v*omega) = {corr:.2f}  "
          f"slope = {slope:.2f} deg per m/s^2")
    # ROS: y a sinistra, roll > 0 abbassa il lato destro. In curva a sinistra
    # (v*omega > 0) piegarsi verso l'interno vuol dire roll < 0: correlazione negativa.
    print("  negative -> leans INTO the turn" if corr < 0 else "  positive -> leans OUT of the turn")


def turn_report(rec: Recording, window_s: float = 0.6, min_turn_deg: float = 150.0) -> None:
    """Direzione del corpo attorno alla caduta e inversioni di marcia su tutto il percorso."""
    o = rec.odom
    for t in (41.5, 41.9, 42.0, 42.124, 42.5, 43.1):
        k = np.argmin(np.abs(o[:, 0] - t))
        print(f"  t={o[k, 0]:6.2f} s  pos=({o[k, 1]:.2f}, {o[k, 2]:.2f})  "
              f"yaw={math.degrees(o[k, 7]):6.1f} deg  v={o[k, 4]:.2f} m/s")
    # Inversione = direzione del moto nei window_s prima e dopo che differisce di > min_turn_deg
    print(f"Reversals of the direction of motion (> {min_turn_deg:.0f} deg):")
    last = -10.0
    for t in np.arange(window_s + 0.1, o[-1, 0] - window_s, 0.04):
        a, da = _motion_dir(o, t - window_s, t)
        b, db = _motion_dir(o, t, t + window_s)
        turn = abs((math.degrees(b - a) + 180) % 360 - 180)
        if turn > min_turn_deg and min(da, db) > 0.1 and t - last > 1.0:
            k = np.argmin(np.abs(o[:, 0] - t))
            print(f"  t={t:6.2f} s  pos=({o[k, 1]:.2f}, {o[k, 2]:.2f})  turn={turn:.0f} deg")
            last = t


def plots(rec: Recording) -> None:
    """Salva media/path.png e media/fall_42s.png."""
    MEDIA.mkdir(exist_ok=True)
    o = rec.odom
    k = np.argmin(np.abs(o[:, 0] - FALL_S[0]))
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(o[:, 1], o[:, 2], lw=1)
    ax.plot(o[0, 1], o[0, 2], "go", label="start")
    ax.plot(o[-1, 1], o[-1, 2], "ks", label="end")
    ax.plot(o[k, 1], o[k, 2], "r*", ms=15, label="free fall, 42 s")
    ax.set_aspect("equal"); ax.grid(alpha=.3); ax.legend(loc="lower right")
    ax.set_title("Odometry x-y [m]")
    fig.tight_layout(); fig.savefig(MEDIA / "path.png", dpi=110); plt.close(fig)

    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    a = _between(rec.imu, 41.5, 42.8)
    axs[0].plot(a[:, 0], a[:, 1]); axs[0].set_ylabel("IMU acc z [m/s²]")
    for name, f in rec.feet.items():
        b = _between(f, 41.5, 42.8)
        axs[1].plot(b[:, 0], b[:, 1], label=name)
    axs[1].set_ylabel("foot F_z [N]"); axs[1].set_yscale("symlog", linthresh=100)
    axs[1].legend(ncol=4, fontsize=8)
    b = _between(o, 41.5, 42.8)
    axs[2].plot(b[:, 0], b[:, 3]); axs[2].set_ylabel("odom z [m]"); axs[2].set_xlabel("s")
    for ax in axs:
        ax.axvspan(*FALL_S, color="r", alpha=.2); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(MEDIA / "fall_42s.png", dpi=110); plt.close(fig)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _roll(q) -> float:
    """Roll in radianti da un quaternione ROS."""
    return math.atan2(2 * (q.w * q.x + q.y * q.z), 1 - 2 * (q.x * q.x + q.y * q.y))


def _yaw(q) -> float:
    """Yaw in radianti da un quaternione ROS."""
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def _motion_dir(o: np.ndarray, lo: float, hi: float) -> tuple[float, float]:
    """Direzione (rad) e lunghezza (m) dello spostamento x-y in [lo, hi)."""
    w = _between(o, lo, hi)
    dx, dy = w[-1, 1] - w[0, 1], w[-1, 2] - w[0, 2]
    return math.atan2(dy, dx), math.hypot(dx, dy)


def _between(a: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Righe con tempo (colonna 0) in [lo, hi)."""
    return a[(a[:, 0] >= lo) & (a[:, 0] < hi)]


def main() -> None:
    rec = load()
    for t, text in rec.status:
        print(f"[{t:6.2f} s] {text}")
    print()
    fall_report(rec)
    print()
    lean_report(rec)
    print()
    turn_report(rec)
    plots(rec)
    print(f"\nPlots saved in {MEDIA}")


if __name__ == "__main__":
    main()
