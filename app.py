import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import streamlit.components.v1 as components
import tempfile
import os
import io
import random

# ── SAYFA AYARI ───────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Project TrustGraph", page_icon="🛡️")

# ── KURUMSAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f0f2f6; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .stTabs [data-baseweb="tab-list"] { background: #1a2342; border-radius: 10px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { color: #aab4d4; font-weight: 500; border-radius: 8px; padding: 8px 20px; }
    .stTabs [aria-selected="true"] { background: #2563eb !important; color: white !important; }
    .metric-card { background: white; border-radius: 12px; padding: 18px 22px; border-left: 5px solid #2563eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 12px; }
    .metric-card.danger  { border-left-color: #e74c3c; }
    .metric-card.warning { border-left-color: #f39c12; }
    .metric-card.success { border-left-color: #27ae60; }
    .metric-card.purple  { border-left-color: #8b5cf6; }
    .metric-title { font-size: 12px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 28px; font-weight: 700; color: #1a2342; margin-top: 4px; }
    .metric-sub   { font-size: 12px; color: #9ca3af; margin-top: 2px; }
    .section-header { font-size: 15px; font-weight: 700; color: #1a2342;
        border-bottom: 2px solid #2563eb; padding-bottom: 6px; margin-bottom: 16px; margin-top: 20px; }
    .header-banner { background: linear-gradient(135deg, #1a2342 0%, #2563eb 100%);
        border-radius: 14px; padding: 22px 28px; color: white; margin-bottom: 20px; }
    .header-banner h1 { font-size: 22px; font-weight: 700; margin: 0; }
    .header-banner p  { font-size: 13px; opacity: 0.8; margin: 4px 0 0; }
    .xai-card { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border-radius: 12px; padding: 20px 24px; color: white; margin: 16px 0; }
    .xai-card h4 { font-size: 14px; font-weight: 700; margin: 0 0 10px 0;
        color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.05em; }
    .xai-card p  { font-size: 13px; line-height: 1.7; margin: 0; color: #e0e7ff; }
    .xai-path { background: rgba(255,255,255,0.1); border-radius: 8px;
        padding: 10px 14px; margin-top: 12px; font-size: 12px; color: #c7d2fe; }
    .hop2-badge { display: inline-block; background: #7c3aed; color: white;
        font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 10px;
        margin-left: 6px; vertical-align: middle; }
    .systemic-badge { display: inline-block; background: #dc2626; color: white;
        font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 10px;
        margin-left: 6px; vertical-align: middle; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
  <h1>🛡️ Project TrustGraph &nbsp;|&nbsp; B2B Risk &amp; Pazarlama Yönetimi Platformu</h1>
  <p>2-Hop GNN Bulaşma Simülasyonu · Sistemik Aktör Stres Testi · XAI Karar Gerekçesi · Kurumsal Bankacılık İstihbarat Platformu</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VERİ ÜRETİCİ — 100 firma/sektör
# ══════════════════════════════════════════════════════════════════════════════
random.seed(42)

SEHIRLER = [
    "İstanbul","Ankara","İzmir","Bursa","Antalya","Adana","Konya","Gaziantep",
    "Mersin","Kayseri","Eskişehir","Trabzon","Samsun","Denizli","Malatya",
    "Kocaeli","Diyarbakır","Şanlıurfa","Manisa","Balıkesir"
]
KELIMELER = [
    "Anadolu","Karadeniz","Ege","Marmara","Akdeniz","Boğaz","Tuna","Fırat",
    "Dicle","Kızılırmak","Sakarya","Gediz","Menderes","Yeşilırmak","Çoruh",
    "Atlas","Doruk","Zirve","Tepe","Yıldız","Güneş","Deniz","Dağ","Ova",
    "Altın","Gümüş","Demir","Bakır","Çelik","Taş","Kaya","Orman","Bağ",
    "Türk","Global","Inter","Trans","Meta","Neo","Pro","Max","Prime",
    "Elit","Prestij","Lider","Öncü","Güç","Vizyon","Misyon","Kıvılcım","Pınar",
    "Şahin","Kartal","Aslan","Doğan","Bozkurt","Selçuk","Osmanlı","Fatih",
    "Yavuz","Kanuni","Alparslan","Malazgirt","Çanakkale","Kurtuluş","Zafer",
    "Başak","Çiçek","Gül","Lale","Menekşe","Papatya","Sümbül","Zambak",
    "Mavi","Kırmızı","Yeşil","Sarı","Beyaz","Siyah","Mor","Turuncu",
    "Hızlı","Güvenli","Akıllı","Dijital","Modern","Klasik","Yeni","Güçlü",
    "Büyük","Küçük","Orta","Ulu","İnce","Geniş","Derin","Yüksek",
    "Birlik","Beraberlik","Dayanışma","Güven","Sadakat","Dürüstlük","Cesaret",
]
UNVANLAR = ["A.Ş.","Ltd. Şti.","San. A.Ş.","Tic. Ltd.","Holding A.Ş.","San. ve Tic. A.Ş.","Koll. Şti."]

SEKTORLER = {
    "İnşaat":    ("120", True),
    "Tekstil":   ("120", True),
    "Teknoloji": ("120", True),
    "Otomotiv":  ("120", True),
    "Kimya":     ("120", True),
    "Enerji":    ("120", True),
    "Sağlık":    ("120", True),
    "Tarım":     ("320", False),
    "Gıda":      ("320", False),
    "Lojistik":  ("320", False),
    "Perakende": ("320", False),
    "Turizm":    ("320", False),
    "Medya":     ("320", False),
    "Eğitim":    ("320", False),
}

SABIT_KAYITLAR = [
    ("101.01.001","Tahsil Edilecek Çekler Merkez",   "Finans",           250000.0,  0.0),
    ("101.01.002","Vadeli Çek Portföyü A",            "Finans",           180000.0,  0.0),
    ("101.01.003","Vadeli Çek Portföyü B",            "Finans",           320000.0,  0.0),
    ("102.01.001","Garanti Bankası Mevduatı",         "Finans",           400000.0,  0.0),
    ("102.01.002","Yapı Kredi Mevduatı",              "Finans",           290000.0,  0.0),
    ("102.01.003","Akbank TL Mevduatı",               "Finans",           510000.0,  0.0),
    ("335.01.001","Aylık Personel Maaşları",          "İnsan Kaynakları", 0.0,  350000.0),
    ("335.01.002","SGK Prim Ödemeleri",               "İnsan Kaynakları", 0.0,  120000.0),
    ("335.01.003","Kıdem Tazminatı Karşılığı",        "İnsan Kaynakları", 0.0,   95000.0),
    ("153.01.001","Depodaki Ticari Mallar A",         "Stok",             450000.0,  0.0),
    ("153.01.002","Hammadde Stok Ambarı",             "Stok",             330000.0,  0.0),
    ("153.01.003","Yarı Mamul Stok",                  "Stok",             210000.0,  0.0),
    ("601.01.001","AB İhracat Gelirleri",             "Dış Ticaret",      0.0,  550000.0),
    ("601.01.002","Orta Doğu İhracat Gelirleri",      "Dış Ticaret",      0.0,  380000.0),
    ("601.01.003","ABD İhracat Gelirleri",            "Dış Ticaret",      0.0,  270000.0),
]

# 2-Hop (dolaylı) tedarikçi/müşteri eşleme tablosu
# { 1.seviye_firma_adı: [(2.seviye_firma_adı, yön), ...] }
# yön: "supplier" = 2. seviye -> 1. seviye, "customer" = 1. seviye -> 2. seviye
HOP2_ESLEME = {
    "İstanbul Anadolu A.Ş.": [
        ("Beton Santrali Ltd.", "supplier"),
        ("Mermer Ocağı A.Ş.",   "supplier"),
    ],
    "Ankara Karadeniz Ltd. Şti.": [
        ("İplik Fabrikası A.Ş.", "supplier"),
    ],
    "İzmir Ege San. A.Ş.": [
        ("Soğuk Zincir Loj. Ltd.", "supplier"),
        ("Ambalaj Tek. A.Ş.",      "customer"),
    ],
    "Bursa Marmara Tic. Ltd.": [
        ("Plastik Kalıp San. A.Ş.", "supplier"),
    ],
    "Antalya Akdeniz Holding A.Ş.": [
        ("Güneş Enerji Sistemleri Ltd.", "supplier"),
        ("Tarım İlaçları Dağ. A.Ş.",     "customer"),
    ],
}

def build_default_mizan():
    rows = []
    gidx = 1
    for sektor, (prefix, borc_mu) in SEKTORLER.items():
        for i in range(100):
            sehir  = SEHIRLER[i % len(SEHIRLER)]
            kelime = KELIMELER[gidx % len(KELIMELER)]
            unvan  = UNVANLAR[i % len(UNVANLAR)]
            firma  = f"{sehir} {kelime} {unvan}"
            hkod   = f"{prefix}.{(gidx // 100)+1:02d}.{(gidx % 100)+1:03d}"
            buyukluk = random.choices(["k","o","b"], weights=[50,35,15])[0]
            if buyukluk == "k":
                tutar = round(random.uniform(50_000,     500_000), -3)
            elif buyukluk == "o":
                tutar = round(random.uniform(500_000,  5_000_000), -3)
            else:
                tutar = round(random.uniform(5_000_000,50_000_000),-3)
            borc, alacak = (tutar, 0.0) if borc_mu else (0.0, tutar)
            rows.append((hkod, firma, sektor, borc, alacak))
            gidx += 1
    for r in SABIT_KAYITLAR:
        rows.append(r)
    df = pd.DataFrame(rows, columns=["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"])
    return df

# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════
AKTIF_PREFIXLER = ("101","102","120","150","153")
PASIF_PREFIXLER = ("103","300","320","335","600","601")

def hesapla_bakiye(row):
    prefix = str(row["Hesap_Kodu"]).split(".")[0]
    if prefix in AKTIF_PREFIXLER:
        return abs(row["Borc_Toplam"] - row["Alacak_Toplam"])
    elif prefix in PASIF_PREFIXLER:
        return abs(row["Alacak_Toplam"] - row["Borc_Toplam"])
    return abs(row["Borc_Toplam"] - row["Alacak_Toplam"])

def ensure_kolonlar(df):
    if "Bakiye" not in df.columns:
        df["Bakiye"] = df.apply(hesapla_bakiye, axis=1)
    if "Islem_Hacmi" not in df.columns:
        df["Islem_Hacmi"] = df["Borc_Toplam"] + df["Alacak_Toplam"]
    return df

def segmentle(ciro):
    if ciro >= 5_000_000:   return "Ticari"
    elif ciro >= 2_000_000: return "Orta KOBİ"
    return "Mikro KOBİ"

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE — İLK YÜKLEME
# ══════════════════════════════════════════════════════════════════════════════
if "mizan_data" not in st.session_state:
    raw = build_default_mizan()
    st.session_state.mizan_data = ensure_kolonlar(raw)

# ── init_istihbarat: Hacme göre sıralı Top-N (A) ─────────────────────────────
def init_istihbarat(mizan_df, n=10):
    random.seed(99)
    # A) Önce Islem_Hacmi garantisi, sonra büyükten küçüğe sırala, ilk N'i al
    _df = ensure_kolonlar(mizan_df.copy())
    firmalar = (
        _df[_df["Hesap_Kodu"].str.startswith(("120","320"))]
        .sort_values(by="Islem_Hacmi", ascending=False)
        .head(n)
        .copy()
    )
    n_actual = len(firmalar)
    tkn_list     = [random.randint(400, 1000) for _ in range(n_actual)]
    tbe_list     = [random.randint(10,  90)   for _ in range(n_actual)]
    medya_list   = [random.randint(0,   80)   for _ in range(n_actual)]
    dbs_list     = [random.choice([True, False]) for _ in range(n_actual)]
    musteri_list = [random.choice([True, False]) for _ in range(n_actual)]
    ciro_list    = [random.randint(500_000, 20_000_000) for _ in range(n_actual)]
    pos_list     = [random.randint(10_000,    500_000)  for _ in range(n_actual)]
    # Sistemik Aktör: ilk 2 firma otomatik True, geri kalanı rastgele
    sistemik_list = [True if i < 2 else random.choice([True, False]) for i in range(n_actual)]
    return pd.DataFrame({
        "Cari Unvanı":                    firmalar["Cari_Unvan"].values,
        "KKB Ticari Kredi Notu (TKN)":    tkn_list,
        "Ticari Borçluluk Endeksi (TBE)": tbe_list,
        "Medya/Haber Olumsuzluk Skoru":   medya_list,
        "DBS Anchor Bayi mi?":            dbs_list,
        "Bankamız Müşterisi mi?":         musteri_list,
        "Yıllık Ciro (TL)":               ciro_list,
        "POS Aylık Ciro (TL)":            pos_list,
        "Sistemik Aktör mü? (Sektör Devi)": sistemik_list,
    })

if "istihbarat" not in st.session_state:
    st.session_state.istihbarat = init_istihbarat(st.session_state.mizan_data)

# ══════════════════════════════════════════════════════════════════════════════
# SOL PANEL
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## ⚙️ Platform Kontrol Paneli")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Kurumsal Mizan Yükle")
uploaded = st.sidebar.file_uploader("Excel (.xlsx) Mizan Dosyası", type=["xlsx"])
if uploaded:
    try:
        raw = pd.read_excel(uploaded)
        raw.columns = ["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"]
        raw = ensure_kolonlar(raw)
        st.session_state.mizan_data  = raw
        st.session_state.istihbarat  = init_istihbarat(raw)
        st.sidebar.success("✅ Mizan başarıyla yüklendi!")
    except Exception as e:
        st.sidebar.error(f"Dosya okunamadı: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Ekosistem Simülasyon Odası")

# Kolon güvenlik garantisi — her rerun'da çalışır
_raw = st.session_state.mizan_data.copy()
_gerekli = ["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"]
if not all(c in _raw.columns for c in _gerekli):
    _raw = build_default_mizan()
if "Bakiye" not in _raw.columns:
    _raw["Bakiye"] = _raw.apply(hesapla_bakiye, axis=1)
if "Islem_Hacmi" not in _raw.columns:
    _raw["Islem_Hacmi"] = _raw["Borc_Toplam"] + _raw["Alacak_Toplam"]
mizan_df = _raw
st.session_state.mizan_data = mizan_df.copy()

sectors = sorted(mizan_df["Sektor"].unique().tolist())
selected_sector = st.sidebar.selectbox("Krize Girecek Sektör:", ["(Seçilmedi)"] + sectors)
shock_intensity = st.sidebar.slider("Sektörel Kriz Şiddeti (%):", 0, 100, 0)
alpha           = st.sidebar.slider("Risk Bulaşma Katsayısı (α):", 0.1, 1.0, 0.5, 0.05)
st.sidebar.markdown("---")
n_slider = st.sidebar.slider("İstihbarat Matrisi Satır Sayısı (N):", 5, 50, 10)

# ══════════════════════════════════════════════════════════════════════════════
# GELİŞMİŞ RİSK HESAPLAMA MOTORU — Sistemik Aktör γ çarpanı ile (B)
# ══════════════════════════════════════════════════════════════════════════════
total_hacim = mizan_df["Islem_Hacmi"].sum() or 1.0

# İstihbarat tablosundan Sistemik Aktör bilgisini çek
ist_ref = st.session_state.istihbarat.copy()
sistemik_set = set()
if "Sistemik Aktör mü? (Sektör Devi)" in ist_ref.columns:
    sistemik_set = set(
        ist_ref.loc[ist_ref["Sistemik Aktör mü? (Sektör Devi)"] == True, "Cari Unvanı"].tolist()
    )

# Partner bazında kendi riski hesapla
partner_risks = {}
for _, row in mizan_df.iterrows():
    base = 15.0
    if row["Sektor"] == selected_sector:
        base = float(shock_intensity)
    partner_risks[row["Cari_Unvan"]] = base

# R_bulaşma = α × Σ ( R_own(j) × γ_j × V_j / V_total )
bulaşma_detay = []
for _, row in mizan_df.iterrows():
    firma = row["Cari_Unvan"]
    r_own = partner_risks[firma]
    gamma = 2.0 if firma in sistemik_set else 1.0
    v_j   = row["Islem_Hacmi"]
    katki = r_own * gamma * (v_j / total_hacim)
    bulaşma_detay.append({
        "firma": firma,
        "sektor": row["Sektor"],
        "r_own": r_own,
        "gamma": gamma,
        "v_j": v_j,
        "katki": katki,
        "hesap_kodu": str(row["Hesap_Kodu"]),
    })

bulaşma_toplam = sum(d["katki"] for d in bulaşma_detay) * alpha
merkez_risk    = min(round(bulaşma_toplam, 1), 100.0)

# En baskın risk kaynağını bul (XAI için)
bulaşma_detay_sorted = sorted(bulaşma_detay, key=lambda x: x["katki"], reverse=True)
top_risk_firma  = bulaşma_detay_sorted[0] if bulaşma_detay_sorted else None

# ══════════════════════════════════════════════════════════════════════════════
# SEKMELER
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🌐 İlişkisel Ekosistem ve Risk Simülatörü",
    "📊 Mizan Analiz ve İstihbarat Laboratuvarı",
    "🎯 Akıllı Pazarlama ve Çapraz Satış Portalı",
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEKME 1 — EKOSİSTEM GRAFİĞİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card_cls = "danger" if merkez_risk > 50 else ("warning" if merkez_risk > 20 else "success")
        st.markdown(f"""<div class="metric-card {card_cls}">
          <div class="metric-title">Merkez Firma Risk Endeksi</div>
          <div class="metric-value">%{merkez_risk}</div>
          <div class="metric-sub">2-Hop GNN · γ-Sistemik · α={alpha}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        partner_count = mizan_df[mizan_df["Hesap_Kodu"].str.startswith(("120","320"))].shape[0]
        st.markdown(f"""<div class="metric-card">
          <div class="metric-title">Aktif Partner Sayısı</div>
          <div class="metric-value">{partner_count:,}</div>
          <div class="metric-sub">Alıcı + Tedarikçi</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        etkilenen = mizan_df[mizan_df["Sektor"] == selected_sector].shape[0] if selected_sector != "(Seçilmedi)" else 0
        st.markdown(f"""<div class="metric-card {'warning' if etkilenen > 0 else ''}">
          <div class="metric-title">Şoktan Etkilenen Partner</div>
          <div class="metric-value">{etkilenen:,}</div>
          <div class="metric-sub">{selected_sector if selected_sector != '(Seçilmedi)' else 'Şok uygulanmadı'}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        sistemik_sayi = len(sistemik_set)
        st.markdown(f"""<div class="metric-card purple">
          <div class="metric-title">Sistemik Aktör (γ=2.0)</div>
          <div class="metric-value">{sistemik_sayi}</div>
          <div class="metric-sub">Sektör Devi · 2x Risk Çarpanı</div>
        </div>""", unsafe_allow_html=True)

    # ── GRAFİK (2-Hop NetworkX + PyVis) ─────────────────────────────────────
    st.markdown('<div class="section-header">🌐 Canlı 2-Hop B2B Ekosistem Grafik Haritası</div>', unsafe_allow_html=True)
    st.caption("Mor kenarlar 2. seviye (dolaylı) bağlantıları gösterir. Kırmızı halka = Sistemik Aktör. Grafik okunabilirlik için örneklenmiş 80 1.seviye partner içerir.")

    graf_df = mizan_df[mizan_df["Hesap_Kodu"].str.startswith(("120","320"))].reset_index(drop=True)
    if len(graf_df) > 80:
        n_sek = max(1, mizan_df["Sektor"].nunique())
        graf_df = (
            graf_df.groupby("Sektor", group_keys=False)
            .apply(lambda x: x.sample(min(len(x), max(1, 80 // n_sek)), random_state=42))
            .reset_index(drop=True)
            .head(80)
        )

    G = nx.DiGraph()
    main_firm = "Merkez_Firma_A"
    merkez_color = "#e74c3c" if merkez_risk > 50 else ("#f39c12" if merkez_risk > 20 else "#2c3e50")
    G.add_node(main_firm, size=42, color=merkez_color,
               title=f"<b>Merkez Firma A</b><br>Bulaşan Risk: <b>%{merkez_risk}</b><br>α={alpha} · 2-Hop GNN")

    max_hacim = graf_df["Islem_Hacmi"].max() or 1.0

    for _, row in graf_df.iterrows():
        name  = row["Cari_Unvan"]
        risk  = partner_risks.get(name, 15.0)
        gamma = 2.0 if name in sistemik_set else 1.0
        cpct  = round(row["Islem_Hacmi"] / total_hacim * 100, 2)
        size  = 12 + int((row["Islem_Hacmi"] / max_hacim) * 22)

        # Sistemik aktörler daha büyük ve kırmızı çerçeveli
        if name in sistemik_set:
            color = "#dc2626"
            size  = max(size, 24)
        elif risk > 60:
            color = "#e74c3c"
        elif risk > 30:
            color = "#f39c12"
        else:
            color = "#27ae60"

        sistemik_label = " ⚠️ SİSTEMİK" if name in sistemik_set else ""
        tip = (f"<b>{name}</b>{sistemik_label}<br>Sektör: {row['Sektor']}<br>"
               f"Ciro Payı: %{cpct}<br>Risk: %{risk}<br>γ={gamma}")
        G.add_node(name, size=size, color=color, title=tip)

        # 1-Hop bağlantı
        if str(row["Hesap_Kodu"]).startswith("120"):
            G.add_edge(main_firm, name, color="#94a3b8", width=1)
        else:
            G.add_edge(name, main_firm, color="#94a3b8", width=1)

        # 2-Hop bağlantılar (B)
        if name in HOP2_ESLEME:
            for hop2_firma, yon in HOP2_ESLEME[name]:
                if hop2_firma not in G.nodes:
                    G.add_node(hop2_firma, size=10, color="#8b5cf6",
                               title=f"<b>{hop2_firma}</b><br><i>2. Seviye Dolaylı Bağlantı</i><br>→ {name}")
                if yon == "supplier":
                    G.add_edge(hop2_firma, name, color="#8b5cf6", width=1, dashes=True)
                else:
                    G.add_edge(name, hop2_firma, color="#8b5cf6", width=1, dashes=True)

    net = Network(height="540px", width="100%", bgcolor="#f8fafc", font_color="#1a2342", directed=True)
    for node, attrs in G.nodes(data=True):
        net.add_node(node, label=node, size=attrs["size"], color=attrs["color"], title=attrs["title"])
    for u, v, edata in G.edges(data=True):
        net.add_edge(u, v,
                     color=edata.get("color","#94a3b8"),
                     width=edata.get("width", 1),
                     arrows="to",
                     dashes=edata.get("dashes", False))
    net.set_options("""
    var options = {
      "physics": { "barnesHut": {
          "gravitationalConstant": -18000,
          "centralGravity": 0.3,
          "springLength": 200,
          "springConstant": 0.04
      }, "minVelocity": 0.75 },
      "nodes": { "font": { "size": 11, "face": "Inter" } },
      "edges": { "smooth": { "type": "dynamic" } }
    }
    """)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        tmp_path = tmp.name
    net.save_graph(tmp_path)
    with open(tmp_path, "r", encoding="utf-8") as f:
        html_str = f.read()
    components.html(html_str, height=550)
    os.unlink(tmp_path)

    # ── XAI / GNNExplainer KARTI (C) ─────────────────────────────────────────
    st.markdown('<div class="section-header">🤖 GNNExplainer: Yapay Zeka Karar Gerekçesi</div>', unsafe_allow_html=True)

    if top_risk_firma is not None:
        tf       = top_risk_firma
        is_sist  = tf["firma"] in sistemik_set
        gamma_str = "γ=2.0 (Sistemik Aktör)" if is_sist else "γ=1.0"
        ciro_pct  = round(tf["v_j"] / total_hacim * 100, 1)
        katki_pct = round(tf["katki"] * alpha, 2)

        # 2-hop bilgisi
        hop2_text = ""
        if tf["firma"] in HOP2_ESLEME:
            hop2_isimler = ", ".join([f[0] for f in HOP2_ESLEME[tf["firma"]]])
            hop2_text = (f" Bu riskin dolaylı kaynağı olarak "
                         f"<b>{hop2_isimler}</b> 2. seviye bağlantıları tespit edilmiştir.")

        # Risk seviyesine göre uyarı rengi
        if merkez_risk > 40:
            xai_level = "🔴 KRİTİK RİSK SEVİYESİ"
            xai_color = "#7f1d1d"
        elif merkez_risk > 15:
            xai_level = "🟠 ORTA RİSK — YAKIN İZLEME"
            xai_color = "#78350f"
        else:
            xai_level = "🟢 DÜŞÜK RİSK — GÜVENLİ EKOSİSTEM"
            xai_color = "#14532d"

        xai_html = f"""
        <div class="xai-card">
          <h4>🤖 GNNExplainer — Dinamik Risk Yolu Analizi &nbsp;|&nbsp; {xai_level}</h4>
          <p>
            <b>Merkez Firma A'nın</b> ekosistem risk endeksi <b>%{merkez_risk}</b>'e ulaşmıştır.
            GNNExplainer Message Passing analizine göre, bu riskin <b>birincil nedeni</b>:
            <b>{tf['sektor']}</b> sektöründeki şoktan etkilenen
            {'<span style="background:#dc2626;color:white;padding:1px 7px;border-radius:8px;font-size:11px;font-weight:700;">⚠️ SİSTEMİK AKTÖR</span>' if is_sist else ''}
            <b>{tf['firma']}</b>'dır.
          </p>
          <div class="xai-path">
            📍 <b>Risk Yolu (Path):</b>
            {tf['firma']} → Merkez_Firma_A
            &nbsp;|&nbsp; Ciro Payı: <b>%{ciro_pct}</b>
            &nbsp;|&nbsp; Kendi Riski: <b>%{tf['r_own']:.0f}</b>
            &nbsp;|&nbsp; Çarpan: <b>{gamma_str}</b>
            &nbsp;|&nbsp; Merkez'e Net Katkı: <b>%{katki_pct}</b>
            {hop2_text}
          </div>
          <p style="margin-top:12px; font-size:12px; color:#a5b4fc;">
            📐 <b>Formül:</b> R_bulaşma = α × Σ( R_own(j) × γ_j × V_j / V_total )
            &nbsp;=&nbsp; {alpha} × Σ( R_own × γ × Ciro_Payı )
            &nbsp;=&nbsp; <b>%{merkez_risk}</b>
          </p>
        </div>
        """
        st.markdown(xai_html, unsafe_allow_html=True)
    else:
        st.info("Simülasyon parametrelerini güncelleyerek GNNExplainer analizini başlatın.")

    # ── KARAR DESTEK ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">💡 Yönetim Komitesi Karar Destek Çıktısı</div>', unsafe_allow_html=True)
    if merkez_risk > 40:
        st.error("⚠️ ACİL DURUM: Ekosistem risk seviyesi kritik eşiği aştı! Tedarikçi çeşitlendirmesi ve alacak sigortası önerilir.")
    elif merkez_risk > 15:
        st.warning("⚡ YAKIN İZLEME: Bulaşıcı risk artış eğiliminde. Portföy limit artışları askıya alınmalıdır.")
    else:
        st.success("✅ GÜVENLİ EKOSİSTEM: Ticari ağ yapısı sağlıklı. DBS ve çapraz satış kampanyaları başlatılabilir.")

    # ── SEKTÖR BAZLI ÖZET ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Sektör Bazlı Risk Özeti</div>', unsafe_allow_html=True)
    sektor_ozet = []
    for sek in sectors:
        sek_df    = mizan_df[mizan_df["Sektor"] == sek]
        sek_hacim = sek_df["Islem_Hacmi"].sum()
        sektor_ozet.append({
            "Sektör":            sek,
            "Firma Sayısı":      len(sek_df),
            "Toplam Hacim (TL)": int(sek_hacim),
            "Hacim Payı (%)":    round(sek_hacim / total_hacim * 100, 2),
            "Sektör Risk (%)":   float(shock_intensity) if sek == selected_sector else 15.0,
            "Sistemik Aktör":    "✅ Var" if any(f in sistemik_set for f in sek_df["Cari_Unvan"].tolist()) else "—",
        })
    st.dataframe(
        pd.DataFrame(sektor_ozet).sort_values("Toplam Hacim (TL)", ascending=False),
        use_container_width=True, hide_index=True
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEKME 2 — MİZAN LABORATUVARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown('<div class="section-header">📋 Tam Mizan Veri Seti (TDHP)</div>', unsafe_allow_html=True)
        fil_sektor = st.multiselect("Sektöre göre filtrele:", options=sectors, default=[])
        show_df = mizan_df.copy()
        if fil_sektor:
            show_df = show_df[show_df["Sektor"].isin(fil_sektor)]
        st.caption(f"Toplam {len(show_df):,} kayıt gösteriliyor.")
        disp = show_df[["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam","Bakiye","Islem_Hacmi"]].copy()
        disp.columns = ["Hesap Kodu","Cari Unvanı","Sektör","Borç (TL)","Alacak (TL)","Bakiye (TL)","İşlem Hacmi (TL)"]
        st.dataframe(disp.style.format({
            "Borç (TL)":        "{:,.0f}",
            "Alacak (TL)":      "{:,.0f}",
            "Bakiye (TL)":      "{:,.0f}",
            "İşlem Hacmi (TL)": "{:,.0f}",
        }), use_container_width=True, hide_index=True, height=420)

        aktif = mizan_df[mizan_df["Hesap_Kodu"].str.startswith(AKTIF_PREFIXLER)]["Bakiye"].sum()
        pasif = mizan_df[mizan_df["Hesap_Kodu"].str.startswith(PASIF_PREFIXLER)]["Bakiye"].sum()
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f"""<div class="metric-card success">
              <div class="metric-title">Toplam Aktif</div>
              <div class="metric-value">₺{aktif/1e6:.1f}M</div></div>""", unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""<div class="metric-card warning">
              <div class="metric-title">Toplam Pasif/Gelir</div>
              <div class="metric-value">₺{pasif/1e6:.1f}M</div></div>""", unsafe_allow_html=True)
        with mc3:
            net_val = aktif - pasif
            n_cls   = "success" if net_val >= 0 else "danger"
            st.markdown(f"""<div class="metric-card {n_cls}">
              <div class="metric-title">Net Bakiye</div>
              <div class="metric-value">₺{net_val/1e6:.1f}M</div></div>""", unsafe_allow_html=True)

    with col_r:
        st.markdown(f'<div class="section-header">🔬 İnteraktif İstihbarat Matrisi (Top-{n_slider} Hacim)</div>', unsafe_allow_html=True)
        st.caption("Firmalar işlem hacmine göre büyükten küçüğe sıralanmıştır. Tüm alanları düzenleyebilirsiniz.")

        # n_slider değişince matrisi yenile — session_state korunur, sadece n farklıysa yeniden üret
        if len(st.session_state.istihbarat) != n_slider:
            st.session_state.istihbarat = init_istihbarat(mizan_df, n=n_slider)

        edited = st.data_editor(
            st.session_state.istihbarat,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "Cari Unvanı":                       st.column_config.TextColumn(disabled=True),
                "KKB Ticari Kredi Notu (TKN)":       st.column_config.NumberColumn(min_value=0,  max_value=1000, step=1),
                "Ticari Borçluluk Endeksi (TBE)":    st.column_config.NumberColumn(min_value=0,  max_value=100,  step=1),
                "Medya/Haber Olumsuzluk Skoru":      st.column_config.NumberColumn(min_value=0,  max_value=100,  step=1),
                "DBS Anchor Bayi mi?":               st.column_config.CheckboxColumn(),
                "Bankamız Müşterisi mi?":            st.column_config.CheckboxColumn(),
                "Yıllık Ciro (TL)":                  st.column_config.NumberColumn(min_value=0, format="₺%d"),
                "POS Aylık Ciro (TL)":               st.column_config.NumberColumn(min_value=0, format="₺%d"),
                "Sistemik Aktör mü? (Sektör Devi)":  st.column_config.CheckboxColumn(
                    help="Sistemik Aktör işaretli firmalar risk bulaşma formülünde γ=2.0 çarpanıyla hesaba katılır."
                ),
            },
            key="ist_editor"
        )
        # Düzenlemeleri session_state'e kaydet
        st.session_state.istihbarat = edited

        st.markdown('<div class="section-header">📐 Q Skoru Önizlemesi</div>', unsafe_allow_html=True)
        preview = edited.copy()
        preview["Q Skoru"] = (
            0.6 * (preview["KKB Ticari Kredi Notu (TKN)"] / 1000) +
            0.4 * (1 - preview["Ticari Borçluluk Endeksi (TBE)"] / 100)
        ).round(3)
        preview["Kalite"] = preview["Q Skoru"].apply(
            lambda q: "🏆 Yüksek" if q >= 0.70 else ("⚠️ Orta" if q >= 0.50 else "🔴 Düşük")
        )
        preview["Sistemik"] = preview["Sistemik Aktör mü? (Sektör Devi)"].apply(
            lambda v: "⚠️ Sistemik" if v else "—"
        )
        st.dataframe(
            preview[["Cari Unvanı","Q Skoru","Kalite","Sistemik"]].sort_values("Q Skoru", ascending=False),
            use_container_width=True, hide_index=True
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEKME 3 — PAZARLAMA PORTALI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    ist = st.session_state.istihbarat.copy()
    mdf = st.session_state.mizan_data.copy()

    # ── MODÜL 1 ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🟢 Modül 1 — Yeni Müşteri Edinimi: Potansiyel Müşteri Fırsatları</div>', unsafe_allow_html=True)
    mod1 = ist[
        (~ist["Bankamız Müşterisi mi?"]) &
        (ist["KKB Ticari Kredi Notu (TKN)"] >= 700) &
        (ist["Ticari Borçluluk Endeksi (TBE)"] <= 40)
    ].copy()
    if mod1.empty:
        st.info("Kriterleri karşılayan potansiyel müşteri bulunamadı. İstihbarat matrisini güncelleyin.")
    else:
        mod1["Segment"] = mod1["Yıllık Ciro (TL)"].apply(segmentle)
        mod1["Aksiyon"] = "📣 Müşteri Kazanım Teklifi Gönder"
        st.dataframe(mod1[["Cari Unvanı","KKB Ticari Kredi Notu (TKN)","Ticari Borçluluk Endeksi (TBE)",
                            "Yıllık Ciro (TL)","POS Aylık Ciro (TL)","Segment","Aksiyon"]],
                     use_container_width=True, hide_index=True)

    # ── MODÜL 2 ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔵 Modül 2 — Alacak Kalitesi Ölçümü (120 Hesap Grubu)</div>', unsafe_allow_html=True)
    mod2 = ist.copy()
    mod2["Q_ar"] = (
        0.6 * (mod2["KKB Ticari Kredi Notu (TKN)"] / 1000) +
        0.4 * (1 - mod2["Ticari Borçluluk Endeksi (TBE)"] / 100)
    ).round(3)
    mod2["Kalite Etiketi"] = mod2["Q_ar"].apply(
        lambda q: "🏆 Yüksek Kaliteli Alacak" if q >= 0.70 else ("⚠️ Orta Risk" if q >= 0.50 else "🔴 Düşük Kalite")
    )
    st.dataframe(mod2[["Cari Unvanı","KKB Ticari Kredi Notu (TKN)","Ticari Borçluluk Endeksi (TBE)",
                        "Q_ar","Kalite Etiketi"]].sort_values("Q_ar", ascending=False),
                 use_container_width=True, hide_index=True)

    # ── MODÜL 3 ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🟠 Modül 3 — Tedarikçi Kalitesi ve DBS Kampanyası (320 Hesap Grubu)</div>', unsafe_allow_html=True)
    mod3 = ist.copy()
    mod3["Q_ap"] = (
        0.6 * (mod3["KKB Ticari Kredi Notu (TKN)"] / 1000) +
        0.4 * (1 - mod3["Ticari Borçluluk Endeksi (TBE)"] / 100)
    ).round(3)
    mod3["DBS Aksiyonu"] = mod3.apply(
        lambda r: "🚀 Sıcak DBS Kampanyası: Limit Artırımı"
        if (r["DBS Anchor Bayi mi?"] and r["Q_ap"] >= 0.75)
        else ("📋 DBS İzleme Listesi" if r["Q_ap"] >= 0.55 else "⛔ DBS Uygun Değil"),
        axis=1
    )
    st.dataframe(mod3[["Cari Unvanı","Q_ap","DBS Anchor Bayi mi?","DBS Aksiyonu"]]
                 .sort_values("Q_ap", ascending=False),
                 use_container_width=True, hide_index=True)

    # ── MODÜL 4 ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🎯 Modül 4 — Gelişmiş Çapraz Satış Tetikleyicileri (Kebir Hesap Analizi)</div>', unsafe_allow_html=True)
    triggers = []

    personel = mdf[mdf["Hesap_Kodu"].str.startswith("335")]["Bakiye"].sum()
    if personel > 200_000:
        triggers.append({"Hesap Grubu":"335 — Personel Maaşları",
            "Tespit":f"Yüksek maaş borcu: ₺{personel:,.0f}",
            "Öneri/Aksiyon":"💼 Maaş Ödemesi Protokolü Teklifi + Çalışanlara Bireysel Kredi/Kart Satışı",
            "Öncelik":"🔴 Yüksek"})

    cek_bakiye = mdf[mdf["Hesap_Kodu"].str.startswith("101")]["Bakiye"].sum()
    alan_120   = mdf[mdf["Hesap_Kodu"].str.startswith("120")]["Bakiye"].sum() or 1.0
    cek_oran   = cek_bakiye / alan_120
    if cek_oran > 0.30:
        triggers.append({"Hesap Grubu":"101 — Tahsil Edilecek Çekler",
            "Tespit":f"Çek portföyü oranı: %{cek_oran*100:.1f} (Eşik: %30)",
            "Öneri/Aksiyon":"✂️ Çek İskonto (Kırma) ve Tahsilat Finansmanı Teklifi",
            "Öncelik":"🟠 Orta"})

    rakip_mevduat = mdf[mdf["Hesap_Kodu"].str.startswith("102")]["Bakiye"].sum()
    if rakip_mevduat > 0:
        triggers.append({"Hesap Grubu":"102 — Diğer Banka Mevduatları",
            "Tespit":f"Rakip bankadaki mevduat: ₺{rakip_mevduat:,.0f}",
            "Öneri/Aksiyon":"🏦 Mevduat ve POS Payı Kapma Kampanyası",
            "Öncelik":"🟠 Orta"})

    stok = mdf[mdf["Hesap_Kodu"].str.startswith("153")]["Bakiye"].sum()
    if stok > 300_000:
        triggers.append({"Hesap Grubu":"153 — Depodaki Ticari Mallar",
            "Tespit":f"Yüksek stok hacmi: ₺{stok:,.0f}",
            "Öneri/Aksiyon":"📦 Stok Teminatlı İşletme Sermayesi Kredisi Önerisi",
            "Öncelik":"🟢 Standart"})

    ihracat      = mdf[mdf["Hesap_Kodu"].str.startswith("601")]["Bakiye"].sum()
    toplam_satis = mdf[mdf["Hesap_Kodu"].str.startswith(("600","601"))]["Bakiye"].sum() or 1.0
    ihracat_oran = ihracat / toplam_satis
    if ihracat_oran >= 0.20:
        triggers.append({"Hesap Grubu":"601 — Yurtdışı İhracat Gelirleri",
            "Tespit":f"İhracat odaklılık oranı: %{ihracat_oran*100:.1f} (Eşik: %20)",
            "Öneri/Aksiyon":"🌍 İhracat Akreditif Finansmanı + FX Forward Döviz Koruması",
            "Öncelik":"🔴 Yüksek"})

    if triggers:
        st.dataframe(pd.DataFrame(triggers), use_container_width=True, hide_index=True)
        tc1, tc2, tc3 = st.columns(3)
        yuksek = sum(1 for t in triggers if "Yüksek"   in t["Öncelik"])
        orta   = sum(1 for t in triggers if "Orta"     in t["Öncelik"])
        std    = sum(1 for t in triggers if "Standart" in t["Öncelik"])
        with tc1:
            st.markdown(f"""<div class="metric-card danger">
              <div class="metric-title">Yüksek Öncelikli Aksiyon</div>
              <div class="metric-value">{yuksek}</div></div>""", unsafe_allow_html=True)
        with tc2:
            st.markdown(f"""<div class="metric-card warning">
              <div class="metric-title">Orta Öncelikli Aksiyon</div>
              <div class="metric-value">{orta}</div></div>""", unsafe_allow_html=True)
        with tc3:
            st.markdown(f"""<div class="metric-card success">
              <div class="metric-title">Standart Aksiyon</div>
              <div class="metric-value">{std}</div></div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Şu anda aktif çapraz satış tetikleyicisi bulunmamaktadır.")

    # ── RAPOR İNDİR ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📥 Pazarlama Özet Raporu</div>', unsafe_allow_html=True)
    rapor_rows = []
    for _, r in ist.iterrows():
        q = round(0.6*(r["KKB Ticari Kredi Notu (TKN)"]/1000) + 0.4*(1-r["Ticari Borçluluk Endeksi (TBE)"]/100), 3)
        rapor_rows.append({
            "Firma":          r["Cari Unvanı"],
            "Müşteri mi?":    "Evet" if r["Bankamız Müşterisi mi?"] else "Hayır",
            "DBS Bayi mi?":   "Evet" if r["DBS Anchor Bayi mi?"] else "Hayır",
            "Sistemik Aktör": "Evet" if r.get("Sistemik Aktör mü? (Sektör Devi)", False) else "Hayır",
            "TKN":            r["KKB Ticari Kredi Notu (TKN)"],
            "TBE":            r["Ticari Borçluluk Endeksi (TBE)"],
            "Q Skoru":        q,
            "Segment":        segmentle(r["Yıllık Ciro (TL)"]),
        })
    rapor_df = pd.DataFrame(rapor_rows)
    st.dataframe(rapor_df, use_container_width=True, hide_index=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        rapor_df.to_excel(writer, index=False, sheet_name="Pazarlama Raporu")
        if triggers:
            pd.DataFrame(triggers).to_excel(writer, index=False, sheet_name="Çapraz Satış Tetikleyicileri")
        mizan_df.to_excel(writer, index=False, sheet_name="Tam Mizan")
    buf.seek(0)
    st.download_button(
        label="📥 Excel Raporu İndir",
        data=buf,
        file_name="trustgraph_pazarlama_raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
