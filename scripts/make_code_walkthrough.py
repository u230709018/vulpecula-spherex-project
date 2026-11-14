"""
Build the team's Turkish code walkthrough (internal note, like docs/EKIP_KURULUM.md).

Usage: .venv/bin/python scripts/make_code_walkthrough.py [out.html]
       (default output: output/kod_anlatimi.html, a git-ignored folder)
Then open the HTML in a browser and print it to PDF, or:
       msedge --headless --no-pdf-header-footer --print-to-pdf=kod_anlatimi.pdf output/kod_anlatimi.html

The code blocks are cut from the real files by function name, so they always match the
repository. If a function named below is renamed or removed, the script stops with an
error at that line: update the explanation there.

Parts of this file were written with the assistance of an AI coding assistant
(Claude, Anthropic) and reviewed by the team. See README "Use of AI".
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output" / "kod_anlatimi.html"
parts = []


def lines_of(rel):
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


def block(rel, start, end, head=None):
    ls = lines_of(rel)[start:end]
    while ls and not ls[-1].strip():
        ls.pop()
    cut = head is not None and len(ls) > head
    if cut:
        ls = ls[:head]
    code = html.escape("\n".join(ls))
    more = '<div class="more">… devamı dosyada</div>' if cut else ""
    parts.append(f'<div class="code"><div class="cap">{rel} · satır {start + 1}</div><pre>{code}</pre>{more}</div>')


def PY(rel, name, head=None):
    ls = lines_of(rel)
    i = next(k for k, l in enumerate(ls) if re.match(rf"(def|class) {name}\b", l))
    while i > 0 and ls[i - 1].startswith("@"):
        i -= 1
    j = next((k for k in range(i + 2, len(ls)) if re.match(r"(def |class |@|# ---|[A-Za-z_]+ ?[:=])", ls[k])
              and not ls[k - 1].startswith("@")), len(ls))
    while ls[j - 1].startswith("@"):
        j -= 1
    block(rel, i, j, head)


def JS(rel, name, head=None):
    ls = lines_of(rel)
    i = next(k for k, l in enumerate(ls) if re.match(rf"(async )?function {name}\(", l))
    j = next(k for k in range(i, len(ls)) if ls[k] == "}" or (k == i and ls[k].rstrip().endswith("}")))
    block(rel, i, j + 1, head)


def RNG(rel, start_pat, end_pat, head=None):
    ls = lines_of(rel)
    i = next(k for k, l in enumerate(ls) if re.search(start_pat, l))
    j = next(k for k in range(i, len(ls)) if re.search(end_pat, ls[k]))
    block(rel, i, j + 1, head)


def H1(t): parts.append(f"<h1>{t}</h1>")
def H2(t): parts.append(f"<h2>{t}</h2>")
def H3(t): parts.append(f"<h3>{t}</h3>")
def P(t): parts.append(f"<p>{t}</p>")
def UL(*items): parts.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
def NOTE(t): parts.append(f'<p class="note">{t}</p>')


SC, PL, CT, MV, MN = ("backend/spherex_core.py", "backend/pipeline.py", "backend/catalogs.py",
                      "backend/moving.py", "backend/main.py")
AJ, IH, CS = "frontend/app.js", "frontend/index.html", "frontend/style.css"

# ------------------------------------------------------------------ cover
parts.append("""<div class="cover"><div class="kicker">NASA Space Apps 2026 · Planet X and SPHEREx</div>
<div class="title">SPHEREx Time Machine</div><div class="sub">Kodun mantığı: tüm repo, parça parça</div>
<p>Bu belge repodaki her dosyanın ne yaptığını, gerçek kod parçalarını göstererek anlatır.
Kod blokları doğrudan dosyalardan kesilmiştir; başlıklarındaki satır numarası dosyadaki yerini gösterir.</p>
<p>Okuma sırası: önce büyük resim ve kavramlar, sonra sunucu (Python), sonra arayüz (JavaScript),
en sonda 14 Kasım'da eklenen yeni özellikler.</p></div>""")

# ------------------------------------------------------------------ 1
H1("1. Büyük resim")
P("Araç, gökyüzünde bir nokta alır ve NASA'nın SPHEREx teleskobunun o noktayı farklı tarihlerde çektiği "
  "görüntüleri art arda oynatır. Sabit yıldızlar yerinde durur; hareket eden ya da parlaklığı değişen bir cisim göze çarpar.")
P("İki parça vardır. <b>Sunucu</b> (Python, FastAPI) veriyi arşivden bulur, indirir, temizler, hizalar ve ölçer. "
  "<b>Arayüz</b> (tarayıcıda çalışan JavaScript) hazır kareleri çizer, oynatır ve kullanıcı etkileşimini yönetir.")
