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
st.set_page_config(layout="wide", page_title="TrustGraph B2B Platform", page_icon="🛡️")

# ── KURUMSAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .stTabs [data-baseweb="tab-list"] { background: #0f172a; border-radius: 10px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 500; border-radius: 8px; padding: 8px 20px; }
    .stTabs [aria-selected="true"] { background: #2563eb !important; color: white !important; }
    .metric-card { background: white; border-radius: 12px; padding: 18px 22px; border-left: 5px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 12px; }
    .metric-card.danger  { border-left-color: #ef4444; }
    .metric-card.warning { border-left-color: #f59e0b; }
    .metric-card.success { border-left-color: #10b981; }
    .metric-card.purple  { border-left-color: #8b5cf6; }
    .metric-title { font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 24px; font-weight: 700; color: #0f172a; margin-top: 4px; }
    .metric-sub   { font-size: 12px; color: #94a3b8; margin-top: 4px; font-weight: 500;}
    .section-header { font-size: 16px; font-weight: 700; color: #0f172a;
        border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 16px; margin-top: 24px; }
    .header-banner { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        border-radius: 14px; padding: 24px 32px; color: white; margin-bottom: 24px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .header-banner h1 { font-size: 24px; font-weight: 700; margin: 0; letter-spacing: -0.02em;}
    .header-banner p  { font-size: 14px; opacity: 0.85; margin: 6px 0 0; }
    .xai-card { background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6;
        border-radius: 12px; padding: 20px 24px; color: #334155; margin: 16px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);}
    .xai-card h4 { font-size: 14px; font-weight: 700; margin: 0 0 10px 0; color: #0f172a; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
  <h1>🛡️ TrustGraph | B2B Ekosistem & Pazarlama Platformu</h1>
  <p>Tedarik Zinciri Stres Testi (KKB/Teminat Odaklı) · Mizan Laboratuvarı · Akıllı Çapraz Satış</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VERİ ÜRETİCİ VE YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════
random.seed(42)

def build_default_mizan():
    # İnşaat Kümelenmesini ağırlıklı içeren varsayılan Mizan verisi
    FIRMALAR = [
        ("Kaya Çimento Sanayi", "Yapı Malzemeleri", "320", 40_000_000),
        ("Demirtaş Çelik Ltd.", "Metal/Demir", "320", 55_000_000),
        ("Atlas Hafriyat", "Hafriyat/Lojistik", "320", 25_000_000),
        ("Ege Mekanik ve Tesisat", "Taşeron/Tesisat", "320", 15_000_000),
        ("Zirve GYO A.Ş.", "İnşaat", "120", 35_000_000),
        ("Marmara Akaryakıt", "Enerji", "320", 12_000_000),
        ("Öncü İş Makinaları", "Otomotiv", "320", 18_000_000),
        ("Dizayn Mimarlık", "Hizmet", "320", 5_000_000),
        ("Bosphorus Lojistik", "Lojistik", "120", 22_000_000),
        ("Vadi Yapı Taşeron", "İnşaat", "320", 9_000_000),
    ]
    
    rows = []
    # İnşaat Kümesi
    for idx, (unvan, sek, prefix, hacim) in enumerate(FIRMALAR):
        hkod = f"{prefix}.01.{idx+1:03d}"
        borc, alacak = (hacim, 0.0) if prefix == "120" else (0.0, hacim)
        rows.append((hkod, unvan, sek, borc, alacak))
        
    # Sabit Kalemler (Pazarlama sekmesi için)
    sabitler = [
        ("101.01.001", "Tahsil Edilecek Çekler Merkez", "Finans", 2500000.0, 0.0),
        ("102.01.001", "Garanti Bankası Mevduatı", "Finans", 400000.0, 0.0),
        ("335.01.001", "Aylık Personel Maaşları", "İnsan Kaynakları", 0.0, 850000.0),
        ("153.01.001", "Depodaki Ticari Mallar", "Stok", 1450000.0, 0.0),
        ("601.01.001", "Yurtdışı İhracat Gelirleri", "Dış Ticaret", 0.0, 3500000.0),
        ("600.01.001", "Yurtiçi Satışlar", "Satış", 0.0, 15000000.0),
    ]
    for r in sabitler: rows.append(r)
        
    return pd.DataFrame(rows, columns=["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"])

def hesapla_bakiye(row):
    prefix = str(row.get("Hesap_Kodu", "")).split(".")[0]
    borc = pd.to_numeric(row.get("Borc_Toplam", 0), errors='coerce') or 0
    alacak = pd.to_numeric(row.get("Alacak_Toplam", 0), errors='coerce') or 0
    if prefix in ("101","102","120","150","153"): return abs(borc - alacak)
    elif prefix in ("103","300","320","335","600","601"): return abs(alacak - borc)
    return abs(borc - alacak)

def ensure_kolonlar(df):
    if "Bakiye" not in df.columns:
        df["Bakiye"] = df.apply(hesapla_bakiye, axis=1)
    if "Islem_Hacmi" not in df.columns:
        df["Islem_Hacmi"] = pd.to_numeric(df.get("Borc_Toplam", 0), errors='coerce').fillna(0) + \
                            pd.to_numeric(df.get("Alacak_Toplam", 0), errors='coerce').fillna(0)
    return df

def init_istihbarat(mizan_df, n=15):
    _df = ensure_kolonlar(mizan_df.copy())
    firmalar = _df[_df["Hesap_Kodu"].astype(str).str.startswith(("120","320"))].sort_values(by="Islem_Hacmi", ascending=False).head(n).copy()
    
    n_actual = len(firmalar)
    if n_actual == 0:
        return pd.DataFrame()

    # Firmalara mantıklı KKB notları ve Ciro ataması
    tkn_list, dbs_list, ciro_list = [], [], []
    for _, row in firmalar.iterrows():
        hacim = row["Islem_Hacmi"]
        # Hacim büyükse ciro da büyüktür
        ciro = hacim * random.uniform(1.5, 4.0)
        ciro_list.append(int(ciro))
        
        # Bazı firmalara bilerek düşük KKB verelim ki simülasyonda batsınlar
        if "Çelik" in row["Cari_Unvan"] or "Taşeron" in row["Cari_Unvan"]:
            tkn_list.append(random.randint(400, 550))
            dbs_list.append(False)
        else:
            tkn_list.append(random.randint(650, 900))
            dbs_list.append(random.choice([True, False]))

    return pd.DataFrame({
        "Cari Unvanı": firmalar["Cari_Unvan"].values,
        "KKB Ticari Kredi Notu (TKN)": tkn_list,
        "Ticari Borçluluk Endeksi (TBE)": [random.randint(10, 80) for _ in range(n_actual)],
        "DBS/Teminatlı Çalışma?": dbs_list,
        "Bankamız Müşterisi mi?": [random.choice([True, False]) for _ in range(n_actual)],
        "Tahmini Yıllık Ciro (TL)": ciro_list
    })

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE (UYGULAMA HAFIZASI)
# ══════════════════════════════════════════════════════════════════════════════
if "mizan_data" not in st.session_state:
    st.session_state.mizan_data = ensure_kolonlar(build_default_mizan())
if "istihbarat" not in st.session_state:
    st.session_state.istihbarat = init_istihbarat(st.session_state.mizan_data)

# ══════════════════════════════════════════════════════════════════════════════
# SOL PANEL: MİZAN YÜKLEME VE SİMÜLASYON TETİKLEYİCİ
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("### 📂 Kurumsal Mizan Yükle")
uploaded = st.sidebar.file_uploader("Excel (.xlsx) Yükle", type=["xlsx"])

if uploaded:
    try:
        raw = pd.read_excel(uploaded)
        if len(raw.columns) >= 5:
            raw = raw.iloc[:, :5]
            raw.columns = ["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"]
            raw["Hesap_Kodu"] = raw["Hesap_Kodu"].fillna("000").astype(str)
            raw["Cari_Unvan"] = raw["Cari_Unvan"].fillna("Bilinmeyen").astype(str)
            raw["Sektor"] = raw["Sektor"].fillna("Diğer").astype(str)
            raw = ensure_kolonlar(raw)
            
            st.session_state.mizan_data = raw
            st.session_state.istihbarat = init_istihbarat(raw)
            st.sidebar.success("✅ Mizan başarıyla yüklendi!")
    except Exception as e:
        st.sidebar.error(f"Hata: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌪️ Stres Testi (Domino Senaryosu)")

ist_df = st.session_state.istihbarat
firma_listesi = ["(Seçiniz)"] + ist_df["Cari Unvanı"].tolist() if not ist_df.empty else ["(Seçiniz)"]

krize_giren = st.sidebar.selectbox("İflas Edecek / Şok Yiyecek Firma:", firma_listesi)
teminat_korumasi = st.sidebar.slider("DBS/Teminat Koruma Gücü (%)", 10, 100, 70, help="Teminatlı çalışmalarda şokun ne kadarının sönümleneceği.")
iflas_esigi = st.sidebar.slider("İflas Eşiği (Bilanço Hasarı %)", 10, 80, 40)

st.sidebar.info("💡 **Domino Formülü:**\nAlınan Hasar = Şok × (İşlem Hacmi / Toplam Ciro) × KKB Kırılganlığı × Teminat Etkisi")

# ══════════════════════════════════════════════════════════════════════════════
# DİNAMİK SİMÜLASYON MOTORU (TAB 1 İÇİN HAZIRLIK)
# ══════════════════════════════════════════════════════════════════════════════
mizan_df = st.session_state.mizan_data

# Node datalarını oluştur
node_status = {}
banka_kredi_riski = 0.0

for _, row in ist_df.iterrows():
    unvan = row["Cari Unvanı"]
    hacim = mizan_df[mizan_df["Cari_Unvan"] == unvan]["Islem_Hacmi"].sum()
    ciro = max(row.get("Tahmini Yıllık Ciro (TL)", hacim*2), hacim*1.1)
    kredi_limit = ciro * 0.15 # Bankamızdaki tahmini kredi limiti
    
    node_status[unvan] = {
        "kkb": row.get("KKB Ticari Kredi Notu (TKN)", 500),
        "dbs": row.get("DBS/Teminatlı Çalışma?", False),
        "ciro": ciro,
        "hacim_bizimle": hacim,
        "kredi_riski": kredi_limit,
        "hasar_orani": 0.0,
        "durum": "Safe",
        "sebep": ""
    }
    banka_kredi_riski += kredi_limit

# Ana Firmamız (Merkez)
merkez_ciro = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith(("600","601"))]["Bakiye"].sum()
if merkez_ciro == 0: merkez_ciro = 100_000_000
node_status["ANA_MUSTERIMIZ"] = {"kkb": 750, "dbs": True, "ciro": merkez_ciro, "kredi_riski": 0, "hasar_orani": 0.0, "durum": "Safe", "sebep": ""}

npl_beklentisi = 0.0

# ── CASCADE ALGORİTMASI ──
if krize_giren != "(Seçiniz)" and krize_giren in node_status:
    node_status[krize_giren]["hasar_orani"] = 100.0
    node_status[krize_giren]["durum"] = "Failed"
    node_status[krize_giren]["sebep"] = "Senaryo Tetikleyicisi (Sıfır Noktası)"
    npl_beklentisi += node_status[krize_giren]["kredi_riski"]
    
    # 1. Dalga: Krizdeki firmadan Ana Müşterimize bulaşma
    batan_ile_hacim = node_status[krize_giren]["hacim_bizimle"]
    bagimlilik = batan_ile_hacim / node_status["ANA_MUSTERIMIZ"]["ciro"]
    teminat_carpani = (100 - teminat_korumasi)/100.0 if node_status[krize_giren]["dbs"] else 1.0
    
    ana_hasar = (100.0 * bagimlilik * ((1000 - 750)/400.0) * teminat_carpani)
    node_status["ANA_MUSTERIMIZ"]["hasar_orani"] += ana_hasar
    
    if node_status["ANA_MUSTERIMIZ"]["hasar_orani"] >= iflas_esigi:
        node_status["ANA_MUSTERIMIZ"]["durum"] = "Failed"
    elif node_status["ANA_MUSTERIMIZ"]["hasar_orani"] >= (iflas_esigi/2):
        node_status["ANA_MUSTERIMIZ"]["durum"] = "Warning"

    # 2. Dalga: Diğer firmalara Hop-2 bulaşma (Basitleştirilmiş Ağ Etkisi)
    # Gerçekte alt kırılımlar olmalı, burada demonstrasyon için rastgele ağ bağı kuruyoruz
    for diger_firma in node_status:
        if diger_firma not in ["ANA_MUSTERIMIZ", krize_giren]:
            # Eğer sektörleri aynıysa veya inşaat kümesiyse %30 ihtimalle dolaylı ticaretleri var diyelim
            if random.random() < 0.3:
                dolayli_hacim = node_status[diger_firma]["ciro"] * random.uniform(0.1, 0.4)
                d_bagimlilik = dolayli_hacim / node_status[diger_firma]["ciro"]
                d_kkb_kirilganlik = max(0.1, (1000 - node_status[diger_firma]["kkb"]) / 400.0)
                d_teminat = (100 - teminat_korumasi)/100.0 if node_status[diger_firma]["dbs"] else 1.0
                
                d_hasar = (100.0 * d_bagimlilik * d_kkb_kirilganlik * d_teminat)
                node_status[diger_firma]["hasar_orani"] += d_hasar
                
                if node_status[diger_firma]["hasar_orani"] >= iflas_esigi:
                    node_status[diger_firma]["durum"] = "Failed"
                    node_status[diger_firma]["sebep"] = f"{krize_giren} iflası kaynaklı dolaylı şok."
                    npl_beklentisi += node_status[diger_firma]["kredi_riski"]
                elif node_status[diger_firma]["hasar_orani"] >= (iflas_esigi/3):
                    node_status[diger_firma]["durum"] = "Warning"
                    node_status[diger_firma]["sebep"] = "Tedarik zinciri nakit sıkışıklığı."

# ══════════════════════════════════════════════════════════════════════════════
# SEKMELER (TABS)
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🌐 Sistemik Stres Testi (Ekosistem Simülatörü)",
    "📊 Mizan Analiz ve İstihbarat Laboratuvarı",
    "🎯 Akıllı Pazarlama ve Çapraz Satış Portalı",
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: SİMÜLASYON GRAFİĞİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    batan_sayisi = sum(1 for k, v in node_status.items() if v["durum"] == "Failed" and k != "ANA_MUSTERIMIZ")
    npl_oran = (npl_beklentisi / banka_kredi_riski * 100) if banka_kredi_riski > 0 else 0
    
    with c1:
        st.markdown(f"""<div class="metric-card purple">
          <div class="metric-title">Toplam Ekosistem Hacmi</div>
          <div class="metric-value">₺{sum(v['ciro'] for v in node_status.values())/1e6:.0f}M</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card success">
          <div class="metric-title">Banka Toplam Kredi Riski</div>
          <div class="metric-value">₺{banka_kredi_riski/1e6:.1f}M</div></div>""", unsafe_allow_html=True)
    with c3:
        cls_bat = "danger" if batan_sayisi > 0 else "success"
        st.markdown(f"""<div class="metric-card {cls_bat}">
          <div class="metric-title">Batan Partner Sayısı</div>
          <div class="metric-value">{batan_sayisi}</div></div>""", unsafe_allow_html=True)
    with c4:
        cls_npl = "danger" if npl_oran > 15 else ("warning" if npl_oran > 0 else "success")
        st.markdown(f"""<div class="metric-card {cls_npl}">
          <div class="metric-title">NPL (Batık) Beklentisi</div>
          <div class="metric-value">₺{npl_beklentisi/1e6:.1f}M</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🕸️ Dinamik Tedarik Zinciri Ağ Haritası</div>', unsafe_allow_html=True)
    
    G = nx.DiGraph()
    # Ana Müşteri Nodu
    m_stat = node_status["ANA_MUSTERIMIZ"]
    m_color = "#ef4444" if m_stat["durum"]=="Failed" else ("#f59e0b" if m_stat["durum"]=="Warning" else "#1e3a8a")
    G.add_node("ANA MÜŞTERİMİZ", size=45, color=m_color, title=f"<b>Ana Müşterimiz (Merkez)</b><br>Bilanço Hasarı: %{m_stat['hasar_orani']:.1f}")
    
    for unvan, data in node_status.items():
        if unvan == "ANA_MUSTERIMIZ": continue
        
        # Renk ve Boyut
        color = "#ef4444" if data["durum"]=="Failed" else ("#f59e0b" if data["durum"]=="Warning" else "#10b981")
        size = max(15, min(35, int((data["kredi_riski"]/5_000_000)*10) + 15))
        
        # Etiket ve Tooltip
        kisa_isim = unvan[:15] + ".." if len(unvan) > 15 else unvan
        teminat_str = "Korumalı (DBS)" if data["dbs"] else "Açık Hesap"
        tooltip = (f"<b>{unvan}</b><br>KKB Notu: {data['kkb']}<br>Çalışma: {teminat_str}<br>"
                   f"Banka Kredi Riski: ₺{data['kredi_riski']/1e6:.1f}M<br>---<br>"
                   f"Hasar Oranı: %{data['hasar_orani']:.1f}<br>Durum: {data['durum']}")
        
        G.add_node(unvan, size=size, color=color, title=tooltip, label=kisa_isim)
        
        # Merkez ile bağlantı
        G.add_edge(unvan, "ANA MÜŞTERİMİZ", color="#cbd5e1", width=max(1, int(data["hacim_bizimle"]/10_000_000)))
        
        # Dolaylı bağlar (Sadece görsel zenginlik ve hop-2 için)
        if data["sebep"] != "" and unvan != krize_giren:
            G.add_edge(krize_giren, unvan, color="#8b5cf6", dashes=True, width=2)

    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#0f172a", directed=True)
    net.from_nx(G)
    net.set_options("""
    var options = {
      "physics": { "barnesHut": { "gravitationalConstant": -12000, "centralGravity": 0.3 }, "minVelocity": 0.75 },
      "nodes": { "font": { "size": 13, "face": "Inter", "bold": true } }
    }
    """)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f:
            components.html(f.read(), height=520)
    os.unlink(tmp.name)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: MİZAN VE İSTİHBARAT LABORATUVARI (DATA EDITOR)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown('<div class="section-header">📋 Tam Mizan Veri Seti (Yüklenen/Ham)</div>', unsafe_allow_html=True)
        show_df = mizan_df.copy()
        show_df.columns = ["Hesap Kodu","Cari Unvanı","Sektör","Borç (TL)","Alacak (TL)","Bakiye (TL)","İşlem Hacmi (TL)"]
        st.dataframe(show_df.style.format({
            "Borç (TL)": "{:,.0f}", "Alacak (TL)": "{:,.0f}", "Bakiye (TL)": "{:,.0f}", "İşlem Hacmi (TL)": "{:,.0f}"
        }), use_container_width=True, hide_index=True, height=450)

    with col_r:
        st.markdown('<div class="section-header">🔬 İnteraktif İstihbarat Matrisi (Risk Parametreleri)</div>', unsafe_allow_html=True)
        st.caption("Not: Buradaki KKB Notu ve Teminat durumu, Tab 1'deki iflas simülasyonunu doğrudan etkiler.")
        
        edited = st.data_editor(
            st.session_state.istihbarat,
            use_container_width=True, hide_index=True, height=450,
            column_config={
                "Cari Unvanı": st.column_config.TextColumn(disabled=True),
                "KKB Ticari Kredi Notu (TKN)": st.column_config.NumberColumn(min_value=0, max_value=1000),
                "DBS/Teminatlı Çalışma?": st.column_config.CheckboxColumn(),
                "Tahmini Yıllık Ciro (TL)": st.column_config.NumberColumn(format="₺%d"),
            },
            key="ist_editor"
        )
        st.session_state.istihbarat = edited

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: PAZARLAMA VE ÇAPRAZ SATIŞ PORTALI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown('<div class="section-header">🎯 Modül: Gelişmiş Çapraz Satış Tetikleyicileri (Kebir Hesap Analizi)</div>', unsafe_allow_html=True)
    triggers = []

    personel = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("335")]["Bakiye"].sum()
    if personel > 200_000:
        triggers.append({"Hesap Grubu":"335 — Personel Maaşları",
            "Tespit":f"Yüksek maaş borcu: ₺{personel:,.0f}",
            "Öneri/Aksiyon":"💼 Maaş Ödemesi Protokolü Teklifi + Bireysel Kredi Satışı",
            "Öncelik":"🔴 Yüksek"})

    cek_bakiye = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("101")]["Bakiye"].sum()
    alan_120   = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("120")]["Bakiye"].sum() or 1.0
    if (cek_bakiye / alan_120) > 0.10:
        triggers.append({"Hesap Grubu":"101 — Tahsil Edilecek Çekler",
            "Tespit":f"Çek portföyü birikimi: ₺{cek_bakiye:,.0f}",
            "Öneri/Aksiyon":"✂️ Çek İskonto (Kırma) ve Tahsilat Finansmanı Teklifi",
            "Öncelik":"🟠 Orta"})

    ihracat = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("601")]["Bakiye"].sum()
    if ihracat > 500_000:
        triggers.append({"Hesap Grubu":"601 — Yurtdışı İhracat Gelirleri",
            "Tespit":f"İhracat Geliri: ₺{ihracat:,.0f}",
            "Öneri/Aksiyon":"🌍 İhracat Akreditif Finansmanı + FX Forward Döviz Koruması",
            "Öncelik":"🔴 Yüksek"})

    if triggers:
        st.dataframe(pd.DataFrame(triggers), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Şu anda aktif çapraz satış tetikleyicisi bulunmamaktadır.")

    st.markdown('<div class="section-header">🔵 Modül: Yeni Müşteri Kazanım Listesi (Sıcak Fırsatlar)</div>', unsafe_allow_html=True)
    ist = st.session_state.istihbarat
    if not ist.empty:
        potansiyel = ist[(~ist["Bankamız Müşterisi mi?"]) & (ist["KKB Ticari Kredi Notu (TKN)"] >= 650)].copy()
        if not potansiyel.empty:
            potansiyel["Aksiyon"] = "📣 Portföy Yöneticisine Ata"
            st.dataframe(potansiyel[["Cari Unvanı", "KKB Ticari Kredi Notu (TKN)", "Tahmini Yıllık Ciro (TL)", "Aksiyon"]], use_container_width=True, hide_index=True)
        else:
            st.info("Kriterlere uygun potansiyel müşteri bulunamadı.")
