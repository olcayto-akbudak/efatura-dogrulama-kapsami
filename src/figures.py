"""README grafikleri.  Kullanım:  python -m src.figures"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "reports"

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
RESMI, EK, YOK = "#2a78d6", "#1baf7a", "#eb6834"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10.5, "text.color": INK,
    "axes.edgecolor": GRID, "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
})


def kapsama():
    o = json.loads((REP / "ozet.json").read_text(encoding="utf-8"))
    rows = sorted(o["kontrol_turu"], key=lambda r: (r["resmi"] / r["n"], -r["n"]))
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    for i, r in enumerate(rows):
        sol = 0
        for deger, renk in ((r["resmi"], RESMI), (r["sadece_ek"], EK), (r["hicbiri"], YOK)):
            if deger:
                ax.barh(i, deger, left=sol, color=renk, height=0.6, edgecolor=SURFACE, linewidth=2)
                ax.text(sol + deger / 2, i, str(deger), ha="center", va="center",
                        color="white", fontsize=10, fontweight="bold")
                sol += deger
        ax.text(r["n"] + 0.4, i, f"resmî yakalama %{r['pct']:.0f}", va="center", fontsize=10, color=INK)
    ax.set_yticks(range(len(rows)), [f"{r['kontrol_turu']}  ({r['n']})" for r in rows])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(r["n"] for r in rows) + 6)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("Enjekte edilen hata sayısı")
    ax.set_title("Hatayı yakalamak için gereken kontrol türüne göre kim yakaladı",
                 loc="left", fontsize=13, fontweight="bold", pad=30)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (RESMI, EK, YOK)]
    ax.legend(handles, ["Resmî katman (XSD + GİB şematronu)", "Yalnız ek aritmetik katman", "Hiçbiri"],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, frameon=False, fontsize=9.5,
              handlelength=1.2, borderaxespad=0.2)
    fig.tight_layout()
    fig.savefig(REP / "figures" / "01_kapsama.png", dpi=160)


if __name__ == "__main__":
    (REP / "figures").mkdir(parents=True, exist_ok=True)
    kapsama()