H3("Bir isteğin yolculuğu")
UL("Kullanıcı bir isim ya da koordinat yazar. İsimse sunucu onu koordinata ve öz harekete çevirir (<code>/api/resolve</code>).",
   "Arayüz <code>/api/frames</code> adresine istek atar. Sonuç önbellekteyse hemen döner; değilse arka planda bir iş başlar.",
   "İş: arşiv sorgusu → ziyaretlere ayırma → indirilecekleri seçme → kesitleri indirme → temizleme → ortak ızgaraya hizalama → ziyaret ve dedektör başına tek kare → tayf ve ışık eğrisi.",
   "Arayüz işi 1,5 saniyede bir yoklar (<code>/api/jobs</code>), bitince sonucu alır (<code>/api/result</code>).",
   "Tarayıcı kareleri normalize eder, seçilen moda göre birleştirir, çizer ve oynatır.")
H3("Dosya haritası")
UL("<code>backend/spherex_core.py</code>: SPHEREx verisiyle ilgili her şey (sorgu, indirme, okuma, hizalama, fotometri).",
   "<code>backend/pipeline.py</code>: uçtan uca iş akışı ve sonuç önbelleği.",
   "<code>backend/catalogs.py</code>: isim çözümleme, öz hareket, Gaia yıldızları, bilinen asteroitler.",
   "<code>backend/moving.py</code>: Güneş Sistemi cismi modu (asteroit ve kuyruklu yıldız takibi).",
   "<code>backend/main.py</code>: web sunucusu ve API adresleri.",
   "<code>frontend/index.html</code>, <code>style.css</code>, <code>app.js</code>: sayfa iskeleti, görünüm, tüm arayüz mantığı.",
   "<code>backend/targets.json</code>, <code>scripts/warm_cache.py</code>, <code>data/results/</code>: hazır hedefler ve önceden hesaplanmış sonuçlar.",
   "<code>render.yaml</code>, <code>Dockerfile</code>, <code>requirements.txt</code>: yayınlama ve kurulum.")

# ------------------------------------------------------------------ 2
H1("2. Bilmeniz gereken kavramlar")
UL("<b>RA / Dec (sağ açıklık / dik açıklık):</b> gökyüzündeki enlem-boylam. RA 0–360°, Dec −90° ile +90° arası.",
   "<b>FITS:</b> astronomi görüntü dosyası biçimi. Bir dosyada birden çok bölüm (IMAGE, FLAGS, VARIANCE, ZODI…) bulunur; her bölümün bir başlığı vardır.",
   "<b>WCS:</b> başlıktaki, gökyüzü koordinatını piksele (ve tersine) çeviren dönüşüm.",
   "<b>MJD:</b> gün sayacı olarak tarih (Modified Julian Date). <b>jyear:</b> ondalıklı yıl (2025.9 gibi).",
   "<b>Dedektör (D1–D6):</b> SPHEREx'in altı dedektörü; her biri 0,75–5,0 µm aralığının bir dilimini görür.",
   "<b>Her pikselin kendi dalga boyu:</b> dedektörlerin önünde konuma göre değişen bir filtre var. Aynı cisim her pozlamada dedektörün başka yerine düşer, yani başka dalga boyunda ölçülür. Tayf böyle oluşur.",
   "<b>Ziyaret (epoch):</b> SPHEREx aynı bölgeye yaklaşık altı ayda bir döner ve birkaç gün içinde çok sayıda görüntü alır. Bu görüntü kümesine ziyaret diyoruz.",
   "<b>Öz hareket (proper motion):</b> bir cismin gökyüzünde yıllık kayması; birimi mili-yay saniyesi/yıl (mas/yr).",
   "<b>Zodi:</b> Güneş Sistemi'ndeki tozun yaydığı arka plan ışığı; görüntüden çıkarılır.",
   "<b>Bayraklar (flags):</b> her piksel için sorun işaretleri (kozmik ışın, doygunluk, hayalet yansıma…).",
   "<b>Kesit (cutout):</b> büyük görüntüden hedefin etrafındaki küçük kare.",
   "<b>Yeniden izdüşüm (reproject):</b> farklı açılarla çekilmiş görüntüleri aynı piksel ızgarasına oturtma.",
   "<b>Birleştirme (co-add):</b> aynı bölgenin birkaç görüntüsünü tek, daha temiz bir karede toplama.")

