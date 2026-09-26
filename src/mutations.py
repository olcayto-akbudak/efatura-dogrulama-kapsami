"""Gerçek hayatta sık görülen e-fatura hataları: her biri geçerli bir tabana tek bir hata enjekte eder.

Her mutasyon: kimlik, taban (A/T/I/D), kategori, hatanın tanımı, iş etkisi ve düzenleme fonksiyonu.
Fonksiyon, bulamadığı düğümde LookupError verir; hiçbir mutasyon sessizce boşa düşmez.
"""
from dataclasses import dataclass
from typing import Callable

from src.xmlutil import CBC, e, para, sonrasina, x, xs, yaz


@dataclass(frozen=True)
class Mutasyon:
    id: str
    taban: str
    kategori: str
    hata: str
    etki: str
    uygula: Callable


M: list[Mutasyon] = []


def m(id, taban, kategori, hata, etki):
    def kaydet(f):
        M.append(Mutasyon(id, taban, kategori, hata, etki, f))
        return f
    return kaydet


SAT = "cac:AccountingSupplierParty/cac:Party"
ALI = "cac:AccountingCustomerParty/cac:Party"
L1, L2 = "cac:InvoiceLine[1]", "cac:InvoiceLine[2]"
DIP = "cac:LegalMonetaryTotal"

# ---------------------------------------------------------------- Kimlik
@m("K01", "A", "Kimlik", "Satıcı VKN'si 9 hane", "Belge yanlış mükellefe bağlanır")
def _(k): yaz(k, f"{SAT}/cac:PartyIdentification/cbc:ID", "123456789")

@m("K02", "A", "Kimlik", "Satıcı VKN'si 10 hane ama kontrol hanesi yanlış", "Var olmayan bir VKN ile fatura")
def _(k): yaz(k, f"{SAT}/cac:PartyIdentification/cbc:ID", "1234567891")

@m("K03", "A", "Kimlik", "Alıcı VKN'si kontrol hanesi yanlış", "KDV indirimi yanlış mükellefe gider")
def _(k): yaz(k, f"{ALI}/cac:PartyIdentification/cbc:ID", "9876543210")

@m("K04", "A", "Kimlik", "Alıcı TCKN'li (gerçek kişi), TCKN kontrol hanesi yanlış", "Var olmayan kişi adına fatura")
def _(k):
    p = x(k, ALI)
    idn = x(p, "cac:PartyIdentification/cbc:ID")
    idn.set("schemeID", "TCKN")
    idn.text = "11111111111"
    p.remove(x(p, "cac:PartyName"))
    kisi = e("cac:Person")
    kisi.append(e("cbc:FirstName", "Ayşe"))
    kisi.append(e("cbc:FamilyName", "Demir"))
    x(p, "cac:PartyTaxScheme").addnext(kisi)

@m("K05", "A", "Kimlik", "VKN'li alıcıda unvan (PartyName) yok", "Alıcı kimliği eksik")
def _(k):
    p = x(k, ALI)
    p.remove(x(p, "cac:PartyName"))

@m("K06", "A", "Kimlik", "schemeID=VKN ama değer 11 haneli", "Kimlik türü karışıklığı")
def _(k): yaz(k, f"{ALI}/cac:PartyIdentification/cbc:ID", "11111111110")

@m("K07", "A", "Kimlik", "Satıcı ve alıcı VKN'si aynı", "Kendi kendine fatura; ana veri hatası")
def _(k): yaz(k, f"{ALI}/cac:PartyIdentification/cbc:ID", "1234567890")

# ---------------------------------------------------------------- Belge başlığı
@m("B01", "A", "Başlık", "Fatura numarası biçimi hatalı (küçük harf seri)", "Numaralandırma kuralı ihlali")
def _(k): yaz(k, "cbc:ID", "abc2026000000123")

@m("B02", "A", "Başlık", "Fatura numarasında yıl, düzenleme tarihiyle uyumsuz (2025)", "Seri/yıl karışıklığı")
def _(k): yaz(k, "cbc:ID", "ABC2025000000123")

