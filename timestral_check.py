"""
timestral_check.py
---------
Può cadere ancora? Previsione dell'accelerazione verticale dell'IMU con
Timestral (Mistral, modello di serie temporali, gira in locale):
1. backtest a finestre mobili: dal solo passato, avrebbe visto arrivare
   la caduta delle 42 s?
2. previsione dei ~4 s dopo la fine della registrazione.

Dipendenze: pip install torch git+https://github.com/mistralai/timestral.git
            (più quelle di fall_checks.py). I pesi (~840 MB) li scarica da
            Hugging Face al primo avvio.
"""

from __future__ import annotations

import numpy as np
from timestral import TimestralForecaster

import fall_checks as fc

MODEL = "mistralai/Timestral-209M"
CTX = 2048          # passi di contesto (~8 s a 250 Hz)
H = 128             # orizzonte (~0.5 s)
STEP_S = 0.25       # passo tra i tagli del backtest
FREE_FALL = 1.0     # m/s², stessa soglia della query Mosaico


def backtest(f: TimestralForecaster, t: np.ndarray, az: np.ndarray) -> np.ndarray:
    """Righe (t_taglio, min q01, min q05, min reale) per ogni taglio."""
    fs = 1 / np.median(np.diff(t))
    cuts = list(range(CTX, len(az) - H, int(STEP_S * fs)))
    ctx = np.stack([az[i - CTX:i] for i in cuts])
    q = np.concatenate([f.forecast(ctx[k:k + 32], prediction_length=H).quantiles[:, 0]
                        for k in range(0, len(ctx), 32)])
    return np.array([(t[i], q[k, :, 0].min(), q[k, :, 1].min(), az[i:i + H].min())
                     for k, i in enumerate(cuts)])


def main() -> None:
    rec = fc.load()
    t, az = rec.imu[:, 0], rec.imu[:, 1]
    f = TimestralForecaster.from_pretrained(MODEL)

    rows = backtest(f, t, az)
    print(" t_cut  min_q01  min_q05  min_true")
    print("-- tagli con caduta reale nell'orizzonte --")
    for r in rows[rows[:, 3] < FREE_FALL]:
        print("%6.2f %8.2f %8.2f %8.2f" % tuple(r))
    print("-- 8 tagli con la coda bassa più ampia --")
    for r in rows[np.argsort(rows[:, 1])[:8]]:
        print("%6.2f %8.2f %8.2f %8.2f" % tuple(r))
    print("tagli con q05 < %.0f m/s²: %d su %d" % (FREE_FALL, (rows[:, 2] < FREE_FALL).sum(), len(rows)))

    fut = f.forecast(az[-4 * CTX:], prediction_length=1024).quantiles[0, 0]
    print("dopo la fine (~4 s): min q01 %.2f, min q05 %.2f, min mediana %.2f m/s²"
          % (fut[:, 0].min(), fut[:, 1].min(), fut[:, 10].min()))


if __name__ == "__main__":
    main()