# ------------------------------------------------------------------ 3
H1("3. backend/spherex_core.py: verinin çekirdeği")
H2("3.1 Sabitler ve bayrak kümeleri")
RNG(SC, r"^IRSA_BASE", r"^MAX_TRANSIENT_PIXELS")
UL("<code>MJYSR_TO_MJY_PER_PIX</code>: görüntüdeki birim (MJy/sr, yüzey parlaklığı) ile bir pikselin kapladığı açıyı çarparak piksel başına akıya (mJy) çevirir.",
   "<code>BAD_FLAGS</code>: ölçüm (fotometri) için kullanılamaz sayılan pikseller.",
   "<code>DISPLAY_BAD_FLAGS</code>: yalnızca kalıcı bozuk pikseller. Görüntülemede daha az piksel maskelenir, çünkü geçici sorunları birleştirmedeki medyan zaten temizler.",
   "<code>ARTIFACT_FLAGS</code>: hareketli cisim gibi görünebilecek sorunlar; kullanıcıya uyarı olarak gösterilir.")
H2("3.2 Veri yapıları")
PY(SC, "ImageRecord")
P("Arşivdeki tek bir görüntünün kimliği: dosya yolu, tarih, dedektör ve hangi ziyarete ait olduğu.")
PY(SC, "Cutout")
P("İndirilmiş bir kesitin tüm içeriği. <code>image</code> sıkı maskelidir (ölçüm için), <code>display</code> hafif maskelidir (görüntüleme için). "
  "<code>wavelength_at</code>, FITS başlığındaki ikinci dönüşümü (“W” anahtarı ve WCS-WAVE tablosu) kullanarak bir pikselin dalga boyunu verir. "
  "<code>flag_names_at</code>, bir pikselin bayrak sayısındaki bitleri isimlere çevirir.")
H2("3.3 Arşiv sorgusu")
PY(SC, "find_images")
P("IRSA'ya tek bir veritabanı sorgusu (ADQL) gider: ayak izi (<code>p.poly</code>) verilen noktayı içeren tüm görüntüler. "
  "Sorguda sürüm adı geçmediği için yeni yayınlanan veriler de kendiliğinden gelir. Arşiv yoğunken hata verebildiğinden 5 kez, "
  "her seferinde iki katı bekleyerek (3, 6, 12… saniye) yeniden dener.")
H2("3.4 Ziyaretlere ayırma ve indirme bütçesi")
PY(SC, "group_epochs")
P("Görüntüler zamana göre sıralanır. Bir öncekinden 10 günden fazla ara varsa ya da ziyaret 40 günü aşacaksa yeni ziyaret başlar. "
  "İkinci kural, sürekli gözlenen derin alanların tek dev ziyaret olmasını önler.")
PY(SC, "budget_select")
P("Her (ziyaret, dedektör) hücresinden en fazla N görüntü seçilir; fazlası varsa zamana eşit aralıklarla yayılmış olanlar alınır. "
  "Binlerce görüntüsü olan derin alanlar böylece makul sürede yüklenir.")
H2("3.5 Kesitleri indirme")
PY(SC, "cutout_url")
PY(SC, "fetch_cutout")
P("IRSA'nın kesit servisi, dosya adresinin sonuna merkez ve boyut eklenince yalnızca o bölgeyi döndürür. "
  "Her kesit, adresinin özetiyle (SHA-1) adlandırılıp diske yazılır; aynı kesit ikinci kez indirilmez. "
  "400/404/500 yanıtı “kesit bu görüntüyle örtüşmüyor” demektir ve denemeden vazgeçilir; ağ hatalarında artan bekleme ile yeniden denenir.")
PY(SC, "fetch_all")
P("İndirmeler 8 iş parçacığıyla paralel yapılır; her biten indirme ilerleme çubuğuna bildirilir.")
H2("3.6 Kesiti okuma ve temizleme")
PY(SC, "load_cutout")
UL("Görüntüden zodi modeli çıkarılır (<code>IMAGE − ZODI</code>).",
   "FLAGS bölümünün başlığındaki <code>MSKN*</code> anahtarları, bayrak adı ile bit numarasını eşler; <code>mask_of</code> istenen adlardan bir bit maskesi kurar.",
   "İki kopya üretilir: hafif maskeli <code>display</code> ve sıkı maskeli <code>image</code>. Maskelenen pikseller NaN (sayı değil) yapılır.",
   "<code>n_transient</code>: karedeki geçici olay sayısı; çok yüksekse kare ileride atılır.")
H2("3.7 Ortak ızgara ve kare üretimi")
PY(SC, "make_grid")
P("Hedefi merkez alan, kuzeyi yukarıda olan bir ızgara tanımlar. Piksel sayısı tek sayıya yuvarlanır ki hedef tam orta piksele düşsün. "
  "<code>cdelt</code>'in ilk değeri eksidir: sağa gidildikçe RA azalır, yani doğu solda kalır.")
