# -*- coding: utf-8 -*-
"""
main.py va importer.py ikkalasida ham kerak bo'ladigan umumiy funksiyalar.
"""
import database as db


def turi_kodidan(mijoz_turi_kodi, mijoz_turi):
    """Portfeldagi kod asosida jismoniy/yuridik ekanini aniqlaydi."""
    kod = str(mijoz_turi_kodi or '').strip().upper()
    turi = str(mijoz_turi or '').strip().upper()
    if turi in ('LE',) or kod in ('9', 'J', 'YUR'):
        return 'yuridik'
    return 'jismoniy'


def kalit_candidates(portfel_row):
    """Mijozni bog'lash uchun ishlatilishi mumkin bo'lgan ID'lar ro'yxati."""
    return [portfel_row.get('stir'), portfel_row.get('pinfl'), portfel_row.get('unikal')]


def resolve_mijoz(portfel_row):
    """Portfel qatoriga mos mijozni (agar bazada bo'lsa) topadi."""
    turi = turi_kodidan(portfel_row.get('mijoz_turi_kodi'), portfel_row.get('mijoz_turi'))
    for kalit in kalit_candidates(portfel_row):
        if not kalit:
            continue
        kalit = str(kalit).strip()
        m = db.find_mijoz(turi, kalit)
        if m:
            return turi, m
    return turi, None
