# DUS Koçluk Sistemi — Proje Planlama Dokümanı

**Proje:** Diş Hekimliği Uzmanlık Sınavı (DUS) Hazırlık Koçluk Platformu
**Platform:** Telegram Bot + Web Panel
**Tarih:** Mayıs 2026

---

## 1. Sistem Özeti

Diş hekimliği uzmanlık sınavına (DUS) hazırlanan öğrenciler için kişiselleştirilmiş çalışma programı oluşturan, günlük takip yapan ve Telegram üzerinden hatırlatma + dönüt toplayan bir koçluk sistemi.

**İki ana bileşen:**

- **Telegram Bot** — Öğrenci ile günlük etkileşim (hatırlatma, dönüt toplama, motivasyon)
- **Web Panel** — Yönetici/koç paneli + öğrenci dashboard (istatistik, takvim, analiz)

---

## 2. Kullanıcı Akışı (User Flow)

### 2.1 Onboarding (İlk Kayıt)

Öğrenci Telegram botu başlatır → Bot sırayla şu verileri toplar:

**Adım 1 — Kişisel Bilgiler**
- Ad Soyad
- İletişim (telefon / e-posta)
- Sınav hedef tarihi (hangi DUS dönemi)

**Adım 2 — Çalışma Durumu Sorgulaması**
- "Aktif olarak çalışıyor musunuz?" (Evet / Hayır)
- Evetse → Mesai saatleri (başlangıç–bitiş)
- Nöbet var mı? (Evet / Hayır, sıklık)

**Adım 3 — Haftalık Müsaitlik Tablosu**

Bot, her gün için ayrı ayrı sorar:

| Gün | Soru |
|-----|------|
| Pazartesi | "Pazartesi günleri kaç saat ders çalışabilirsiniz?" |
| Salı | "Salı günleri kaç saat ders çalışabilirsiniz?" |
| Çarşamba | "Çarşamba günleri kaç saat ders çalışabilirsiniz?" |
| Perşembe | "Perşembe günleri kaç saat ders çalışabilirsiniz?" |
| Cuma | "Cuma günleri kaç saat ders çalışabilirsiniz?" |
| Cumartesi | "Cumartesi günleri kaç saat ders çalışabilirsiniz?" |
| Pazar | "Pazar günleri kaç saat ders çalışabilirsiniz?" |

Bot otomatik hesaplar:
- Haftalık toplam çalışma saati
- Hafta içi ortalaması
- Hafta sonu ortalaması

**Adım 4 — Mevcut Hazırlık Durumu**
- "Daha önce DUS'a çalıştınız mı?" (Evet / Hayır)
- Evetse → "Hangi kaynakları kullandınız?"
- "Eksik hissettiğiniz konular var mı?" (serbest metin veya konu listesinden seçim)
- "Daha önce deneme sınavına girdiniz mi?" → Son deneme puanı

**Adım 5 — Hedef Belirleme**
- "Hedefiniz nedir?" (Serbest alan veya seçenekler)
  - İlk 100'e girmek
  - İlk 500'e girmek
  - Sadece kazanmak
  - Belirli bir branşı kazanmak (hangi branş?)
- "Günlük çalışma tercihiniz?" (Sabah / Öğlen / Akşam / Esnek)

---

### 2.2 Öğrenci Profil Sınıflandırması

Sistem toplanan verilere göre öğrenciyi otomatik sınıflandırır:

| Profil | Haftalık Saat | Çalışma Durumu | Program Yoğunluğu |
|--------|---------------|----------------|-------------------|
| **Yoğun** | 40+ saat | Çalışmıyor, tam zamanlı hazırlık | Maksimum yoğunluk |
| **Orta** | 20–40 saat | Yarı zamanlı veya esnek çalışan | Dengeli program |
| **Sınırlı** | 10–20 saat | Tam zamanlı çalışan | Verimlilik odaklı |
| **Minimal** | <10 saat | Yoğun mesai + nöbet | Öncelikli konulara odak |

---