PY(SC, "build_frames")
UL("Her kesitten kendi arka planı (medyan) çıkarılır, sonra <code>reproject_interp</code> ile ortak ızgaraya taşınır.",
   "Kesitler (ziyaret, dedektör) çiftine göre gruplanır.",
   "Grupta 3 ya da daha fazla görüntü varsa piksel bazında medyan alınır; tek karede görünen kozmik ışınlar böylece elenir.",
   "Daha az görüntü varsa gürültüsü az olana fazla ağırlık veren (1/varyans) ortalama kullanılır.")
H2("3.8 Fotometri: bir noktanın parlaklığını ölçme")
PY(SC, "photometry_at")
UL("Hedefin piksel konumu WCS ile bulunur.",
   "Kaynağın etrafında 2 piksel yarıçaplı bir daire (açıklık) ve 4–8 piksel arası bir halka tanımlanır. Halka, yerel arka planı verir.",
   "Akı = dairedeki toplam − (arka plan × piksel sayısı). Sonuç mJy'ye çevrilir; belirsizlik VARIANCE bölümünden gelir.",
   "Merkezdeki pikseller maskeliyse nokta “good = False” olarak işaretlenir.",
   "<b>Doymuş yıldızlar:</b> merkez piksel dolmuşsa ölçüm yıldızın doymamış kanatlarından (1,5–5 piksel) yapılır. Bu mutlak akı vermez ama göreli ışık eğrisi için güvenilirdir.",
   "Her ölçüm o pikselin dalga boyuyla birlikte döner; tayfın bir noktası böyle oluşur.")

# ------------------------------------------------------------------ 4
H1("4. backend/pipeline.py: iş akışı ve önbellek")
PY(PL, "job_key")
PY(PL, "cached_result")
P("Her isteğin parametreleri (yuvarlanmış koordinat, görüş alanı, işlem sürümü…) bir anahtara çevrilir. "
  "Sonuç <code>data/results/&lt;anahtar&gt;.json</code> dosyasına yazılır; aynı istek tekrar gelirse dosyadan okunur. "
  "<code>PIPELINE_VERSION</code> artırılırsa tüm anahtarlar değişir ve eski sonuçlar yok sayılır.")
PY(PL, "cutouts_for")
P("Tıklanan bir noktanın tayfını ölçmek için ham kesitler gerekir. Son 4 alanın kesitleri bellekte tutulur; "
  "bellekte yoksa diskteki önbellekten yeniden okunur.")
PY(PL, "spectrum_and_lightcurve")
UL("Her kesitte fotometri yapılır. Hedef hareketliyse her ziyaret için o tarihteki konumu kullanılır.",
   "Noktalar dalga boyuna göre sıralanır: bu tayftır.",
   "Işık eğrisi: her (ziyaret, dedektör) için iyi noktaların medyanı. Belirsizlik, medyanın standart hatasıdır (1,253 × sapma / √n).")
PY(PL, "run_frames_job")
P("Tüm adımları sırayla çağıran ana fonksiyon. Dikkat edilecek noktalar:")
UL("Alan, hedefin 2025.9'daki konumuna ortalanır; hızlı cisimler katalogdaki eski konumlarında aranmaz.",
   "İndirilemeyen ve geçici olay sayısı çok yüksek kareler sayılarak ayrılır; bu sayılar arayüzdeki veri kalitesi notlarında görünür.",
   "Sonuç sözlüğü: ızgara bilgisi (<code>grid</code>), ziyaretler ve her birinde hedefin konumu (<code>epochs</code>), kareler (<code>frames</code>, base64 kodlu float32), kullanılan görüntüler, istatistikler, tayf noktaları ve ışık eğrisi.")

# ------------------------------------------------------------------ 5
H1("5. backend/catalogs.py: isimler, öz hareket, Gaia, asteroitler")
PY(CT, "propagate")
P("Bir konumu öz hareketiyle başka bir yıla taşır. 3,6 milyon, mili-yay saniyesini dereceye çevirir. "
  "RA'da <code>cos(dec)</code>'e bölünür, çünkü kutuplara yaklaştıkça RA çizgileri sıklaşır.")
PY(CT, "resolve")
P("İsim çözümleme üç basamaklıdır: önce yerleşik hedefler (<code>targets.json</code>), sonra SIMBAD'ın Harvard kopyası, sonra CDS Sesame. "
  "Hiçbir servis yanıt vermezse <code>ResolverDown</code> hatası atılır; servis yanıt verdi ama isim yoksa <code>None</code> döner. "
  "Bu ayrım 14 Kasım'da eklendi (bkz. Bölüm 9).")
