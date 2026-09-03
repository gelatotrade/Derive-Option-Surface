"""Animations: underlying chart + option orderbook + 3D implied-vol surface -> GIF / MP4.

Every frame is one timestamp and shows three linked views of the same data:

* **top-left**   — the underlying (Derive index) with a cursor at the frame time;
* **bottom-left** — the option orderbook of the front expiry as a *ladder*: call
  and put mids per strike with their bid/ask band and the forward as a
  vertical line — this is what actually moves when the underlying moves;
* **right**      — the 3D surface *(moneyness, tenor, implied vol)* built from
  the mids of *every* live option at that timestamp.

Rendering is plain matplotlib on the Agg backend; frames are composed into a
GIF (README-embeddable) and, when ffmpeg is available, an MP4.
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

from .surface import Surface  # noqa: E402

log = logging.getLogger(__name__)

# Palette: light chart surface, text tokens for all text, categorical slots for
# calls (blue) / puts (orange), one-hue sequential ramp for magnitude (IV) and a
# blue<->red diverging ramp with a neutral midpoint for signed greeks.
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
CALL, PUT, SPOT = "#2a78d6", "#eb6834", "#4a3aa7"
SEQ_BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
CMAP_SEQ = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
CMAP_DIV = LinearSegmentedColormap.from_list("div_blue_red", ["#0d366b", "#2a78d6", "#f0efec", "#e34948", "#7a1f1f"])
SIGNED_GREEKS = {"vanna", "charm", "theta", "speed", "zomma", "color", "ultima", "rho", "volga"}
GREEK_LABEL = {
    "iv": "Implied Vol (%)", "delta": "Delta", "gamma": "Gamma", "vega": "Vega", "theta": "Theta", "vanna": "Vanna",
    "volga": "Volga", "charm": "Charm", "speed": "Speed", "zomma": "Zomma", "color": "Color", "ultima": "Ultima",
}
DAY_TICKS = np.array([1, 2, 3, 5, 7, 14, 30, 60, 90, 180, 365])


# --------------------------------------------------------------------- frames
@dataclass
class Frame:
    ts_ms: int
    surface: Surface
    ladder: pd.DataFrame | None  # strike, call_bid, call_ask, put_bid, put_ask (live / shock mode)
    ladder_expiry: int
    forward: float
    fills: pd.DataFrame | None = None  # strike, iv, weight (tape mode: the fills behind the front smile)
    caption: str | None = None

    @property
    def when(self) -> dt.datetime:
        return dt.datetime.fromtimestamp(self.ts_ms / 1000, dt.timezone.utc)


def pick_ladder_expiry(df: pd.DataFrame, ts_ms: int, min_days: float = 2.5, max_days: float = 12.0, band: float = 0.15) -> int:
    """The expiry between 2.5 and 12 days out (the front weekly) with the most two-sided quotes near the money."""
    d = df.copy()
    d["days"] = (d["expiry"] - ts_ms / 1000) / 86400
    d["near"] = (d["strike"] / d["forward"].fillna(d["index"]) - 1).abs() <= band
    d["two"] = d["bid"].gt(0) & d["ask"].gt(0)
    cand = d[d["days"].between(min_days, max_days)]
    if cand.empty:
        cand = d[d["days"] > min_days]
    score = cand[cand["near"] & cand["two"]].groupby("expiry").size()
    return int(score.idxmax()) if len(score) else int(cand["expiry"].min())


def ladder_from_snapshot(df: pd.DataFrame, expiry: int, band: float = 0.15) -> tuple[pd.DataFrame, float]:
    g = df[df["expiry"] == expiry]
    F = float(g["forward"].median()) if g["forward"].notna().any() else float(g["index"].median())
    piv = g.pivot_table(index="strike", columns="option_type", values=["bid", "ask"])
    lad = pd.DataFrame(index=piv.index)
    for side, col in (("call", "C"), ("put", "P")):
        for lvl in ("bid", "ask"):
            lad[f"{side}_{lvl}"] = piv[(lvl, col)] if (lvl, col) in piv.columns else np.nan
    lad = lad[np.abs(lad.index.values / F - 1) <= band].reset_index()
    for side in ("call", "put"):
        b, a = lad[f"{side}_bid"], lad[f"{side}_ask"]
        lad[f"{side}_mid"] = np.where(b.gt(0) & a.gt(0), 0.5 * (b + a), np.nan)
    return lad, F


def frame_from_snapshot(df: pd.DataFrame, currency: str, ts_ms: int, ladder_expiry: int | None = None) -> Frame:
    surface = Surface.from_snapshot(df, currency, ts_ms)
    expiry = ladder_expiry or pick_ladder_expiry(df, ts_ms)
    ladder, F = ladder_from_snapshot(df, expiry)
    return Frame(ts_ms, surface, ladder, expiry, F)


# ------------------------------------------------------------------- renderer
class Renderer:
    """Draws one frame; keeps axis limits fixed across frames so motion is real motion."""

    def __init__(
        self,
        currency: str,
        *,
        axis: str = "delta",
        color_by: str = "iv",
        width: int = 960,
        height: int = 540,
        dpi: int = 100,
        zlim: tuple[float, float] | None = None,
        clim: tuple[float, float] | None = None,
        elev: float = 24,
        azim: float = -128,
        title: str | None = None,
    ):
        self.currency, self.axis, self.color_by = currency, axis, color_by
        self.figsize, self.dpi = (width / dpi, height / dpi), dpi
        self.zlim, self.clim, self.elev, self.azim = zlim, clim, elev, azim
        self.title = title or f"{currency} · Derive Options · Orderbook-Mid Surface"

    # --- helpers -----------------------------------------------------------
    x_grid: np.ndarray | None = None  # explicit axis grid (required for axis="strike")
    time_axis: bool = True  # False for what-if movies whose x is a scenario step, not a clock

    mask_wings: bool = False  # strike/logm axes: hide nodes the orderbook does not quote

    def surface_arrays(self, surface: Surface):
        x, tenors, iv = surface.grid(self.axis, self.x_grid, mask_wings=self.mask_wings)
        if self.color_by == "iv":
            C = iv * 100
        else:
            C = surface.greeks_grid(self.axis, self.x_grid)[self.color_by]
            C = np.where(np.isnan(iv), np.nan, C)
        return x, tenors, iv * 100, C

    def fit_limits(self, frames: list[Frame], pad: float = 0.06) -> None:
        """Set z/colour limits from the whole animation (2nd–98th percentile)."""
        zs, cs = [], []
        for f in frames:
            _, _, z, c = self.surface_arrays(f.surface)
            zs.append(z.ravel())
            cs.append(c.ravel())
        z, c = np.concatenate(zs), np.concatenate(cs)
        lo, hi = np.nanpercentile(z, [1, 99])
        self.zlim = (lo - pad * (hi - lo), hi + pad * (hi - lo))
        if self.color_by in SIGNED_GREEKS:
            m = np.nanpercentile(np.abs(c), 98)
            self.clim = (-m, m)
        else:
            lo, hi = np.nanpercentile(c, [1, 99])
            self.clim = (lo, hi)

    def _style(self, ax) -> None:
        ax.set_facecolor(SURFACE)
        for s in ax.spines.values():
            s.set_color(AXIS)
        ax.tick_params(colors=INK2, labelsize=8)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)

    # --- panels ------------------------------------------------------------
    def draw_spot(self, ax, spot_t: np.ndarray, spot_p: np.ndarray, frame: Frame, xlim=None, ylim=None) -> None:
        self._style(ax)
        ax.plot(spot_t, spot_p, color=SPOT, linewidth=1.6, solid_capstyle="round")
        i = int(np.searchsorted(spot_t, frame.ts_ms / 1000, side="right")) - 1
        i = max(0, min(i, len(spot_t) - 1))
        ax.plot(spot_t[i], spot_p[i], "o", ms=7, color=SPOT, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.axvline(spot_t[i], color=AXIS, linewidth=0.8)
        chg = spot_p[i] / spot_p[0] - 1
        ax.set_title(f"{spot_p[i]:,.2f}  ({chg:+.2%})", fontsize=9, color=INK, loc="right")
        if xlim:
            ax.set_xlim(*xlim)
        if ylim:
            ax.set_ylim(*ylim)
        if self.time_axis:
            ticks = ax.get_xticks()
            ax.set_xticks(ticks)
            span = (spot_t[-1] - spot_t[0]) if len(spot_t) > 1 else 0
            fmt = "%H:%M" if span < 3 * 86400 else "%d.%m"
            ax.set_xticklabels([dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime(fmt) for t in ticks])
            ax.set_title("Underlying · Derive Index (UTC)", fontsize=9, color=INK2, loc="left")
        else:
            ax.set_xlabel("Szenario-Schritt", fontsize=8, color=INK2)
            ax.set_title("Underlying · Szenario-Pfad", fontsize=9, color=INK2, loc="left")

    def draw_ladder(self, ax, frame: Frame, ylim=None) -> None:
        self._style(ax)
        lad = frame.ladder
        days = (frame.ladder_expiry - frame.ts_ms / 1000) / 86400
        for side, color, label in (("call", CALL, "Call"), ("put", PUT, "Put")):
            ok = lad[f"{side}_mid"].notna()
            ax.fill_between(lad["strike"][ok], lad[f"{side}_bid"][ok], lad[f"{side}_ask"][ok], color=color, alpha=0.18, linewidth=0)
            ax.plot(lad["strike"][ok], lad[f"{side}_mid"][ok], "-o", color=color, ms=4.5, linewidth=1.6, label=f"{label} Mid (Band = Bid/Ask)")
        ax.axvline(frame.forward, color=INK2, linewidth=1.0)
        ax.text(frame.forward, 0.04, f" Fwd {frame.forward:,.0f}", transform=ax.get_xaxis_transform(), fontsize=8, color=INK2, va="bottom")
        ax.set_title(f"Option-Orderbook · Verfall in {days:.1f}d · Mid je Strike (USDC)", fontsize=9, color=INK2, loc="left")
        ax.set_xlabel("Strike", fontsize=8, color=INK2)
        ax.legend(loc="upper center", fontsize=7.5, frameon=False, ncol=2)
        if ylim:
            ax.set_ylim(*ylim)

    def draw_smile(self, ax, frame: Frame, ylim=None) -> None:
        """Tape mode: the fills behind the front smile and the SVI curve through them."""
        self._style(ax)
        sm = next((s for s in frame.surface.smiles if s.T * 365 >= 2), frame.surface.smiles[0])
        days = sm.T * 365
        f = frame.fills[frame.fills["expiry"] == sm.expiry] if frame.fills is not None else None
        if f is not None and len(f):
            size = 12 + 40 * (f["weight"] / f["weight"].max())
            ax.scatter(f["strike"] / frame.surface.spot * 100, f["iv"] * 100, s=size, color=CALL, alpha=0.55, edgecolor=SURFACE, linewidth=0.8, label="Fills (24h, Größe = Gewicht)")
        m = np.linspace(sm.k.min() - 0.02, sm.k.max() + 0.02, 80)
        ax.plot(np.exp(m) * sm.F / frame.surface.spot * 100, sm(m) * 100, color=PUT, linewidth=1.8, label="SVI-Fit")
        ax.axvline(100.0, color=INK2, linewidth=1.0)
        ax.set_title(f"Front-Smile · Verfall in {days:.0f}d · IV je Strike aus Fills", fontsize=9, color=INK2, loc="left")
        ax.set_xlabel("Strike / Spot (%)", fontsize=8, color=INK2)
        ax.set_ylabel("IV (%)", fontsize=8, color=INK2)
        ax.legend(loc="upper center", fontsize=7.5, frameon=False, ncol=2)
        if ylim:
            ax.set_ylim(*ylim)

    def draw_surface(self, ax, frame: Frame) -> None:
        x, tenors, Z, C = self.surface_arrays(frame.surface)
        days = tenors * 365
        X, Y = np.meshgrid(x, np.log10(days))
        if self.color_by in SIGNED_GREEKS:
            cmap, norm = CMAP_DIV, TwoSlopeNorm(vmin=self.clim[0], vcenter=0.0, vmax=self.clim[1]) if self.clim else None
        else:
            cmap, norm = CMAP_SEQ, Normalize(*self.clim) if self.clim else None
        colors = cmap(norm(np.nan_to_num(C, nan=0.0))) if norm is not None else cmap(Normalize()(np.nan_to_num(C, nan=0.0)))
        # matplotlib drops every face that touches a NaN vertex: the unquoted region simply is not drawn
        ax.plot_surface(X, Y, Z, facecolors=colors, rstride=1, cstride=1, linewidth=0.25, edgecolor=(0, 0, 0, 0.12), shade=False, antialiased=True)
        ax.view_init(elev=self.elev, azim=self.azim)
        ax.set_facecolor(SURFACE)
        for axis_ in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis_.set_pane_color((1, 1, 1, 0))
            axis_._axinfo["grid"]["color"] = GRID
        ax.tick_params(colors=INK2, labelsize=7.5, pad=0)
        if self.axis == "delta":
            ax.set_xlabel("Call-Delta (Put = Δ−1)", fontsize=8, color=INK2, labelpad=4)
            ax.set_xticks([0.1, 0.25, 0.5, 0.75, 0.9])
        elif self.axis == "strike":
            ax.set_xlabel("Strike", fontsize=8, color=INK2, labelpad=4)
        else:
            ax.set_xlabel("log(K/F)", fontsize=8, color=INK2, labelpad=4)
        ticks = DAY_TICKS[(DAY_TICKS >= days.min() * 0.95) & (DAY_TICKS <= days.max() * 1.05)]
        ax.set_yticks(np.log10(ticks))
        ax.set_yticklabels([f"{t:d}d" for t in ticks])
        ax.set_ylabel("Tage bis Verfall", fontsize=8, color=INK2, labelpad=4)
        ax.set_zlabel("Implied Vol (%)", fontsize=8, color=INK2, labelpad=2)
        if self.zlim:
            ax.set_zlim(*self.zlim)
        ax.set_xlim(x.min(), x.max())
        ax.set_ylim(np.log10(days.min()), np.log10(days.max()))
        atm = frame.surface.atm_term_structure() * 100
        T = frame.surface.tenors * 365
        picks = sorted({0, len(T) // 2, len(T) - 1})
        info = "ATM IV  " + "  ·  ".join(f"{T[i]:.0f}d {atm[i]:.1f}%" for i in picks)
        ax.text2D(0.02, 0.97, info, transform=ax.transAxes, fontsize=8.5, color=INK, va="top")
        if self.color_by != "iv":
            ax.text2D(0.02, 0.92, f"Farbe: {GREEK_LABEL.get(self.color_by, self.color_by)}", transform=ax.transAxes, fontsize=8, color=INK2, va="top")

    # --- frame -------------------------------------------------------------
    def render(self, frame: Frame, spot_t: np.ndarray, spot_p: np.ndarray, spot_xlim=None, spot_ylim=None, ladder_ylim=None) -> np.ndarray:
        fig = plt.figure(figsize=self.figsize, dpi=self.dpi, facecolor=SURFACE)
        gs = GridSpec(2, 2, figure=fig, width_ratios=[1.0, 1.35], height_ratios=[1, 1.15], left=0.06, right=0.98, top=0.90, bottom=0.13, wspace=0.10, hspace=0.45)
        ax_spot = fig.add_subplot(gs[0, 0])
        ax_book = fig.add_subplot(gs[1, 0])
        ax_surf = fig.add_subplot(gs[:, 1], projection="3d")
        self.draw_spot(ax_spot, spot_t, spot_p, frame, spot_xlim, spot_ylim)
        if frame.ladder is not None:
            self.draw_ladder(ax_book, frame, ladder_ylim)
        else:
            self.draw_smile(ax_book, frame, ladder_ylim)
        self.draw_surface(ax_surf, frame)
        if frame.caption:
            fig.text(0.06, 0.018, frame.caption, fontsize=8.5, color=INK2)
        fig.text(0.06, 0.955, self.title, fontsize=12, color=INK, weight="bold")
        fig.text(0.98, 0.955, frame.when.strftime("%Y-%m-%d %H:%M:%S UTC"), fontsize=9, color=INK2, ha="right")
        fig.canvas.draw()
        rgb = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        plt.close(fig)
        return rgb


# --------------------------------------------------------------------- output
def write_gif(frames: list[np.ndarray], path: Path, fps: float = 8, hold_last: int = 6) -> Path:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    imgs = [Image.fromarray(f).quantize(colors=192, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    imgs += [imgs[-1]] * hold_last
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=int(1000 / fps), loop=0, optimize=True)
    log.info("wrote %s (%d frames, %.1f MB)", path, len(imgs), path.stat().st_size / 1e6)
    return path


def write_mp4(frames: list[np.ndarray], path: Path, fps: float = 8) -> Path | None:
    try:
        import imageio

        path.parent.mkdir(parents=True, exist_ok=True)
        with imageio.get_writer(path, fps=fps, codec="libx264", macro_block_size=1, pixelformat="yuv420p", ffmpeg_params=["-crf", "23"]) as w:
            for f in frames:
                w.append_data(f)
        log.info("wrote %s (%.1f MB)", path, path.stat().st_size / 1e6)
        return path
    except Exception as exc:  # ffmpeg missing -> GIF only
        log.warning("mp4 skipped: %s", exc)
        return None


# ---------------------------------------------------------------- live movie
def load_live_tickers(data_dir: Path, currency: str) -> pd.DataFrame:
    merged = data_dir / "live" / f"{currency}_tickers.parquet"
    if merged.exists():
        return pd.read_parquet(merged)
    parts = sorted((data_dir / "raw" / "live").glob(f"tickers_{currency}_part*.parquet"))
    return pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True)


def animate_live(
    data_dir: Path, currency: str, out_dir: Path, *, every: int = 3, max_frames: int = 150, axis: str = "delta",
    color_by: str = "iv", fps: float = 8, width: int = 960, height: int = 540, suffix: str = ""
) -> Path:
    tk = load_live_tickers(data_dir, currency)
    cycles = np.sort(tk["cycle_ts"].unique())
    spot_t = cycles / 1000
    spot_p = tk.groupby("cycle_ts")["index"].median().reindex(cycles).ffill().values
    use = cycles[::every]
    if len(use) > max_frames:
        use = use[np.linspace(0, len(use) - 1, max_frames).round().astype(int)]
    frames: list[Frame] = []
    ladder_expiry = None
    for ts in use:
        snap = tk[tk["cycle_ts"] == ts]
        f = frame_from_snapshot(snap, currency, int(ts), ladder_expiry)
        ladder_expiry = ladder_expiry or f.ladder_expiry  # keep the same expiry across the movie
        frames.append(f)
    r = Renderer(currency, axis=axis, color_by=color_by, width=width, height=height)
    r.fit_limits(frames)
    lo, hi = np.nanmin([f.ladder[["call_bid", "put_bid"]].min().min() for f in frames]), np.nanmax([f.ladder[["call_ask", "put_ask"]].max().max() for f in frames])
    ladder_ylim = (0, hi * 1.08)
    pad = (spot_p.max() - spot_p.min()) * 0.15 or spot_p[0] * 0.002
    rgb = [r.render(f, spot_t, spot_p, (spot_t[0], spot_t[-1]), (spot_p.min() - pad, spot_p.max() + pad), ladder_ylim) for f in frames]
    tag = f"{currency}_live{suffix}"
    write_mp4(rgb, out_dir / f"{tag}.mp4", fps)
    return write_gif(rgb, out_dir / f"{tag}.gif", fps)


def render_still(data_dir: Path, currency: str, out_path: Path, *, axis: str = "delta", color_by: str = "iv", width: int = 1280, height: int = 720) -> Path:
    """One high-resolution frame of the latest recorded snapshot (README hero image)."""
    from PIL import Image

    tk = load_live_tickers(data_dir, currency)
    cycles = np.sort(tk["cycle_ts"].unique())
    spot_t = cycles / 1000
    spot_p = tk.groupby("cycle_ts")["index"].median().reindex(cycles).ffill().values
    last = int(cycles[-1])
    f = frame_from_snapshot(tk[tk["cycle_ts"] == last], currency, last)
    r = Renderer(currency, axis=axis, color_by=color_by, width=width, height=height)
    r.fit_limits([f])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(r.render(f, spot_t, spot_p)).save(out_path, optimize=True)
    log.info("wrote %s", out_path)
    return out_path


# ---------------------------------------------------------------- tape movie
def animate_tape(
    data_dir: Path, currency: str, out_dir: Path, *, days: int = 60, step_h: int = 12, axis: str = "delta", color_by: str = "iv",
    fps: float = 8, width: int = 960, height: int = 540, suffix: str = ""
) -> Path:
    """Surfaces reconstructed from the trade tape, one frame every ``step_h`` hours over the last ``days`` days."""
    from .tape import load_spot, load_trades, surface_at, trade_ivs

    fills = trade_ivs(load_trades(data_dir, currency))
    spot = load_spot(data_dir, currency, "1h")
    t_end = int(spot.index[-1])
    times = np.arange(t_end - days * 86400, t_end + 1, step_h * 3600) * 1000
    frames: list[Frame] = []
    for ts in times:
        s = surface_at(fills, spot, int(ts), currency)
        if s is None or len(s.smiles) < 2:
            continue
        lo = ts - 86400 * 1000
        w = fills[(fills["timestamp"] > lo) & (fills["timestamp"] <= ts) & fills["otm"]]
        age = (ts - w["timestamp"].values) / 1000.0
        f = pd.DataFrame({"expiry": w["expiry"].values, "strike": w["strike"].values, "iv": w["iv"].values,
                          "weight": w["trade_amount"].values * np.exp(-age * np.log(2) / (6 * 3600))})
        frames.append(Frame(int(ts), s, None, s.smiles[0].expiry, s.spot, fills=f,
                            caption="Quelle: Derive Trade-Tape (jeder Fill = gekreuzte Quote), SVI-Fit über 24h-Fenster, zeit- und größengewichtet"))
    r = Renderer(currency, axis=axis, color_by=color_by, width=width, height=height, title=f"{currency} · Derive Options · Surface aus dem Trade-Tape")
    r.fit_limits(frames)
    sub = spot[(spot.index >= times[0] / 1000 - 3600) & (spot.index <= times[-1] / 1000 + 3600)]
    spot_t, spot_p = sub.index.values.astype(float), sub.values
    pad = (spot_p.max() - spot_p.min()) * 0.1
    ivs = np.concatenate([f.fills["iv"].values for f in frames if len(f.fills)]) * 100
    smile_ylim = (max(0, np.nanpercentile(ivs, 1) * 0.8), np.nanpercentile(ivs, 99) * 1.15)
    rgb = [r.render(f, spot_t, spot_p, (spot_t[0], spot_t[-1]), (spot_p.min() - pad, spot_p.max() + pad), smile_ylim) for f in frames]
    tag = f"{currency}_tape{suffix}"
    write_mp4(rgb, out_dir / f"{tag}.mp4", fps)
    return write_gif(rgb, out_dir / f"{tag}.gif", fps)


if __name__ == "__main__":  # python -m derive_surface.animate live|tape BTC [color_by]
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    kind, ccy = sys.argv[1], sys.argv[2]
    color_by = sys.argv[3] if len(sys.argv) > 3 else "iv"
    suffix = "" if color_by == "iv" else f"_{color_by}"
    if kind == "live":
        animate_live(Path("data"), ccy, Path("docs/media"), color_by=color_by, suffix=suffix)
    elif kind == "tape":
        animate_tape(Path("data"), ccy, Path("docs/media"), color_by=color_by, suffix=suffix)
