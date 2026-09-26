"""VKN ve TCKN kontrol hanesi algoritmaları (Gelir İdaresi ve NVİ'nin yayımladığı yöntem)."""


def vkn_gecerli(vkn: str) -> bool:
    if len(vkn) != 10 or not vkn.isdigit():
        return False
    d = [int(c) for c in vkn]
    toplam = 0
    for i in range(9):
        tmp = (d[i] + 9 - i) % 10
        v = (tmp * 2 ** (9 - i)) % 9
        if tmp != 0 and v == 0:
            v = 9
        toplam += v
    return (10 - toplam % 10) % 10 == d[9]


def tckn_gecerli(tckn: str) -> bool:
    if len(tckn) != 11 or not tckn.isdigit() or tckn[0] == "0":
        return False
    d = [int(c) for c in tckn]
    d10 = ((d[0] + d[2] + d[4] + d[6] + d[8]) * 7 - (d[1] + d[3] + d[5] + d[7])) % 10
    return d10 == d[9] and sum(d[:10]) % 10 == d[10]


def vkn_tamamla(ilk9: str) -> str:
    for k in range(10):
        if vkn_gecerli(ilk9 + str(k)):
            return ilk9 + str(k)
    raise ValueError(ilk9)