## 3. DUS Konu Yapısı ve Soru Dağılımı

### 3.1 Ana Dersler

> **NOT:** Aşağıdaki tablo ÖRNEK yapıdır. Gerçek soru dağılımı, konu ağırlıkları ve ders başına önerilen çalışma süreleri Hasan tarafından doldurulacaktır.

| # | Ders Adı | Ortalama Soru Sayısı | Ağırlık (%) | Tahmini Çalışma Süresi (saat) |
|---|----------|---------------------|-------------|-------------------------------|
| 1 | Periodontoloji | — | — | — |
| 2 | Oral Diagnoz ve Radyoloji | — | — | — |
| 3 | Ağız, Diş ve Çene Cerrahisi | — | — | — |
| 4 | Ortodonti | — | — | — |
| 5 | Protetik Diş Tedavisi | — | — | — |
| 6 | Endodonti | — | — | — |
| 7 | Restoratif Diş Tedavisi | — | — | — |
| 8 | Pedodonti | — | — | — |
| 9 | Oral Patoloji | — | — | — |
| 10 | Farmakoloji | — | — | — |
| 11 | Temel Tıp Bilimleri | — | — | — |
| — | **TOPLAM** | **~200** | **100%** | **—** |

### 3.2 Konu Detay Şablonu (Her Ders İçin)

```
Ders: [Ders Adı]
├── Konu 1: [Konu adı]
│   ├── Ortalama soru sayısı: X
│   ├── Zorluk seviyesi: Kolay / Orta / Zor
│   ├── Önerilen çalışma süresi: X saat
│   └── Öncelik: Yüksek / Orta / Düşük
├── Konu 2: [Konu adı]
│   ├── ...
```

> Bu yapıyı doldurmak için Hasan'dan ders-konu-soru dağılımı verisi alınacak.

---

## 4. Akıllı Program Oluşturma Motoru

### 4.1 Program Oluşturma Algoritması

**Girdiler:**
1. Öğrencinin haftalık müsaitlik tablosu (gün × saat)
2. Sınava kalan gün sayısı
3. Ders/konu bazlı soru ağırlıkları
4. Ders/konu bazlı önerilen çalışma süreleri
5. Öğrencinin mevcut bilgi seviyesi (eksik konular)
6. Hedef profili (yoğun / orta / sınırlı / minimal)

**Hesaplama Mantığı:**

```
toplam_mevcut_saat = haftalık_saat × kalan_hafta_sayısı
tekrar_faktörü = 1.3  (her konu için %30 tekrar süresi eklenir)
gerekli_toplam_saat = Σ(ders_çalışma_süresi × tekrar_faktörü)

eğer toplam_mevcut_saat >= gerekli_toplam_saat:
    → Tüm konulara tam süre ayrılır + ekstra tekrar zamanı
eğer toplam_mevcut_saat < gerekli_toplam_saat:
    → Önceliklendirme devreye girer:
      1. Soru ağırlığı yüksek dersler önce
      2. Öğrencinin eksik konuları önce
      3. Zorluk seviyesine göre süre ayarı
      4. Düşük ağırlıklı konulara minimum süre
```

### 4.2 Günlük Program Yapısı

Her gün için oluşturulan program şablonu:

```
📅 [Tarih] — [Gün adı]
⏰ Toplam hedef: X saat

🔹 Oturum 1 (09:00–10:30) — 1.5 saat
   📚 Ders: Periodontoloji
   📖 Konu: Periodontal Hastalıkların Sınıflandırılması
   🎯 Hedef: Yeni sınıflandırma sistemini öğren

🔹 Oturum 2 (11:00–12:30) — 1.5 saat
   📚 Ders: Endodonti
   📖 Konu: Kök Kanal Morfolojisi
   🎯 Hedef: Üst çene dişleri kanal anatomisi

☕ Mola (12:30–14:00)

🔹 Oturum 3 (14:00–15:30) — 1.5 saat
   📚 Ders: Periodontoloji (Tekrar)
   📖 Konu: Dün çalışılan konunun tekrarı
   🎯 Hedef: Soru çözümü + özet notlar

📊 Gün sonu hedef: 4.5 saat
```

