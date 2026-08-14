# -*- coding: utf-8 -*-
"""
Qarz Nazorat Dastur — Bosh oyna (Tkinter GUI)

Ishga tushirish:  python main.py
"""
import os
import sys
import threading
import datetime
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

import database as db
import importer
import letters
import util

def _app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _app_dir()
XATLAR_DIR = os.path.join(APP_DIR, 'yaratilgan_xatlar')

BG = '#F7F3EA'
INK = '#20281F'
STAMP = '#2F5233'
KRAFT = '#A9805A'
WHITE = '#FFFDF8'
ERR = '#8C3B2E'


resolve_mijoz = util.resolve_mijoz  # qulaylik uchun shu modulda ham mavjud


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Qarz Nazorat va Talabnoma Tizimi")
        self.geometry("1180x720")
        self.configure(bg=BG)

        self._setup_style()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_dashboard = DashboardTab(self.notebook, self)
        self.tab_portfel = PortfelTab(self.notebook, self)
        self.tab_mijozlar = MijozlarTab(self.notebook, self)
        self.tab_tahlil = TahlilTab(self.notebook, self)
        self.tab_xatlar = XatlarTab(self.notebook, self)
        self.tab_sozlamalar = SozlamalarTab(self.notebook, self)

        self.notebook.add(self.tab_dashboard, text='  Bosh sahifa  ')
        self.notebook.add(self.tab_portfel, text='  Portfel  ')
        self.notebook.add(self.tab_mijozlar, text='  Mijozlar bazasi  ')
        self.notebook.add(self.tab_tahlil, text='  Tahlil / Talabnoma  ')
        self.notebook.add(self.tab_xatlar, text='  Xatlar holati  ')
        self.notebook.add(self.tab_sozlamalar, text='  Sozlamalar  ')

        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        self._check_muddat_otganlar()

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[14, 8])
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=INK, font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground=INK)
        style.configure('Sub.TLabel', font=('Segoe UI', 9), foreground='#5B6459')
        style.configure('Stat.TLabel', font=('Consolas', 22, 'bold'), foreground=STAMP)
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=8)
        style.configure('Accent.TButton', background=STAMP, foreground=WHITE)
        style.map('Accent.TButton', background=[('active', '#3E6B45')])
        style.configure('Treeview', font=('Segoe UI', 9), rowheight=26)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))

    def _on_tab_changed(self, event):
        current = event.widget.tab(event.widget.select(), 'text').strip()
        if current == 'Bosh sahifa':
            self.tab_dashboard.refresh()
        elif current == 'Tahlil / Talabnoma':
            self.tab_tahlil.refresh_stats()
        elif current == 'Xatlar holati':
            self.tab_xatlar.refresh()

    def _check_muddat_otganlar(self):
        n = db.update_muddati_otganlar()
        if n > 0:
            messagebox.showwarning(
                "Eslatma",
                f"{n} ta xat yuborish muddati tugagan! 'Xatlar holati' bo'limini tekshiring."
            )
        self.after(60 * 60 * 1000, self._check_muddat_otganlar)  # har soatda tekshirish


class ScrollableFrame(ttk.Frame):
    """Vertikal scroll qila oladigan konteyner."""
    def __init__(self, parent):
        super().__init__(parent)
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        self.body = ttk.Frame(canvas)

        self.body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas_window = canvas.create_window((0, 0), window=self.body, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind_all('<MouseWheel>', _on_mousewheel)


def _fmt_summa_qisqa(v):
    v = v or 0
    if v >= 1_000_000_000:
        return f"{v / 1_000_000_000:.1f} mlrd"
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f} mln"
    return f"{v:,.0f}".replace(',', ' ')


