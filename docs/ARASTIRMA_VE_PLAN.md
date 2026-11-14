# SPHEREx Zaman Makinesi — Kaynak Taraması ve Ekip Planı

NASA Space Apps 2026 · "Planet X and SPHEREx" · 5 kişilik ekip
Belge tarihi: Cumartesi 14 Kasım 2026, 12:00 (TSİ)

> **Son teslim: Pazar 15 Kasım, 23:59 (yerel etkinlik saati).** Şu andan itibaren ~36 saat var.
> Yerel etkinliğin jüri saati farklı olabilir. **Local Lead'e sorun.**

---

## BÖLÜM 1 — Kaynak taraması (hepsi tarandı)

### 1.1 Neye baktık?

| # | Kaynak | Alt sayfalar | Sonuç |
|---|---|---|---|
| 1 | Challenge sayfası (Details + Resources sekmesi) | Teslim rehberi, Jüri rehberi, SSS | Yeni kaynak **eklenmemiş**. Kurallar §1.2'de |
| 2 | IRSA SPHEREx | DR1/QR genel bakış, veri erişim rehberi, cutout aracı, Spectrophotometry aracı yardım sayfası, MOST, bulut erişimi, spektral kalibrasyon, **Explanatory Supplement (84 sayfa PDF)**, anormal görüntü listesi | Teknik bilgilerin çoğu buradan (§1.3) |
| 3 | SPHEREx eğitim notebook'ları (6 adet) | Giriş, cutout, ePSF, kaynak keşfi (+ yardımcı paket kodu), mozaik, HiPS küpü | Fotometri ve spektrum yöntemi (§1.4) |
| 4 | WiseView | Settings, Help, Links, About, URL formatı | Arayüz modelimiz (§1.5) |
| 5 | Backyard Worlds (backyardworlds.org) | Araştırma sayfası | Vatandaş bilimi dili ve "mover/dipole" kavramı |
| 6 | Gaia DR3 (MAST sayfası) | ESA DR3 dokümanı, gaia_source veri modeli, DR4 durumu, astroquery | Sorgu test edildi, 4.5 sn (§1.6) |
| 7 | Aladin Lite | Resmi doküman (cds-astro.github.io), GitHub örnekleri | Gömme kodu hazır (§1.6) |
| 8 | CSA NEOSSat | CSA sayfası, CADC, CADC TAP, notebook 01 ve **02**, CSA veri seti sayfası | Düşük öncelik (§1.7) |
| 9 | Ek: JPL Small-Body Identification API | — | Çalışıyor. Bilinen asteroitleri etiketlemek için |

**Erişilemeyenler:**
- IRSA Spectrophotometry ve Mosaic araç sayfaları 404 verdi. Yardım dokümanlarını okuduk, ikisinin de API'si yok.
- VizieR katalog sayfaları açılmadı. Gaia'ya ESA üzerinden erişiyoruz, sorun değil.
- IMCCE SkyBoT 403 verdi. Yerine JPL kullanacağız.

### 1.2 Kurallar (plan bunlara göre kuruldu)

**Teslim**
- Teslim proje sayfasından yapılıyor. "Submit for Judging" butonuna **Pazar 23:59'dan önce** basılmalı. Bu süreye kadar istenildiği kadar tekrar gönderilebiliyor.
- **Her şey İngilizce:** proje sayfası, link verilen tüm materyaller, slaytlar. Bu yüzden **arayüz de İngilizce olmalı.**
- **Demo:** ≤30 saniyelik video **veya** ≤7 slayt (başlık ve giriş dahil). Limit aşılırsa global jüriye giremiyor.
- **Linkler herkese açık olmalı**, giriş gerektirmemeli.
- En az bir NASA verisi kullanılmalı. Partner ajans verisi kullanmak da "highly encouraged". **Türkiye Uzay Ajansı da bu yılki partnerler arasında.**

**Yapay zekâ (SI) kuralı.** Bu bizi doğrudan ilgilendiriyor:
- SI araçlarının **nerede ve nasıl** kullanıldığı açıkça belirtilmeli. Kod için bu, README'de ve dosya başlıklarında yazmak demek.
- "SI should not be used to come up with your idea": çözüm fikri ve tasarım kararları ekibin olmalı.
- **Bu belgedeki özellik listesi bir öneri.** Ekip tartışıp kendi kararını vermeli, kararları da kayıt altına almalı.

**Jüri kriterleri** (her biri 1–5 puan):

| Kriter | Bizim için anlamı |
|---|---|
| Impact | Gönüllülerin keşif yapmasını sağlamak. Backyard Worlds hikâyesi |
| Creativity | 102 bandın yaratıcı kullanımı: spektrum, renkli kompozit, hareket ölçümü |
| **Validity** | Bilimsel doğruluk: Gaia ile karşılaştırma, ölçülen öz hareket, bayrak/artefakt uyarıları |
| **Relevance** | NASA verisi işin merkezinde. 5 test hedefinin hepsi çalışıyor |
| **Presentation** | Jüri bunu ayrıca vurguluyor. 1 kişi tam zamanlı buna ayrılmalı |

Global ödül kategorileri arasında bize en uygun ikisi: **Best Use of Data** ("space data'yı erişilebilir kılan") ve **Best Use of Science**.

### 1.3 SPHEREx verisi: kritik bilgiler

**Erişim (hepsi test edildi):**
- **Görüntü listesi.** IRSA TAP'ta `spherex.artifact JOIN spherex.plane` + `CONTAINS(POINT, p.poly)` sorgusu kullanılıyor.
  - **Gecikmesiz:** her hafta eklenen yeni veri anında görünüyor. Challenge'daki "kolay güncellenebilir" maddesi böylece kendiliğinden karşılanıyor.
  - Yayın adı (DR1/QR3) koda gömülü değil.
- **Cutout.** `<dosya URL>?center=RA,DEC&size=<derece>`
  - Çıktı tüm katmanları içeren bir FITS dosyası.
  - Görüntü kuzey yukarı **değil** ve bozulma (distortion) var.
  - 7–12 paralel istek öneriliyor. Ara sıra hata çıkıyor, yeniden deneme şart.
  - IRSA zaman zaman **503** veriyor. Bunu yaşadık.
- **S3 bulutu:** `s3://nasa-irsa-spherex/` (anonim, ücretsiz). Tam dosya ~70 MB olduğu için cutout servisi daha pratik.
- **Hızlı bağlam spektrumu:** DR1 HiPS küpü, `.../dr1/hips5_cube/hips_20261026/Norder5/Dir{D}/Npix{N}_cube.fits`
  - 512×512×102 kanal, ama dosya ~300 MB.
  - Notebook'ta "sadece görselleştirme için" diye belirtiliyor.

**Dosya yapısı:**
- **IMAGE:** MJy/sr cinsinden. **Zodyak ışığı çıkarılmamış.** Ayrı ZODI katmanından çıkarıyoruz.
- **VARIANCE** ve **ZODI** katmanları.
- **FLAGS:** 28 bitlik bayrak.
- **EPSF:** 33×33 PSF, 5× aşırı örneklemeli.
- **WCS-WAVE:** her pikselin dalga boyu.

