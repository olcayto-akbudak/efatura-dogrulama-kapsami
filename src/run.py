"""Her mutasyonu uygular, doğrular ve hangi katmanın yakaladığını kaydeder.

Katmanlar:
  xsd       OASIS UBL 2.1 şeması (GİB paketinin parçası, resmî)
  sematron  GİB UBL-TR şematronu (resmî)
  hesap     efatura-kontrol'ün aritmetik katmanı (resmî değil; UBL-TR kılavuzundaki tanımlardan)

Kullanım:  python -m src.run
"""
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from efatura_kontrol.kontrol import kontrol_et

from src.mutations import KONTROL_TURU, M
from src.xmlutil import bayt, kopya, oku

ROOT = Path(__file__).resolve().parents[1]
BASES = {"A": "A_temel_satis.xml", "T": "T_tevkifat.xml", "I": "I_istisna.xml", "D": "D_doviz.xml"}
OUT = ROOT / "reports"
SAMPLES = ROOT / "mutants"


def bulgular(xml: bytes, ad: str):
    r = kontrol_et(xml, ad=ad)
    return [b for b in r.bulgular if b.seviye in ("hata", "uyari") and not b.kod.endswith("-ozet")]


def katman(bs):
    kaynaklar = {b.kaynak for b in bs if b.seviye == "hata"}
    if "xml" in kaynaklar or "xsd" in kaynaklar:
        return "XSD"
    if "sematron" in kaynaklar:
        return "GİB şematronu"
    if {b.kaynak for b in bs} & {"hesap"}:
        return "Yalnız ek aritmetik"
    return "Hiçbiri"


def main():
    OUT.mkdir(exist_ok=True)
    SAMPLES.mkdir(exist_ok=True)
    tabanlar = {k: oku(ROOT / "bases" / v) for k, v in BASES.items()}
    for k, t in tabanlar.items():
        assert not bulgular(bayt(t), k), f"Taban {k} geçerli değil"

    satirlar = []
    for mu in M:
        agac = kopya(tabanlar[mu.taban])
        mu.uygula(agac.getroot())
        xml = bayt(agac)
        (SAMPLES / f"{mu.id}.xml").write_bytes(xml)
        bs = bulgular(xml, mu.id)
        resmi = [b for b in bs if b.kaynak in ("xml", "xsd", "sematron") and b.seviye == "hata"]
        satirlar.append({
            "id": mu.id, "taban": mu.taban, "kategori": mu.kategori, "kontrol_turu": KONTROL_TURU[mu.id], "hata": mu.hata, "etki": mu.etki,
            "katman": katman(bs),
            "resmi_ret": bool(resmi),
            "resmi_kurallar": "; ".join(sorted({b.kod for b in resmi})),
            "gib_mesaji": (resmi[0].gib_mesaj or resmi[0].mesaj)[:160] if resmi else "",
            "ek_katman_bulgulari": "; ".join(sorted({b.kod for b in bs if b.kaynak == "hesap"})),
        })
    tum = pd.DataFrame(satirlar)
    tum.to_csv(OUT / "mutasyon_sonuclari.csv", index=False, encoding="utf-8")
    kontrol = tum[tum.kategori == "Kontrol vakası"]
    df = tum[tum.kategori != "Kontrol vakası"]

    ozet = {
        "mutasyon": len(df),
        "kontrol_vakalari": kontrol[["id", "katman"]].to_dict("records"),
        "katman_dagilimi": df.katman.value_counts().to_dict(),
        "resmi_yakalama_pct": round(100 * df.resmi_ret.mean(), 1),
        "resmi_kacirilan": int((~df.resmi_ret).sum()),
        "kacirilan_ek_katman_yakaladi": int(((~df.resmi_ret) & (df.katman == "Yalnız ek aritmetik")).sum()),
        "kacirilan_hicbiri": int((df.katman == "Hiçbiri").sum()),
        "kategori": (df.groupby("kategori").agg(n=("id", "size"), resmi=("resmi_ret", "sum"))
                     .assign(pct=lambda d: (100 * d.resmi / d.n).round(0)).reset_index()
                     .to_dict("records")),
        "kontrol_turu": (df.groupby("kontrol_turu").agg(
            n=("id", "size"), resmi=("resmi_ret", "sum"),
            sadece_ek=("katman", lambda s: int((s == "Yalnız ek aritmetik").sum())),
            hicbiri=("katman", lambda s: int((s == "Hiçbiri").sum())))
            .assign(pct=lambda d: (100 * d.resmi / d.n).round(0)).reset_index().to_dict("records")),
        "hicbiri_listesi": df.loc[df.katman == "Hiçbiri", "id"].tolist(),
        "sadece_ek_listesi": df.loc[df.katman == "Yalnız ek aritmetik", "id"].tolist(),
        "motor": "efatura-kontrol 0.1.0 @ 87c0ca0 (GİB şematron 20260701, UBL-TR 1.2.1, e-Fatura Paketi 29)",
    }
    (OUT / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_colwidth", 70)
    print(tum[["id", "katman", "resmi_kurallar", "ek_katman_bulgulari"]].to_string(index=False))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kategori"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