class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        scroll = ScrollableFrame(self)
        scroll.pack(fill='both', expand=True)
        body = scroll.body

        ttk.Label(body, text="Qarz Nazorat va Talabnoma Tizimi", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(body, text="Portfelni tahlil qiling, muddati o'tgan mijozlarga xat tayyorlang.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 16))

        cards = ttk.Frame(body)
        cards.pack(fill='x', padx=20)
        self.card_portfel = self._card(cards, "Portfeldagi kreditlar")
        self.card_45kun = self._card(cards, "45+ kun muddati o'tgan")
        self.card_tayyor = self._card(cards, "Yuborilmagan xatlar")
        self.card_otgan = self._card(cards, "Muddati o'tgan xatlar")

        # ---- Bugungi harakatlar ----
        ttk.Label(body, text="Bugungi harakatlar", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(24, 8))
        today_cards = ttk.Frame(body)
        today_cards.pack(fill='x', padx=20)
        self.card_bugun_yaratildi = self._card(today_cards, "Bugun yaratilgan xatlar", small=True)
        self.card_bugun_yuborildi = self._card(today_cards, "Bugun yuborilgan xatlar", small=True)

        # ---- Statistika (grafik) ----
        ttk.Label(body, text="Statistika", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(24, 8))
        charts_row = ttk.Frame(body)
        charts_row.pack(fill='x', padx=20)

        viloyat_box = tk.Frame(charts_row, bg=WHITE, highlightbackground='#E4DCC8', highlightthickness=1)
        viloyat_box.pack(side='left', fill='both', expand=True, padx=(0, 8), ipady=10)
        tk.Label(viloyat_box, text="Tarmoq bo'yicha Stage 3 kreditlar",
                 bg=WHITE, fg=INK, font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=12, pady=(4, 8))
        self.viloyat_canvas = tk.Canvas(viloyat_box, bg=WHITE, height=200, highlightthickness=0)
        self.viloyat_canvas.pack(fill='x', padx=12, pady=(0, 8))

        turi_box = tk.Frame(charts_row, bg=WHITE, highlightbackground='#E4DCC8', highlightthickness=1)
        turi_box.pack(side='left', fill='both', expand=True, padx=(8, 0), ipady=10)
        tk.Label(turi_box, text="Jismoniy / Yuridik shaxslar taqsimoti",
                 bg=WHITE, fg=INK, font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=12, pady=(4, 8))
        self.turi_canvas = tk.Canvas(turi_box, bg=WHITE, height=200, highlightthickness=0)
        self.turi_canvas.pack(fill='x', padx=12, pady=(0, 8))

        # ---- So'nggi harakatlar ----
        ttk.Label(body, text="So'nggi harakatlar", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(24, 8))
        cols = ('sana', 'mijoz', 'xat_turi', 'holat')
        self.recent_tree = ttk.Treeview(body, columns=cols, show='headings', height=8)
        headings = {'sana': 'Sana', 'mijoz': 'Mijoz', 'xat_turi': 'Xat turi', 'holat': 'Holat'}
        widths = {'sana': 140, 'mijoz': 320, 'xat_turi': 110, 'holat': 130}
        for c in cols:
            self.recent_tree.heading(c, text=headings[c])
            self.recent_tree.column(c, width=widths[c])
        self.recent_tree.pack(fill='x', padx=20, pady=(0, 10))

        # ---- Ishlash tartibi ----
        info = ttk.Frame(body)
        info.pack(fill='x', padx=20, pady=(14, 30))
        ttk.Label(info, text="Ishlash tartibi:", style='Header.TLabel').pack(anchor='w')
        steps = [
            "1. 'Portfel' bo'limida .xlsb faylni yuklang.",
            "2. 'Mijozlar bazasi' bo'limida jismoniy/yuridik shaxslar ma'lumotini import qiling.",
            "3. 'Tahlil / Talabnoma' bo'limida 45 kundan o'tgan mijozlarni ko'ring, xat yarating.",
            "4. 'Xatlar holati' bo'limida yuborilganlarni belgilang — 3 kun ichida yuborilmasa, eslatma chiqadi.",
        ]
        for s in steps:
            ttk.Label(info, text=s, font=('Segoe UI', 10)).pack(anchor='w', pady=3)

        self.refresh()

    def _card(self, parent, title, small=False):
        f = tk.Frame(parent, bg=WHITE, highlightbackground='#E4DCC8', highlightthickness=1)
        f.pack(side='left', expand=True, fill='both', padx=6, ipady=14 if not small else 10)
        num = tk.Label(f, text='0', bg=WHITE, fg=STAMP, font=('Consolas', 22 if small else 26, 'bold'))
        num.pack(pady=(10, 0))
        tk.Label(f, text=title, bg=WHITE, fg='#5B6459', font=('Segoe UI', 9),
                 wraplength=220, justify='center').pack(pady=(0, 8))
        return num

    def _draw_hbar_chart(self, canvas, items, label_key, value_key, value_fmt=str, color=STAMP):
        """items: list of dict; oddiy tk.Canvas'da gorizontal ustunli diagramma chizadi."""
        canvas.delete('all')
        canvas.update_idletasks()
        width = canvas.winfo_width() or 380
        if not items:
            canvas.create_text(width // 2, 90, text="Ma'lumot yo'q", fill='#5B6459', font=('Segoe UI', 9))
            return
        max_val = max((it[value_key] or 0) for it in items) or 1
        row_h = 22
        label_w = 150
        bar_max_w = max(width - label_w - 130, 40)
        y = 8
        for it in items:
            label = str(it[label_key])[:22]
            val = it[value_key] or 0
            bar_w = int((val / max_val) * bar_max_w)
            canvas.create_text(4, y + row_h // 2, text=label, anchor='w',
                                font=('Segoe UI', 8), fill=INK)
            canvas.create_rectangle(label_w, y + 3, label_w + bar_w, y + row_h - 3,
                                     fill=color, outline='')
            canvas.create_text(label_w + bar_w + 6, y + row_h // 2,
                                text=value_fmt(val), anchor='w',
                                font=('Segoe UI', 8), fill='#5B6459')
            y += row_h
        canvas.configure(height=max(y + 6, 60))

    def refresh(self):
        conn = db.get_conn()
        portfel_n = conn.execute('SELECT COUNT(*) c FROM portfel').fetchone()['c']
        conn.close()
        chegara = int(db.get_setting('dpd_chegara_kun', 45))
        kun45 = len(db.get_portfel_45_kun(chegara))
        tayyor = len(db.get_xatlar('tayyor'))
        otgan = len(db.get_xatlar('muddati_otgan'))

        self.card_portfel.config(text=str(portfel_n))
        self.card_45kun.config(text=str(kun45))
        self.card_tayyor.config(text=str(tayyor))
        self.card_otgan.config(text=str(otgan))
        self.card_otgan.config(fg=ERR if otgan > 0 else STAMP)

        bugungi = db.get_bugungi_harakatlar()
        self.card_bugun_yaratildi.config(text=str(bugungi['yaratildi']))
        self.card_bugun_yuborildi.config(text=str(bugungi['yuborildi']))

        tarmoq_data = db.get_tarmoq_stage3_breakdown(limit=8)
        self._draw_hbar_chart(
            self.viloyat_canvas, tarmoq_data, 'tarmoq', 'jami',
            value_fmt=_fmt_summa_qisqa, color=STAMP
        )

        turi_data = db.get_turi_breakdown(chegara)
        turi_items = [
            {'nomi': 'Jismoniy', 'soni': turi_data['jismoniy']},
            {'nomi': 'Yuridik', 'soni': turi_data['yuridik']},
        ]
        self._draw_hbar_chart(self.turi_canvas, turi_items, 'nomi', 'soni', color=KRAFT)

        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        recent = db.get_xatlar()[:10]
        status_labels = {'tayyor': 'Tayyor', 'yuborildi': '✓ Yuborildi', 'muddati_otgan': "⚠ Muddati o'tgan"}
        for r in recent:
            try:
                sana = datetime.datetime.fromisoformat(r['yaratilgan_sana']).strftime('%d.%m.%Y %H:%M')
            except Exception:
                sana = r['yaratilgan_sana'] or ''
            self.recent_tree.insert('', 'end', values=(
                sana, r['mijoz_nomi'], r['xat_turi'], status_labels.get(r['holat'], r['holat'])
            ))


class PortfelTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Portfel ma'lumotlarini import qilish", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(self, text="IFRS portfel hisobotini (.xlsb) yuklang. Mavjud bo'lsa, eski "
                              "ma'lumotlar almashtiriladi.", style='Sub.TLabel').pack(
            anchor='w', padx=20, pady=(0, 16))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(anchor='w', padx=20)
        ttk.Button(btn_frame, text="📂 .xlsb faylni tanlash va import qilish",
                   style='Accent.TButton', command=self.import_file).pack(side='left')

        self.status_label = ttk.Label(self, text='', style='Sub.TLabel')
        self.status_label.pack(anchor='w', padx=20, pady=10)

        self.progress = ttk.Progressbar(self, mode='determinate', length=400)
        self.progress.pack(anchor='w', padx=20, pady=(0, 10))

        cols = ('anketa', 'mijoz', 'turi', 'dpd', 'jami_qarz')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=18)
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz nomi', 'turi': 'Turi',
                    'dpd': 'DPD (kun)', 'jami_qarz': "Muddati o'tgan qarz"}
        widths = {'anketa': 100, 'mijoz': 350, 'turi': 90, 'dpd': 90, 'jami_qarz': 160}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)

        self.refresh_table()

    def import_file(self):
        filepath = filedialog.askopenfilename(
            title="Portfel faylini tanlang",
            filetypes=[("Excel Binary", "*.xlsb"), ("Barcha fayllar", "*.*")]
        )
        if not filepath:
            return
        self.status_label.config(text="Import qilinmoqda...")
        self.progress['value'] = 0

        def worker():
            try:
                db.clear_portfel()

                def cb(i, total):
                    pct = int(i / max(total, 1) * 100)
                    self.progress['value'] = pct

                result = importer.import_portfel_xlsb(filepath, progress_cb=cb)
                self.progress['value'] = 100
                msg = f"Tayyor! {result['jami_qator']} ta qator import qilindi (varaq: {result['sheet']})."
                if result['topilmagan_ustunlar']:
                    msg += f"\nOgohlantirish: {len(result['topilmagan_ustunlar'])} ta ustun faylda topilmadi."
                self.status_label.config(text=msg)
                self.refresh_table()
                self.app.tab_dashboard.refresh()
            except Exception as e:
                messagebox.showerror("Xato", f"Import vaqtida xato: {e}")
                self.status_label.config(text="Xato yuz berdi.")

        threading.Thread(target=worker, daemon=True).start()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = db.get_conn()
        rows = conn.execute('SELECT * FROM portfel ORDER BY dpd_max DESC LIMIT 500').fetchall()
        conn.close()
        for r in rows:
            self.tree.insert('', 'end', values=(
                r['anketa_raqami'], r['mijoz_nomi'], r['mijoz_turi'], r['dpd_max'],
                f"{r['jami_qarz']:,.0f}".replace(',', ' ') if r['jami_qarz'] else '0'
            ))


class MijozlarTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Mijozlar bazasini import qilish", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(self, text="Jismoniy va yuridik shaxslar ma'lumotini alohida yuklang. "
                              "Ustunlarni o'zingiz moslashtirasiz.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 16))

        btns = ttk.Frame(self)
        btns.pack(anchor='w', padx=20)
        ttk.Button(btns, text="👤 Jismoniy shaxslar faylini import qilish",
                   style='Accent.TButton',
                   command=lambda: self.import_file('jismoniy')).pack(side='left', padx=(0, 10))
        ttk.Button(btns, text="🏢 Yuridik shaxslar faylini import qilish",
                   style='Accent.TButton',
                   command=lambda: self.import_file('yuridik')).pack(side='left')

        self.status_label = ttk.Label(self, text='', style='Sub.TLabel')
        self.status_label.pack(anchor='w', padx=20, pady=14)

        stats = ttk.Frame(self)
        stats.pack(anchor='w', padx=20)
        self.lbl_jis = ttk.Label(stats, text="Jismoniy shaxslar: 0")
        self.lbl_jis.pack(anchor='w', pady=2)
        self.lbl_yur = ttk.Label(stats, text="Yuridik shaxslar: 0")
        self.lbl_yur.pack(anchor='w', pady=2)
        self.refresh_stats()

    def refresh_stats(self):
        conn = db.get_conn()
        jis = conn.execute("SELECT COUNT(*) c FROM mijozlar WHERE turi='jismoniy'").fetchone()['c']
        yur = conn.execute("SELECT COUNT(*) c FROM mijozlar WHERE turi='yuridik'").fetchone()['c']
        conn.close()
        self.lbl_jis.config(text=f"Jismoniy shaxslar: {jis}")
        self.lbl_yur.config(text=f"Yuridik shaxslar: {yur}")

    def import_file(self, turi):
        filepath = filedialog.askopenfilename(
            title="Mijozlar faylini tanlang",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Barcha fayllar", "*.*")]
        )
        if not filepath:
            return
        try:
            cols, preview_df = importer.preview_mijozlar_columns(filepath)
        except Exception as e:
            messagebox.showerror("Xato", f"Fayl o'qilmadi: {e}")
            return

        dialog = ColumnMapDialog(self, cols, preview_df, turi)
        self.wait_window(dialog)
        if not dialog.result:
            return

        self.status_label.config(text="Import qilinmoqda...")

        def worker():
            try:
                result = importer.import_mijozlar_xlsx(filepath, turi, dialog.result)
                self.status_label.config(
                    text=f"Tayyor! {result['import_qilingan']} / {result['jami_qator']} qator import qilindi.")
                self.refresh_stats()
            except Exception as e:
                messagebox.showerror("Xato", f"Import vaqtida xato: {e}")

        threading.Thread(target=worker, daemon=True).start()


