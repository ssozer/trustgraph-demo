Evet, bu hata teknik olarak aynı kökten (Pandas'ın kolon yapısını kaybetmesi veya okuyamaması) geliyor. Özellikle dışarıdan Excel yüklendiğinde, kolonların sayısal algılanması (örneğin hesap kodlarının metin yerine integer algılanması) veya örnekleme (sampling) sırasında dataframe indekslerinin bozulması uygulamanın çökmesine neden olur.

Bir daha benzer hiçbir hata (`KeyError`, `AttributeError`, `ZeroDivisionError`) almamanız için kodu **tamamen zırhlandırdım**. Yapılan kritik düzeltmeler:

1. **Güvenli Örnekleme (Safe Sampling):** Gruplama (groupby) sırasında kolonların düşmesini engellemek için direkt örnekleme metoduna geçildi.
2. **`.get()` Metodu Entegrasyonu:** Grafik düğümleri oluşturulurken değerler doğrudan `row['Sektor']` şeklinde değil, hata vermeyen `row.get('Sektor', 'Bilinmiyor')` formatıyla çağrıldı.
3. **Tip Güvenliği (Type Safety):** Excel'den gelen "Hesap Kodu" gibi kolonların `.str` fonksiyonlarında hata vermemesi için tamamı `.astype(str)` ile korumaya alındı.
4. **Excel Yükleme Kontrolü:** Eksik veya hatalı formatta Excel yüklendiğinde uygulamanın çökmemesi için yükleme esnasına doğrulama (validation) eklendi.

Aşağıdaki kodu tamamen kopyalayıp dosyanıza yapıştırabilirsiniz:

```python
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
  <h1>🛡️ Project TrustGraph &nbsp;|&nbsp; B2B Risk &amp; Pazarlama Yönetimi Platformu</h1>
  <p>2-Hop GNN Bulaşma Simülasyonu · Sistemik Aktör Stres Testi · XAI Karar Gerekçesi · Kurumsal Bankacılık İstihbarat Platformu</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VERİ ÜRETİCİ
# ══════════════════════════════════════════════════════════════════════════════
random.seed(42)

SEHIRLER = ["İstanbul","Ankara","İzmir","Bursa","Antalya","Adana","Konya","Gaziantep","Mersin","Kayseri"]
KELIMELER = ["Anadolu","Karadeniz","Ege","Marmara","Akdeniz","Global","Pro","Lider","Öncü","Zirve"]
UNVANLAR = ["A.Ş.","Ltd. Şti.","San. A.Ş.","Tic. Ltd."]

SEKTORLER = {
    "İnşaat":    ("120", True),
    "Tekstil":   ("120", True),
    "Teknoloji": ("120", True),
    "Otomotiv":  ("120", True),
    "Kimya":     ("120", True),
    "Tarım":     ("320", False),
    "Gıda":      ("320", False),
    "Lojistik":  ("320", False),
}

SABIT_KAYITLAR = [
    ("101.01.001","Tahsil Edilecek Çekler Merkez",   "Finans",           250000.0,  0.0),
    ("102.01.001","Garanti Bankası Mevduatı",         "Finans",           400000.0,  0.0),
    ("335.01.001","Aylık Personel Maaşları",          "İnsan Kaynakları", 0.0,  350000.0),
    ("153.01.001","Depodaki Ticari Mallar A",         "Stok",             450000.0,  0.0),
    ("601.01.001","AB İhracat Gelirleri",             "Dış Ticaret",      0.0,  550000.0),
]

HOP2_ESLEME = {
    "İstanbul Anadolu A.Ş.": [("Beton Santrali Ltd.", "supplier")],
    "Ankara Karadeniz Ltd. Şti.": [("İplik Fabrikası A.Ş.", "supplier")],
    "İzmir Ege San. A.Ş.": [("Soğuk Zincir Loj. Ltd.", "supplier")],
}

def build_default_mizan():
    rows = []
    gidx = 1
    for sektor, (prefix, borc_mu) in SEKTORLER.items():
        for i in range(50):
            sehir  = SEHIRLER[i % len(SEHIRLER)]
            kelime = KELIMELER[gidx % len(KELIMELER)]
            unvan  = UNVANLAR[i % len(UNVANLAR)]
            firma  = f"{sehir} {kelime} {unvan}"
            hkod   = f"{prefix}.{(gidx // 100)+1:02d}.{(gidx % 100)+1:03d}"
            
            tutar = round(random.uniform(50_000, 5_000_000), -3)
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
    prefix = str(row.get("Hesap_Kodu", "")).split(".")[0]
    borc = pd.to_numeric(row.get("Borc_Toplam", 0), errors='coerce') or 0
    alacak = pd.to_numeric(row.get("Alacak_Toplam", 0), errors='coerce') or 0
    
    if prefix in AKTIF_PREFIXLER:
        return abs(borc - alacak)
    elif prefix in PASIF_PREFIXLER:
        return abs(alacak - borc)
    return abs(borc - alacak)

def ensure_kolonlar(df):
    if "Bakiye" not in df.columns:
        df["Bakiye"] = df.apply(hesapla_bakiye, axis=1)
    if "Islem_Hacmi" not in df.columns:
        df["Islem_Hacmi"] = pd.to_numeric(df.get("Borc_Toplam", 0), errors='coerce').fillna(0) + \
                            pd.to_numeric(df.get("Alacak_Toplam", 0), errors='coerce').fillna(0)
    return df

def segmentle(ciro):
    if ciro >= 5_000_000:   return "Ticari"
    elif ciro >= 2_000_000: return "Orta KOBİ"
    return "Mikro KOBİ"

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "mizan_data" not in st.session_state:
    st.session_state.mizan_data = ensure_kolonlar(build_default_mizan())

def init_istihbarat(mizan_df, n=10):
    random.seed(99)
    _df = ensure_kolonlar(mizan_df.copy())
    
    # Güvenli filtreleme (Hesap Kodunu string'e çevirerek kontrol et)
    firmalar = (
        _df[_df["Hesap_Kodu"].astype(str).str.startswith(("120","320"))]
        .sort_values(by="Islem_Hacmi", ascending=False)
        .head(n)
        .copy()
    )
    
    n_actual = len(firmalar)
    if n_actual == 0:
        return pd.DataFrame(columns=[
            "Cari Unvanı", "KKB Ticari Kredi Notu (TKN)", "Ticari Borçluluk Endeksi (TBE)",
            "Medya/Haber Olumsuzluk Skoru", "DBS Anchor Bayi mi?", "Bankamız Müşterisi mi?",
            "Yıllık Ciro (TL)", "POS Aylık Ciro (TL)", "Sistemik Aktör mü? (Sektör Devi)"
        ])

    return pd.DataFrame({
        "Cari Unvanı":                    firmalar["Cari_Unvan"].values,
        "KKB Ticari Kredi Notu (TKN)":    [random.randint(400, 1000) for _ in range(n_actual)],
        "Ticari Borçluluk Endeksi (TBE)": [random.randint(10, 90) for _ in range(n_actual)],
        "Medya/Haber Olumsuzluk Skoru":   [random.randint(0, 80) for _ in range(n_actual)],
        "DBS Anchor Bayi mi?":            [random.choice([True, False]) for _ in range(n_actual)],
        "Bankamız Müşterisi mi?":         [random.choice([True, False]) for _ in range(n_actual)],
        "Yıllık Ciro (TL)":               [random.randint(500_000, 20_000_000) for _ in range(n_actual)],
        "POS Aylık Ciro (TL)":            [random.randint(10_000, 500_000) for _ in range(n_actual)],
        "Sistemik Aktör mü? (Sektör Devi)": [True if i < 2 else random.choice([True, False]) for i in range(n_actual)],
    })

if "istihbarat" not in st.session_state:
    st.session_state.istihbarat = init_istihbarat(st.session_state.mizan_data)

# ══════════════════════════════════════════════════════════════════════════════
# SOL PANEL VE DOSYA YÜKLEME
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## ⚙️ Platform Kontrol Paneli")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Kurumsal Mizan Yükle")
uploaded = st.sidebar.file_uploader("Excel (.xlsx) Mizan Dosyası", type=["xlsx"])

if uploaded:
    try:
        raw = pd.read_excel(uploaded)
        if len(raw.columns) >= 5:
            # Sadece ilk 5 kolonu al ve standart isimlendir
            raw = raw.iloc[:, :5]
            raw.columns = ["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"]
            
            # Boş veya hatalı verileri temizle
            raw["Hesap_Kodu"] = raw["Hesap_Kodu"].fillna("000").astype(str)
            raw["Cari_Unvan"] = raw["Cari_Unvan"].fillna("Bilinmeyen Cari").astype(str)
            raw["Sektor"] = raw["Sektor"].fillna("Diğer").astype(str)
            raw["Borc_Toplam"] = pd.to_numeric(raw["Borc_Toplam"], errors='coerce').fillna(0)
            raw["Alacak_Toplam"] = pd.to_numeric(raw["Alacak_Toplam"], errors='coerce').fillna(0)
            
            raw = ensure_kolonlar(raw)
            st.session_state.mizan_data = raw
            st.session_state.istihbarat = init_istihbarat(raw)
            st.sidebar.success("✅ Mizan başarıyla yüklendi!")
        else:
            st.sidebar.error("⚠️ Hata: Yüklenen dosya en az 5 kolon içermelidir (Hesap Kodu, Unvan, Sektör, Borç, Alacak).")
    except Exception as e:
        st.sidebar.error(f"Dosya okunamadı: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Ekosistem Simülasyon Odası")

mizan_df = st.session_state.mizan_data.copy()
sectors = sorted(mizan_df["Sektor"].dropna().unique().tolist())

selected_sector = st.sidebar.selectbox("Krize Girecek Sektör:", ["(Seçilmedi)"] + sectors)
shock_intensity = st.sidebar.slider("Sektörel Kriz Şiddeti (%):", 0, 100, 0)
alpha           = st.sidebar.slider("Risk Bulaşma Katsayısı (α):", 0.1, 1.0, 0.5, 0.05)
st.sidebar.markdown("---")
n_slider = st.sidebar.slider("İstihbarat Matrisi Satır Sayısı (N):", 5, 50, 10)

# ══════════════════════════════════════════════════════════════════════════════
# RİSK HESAPLAMA (Sistemik Aktör Çarpanı Dahil)
# ══════════════════════════════════════════════════════════════════════════════
total_hacim = mizan_df["Islem_Hacmi"].sum()
if pd.isna(total_hacim) or total_hacim <= 0:
    total_hacim = 1.0

ist_ref = st.session_state.istihbarat.copy()
sistemik_set = set()
if not ist_ref.empty and "Sistemik Aktör mü? (Sektör Devi)" in ist_ref.columns:
    sistemik_set = set(ist_ref.loc[ist_ref["Sistemik Aktör mü? (Sektör Devi)"] == True, "Cari Unvanı"].tolist())

partner_risks = {}
for _, row in mizan_df.iterrows():
    unvan = row.get("Cari_Unvan", "Bilinmeyen")
    base = 15.0
    if row.get("Sektor", "") == selected_sector:
        base = float(shock_intensity)
    partner_risks[unvan] = base

bulaşma_detay = []
for _, row in mizan_df.iterrows():
    firma = row.get("Cari_Unvan", "Bilinmeyen")
    sektor = row.get("Sektor", "Diğer")
    hkod = str(row.get("Hesap_Kodu", "000"))
    v_j = pd.to_numeric(row.get("Islem_Hacmi", 0), errors='coerce') or 0
    
    r_own = partner_risks.get(firma, 15.0)
    gamma = 2.0 if firma in sistemik_set else 1.0
    katki = r_own * gamma * (v_j / total_hacim)
    
    bulaşma_detay.append({
        "firma": firma, "sektor": sektor, "r_own": r_own, 
        "gamma": gamma, "v_j": v_j, "katki": katki, "hesap_kodu": hkod
    })

bulaşma_toplam = sum(d["katki"] for d in bulaşma_detay) * alpha
merkez_risk    = min(round(bulaşma_toplam, 1), 100.0)

bulaşma_detay_sorted = sorted(bulaşma_detay, key=lambda x: x["katki"], reverse=True)
top_risk_firma = bulaşma_detay_sorted[0] if bulaşma_detay_sorted else None

# ══════════════════════════════════════════════════════════════════════════════
# GÖRSELLEŞTİRME VE SEKMELER
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🌐 İlişkisel Ekosistem ve Risk Simülatörü",
    "📊 Mizan Analiz ve İstihbarat Laboratuvarı",
    "🎯 Akıllı Pazarlama ve Çapraz Satış Portalı",
])

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
        partner_count = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith(("120","320"))].shape[0]
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
        st.markdown(f"""<div class="metric-card purple">
          <div class="metric-title">Sistemik Aktör (γ=2.0)</div>
          <div class="metric-value">{len(sistemik_set)}</div>
          <div class="metric-sub">Sektör Devi · 2x Risk Çarpanı</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🌐 Canlı 2-Hop B2B Ekosistem Grafik Haritası</div>', unsafe_allow_html=True)
    
    # GÜVENLİ GRAFİK ÖRNEKLEMESİ (SAFE SAMPLING)
    graf_df = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith(("120","320"))].reset_index(drop=True)
    if len(graf_df) > 80:
        graf_df = graf_df.sample(n=80, random_state=42).reset_index(drop=True)

    G = nx.DiGraph()
    main_firm = "Merkez_Firma_A"
    merkez_color = "#e74c3c" if merkez_risk > 50 else ("#f39c12" if merkez_risk > 20 else "#2c3e50")
    G.add_node(main_firm, size=42, color=merkez_color,
               title=f"<b>Merkez Firma A</b><br>Bulaşan Risk: <b>%{merkez_risk}</b>")

    max_hacim = graf_df["Islem_Hacmi"].max() if not graf_df.empty else 1.0
    if pd.isna(max_hacim) or max_hacim <= 0: max_hacim = 1.0

    for _, row in graf_df.iterrows():
        # Düğümler için güvenli veri çekimi (KeyError engelleme)
        name   = row.get("Cari_Unvan", "Bilinmeyen Firma")
        sektor = row.get("Sektor", "Bilinmeyen Sektör")
        hacim  = row.get("Islem_Hacmi", 0)
        hkod   = str(row.get("Hesap_Kodu", ""))
        
        risk  = partner_risks.get(name, 15.0)
        gamma = 2.0 if name in sistemik_set else 1.0
        cpct  = round((hacim / total_hacim) * 100, 2)
        size  = 12 + int((hacim / max_hacim) * 22)

        if name in sistemik_set:
            color = "#dc2626"
            size  = max(size, 24)
        elif risk > 60: color = "#e74c3c"
        elif risk > 30: color = "#f39c12"
        else:           color = "#27ae60"

        sistemik_label = " ⚠️ SİSTEMİK" if name in sistemik_set else ""
        tip = f"<b>{name}</b>{sistemik_label}<br>Sektör: {sektor}<br>Ciro Payı: %{cpct}<br>Risk: %{risk}<br>γ={gamma}"
        
        G.add_node(name, size=size, color=color, title=tip)

        if hkod.startswith("120"):
            G.add_edge(main_firm, name, color="#94a3b8", width=1)
        else:
            G.add_edge(name, main_firm, color="#94a3b8", width=1)

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
        net.add_node(node, label=node, size=attrs["size"], color=attrs["color"], title=attrs.get("title", ""))
    for u, v, edata in G.edges(data=True):
        net.add_edge(u, v, color=edata.get("color","#94a3b8"), width=edata.get("width", 1), arrows="to", dashes=edata.get("dashes", False))
    
    net.set_options("""
    var options = {
      "physics": { "barnesHut": { "gravitationalConstant": -18000, "centralGravity": 0.3, "springLength": 200 }, "minVelocity": 0.75 },
      "nodes": { "font": { "size": 11, "face": "Inter" } }
    }
    """)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f:
            components.html(f.read(), height=550)
    os.unlink(tmp.name)

    # ── XAI KARTI
    st.markdown('<div class="section-header">🤖 GNNExplainer: Yapay Zeka Karar Gerekçesi</div>', unsafe_allow_html=True)
    if top_risk_firma:
        tf = top_risk_firma
        is_sist = tf.get("firma") in sistemik_set
        gamma_str = "γ=2.0 (Sistemik Aktör)" if is_sist else "γ=1.0"
        ciro_pct = round((tf.get("v_j", 0) / total_hacim) * 100, 1)
        
        xai_level, xai_color = ("🔴 KRİTİK RİSK SEVİYESİ", "#7f1d1d") if merkez_risk > 40 else \
                               ("🟠 ORTA RİSK — YAKIN İZLEME", "#78350f") if merkez_risk > 15 else \
                               ("🟢 DÜŞÜK RİSK — GÜVENLİ EKOSİSTEM", "#14532d")

        st.markdown(f"""
        <div class="xai-card">
          <h4>🤖 GNNExplainer — Dinamik Risk Yolu Analizi &nbsp;|&nbsp; {xai_level}</h4>
          <p>Merkez Firma A'nın ekosistem risk endeksi <b>%{merkez_risk}</b>'e ulaşmıştır. Bulaşan riskin <b>birincil nedeni</b>: <b>{tf.get('sektor', 'Bilinmiyor')}</b> sektöründeki <b>{tf.get('firma', 'Bilinmiyor')}</b>'dır.</p>
          <div class="xai-path">
            📍 <b>Risk Yolu:</b> {tf.get('firma', '')} → Merkez Firma A &nbsp;|&nbsp; Ciro Payı: <b>%{ciro_pct}</b> &nbsp;|&nbsp; Kendi Riski: <b>%{tf.get('r_own', 0):.0f}</b> &nbsp;|&nbsp; Çarpan: <b>{gamma_str}</b>
          </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    col_l, col_r = st.columns([1.1, 1])
    with col_l:
        st.markdown('<div class="section-header">📋 Tam Mizan Veri Seti (TDHP)</div>', unsafe_allow_html=True)
        st.dataframe(mizan_df, use_container_width=True, hide_index=True, height=420)
    with col_r:
        st.markdown(f'<div class="section-header">🔬 İnteraktif İstihbarat Matrisi</div>', unsafe_allow_html=True)
        if len(st.session_state.istihbarat) != n_slider:
            st.session_state.istihbarat = init_istihbarat(mizan_df, n=n_slider)
        edited = st.data_editor(st.session_state.istihbarat, use_container_width=True, hide_index=True, height=400)
        st.session_state.istihbarat = edited

with tab3:
    mdf = st.session_state.mizan_data.copy()
    ist = st.session_state.istihbarat.copy()
    
    st.markdown('<div class="section-header">🎯 Çapraz Satış Tetikleyicileri (Kebir Hesap Analizi)</div>', unsafe_allow_html=True)
    triggers = []

    # Str tipine çevirerek arama yapıyoruz (TypeError engellendi)
    personel = mdf[mdf["Hesap_Kodu"].astype(str).str.startswith("335")]["Bakiye"].sum()
    if personel > 200_000:
        triggers.append({"Aksiyon": "Maaş Ödemesi Protokolü Teklifi", "Tutar": f"₺{personel:,.0f}"})
        
    ihracat = mdf[mdf["Hesap_Kodu"].astype(str).str.startswith("601")]["Bakiye"].sum()
    if ihracat > 100_000:
        triggers.append({"Aksiyon": "İhracat Akreditif Finansmanı Önerisi", "Tutar": f"₺{ihracat:,.0f}"})

    if triggers:
        st.dataframe(pd.DataFrame(triggers), use_container_width=True, hide_index=True)
    else:
        st.success("Tetikleyici bulunamadı.")

```