### 4.3 Spaced Repetition (Aralıklı Tekrar) Entegrasyonu

Sistem, konuları şu tekrar döngüsüne yerleştirir:

| Tekrar # | Zamanlama | Yöntem |
|----------|-----------|--------|
| 1. Tekrar | Ertesi gün | Özet okuma (15 dk) |
| 2. Tekrar | 3 gün sonra | Soru çözümü (30 dk) |
| 3. Tekrar | 1 hafta sonra | Mini test (20 dk) |
| 4. Tekrar | 2 hafta sonra | Karışık soru seti |
| 5. Tekrar | 1 ay sonra | Deneme sınavı içinde |

---

## 5. Telegram Bot Akışları

### 5.1 Günlük Hatırlatma Döngüsü

```
[Sabah — çalışma saati başlangıcından 15 dk önce]
Bot → "Günaydın! 🌅 Bugünkü programın hazır:
       📚 Periodontoloji — Periodontal Tedavi (1.5 saat)
       📚 Endodonti — Irrigasyon Solüsyonları (1.5 saat)
       📚 Tekrar — Dünkü konular (1 saat)
       ⏰ Toplam hedef: 4 saat
       Haydi başlayalım! 💪"

[Her oturum başlangıcında]
Bot → "⏰ Oturum başlama zamanı!
       📚 Endodonti — Irrigasyon Solüsyonları
       ⏱ Süre: 1.5 saat
       Başladın mı? [Evet ✅] [15 dk ertele ⏳] [Bugün yapamıyorum ❌]"

[Oturum süresi dolduğunda]
Bot → "⏰ Oturum süresi doldu!
       📚 Endodonti — Irrigasyon Solüsyonları
       Tamamladın mı? [Evet ✅] [Yarım kaldı 🔄] [Yapamadım ❌]"
```

### 5.2 Gün Sonu Dönüt Toplama

```
[Günün son çalışma saatinden 30 dk sonra]
Bot → "📊 Gün Sonu Raporu Zamanı!
       Bugün programdaki konuları değerlendirelim:"

Bot → "1️⃣ Periodontoloji — Periodontal Tedavi
       Ne kadar çalıştın?
       [0 dk] [30 dk] [1 saat] [1.5 saat] [2+ saat]"

Bot → "Konuyu nasıl buldun?
       [Kolaydı ✅] [Orta 🔶] [Zorlandım 🔴] [Hiç anlamadım ⛔]"

Bot → "2️⃣ Endodonti — Irrigasyon Solüsyonları
       Ne kadar çalıştın?
       [0 dk] [30 dk] [1 saat] [1.5 saat] [2+ saat]"

[Tüm konular sorulduktan sonra]
Bot → "📝 Bugün programda olmayan ek bir konu çalıştın mı?
       [Hayır] [Evet — hangisi?]"

Bot → "💬 Bugün hakkında eklemek istediğin bir not var mı?
       (serbest metin veya [Yok])"

Bot → "✅ Rapor kaydedildi! Bugün X/Y saatlik hedefinizin Z saatini tamamladınız.
       Yarınki program: [özet]
       İyi geceler! 🌙"
```

### 5.3 Haftalık Özet Raporu

```
[Her Pazar akşamı]
Bot → "📊 Haftalık Performans Raporu

       ⏰ Çalışma: 18 / 25 saat (%72)
       📚 Tamamlanan konu: 12 / 15
       🔴 Eksik kalan: 3 konu
       📈 Trend: Geçen haftaya göre %15 artış

       En güçlü: Periodontoloji ✅
       Geliştirilmeli: Ortodonti ⚠️

       Gelecek hafta programında düzenleme yapılsın mı?
       [Aynı kalsın] [Ağırlıkları değiştir] [Koçla görüş]"
```

### 5.4 Bot Komutları