class ColumnMapDialog(tk.Toplevel):
    """Excel ustunlarini bazadagi maydonlarga moslashtirish oynasi."""
    FIELDS = [
        ('kalit', "Bog'lovchi ID (STIR / PINFL / Уникал) *", True),
        ('ism', "Ism-familiya / Tashkilot nomi *", True),
        ('manzil', "Manzil", False),
        ('telefon', "Telefon", False),
        ('hujjat_raqami', "Passport / STIR raqami", False),
        ('rahbar_ism', "Rahbar F.I.Sh (yuridik shaxs uchun)", False),
    ]

    def __init__(self, parent, columns, preview_df, turi):
        super().__init__(parent)
        self.title(f"Ustunlarni moslashtirish — {turi}")
        self.geometry("560x480")
        self.configure(bg=BG)
        self.result = None
        self.columns = [''] + list(columns)

        ttk.Label(self, text="Har bir maydon uchun mos Excel ustunini tanlang:",
                  style='Header.TLabel').pack(anchor='w', padx=16, pady=(16, 10))

        self.vars = {}
        form = ttk.Frame(self)
        form.pack(fill='x', padx=16)
        for field, label, required in self.FIELDS:
            row = ttk.Frame(form)
            row.pack(fill='x', pady=4)
            ttk.Label(row, text=label, width=38).pack(side='left')
            var = tk.StringVar(value='')
            combo = ttk.Combobox(row, textvariable=var, values=self.columns, state='readonly', width=28)
            combo.pack(side='left')
            self.vars[field] = var

        btns = ttk.Frame(self)
        btns.pack(fill='x', padx=16, pady=16, side='bottom')
        ttk.Button(btns, text="Bekor qilish", command=self.destroy).pack(side='right', padx=4)
        ttk.Button(btns, text="Import qilish", style='Accent.TButton',
                   command=self.on_confirm).pack(side='right', padx=4)

        self.transient(parent)
        self.grab_set()

    def on_confirm(self):
        mapping = {f: v.get() for f, v in self.vars.items() if v.get()}
        if not mapping.get('kalit') or not mapping.get('ism'):
            messagebox.showerror("Xato", "Bog'lovchi ID va Ism ustunlari majburiy.")
            return
        self.result = mapping
        self.destroy()


