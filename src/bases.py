"""Mutasyon testinin başlangıç noktası olan dört geçerli fatura.

A: TEMELFATURA/SATIS, iki satır (%20 ve %10 KDV), TRY
T: TEMELFATURA/TEVKIFAT, yemek servisi, 604 kodlu 5/10 tevkifat
I: TEMELFATURA/ISTISNA, KDV %0, 350 muafiyet kodu
D: TICARIFATURA/SATIS, USD, döviz kuru bilgisiyle

A ve tek satırlı iskelet efatura-kontrol'ün `ornek-fatura` üreticisiyle üretilir (bases/*.json);
T, I, D bu iskeletten türetilir. Her taban sıfır hata ile doğrulanmadan mutasyona girmez.

Kullanım:  python -m src.bases
"""
import subprocess
from pathlib import Path

from src.xmlutil import CBC, NS, bayt, e, oku, para, sonrasina, x, xs, yaz

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "bases"


def uret(json_ad, xml_ad):
    subprocess.run(["efatura-kontrol", "ornek-fatura", str(B / json_ad), "-o", str(B / xml_ad)],
                   check=True, capture_output=True)


def tevkifat_toplami(kod, oran, matrah, tutar):
    w = e("cac:WithholdingTaxTotal")
    w.append(e("cbc:TaxAmount", para(tutar), currencyID="TRY"))
    st = e("cac:TaxSubtotal")
    st.append(e("cbc:TaxableAmount", para(matrah), currencyID="TRY"))
    st.append(e("cbc:TaxAmount", para(tutar), currencyID="TRY"))
    st.append(e("cbc:Percent", oran))
    tc = e("cac:TaxCategory")
    ts = e("cac:TaxScheme")
    ts.append(e("cbc:Name", "KDV TEVKİFAT"))
    ts.append(e("cbc:TaxTypeCode", kod))
    tc.append(ts)
    st.append(tc)
    w.append(st)
    return w


def taban_t():
    t = oku(B / "_tek_satir.xml")
    k = t.getroot()
    yaz(k, "cbc:InvoiceTypeCode", "TEVKIFAT")
    yaz(k, "cbc:ID", "ABC2026000000125")
    yaz(k, "cbc:UUID", "3B2F1A0E-5C4D-4E3F-8A2B-1C0D9E8F7A6B")
    kdv, tev = 2000, 1000  # 10.000 TL matrah, %20 KDV, 5/10 tevkifat
    sonrasina(x(k, "cac:InvoiceLine/cac:TaxTotal"), tevkifat_toplami("604", 50, kdv, tev))
    sonrasina(x(k, "cac:TaxTotal"), tevkifat_toplami("604", 50, kdv, tev))
    yaz(k, "cac:LegalMonetaryTotal/cbc:PayableAmount", para(10000 + kdv - tev))
    return t


def taban_i():
    t = oku(B / "_tek_satir.xml")
    k = t.getroot()
    yaz(k, "cbc:InvoiceTypeCode", "ISTISNA")
    yaz(k, "cbc:ID", "ABC2026000000126")
    yaz(k, "cbc:UUID", "9D8C7B6A-5F4E-4D3C-8B2A-1F0E9D8C7B6A")
    yaz(k, "cac:InvoiceLine/cac:Item/cbc:Name", "Eğitim hizmeti")
    for yol in ("cac:TaxTotal", "cac:InvoiceLine/cac:TaxTotal"):
        yaz(k, f"{yol}/cbc:TaxAmount", "0.00")
        yaz(k, f"{yol}/cac:TaxSubtotal/cbc:TaxAmount", "0.00")
        yaz(k, f"{yol}/cac:TaxSubtotal/cbc:Percent", "0")
        tc = x(k, f"{yol}/cac:TaxSubtotal/cac:TaxCategory")
        tc.insert(0, e("cbc:TaxExemptionReason", "KDV Kanunu 17/2-b kapsamında istisna"))
        tc.insert(0, e("cbc:TaxExemptionReasonCode", "350"))
    yaz(k, "cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount", "10000.00")
    yaz(k, "cac:LegalMonetaryTotal/cbc:PayableAmount", "10000.00")
    return t


def taban_d():
    t = oku(B / "_tek_satir.xml")
    k = t.getroot()
    yaz(k, "cbc:ProfileID", "TICARIFATURA")
    yaz(k, "cbc:ID", "ABC2026000000127")
    yaz(k, "cbc:UUID", "1E2D3C4B-5A69-4788-9FA0-B1C2D3E4F506")
    yaz(k, "cbc:DocumentCurrencyCode", "USD")
    for d in xs(k, "//*[@currencyID]"):
        d.set("currencyID", "USD")
    # 10.000 TRY iskeleti 1.000 USD'ye ölçekle
    for d in xs(k, "//*[@currencyID]"):
        d.text = para(float(d.text) / 10)
    kur = e("cac:PricingExchangeRate")
    kur.append(e("cbc:SourceCurrencyCode", "USD"))
    kur.append(e("cbc:TargetCurrencyCode", "TRY"))
    kur.append(e("cbc:CalculationRate", "41.2500"))
    sonrasina(x(k, "cac:AccountingCustomerParty"), kur)
    return t


def dogrula(yol) -> str:
    r = subprocess.run(["efatura-kontrol", "dogrula", str(yol)], capture_output=True, text=True)
    return r.stdout.strip().splitlines()[0] if r.returncode == 0 else r.stdout


def main():
    uret("A_temel_satis.json", "A_temel_satis.xml")
    uret("_tek_satir.json", "_tek_satir.xml")
    for ad, f in (("T_tevkifat.xml", taban_t), ("I_istisna.xml", taban_i), ("D_doviz.xml", taban_d)):
        (B / ad).write_bytes(bayt(f()))
    (B / "_tek_satir.xml").unlink()
    for ad in ("A_temel_satis.xml", "T_tevkifat.xml", "I_istisna.xml", "D_doviz.xml"):
        print(dogrula(B / ad))


if __name__ == "__main__":
    main()