@m("B03", "A", "Başlık", "UUID biçimi geçersiz", "Belge tekil tanımlanamaz")
def _(k): yaz(k, "cbc:UUID", "12345")

@m("B04", "A", "Başlık", "Düzenleme tarihi ileri bir tarih (2099-01-15)", "Dönem kayması, erken KDV beyanı")
def _(k): yaz(k, "cbc:IssueDate", "2099-01-15")

@m("B05", "A", "Başlık", "Düzenleme tarihi 2004 (e-fatura öncesi)", "Geçersiz dönem")
def _(k):
    yaz(k, "cbc:IssueDate", "2004-06-01")
    yaz(k, "cbc:ID", "ABC2004000000123")

@m("B06", "A", "Başlık", "Senaryo (ProfileID) kod listesinde yok", "Belge işlenemez")
def _(k): yaz(k, "cbc:ProfileID", "TEMEL")

@m("B07", "A", "Başlık", "Fatura tipi kod listesinde yok", "Belge işlenemez")
def _(k): yaz(k, "cbc:InvoiceTypeCode", "SATIŞ")

@m("B08", "A", "Başlık", "TICARIFATURA senaryosunda IADE tipi", "İade süreci yanlış senaryoda")
def _(k):
    yaz(k, "cbc:ProfileID", "TICARIFATURA")
    yaz(k, "cbc:InvoiceTypeCode", "IADE")

@m("B09", "A", "Başlık", "Satır sayısı alanı (LineCountNumeric) gerçek satır sayısından farklı", "Tutarsız başlık")
def _(k): yaz(k, "cbc:LineCountNumeric", "3")

@m("B10", "A", "Başlık", "Özelleştirme numarası eski (TR1.0)", "Yanlış kılavuz sürümü")
def _(k): yaz(k, "cbc:CustomizationID", "TR1.0")

@m("B11", "A", "Başlık", "İki satır aynı satır numarasına (ID=1) sahip", "Satır referansı belirsiz")
def _(k): yaz(k, f"{L2}/cbc:ID", "1")

# ---------------------------------------------------------------- Kod listeleri ve oranlar
@m("C01", "A", "Kod ve oran", "Birim kodu 'ADET' (UN/ECE yerine yerel kısaltma)", "Belge reddedilir")
def _(k): x(k, f"{L1}/cbc:InvoicedQuantity").set("unitCode", "ADET")

@m("C02", "A", "Kod ve oran", "Para birimi kodu 'TL'", "Belge reddedilir")
def _(k):
    yaz(k, "cbc:DocumentCurrencyCode", "TL")
    for d in xs(k, "//*[@currencyID]"):
        d.set("currencyID", "TL")

@m("C03", "A", "Kod ve oran", "Vergi tipi kodu listede yok (9999)", "Vergi türü tanınmaz")
def _(k):
    for d in xs(k, "//cac:TaxSubtotal[cbc:Percent='10']//cbc:TaxTypeCode"):
        d.text = "9999"

@m("C04", "A", "Kod ve oran", "KDV oranı %18 (Temmuz 2023 öncesi oran), tutarlar tutarlı", "Eksik KDV tahsili, vergi farkı")
def _(k):
    for yol in (f"{L1}/cac:TaxTotal", "cac:TaxTotal"):
        st = x(k, f"{yol}/cac:TaxSubtotal[cbc:Percent='20']")
        yaz(st, "cbc:Percent", "18")
        yaz(st, "cbc:TaxAmount", "2250.00")
    yaz(k, f"{L1}/cac:TaxTotal/cbc:TaxAmount", "2250.00")
    yaz(k, "cac:TaxTotal/cbc:TaxAmount", "2285.00")
    yaz(k, f"{DIP}/cbc:TaxInclusiveAmount", "15135.00")
    yaz(k, f"{DIP}/cbc:PayableAmount", "15135.00")