PY(CT, "gaia_sources")
P("Alandaki Gaia DR3 yıldızları önce ESA arşivinden, olmazsa MAST'tan çekilir. Gaia konumları 2016.0 yılına aittir; "
  "her yıldız, her ziyaretin tarihine <code>propagate</code> ile taşınır. Arayüz bunları daire olarak çizer ve "
  "“hedefin yerinde Gaia yıldızı var mı” sorusunu yanıtlar.")
PY(CT, "known_small_bodies", head=14)
P("JPL'in servisi, verilen tarihte verilen alanda bulunan bilinen asteroit ve kuyruklu yıldızları döndürür. "
  "Böylece hareket eden bir nokta görüldüğünde “bu zaten bilinen bir asteroit mi” kontrol edilebilir.")

# ------------------------------------------------------------------ 6
H1("6. backend/moving.py: Güneş Sistemi cismi modu")
P("Asteroitler ve kuyruklu yıldızlar o kadar hızlı hareket eder ki sabit bir gökyüzü karesinde kalmazlar. "
  "Bu modda mantık tersine çevrilir: her kare cismin o anki konumuna ortalanır; cisim ortada sabit durur, yıldızlar akar.")
PY(MV, "most_query", head=22)
P("IRSA'nın MOST aracı cismin yörüngesini hesaplar ve onu içeren SPHEREx görüntülerini, her görüntüde cismin konumuyla birlikte listeler. "
  "İsim birden çok cisimle eşleşirse <code>AmbiguousName</code> atılır ve arayüz “bunu mu demek istediniz” seçenekleri gösterir.")
RNG(MV, r"^def run_moving_job", r"progress\(\"process\", 1, 1")
P("Sabit alan modundan farkı: her görüntü ayrı bir karedir (birleştirme yok) ve her kare için ızgara, cismin o andaki konumuna göre yeniden kurulur. "
  "Arayüzdeki “Stack” modu bu kareleri üst üste koyunca cisim birikir, yıldızlar bulanıklaşır.")

# ------------------------------------------------------------------ 7
H1("7. backend/main.py: web sunucusu")
RNG(MN, r"^app = FastAPI", r"^EXECUTOR")
RNG(MN, r"^class FramesRequest", r"name: str \| None = None")
P("<code>FramesRequest</code>, gelen isteğin biçimini ve sınırlarını tanımlar (örneğin görüş alanı 1–20 yay dakikası). "
  "Sınır dışı bir değer gelirse FastAPI isteği kendiliğinden reddeder.")
PY(MN, "_run")
PY(MN, "frames")
P("Yükleme dakikalar sürebildiği için istek hemen yanıtlanır. Tam sonuç ya da istenen önizleme önbellekteyse “done” ve anahtar döner. "
  "Değilse iş, en fazla 2 işi aynı anda çalıştıran bir havuza verilir ve bir iş numarası döner. "
  "<code>JOBS</code> sözlüğü işlerin durumunu tutar; birden çok iş parçacığı yazdığı için kilitle korunur.")
PY(MN, "job")
PY(MN, "spectrum")
P("Kalan adresler ince sarmalayıcılardır: <code>/api/targets</code>, <code>/api/resolve</code>, <code>/api/moving</code>, "
  "<code>/api/result</code>, <code>/api/gaia</code>, <code>/api/asteroids</code>. Son satır <code>frontend/</code> klasörünü olduğu gibi sunar.")

# ------------------------------------------------------------------ 8
H1("8. Arayüz: index.html, style.css, app.js")
P("<code>index.html</code> yalnızca iskelettir: üstte arama çubuğu ve hazır hedef düğmeleri, ortada iki üst üste tuval "
  "(<code>#img</code> görüntü için, <code>#overlay</code> işaretler için), altında kontroller, yanda tayf, ışık eğrisi ve notlar. "
  "Grafikleri Plotly, gökyüzü bağlam haritasını Aladin Lite çizer. Tüm mantık <code>app.js</code>'tedir.")
H2("8.1 Durum nesnesi")
RNG(AJ, r"^const S = \{", r"^\};")
P("Arayüzün hatırladığı her şey tek nesnededir: son sonuç, normalize edilmiş kareler (<code>z</code>), gösterilen ziyaret (<code>cur</code>), "
  "mod, seçili dedektörler, Gaia ve asteroit verisi, otomatik ipuçları.")
H2("8.2 Girdi ve sunucu çağrıları")
JS(AJ, "parseCoords")
P("Metin iki ondalık sayıysa derece olarak alınır. Değilse saat:dakika:saniye ve derece:dakika:saniye biçimi denenir; "
  "RA saatten dereceye 15 ile çarpılarak çevrilir. Hiçbiri uymazsa <code>null</code> döner ve metin isim sayılır.")
