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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-banner">
  <h1>🛡️ TrustGraph | B2B Ekosistem & Pazarlama Platformu</h1>
  <p>Tedarik Zinciri Stres Testi (Firma Bazlı Direnç Modeli) · Mizan Laboratuvarı · Akıllı Çapraz Satış</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VERİ ÜRETİCİ VE YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════
random.seed(42)

def build_default_mizan():
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
    for idx, (unvan, sek, prefix, hacim) in enumerate(FIRMALAR):
        hkod = f"{prefix}.01.{idx+1:03d}"
        borc, alacak = (hacim, 0.0) if prefix == "120" else (0.0, hacim)
        rows.append((hkod, unvan, sek, borc, alacak))
        
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
    borc = pd.to_numeric(row.get("Borc_Toplam", 0), errors='coerce') or 0.0
    alacak = pd.to_numeric(row.get("Alacak_Toplam", 0), errors='coerce') or 0.0
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
    
    hesap_kodlari = _df["Hesap_Kodu"].astype(str)
    firmalar = _df[hesap_kodlari.str.startswith(("120","320"))].sort_values(by="Islem_Hacmi", ascending=False).head(n).copy()
    
    n_actual = len(firmalar)
    if n_actual == 0: return pd.DataFrame()

    tkn_list, sigorta_list, ciro_list, esik_list = [], [], [], []
    
    for _, row in firmalar.iterrows():
        hacim = row.get("Islem_Hacmi", 0)
        ciro = int(hacim * random.uniform(1.5, 4.0))
        ciro_list.append(ciro)
        
        unvan = str(row.get("Cari_Unvan", ""))
        # Sektörel / Unvan bazlı risk belirleme
        if "Çelik" in unvan or "Taşeron" in unvan or "Hafriyat" in unvan:
            kkb = random.randint(400, 550)
            sigorta = random.choice([0, 0, 10, 20]) # Teminatı yok ya da çok zayıf
        else:
            kkb = random.randint(700, 900)
            sigorta = random.choice([50, 70, 80, 100]) # Güçlü teminat
            
        tkn_list.append(kkb)
        sigorta_list.append(sigorta)
        
        # FIRMA BAZLI İFLAS EŞİĞİ (Direnç) HESABI: KKB ile doğru orantılı
        # Örnek: KKB 900 -> %55 direnebilir. KKB 400 -> %20'de batar.
        esik = int(max(15, min(65, (kkb / 1000) * 60)))
        esik_list.append(esik)

    return pd.DataFrame({
        "Cari Unvanı": firmalar["Cari_Unvan"].values,
        "KKB Ticari Kredi Notu (TKN)": tkn_list,
        "Bilanço Direnci / İflas Eşiği (%)": esik_list,
        "Teminat/Sigorta Kapsamı (%)": sigorta_list,
        "Bankamız Müşterisi mi?": [random.choice([True, False]) for _ in range(n_actual)],
        "Tahmini Yıllık Ciro (TL)": ciro_list
    })

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE KONTROLÜ
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
        else:
            st.sidebar.error("Hata: Veri formatı en az 5 kolon olmalı.")
    except Exception as e:
        st.sidebar.error(f"Hata: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌪️ Domino Stres Testi")

ist_df = st.session_state.istihbarat
firma_listesi = ["(Seçiniz)"] + ist_df["Cari Unvanı"].tolist() if not ist_df.empty and "Cari Unvanı" in ist_df.columns else ["(Seçiniz)"]

krize_giren = st.sidebar.selectbox("Şok Yiyecek (Temerrüt) Firma:", firma_listesi)

st.sidebar.info("""💡 **Dinamik Ağ Algoritması:**
Her firmanın dayanıklılığı **KENDİ** KKB notuna ve Teminat gücüne göre ayrı ayrı hesaplanır. Global sabitler kullanılmaz.""")

# ══════════════════════════════════════════════════════════════════════════════
# DİNAMİK SİMÜLASYON MOTORU (FİRMA SPESİFİK PARAMETRELERLE)
# ══════════════════════════════════════════════════════════════════════════════
mizan_df = st.session_state.mizan_data
node_status = {}
banka_kredi_riski = 0.0

