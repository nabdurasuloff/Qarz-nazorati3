# -*- coding: utf-8 -*-
"""
Excel/XLSB fayllardan ma'lumot import qilish.
"""
import pandas as pd
import database as db
import util

# Portfel faylidagi ustun nomlari -> bazamizdagi maydon nomlari
PORTFEL_COLMAP = {
    'Порт_код': 'port_kod',
    'Анкета раками': 'anketa_raqami',
    'Уникал': 'unikal',
    'СТИР': 'stir',
    'ПИНФЛ': 'pinfl',
    'Филиал коди': 'filial_kodi',
    'Вилоят': 'viloyat',
    'Тармок': 'tarmoq',
    'Stage': 'stage',
    'Жис / юр / Ятт - коди': 'mijoz_turi_kodi',
    'Мижоз тури': 'mijoz_turi',
    'Мижоз номи': 'mijoz_nomi',
    'Валюта коди': 'valyuta',
    'Кредит хисоб раками': 'kredit_hisob_raqami',
    'Йиллик фоиз ставкаси': 'yillik_foiz',
    'Шартнома санаси': 'shartnoma_sanasi',
    'Шартнома тугаш санаси': 'shartnoma_tugash_sanasi',
    'Тулов максади': 'tulov_maqsadi',
    'DPD days of principal -Муддати ўтган асосий қарз кунлар сони': 'dpd_asosiy',
    'DPD days of percentage -Муддати ўтган фоиз кунлар сони': 'dpd_foiz',
    'EAD (Жами қарздорлик суммаси)': 'ead',
    'Муддати утган жами кредит колдиги (экв)': 'jami_qarz',
}


def _clean_id(val):
    """Raqamli ID maydonlarini (СТИР, ПИНФЛ, Уникал...) '123.0' emas '123' ko'rinishga keltiradi."""
    if val is None:
        return None
    try:
        import math
        if isinstance(val, float):
            if math.isnan(val):
                return None
            if val == int(val):
                return str(int(val))
            return str(val)
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s if s and s.lower() != 'nan' else None


ID_FIELDS = {'anketa_raqami', 'unikal', 'stir', 'pinfl', 'filial_kodi', 'kredit_hisob_raqami'}


def import_portfel_xlsb(filepath, sheet_name=None, progress_cb=None):
    """
    Portfel .xlsb faylini o'qib, bazaga yozadi.
    sheet_name berilmasa, ma'lumot bor birinchi varaq olinadi.
    """
    xl = pd.ExcelFile(filepath, engine='pyxlsb')
    sheets = xl.sheet_names

    df = None
    chosen_sheet = None
    if sheet_name:
        df = pd.read_excel(filepath, engine='pyxlsb', sheet_name=sheet_name)
        chosen_sheet = sheet_name
    else:
        for s in sheets:
            tmp = pd.read_excel(filepath, engine='pyxlsb', sheet_name=s)
            if len(tmp) > 0:
                df = tmp
                chosen_sheet = s
                break
        if df is None:
            df = pd.read_excel(filepath, engine='pyxlsb', sheet_name=sheets[0])
            chosen_sheet = sheets[0]

    available_cols = {c: PORTFEL_COLMAP[c] for c in PORTFEL_COLMAP if c in df.columns}
    missing = [c for c in PORTFEL_COLMAP if c not in df.columns]

    rows = []
    total = len(df)
    for i, (_, r) in enumerate(df.iterrows()):
        row = {}
        for src_col, dst_field in available_cols.items():
            val = r.get(src_col)
            if dst_field in ID_FIELDS:
                val = _clean_id(val)
            row[dst_field] = val

        dpd_a = row.get('dpd_asosiy') or 0
        dpd_f = row.get('dpd_foiz') or 0
        try:
            dpd_a = int(dpd_a)
        except (TypeError, ValueError):
            dpd_a = 0
        try:
            dpd_f = int(dpd_f)
        except (TypeError, ValueError):
            dpd_f = 0
        row['dpd_asosiy'] = dpd_a
        row['dpd_foiz'] = dpd_f
        row['dpd_max'] = max(dpd_a, dpd_f)

        jami = row.get('jami_qarz') or 0
        try:
            jami = float(jami)
        except (TypeError, ValueError):
            jami = 0.0
        row['jami_qarz'] = jami
        # Asosiy/foiz/jarima taqsimoti alohida ustunlar sifatida ushbu
        # faylda yo'q — hozircha jami summa asosiy qarz sifatida olinadi.
        # Aniq taqsimot ustunlari ma'lum bo'lgach, shu joyni yangilash kerak.
        row.setdefault('asosiy_qarz', jami)
        row.setdefault('foiz_qarz', 0)
        row.setdefault('jarima', 0)

        rows.append(row)
        if progress_cb and i % 200 == 0:
            progress_cb(i, total)

    db.insert_portfel_rows(rows)
    return {
        'sheet': chosen_sheet,
        'jami_qator': len(rows),
        'topilmagan_ustunlar': missing,
    }