**Gözlem takvimi** (Supplement §1.4):
- Gözlemler yılda 2 tarama turu halinde. **Survey 1–2:** ilk 12.5 ay (DR1). **Survey 3–4:** sonraki 12.5 ay (QR3, Mayıs 2026'dan itibaren).
- Bir bölge birkaç günde tamamlanıyor. Tek bir noktaya yüzlerce görüntü düşebiliyor: WISE 0855 için 258 görüntü, 4 ziyaret grubu.
- **Gaia DR4 2 Aralık 2026'da çıkıyor**, hackathon'dan sonra. Tablo adını ayar dosyasına koyarsak tek satırla geçilir. Bu da "güncellenebilirlik" hikâyesine katkı sağlar.

**Konum hassasiyeti** (Supplement §4.2.2):
- **RMS < 0.3″**, piksel ise 6.15″.
- Barnard's Star'ın 1 yıllık hareketi (~10″) gözle 1.5 piksel ama **ölçümle 30 sigmadan fazla**.
- **Bu, ağırlık merkezi (centroid) ölçümüyle öz hareketi doğrudan hesaplayabileceğimiz anlamına geliyor.** Sonucu Gaia ile karşılaştırmak güçlü bir Validity puanı getirir.

**Bayraklar** (Supplement Tablo 16):
- **Maskelenecekler:** TRANSIENT, OVERFLOW, SUR_ERROR, NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, OUTLIER, CROSSTALK, GHOST, GHOST_FPA, GHOST_EXT, STREAK, BLOOM, SNOWBALL, HALO, SATELLITE_HALO.
- **SOURCE (bit 21) maskelenmeyecek.** Bu "bilinen kaynak burada" demek. Supplement'a göre referans kataloğa **bilinen güneş sistemi nesneleri de dahil.**
  - **Katalogda olmayan hareketli bir nesne SOURCE bayrağı taşımaz.** Bu, "yeni olabilir" ipucu olarak kullanılabilir.

**Hareketli nesne gibi görünebilen artefaktlar** (Supplement §2.3, kullanıcıyı uyarmak için):
- **Kenar hayaleti (frame-edge ghost).** Üçgen şeklinde. Ardışık küçük kaydırmalarda **birden fazla karede tekrar ediyor.** Sahte hareketlinin en olası kaynağı bu.
- **Çizgisel hayalet** ve **ışın bölücü hayaleti** (~10′ disk, Band 3–4 sınırında).
- **8° hayaleti** ve **Ay kaynaklı kenar ışığı.**
- **Kozmik ışın, kartopu (snowball), çapraz konuşma (crosstalk).** Crosstalk 32 satır veya 64 sütun kaydırılmış **negatif kopyalar** üretiyor.
- **Uydu izleri.** Sönük olanlar bayraksız kalabiliyor.
- **Dağınık optik geçici ışık:** görüntülerin ~%1'inde görülüyor.
- **Atmosferik çizgiler:**
  - He 1.083 µm, Band 1–2'de zodyak ışığının 30 katına kadar çıkabiliyor.
  - Diğer çizgiler: 0.78, 0.84, 0.93, 1.13, 1.81, 2.63, 2.75, 4.03, 4.64 µm.
  - Shuttle glow (uzay aracı parıltısı): ~2.9 µm ve ~4.5 µm.
- **Resmi anormal görüntü listesi (CSV):** https://spherex.caltech.edu/page/anomalyimages. Bu listedeki görüntüleri otomatik işaretleyebilir veya hariç tutabiliriz.

**Zorunlu teşekkür metni** (sitenin altına konacak):
> "This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration."

Atıf: DR1 DOI 10.26131/IRSA678, QR3 DOI 10.26131/IRSA662.

### 1.4 Spektrum ve fotometri yöntemi

Kaynak keşfi yardımcı paketinden alındı (BSD-3 lisanslı, kullanırsak atıf vereceğiz).

**Adımlar:**
1. **Birim dönüşümü.** `mJy/piksel = MJy/sr × (6.15″)² × 2.3504e-8 × 1e9`. Pratikte tek çarpan: `0.889 mJy/piksel` (MJy/sr başına).
2. **Arka plan.** Halka (annulus) içinde, iç yarıçap 7 px, dış yarıçap 16 px. 3σ kırpılmış medyan alınıyor.
3. **Açıklık fotometrisi.** Yarıçap 3 px. `photutils` ile, alt piksel modunda.
4. **Dalga boyu.** Hedefin piksel konumunda WCS `"W"` değeri okunuyor. Notebook bunu `sip = None` ile yapıyor.
5. **Spektrum.** Her görüntüden bir (dalga boyu, akı) noktası alınıyor. Yüzlerce nokta, 0.75–5 µm aralığını kaplıyor.
6. **Bayraklar.** Paket bayraklı ölçümleri atmıyor, sayıyor. Biz grafikte farklı renkle gösterebiliriz.

**PSF fotometrisi** (daha temiz sonuç, P2 öncelikli): EPSF tablosunda en yakın bölge seçiliyor. Cutout koordinatı önce ana görüntüye çevrilmeli: `x_orig = 1 + x_cutout − CRPIX1A`.

IRSA'nın Spectrophotometry Tool'u Tractor PSF fotometrisi yapıyor. Ama **API'si yok**, işlem sırası uzun (her nokta ~1.7 sn) ve tek seferde en fazla 20 kaynak alıyor. Bizim aracımız **anlık** çalışacak. Jüriye farkımızı anlatırken bu önemli bir nokta.

### 1.5 WiseView: kopyalayacağımız ve aşacağımız şeyler

**WiseView'de olanlar:**
- RA/Dec girişi: derece veya `1h2m3s`, `1:2:3`, `1 2 3` formatları.
- FOV (arcsec), bant seçimi (W1, W2, W1+W2 renkli).
- Kayan pencere (yıl), blink hızı, zoom.
- Min–max germe, asinh doğrusallığı, ters çevirme.
- Seçenekler: önce/sonra, sınır çerçevesi, Gaia DR3 katmanı, fark görüntüsü, kaydır-topla (pmra/pmdec), sentetik nesne.
- Epoch göstergesi (`....++....`).
- **Tıkla → oraya git, sürükle → yeni FOV ile yeni sekme.**
- Linkler: Legacy Survey, SIMBAD, VizieR.
- Alt panelde Pan-STARRS görüntüsü.
- **Tüm ayarlar URL hash'inde.** Örnek: `#ra=…&dec=…&size=…&band=…&speed=…&diff=…&gaia=…&invert=…`

**WiseView'de olmayan, bizim ekleyeceklerimiz:**
1. Anlık spektrum (102 bant).
2. Işık eğrisi.
3. **Ölçülen öz hareket** ve Gaia ile karşılaştırması.
4. Bilinen asteroit etiketleri.
5. Bayrak ve artefakt uyarıları, anormal görüntü listesi.
6. Dedektör bazlı renkli kompozit.
7. "Mover nasıl tanınır" eğitim paneli (Backyard Worlds dili: *mover*, *dipole*).

### 1.6 Gaia ve Aladin

**Gaia DR3:**
- ESA'nın `astroquery.gaia` servisi ve ADQL `CONTAINS(POINT, CIRCLE)` sorgusuyla, ~4.5 sn. MAST üzerinden DR3 desteklenmiyor.
- Referans dönemi **J2016.0**. Her epoch'a taşımak için:
  - `Δdec = pmdec·Δt`
  - `Δra = pmra·Δt / cos(dec)`
  - Birim mas'tır, dereceye çevrilmeli.

**Aladin Lite:**
- Script: `https://cdn.jsdelivr.net/npm/aladin-lite@3.8.2/dist/aladin.js`
- Başlatma:
  ```js
  A.init.then(() => {
    const a = A.aladin('#al', { survey: 'P/PanSTARRS/DR1/color-z-zg-g', fov: 0.1, target: 'ra dec' });
  });
  ```
- Katalog bindirme: `A.catalogFromVizieR('I/355/gaiadr3', target, radius_deg, {onClick:'showTable'})`
- Kendi işaretlerimiz: `A.catalog()` ile katalog oluşturup `cat.addSources([A.source(ra, dec, {...})])` ile eklenir.
- Olaylar: `aladin.on('click' | 'objectClicked' | 'positionChanged', ...)`
- Kullanılabilir HiPS'ler: `P/DSS2/color`, `P/allWISE/color`, `P/PanSTARRS/DR1/color-z-zg-g`. **Aladin'de SPHEREx HiPS'i yok.**

**Asteroitler (JPL):**
- `https://ssd-api.jpl.nasa.gov/sb_ident.api?sb-kind=a&mpc-code=500&obs-time=YYYY-MM-DD_hh:mm:ss&fov-ra-center=HH-MM-SS.ss&fov-dec-center=[M]DD-MM-SS.s&fov-ra-hwidth=0.1&fov-dec-hwidth=0.1`
- Sonuç olarak isim, konum, parlaklık ve hız dönüyor.
- `mpc-code=500` yer merkezli konum verir. SPHEREx alçak yörüngede (~700 km) olduğu için bu yeterli.

### 1.7 CSA / NEOSSat

- **Uydu:** 15 cm teleskop, 3″/piksel, 0.85° FOV, filtresiz (CLEAR). 2013'ten beri aktif.
- **Veri:** CADC'de `NEOSSAT` koleksiyonu. Erişim TAP üzerinden: `ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/argus/sync`.
- **Notebook 02:** CADC'den indirme, dark çıkarma, üst üste toplama, **LSD ile çizgi (streaklet) tespiti**, ardışık kare farkı ve GIF yapıyor.
  - Bu, otomatik hareketli aday tespiti için bize fikir veriyor.
- **Arşivin içeriği:** çoğunlukla TESS ötegezegen hedeflerinin uzun süreli gözlemleri. Bizim hedeflerimizde NEOSSat görüntüsü olma ihtimali düşük.
- **Karar:** canlı entegrasyon yapmıyoruz. Zaman kalırsa (P2) "Partner data" paneli eklenir: aynı konumda NEOSSat karesi varsa gösterilir. Her durumda referanslarda ve sunumda belirtilecek.

### 1.8 Ek tarama: veri setleri, SPHEREx sitesi, IRSA Data Explorer

**Veri setleri (SIA koleksiyonları):** `spherex_dr1`, `spherex_dr1_deep`, `spherex_dr1_cube`, `spherex_qr3`, `spherex_qr3_deep`. TAP sorgumuz hepsini kapsıyor. Test hedeflerinde durum:

| Hedef | DR1 | QR3 | Derin alan | Toplam | Not |
|---|---|---|---|---|---|
| WISE 0855 | 258 | 0 | 0 | 258 | QR3'te henüz gözlenmemiş. Zaman aralığı Mayıs 2025 – Mayıs 2026 |
| Barnard's Star | 240 | 123 | 0 | 363 | Zaman aralığı **Ağu 2025 – Eyl 2026 (13 ay)** |
| R Draconis | — | — | — | **2493** (1638 DR1 + 855 QR3) | Kuzey Ekliptik Kutbu derin alanında. Yoğun ışık eğrisi verisi var. *(Düzeltme: ilk sayım yanlış koordinatla yapılmıştı. Doğru konum 248.168, +66.755.)* |
| RW Aurigae | 226 | 109 | — | 335 | |
| ε Indi B (2025 konumu) | 338 | 120 | — | 458 | |

→ **Derin alanlarda görüntü sayısı çok yüksek.** Her epoch'tan en fazla N görüntü alınmalı (örneğin bant başına 10) ve isteğe bağlı "tümü" seçeneği sunulmalı. Yoksa tek istek 2000+ cutout indirir.

**SPHEREx sitesi (spherex.caltech.edu):**
- **Kahverengi cüce haberi (8 Ekim 2026).**
  - SPHEREx spektrumlarında 37 kahverengi cücede **su, CO₂, CO ve metan** görülmüş, binlercesi inceleniyor.
  - Spektrum grafiğine **molekül bantlarını işaretleyelim**: H₂O ~1.4 / 1.9 / 2.7 µm, CH₄ ~1.65 / 2.2 / 3.3 µm, CO₂ ~4.3 µm, CO ~4.6 µm.
  - Bu kısa bir iş ama bilimsel olarak çok etkili.
- **Yıldızlararası kuyruklu yıldız 3I/ATLAS** Aralık 2025'te SPHEREx ile gözlenmiş. Hızlı hareket eden nesne demosu için aday (P2). Konumu JPL Horizons'tan alınır.
- **Görsel kullanım politikası.**
  - Sitedeki görseller "Courtesy NASA/JPL-Caltech" atfıyla kullanılabilir.
  - **NASA ve JPL logoları izinsiz kullanılamaz.** Sitemizde ve slaytlarımızda logo olmayacak. Teslim kuralı da NASA markalı içerik üretmeyi yasaklıyor.
- **"Data Tools" sayfası.** Resmi araçlar: arama, Spectrophotometry, Cutout, Source Discovery, Mosaic. Spectral Cube Cutout Ocak 2027'de geliyor. **Hiçbiri zaman içinde blink veya animasyon yapmıyor.** Bizim boşluğumuz tam burası.

**IRSA Data Explorer (uygulama tarayıcısında denendi):**
- Konum, zaman ve bant filtreli arama sunuyor. Sonuçlar tablo halinde ve görüntüler tek tek açılıyor.
- Deep field kapsama haritası var.
- Aramalar **sıraya giriyor (job queue)**. Bugün 20 saniyeden uzun bekledi, büyük olasılıkla hackathon yoğunluğu.
- İsimle aramada "Barnard's Star" çözülmedi (kesme işareti sorunu). Bizim isim çözümleyicimiz bunu desteklemeli.

**Bakılmayan, bilinçli olarak atlanan sayfalar:** MAST Portal, CasJobs, VO Services (genel MAST araçları, Gaia'ya ESA'dan erişiyoruz). NEOSSat FITS kullanıcı kılavuzu PDF'i (NEOSSat'ı canlı entegre etmiyoruz). SPHEREx ekip ve kurum sayfaları. WiseView eğitim videosu.