for _, row in ist_df.iterrows():
    unvan = row.get("Cari Unvanı", "Bilinmeyen")
    hacim = mizan_df[mizan_df["Cari_Unvan"] == unvan]["Islem_Hacmi"].sum() if "Cari_Unvan" in mizan_df.columns else 0
        
    ciro = max(pd.to_numeric(row.get("Tahmini Yıllık Ciro (TL)", hacim * 2), errors='coerce') or hacim * 2, hacim * 1.1)
    kredi_limit = ciro * 0.15 
    
    # Firma Spesifik Parametreleri İstihbarat Matrisinden Çekiyoruz
    kkb_val = pd.to_numeric(row.get("KKB Ticari Kredi Notu (TKN)", 500), errors='coerce') or 500
    teminat_val = pd.to_numeric(row.get("Teminat/Sigorta Kapsamı (%)", 0), errors='coerce') or 0
    esik_val = pd.to_numeric(row.get("Bilanço Direnci / İflas Eşiği (%)", 40), errors='coerce') or 40

    node_status[unvan] = {
        "kkb": kkb_val, "teminat": teminat_val, "esik": esik_val, "ciro": ciro, "hacim_bizimle": hacim,
        "kredi_riski": kredi_limit, "hasar_orani": 0.0, "durum": "Safe", "sebep": ""
    }
    banka_kredi_riski += kredi_limit

merkez_ciro = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith(("600","601"))]["Bakiye"].sum() if "Bakiye" in mizan_df.columns else 100_000_000
if merkez_ciro == 0: merkez_ciro = 100_000_000
node_status["ANA_MUSTERIMIZ"] = {"kkb": 750, "teminat": 100, "esik": 50, "ciro": merkez_ciro, "kredi_riski": 0, "hasar_orani": 0.0, "durum": "Safe", "sebep": ""}

npl_beklentisi = 0.0

if krize_giren != "(Seçiniz)" and krize_giren in node_status:
    node_status[krize_giren]["hasar_orani"] = 100.0
    node_status[krize_giren]["durum"] = "Failed"
    npl_beklentisi += node_status[krize_giren]["kredi_riski"]
    
    # 1. Dalga
    batan_ile_hacim = node_status[krize_giren]["hacim_bizimle"]
    bagimlilik = batan_ile_hacim / node_status["ANA_MUSTERIMIZ"]["ciro"]
    # Merkez müşterimizin teminat koruması batan firmaya özel
    merkez_hasar_katsayisi = (100 - node_status[krize_giren]["teminat"])/100.0 
    
    ana_hasar = (100.0 * bagimlilik * ((1000 - 750)/400.0) * merkez_hasar_katsayisi)
    node_status["ANA_MUSTERIMIZ"]["hasar_orani"] += ana_hasar
    
    if node_status["ANA_MUSTERIMIZ"]["hasar_orani"] >= node_status["ANA_MUSTERIMIZ"]["esik"]: 
        node_status["ANA_MUSTERIMIZ"]["durum"] = "Failed"
    elif node_status["ANA_MUSTERIMIZ"]["hasar_orani"] >= (node_status["ANA_MUSTERIMIZ"]["esik"]/2): 
        node_status["ANA_MUSTERIMIZ"]["durum"] = "Warning"

    # 2. Dalga (Ağ Bulaşması)
    for diger_firma in node_status:
        if diger_firma not in ["ANA_MUSTERIMIZ", krize_giren]:
            if random.random() < 0.35: # Ekosistem ticaret ihtimali
                d_bagimlilik = (node_status[diger_firma]["ciro"] * random.uniform(0.1, 0.5)) / node_status[diger_firma]["ciro"]
                d_kkb_kirilganlik = max(0.1, (1000 - node_status[diger_firma]["kkb"]) / 400.0)
                
                # FİRMA KENDİ TEMİNAT ORANIYLA KORUNUR
                d_teminat_katsayisi = (100 - node_status[diger_firma]["teminat"])/100.0
                
                node_status[diger_firma]["hasar_orani"] += (100.0 * d_bagimlilik * d_kkb_kirilganlik * d_teminat_katsayisi)
                
                # FİRMA KENDİ BİLANÇO DİRENCİ (EŞİĞİ) ÜZERİNDEN BATAR
                if node_status[diger_firma]["hasar_orani"] >= node_status[diger_firma]["esik"]:
                    node_status[diger_firma]["durum"] = "Failed"
                    npl_beklentisi += node_status[diger_firma]["kredi_riski"]
                elif node_status[diger_firma]["hasar_orani"] >= (node_status[diger_firma]["esik"]/2):
                    node_status[diger_firma]["durum"] = "Warning"