def preview_mijozlar_columns(filepath, sheet_name=0, nrows=5):
    """Mijozlar faylining ustunlarini va namuna qatorlarini qaytaradi (moslashtirish uchun)."""
    df = pd.read_excel(filepath, sheet_name=sheet_name, nrows=nrows)
    return list(df.columns), df.head(nrows)


def import_mijozlar_xlsx(filepath, turi, column_mapping, sheet_name=0, progress_cb=None):
    """
    turi: 'jismoniy' yoki 'yuridik'
    column_mapping: dict — {'kalit': 'Excel ustun nomi', 'ism': '...', 'manzil': '...',
                             'telefon': '...', 'hujjat_raqami': '...', 'rahbar_ism': '...'}
    Faqat 'kalit' va 'ism' majburiy — qolganlari bo'sh qoldirilishi mumkin.
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    total = len(df)
    count = 0
    for i, (_, r) in enumerate(df.iterrows()):
        def get(field):
            col = column_mapping.get(field)
            if not col or col not in df.columns:
                return ''
            val = r.get(col)
            if pd.isna(val):
                return ''
            return str(val).strip()

        kalit = get('kalit')
        ism = get('ism')
        if not kalit or not ism:
            continue
        db.upsert_mijoz(
            turi=turi,
            kalit=kalit,
            ism=ism,
            manzil=get('manzil'),
            telefon=_clean_id(get('telefon')) or get('telefon'),
            hujjat_raqami=get('hujjat_raqami'),
            rahbar_ism=get('rahbar_ism'),
        )
        count += 1
        if progress_cb and i % 200 == 0:
            progress_cb(i, total)

    return {'jami_qator': total, 'import_qilingan': count}


# ---------------------------------------------------------------------------
# Talabnoma ro'yxatini Excel'ga eksport qilish / tahrirlangan Excel'ni qaytarib olish
# ---------------------------------------------------------------------------

TAHLIL_EXPORT_COLS = [
    ('anketa_raqami', 'Anketa raqami'),
    ('mijoz_nomi', 'Mijoz nomi'),
    ('turi', 'Turi'),
    ('manzil', 'Manzil'),
    ('telefon', 'Telefon'),
    ('dpd_max', 'DPD (kun)'),
    ('jami_qarz', "Muddati o'tgan qarz"),
    ('xat_turi', 'Xat turi'),
]


def export_tahlil_excel(rows, output_path):
    """
    rows: list of dict — har birida anketa_raqami, mijoz_nomi, turi, manzil,
          telefon, dpd_max, jami_qarz, xat_turi kalitlari bo'lishi kerak.
    Manzil va Telefon ustunlari tahrirlash uchun — qolganlari faqat ma'lumot uchun.
    """
    cols = [c[0] for c in TAHLIL_EXPORT_COLS]
    headers = [c[1] for c in TAHLIL_EXPORT_COLS]
    data = [[r.get(c, '') for c in cols] for r in rows]
    df = pd.DataFrame(data, columns=headers)
    df.to_excel(output_path, index=False)
    return output_path


def import_manzil_updates(filepath):
    """
    Tahrirlangan Excel'ni o'qib, 'Manzil' / 'Telefon' ustunlaridagi o'zgarishlarni
    mijozlar bazasiga yozadi (Anketa raqami orqali portfel bilan bog'lab).
    """
    df = pd.read_excel(filepath)
    required = {'Anketa raqami', 'Manzil'}
    if not required.issubset(set(df.columns)):
        raise ValueError(
            "Excel faylida 'Anketa raqami' va 'Manzil' ustunlari topilmadi. "
            "Iltimos, dastur bergan asl Excel tuzilmasini o'zgartirmang."
        )

    updated = 0
    skipped = 0
    for _, r in df.iterrows():
        anketa = r.get('Anketa raqami')
        if pd.isna(anketa):
            continue
        anketa = str(anketa).strip()
        yangi_manzil = r.get('Manzil')
        yangi_manzil = '' if pd.isna(yangi_manzil) else str(yangi_manzil).strip()
        yangi_telefon = _clean_id(r.get('Telefon')) or ''
        yangi_ism = r.get('Mijoz nomi')
        yangi_ism = None if pd.isna(yangi_ism) else str(yangi_ism).strip()

        portfel_rows = db.get_portfel_by_anketa(anketa)
        if not portfel_rows:
            skipped += 1
            continue
        prow = portfel_rows[0]
        turi, mijoz = util.resolve_mijoz(prow)

        if mijoz:
            kalit = mijoz['kalit']
            ism = yangi_ism or mijoz['ism']
            hujjat = mijoz.get('hujjat_raqami', '') or ''
            rahbar = mijoz.get('rahbar_ism', '') or ''
        else:
            kalit = next((k for k in util.kalit_candidates(prow) if k), None)
            if not kalit:
                skipped += 1
                continue
            ism = yangi_ism or prow.get('mijoz_nomi', '')
            hujjat = ''
            rahbar = ''

        db.upsert_mijoz(
            turi=turi, kalit=str(kalit), ism=ism, manzil=yangi_manzil,
            telefon=yangi_telefon, hujjat_raqami=hujjat, rahbar_ism=rahbar,
        )
        updated += 1

    return {'yangilandi': updated, 'otkazib_yuborildi': skipped}
