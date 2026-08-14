# Qarz Nazorat va Talabnoma Tizimi

Bitta kompyuterda, internetsiz (oflayn) ishlaydigan dastur. Portfelni tahlil
qiladi, 45 kundan ko'p muddati o'tgan mijozlarni ajratadi va ularga
Ogohlantirish xati (jismoniy shaxs) / Talabnoma (yuridik shaxs) tayyorlaydi.

## 1. Kompyuterda ishga tushirish (test uchun, .exe siz)

Kompyuteringizda **Python 3.10+** o'rnatilgan bo'lishi kerak
(https://python.org — o'rnatishda "Add Python to PATH" belgisini bosing).

```
pip install -r requirements.txt
python main.py
```

Dastur ochiladi. Birinchi marta ishga tushganda `qarz_nazorat.db` fayli
avtomatik yaratiladi — bu sizning bazangiz, uni o'chirmang.

## 2. .EXE qilib yig'ish (Windows'da)

1. Ushbu papkani (`qarz_nazorat`) Windows kompyuteringizga ko'chiring.
2. Python o'rnatilganini tekshiring (`cmd` da `python --version`).
3. Papka ichida `build_exe.bat` faylini ikki marta bosing.
4. Bir necha daqiqadan so'ng `dist\QarzNazorat.exe` fayli tayyor bo'ladi.
5. Shu `.exe` faylni istalgan joyga (masalan Desktop'ga) ko'chirib, ishlatishingiz mumkin — endi Python ham, internet ham kerak emas.

**Muhim:** `.exe` ishga tushganda, u joylashgan papkada `qarz_nazorat.db`
va `yaratilgan_xatlar` papkasi avtomatik hosil bo'ladi — shu papkani
zaxira nusxalashni unutmang.

## 3. Ishlatish tartibi

1. **Portfel** bo'limi — IFRS portfel hisobotini (`.xlsb`) yuklang.
2. **Mijozlar bazasi** — jismoniy va yuridik shaxslar faylini alohida
   yuklaysiz. Har birida ustunlarni (Ism, Manzil, Telefon, Bog'lovchi ID)
   o'zingiz moslashtirasiz — shuning uchun fayl formati istalgancha bo'lishi
   mumkin.
   - **"Bog'lovchi ID"** — bu portfeldagi СТИР, ПИНФЛ yoki Уникал
     raqamlaridan biriga mos keladigan ustun bo'lishi kerak, aks holda
     dastur mijozni portfel bilan bog'lay olmaydi.
3. **Tahlil / Talabnoma** — "Tahlil qilish" tugmasi 45+ kun (sozlamalarda
   o'zgartirish mumkin) muddati o'tgan mijozlarni ro'yxat qilib beradi.
   Ro'yxatda, standart holatda, faqat hali xati yaratilmagan yoki
   muddati o'tib ketgan mijozlar ko'rinadi — xat yaratilganlar avtomatik
   chiqib ketadi (checkbox orqali barchasini ko'rish mumkin).

   **Paketlarga bo'lib ishlash** (masalan 150 tani 30 tadan 5 paket qilib):
   - "Paket hajmi" (10/30/50/100/Barchasi) tanlang
   - "① Birinchi paketni belgilash" — ro'yxatdagi birinchi N tani avtomatik
     belgilaydi (yoki Ctrl/Shift bosib o'zingiz ham tanlashingiz mumkin)

   **Manzilni tekshirish/to'g'irlash** (xat yaratishdan oldin):
   - "📊 Excel'ga eksport qilish" — tanlangan mijozlar ro'yxatini (Ism,
     Manzil, Telefon va h.k.) Excel qilib beradi
   - Excel'da kerakli manzil/telefonni to'g'irlaysiz
   - "📥 Tahrirlangan Excel'ni yuklash" — tuzatilgan faylni qaytarib
     yuklaysiz, dastur o'zgargan manzilni **mijozlar bazasiga saqlab qoladi**
     (keyingi safar ham eslab qoladi)
   - So'ng "✉ Tanlanganlar uchun xat yaratish (ommaviy)" bosasiz — endi
     to'g'irlangan manzil bilan tayyorlanadi

   Yoki anketa raqami bo'yicha qidirib, bitta mijozga alohida xat
   yaratishingiz mumkin. Xatlar `yaratilgan_xatlar` papkasiga saqlanadi.
4. **Xatlar holati** — yaratilgan barcha xatlar va ularning holati
   (Tayyor / Yuborildi / Muddati o'tgan) shu yerda ko'rinadi. Xat jo'natilgach
   "Yuborildi deb belgilash" tugmasini bosing. Agar xodim 3 kun ichida
   belgilamasa, dastur ochilganda avtomatik ogohlantirish chiqadi.
5. **Sozlamalar** — bank nomi, filial nomi, telefon, 45 kunlik chegara va
   3 kunlik ichki muddatni shu yerdan o'zgartirasiz.

   **Shablonni yangilash** — xat shabloni (Word) o'zgarsa, shu yerdan yangi
   `.docx` faylni yuklaysiz. Yuklagach, hali yuborilmagan ("Tayyor"
   holatidagi) barcha xatlar avtomatik ravishda yangi shablon bilan
   qayta tayyorlanadi (savol chiqadi — "Ha" desangiz).

## 4. Hozircha ochiq qolgan masalalar

- **Asosiy/foiz/jarima taqsimoti**: hozirgi portfel faylida qarzning
  asosiy qarz / foiz / jarima bo'yicha alohida taqsimoti aniq ustun sifatida
  yo'q edi — vaqtincha jami summa "asosiy qarz" sifatida ko'rsatilmoqda.
  Aniq ustunlarni bilsangiz, `importer.py` faylidagi `PORTFEL_COLMAP` hamda
  `asosiy_qarz`/`foiz_qarz`/`jarima` hisoblanadigan joyni yangilab beraman.
- **Mijozlar bazasi**: hozircha ulanmagan — siz ma'lumotni tozalab
  bergach, "Mijozlar bazasi" bo'limi orqali import qilib, ustunlarni
  moslashtirasiz.
- **Talabnoma matni**: hozircha Ogohlantirish xatiga o'xshab, faqat sarlavha
  "ТАЛАБНОМА" deb almashtirilgan. Matn boshqacha bo'lishi kerak bo'lsa,
  ayting — alohida shablon tuzib beraman.

## 5. Fayl tuzilishi

```
qarz_nazorat/
├── main.py              # Dastur oynasi (GUI)
├── database.py          # SQLite baza
├── importer.py          # Excel/XLSB import
├── letters.py           # Word xat generatsiyasi
├── templates/
│   └── xat_shablon.docx # Xat shabloni
├── requirements.txt
├── build_exe.bat        # .exe yig'ish uchun
└── README.md
```