| Komut | Açıklama |
|-------|----------|
| `/basla` | Onboarding başlat |
| `/program` | Bugünkü programı göster |
| `/yarin` | Yarınki programı göster |
| `/hafta` | Haftalık program özeti |
| `/rapor` | Haftalık performans raporu |
| `/durum` | Genel ilerleme durumu |
| `/guncelle` | Müsaitlik bilgilerini güncelle |
| `/hedef` | Hedef güncelle |
| `/mola` | Belirli günlerde mola tanımla |
| `/destek` | Koçla iletişim |

---

## 6. Web Panel

### 6.1 Öğrenci Dashboard'u

**Ana Ekran:**
- Bugünün programı (konu + saat + durum)
- Haftalık ilerleme çubuğu (saat bazlı)
- Genel ilerleme (tamamlanan konular / toplam)
- Yaklaşan tekrar konuları
- Sınava kalan gün sayacı

**Takvim Görünümü:**
- Aylık takvim → her gün renk kodlu (yeşil: hedef tuttu, sarı: kısmen, kırmızı: eksik, gri: mola)
- Güne tıklayınca detay: hangi konular çalışıldı, kaç saat, dönüt puanları

**İstatistikler:**
- Ders bazlı ilerleme (her ders için yüzde çubuğu)
- Konu bazlı zorluk haritası (kolay/orta/zor renk matrisi)
- Haftalık/aylık çalışma saati trendi (line chart)
- Hedef vs gerçekleşen karşılaştırması
- Tahmini hazırlık tamamlanma tarihi

**Konu Havuzu:**
- Tüm dersler → konular listesi
- Her konunun durumu: Çalışılmadı / Çalışıldı / Tekrar edildi / Pekiştirildi
- Konu notları (öğrenci serbest not ekleyebilir)

### 6.2 Koç/Admin Paneli

**Öğrenci Listesi:**
- Tüm kayıtlı öğrenciler
- Hızlı durum: son aktivite, uyum oranı, risk seviyesi
- Filtreleme: profil tipi, uyum oranı, son aktiflik

**Öğrenci Detay:**
- Tüm öğrenci dashboard verileri (okuma yetkisi)
- Program düzenleme (sürükle-bırak takvim)
- Not ekleme (öğrenciye görünür/görünmez)
- Mesaj gönderme (Telegram üzerinden)

**Analitik:**
- Genel uyum oranı ortalaması
- En çok zorlanılan konular (tüm öğrenciler geneli)
- Aktif / pasif öğrenci oranı
- Program tamamlama projeksiyonu

---

## 7. Teknik Mimari

### 7.1 Teknoloji Stack (Önerilen)

| Katman | Teknoloji | Gerekçe |
|--------|-----------|---------|
| **Backend** | FastAPI (Python) | Hızlı geliştirme, async desteği, bot entegrasyonu kolay |
| **Veritabanı** | PostgreSQL (Supabase) | Ücretsiz tier yeterli, realtime, auth dahil |
| **Telegram Bot** | python-telegram-bot / aiogram | Async, inline keyboard desteği |
| **Web Panel Frontend** | React (Vite) veya Next.js | Dashboard için ideal |
| **Zamanlayıcı** | APScheduler veya Celery Beat | Hatırlatma zamanlaması |
| **Hosting** | Railway / Render / VPS | Bot + API aynı yerde |
| **Cache** | Redis (opsiyonel) | Sık erişilen veriler |

### 7.2 Veritabanı Şeması (Temel Tablolar)