class TahlilTab(ttk.Frame):
    PAKET_OPTIONS = ['10', '30', '50', '100', 'Barchasi']

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Tahlil va Talabnoma", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        self.sub_label = ttk.Label(self, text='', style='Sub.TLabel')
        self.sub_label.pack(anchor='w', padx=20, pady=(0, 10))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=20)
        ttk.Button(toolbar, text="🔍 Tahlil qilish (yangilash)",
                   command=self.refresh_stats).pack(side='left')

        self.only_new_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="Faqat xat yaratilmagan / muddati o'tganlar",
                         variable=self.only_new_var,
                         command=self.refresh_stats).pack(side='left', padx=14)

        paket_frame = ttk.Frame(self)
        paket_frame.pack(fill='x', padx=20, pady=(10, 6))
        ttk.Label(paket_frame, text="Paket hajmi:").pack(side='left')
        self.paket_var = tk.StringVar(value='30')
        ttk.Combobox(paket_frame, textvariable=self.paket_var, values=self.PAKET_OPTIONS,
                     state='readonly', width=10).pack(side='left', padx=8)
        ttk.Button(paket_frame, text="① Birinchi paketni belgilash",
                   command=self.select_paket).pack(side='left', padx=6)
        ttk.Button(paket_frame, text="📊 Excel'ga eksport qilish (tanlanganlar)",
                   command=self.export_excel).pack(side='left', padx=6)
        ttk.Button(paket_frame, text="📥 Tahrirlangan Excel'ni yuklash",
                   command=self.import_excel_updates).pack(side='left', padx=6)

        gen_frame = ttk.Frame(self)
        gen_frame.pack(fill='x', padx=20, pady=(0, 6))
        ttk.Button(gen_frame, text="✉ Tanlanganlar uchun xat yaratish (ommaviy)",
                   style='Accent.TButton', command=self.generate_bulk).pack(side='left')

        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=20, pady=(14, 6))
        ttk.Label(search_frame, text="Bitta mijozga: Anketa raqami").pack(side='left')
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side='left', padx=8)
        ttk.Button(search_frame, text="Qidirish", command=self.search_single).pack(side='left')
        ttk.Button(search_frame, text="✉ Xatni yuborish (shu mijozga)",
                   command=self.generate_single).pack(side='left', padx=8)

        cols = ('anketa', 'mijoz', 'turi', 'dpd', 'jami_qarz', 'mijoz_topildi', 'holat')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=14, selectmode='extended')
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz nomi', 'turi': 'Turi',
                    'dpd': 'DPD (kun)', 'jami_qarz': "Muddati o'tgan qarz",
                    'mijoz_topildi': "Bazada mavjud?", 'holat': 'Oldingi xat holati'}
        widths = {'anketa': 90, 'mijoz': 280, 'turi': 80, 'dpd': 80, 'jami_qarz': 140,
                  'mijoz_topildi': 100, 'holat': 130}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)
        ttk.Label(self, text="Ctrl / Shift bosib bir nechta mijozni tanlashingiz mumkin.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 10))

        self._rows_cache = []
        self.refresh_stats()

    def refresh_stats(self):
        chegara = int(db.get_setting('dpd_chegara_kun', 45))
        rows = db.get_portfel_45_kun(chegara)
        status_map = db.get_latest_xat_status_by_portfel()

        if self.only_new_var.get():
            rows = [r for r in rows if status_map.get(r['id']) not in ('tayyor', 'yuborildi')]

        self._rows_cache = rows
        self._status_map = status_map
        self.sub_label.config(
            text=f"{chegara}+ kun muddati o'tgan mijozlar: {len(rows)} ta "
                 f"(jami tahlil qilingan {len(db.get_portfel_45_kun(chegara))} tadan)")
        self._fill_tree(rows)

    def _fill_tree(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        status_labels = {'tayyor': 'Tayyor', 'yuborildi': 'Yuborilgan',
                          'muddati_otgan': "⚠ Muddati o'tgan"}
        for r in rows:
            turi, mijoz = resolve_mijoz(r)
            holat = status_labels.get(self._status_map.get(r['id']), '—') if hasattr(self, '_status_map') else '—'
            self.tree.insert('', 'end', iid=str(r['id']), values=(
                r['anketa_raqami'], r['mijoz_nomi'], turi, r['dpd_max'],
                f"{r['jami_qarz']:,.0f}".replace(',', ' ') if r['jami_qarz'] else '0',
                "Ha" if mijoz else "Yo'q", holat
            ))

    def select_paket(self):
        paket = self.paket_var.get()
        all_items = self.tree.get_children()
        if not all_items:
            messagebox.showinfo("Diqqat", "Ro'yxat bo'sh.")
            return
        n = len(all_items) if paket == 'Barchasi' else int(paket)
        to_select = all_items[:n]
        self.tree.selection_set(to_select)
        if to_select:
            self.tree.see(to_select[0])
        messagebox.showinfo("Tanlandi", f"{len(to_select)} ta mijoz tanlandi (paket hajmi: {paket}).")

    def _selected_rows(self):
        selected = self.tree.selection()
        if not selected:
            return []
        ids = [int(i) for i in selected]
        return [r for r in self._rows_cache if r['id'] in ids]

    def _rows_for_excel(self, portfel_rows):
        out = []
        for r in portfel_rows:
            turi, mijoz = resolve_mijoz(r)
            xat_turi = 'Talabnoma' if turi == 'yuridik' else 'Ogohlantirish'
            out.append({
                'anketa_raqami': r.get('anketa_raqami', ''),
                'mijoz_nomi': mijoz['ism'] if mijoz else r.get('mijoz_nomi', ''),
                'turi': turi,
                'manzil': mijoz['manzil'] if mijoz else '',
                'telefon': mijoz['telefon'] if mijoz else '',
                'dpd_max': r.get('dpd_max', 0),
                'jami_qarz': r.get('jami_qarz', 0),
                'xat_turi': xat_turi,
            })
        return out

    def export_excel(self):
        rows = self._selected_rows()
        if not rows:
            messagebox.showinfo("Diqqat", "Avval ro'yxatdan mijozlarni tanlang "
                                           "('Birinchi paketni belgilash' yordam beradi).")
            return
        out_path = filedialog.asksaveasfilename(
            title="Excel faylni saqlash", defaultextension=".xlsx",
            initialfile="talabnoma_royxati.xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not out_path:
            return
        try:
            excel_rows = self._rows_for_excel(rows)
            importer.export_tahlil_excel(excel_rows, out_path)
            messagebox.showinfo(
                "Tayyor",
                f"{len(excel_rows)} ta qator eksport qilindi:\n{out_path}\n\n"
                "Manzil / Telefon ustunlarini tahrirlab, so'ng "
                "'Tahrirlangan Excel'ni yuklash' orqali qaytaring."
            )
            webbrowser.open(out_path)
        except Exception as e:
            messagebox.showerror("Xato", str(e))

    def import_excel_updates(self):
        filepath = filedialog.askopenfilename(
            title="Tahrirlangan Excel faylni tanlang",
            filetypes=[("Excel", "*.xlsx *.xls")]
        )
        if not filepath:
            return
        try:
            result = importer.import_manzil_updates(filepath)
            msg = f"{result['yangilandi']} ta mijoz manzili/ma'lumoti yangilandi."
            if result['otkazib_yuborildi']:
                msg += f"\n{result['otkazib_yuborildi']} ta qator o'tkazib yuborildi " \
                       f"(anketa raqami portfelda topilmadi)."
            messagebox.showinfo("Tayyor", msg)
            self.refresh_stats()
        except Exception as e:
            messagebox.showerror("Xato", str(e))

    def search_single(self):
        anketa = self.search_var.get().strip()
        if not anketa:
            return
        rows = db.get_portfel_by_anketa(anketa)
        self._status_map = db.get_latest_xat_status_by_portfel()
        self._rows_cache = rows
        self._fill_tree(rows)

    def _generate_for_row(self, portfel_row):
        turi, mijoz = resolve_mijoz(portfel_row)
        xat_turi = 'Talabnoma' if turi == 'yuridik' else 'Ogohlantirish'

        mijoz_ism = mijoz['ism'] if mijoz else portfel_row.get('mijoz_nomi', '')
        mijoz_manzil = mijoz['manzil'] if mijoz else ''
        rahbar_ism = mijoz.get('rahbar_ism') if mijoz else ''

        settings = db.get_all_settings()
        anketa = portfel_row.get('anketa_raqami', 'noma_lum')
        fname = f"{xat_turi}_{letters.safe_filename(anketa)}_{letters.safe_filename(mijoz_ism)}.docx"
        out_path = os.path.join(XATLAR_DIR, fname)

        letters.generate_letter(
            output_path=out_path,
            xat_turi=xat_turi,
            mijoz_ism=mijoz_ism,
            mijoz_manzil=mijoz_manzil,
            portfel_row=portfel_row,
            settings=settings,
            anketa_raqami=anketa,
            rahbar_ism=rahbar_ism,
        )
        muddat_kun = int(settings.get('eslatma_muddati_kun', 3))
        db.create_xat(
            portfel_id=portfel_row['id'],
            anketa_raqami=anketa,
            mijoz_nomi=mijoz_ism,
            mijoz_turi=turi,
            xat_turi=xat_turi,
            fayl_yoli=out_path,
            muddat_kun=muddat_kun,
        )
        return out_path

    def generate_bulk(self):
        rows = self._selected_rows()
        if not rows:
            messagebox.showinfo("Diqqat", "Iltimos, kamida bitta mijozni tanlang "
                                           "('Birinchi paketni belgilash' yordam beradi).")
            return

        os.makedirs(XATLAR_DIR, exist_ok=True)
        created = []
        errors = []
        for r in rows:
            try:
                path = self._generate_for_row(r)
                created.append(path)
            except Exception as e:
                errors.append(f"{r.get('anketa_raqami')}: {e}")

        msg = f"{len(created)} ta xat yaratildi.\nJoylashuv: {XATLAR_DIR}"
        if errors:
            msg += f"\n\n{len(errors)} ta xatoda:\n" + '\n'.join(errors[:5])
        messagebox.showinfo("Tayyor", msg)
        webbrowser.open(XATLAR_DIR)
        self.app.tab_dashboard.refresh()
        self.app.tab_xatlar.refresh()
        self.refresh_stats()

    def generate_single(self):
        anketa = self.search_var.get().strip()
        if not anketa:
            messagebox.showinfo("Diqqat", "Anketa raqamini kiriting.")
            return
        rows = db.get_portfel_by_anketa(anketa)
        if not rows:
            messagebox.showinfo("Topilmadi", "Bu anketa raqami bo'yicha ma'lumot topilmadi.")
            return
        row = rows[0]
        os.makedirs(XATLAR_DIR, exist_ok=True)
        try:
            path = self._generate_for_row(row)
            messagebox.showinfo("Tayyor", f"Xat yaratildi:\n{path}")
            webbrowser.open(path)
        except Exception as e:
            messagebox.showerror("Xato", str(e))
        self.app.tab_dashboard.refresh()
        self.app.tab_xatlar.refresh()


class XatlarTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Xatlar holati", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(self, text="Tayyorlangan xat 3 kun ichida yuborilmasa, 'muddati o'tgan' deb belgilanadi.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 14))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=20)
        ttk.Button(toolbar, text="🔄 Yangilash", command=self.refresh).pack(side='left')
        ttk.Button(toolbar, text="✓ Yuborildi deb belgilash", style='Accent.TButton',
                   command=self.mark_sent).pack(side='left', padx=10)
        ttk.Button(toolbar, text="📂 Faylni ochish", command=self.open_file).pack(side='left')

        cols = ('anketa', 'mijoz', 'turi', 'xat_turi', 'yaratilgan', 'muddat', 'holat')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=18)
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz', 'turi': 'Turi', 'xat_turi': 'Xat turi',
                    'yaratilgan': 'Yaratilgan', 'muddat': 'Yuborish muddati', 'holat': 'Holat'}
        widths = {'anketa': 90, 'mijoz': 260, 'turi': 80, 'xat_turi': 100,
                  'yaratilgan': 130, 'muddat': 130, 'holat': 120}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.tag_configure('otgan', foreground=ERR)
        self.tree.tag_configure('yuborildi', foreground=STAMP)
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)

        self._id_map = {}
        self.refresh()

    def refresh(self):
        db.update_muddati_otganlar()
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = db.get_xatlar()
        for r in rows:
            tag = ''
            holat_label = r['holat']
            if r['holat'] == 'muddati_otgan':
                tag = 'otgan'
                holat_label = "⚠ Muddati o'tgan"
            elif r['holat'] == 'yuborildi':
                tag = 'yuborildi'
                holat_label = "✓ Yuborildi"
            else:
                holat_label = "Tayyor"

            def fmt_date(s):
                try:
                    return datetime.datetime.fromisoformat(s).strftime('%d.%m.%Y')
                except Exception:
                    return s or ''

            iid = str(r['id'])
            self.tree.insert('', 'end', iid=iid, values=(
                r['anketa_raqami'], r['mijoz_nomi'], r['mijoz_turi'], r['xat_turi'],
                fmt_date(r['yaratilgan_sana']), fmt_date(r['muddat_sana']), holat_label
            ), tags=(tag,))
            self._id_map[iid] = r

        self.app.tab_dashboard.refresh()

    def mark_sent(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Diqqat", "Xatni tanlang.")
            return
        for iid in selected:
            db.mark_xat_yuborildi(int(iid))
        self.refresh()

    def open_file(self):
        selected = self.tree.selection()
        if not selected:
            return
        r = self._id_map.get(selected[0])
        if r and r['fayl_yoli'] and os.path.exists(r['fayl_yoli']):
            webbrowser.open(r['fayl_yoli'])
        else:
            messagebox.showinfo("Topilmadi", "Fayl topilmadi.")


class SozlamalarTab(ttk.Frame):
    FIELDS = [
        ('bank_nomi', 'Bank nomi (to‘liq)'),
        ('bank_qisqa_nomi', 'Bank nomi (qisqa)'),
        ('bank_manzil', 'Bank manzili'),
        ('bank_email', 'Bank email'),
        ('bank_sayt', 'Bank sayti'),
        ('bank_tel', 'Bank markaziy tel'),
        ('bank_mobil_ilova', 'Mobil ilova nomi'),
        ('bank_kodi', 'Bank kodi'),
        ('aloqa_markazi_tel', 'Aloqa markazi tel'),
        ('filial_nomi', 'Filial nomi'),
        ('filial_tel', 'Filial telefon'),
        ('rahbar_ism', 'Filial rahbari F.I.Sh (standart)'),
        ('tolov_muddati_kun', "To'lov uchun beriladigan muddat (bank ish kuni)"),
        ('eslatma_muddati_kun', "Xat yuborish uchun ichki muddat (kun)"),
        ('dpd_chegara_kun', "Tahlil uchun DPD chegarasi (kun)"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Sozlamalar", style='Header.TLabel').pack(anchor='w', padx=20, pady=(20, 14))

        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill='both', expand=True, padx=20)

        self.vars = {}
        current = db.get_all_settings()
        for key, label in self.FIELDS:
            row = ttk.Frame(canvas_frame)
            row.pack(fill='x', pady=5)
            ttk.Label(row, text=label, width=42).pack(side='left')
            var = tk.StringVar(value=current.get(key, ''))
            ttk.Entry(row, textvariable=var, width=50).pack(side='left')
            self.vars[key] = var

        ttk.Button(self, text="💾 Saqlash", style='Accent.TButton',
                   command=self.save).pack(anchor='w', padx=20, pady=16)

        # ---- Xat shabloni ----
        sep = ttk.Frame(self, height=2)
        sep.pack(fill='x', padx=20, pady=(4, 14))
        ttk.Label(self, text="Xat shabloni (Word)", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(0, 4))
        ttk.Label(self, text="Yangi shablon yuklasangiz, hali yuborilmagan ('Tayyor' holatidagi) "
                              "xatlar avtomatik shu yangi shablon bilan qayta tayyorlanadi.",
                  style='Sub.TLabel', wraplength=800, justify='left').pack(
            anchor='w', padx=20, pady=(0, 10))

        tpl_frame = ttk.Frame(self)
        tpl_frame.pack(anchor='w', padx=20)
        ttk.Button(tpl_frame, text="📄 Joriy shablonni ochish",
                   command=self.open_template).pack(side='left')
        ttk.Button(tpl_frame, text="📤 Yangi shablon yuklash (.docx)", style='Accent.TButton',
                   command=self.upload_template).pack(side='left', padx=10)

    def save(self):
        for key, var in self.vars.items():
            db.set_setting(key, var.get())
        messagebox.showinfo("Saqlandi", "Sozlamalar saqlandi.")

    def open_template(self):
        if os.path.exists(letters.TEMPLATE_PATH):
            webbrowser.open(letters.TEMPLATE_PATH)
        else:
            messagebox.showerror("Topilmadi", "Shablon fayli topilmadi.")

    def upload_template(self):
        filepath = filedialog.askopenfilename(
            title="Yangi shablon faylini tanlang",
            filetypes=[("Word hujjati", "*.docx")]
        )
        if not filepath:
            return
        try:
            import shutil
            os.makedirs(os.path.dirname(letters.TEMPLATE_PATH), exist_ok=True)
            if os.path.exists(letters.TEMPLATE_PATH):
                backup = letters.TEMPLATE_PATH + '.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.bak'
                shutil.copy2(letters.TEMPLATE_PATH, backup)
            shutil.copy2(filepath, letters.TEMPLATE_PATH)
        except Exception as e:
            messagebox.showerror("Xato", f"Shablonni saqlashda xato: {e}")
            return

        javob = messagebox.askyesno(
            "Qayta tayyorlash",
            "Shablon yangilandi.\n\nHali yuborilmagan ('Tayyor' holatidagi) xatlarni "
            "yangi shablon bilan hozir qayta tayyorlaymi?"
        )
        if javob:
            self._regenerate_pending()

    def _regenerate_pending(self):
        pending = db.get_xatlar('tayyor')
        settings = db.get_all_settings()
        updated = 0
        errors = []
        for xat in pending:
            try:
                prow = db.get_portfel_by_id(xat['portfel_id'])
                if not prow:
                    continue
                turi, mijoz = util.resolve_mijoz(prow)
                mijoz_ism = mijoz['ism'] if mijoz else prow.get('mijoz_nomi', '')
                mijoz_manzil = mijoz['manzil'] if mijoz else ''
                rahbar_ism = mijoz.get('rahbar_ism') if mijoz else ''
                letters.generate_letter(
                    output_path=xat['fayl_yoli'],
                    xat_turi=xat['xat_turi'],
                    mijoz_ism=mijoz_ism,
                    mijoz_manzil=mijoz_manzil,
                    portfel_row=prow,
                    settings=settings,
                    anketa_raqami=xat['anketa_raqami'],
                    rahbar_ism=rahbar_ism,
                )
                updated += 1
            except Exception as e:
                errors.append(f"{xat.get('anketa_raqami')}: {e}")

        msg = f"{updated} ta xat yangi shablon bilan qayta tayyorlandi."
        if errors:
            msg += f"\n\n{len(errors)} ta xatoda:\n" + '\n'.join(errors[:5])
        messagebox.showinfo("Tayyor", msg)


def main():
    os.makedirs(XATLAR_DIR, exist_ok=True)
    db.init_db()
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