# ══════════════════════════════════════════════════════════════════════════════
# SEKMELER (TABS)
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🌐 Sistemik Stres Testi (Ekosistem Simülatörü)",
    "📊 Mizan Analiz ve İstihbarat Laboratuvarı",
    "🎯 Akıllı Pazarlama ve Çapraz Satış Portalı",
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: SİMÜLASYON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    batan_sayisi = sum(1 for k, v in node_status.items() if v["durum"] == "Failed" and k != "ANA_MUSTERIMIZ")
    npl_oran = (npl_beklentisi / banka_kredi_riski * 100) if banka_kredi_riski > 0 else 0
    
    with c1: st.markdown(f"""<div class="metric-card purple"><div class="metric-title">Toplam Ekosistem Hacmi</div><div class="metric-value">₺{sum(v['ciro'] for v in node_status.values())/1e6:.0f}M</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card success"><div class="metric-title">Banka Toplam Kredi Riski</div><div class="metric-value">₺{banka_kredi_riski/1e6:.1f}M</div></div>""", unsafe_allow_html=True)
    with c3:
        cls_bat = "danger" if batan_sayisi > 0 else "success"
        st.markdown(f"""<div class="metric-card {cls_bat}"><div class="metric-title">Batan Partner Sayısı</div><div class="metric-value">{batan_sayisi}</div></div>""", unsafe_allow_html=True)
    with c4:
        cls_npl = "danger" if npl_oran > 15 else ("warning" if npl_oran > 0 else "success")
        st.markdown(f"""<div class="metric-card {cls_npl}"><div class="metric-title">NPL (Batık) Beklentisi</div><div class="metric-value">₺{npl_beklentisi/1e6:.1f}M</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🕸️ Dinamik Tedarik Zinciri Ağ Haritası</div>', unsafe_allow_html=True)
    st.caption("Not: Her firmanın balonu üzerine fareyle geldiğinizde, firmaya özel İflas Eşiğini ve Teminat gücünü görebilirsiniz.")
    
    G = nx.DiGraph()
    m_stat = node_status["ANA_MUSTERIMIZ"]
    G.add_node("ANA MÜŞTERİMİZ", size=45, color="#ef4444" if m_stat["durum"]=="Failed" else ("#f59e0b" if m_stat["durum"]=="Warning" else "#1e3a8a"), title=f"<b>Ana Müşterimiz (Merkez)</b><br>Bilanço Hasarı: %{m_stat['hasar_orani']:.1f}")
    
    for unvan, data in node_status.items():
        if unvan == "ANA_MUSTERIMIZ": continue
        color = "#ef4444" if data["durum"]=="Failed" else ("#f59e0b" if data["durum"]=="Warning" else "#10b981")
        size = max(15, min(35, int((data["kredi_riski"]/5_000_000)*10) + 15))
        
        # Tooltip'e spesifik özellikleri ekledik
        tooltip = (f"<b>{unvan}</b><br>KKB Notu: {data['kkb']}<br>"
                   f"Teminat Koruma Oranı: %{data['teminat']}<br>"
                   f"Kırılma (İflas) Eşiği: %{data['esik']}<br>---<br>"
                   f"Anlık Hasar: %{data['hasar_orani']:.1f}<br>Durum: {data['durum']}")
                   
        G.add_node(unvan, size=size, color=color, title=tooltip, label=unvan[:15])
        G.add_edge(unvan, "ANA MÜŞTERİMİZ", color="#cbd5e1", width=max(1, int(data["hacim_bizimle"]/10_000_000)))
        if unvan != krize_giren and data["durum"] != "Safe": G.add_edge(krize_giren, unvan, color="#8b5cf6", dashes=True, width=2)

    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#0f172a", directed=True)
    net.from_nx(G)
    net.set_options("""{"physics": {"barnesHut": {"gravitationalConstant": -12000, "centralGravity": 0.3}}, "nodes": {"font": {"size": 13, "face": "Inter", "bold": true}}}""")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f: components.html(f.read(), height=520)
    os.unlink(tmp.name)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: LABORATUVAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.markdown('<div class="section-header">📋 Tam Mizan Veri Seti</div>', unsafe_allow_html=True)
        show_df = mizan_df.copy()
        if len(show_df.columns) == 7: show_df.columns = ["Hesap Kodu","Cari Unvanı","Sektör","Borç (TL)","Alacak (TL)","Bakiye (TL)","İşlem Hacmi (TL)"]
        st.dataframe(show_df, use_container_width=True, hide_index=True, height=450)
    with col_r:
        st.markdown('<div class="section-header">🔬 İnteraktif İstihbarat Matrisi (Firma Spesifik Parametreler)</div>', unsafe_allow_html=True)
        st.caption("Buradaki İflas Eşiği ve Teminat Kapsamı, Tab 1'deki iflas simülasyonunu *her firma için ayrı ayrı* etkiler.")
        
        # Sütun tiplerini ayarlıyoruz
        edited = st.data_editor(
            st.session_state.istihbarat,
            use_container_width=True, hide_index=True, height=450,
            column_config={
                "Cari Unvanı": st.column_config.TextColumn(disabled=True),
                "KKB Ticari Kredi Notu (TKN)": st.column_config.NumberColumn(min_value=0, max_value=1000),
                "Bilanço Direnci / İflas Eşiği (%)": st.column_config.NumberColumn(min_value=5, max_value=100, help="Firma cirosunun % kaçı kadar hasar alırsa iflas eder?"),
                "Teminat/Sigorta Kapsamı (%)": st.column_config.NumberColumn(min_value=0, max_value=100, help="Olası zararın % kaçı sigorta/teminat kapsamındadır?"),
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

    if "Bakiye" in mizan_df.columns:
        personel = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("335")]["Bakiye"].sum()
        if personel > 200_000: triggers.append({"Hesap Grubu":"335", "Tespit":f"Yüksek maaş borcu: ₺{personel:,.0f}", "Aksiyon":"Maaş Protokolü Teklifi", "Öncelik":"🔴 Yüksek"})

        cek_bakiye = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("101")]["Bakiye"].sum()
        alan_120 = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("120")]["Bakiye"].sum() or 1.0
        if (cek_bakiye / alan_120) > 0.10: triggers.append({"Hesap Grubu":"101", "Tespit":f"Çek birikimi: ₺{cek_bakiye:,.0f}", "Aksiyon":"Çek İskonto Teklifi", "Öncelik":"🟠 Orta"})

        ihracat = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("601")]["Bakiye"].sum()
        if ihracat > 500_000: triggers.append({"Hesap Grubu":"601", "Tespit":f"İhracat Geliri: ₺{ihracat:,.0f}", "Aksiyon":"Akreditif Finansmanı", "Öncelik":"🔴 Yüksek"})

    if triggers: st.dataframe(pd.DataFrame(triggers), use_container_width=True, hide_index=True)
    else: st.success("✅ Şu anda aktif çapraz satış tetikleyicisi bulunmamaktadır.")

    st.markdown('<div class="section-header">🔵 Modül: Yeni Müşteri Kazanım Listesi (Sıcak Fırsatlar)</div>', unsafe_allow_html=True)
    ist = st.session_state.istihbarat
    
    if not ist.empty:
        banka_col = "Bankamız Müşterisi mi?"
        kkb_col = "KKB Ticari Kredi Notu (TKN)"
        
        if banka_col in ist.columns and kkb_col in ist.columns:
            mask_musteri = ist[banka_col].fillna(False).astype(bool)
            mask_kkb = pd.to_numeric(ist[kkb_col], errors='coerce').fillna(0) >= 650
            potansiyel = ist[(~mask_musteri) & mask_kkb].copy()
            
            if not potansiyel.empty:
                potansiyel["Aksiyon"] = "📣 Portföy Yöneticisine Ata"
                hedef_kolonlar = ["Cari Unvanı", kkb_col, "Tahmini Yıllık Ciro (TL)", "Aksiyon"]
                gosterilecek_kolonlar = [col for col in hedef_kolonlar if col in potansiyel.columns]
                st.dataframe(potansiyel[gosterilecek_kolonlar], use_container_width=True, hide_index=True)
            else:
                st.info("Kriterlere uygun potansiyel müşteri bulunamadı.")
        else:
            st.warning("Verilerde 'Banka Müşterisi' veya 'KKB Notu' kolonları eksik. Lütfen sayfayı yenileyin.")