### 1.9 Detaylı inceleme: IRSA SPHEREx sayfası (25 linkin hepsi)

Sayfadaki her link kendi tarayıcımızda açılarak okundu.

| Link | İçerik | Bizim için anlamı |
|---|---|---|
| Mission Characteristics | 6 bant, R değerleri, teşekkür metni, 4 temel makale | Teşekkür metni sitenin altına (§1.3) |
| DR1 / QR genel bakış | DR1 = Survey 1+2 (yeniden işlenmiş). QR3 = Survey 3+4, haftalık geliyor. QR2 artık aranamıyor (Şubat 2027'ye kadar indirilebilir) | DR1 + QR3 kullanıyoruz. **Atıf: DR1 DOI 10.26131/IRSA678, QR3 DOI 10.26131/IRSA662** |
| PSF başlık hatası | Sadece eski QR1/QR2'yi etkiliyor | Bizi ilgilendirmiyor |
| **SPLICES** | ~9 milyon buz absorpsiyonu adayı kaynaktan oluşan katalog (YSO, değişen yıldız, karbon yıldızı). TAP ile erişiliyor | P2: "Bu kaynak SPLICES'ta" etiketi. Buz bantlarını (H₂O 3.0 µm, CO₂ 4.27 µm, CO 4.67 µm) spektrumda işaretlemek |
| **Kuyruklu yıldız 3I/ATLAS** | **Hazır tablo:** 259 görüntü, **her görüntüde kuyruklu yıldızın konumu** (`comet_ra`, `comet_dec`). Ağustos ve Aralık 2025. Tablo indirildi ve doğrulandı | **Hareketli nesne demosu için birebir.** Gerçek bir yıldızlararası kuyruklu yıldızın SPHEREx'te ilerleyişi |
| **MOST (Moving Object Search Tool)** | **API'si var ve `catalog=spherex` destekliyor.** Nesne adı veya NAIF ID verildiğinde, nesnenin geçtiği SPHEREx görüntülerini ve her birindeki tahmini konumu döndürüyor. **Test edildi:** 3I için 52 sn'de 160 satır. İsim belirsizse NAIF ID istiyor (`Vesta` → `20000004`) | **Yeni mod önerisi: "Track a Solar System object"** (§2'de P1) |
| Bulut erişimi | `s3://nasa-irsa-spherex/{dr1,qr3,qr2}/`, anonim erişim. Spektral görüntülerin yanında kalibrasyon ürünleri de var | **S3'ten kısmi okuma test edildi:** `fits.open(..., use_fsspec=True)` + `Cutout2D(h['IMAGE'].section)` ile ~10 sn/dosya. IRSA cutout servisi çökerse **yedek yol** |
| Spectrophotometry Tool (yardım + SSS) | Tractor ile PSF fotometrisi, ama **iş başına en az 5 dk**, aynı anda 2 iş, bir seferde 20 kaynak, **API yok**. **Konumu yeniden ortalamıyor.** SSS: "Hızlı hareket eden yıldızda yanlış konum = kötü spektrum". SSS: "Spektrumdaki inip çıkmalar epoch farkından olabilir, noktaları tarihe göre renklendirin" | Bizim farkımız **hızlı bakış spektrumu**, ve hareket düzeltmeli konumdan. Spektrum grafiğinde **varsayılan renk epoch olmalı**. "Research-grade için IRSA Spectrophotometry Tool" linki konulmalı. Bayrak bitleri 32 (CONTAINS_BAD_PIXEL) ve 33 (FIT_ERROR) sadece onların çıktısında var |
| Mosaic Tool (yardım) | Zodyak ışığı çıkarılmış küp, 102 kanal, en fazla 5°×5°, en küçük piksel 6.15″. Deep field karelerini kullanmıyor. API yok | Fikir verici. Bizim karelerimiz de ZODI çıkarılmış |
| Cutout Tool + `ibe/cutouts.html` | `center=` için `deg` veya `pix`, `size=` için `deg`, `arcmin`, `arcsec` veya `pix` kullanılabiliyor. SPHEREx cutout'ları sıkıştırılmıyor. Görüntü dışına taşan kesit kırpılıyor. Hiç örtüşme yoksa 500 hatası dönüyor | `size=3arcmin` gibi doğrudan kullanılabilir. 500 hatası "görüntü dışında" anlamına geliyor, yeniden denenmemeli |
| Bilinen hatalar listesi | Data Explorer'da işler kayboluyor. Sunucular iki haftada bir Salı sabahı (Pasifik saati) bakımda | Pazar günü bakım yok, iyi. Yine de önbellek şart |
| Arşiv Kullanıcı Rehberi (3 alt sayfa) | Dosya adı formatı, ~70 MB/dosya, **All-Sky Cube** (HEALPix order 5, 12,288 karo, 12.9″/px, zodyak çıkarılmış, HiPS PNG'si 0–40 MJy/sr sabit germe ile), tüm kalibrasyon ürünleri, SIA2 ~1 gün gecikmeli (**TAP gecikmesiz**, bizim seçimimiz doğru) | Aladin'de SPHEREx All-Sky HiPS'ini arka plan olarak göstermeyi deneyebiliriz (P2, test edilmedi) |
| Spektral kalibrasyonlar | Laboratuvarda ölçülmüş geçirgenlik eğrileri (kanal başına) | Gerek yok. Geniş bant sentezi yaparsak lazım olabilir |
| Program Interfaces (voapi) | Catalogs, Images, Spectra, **ZTF Lightcurves**, MOST, IBE | **CatWISE2020 ve AllWISE TAP'ta çalışıyor** (pmra/pmdec var) ama bugün sorgu başına ~75 sn. ZTF ışık eğrisi API'si zaman aşımına uğradı. İkisi de P2 ve mutlaka önbellekli olmalı |
| 4 temel makale | ADS insan doğrulaması (CAPTCHA) istedi, **atlatılmadı**. Özetler arXiv'den okundu | Aşağıda |
| SPHEREx web sitesi, 6 notebook | Daha önce incelenmişti (§1.4, §1.8) | — |

**Makalelerden önemli rakamlar:**
- **Bock et al. (arXiv:2511.02985):** 4 tam tarama sonunda 5σ derinlik **19.5–19.9 AB** (0.75–3.8 µm) ve **17.8–18.8 AB** (3.8–5 µm). Tek epoch daha sığ: yaklaşık 4 tarama yerine 1, yani ~0.75 mag daha az. Ekip 3 yıl sonunda **güneş sistemi nesneleri kataloğu** çıkaracak.
- **Akeson et al. (arXiv:2511.15823):** Pipeline makalesi. Bizim kullandığımız ürünleri anlatıyor.
- **Crill et al. (arXiv:2505.24856):** Sky Simulator. Hassasiyet zodyak ışığıyla sınırlı.
- **Korngut et al. (arXiv:2603.29835):** Alet tüm gereksinimleri karşılıyor.
- **Ek: SPHEREx kahverengi cüce spektrumları (arXiv:2607.00543):**
  - 37 kahverengi cüce, **L0'dan Y4'e kadar**. WISE 0855 bir Y4 cücesi, yani büyük olasılıkla listede.
  - Bizim anlık spektrumumuzu bu makaledekiyle karşılaştırmak **güçlü bir Validity kanıtı** olur.
  - Makale, modellerin en çok CO₂ ve CO bantlarında zorlandığını söylüyor.

### 1.10 Detaylı inceleme: SPHEREx eğitim notebook'ları (6 notebook + ilgili 2 bölüm)

Her notebook kendi tarayıcımızda baştan sona okundu.

| Notebook | Yeni ve önemli bilgi | Bizim için anlamı |
|---|---|---|
| **Intro** | Başlıkta görüntü başına kalite sayaçları var: `L2 N_TRANSIENT`, `N_HALO`, `N_PERSIST` vb. Tam dosyada FLAGS sıkıştırılmış (CompImageHDU). WCS-WAVE sadece **9×9 kontrol noktalı** bir tablo | **Otomatik kare kalite filtresi.** Supplement, `N_TRANSIENT > 300.000` olanları kötü sayıyor. Dalga boyu bilinear interpolasyonla doğrudan hesaplanabilir: hızlı ve SIP uyarısı yok |
| **Cutouts** | TAP sorgusu 20 sn. **Paralel indirmede başarısızlık oranı serialden yüksek** (84 cutout'ta 16'ya karşı 4). `cache=True` önbellek ipucu. Dosya adında `l2b_retry` gördük, ama kontrolümüzde **kopya yok**: retry dosyası orijinalin yerini alıyor | Yeniden deneme şart (bizde var). Worker sayısı 8–10'da kalsın. Kopya ayıklamaya gerek yok |
| **PSF** | ePSF'ler `photutils.psf.ImagePSF(data=epsf, oversampling=(5,5))` ile kullanılıyor. `evaluate(X,Y,flux=1,x_0,y_0)` ile piksel altı konumda çizilebiliyor. PSF FWHM ~7.5″. `NEFF` ~4.4–4.8 px, kırmızıda büyüyor. Cutout koordinatı ana görüntüye `1 + x − CRPIX1A` ile çevriliyor | **PSF-fit fotometri:** `flux = Σ(w·d·P)/Σ(w·P²)`. **PSF-fit astrometri** (x₀, y₀ serbest): her görüntüde tam konum ölçülür, ardından öz hareket hesaplanır (P1 #10) |
| **Source Discovery** | MJy/sr'den μJy'ye dönüşüm için SAPM (piksel alanı haritası) S3'te. `sep` ile arka plan. **Bant farkı (D2−D4) ile kırmızı kaynak avı.** Bayrak filtresi: `flags ∈ {0, 2, 2097152}`. Açıklık 3/4/5 px, halka 7–16 px. BSD-3 lisanslı yardımcı paket. IRSA teşekkür metni | **Yeni özellik: "Color difference" modu.** Kahverengi cüceler 4.5 µm'de (D5–D6) parlak, metan yüzünden 3.3 µm'de (D4) sönük. Bu yüzden D6−D4 farkında öne çıkarlar. Backyard Worlds'ün W1−W2 yönteminin SPHEREx karşılığı |
| **Mosaic Cube** | 102 kanal tablosu (merkez dalga boyu + bant genişliği). **Çizgi haritası:** ilgili katman − komşu 4 katmanın medyanı. GALEX ile karşılaştırma | **Yeni özellik: "Narrow-band blink".** Kullanıcı dalga boyu aralığı seçer (örneğin CO 4.6 µm), kareler sadece o aralıktaki piksellerden oluşturulur. 102 bandın yaratıcı kullanımına doğrudan bir cevap |
| **HiPS Cube** | HiPS adresi: `https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube`. Standart HipsGen, PNG karolar, 102 katman, `hips_pixel_cut 0 40`, asinh. FITS karosu ~300 MB. **Hazır emisyon çizgisi listesi:** Paβ 1.282, H⁻ 1.60, Paα 1.875, Brγ 2.166, Brβ 2.626, PAH 3.30, Brα 4.052, CO 4.67 µm | Aladin'de SPHEREx HiPS arka plan olarak denenecek (P2). Çizgi listesi spektrum grafiğine eklenecek (P1 #17) |
| **Moving Object Searches** (Techniques) | `astroquery.ipac.irsa.most.Most.query_object(obj_name="20000004", catalog="spherex", obs_begin, obs_end)` hazır kullanılıyor. **SPHEREx desteği Haziran 2026'da eklenmiş.** Kesitleri nesneye göre ortalayıp **median stack** yaparak sönük nesneyi gösteriyor (2I/Borisov örneği). MPC tek satır veya yörünge elemanlarıyla yeni keşfedilen nesneler de aranabiliyor. **Kontrol:** MOST çıktısı artık **DR1** linkleri veriyor (160/160) | "Track a Solar System object" modu (P1 #16) bu kodla doğrudan kurulur. **Kaydır-topla (nesne merkezli stack)** ile sönük asteroitler görünür olur |
| WISE notebook'ları (menü) | AllWISE görüntüleri, NEOWISE güneş sistemi ışık eğrileri, NEOWISE çok epoch'lu ışık eğrileri (Parquet) | P2: değişen yıldızlarda NEOWISE 3.4/4.6 µm ışık eğrisini SPHEREx ile yan yana göstermek (aynı dalga boyları, 10 yıllık taban çizgisi) |
| Diğer Techniques | Cloud Access, HATS/LSDB, Parallelization, SED görselleştirme | Doğrudan gerekmiyor |

### 1.11 Detaylı inceleme: WiseView (byw.tools/wiseview)

Uygulama tarayıcısında modlar tek tek denendi. Kaynak kodu (`static/flash3.js`, 43 KB) okundu.

**Mimari:**
- Tarayıcı, AWS Lambda üzerindeki `png-animation` servisine bütün ayarları gönderiyor. Servis **sunucuda germe uygulanmış PNG kareler** üretiyor, bunlar S3'ten (`amnh-citsci-public`) çekiliyor.
  - Sonuç: **parlaklık kaydırıcısı her değiştiğinde kareler yeniden isteniyor**, yani yavaş.
  - Bizde germe, ters çevirme ve fark tarayıcıda yapılacak, anında olacak.
- Cevapta `all_mjds`, `mjds`, `epochs`, `neg_epochs`, WCS (CRPIX/CRVAL/NAXIS) ve min/max var. Bizim `/api/frames` tasarımımız da aynı mantıkta.
- `/xref`: o koordinatın Backyard Worlds (Zooniverse) subject ID'leri.
- `/pawnstars`: alt panelde Pan-STARRS renkli görüntüsü.
- Gaia: DR3 sorgusu bir AWS proxy üzerinden yapılıyor, yıldızlar her epoch'a öz hareketle kaydırılıyor.
  - **Hata:** referans dönemi 2015.5 alınmış (DR2'nin dönemi), DR3 için doğrusu 2016.0. Bizde doğru yapılacak.
- Kullanılan teknolojiler: jQuery, jQuery UI kaydırıcılar, canvas üzerine katman çizimi.
- `/wiseview-v3` aynı sayfa. Klavye kısayolu **yok**.

**Kontroller (tam liste):**
- **Konum ve görüntü:** RA/Dec (derece veya altmışlık), FOV (″), bant (W1 / W2 / W1+W2 renkli).
- **Zaman:** Sliding window (yıl), Blink interval (ms), Skip middle epochs, Skip duplicate windows.
- **Görünüm:** Zoom, Min–max pixel (symlog kaydırıcı), Stretch Linearity (asinh "a"), Invert, Maximize dynamic range, Border epoch 0.
- **WISE'a özel:** Separate scan directions (paralaks için), Use only NEOWISE, Smooth by scan direction.
- **Katman:** Gaia DR3 overlay.
- **Difference imaging** + "Exclusion window (yıl)".
- **Shift and add** + pmra/pmdec (mas/yıl).
- **Synthetic Object A ve B:** RA, Dec, W1/W2 parlaklığı, pmra/pmdec, referans MJD, "Subtraction".
- **Gezinme:** Görüntüye tıklama oraya ortalar. Sürükleme, seçilen alanı yeni sekmede yeni FOV ile açar.
- **Links sekmesi:** Legacy Survey (unwise-neo11 katmanı), Pan-STARRS, SIMBAD, VizieR, Zooniverse subject'leri.
- **Help sekmesi:** YouTube eğitim videosu (izlenemedi) ve V1↔V2 ayar karşılıkları.
- **About sekmesi:** unWISE atıfları, asinh açıklaması. Sitenin altında "WiseView is operated by the American Museum of Natural History" yazıyor.

**Denenen modlar ve öğrenilenler:**
- **Difference imaging, en önemli öğrenim.** Her kareden **diğer tüm epoch'ların ortalaması (şablon)** çıkarılıyor. Exclusion window içindeki yakın epoch'lar şablona katılmıyor. Sonuçta sabit yıldızlar tamamen kayboluyor, **sadece hareket eden nesne kalıyor**. WISE 0855'te çok net görüldü.
  - → **Bizim P0 "fark" özelliğini bu yöntemle yapalım** ("son − ilk" yerine "kare − diğerlerinin medyanı").
- **Gaia overlay:** WISE 0855'in **Gaia karşılığı yok** (optikte görünmeyecek kadar soğuk).
  - → "Hareket ediyor ama Gaia'da yok = ilginç aday" mantığını kullanıcıya açıkça gösterelim. Örneğin hareketli kaynağın yanında "No Gaia match" etiketi.
- **Shift and add:** Kareler pm·Δt kadar kaydırılıyor, hareketli nesne sabit kalırken yıldızlar kayıyor. Sönük nesneleri toplamak için kullanılıyor.
- **Zaman aralığı farkı:** WiseView'de 2010–2023 arasında **13 yıl** var, SPHEREx'te ~1.3 yıl.
  - → **Her hedef için "Open in WiseView" linki** (aynı RA/Dec, aynı FOV) koyalım. WISE'ın 3.4/4.6 µm bantları SPHEREx D5/D6 ile örtüşüyor. Uzun dönem hareketi oradan, spektrumu bizden görmek güçlü bir hikâye.

**WiseView'de olmayanlar, bizim üstün olacağımız yerler:**
1. **Anında germe** (sunucuya gitmeden).
2. Spektrum.
3. Işık eğrisi.
4. Asteroit etiketleri ve MOST modu.
5. Bayrak ve artefakt uyarıları.
6. Klavye kısayolları (boşluk ile oynat/durdur, ← → ile kare, D ile fark, I ile invert).
7. Doğru Gaia dönemi.
8. 6 dedektör ve dar bant seçimi.
9. Mobil uyum (WiseView "Chrome için tasarlandı", mobilde zayıf).

### 1.12 Detaylı inceleme: Gaia (MAST sayfası ve bağlantıları)

| Link | İçerik | Bizim için anlamı |
|---|---|---|
| MAST Gaia sayfası | Görev özeti + 14 link | — |
| DR1/DR2/EDR3/DR3 DOI sayfaları (archives.esac.esa.int) | **404**. Yerine ESA DR3 sayfası okundu | — |
| **ESA Gaia DR3 sayfası** | **Referans dönemi J2016.0** (DR2 2015.5, DR1 2015.0). G ≈ 3–21. 1.47 milyar kaynakta tam astrometri, **344 milyon kaynakta sadece konum (pm yok)**. Öz hareket hatası G<15 için ~0.02 mas/yıl. Hazır çapraz eşleşme tabloları var (**allWISE**, 2MASS, Pan-STARRS). 1.7 milyon uzun periyotlu değişkende epoch fotometrisi var. 94 bin ultra soğuk yıldız | Kodda boş pmra/pmdec güvenle atlanmalı. Dönem 2016.0 olmalı (WiseView'de hata). R Dra için Gaia ışık eğrisi P2 olabilir |
| ESA Gaia Archive | Arayüz. **3.15 sürümünde "breaking change" uyarısı var**, ama sorgularımız etkilenmedi | **TAP düz HTTP ile test edildi:** `https://gea.esac.esa.int/tap-server/tap/sync`, CSV, **1.9 sn** |
| MAST Portal / Astroquery | MAST'ta `Catalogs` Gaia DR1/DR2 için. DR3 resmi olarak belgelenmemiş | Kullanmıyoruz |
| CasJobs | SQL toplu sorgu, hesap gerekiyor | Gerek yok |
| **MAST VO Services** | Katalog listesinde **"GAIA dr3"**, AllWISE, 2MASS, PanSTARRS dahil. **Test edildi:** `https://gsss.stsci.edu/webservices/vo/CatalogSearch.aspx?RA=..&DEC=..&SR=..&CAT=GAIADR3&FORMAT=CSV`, **0.8 sn** | **ESA'ya yedek Gaia kaynağı** (ve AllWISE için de) |

**⚠️ KRİTİK BULGU: hedefleri SPHEREx tarihine taşımadan araç yanlış yeri gösterir.**

CDS Sesame ile çekilen J2000 konumları ve öz hareketlerle 2025.6'ya kadar olan yer değiştirme:

| Hedef | pm (mas/yıl) | 2000→2025.6 kayma |
|---|---|---|
| Barnard's Star | (−802, +10362) | **266″ = 4.4′** |
| ε Indi B | (+3982, −2467) | **120″ = 2′** |
| WISE 0855 | (−8118, +673) | Challenge koordinatları **~2010.5 dönemine** ait. 2025'te o noktanın **~2′ batısında** |
| RW Aur, R Dra | ~20 | ~1″ (önemsiz) |

- **WISE 0855 veriyle doğrulandı.**
  - 7′ alanla yeniden çalıştırıldı. Dört epoch'ta da **2010.5 varsayımıyla öngörülen konumda** sinyal var: S/N 2.3 → 2.6 → 2.9 → 4.4, konum batıya kayıyor.
  - Challenge koordinatının tam üzerinde **hiçbir şey yok** (S/N ≈ 1). **İlk kavram kanıtımız boş gökyüzüne bakıyormuş.**
- **P0'a eklendi:** İsimle aramada konum ve pm çözümlenir. Görüş alanı **SPHEREx epoch'larının ortasına** taşınır. Her karede hedefin öngörülen konumu işaretlenir. Koordinatla girişte "Bu yüksek öz hareketli bir yıldız mı?" kontrolü için Gaia/SIMBAD'a bakılır.
- **Sunum için güçlü bir hikâye:** "Challenge'ın verdiği koordinata bakarsanız WISE 0855'i göremezsiniz. 15 yılda 2 yay dakikası kaçtı. Aracımız onu otomatik buluyor."
- **Servis notları:**
  - SIMBAD TAP bugün 404 verdi. Sesame çalıştı ama WISE 0855 için zaman aşımına uğradı.
  - → İsim çözümleme **birden çok kaynaklı** olmalı (Sesame → SIMBAD → yerel tablo).
  - 5 test hedefi + 3I/ATLAS için konum ve pm değerleri **yerel bir JSON'a gömülmeli**.

### 1.13 Detaylı inceleme: CSA NEOSSat sayfası

- **Sayfa içeriği:**
  - 15 cm teleskop, ~800 km yörünge, 2013'ten beri aktif. Asteroit, kuyruklu yıldız, uzay çöpü (DRDC HEOSS) ve ötegezegen geçişleri.
  - Veriler CSA Açık Veri Portalı ve CADC'ye gidiyor.
  - Konuk gözlemci programının proje listesinde bizimle ilgili olanlar: **ultra soğuk cüce dönme periyotları** (Lambier, Metchev), **2I/Borisov izleme**, yakın-Güneş kuyruklu yıldızları, T CrB.
- **Linkler:**
  - Sayfadaki Açık Veri Portalı linki (`donnees-data…/9ae3e718…`) **kırık (404)**. Çalışan sayfa: `data.asc-csa.gc.ca/dataset/neossat`.
  - "Comets and asteroids" sayfası genel bilgi içeriyor.
  - Konuk gözlemci duyurusu (Cycle 7) bizim için gerekli değil.
- **Test hedeflerimizde NEOSSat kapsamı (CADC TAP, kalibre kareler):**

  | Hedef | Kare sayısı |
  |---|---|
  | Barnard | 1 (Kas 2019) |
  | ε Indi B | 0 |
  | WISE 0855 | 2 (2021) |
  | RW Aur | 0 |
  | R Dra | 1 (Eki 2024) |

  - Hepsi optik ve SPHEREx'ten farklı yıllarda. WISE 0855 optikte görünmez.
- **Sonuç: değerlendirme veriyle doğrulandı.** Canlı entegrasyon yok. İstenirse Barnard'ın 2019 NEOSSat karesi "partner verisi, optik karşılaştırma" olarak statik bir panelde gösterilebilir (P2). Sunumda CSA'ya atıf yapılacak.

### 1.14 Detaylı inceleme: CADC (Kanada Astronomi Veri Merkezi)

**Ana sayfa:**
- 15 teleskop arşivi: JWST, Gemini, CFHT, JCMT, HST, NEOSSat, BRITE, MOST (Kanada uydusu, IRSA MOST ile karıştırılmamalı), UKIRT vb.
- 12 gelişmiş veri ürünü: MegaPipe, IRIS, VLASS vb.
- Servisler: SSOIS, DSS, CANFAR, Advanced search, Web services.
- Not: "CADC hizmetleri profesyonel astronomlar içindir." Bu yüzden canlı ve yoğun kullanım yerine **link ve hafif sorgu** tercih edilmeli.

| Sayfa | İçerik | Bizim için anlamı |
|---|---|---|
| NEOSSat koleksiyonu | Ürün seviyeleri RAW/CLEAN/COR/CORD. Teşekkür metni. FITS Kullanıcı Rehberi (33 sayfa) ve "NEOSSat Experience" (16 sayfa) PDF'leri okundu. Başlıklarda standart WCS (CD matrisi) var. Sınır parlaklık ~19 mag (100 sn). MPC kodu C53. İşleme yazılımı `jasonfrowe/neossat` (GPL-3) | NEOSSat değerlendirmesi değişmedi (§1.13) |
| **SSOIS (Solar System Object Image Search)** | **75 milyon görüntüde** bir asteroit veya kuyruklu yıldızı arıyor. Kapsamı: WISE, NEOSSat, Pan-STARRS, SDSS, DECam, HST, CFHT, Gemini, ESO, Subaru, Skymapper, LCO… **SPHEREx yok.** **URL ile sorgulanabiliyor:** `/en/ssois/results.html?lang=en&object=<isim>&search=bynameall&epoch1=YYYY+MM+DD&epoch2=...`. **TSV API:** `/cadcbin/ssos/ssosclf.pl?...;format=tsv`. **Sabit konum API:** `/cadcbin/ssos/fixedssos.pl?pos=RA,DEC`. **Testler:** Vesta (Ağu 2025), 1 sn'de 4 DECam karesi. **3I/ATLAS (Ara 2025), aynı ay Hubble WFC3 görüntüleri.** Barnard'ın 2025 konumunda 36 DECam karesi | **Partner kaynağı entegrasyonu (P1, çok ucuz):** asteroit/kuyruklu yıldız modunda **"Find this object in other archives (CADC SSOIS)"** linki. Herhangi bir hedefte "Other telescopes at this position" linki. Sunum: "SPHEREx'in kızılötesinde gördüğü 3I/ATLAS'ı aynı ay Hubble da çekti, linkle ulaşılıyor" |
| **DSS (Digitized Sky Survey)** | POSS-I (1950–58), POSS-II (1987–98), SERC/AAO plakaları, 1.0–1.7″/px. Cutout testi `archive.stsci.edu/cgi-bin/dss_search?v=poss1_red\|poss2ukstu_red&r=&d=&h=&w=&f=gif` ile çalıştı | **"70 yıllık hareket" görseli:** Barnard 1953'ten bu yana ~12.8′ kaydı. POSS-II'de (1990'lar) 10′ kadrajın alt kenarında, POSS-I'de kadrajın dışında. Aladin'de DSS2 katmanı + hedefin 1950→2026 yolu çizgi olarak (P1, ucuz) |
| Web services | argus (TAP), caom2ops (DataLink/SODA cutout/pkg), sia, data, vault, youcat | NEOSSat canlı kullanılmayacağı için gerek yok |
| Service Status | Harici durum sayfasına yönlendiriyor | — |
| Documentation | Daha önce okundu (TAP formatı) | — |
| Diğer arşivler (JWST, HST, Gemini, BRITE, IRIS vb.) | Kısa göz atıldı | Doğrudan ihtiyaç yok. SSOIS ve DSS üzerinden dolaylı faydalanılıyor |

**Teşekkür metinleri** (sitenin altına, CADC servisleri kullanılırsa):
- CADC: "This research used the facilities of the Canadian Astronomy Data Centre operated by the National Research Council of Canada with the support of the Canadian Space Agency."
- SSOIS: Gwyn, Hill & Kavelaars (2012) atfı.

### 1.15 Detaylı inceleme: CSA NEOSSAT_Tutorial (GitHub)

**Repo bilgileri:** `asc-csa/NEOSSAT_Tutorial`, 2023'te açılmış, son güncelleme Ekim 2025. Dosyalar: README, LICENSE, 4 notebook (01 ve 02, İngilizce + Fransızca). Fransızcalar çıktısız çeviri.

**Lisans: değiştirilmiş MIT.**
- © Kanada Kraliyeti / CSA, 2023.
- Kullanım, değiştirme ve dağıtım serbest. **Telif notu korunmalı.**
- **CSA'nın adı izinsiz tanıtım ve reklamda kullanılamaz.** Yani "CSA onaylı" gibi bir izlenim vermemeliyiz, sadece "CSA verisi/tutorial'ı kullanıldı" diyebiliriz.

| Notebook | İçerik (baştan sona okundu) | Test sonucu | Bizim için anlamı |
|---|---|---|---|
| **01 – Extracting Data & Visualization** | (1) CSA FTP'den yıl/gün/saate göre indirme: `ftp.asc-csa.gc.ca /users/OpenData_DonneesOuvertes/pub/NEOSSAT/ASTRO/{yıl}/{gün}/`, dosya adı `NEOS_SCI_YYYYDDDhhmmss.fits`. (2) CADC'den `astroquery.cadc`: `get_collections`, `query_region(coord, radius, collection='NEOSSAT')`, `time_exposure` filtresi, `get_image_list` ile cutout URL'leri. Sondaki notebook 02 linki **kırık** (dosya `code/` altına taşınmış) | `query_region(c, 0.5*u.deg, ...)` güncel astroquery'de **hata veriyor**. Yarıçap `radius=` anahtar sözcüğüyle verilmeli. Düzeltilmiş haliyle Barnard çevresinde 662 satır, 2 kalibre kare. **Cutout URL'si alındı:** `caom2ops/sync?ID=cadc:NEOSSAT/NEOS_SCI_2019305153110_clean.fits&POS=CIRCLE ra dec 0.1` | İsteğe bağlı "partner data" panelinin tarifi hazır (P2) |
| **02 – Pre-Processing & Analysis** | (A) ADQL ile tarih araması (`Plane.time_bounds_samples` INTERVAL, `calibrationLevel=2`, `quality_flag != 'junk'`), `instrument_keywords` (06-ST_ACQUIRE / 16-FINE_POINT), `get_data_urls` ile indirme. (B) FITS yapısı: 1024×1024, ~3″/px, dosya adı ekleri `_cor`/`_clean`/`_cord`. (C) Overscan düzeltme (son 50 sütun), median dark, dark çıkarma. (D) Median stack. **LSD ile çizgi (streaklet) tespiti.** **Hareketli nesne maskesi: kare − medyan, 3σ eşik, binary_opening, remove_small_objects.** Optik akış önerisi. (E) Maske görselleştirme, GIF. Not: kayma düzeltmesi yapılmadığı için "her şey hareket ediyor" görünüyor | Tarih araması tutorial'daki sonucu **birebir** verdi (98 satır, 16 sn) | **Fikir (P2): fark modunda otomatik aday işaretleme.** Kare − şablon, ardından 3σ eşik ve morfolojik temizlik, sonra aday lekeleri daire ile işaretlemek. WiseView'de yok. Hizalamanın (reproject) önemini doğruluyor |

**Sonuç:**
- Tutorial bize NEOSSat verisine erişimin çalışan tarifini veriyor (bir küçük düzeltmeyle).
- Hareketli nesne tespit mantığı bizim fark yöntemimizle aynı, otomatik aday işaretleme fikri buradan.
- NEOSSat'ın test hedeflerimizdeki kapsamı çok az olduğu için (§1.13) canlı entegrasyon kararı değişmedi.
- **Proje sayfasındaki "Space Agency Partner Data" alanına** NEOSSat tutorial'ı, CADC ve SSOIS yazılacak.

### 1.16 Detaylı inceleme: NEOSSat Dataset (CSA Açık Veri Portalı)

**Sayfa:** `data.asc-csa.gc.ca/dataset/neossat`. Lisans **Open Government Licence – Canada** (atıf yeterli). 2018'de yayımlanmış, metadata Haziran 2026'da güncellenmiş. Kitle: "General public, Scientists".

| Kaynak | İçerik | Not |
|---|---|---|
| CADC Data Archive | CADC NEOSSat sayfası | §1.14'te okundu |
| **Astronomy Data (HTTP dizini)** | `data.asc-csa.gc.ca/users/OpenData_DonneesOuvertes/pub/NEOSSAT/ASTRO/{yıl}/{gün}/`. **2017–2026 arası**, en son klasör **2026/312 (8 Kasım 2026)**, o gün 181 dosya. Ham `.fits.gz` + `_cor` + `_cord` | **Veri canlı ve güncel.** FTP'nin HTTP karşılığı (tutorial FTP kullanıyor). Konuma göre arama yok, sadece tarihe göre |
| XML | Görüntü başına metadata (teleskop, hedef adı, pointing durumu, CCD sıcaklığı, gözlem zamanı). **6004 dosya, sadece 2015–2018 arası.** Eski FTP yollarını gösteriyor | Güncel değil, gerekmez |
| FITS Image User's Guide (PDF) | §1.14'te okundu | — |
| **Supporting document (DOCX, EN/FR)** | Teknik özet: **1072×1072 CCD, 0.8° FOV, 777 km Güneş-eşzamanlı yörünge, Güneş'e 45°'ye kadar, sınır parlaklık 19.4 mag (100 sn, işlem sonrası).** Ayrıca kaynak listesi: MPC, JPL Horizons, ESA NEOCC, CNEOS, IAWN, NASA Exoplanet Archive, CDS (SIMBAD/VizieR/Aladin), astropy, DS9, **Space Apps 2014 asteroit challenge'ı** | Kullandığımız servislerle örtüşüyor. Yeni bir şey gerektirmiyor |
| NEOSSat Experience (PDF) | §1.14'te okundu | — |
| Tutorial | §1.15'te incelendi | — |
| JSON metadata (CKAN API) | `donnees-data.asc-csa.gc.ca/api/action/package_show?id=62d8033b-…`. Kaynak listesi ve lisans makine tarafından okunabiliyor | — |
| Benzer veri seti: **NEOSSat Proje Değerlendirmesi** (2014, PDF 69 sayfa) | 2005–2013 dönemi yönetim ve denetim raporu: bütçe, gecikmeler, yüklenici riski, 3 öneri. 2013 sonunda bilimsel görüntü kalitesi henüz yeterli değilmiş | Teknik karşılığı yok |
| Diğer benzer veri setleri | THEMIS, WINDII, CASSIOPE (uzay havası ve atmosfer), OSIRIS-REx, MOST (AMSA) | Konumuzla ilgisi yok |

**Sonuç:** NEOSSat değerlendirmesi değişmedi (§1.13, §1.15). Partner kaynak kullanımımız şöyle olacak:
1. **CADC SSOIS linkleri** (P1, §1.14).
2. İsteğe bağlı, Barnard'ın 2019 NEOSSat karesi ile "partner data" paneli (P2).
3. Proje sayfasında ve sunumda CSA/CADC atıfları.

---

> ### ✅ KAYNAK TARAMASI TAMAMLANDI (14 Kasım 2026, ~14:10)
> Challenge'ın Resources sekmesindeki **8 linkin hepsi** ve bağlantılı alt sayfalar okundu, kritik servisler kodla test edildi:
> - IRSA SPHEREx (25 link)
> - SPHEREx eğitim notebook'ları (6 notebook + MOST notebook'u)
> - WiseView
> - Gaia (MAST + ESA)
> - CSA NEOSSat
> - CADC (SSOIS, DSS dahil)
> - NEOSSat Tutorial
> - NEOSSat Dataset
>
> Ek olarak SPHEREx Explanatory Supplement (84 sayfa), challenge teslim ve jüri rehberleri, SPHEREx sitesi ve Backyard Worlds incelendi.
>
> **Ulaşılamayan / atlatılmayan:** ADS makale sayfaları (CAPTCHA, özetler arXiv'den alındı), birkaç kırık link (404), WiseView YouTube eğitim videosu.

## BÖLÜM 2 — Ürün tanımı

**İsim önerisi:** *SPHEREx Blink* veya *Time Machine for the Infrared Sky* (ekip seçecek).

**Tek cümle:** Gökyüzünde bir koordinat girin. SPHEREx'in o bölgeyi farklı zamanlarda çektiği görüntüler video gibi oynasın, hareket eden ve parlaklığı değişen nesneler göze çarpsın. Herhangi bir noktaya tıklayın, 0.75–5 µm spektrumu ve ışık eğrisi anında çizilsin.

### Öncelikler

**P0: Pazar sabahı itibarıyla çalışıyor olmalı**
1. Koordinat veya isim girişi, FOV, bant seçimi (6 dedektör + "all").
   **İsimle girişte konum + öz hareket çözülür ve görüş alanı SPHEREx tarihine taşınır** (§1.12, kritik). Hedefin her karedeki öngörülen konumu işaretlenir.
2. Epoch blink: hız, zoom, germe (min/max, asinh), ters çevirme.
3. Fark görüntüsü **WiseView yöntemiyle** (her kare − diğer epoch'ların medyanı, exclusion window ile) ve önce/sonra modu.
4. URL'de tüm ayarlar (paylaş/göm), `?ra=..&dec=..` desteği.
5. 5 test hedefinin önbelleği ısıtılmış ve hepsi çalışıyor.
6. İnternette herkese açık adreste yayında.

**P1: bizi öne çıkaracaklar**

| # | Özellik | Neden |
|---|---|---|
| 7 | Anlık spektrum (tıklanan nokta) | Challenge'da "extra kudos" |
| 8 | Işık eğrisi | RW Aur ve R Dra test hedefleri bunu gerektiriyor |
| 9 | Gaia DR3 katmanı + öz hareket okları | Challenge'da açıkça isteniyor |
| 10 | **Ölçülen öz hareket** (centroid) ve Gaia karşılaştırması | Validity puanı |
| 11 | Bayrak ve anormal görüntü uyarıları | Challenge'da isteniyor, sahte hareketlileri eliyor |
| 12 | Bilinen asteroit etiketleri (JPL) | Kolay ve etkili |
| 13 | Dedektör renkli kompozit | 102 bandın yaratıcı kullanımı |
| 14 | Aladin bağlam paneli + SIMBAD/VizieR linkleri | Challenge'da isteniyor |
| 15 | "How to spot a mover" kısa rehberi | Impact puanı (vatandaş bilimi) |
| 16 | **"Track a Solar System object" modu** (MOST API ile). Demo: 3I/ATLAS | Asteroit ve kuyruklu yıldız için hazır NASA servisi. Challenge'ın ilk cümlesindeki "comets, asteroids" kısmını karşılıyor |
| 17 | Spektrumda molekül ve buz bantları (H₂O, CH₄, CO₂, CO) + emisyon çizgileri | Kahverengi cüce makalesi ve SPHEREx'in bilimsel amacıyla bağlantılı |
| 18 | **"Color difference" modu** (örn. D6−D4) | Kahverengi cüce avı. Backyard Worlds yönteminin SPHEREx karşılığı |
| 19 | **"Narrow-band blink"** (dalga boyu aralığı seçimi) | 102 bandın yaratıcı kullanımı (challenge'daki açık istek) |
| 20 | Otomatik kare kalite filtresi (`L2 N_*` sayaçları + anormal görüntü listesi) | Sahte hareketlileri azaltır, Validity |
| 21 | "Open in WiseView" linki (aynı koordinat ve FOV) + "No Gaia match" etiketi | 13 yıllık WISE verisiyle bağlam. Backyard Worlds'ün aday seçme mantığı |
| 22 | Klavye kısayolları + mobil uyum | WiseView'de olmayan kullanılabilirlik |
| 23 | **CADC SSOIS linkleri** ("Find this object in other archives", "Other telescopes at this position") | CSA partner kaynağının gerçek ve anlamlı kullanımı. Neredeyse sıfır efor |
| 24 | **Uzun dönem hareket izi:** Aladin'de DSS2 + hedefin 1950→2026 yolu | "70 yılda 13 yay dakikası" hikâyesi |
| 25 | (P2) **Otomatik aday işaretleme:** fark karesinde 3σ eşik + morfolojik temizlik, adaylar daire ile işaretlenir | NEOSSat tutorial yöntemi. WiseView'de yok |

**P2: zaman kalırsa**
- Kaydır-topla
- PSF fotometrisi
- HiPS bağlam spektrumu
- Otomatik aday tespiti (fark görüntüsünde dipol arama)
- NEOSSat paneli
- Sentetik nesne ekleme

---

## BÖLÜM 3 — Mimari ve API sözleşmesi

```
frontend/  (düz HTML + JS, build adımı yok)
  index.html, app.js, viewer.js (canvas blink), charts.js, aladin.js, url.js
backend/   (Python FastAPI)
  main.py (uç noktalar), spherex_core.py (mevcut), photometry.py, catalogs.py
data/cache/  (cutout FITS + hesaplanmış sonuçlar, .gitignore'da)
```

**API sözleşmesi.** İlk saatte üzerinde anlaşılır, sonra frontend sahte veriyle başlar:

| Uç nokta | Döndürdüğü |
|---|---|
| `GET /api/frames?ra&dec&fov_arcmin&bands` | `{target, wcs:{crval,crpix,cdelt}, shape:[ny,nx], epochs:[{id, date_start, date_end, mjd, n_images, bands, anomalous, data_b64 /*float32*/}]}` |
| `GET /api/spectrum?ra&dec` | `[{wavelength_um, flux_mjy, err_mjy, mjd, epoch, detector, flags:[...]}]` |
| `GET /api/lightcurve?ra&dec&bands` | `[{mjd, flux_mjy, err_mjy, detector}]` |
| `GET /api/motion?ra&dec` | `{epochs:[{mjd, ra, dec, err}], pm_measured:{pmra, pmdec, err}, gaia_match:{source_id, pmra, pmdec}}` |
| `GET /api/gaia?ra&dec&fov_arcmin` | `[{source_id, ra, dec, pmra, pmdec, parallax, g, at_epoch:{<id>:[ra,dec]}}]` |
| `GET /api/asteroids?ra&dec&fov_arcmin&mjd` | `[{name, ra, dec, vmag, ra_rate, dec_rate}]` |
| `GET /api/resolve?name=` | `{ra, dec}` (Sesame/SIMBAD) |

**Önemli kararlar:**
- **Tarayıcıya ham float32 dizi gidiyor.** Germe, ters çevirme ve fark tarayıcıda anında hesaplanıyor. Boyut küçük: 10′ FOV ≈ 98×98 piksel ≈ 38 KB/epoch.
- **Ağır işler önbellekte.** Aynı istek ikinci kez anında dönüyor. Demo hedefleri önceden ısıtılıyor.
- **Uzun istekler için ilerleme göstergesi** var. İlk istek 1–2 dk sürebiliyor.
- **Yayına alma:** Hugging Face Spaces (Docker, ücretsiz, kalıcı disk yok, önbellek imaja gömülür) veya Render/Railway. **Cumartesi gecesi ilk deploy yapılır**, sona bırakılmaz.

---

## BÖLÜM 4 — 5 kişilik görev dağılımı

| Rol | Sorumluluk | Gereken beceri |
|---|---|---|
| **A: Veri/Backend** | FastAPI, IRSA hattı, önbellek, `/frames`, anormal liste, hata yönetimi, deploy'da backend | Python |
| **B: Bilim/Analiz** | Fotometri, spektrum, ışık eğrisi, centroid ile öz hareket, Gaia taşıma, JPL asteroit, 5 hedefin bilimsel doğrulaması | Python + astronomi ilgisi |
| **C: Görüntüleyici (frontend çekirdeği)** | Canvas blink, kontroller, fark ve önce/sonra, URL hash, tıkla-git, klavye kısayolları | JavaScript |
| **D: Paneller + Tasarım/UX** | Spektrum/ışık eğrisi grafikleri, Gaia/asteroit/bayrak katmanları, Aladin paneli, rehber metinleri (İngilizce), görsel tasarım | JavaScript + tasarım |
| **E: Sunum/Teslim/QA** | Repo düzeni, README, SI beyanı, referans listesi, demo videosu (≤30 sn) + 7 slayt, proje sayfası metni (İngilizce), test, yayın linki kontrolü | İletişim, tasarım |

E tek başına değil: Pazar öğleden sonra herkes sunuma destek verir.

---

## BÖLÜM 5 — Zaman çizelgesi (TSİ)

| Ne zaman | Ne | Kontrol noktası |
|---|---|---|
| **Cmt 12:00–13:00** | Başlangıç: GitHub reposu, Python ortamı, API sözleşmesinin onayı, rol dağılımı. A, WISE 0855 için **sahte JSON** üretir, C/D onunla hemen başlar | Herkes repo'yu çalıştırabiliyor |
| **Cmt 13:00–20:00** | **Sprint 1.** A: `/api/frames` + önbellek. B: fotometri ve spektrum prototipi (notebook). C: blink görüntüleyici + kontroller. D: sayfa iskeleti, tasarım, grafik bileşenleri. E: README, 5 hedefin önbelleğini ısıtma betiği, deploy denemesi | **20:00: tarayıcıda gerçek veriyle WISE 0855 blink** |
| **Cmt 20:00–02:00** | **Sprint 2.** Fark ve önce/sonra, URL, FOV, bant seçimi, isimle arama. B: `/spectrum` + `/lightcurve`. **İlk deploy** | **02:00: P0 yayında** |
| **Paz 02:00–08:00** | Uyku (en az 5 saat). Gerekirse vardiyalı | — |
| **Paz 08:00–16:00** | **Sprint 3: P1.** Spektrum/ışık eğrisi panelleri, Gaia okları, ölçülen öz hareket, asteroitler, bayrak uyarıları, renkli kompozit, Aladin, rehber | 12:00 ara kontrol |
| **Paz 16:00** | **Özellik dondurma.** Yeni özellik yok, sadece hata düzeltme | — |
| **Paz 16:00–20:00** | Hata düzeltme, son deploy, ekran görüntüleri. E: demo videosu ve slaytlar | 20:00: son deploy |
| **Paz 20:00–22:30** | Proje sayfası (İngilizce), referanslar, SI beyanı, linklerin gizli pencerede testi | — |
| **Paz 22:30** | **TESLİM.** 1.5 saat yedek. 23:59'a kadar tekrar gönderilebilir | ✅ |

---

## BÖLÜM 6 — Riskler

| Risk | Önlem |
|---|---|
| IRSA yavaş veya 503 veriyor (bugün Data Explorer da sırada bekledi) | Yeniden deneme (var), 5 hedefin önbelleği önceden ısıtılmış, demo önbellekten çalışır |
| Derin alanda binlerce görüntü (R Dra: 2256) | Epoch ve bant başına görüntü sınırı, "tümünü indir" isteğe bağlı |
| Hareket gözle 1–2 piksel, belirsiz | Fark görüntüsü, ölçülen öz hareket, Gaia okları, zoom. Demo için **Barnard's Star** (parlak) |
| Sahte hareketli (hayalet, kozmik ışın) | Bayrak maskeleme + anormal liste + kullanıcı uyarısı |
| Deploy son dakikada patlar | Cumartesi gecesi ilk deploy |
| SI kuralı | README'de ve dosya başlıklarında SI beyanı. Tasarım kararlarını ekip verir ve kayda geçirir |
| Kod yorumları Türkçe | Teslimden önce İngilizceye çevrilecek (E kontrol eder) |