JS(AJ, "api")
JS(AJ, "decodeF32")
P("Kareler sunucudan metin (base64) olarak gelir; <code>decodeF32</code> bunları tekrar sayı dizisine çevirir.")
H2("8.3 Koordinat dönüşümü")
JS(AJ, "world2pix")
JS(AJ, "pix2world")
P("Sunucudaki ızgaranın aynısı tarayıcıda da hesaplanır (teğet düzlem izdüşümü). Böylece Gaia yıldızları ve hedef izi doğru piksele çizilir, "
  "fare tıklaması da gökyüzü koordinatına çevrilir.")
H2("8.4 Kareleri hazırlama")
JS(AJ, "normaliseFrames")
P("Her kareden medyanı çıkarılır ve kare kendi gürültüsüne (MAD × 1,4826) bölünür. Sonuç “gürültünün kaç katı” birimindedir; "
  "farklı dedektörler ve ziyaretler böylece karşılaştırılabilir olur.")
JS(AJ, "composite")
P("Seçili dedektörlerin kareleri toplanır ve katkı veren dedektör sayısının kareköküne bölünür; gürültü yine 1 birim kalır.")
JS(AJ, "rebuildDisplay", head=32)
UL("<b>Blink:</b> her ziyaretin birleşik karesi olduğu gibi.",
   "<b>Difference:</b> her ziyaret eksi diğer ziyaretlerin medyanı. Sabit yıldızlar silinir, hareket eden cisim iz bırakır.",
   "<b>Colour:</b> üç kanal: kırmızı D5+D6, yeşil D3+D4, mavi D1+D2.",
   "<b>D6−D4:</b> uzun dalga boyu eksi 3,3 µm metan bandı; soğuk kahverengi cüceler öne çıkar.",
   "<b>Stack:</b> tüm ziyaretlerin medyanı; en derin tek kare.")
H2("8.5 Çizim")
JS(AJ, "computeLimits")
JS(AJ, "stretch")
P("Siyah ve beyaz noktaları, piksel değerlerinin yüzdelik dilimlerinden seçilir. <code>stretch</code> değeri 0–1 arasına sıkıştırır ve "
  "asinh eğrisiyle sönük kaynakları görünür kılar. Fark modlarında sınırlar sıfır etrafında simetriktir.")
JS(AJ, "render", head=34)
P("Küçük bir gizli tuvale piksel piksel yazılır (y ekseni ters çevrilerek, çünkü görüntüde satır 0 alttadır), "
  "sonra yakınlaştırma oranına göre büyük tuvale kopyalanır. Yumuşatma kapalıdır; pikseller kare kare görünür.")
JS(AJ, "view")
JS(AJ, "toCanvas")
JS(AJ, "drawOverlay", head=20)
P("İşaret katmanı ayrı bir tuvaldir: ilk ziyareti belirten kesikli çerçeve, Gaia yıldızları (hızlı olanlar ok ile), asteroitler, "
  "hedefin tahmini izi, otomatik ipuçları, kayıtlı adaylar ve tıklanan nokta.")
H2("8.6 Oynatma ve yükleme")
JS(AJ, "play")
JS(AJ, "fetchResult")
P("<code>fetchResult</code> isteği gönderir ve iş bitene kadar 1,5 saniyede bir durumu sorar. <code>token</code>, kullanıcı bu sırada başka bir hedef "
  "yüklerse eski isteğin sonucunun ekrana yazılmasını engeller.")
JS(AJ, "runJob", head=11)
JS(AJ, "upgradeToFull")
P("<b>Önce önizleme, sonra tam sürüm.</b> Yeni bir alan için arayüz önce <code>preview: true</code> ile ister. Sunucu bu durumda ziyaret ve dedektör başına "
  "8 yerine 3 görüntü indirir (<code>PREVIEW_PER_CELL</code>); bu 3 görüntü tam sürümün seçeceği 8 görüntünün içinden alınır, yani tam sürüm onları yeniden indirmez. "
  "Önizleme ekrana gelince <code>upgradeToFull</code> tam sürümü arka planda ister ve hazır olunca aynı ziyarette kalarak yerine koyar. "
  "Tam sonuç zaten önbellekteyse sunucu doğrudan onu döndürür ve önizleme hiç görünmez.")