```
students
├── id (PK)
├── telegram_id (unique)
├── name
├── email
├── phone
├── is_working (bool)
├── work_hours_start
├── work_hours_end
├── has_shifts (bool)
├── exam_target_date
├── target_goal (enum: top100 / top500 / pass / branch)
├── target_branch
├── profile_type (enum: intensive / moderate / limited / minimal)
├── study_preference (enum: morning / afternoon / evening / flexible)
├── previous_study (bool)
├── previous_resources (text)
├── last_mock_score (int, nullable)
├── weak_topics (jsonb)
├── created_at
└── updated_at

weekly_availability
├── id (PK)
├── student_id (FK → students)
├── day_of_week (0-6, pazartesi=0)
├── available_hours (decimal)
└── updated_at

courses
├── id (PK)
├── name
├── total_questions (ortalama soru sayısı)
├── weight_percent
├── estimated_study_hours
├── display_order
└── is_active

topics
├── id (PK)
├── course_id (FK → courses)
├── name
├── question_count (ortalama soru sayısı)
├── difficulty (enum: easy / medium / hard)
├── recommended_hours (decimal)
├── priority (enum: high / medium / low)
└── display_order

study_plans
├── id (PK)
├── student_id (FK → students)
├── start_date
├── end_date
├── status (enum: active / paused / completed)
├── total_planned_hours
├── created_at
└── updated_at

daily_schedule
├── id (PK)
├── plan_id (FK → study_plans)
├── date
├── day_of_week
├── total_planned_hours
└── is_rest_day (bool)

sessions
├── id (PK)
├── schedule_id (FK → daily_schedule)
├── topic_id (FK → topics)
├── session_type (enum: new_study / review_1 / review_2 / review_3 / review_4 / review_5)
├── planned_start_time
├── planned_duration_minutes
├── order_in_day
└── description

daily_reports
├── id (PK)
├── student_id (FK → students)
├── schedule_id (FK → daily_schedule)
├── date
├── reported_at (timestamp)
├── total_actual_hours (decimal)
├── compliance_rate (decimal, 0-100)
├── extra_topics_studied (text, nullable)
├── notes (text, nullable)
└── mood (enum: great / good / neutral / bad / terrible, nullable)

session_feedback
├── id (PK)
├── report_id (FK → daily_reports)
├── session_id (FK → sessions)
├── actual_duration_minutes (int)
├── status (enum: completed / partial / skipped)
├── difficulty_rating (enum: easy / medium / hard / impossible)
├── started_on_time (bool)
└── notes (text, nullable)

topic_progress
├── id (PK)
├── student_id (FK → students)
├── topic_id (FK → topics)
├── status (enum: not_started / studied / reviewed / reinforced / mastered)
├── total_time_spent_minutes (int)
├── review_count (int)
├── last_difficulty_rating
├── next_review_date
├── first_studied_at
└── last_studied_at

notifications
├── id (PK)
├── student_id (FK → students)
├── type (enum: session_start / session_end / daily_report / weekly_report / custom)
├── scheduled_at (timestamp)
├── sent_at (timestamp, nullable)
├── message_text
├── response (text, nullable)
└── status (enum: pending / sent / responded / expired)
```

### 7.3 Sistem Akış Diyagramı

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Telegram    │◄───►│   FastAPI     │◄───►│  PostgreSQL   │
│  Bot         │     │   Backend    │     │  (Supabase)  │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │  Scheduler   │
                    │  (APScheduler)│
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │  Web Panel   │
                    │  (React)     │
                    └──────────────┘
