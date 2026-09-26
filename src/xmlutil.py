"""lxml yardımcıları: UBL-TR ad alanları ve küçük düzenleme fonksiyonları."""
from copy import deepcopy
from decimal import Decimal

from lxml import etree

NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
}
CAC, CBC = "{%s}" % NS["cac"], "{%s}" % NS["cbc"]


def oku(yol) -> etree._ElementTree:
    return etree.parse(str(yol), etree.XMLParser(remove_blank_text=True))


def x(kok, yol):
    """Tek düğüm; bulunamazsa hata (mutasyonun sessizce boşa düşmemesi için)."""
    s = kok.xpath(yol, namespaces=NS)
    if not s:
        raise LookupError(f"Bulunamadı: {yol}")
    return s[0]


def xs(kok, yol):
    return kok.xpath(yol, namespaces=NS)


def yaz(kok, yol, deger):
    x(kok, yol).text = str(deger)


def e(ad, metin=None, **nit):
    on, yerel = ad.split(":")
    d = etree.Element((CAC if on == "cac" else CBC) + yerel, nit)
    if metin is not None:
        d.text = str(metin)
    return d


def sonrasina(dugum, yeni):
    dugum.addnext(yeni)
    return yeni


def para(d) -> str:
    return str(Decimal(d).quantize(Decimal("0.01")))


def kopya(agac):
    return deepcopy(agac)


def bayt(agac) -> bytes:
    return etree.tostring(agac, xml_declaration=True, encoding="UTF-8", pretty_print=True)