@m("C05", "A", "Kod ve oran", "KDV oranı %19 (mevzuatta olmayan oran), tutarlar tutarlı", "Hatalı vergi")
def _(k):
    for yol in (f"{L1}/cac:TaxTotal", "cac:TaxTotal"):
        st = x(k, f"{yol}/cac:TaxSubtotal[cbc:Percent='20']")
        yaz(st, "cbc:Percent", "19")
        yaz(st, "cbc:TaxAmount", "2375.00")
    yaz(k, f"{L1}/cac:TaxTotal/cbc:TaxAmount", "2375.00")
    yaz(k, "cac:TaxTotal/cbc:TaxAmount", "2410.00")
    yaz(k, f"{DIP}/cbc:TaxInclusiveAmount", "15260.00")
    yaz(k, f"{DIP}/cbc:PayableAmount", "15260.00")

@m("C06", "A", "Kod ve oran", "KDV %0 ama tip SATIS ve muafiyet kodu yok", "Gerekçesiz vergisiz satış")
def _(k):
    for yol in (f"{L2}/cac:TaxTotal", "cac:TaxTotal"):
        st = x(k, f"{yol}/cac:TaxSubtotal[cbc:Percent='10']")
        yaz(st, "cbc:Percent", "0")
        yaz(st, "cbc:TaxAmount", "0.00")
    yaz(k, f"{L2}/cac:TaxTotal/cbc:TaxAmount", "0.00")
    yaz(k, "cac:TaxTotal/cbc:TaxAmount", "2500.00")
    yaz(k, f"{DIP}/cbc:TaxInclusiveAmount", "15350.00")
    yaz(k, f"{DIP}/cbc:PayableAmount", "15350.00")

# ---------------------------------------------------------------- Aritmetik
@m("H01", "A", "Aritmetik", "Satır tutarı ≠ miktar × birim fiyat", "Yanlış tutar faturalanır")
def _(k): yaz(k, f"{L1}/cac:Price/cbc:PriceAmount", "1200")

@m("H02", "A", "Aritmetik", "Satır KDV tutarı ≠ matrah × oran", "KDV hatalı")
def _(k):
    yaz(k, f"{L1}/cac:TaxTotal/cbc:TaxAmount", "2400.00")
    yaz(k, f"{L1}/cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount", "2400.00")

@m("H03", "A", "Aritmetik", "Belge KDV toplamı ≠ alt toplamların toplamı", "Beyana yanlış KDV")
def _(k): yaz(k, "cac:TaxTotal/cbc:TaxAmount", "2600.00")

@m("H04", "A", "Aritmetik", "Ödenecek tutar yanlış", "Fazla/eksik tahsilat")
def _(k): yaz(k, f"{DIP}/cbc:PayableAmount", "15835.00")

@m("H05", "A", "Aritmetik", "Vergiler dahil tutar yanlış", "Tutarsız dip toplam")
def _(k): yaz(k, f"{DIP}/cbc:TaxInclusiveAmount", "15285.00")

@m("H06", "A", "Aritmetik", "Dip mal/hizmet toplamı ≠ satır tutarları toplamı", "Tutarsız dip toplam")
def _(k): yaz(k, f"{DIP}/cbc:LineExtensionAmount", "12500.00")

@m("H07", "A", "Aritmetik", "Tüm tutarlar tutarlı biçimde %10 fazla (birim fiyat girişi hatalı)", "İç tutarlı ama yanlış fatura")
def _(k):
    yaz(k, f"{L1}/cac:Price/cbc:PriceAmount", "1375")
    for yol, v in ((f"{L1}/cbc:LineExtensionAmount", 13750), (f"{L1}/cac:TaxTotal/cbc:TaxAmount", 2750),
                   (f"{L1}/cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount", 13750),
                   (f"{L1}/cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount", 2750),
                   ("cac:TaxTotal/cbc:TaxAmount", 2785),
                   ("cac:TaxTotal/cac:TaxSubtotal[cbc:Percent='20']/cbc:TaxableAmount", 13750),
                   ("cac:TaxTotal/cac:TaxSubtotal[cbc:Percent='20']/cbc:TaxAmount", 2750),
                   (f"{DIP}/cbc:LineExtensionAmount", 14100), (f"{DIP}/cbc:TaxExclusiveAmount", 14100),
                   (f"{DIP}/cbc:TaxInclusiveAmount", 16885), (f"{DIP}/cbc:PayableAmount", 16885)):
        yaz(k, yol, para(v))