```

---

## 8. Program Yeniden Düzenleme (Adaptif Sistem)

### 8.1 Otomatik Ayarlama Tetikleyicileri

Sistem şu durumlarda programı otomatik revize eder:

| Tetikleyici | Aksiyon |
|-------------|---------|
| 3 gün üst üste uyum <%50 | Günlük yükü azalt, öncelikli konulara odakla |
| Bir konuda "Zorlandım" 2+ kez | O konuya ekstra tekrar ekle |
| Haftalık uyum >%90 | Tempolu artış öner |
| Öğrenci mola tanımladı | Kaçırılan konuları yeniden dağıt |
| Deneme sınavı sonucu girildi | Zayıf alanlara ağırlık kaydır |
| Müsaitlik güncellendi | Tüm programı yeniden hesapla |

### 8.2 Koç Müdahalesi

- Koç panelinden manuel program düzenleme
- Öğrenciye özel konu ekleme/çıkarma
- Motive edici mesaj gönderme
- Birebir görüşme planlama

---

## 9. Bildirim Zamanlaması

### 9.1 Günlük Bildirim Takvimi

| Zaman | Bildirim Tipi | Kanal |
|-------|---------------|-------|
| Çalışma başlangıcı - 15dk | Günlük program özeti | Telegram |
| Her oturum başlangıcı | Oturum hatırlatması | Telegram |
| Her oturum bitişi | Tamamlama onayı | Telegram |
| Son oturum + 30dk | Gün sonu dönüt formu | Telegram |
| 22:00 (cevap gelmezse) | Dönüt hatırlatması | Telegram |

### 9.2 Haftalık Bildirimler

| Zaman | Bildirim |
|-------|----------|
| Pazar 20:00 | Haftalık performans raporu |
| Pazartesi 08:00 | Yeni hafta programı özeti |

---

## 10. Gelecek Geliştirmeler (v2+)

| Özellik | Açıklama | Öncelik |
|---------|----------|---------|
| AI Soru Üretme | Konu bazlı pratik soru üretimi (Claude API) | Yüksek |
| Deneme Sınavı Modülü | Zamanlı mini testler, sonuç analizi | Yüksek |
| Sosyal Özellikler | Öğrenci sıralaması, grup motivasyonu | Orta |
| Pomodoro Timer | Bot içinde zamanlayıcı | Orta |
| Sesli Bildirim | Telegram voice message ile hatırlatma | Düşük |
| Kaynak Entegrasyonu | PDF/video kaynak linkleri konu bazlı | Orta |
| WhatsApp Desteği | Alternatif kanal | Düşük |
| Mobil App (PWA) | Web paneli mobil optimize | Orta |

---

## 11. Geliştirme Fazları

### Faz 1 — MVP (2-3 hafta)
- [ ] Telegram bot: onboarding akışı
- [ ] Veritabanı kurulumu (Supabase)
- [ ] Müsaitlik toplama + profil oluşturma
- [ ] Basit program oluşturma (konu verisi ile)
- [ ] Günlük hatırlatma gönderimi
- [ ] Gün sonu dönüt toplama

### Faz 2 — Akıllı Program (1-2 hafta)
- [ ] Spaced repetition algoritması
- [ ] Adaptif program düzenleme
- [ ] Haftalık rapor
- [ ] Deneme sınavı sonucu entegrasyonu

### Faz 3 — Web Panel (2-3 hafta)
- [ ] Öğrenci dashboard
- [ ] Takvim görünümü
- [ ] İstatistik grafikleri
- [ ] Koç/admin paneli

### Faz 4 — Optimizasyon (sürekli)
- [ ] AI destekli soru üretimi
- [ ] Gelişmiş analitik
- [ ] Performans tahminleme
- [ ] Çoklu öğrenci yönetimi

---

## 12. Hasan'dan Beklenen Veriler

Sistemi çalıştırmak için şu verilerin girilmesi gerekiyor:

1. **Ders Listesi** — DUS'taki tüm dersler (Bölüm 3.1 tablosu)
2. **Konu Dağılımı** — Her dersin altındaki konular
3. **Soru Dağılımı** — Her konudan ortalama kaç soru geldiği
4. **Çalışma Süreleri** — Her konuya önerilen çalışma saati
5. **Zorluk Seviyeleri** — Konu bazlı zorluk derecelendirmesi
6. **Öncelik Sırası** — Hangi konular öncelikli

> Bu veriler JSON veya Excel formatında girilebilir. Bot ve program motoru bu verilerle çalışacak.

---

## 13. Açık Sorular

- [ ] Ücretlendirme modeli ne olacak? (Abonelik / tek seferlik / freemium)
- [ ] Kaç öğrenciye hizmet verilecek? (ölçeklendirme kararı)
- [ ] Koç olarak kim müdahale edecek? (Hasan mı, başka biri mi, AI koç mu?)
- [ ] Mevcut DUS kaynak/kitap entegrasyonu gerekli mi?
- [ ] Deneme sınavı verileri hangi formatta gelecek?