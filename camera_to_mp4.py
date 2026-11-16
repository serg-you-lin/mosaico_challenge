"""
camera_to_mp4.py
---------
Prende i fotogrammi della camera frontale e li salva in un MP4 H.264
visibile su qualsiasi schermo/player.

Sorgenti:
  --source mosaico  (default) legge dal server Mosaico (sequenza spot_yb42),
                    da usare nel Codespace dopo run.sh.
  --source mcap     legge spot_yb42.mcap direttamente, senza server
                    (serve anche: pip install mcap-ros2-support).

Esempi:
    python camera_to_mp4.py                         # video intero
    python camera_to_mp4.py --start 39 --end 46     # solo attorno alla caduta
"""

from __future__ import annotations

import argparse
import io
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import av
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SEQUENCE = "spot_yb42"
TOPIC = "/camera/front/image"
MCAP_PATH = HERE / "spot_yb42.mcap"
# Finestra di caduta libera trovata da freefall_query.py
FREE_FALL_NS = (1795181862000000000, 1795181862124000000)


@dataclass
class CameraFrame:
    timestamp_ns:   int
    image:          Image.Image


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def frames_from_mosaico(start_s: float | None = None, end_s: float | None = None,
                        host: str = "localhost", port: int = 6726) -> tuple[list[CameraFrame], int]:
    """Legge i fotogrammi dal server; ritorna (fotogrammi, timestamp del primo fotogramma del topic)."""
    from mosaicolabs import CompressedImage, MosaicoClient

    with MosaicoClient.connect(host, port) as client:
        handler = client.topic_handler(SEQUENCE, TOPIC)
        if handler is None:
            raise SystemExit(f"topic {TOPIC} non trovato nella sequenza {SEQUENCE}: hai lanciato run.sh?")
        t0 = handler.get_data_streamer().next_timestamp()
        # Ogni get_data_streamer() chiude il precedente: il primo serviva solo per t0
        streamer = handler.get_data_streamer(*_window_ns(t0, start_s, end_s))
        frames = [CameraFrame(msg.timestamp_ns, msg.get_data(CompressedImage).to_image())
                  for msg in streamer]
        handler.close()
    return frames, t0


def frames_from_mcap(start_s: float | None = None, end_s: float | None = None,
                     mcap_path: Path = MCAP_PATH) -> tuple[list[CameraFrame], int]:
    """Come frames_from_mosaico, ma leggendo il .mcap direttamente."""
    from mcap.reader import make_reader
    from mcap_ros2.decoder import DecoderFactory

    with open(mcap_path, "rb") as f:
        reader = make_reader(f, decoder_factories=[DecoderFactory()])
        raw = [(msg.log_time, bytes(ros_msg.data))
               for _, _, msg, ros_msg in reader.iter_decoded_messages(topics=[TOPIC])]
    t0 = raw[0][0]
    lo, hi = _window_ns(t0, start_s, end_s)
    frames = [CameraFrame(t, Image.open(io.BytesIO(jpeg)).convert("RGB"))
              for t, jpeg in raw
              if (lo is None or t >= lo) and (hi is None or t < hi)]
    return frames, t0


def write_mp4(frames: list[CameraFrame], out_path: Path, t0_ns: int,
              scale: int = 3, overlay: bool = True) -> float:
    """Scrive l'MP4 a fps costante pari a quello medio della registrazione; ritorna gli fps."""
    if len(frames) < 2:
        raise ValueError("servono almeno 2 fotogrammi")
    duration_s = (frames[-1].timestamp_ns - frames[0].timestamp_ns) / 1e9
    fps = (len(frames) - 1) / duration_s

    # H.264 con yuv420p vuole lati pari
    width = (frames[0].image.width * scale) // 2 * 2
    height = (frames[0].image.height * scale) // 2 * 2

    with av.open(str(out_path), mode="w") as container:
        stream = container.add_stream("libx264", rate=Fraction(fps).limit_denominator(1000))
        stream.width, stream.height = width, height
        stream.pix_fmt = "yuv420p"
        stream.options = {"crf": "18"}
        for frame in frames:
            img = frame.image.convert("RGB").resize((width, height), Image.LANCZOS)
            if overlay:
                _draw_overlay(img, frame.timestamp_ns, t0_ns)
            for packet in stream.encode(av.VideoFrame.from_image(img)):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return fps


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _window_ns(t0_ns: int, start_s: float | None,
               end_s: float | None) -> tuple[int | None, int | None]:
    """Converte secondi relativi al primo fotogramma in timestamp assoluti [start, end)."""
    lo = t0_ns + int(start_s * 1e9) if start_s is not None else None
    hi = t0_ns + int(end_s * 1e9) if end_s is not None else None
    return lo, hi


def _draw_overlay(img: Image.Image, timestamp_ns: int, t0_ns: int) -> None:
    """Scrive il tempo relativo in alto a sinistra; in rosso durante la caduta libera."""
    falling = FREE_FALL_NS[0] <= timestamp_ns <= FREE_FALL_NS[1]
    text = f"t = {(timestamp_ns - t0_ns) / 1e9:6.3f} s" + ("   FREE FALL" if falling else "")
    size = max(12, img.height // 20)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, size * 14, size + 10), fill=(0, 0, 0))
    draw.text((6, 4), text, fill=(255, 60, 60) if falling else (255, 255, 255),
              font_size=size)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", choices=("mosaico", "mcap"), default="mosaico")
    p.add_argument("--out", type=Path, default=HERE / "camera_front.mp4")
    p.add_argument("--scale", type=int, default=3, help="ingrandimento (320x240 -> 960x720)")
    p.add_argument("--start", type=float, default=None, help="secondi dal primo fotogramma")
    p.add_argument("--end", type=float, default=None, help="secondi dal primo fotogramma")
    p.add_argument("--no-overlay", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    read = frames_from_mosaico if args.source == "mosaico" else frames_from_mcap
    frames, t0 = read(args.start, args.end)
    fps = write_mp4(frames, args.out, t0, args.scale, not args.no_overlay)
    print(f"{len(frames)} fotogrammi da {args.source}, {fps:.2f} fps -> {args.out}")


if __name__ == "__main__":
    main()