@m("H08", "A", "Aritmetik", "Negatif miktar ve tutar (iade, satış faturasına eksi satır olarak yazılmış), toplamlar tutarlı", "İade yanlış belge tipiyle")
def _(k):
    yaz(k, f"{L2}/cbc:InvoicedQuantity", "-4")
    for yol, v in ((f"{L2}/cbc:LineExtensionAmount", -350), (f"{L2}/cac:TaxTotal/cbc:TaxAmount", -35),
                   (f"{L2}/cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount", -350),
                   (f"{L2}/cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount", -35),
                   ("cac:TaxTotal/cac:TaxSubtotal[cbc:Percent='10']/cbc:TaxableAmount", -350),
                   ("cac:TaxTotal/cac:TaxSubtotal[cbc:Percent='10']/cbc:TaxAmount", -35),
                   ("cac:TaxTotal/cbc:TaxAmount", 2465),
                   (f"{DIP}/cbc:LineExtensionAmount", 12150), (f"{DIP}/cbc:TaxExclusiveAmount", 12150),
                   (f"{DIP}/cbc:TaxInclusiveAmount", 14615), (f"{DIP}/cbc:PayableAmount", 14615)):
        yaz(k, yol, para(v))

@m("H09", "A", "Aritmetik", "Tutarlarda 3 ondalık hane", "Yuvarlama farkı, mutabakat sorunu")
def _(k): yaz(k, f"{DIP}/cbc:PayableAmount", "15385.004")

@m("H10", "A", "Kontrol vakası", "Ödenecek tutarda 1 kuruş fark (tolerans içi kontrol vakası)", "İhmal edilebilir")
def _(k): yaz(k, f"{DIP}/cbc:PayableAmount", "15385.01")

# ---------------------------------------------------------------- Tevkifat
@m("T01", "T", "Tevkifat", "TEVKIFAT tipinde tevkifat bloğu yok", "Tevkifat uygulanmaz, alıcı fazla öder")
def _(k):
    for w in xs(k, "//cac:WithholdingTaxTotal"):
        w.getparent().remove(w)
    yaz(k, f"{DIP}/cbc:PayableAmount", "12000.00")

@m("T02", "T", "Tevkifat", "Tevkifat kodu listede yok (699)", "Tevkifat türü tanınmaz")
def _(k):
    for d in xs(k, "//cac:WithholdingTaxTotal//cbc:TaxTypeCode"):
        d.text = "699"

@m("T03", "T", "Tevkifat", "Tevkifat kodu ile oranı uyumsuz (604 kodu, %90)", "Yanlış tevkifat oranı")
def _(k):
    for st in xs(k, "//cac:WithholdingTaxTotal/cac:TaxSubtotal"):
        yaz(st, "cbc:Percent", "90")
        yaz(st, "cbc:TaxAmount", "1800.00")
    for w in xs(k, "//cac:WithholdingTaxTotal/cbc:TaxAmount"):
        w.text = "1800.00"
    yaz(k, f"{DIP}/cbc:PayableAmount", "10200.00")

@m("T04", "T", "Tevkifat", "Tevkifat tutarı ≠ KDV × oran (kod ve oran doğru)", "Eksik/fazla tevkifat")
def _(k):
    for d in xs(k, "//cac:WithholdingTaxTotal//cbc:TaxAmount"):
        d.text = "900.00"
    yaz(k, f"{DIP}/cbc:PayableAmount", "11100.00")

