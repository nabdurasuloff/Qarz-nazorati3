# -*- coding: utf-8 -*-
"""
Ma'lumotlar bazasi (SQLite) bilan ishlash.
Dastur ishga tushganda 'qarz_nazorat.db' fayli avtomatik yaratiladi.
"""
import sqlite3
import os
import sys
import datetime


def _app_dir():
    # .exe (PyInstaller --onefile) sifatida ishga tushganda ma'lumotlar bazasi
    # dastur fayli joylashgan papkada saqlanadi (vaqtinchalik _MEIPASS'da emas),
    # shunda dastur qayta ishga tushirilganda ma'lumotlar yo'qolmaydi.
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


DB_PATH = os.path.join(_app_dir(), 'qarz_nazorat.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS portfel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        port_kod TEXT,
        anketa_raqami TEXT,
        unikal TEXT,
        stir TEXT,
        pinfl TEXT,
        filial_kodi TEXT,
        viloyat TEXT,
        tarmoq TEXT,
        stage TEXT,
        mijoz_turi_kodi TEXT,
        mijoz_turi TEXT,
        mijoz_nomi TEXT,
        valyuta TEXT,
        kredit_hisob_raqami TEXT,
        yillik_foiz REAL,
        shartnoma_sanasi TEXT,
        shartnoma_tugash_sanasi TEXT,
        tulov_maqsadi TEXT,
        dpd_asosiy INTEGER DEFAULT 0,
        dpd_foiz INTEGER DEFAULT 0,
        dpd_max INTEGER DEFAULT 0,
        ead REAL DEFAULT 0,
        jami_qarz REAL DEFAULT 0,
        asosiy_qarz REAL DEFAULT 0,
        foiz_qarz REAL DEFAULT 0,
        jarima REAL DEFAULT 0,
        import_sanasi TEXT,
        holat TEXT DEFAULT 'yangi'
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS mijozlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turi TEXT,                  -- 'jismoniy' yoki 'yuridik'
        kalit TEXT,                 -- bog'lash uchun: unikal / стир / пинфл
        ism TEXT,
        manzil TEXT,
        telefon TEXT,
        hujjat_raqami TEXT,         -- pasport yoki STIR
        rahbar_ism TEXT,
        import_sanasi TEXT,
        UNIQUE(kalit, turi)
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS xatlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        portfel_id INTEGER,
        anketa_raqami TEXT,
        mijoz_nomi TEXT,
        mijoz_turi TEXT,
        xat_turi TEXT,               -- 'Ogohlantirish' / 'Talabnoma'
        yaratilgan_sana TEXT,
        muddat_sana TEXT,
        holat TEXT DEFAULT 'tayyor', -- tayyor / yuborildi / muddati_otgan
        yuborilgan_sana TEXT,
        fayl_yoli TEXT,
        FOREIGN KEY(portfel_id) REFERENCES portfel(id)
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS sozlamalar (
        kalit TEXT PRIMARY KEY,
        qiymat TEXT
    )
    ''')

    defaults = {
        'bank_nomi': '"АГРОБАНК" АТБ',
        'bank_qisqa_nomi': 'АГРОБАНК',
        'bank_manzil': "100096, Ўзбекистон Республикаси, Тошкент ш., Муқимий кўчаси, 43",
        'bank_email': 'headoffice@agrobank.uz',
        'bank_sayt': 'www.agrobank.uz',
        'bank_tel': '1216',
        'bank_mobil_ilova': 'AGROBANK',
        'bank_kodi': '00382',
        'aloqa_markazi_tel': '1216',
        'filial_nomi': 'Боёвут',
        'filial_tel': '71-202-80-08 (382-01)',
        'rahbar_ism': '',
        'tolov_muddati_kun': '10',
        'eslatma_muddati_kun': '3',
        'dpd_chegara_kun': '45',
    }
    for k, v in defaults.items():
        cur.execute('INSERT OR IGNORE INTO sozlamalar (kalit, qiymat) VALUES (?, ?)', (k, v))

    conn.commit()
    conn.close()


def get_setting(kalit, default=''):
    conn = get_conn()
    row = conn.execute('SELECT qiymat FROM sozlamalar WHERE kalit=?', (kalit,)).fetchone()
    conn.close()
    return row['qiymat'] if row else default


def get_all_settings():
    conn = get_conn()
    rows = conn.execute('SELECT kalit, qiymat FROM sozlamalar').fetchall()
    conn.close()
    return {r['kalit']: r['qiymat'] for r in rows}


def set_setting(kalit, qiymat):
    conn = get_conn()
    conn.execute('INSERT INTO sozlamalar (kalit, qiymat) VALUES (?, ?) '
                 'ON CONFLICT(kalit) DO UPDATE SET qiymat=excluded.qiymat', (kalit, qiymat))
    conn.commit()
    conn.close()


def clear_portfel():
    conn = get_conn()
    conn.execute('DELETE FROM portfel')
    conn.commit()
    conn.close()


def insert_portfel_rows(rows):
    """rows: list of dicts matching portfel columns (without id)."""
    conn = get_conn()
    cur = conn.cursor()
    cols = ['port_kod', 'anketa_raqami', 'unikal', 'stir', 'pinfl', 'filial_kodi', 'viloyat',
            'tarmoq', 'stage',
            'mijoz_turi_kodi', 'mijoz_turi', 'mijoz_nomi', 'valyuta', 'kredit_hisob_raqami',
            'yillik_foiz', 'shartnoma_sanasi', 'shartnoma_tugash_sanasi', 'tulov_maqsadi',
            'dpd_asosiy', 'dpd_foiz', 'dpd_max', 'ead', 'jami_qarz', 'asosiy_qarz', 'foiz_qarz',
            'jarima', 'import_sanasi', 'holat']
    placeholders = ','.join(['?'] * len(cols))
    sql = f"INSERT INTO portfel ({','.join(cols)}) VALUES ({placeholders})"
    now = datetime.datetime.now().isoformat()
    for r in rows:
        r.setdefault('import_sanasi', now)
        r.setdefault('holat', 'yangi')
        values = [r.get(c) for c in cols]
        cur.execute(sql, values)
    conn.commit()
    conn.close()


def upsert_mijoz(turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism=''):
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.execute('''
        INSERT INTO mijozlar (turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism, import_sanasi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(kalit, turi) DO UPDATE SET
            ism=excluded.ism, manzil=excluded.manzil, telefon=excluded.telefon,
            hujjat_raqami=excluded.hujjat_raqami, rahbar_ism=excluded.rahbar_ism,
            import_sanasi=excluded.import_sanasi
    ''', (turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism, now))
    conn.commit()
    conn.close()


def find_mijoz(turi, kalit):
    conn = get_conn()
    row = conn.execute('SELECT * FROM mijozlar WHERE turi=? AND kalit=?', (turi, kalit)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tarmoq_stage3_breakdown(limit=8):
    """Tarmoq (soha) bo'yicha Stage 3 (eng muammoli) kreditlar taqsimoti."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT COALESCE(NULLIF(TRIM(tarmoq), ''), "Noma'lum") AS tarmoq,
               COUNT(*) AS soni, SUM(jami_qarz) AS jami
        FROM portfel
        WHERE TRIM(stage) = '3'
        GROUP BY tarmoq
        ORDER BY jami DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_viloyat_breakdown(chegara_kun=45, limit=8):
    """Viloyat bo'yicha 45+ kun mijozlar soni va muddati o'tgan qarz yig'indisi."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT COALESCE(NULLIF(TRIM(viloyat), ''), "Noma'lum") AS viloyat,
               COUNT(*) AS soni, SUM(jami_qarz) AS jami
        FROM portfel
        WHERE dpd_max >= ?
        GROUP BY viloyat
        ORDER BY jami DESC
        LIMIT ?
    ''', (chegara_kun, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_turi_breakdown(chegara_kun=45):
    """Jismoniy/yuridik (portfeldagi kod bo'yicha taxminiy) taqsimot."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT mijoz_turi_kodi, mijoz_turi, COUNT(*) AS soni
        FROM portfel WHERE dpd_max >= ?
        GROUP BY mijoz_turi_kodi, mijoz_turi
    ''', (chegara_kun,)).fetchall()
    conn.close()
    jismoniy, yuridik = 0, 0
    for r in rows:
        kod = str(r['mijoz_turi_kodi'] or '').strip().upper()
        turi = str(r['mijoz_turi'] or '').strip().upper()
        if turi == 'LE' or kod in ('9', 'J', 'YUR'):
            yuridik += r['soni']
        else:
            jismoniy += r['soni']
    return {'jismoniy': jismoniy, 'yuridik': yuridik}


def get_bugungi_harakatlar():
    """Bugun yaratilgan va bugun yuborilgan xatlar soni."""
    bugun = datetime.date.today().isoformat()
    conn = get_conn()
    yaratildi = conn.execute(
        "SELECT COUNT(*) c FROM xatlar WHERE yaratilgan_sana LIKE ?", (bugun + '%',)
    ).fetchone()['c']
    yuborildi = conn.execute(
        "SELECT COUNT(*) c FROM xatlar WHERE yuborilgan_sana LIKE ?", (bugun + '%',)
    ).fetchone()['c']
    conn.close()
    return {'yaratildi': yaratildi, 'yuborildi': yuborildi}


def get_latest_xat_status_by_portfel():
    """Har bir portfel_id uchun eng oxirgi xat holatini qaytaradi: {portfel_id: holat}"""
    conn = get_conn()
    rows = conn.execute('''
        SELECT portfel_id, holat FROM xatlar x1
        WHERE yaratilgan_sana = (
            SELECT MAX(yaratilgan_sana) FROM xatlar x2 WHERE x2.portfel_id = x1.portfel_id
        )
    ''').fetchall()
    conn.close()
    return {r['portfel_id']: r['holat'] for r in rows}


def get_portfel_45_kun(chegara_kun=45):
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM portfel WHERE dpd_max >= ? ORDER BY dpd_max DESC', (chegara_kun,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_portfel_by_id(portfel_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM portfel WHERE id=?', (portfel_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_portfel_by_anketa(anketa_raqami):
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM portfel WHERE anketa_raqami LIKE ?', (f'%{anketa_raqami}%',)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_xat(portfel_id, anketa_raqami, mijoz_nomi, mijoz_turi, xat_turi, fayl_yoli, muddat_kun=3):
    conn = get_conn()
    now = datetime.datetime.now()
    muddat = now + datetime.timedelta(days=muddat_kun)
    conn.execute('''
        INSERT INTO xatlar (portfel_id, anketa_raqami, mijoz_nomi, mijoz_turi, xat_turi,
                             yaratilgan_sana, muddat_sana, holat, fayl_yoli)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'tayyor', ?)
    ''', (portfel_id, anketa_raqami, mijoz_nomi, mijoz_turi, xat_turi,
          now.isoformat(), muddat.isoformat(), fayl_yoli))
    conn.commit()
    conn.close()


def get_xatlar(holat=None):
    conn = get_conn()
    if holat:
        rows = conn.execute('SELECT * FROM xatlar WHERE holat=? ORDER BY yaratilgan_sana DESC', (holat,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM xatlar ORDER BY yaratilgan_sana DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_xat_yuborildi(xat_id):
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.execute("UPDATE xatlar SET holat='yuborildi', yuborilgan_sana=? WHERE id=?", (now, xat_id))
    conn.commit()
    conn.close()


def update_muddati_otganlar():
    """3 kunlik muddat o'tgan, lekin hali yuborilmagan xatlarni belgilaydi."""
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.execute('''
        UPDATE xatlar SET holat='muddati_otgan'
        WHERE holat='tayyor' AND muddat_sana < ?
    ''', (now,))
    conn.commit()
    n = conn.execute("SELECT COUNT(*) c FROM xatlar WHERE holat='muddati_otgan'").fetchone()['c']
    conn.close()
    return n