RNG(PL, r"chosen = sx.budget_select\(records", r"chosen = sx.budget_select\(chosen")
JS(AJ, "onResult")
H2("8.7 Öz hareketi SPHEREx'ten ölçme")
JS(AJ, "measureMotion", head=32)
P("Her ziyarette hedefin tahmini konumu etrafındaki en parlak piksel bulunur ve çevresindeki ışığın ağırlık merkezi alınır. "
  "Bu konumlara zamana karşı doğru uydurulur; eğim, yıllık harekettir. WISE 0855 için 7,7 ± 0,5″/yıl ölçülür (katalog 8,1).")
H2("8.8 Adres çubuğunda durum")
JS(AJ, "setHash")
JS(AJ, "initFromHash")
P("Her ayar adresin <code>#</code> sonrasına yazılır; adresi açan kişi aynı görünümü görür. Sayfa açılırken bu kısım okunur ve uygulanır.")

# ------------------------------------------------------------------ 9
H1("9. 14 Kasım'da eklenen özellikler")
H2("9.1 Hatalı giriş uyarısı ve biçim rehberi")
JS(AJ, "inputHelp")
JS(AJ, "submitQuery")
UL("Koordinat ayrıştırıldı ama dakika/saniye 60'ı aşıyorsa ya da RA/Dec gökyüzü dışındaysa ayrı ayrı mesaj verilir.",
   "Metinde hiç harf yoksa (örneğin tek bir sayı) “eksik konum” denir; isim servisine boşuna gidilmez.",
   "İsim bulunamazsa sunucunun mesajı gösterilir.",
   "Her durumda kabul edilen biçimler tıklanabilir örneklerle listelenir. <code>esc</code>, kullanıcının yazdığı metnin sayfaya HTML olarak karışmasını engeller.")
H2("9.2 İsim çözümlemede yedek servis")
PY(CT, "_simbad_harvard")
P("CDS'in Strazburg'daki sunucuları kapalıyken eski kod her ismi “bulunamadı” diye reddediyordu. Harvard'daki SIMBAD kopyasına küçük bir betik gönderilir; "
  "yanıt <code>RA Dec|pmRA pmDec</code> biçiminde tek satırdır. İsim tek satıra indirilir ki betiğe başka komut karışmasın. "
  "Sunucu tarafında “servis kapalı” 503, “isim yok” 404 olarak döner.")
RNG(MN, r"^@app.get\(\"/api/resolve\"\)", r"^    return r")
H2("9.3 Otomatik değişim ipucu")
RNG(AJ, r"^// Thresholds tuned", r"^const DETECT_FRACTION")
JS(AJ, "detectChanges")
UL("Her ziyaret için fark karesi hesaplanır: o ziyaret eksi diğerlerinin medyanı.",
   "Fark karesinin gürültüsü sağlam bir yöntemle (MAD) ölçülür.",
   "Bir piksel iki koşulu birden sağlamalıdır: gürültünün 7 katını aşmalı ve kaynağın kendi parlaklığının en az %35'i kadar olmalı. İkinci koşul, sabit parlak yıldızların küçük kalıntılarını eler.",
   "Piksel, 3×3 komşuluğunda en yüksek olmalı ve en az bir komşusu da belirgin olmalıdır. Gerçek bir yıldızın ışığı komşu piksele taşar; kozmik ışın tek pikselde kalır.",
   "Bulunanlar güce göre sıralanır; daha güçlü birine 5 pikselden yakın olanlar atılır, ziyaret başına en fazla 5 tanesi tutulur.")
JS(AJ, "gaiaNear")
P("İşaretin 4 yay saniyesi yakınında Gaia yıldızı yoksa kutu düz çizgiyle çizilir ve “no Gaia” yazılır: optikte görünmeyen, hareket eden bir kaynak "
  "kahverengi cüce adayıdır.")
NOTE("Sınır: bu bir ipucudur, dedektör değildir. WISE 0855'i yalnızca son ziyarette işaretler; doymuş yıldızların çevresindeki kalıntıları da kutuya alır.")
H2("9.4 Aday listesi")
JS(AJ, "addCandidate")
JS(AJ, "downloadCands")
P("Tıklanan nokta (ya da hiçbir yere tıklanmadıysa hedef), o anki ziyaret tarihi, mod, dedektörler ve Gaia eşleşmesiyle birlikte tarayıcının "
  "yerel deposuna (<code>localStorage</code>) yazılır. Her adayın, o konuma ortalanmış görünümü açan bir linki vardır. "
  "CSV dosyası tarayıcıda üretilir; sunucuya hiçbir şey gönderilmez.")
H2("9.5 Paylaşma ve gömülü mod")
JS(AJ, "viewUrl")
JS(AJ, "share")
RNG(CS, r"embed=1: only the viewer", r"body.embed .layout")
P("Adreste <code>embed=1</code> varsa <code>body</code>'ye <code>embed</code> sınıfı eklenir ve bu CSS kuralları başlığı, yan panelleri ve ek kontrolleri gizler. "
  "“Copy embed code” düğmesi, bu adresi içeren hazır bir <code>&lt;iframe&gt;</code> kodu verir.")