@m("T05", "T", "Tevkifat", "Ödenecek tutardan tevkifat düşülmemiş", "Alıcı tevkifatı da satıcıya öder")
def _(k): yaz(k, f"{DIP}/cbc:PayableAmount", "12000.00")

@m("T06", "A", "Tevkifat", "SATIS tipinde tevkifat bloğu var (satır ve belge düzeyinde)", "Tip ile içerik çelişkisi")
def _(k):
    from src.bases import tevkifat_toplami
    sonrasina(x(k, f"{L1}/cac:TaxTotal"), tevkifat_toplami("604", 50, 2500, 1250))
    sonrasina(x(k, "cac:TaxTotal"), tevkifat_toplami("604", 50, 2500, 1250))
    yaz(k, f"{DIP}/cbc:PayableAmount", "14135.00")

@m("T08", "A", "Tevkifat", "SATIS tipinde tevkifat yalnız satır düzeyinde", "Tip ile içerik çelişkisi, dip toplama yansımaz")
def _(k):
    from src.bases import tevkifat_toplami
    sonrasina(x(k, f"{L1}/cac:TaxTotal"), tevkifat_toplami("604", 50, 2500, 1250))

@m("T07", "T", "Tevkifat", "Tevkifat yalnız satırda var, belge düzeyinde yok", "Dip toplamda tevkifat görünmez")
def _(k):
    w = x(k, "cac:WithholdingTaxTotal")
    k.remove(w)

# ---------------------------------------------------------------- İstisna
@m("I01", "I", "İstisna", "ISTISNA tipinde muafiyet kodu yok, gerekçe metni duruyor", "Gerekçesiz istisna, cezalı tarhiyat riski")
def _(k):
    for d in xs(k, "//cbc:TaxExemptionReasonCode"):
        d.getparent().remove(d)

@m("I06", "I", "İstisna", "ISTISNA tipinde ne muafiyet kodu ne gerekçe metni var", "Gerekçesiz istisna, cezalı tarhiyat riski")
def _(k):
    for d in xs(k, "//cbc:TaxExemptionReasonCode | //cbc:TaxExemptionReason"):
        d.getparent().remove(d)

@m("I02", "I", "İstisna", "Muafiyet kodu listede yok (399)", "Geçersiz istisna gerekçesi")
def _(k):
    for d in xs(k, "//cbc:TaxExemptionReasonCode"):
        d.text = "399"

@m("I03", "I", "İstisna", "ISTISNA tipinde KDV %20 hesaplanmış", "İstisna uygulanmamış, fazla vergi")
def _(k):
    for st in xs(k, "//cac:TaxTotal/cac:TaxSubtotal"):
        yaz(st, "cbc:Percent", "20")
        yaz(st, "cbc:TaxAmount", "2000.00")
    for t in xs(k, "//cac:TaxTotal/cbc:TaxAmount"):
        t.text = "2000.00"
    yaz(k, f"{DIP}/cbc:TaxInclusiveAmount", "12000.00")
    yaz(k, f"{DIP}/cbc:PayableAmount", "12000.00")

@m("I04", "I", "İstisna", "İhracat istisna kodu (701) TEMELFATURA/ISTISNA'da", "Yanlış istisna türü")
def _(k):
    for d in xs(k, "//cbc:TaxExemptionReasonCode"):
        d.text = "701"

@m("I05", "I", "İstisna", "Özel matrah kodu (801) ISTISNA tipinde", "Yanlış istisna türü")
def _(k):
    for d in xs(k, "//cbc:TaxExemptionReasonCode"):
        d.text = "801"

# ---------------------------------------------------------------- Döviz
@m("D01", "D", "Döviz", "USD faturada kur bilgisi yok", "TL karşılığı hesaplanamaz")
def _(k):
    kur = x(k, "cac:PricingExchangeRate")
    k.remove(kur)

@m("D02", "D", "Döviz", "Kur değeri gerçekçi değil (0,0412)", "TL karşılığı 1.000 kat hatalı")
def _(k): yaz(k, "cac:PricingExchangeRate/cbc:CalculationRate", "0.0412")

@m("D03", "D", "Döviz", "Bir tutar alanı farklı para biriminde (EUR)", "Karışık para birimi")
def _(k): x(k, f"{L1}/cbc:LineExtensionAmount").set("currencyID", "EUR")

@m("D04", "D", "Döviz", "Kaynak para birimi belge para biriminden farklı (EUR)", "Kur yanlış paraya ait")
def _(k): yaz(k, "cac:PricingExchangeRate/cbc:SourceCurrencyCode", "EUR")

@m("D05", "D", "Döviz", "Belge para birimi USD ama kur hedefi USD (TRY değil)", "TL karşılığı yok")
def _(k): yaz(k, "cac:PricingExchangeRate/cbc:TargetCurrencyCode", "USD")

# ---------------------------------------------------------------- Yapı
@m("Y01", "A", "Yapı", "Eleman sırası bozuk (IssueDate, UUID'den önce)", "Belge ayrıştırılamaz")
def _(k):
    u = x(k, "cbc:UUID")
    x(k, "cbc:IssueDate").addnext(u)

@m("Y02", "A", "Yapı", "Fatura numarası (cbc:ID) yok", "Belge ayrıştırılamaz")
def _(k): k.remove(x(k, "cbc:ID"))

@m("Y03", "A", "Yapı", "Alıcı bloğu yok", "Belge ayrıştırılamaz")
def _(k): k.remove(x(k, "cac:AccountingCustomerParty"))

@m("Y04", "A", "Yapı", "Tutar alanında para birimi niteliği yok", "Belge ayrıştırılamaz")
def _(k):
    d = x(k, f"{DIP}/cbc:PayableAmount")
    del d.attrib["currencyID"]

@m("Y05", "A", "Yapı", "Tutarda ondalık ayırıcı virgül (15385,00)", "Belge ayrıştırılamaz")
def _(k): yaz(k, f"{DIP}/cbc:PayableAmount", "15385,00")


# Hatayı yakalamak için gereken kontrolün türü (kök neden analizinin ekseni)
BICIM, KOD, CAPRAZ, ARIT, ANLAM = ("Biçim ve yapı", "Kod listesi", "Alanlar arası tutarlılık",
                                   "Aritmetik", "Anlamsal doğruluk")
KONTROL_TURU = {
    "K01": BICIM, "K02": ANLAM, "K03": ANLAM, "K04": ANLAM, "K05": BICIM, "K06": BICIM, "K07": CAPRAZ,
    "B01": BICIM, "B02": CAPRAZ, "B03": BICIM, "B04": ANLAM, "B05": ANLAM, "B06": KOD, "B07": KOD,
    "B08": CAPRAZ, "B09": CAPRAZ, "B10": KOD, "B11": CAPRAZ,
    "C01": KOD, "C02": KOD, "C03": KOD, "C04": ANLAM, "C05": ANLAM, "C06": CAPRAZ,
    "H01": ARIT, "H02": ARIT, "H03": ARIT, "H04": ARIT, "H05": ARIT, "H06": ARIT, "H07": ANLAM,
    "H08": CAPRAZ, "H09": BICIM, "H10": ARIT,
    "T01": CAPRAZ, "T02": KOD, "T03": CAPRAZ, "T04": ARIT, "T05": ARIT, "T06": CAPRAZ, "T07": CAPRAZ,
    "T08": CAPRAZ,
    "I01": CAPRAZ, "I06": CAPRAZ, "I02": KOD, "I03": CAPRAZ, "I04": CAPRAZ, "I05": CAPRAZ,
    "D01": CAPRAZ, "D02": ANLAM, "D03": CAPRAZ, "D04": CAPRAZ, "D05": CAPRAZ,
    "Y01": BICIM, "Y02": BICIM, "Y03": BICIM, "Y04": BICIM, "Y05": BICIM,
}
assert set(KONTROL_TURU) == {mu.id for mu in M}, "Her mutasyonun kontrol türü tanımlı olmalı"