H2("9.6 Küçük eklemeler")
UL("<b>Latest image rozeti:</b> alandaki en yeni görüntünün tarihi.",
   "<b>hashchange dinleyicisi:</b> aday linkine tıklanınca sayfa yeniden yüklenmeden o görünüm açılır.",
   "<b>Telefon düzeni:</b> rozetler artık alt alta dizilir ve satır kırar; önceden sağdan kesiliyordu.",
   "<b>README:</b> yeni veri sürümünden sonra önbelleğin nasıl yenileneceğini anlatan bölüm.")

# ------------------------------------------------------------------ 10
H1("10. Diğer dosyalar")
RNG("backend/targets.json", r'"id": "wise0855"', r'"note"')
P("Hazır hedeflerin konumu, öz hareketi ve bu değerlerin ait olduğu yıl. WISE 0855'in yılı 2010.5'tir; challenge'ın verdiği koordinat o yıla aittir.")
RNG("scripts/warm_cache.py", r"^fovs = ", r"FAILED")
P("Hazır hedefleri önceden hesaplayıp <code>data/results/</code> klasörüne yazar; demo sırasında bu hedefler anında açılır.")
RNG("render.yaml", r"^services:", r"value: ")
P("Render'a siteyi nasıl kuracağını ve başlatacağını söyler. <code>autoDeploy: true</code> olduğu için <code>main</code> dalına her gönderim canlı siteyi günceller.")

# ------------------------------------------------------------------ 11
H1("11. Bilinen sınırlar")
UL("Yeni bir alanın ilk yüklemesi 1–4 dakika sürer; süre IRSA'nın yoğunluğuna bağlıdır.",
   "Çok parlak yıldızlar doymuştur: tayfları yaklaşık, ışık eğrileri yalnızca görelidir.",
   "Aynı dedektörde bile dalga boyu pozlamadan pozlamaya değişir; tek tek noktaların parlaklığı doğrudan karşılaştırılamaz.",
   "Otomatik ipucu beş demo alanında ayarlanmıştır; başka alanlarda yanlış alarm oranı ölçülmedi.",
   "Aday listesi yalnızca o tarayıcıda durur; tarayıcı verisi silinirse kaybolur.",
   "Kaydedilmiş alanlar kendiliğinden yenilenmez; yeni veri için önbelleğin silinmesi gerekir.")

CSS = """
@page { size: A4; margin: 16mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.2pt; line-height: 1.5; color: #1b2330; }
h1 { font-size: 17pt; color: #0b3a66; border-bottom: 2px solid #0b3a66; padding-bottom: 3px; margin: 26px 0 10px; page-break-after: avoid; }
h2 { font-size: 12.5pt; color: #0b3a66; margin: 18px 0 6px; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 14px 0 4px; page-break-after: avoid; }
p { margin: 6px 0; } ul { margin: 6px 0 8px; padding-left: 20px; } li { margin-bottom: 3px; }
code { font-family: Consolas, monospace; font-size: 9.2pt; background: #eef2f7; padding: 0 3px; border-radius: 3px; }
.code { margin: 8px 0 10px; border: 1px solid #c9d3df; border-radius: 5px; overflow: hidden; }
.cap { background: #0b3a66; color: #fff; font: 8.3pt Consolas, monospace; padding: 3px 8px; }
pre { margin: 0; padding: 7px 9px; background: #f6f8fb; font: 7.9pt/1.38 Consolas, monospace; white-space: pre-wrap; word-break: break-word; }
.more { font-size: 8.3pt; color: #5b6878; padding: 2px 9px 4px; background: #f6f8fb; font-style: italic; }
.note { background: #fff6e0; border-left: 4px solid #e0a020; padding: 6px 10px; }
.cover { padding: 60px 0 30px; page-break-after: always; }
.kicker { color: #5b6878; letter-spacing: .5px; font-size: 10pt; }
.title { font-size: 32pt; font-weight: 700; color: #0b3a66; margin: 8px 0 2px; }
.sub { font-size: 14pt; color: #33465c; margin-bottom: 26px; }
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(f"<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>SPHEREx Time Machine: Kod Anlatımı</title>"
               f"<style>{CSS}</style></head><body>{''.join(parts)}</body></html>", encoding="utf-8")
print(f"Wrote {OUT} ({sum(1 for p in parts if p.startswith('<div class=' + chr(34) + 'code'))} code blocks)")
