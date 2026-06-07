import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import streamlit.components.v1 as components
import tempfile
import os
import io

# ── SAYFA AYARI ──────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Project TrustGraph",
    page_icon="🛡️"
)

# ── KURUMSAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background-color: #f0f2f6; }

    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    .stTabs [data-baseweb="tab-list"] {
        background: #1a2342;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #aab4d4;
        font-weight: 500;
        border-radius: 8px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #2563eb !important;
        color: white !important;
    }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 18px 22px;
        border-left: 5px solid #2563eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .metric-card.danger { border-left-color: #e74c3c; }
    .metric-card.warning { border-left-color: #f39c12; }
    .metric-card.success { border-left-color: #27ae60; }

    .metric-title { font-size: 12px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 28px; font-weight: 700; color: #1a2342; margin-top: 4px; }
    .metric-sub   { font-size: 12px; color: #9ca3af; margin-top: 2px; }

    .section-header {
        font-size: 15px;
        font-weight: 700;
        color: #1a2342;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 6px;
        margin-bottom: 16px;
        margin-top: 20px;
    }

    .action-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .tag-green  { background: #dcfce7; color: #166534; }
    .tag-orange { background: #fff7ed; color: #9a3412; }
    .tag-red    { background: #fee2e2; color: #991b1b; }
    .tag-blue   { background: #dbeafe; color: #1e40af; }

    .header-banner {
        background: linear-gradient(135deg, #1a2342 0%, #2563eb 100%);
        border-radius: 14px;
        padding: 22px 28px;
        color: white;
        margin-bottom: 20px;
    }
    .header-banner h1 { font-size: 22px; font-weight: 700; margin: 0; }
    .header-banner p  { font-size: 13px; opacity: 0.8; margin: 4px 0 0; }
</style>
""", unsafe_allow_html=True)

# ── BAŞLIK ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
  <h1>🛡️ Project TrustGraph &nbsp;|&nbsp; B2B Risk &amp; Pazarlama Yönetimi Platformu</h1>
  <p>Sektörel Krizlerin ve Partner Risklerinin Ekosisteme Canlı Bulaşma Simülasyonu · Kurumsal Bankacılık İstihbarat Platformu</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HAZIR MİZAN VERİ SETİ
# ══════════════════════════════════════════════════════════════════════════════
DEFAULT_MIZAN = pd.DataFrame({
    "Hesap_Kodu":    ["120.01.001","120.01.002","320.01.001","320.01.002",
                      "120.01.003","101.01.001","102.01.001","335.01.001",
                      "153.01.001","601.01.001"],
    "Cari_Unvan":    ["Anadolu İnşaat A.Ş.","Karadeniz Tekstil Ltd.",
                      "Ege Gıda San. A.Ş.","Marmara Lojistik A.Ş.",
                      "İstanbul Teknoloji Ltd.","Tahsil Edilecek Çekler",
                      "Diğer Banka Mevduatları","Aylık Personel Maaşları",
                      "Depodaki Ticari Mallar","Yurtdışı İhracat Gelirleri"],
    "Sektor":        ["İnşaat","Tekstil","Gıda","Lojistik","Teknoloji",
                      "Finans","Finans","İnsan Kaynakları","Stok","Dış Ticaret"],
    "Borc_Toplam":   [500000.0, 150000.0,      0.0,      0.0,
                      300000.0, 250000.0, 400000.0,      0.0,
                      450000.0,      0.0],
    "Alacak_Toplam": [     0.0,      0.0, 400000.0, 600000.0,
                           0.0,      0.0,      0.0, 350000.0,
                           0.0, 550000.0],
})

# Bakiye hesabı: aktif hesaplar borç ağırlıklı, pasif/gelir hesapları alacak ağırlıklı
AKTIF_PREFIXLER = ("101","102","120","150","153")
PASIF_PREFIXLER = ("103","300","320","335","600","601")

def hesapla_bakiye(row):
    kod = str(row["Hesap_Kodu"])
    prefix = kod.split(".")[0]
    if prefix in AKTIF_PREFIXLER:
        return abs(row["Borc_Toplam"] - row["Alacak_Toplam"])
    elif prefix in PASIF_PREFIXLER:
        return abs(row["Alacak_Toplam"] - row["Borc_Toplam"])
    return abs(row["Borc_Toplam"] - row["Alacak_Toplam"])

# ── SESSION STATE BAŞLAT ──────────────────────────────────────────────────────
if "mizan_data" not in st.session_state:
    df = DEFAULT_MIZAN.copy()
    df["Bakiye"] = df.apply(hesapla_bakiye, axis=1)
    df["Islem_Hacmi"] = df["Borc_Toplam"] + df["Alacak_Toplam"]
    st.session_state.mizan_data = df

# İstihbarat matrisini başlat (alıcı+satıcı firmalar için)
def init_istihbarat(mizan_df, n=5):
    firmalar = mizan_df[mizan_df["Hesap_Kodu"].str.startswith(("120","320"))].head(n).copy()
    ist = pd.DataFrame({
        "Cari Unvanı":                      firmalar["Cari_Unvan"].values,
        "KKB Ticari Kredi Notu (TKN)":      [750, 620, 810, 540, 700],
        "Ticari Borçluluk Endeksi (TBE)":   [30,  55,  20,  70,  35],
        "Medya/Haber Olumsuzluk Skoru":     [10,  40,  5,   60,  15],
        "DBS Anchor Bayi mi?":              [True, False, True, False, True],
        "Bankamız Müşterisi mi?":           [True, False, True, False, False],
        "Yıllık Ciro (TL)":                [5000000, 1500000, 8000000, 900000, 3000000],
        "POS Aylık Ciro (TL)":             [200000,  50000,  350000,  20000, 150000],
    })
    return ist

if "istihbarat" not in st.session_state:
    st.session_state.istihbarat = init_istihbarat(st.session_state.mizan_data)

# ══════════════════════════════════════════════════════════════════════════════
# SOL PANEL
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## ⚙️ Platform Kontrol Paneli")
st.sidebar.markdown("---")

# Excel Yükleme
st.sidebar.markdown("### 📂 Kurumsal Mizan Yükle")
uploaded = st.sidebar.file_uploader("Excel (.xlsx) Mizan Dosyası", type=["xlsx"])
if uploaded:
    try:
        raw = pd.read_excel(uploaded)
        raw.columns = ["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"]
        raw["Bakiye"]      = raw.apply(hesapla_bakiye, axis=1)
        raw["Islem_Hacmi"] = raw["Borc_Toplam"] + raw["Alacak_Toplam"]
        st.session_state.mizan_data  = raw
        st.session_state.istihbarat  = init_istihbarat(raw)
        st.sidebar.success("✅ Mizan başarıyla yüklendi!")
    except Exception as e:
        st.sidebar.error(f"Dosya okunamadı: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Ekosistem Simülasyon Odası")

mizan_df = st.session_state.mizan_data.copy()
sectors  = sorted(mizan_df["Sektor"].unique().tolist())

selected_sector   = st.sidebar.selectbox("Krize Girecek Sektör:", ["(Seçilmedi)"] + sectors)
shock_intensity   = st.sidebar.slider("Sektörel Kriz Şiddeti (%):", 0, 100, 0)
alpha             = st.sidebar.slider("Risk Bulaşma Katsayısı (α):", 0.1, 1.0, 0.5, 0.05)

st.sidebar.markdown("---")
n_slider = st.sidebar.slider("İstihbarat Matrisi Satır Sayısı (N):", 2, 10, 5)

# ══════════════════════════════════════════════════════════════════════════════
# RISK HESAPLAMA MOTORU
# ══════════════════════════════════════════════════════════════════════════════
total_hacim = mizan_df["Islem_Hacmi"].sum() or 1.0

partner_risks = {}
for _, row in mizan_df.iterrows():
    base = 15.0
    if row["Sektor"] == selected_sector:
        base = float(shock_intensity)
    partner_risks[row["Cari_Unvan"]] = base

bulaşma = sum(
    partner_risks[r["Cari_Unvan"]] * (r["Islem_Hacmi"] / total_hacim)
    for _, r in mizan_df.iterrows()
) * alpha
merkez_risk = min(round(bulaşma, 1), 100.0)

# ══════════════════════════════════════════════════════════════════════════════
# SEKMELER
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🌐 İlişkisel Ekosistem ve Risk Simülatörü",
    "📊 Mizan Analiz ve İstihbarat Laboratuvarı",
    "🎯 Akıllı Pazarlama ve Çapraz Satış Portalı",
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEKME 1 — EKOSİSTEM GRAFİĞİ VE RİSK SİMÜLATÖRÜ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    # Üst metrik kartları
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card_cls = "danger" if merkez_risk > 50 else ("warning" if merkez_risk > 20 else "success")
        st.markdown(f"""
        <div class="metric-card {card_cls}">
          <div class="metric-title">Merkez Firma Risk Endeksi</div>
          <div class="metric-value">%{merkez_risk}</div>
          <div class="metric-sub">GNN Message Passing · α={alpha}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        partner_count = mizan_df[mizan_df["Hesap_Kodu"].str.startswith(("120","320"))].shape[0]
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-title">Aktif Partner Sayısı</div>
          <div class="metric-value">{partner_count}</div>
          <div class="metric-sub">Alıcı + Tedarikçi</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        etkilenen = sum(1 for _, r in mizan_df.iterrows() if r["Sektor"] == selected_sector)
        st.markdown(f"""
        <div class="metric-card {'warning' if etkilenen > 0 else ''}">
          <div class="metric-title">Şoktan Etkilenen Partner</div>
          <div class="metric-value">{etkilenen}</div>
          <div class="metric-sub">{selected_sector if selected_sector != '(Seçilmedi)' else 'Şok uygulanmadı'}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-title">Toplam Mizan Hacmi</div>
          <div class="metric-value">₺{total_hacim/1e6:.1f}M</div>
          <div class="metric-sub">Borç + Alacak toplamı</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🌐 Canlı Etkileşimli B2B Ekosistem Grafik Haritası</div>', unsafe_allow_html=True)
    st.caption("Sol panelden sektörel şok uyguladığınızda partner düğümlerinin ve Merkez Firma'nın renklerinin değişimini izleyin.")

    # NetworkX Grafik
    G = nx.DiGraph()
    main_firm = "Merkez_Firma_A"

    if merkez_risk > 50:
        merkez_color = "#e74c3c"
    elif merkez_risk > 20:
        merkez_color = "#f39c12"
    else:
        merkez_color = "#2c3e50"

    G.add_node(main_firm, size=38, color=merkez_color,
               title=f"<b>Merkez Firma A</b><br>Bulaşan Risk: <b>%{merkez_risk}</b><br>α={alpha}")

    max_hacim = mizan_df["Islem_Hacmi"].max() or 1.0

    for _, row in mizan_df.iterrows():
        name  = row["Cari_Unvan"]
        risk  = partner_risks[name]
        cpct  = round(row["Islem_Hacmi"] / total_hacim * 100, 1)
        size  = 14 + int((row["Islem_Hacmi"] / max_hacim) * 24)

        if risk > 60:
            color = "#e74c3c"
        elif risk > 30:
            color = "#f39c12"
        else:
            color = "#27ae60"

        tip = (f"<b>{name}</b><br>Sektör: {row['Sektor']}<br>"
               f"Ciro Payı: %{cpct}<br>Risk: %{risk}")
        G.add_node(name, size=size, color=color, title=tip)

        if str(row["Hesap_Kodu"]).startswith("120"):
            G.add_edge(main_firm, name)
        elif str(row["Hesap_Kodu"]).startswith("320"):
            G.add_edge(name, main_firm)

    net = Network(height="480px", width="100%", bgcolor="#f8fafc",
                  font_color="#1a2342", directed=True)
    for node, attrs in G.nodes(data=True):
        net.add_node(node, label=node, size=attrs["size"],
                     color=attrs["color"], title=attrs["title"])
    for u, v in G.edges():
        net.add_edge(u, v, color="#94a3b8", width=2, arrows="to")

    net.set_options("""
    var options = {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -14000,
          "centralGravity": 0.35,
          "springLength": 180,
          "springConstant": 0.04
        },
        "minVelocity": 0.75
      },
      "nodes": { "font": { "size": 13, "face": "Inter" } },
      "edges": { "smooth": { "type": "dynamic" } }
    }
    """)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        tmp_path = tmp.name
    net.save_graph(tmp_path)
    with open(tmp_path, "r", encoding="utf-8") as f:
        html_str = f.read()
    components.html(html_str, height=490)
    os.unlink(tmp_path)

    # Karar Destek
    st.markdown('<div class="section-header">💡 Yönetim Komitesi Karar Destek Çıktısı</div>', unsafe_allow_html=True)
    if merkez_risk > 40:
        st.error("⚠️ ACİL DURUM: Ekosistem risk seviyesi kritik eşiği aştı! Sektörel daralma Merkez Firma'yı doğrudan tehdit ediyor. Tedarikçi çeşitlendirmesi ve alacak sigortası önerilir.")
    elif merkez_risk > 15:
        st.warning("⚡ YAKIN İZLEME: Bulaşıcı risk artış eğiliminde. Portföy limit artışları askıya alınmalıdır.")
    else:
        st.success("✅ GÜVENLİ EKOSİSTEM: Ticari ağ yapısı sağlıklı. DBS ve çapraz satış kampanyaları başlatılabilir.")

    # Risk Dağılım Tablosu
    st.markdown('<div class="section-header">📊 Ekosistem Risk Dağılım Raporu</div>', unsafe_allow_html=True)
    rapor = []
    for _, row in mizan_df.iterrows():
        rapor.append({
            "Partner Firma":      row["Cari_Unvan"],
            "Sektör":             row["Sektor"],
            "Hesap Kodu":         row["Hesap_Kodu"],
            "Ciro Payı (%)":      round(row["Islem_Hacmi"] / total_hacim * 100, 1),
            "Risk Puanı (%)":     partner_risks[row["Cari_Unvan"]],
            "Bulaşma Katkısı (%)": round(partner_risks[row["Cari_Unvan"]] * (row["Islem_Hacmi"] / total_hacim) * alpha, 2),
        })
    st.dataframe(pd.DataFrame(rapor), use_container_width=True, hide_index=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEKME 2 — MİZAN ANALİZ VE İSTİHBARAT LABORATUVARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown('<div class="section-header">📋 Mizan Veri Seti (TDHP)</div>', unsafe_allow_html=True)
        show_df = st.session_state.mizan_data[[
            "Hesap_Kodu","Cari_Unvan","Sektor",
            "Borc_Toplam","Alacak_Toplam","Bakiye","Islem_Hacmi"
        ]].copy()
        show_df.columns = ["Hesap Kodu","Cari Unvanı","Sektör",
                            "Borç (TL)","Alacak (TL)","Bakiye (TL)","İşlem Hacmi (TL)"]
        st.dataframe(show_df.style.format({
            "Borç (TL)":         "{:,.0f}",
            "Alacak (TL)":       "{:,.0f}",
            "Bakiye (TL)":       "{:,.0f}",
            "İşlem Hacmi (TL)":  "{:,.0f}",
        }), use_container_width=True, hide_index=True)

        # Özet metrikler
        aktif  = st.session_state.mizan_data[
            st.session_state.mizan_data["Hesap_Kodu"].str.startswith(tuple(AKTIF_PREFIXLER))
        ]["Bakiye"].sum()
        pasif  = st.session_state.mizan_data[
            st.session_state.mizan_data["Hesap_Kodu"].str.startswith(tuple(PASIF_PREFIXLER))
        ]["Bakiye"].sum()

        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f"""<div class="metric-card success">
              <div class="metric-title">Toplam Aktif</div>
              <div class="metric-value">₺{aktif/1e6:.2f}M</div>
            </div>""", unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""<div class="metric-card warning">
              <div class="metric-title">Toplam Pasif/Gelir</div>
              <div class="metric-value">₺{pasif/1e6:.2f}M</div>
            </div>""", unsafe_allow_html=True)
        with mc3:
            st.markdown(f"""<div class="metric-card">
              <div class="metric-title">Net Bakiye</div>
              <div class="metric-value">₺{(aktif-pasif)/1e6:.2f}M</div>
            </div>""", unsafe_allow_html=True)

    with col_r:
        st.markdown(f'<div class="section-header">🔬 İnteraktif İstihbarat Matrisi (İlk {n_slider} Firma)</div>', unsafe_allow_html=True)
        st.caption("Aşağıdaki değerleri doğrudan düzenleyebilirsiniz. Değişiklikler oturum boyunca korunur.")

        # n_slider değişince istihbarat matrisini yeniden oluştur
        ist_df = init_istihbarat(st.session_state.mizan_data, n=n_slider)

        # Mevcut session_state verilerini yeni satır sayısına göre birleştir
        mevcut = st.session_state.istihbarat
        if len(mevcut) != n_slider:
            st.session_state.istihbarat = ist_df

        edited = st.data_editor(
            st.session_state.istihbarat,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cari Unvanı": st.column_config.TextColumn("Cari Unvanı", disabled=True),
                "KKB Ticari Kredi Notu (TKN)":     st.column_config.NumberColumn(min_value=0,   max_value=1000, step=1),
                "Ticari Borçluluk Endeksi (TBE)":  st.column_config.NumberColumn(min_value=0,   max_value=100,  step=1),
                "Medya/Haber Olumsuzluk Skoru":    st.column_config.NumberColumn(min_value=0,   max_value=100,  step=1),
                "DBS Anchor Bayi mi?":              st.column_config.CheckboxColumn(),
                "Bankamız Müşterisi mi?":           st.column_config.CheckboxColumn(),
                "Yıllık Ciro (TL)":                st.column_config.NumberColumn(min_value=0, format="₺%d"),
                "POS Aylık Ciro (TL)":             st.column_config.NumberColumn(min_value=0, format="₺%d"),
            },
            key="ist_editor"
        )
        st.session_state.istihbarat = edited

        # Kalite skorları önizleme
        st.markdown('<div class="section-header">📐 Otomatik Kalite Skor Önizlemesi</div>', unsafe_allow_html=True)
        preview = edited.copy()
        preview["Q Skoru"] = (
            0.6 * (preview["KKB Ticari Kredi Notu (TKN)"] / 1000) +
            0.4 * (1 - preview["Ticari Borçluluk Endeksi (TBE)"] / 100)
        ).round(3)
        st.dataframe(preview[["Cari Unvanı","Q Skoru"]]
                     .sort_values("Q Skoru", ascending=False),
                     use_container_width=True, hide_index=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEKME 3 — AKILLI PAZARLAMA VE ÇAPRAZ SATIŞ PORTALI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    ist = st.session_state.istihbarat.copy()
    mdf = st.session_state.mizan_data.copy()

    # Ortak yardımcı: segment belirle
    def segmentle(ciro):
        if ciro >= 5_000_000:   return "Ticari"
        elif ciro >= 2_000_000: return "Orta KOBİ"
        else:                   return "Mikro KOBİ"

    # ── MODÜL 1: YENİ MÜŞTERİ EDİNİMİ ──────────────────────────────────────
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
        st.dataframe(
            mod1[["Cari Unvanı","KKB Ticari Kredi Notu (TKN)","Ticari Borçluluk Endeksi (TBE)",
                  "Yıllık Ciro (TL)","POS Aylık Ciro (TL)","Segment","Aksiyon"]],
            use_container_width=True, hide_index=True
        )

    # ── MODÜL 2: ALACAK KALİTESİ ÖLÇÜMÜ ────────────────────────────────────
    st.markdown('<div class="section-header">🔵 Modül 2 — Alacak Kalitesi Ölçümü (120 Hesap Grubu)</div>', unsafe_allow_html=True)
    alici_kodlar = mdf[mdf["Hesap_Kodu"].str.startswith("120")]["Cari_Unvan"].tolist()
    mod2 = ist[ist["Cari Unvanı"].isin(alici_kodlar)].copy()

    if mod2.empty:
        # Eşleşme yoksa tüm istihbaratı göster
        mod2 = ist.copy()

    mod2["Q_ar"] = (
        0.6 * (mod2["KKB Ticari Kredi Notu (TKN)"] / 1000) +
        0.4 * (1 - mod2["Ticari Borçluluk Endeksi (TBE)"] / 100)
    ).round(3)
    mod2["Kalite Etiketi"] = mod2["Q_ar"].apply(
        lambda q: "🏆 Yüksek Kaliteli Alacak" if q >= 0.70 else ("⚠️ Orta Risk" if q >= 0.50 else "🔴 Düşük Kalite")
    )
    st.dataframe(
        mod2[["Cari Unvanı","KKB Ticari Kredi Notu (TKN)","Ticari Borçluluk Endeksi (TBE)","Q_ar","Kalite Etiketi"]]
        .sort_values("Q_ar", ascending=False),
        use_container_width=True, hide_index=True
    )

    # ── MODÜL 3: TEDARİKÇİ KALİTESİ & DBS ──────────────────────────────────
    st.markdown('<div class="section-header">🟠 Modül 3 — Tedarikçi Kalitesi ve DBS Kampanyası (320 Hesap Grubu)</div>', unsafe_allow_html=True)
    satici_kodlar = mdf[mdf["Hesap_Kodu"].str.startswith("320")]["Cari_Unvan"].tolist()
    mod3 = ist[ist["Cari Unvanı"].isin(satici_kodlar)].copy()

    if mod3.empty:
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
    st.dataframe(
        mod3[["Cari Unvanı","Q_ap","DBS Anchor Bayi mi?","DBS Aksiyonu"]]
        .sort_values("Q_ap", ascending=False),
        use_container_width=True, hide_index=True
    )

    # ── MODÜL 4: GELİŞMİŞ ÇAPRAZ SATIŞ TETİKLEYİCİLERİ ────────────────────
    st.markdown('<div class="section-header">🎯 Modül 4 — Gelişmiş Çapraz Satış Tetikleyicileri (Kebir Hesap Analizi)</div>', unsafe_allow_html=True)

    triggers = []

    # 335 — Personel Maaşları
    personel = mdf[mdf["Hesap_Kodu"].str.startswith("335")]["Bakiye"].sum()
    if personel > 200_000:
        triggers.append({
            "Hesap Grubu":  "335 — Personel Maaşları",
            "Tespit":       f"Yüksek maaş borcu: ₺{personel:,.0f}",
            "Öneri/Aksiyon": "💼 Maaş Ödemesi Protokolü Teklifi + Çalışanlara Bireysel Kredi/Kart Satışı",
            "Öncelik":      "🔴 Yüksek",
        })

    # 101 — Alınan Çekler
    cek_bakiye  = mdf[mdf["Hesap_Kodu"].str.startswith("101")]["Bakiye"].sum()
    alan_120    = mdf[mdf["Hesap_Kodu"].str.startswith("120")]["Bakiye"].sum() or 1.0
    cek_oran    = cek_bakiye / alan_120
    if cek_oran > 0.30:
        triggers.append({
            "Hesap Grubu":  "101 — Tahsil Edilecek Çekler",
            "Tespit":       f"Çek portföyü oranı: %{cek_oran*100:.1f} (Eşik: %30)",
            "Öneri/Aksiyon": "✂️ Çek İskonto (Kırma) ve Tahsilat Finansmanı Teklifi",
            "Öncelik":      "🟠 Orta",
        })

    # 102 — Rakip Banka Mevduatı
    rakip_mevduat = mdf[mdf["Hesap_Kodu"].str.startswith("102")]["Bakiye"].sum()
    if rakip_mevduat > 0:
        triggers.append({
            "Hesap Grubu":  "102 — Diğer Banka Mevduatları",
            "Tespit":       f"Rakip bankadaki mevduat: ₺{rakip_mevduat:,.0f}",
            "Öneri/Aksiyon": "🏦 Mevduat ve POS Payı Kapma Kampanyası",
            "Öncelik":      "🟠 Orta",
        })

    # 153 — Stok Finansmanı
    stok = mdf[mdf["Hesap_Kodu"].str.startswith("153")]["Bakiye"].sum()
    if stok > 300_000:
        triggers.append({
            "Hesap Grubu":  "153 — Depodaki Ticari Mallar",
            "Tespit":       f"Yüksek stok hacmi: ₺{stok:,.0f}",
            "Öneri/Aksiyon": "📦 Stok Teminatlı İşletme Sermayesi Kredisi Önerisi",
            "Öncelik":      "🟢 Standart",
        })

    # 601 — İhracat Odaklılık
    ihracat = mdf[mdf["Hesap_Kodu"].str.startswith("601")]["Bakiye"].sum()
    toplam_satis = mdf[mdf["Hesap_Kodu"].str.startswith(("600","601"))]["Bakiye"].sum() or 1.0
    ihracat_oran = ihracat / toplam_satis
    if ihracat_oran >= 0.20:
        triggers.append({
            "Hesap Grubu":  "601 — Yurtdışı İhracat Gelirleri",
            "Tespit":       f"İhracat odaklılık oranı: %{ihracat_oran*100:.1f} (Eşik: %20)",
            "Öneri/Aksiyon": "🌍 İhracat Akreditif Finansmanı + FX Forward Döviz Koruması",
            "Öncelik":      "🔴 Yüksek",
        })

    if triggers:
        trig_df = pd.DataFrame(triggers)
        st.dataframe(trig_df, use_container_width=True, hide_index=True)

        # Özet sayaçlar
        tc1, tc2, tc3 = st.columns(3)
        yuksek = sum(1 for t in triggers if "Yüksek" in t["Öncelik"])
        orta   = sum(1 for t in triggers if "Orta"   in t["Öncelik"])
        std    = sum(1 for t in triggers if "Standart" in t["Öncelik"])
        with tc1:
            st.markdown(f"""<div class="metric-card danger">
              <div class="metric-title">Yüksek Öncelikli Aksiyon</div>
              <div class="metric-value">{yuksek}</div>
            </div>""", unsafe_allow_html=True)
        with tc2:
            st.markdown(f"""<div class="metric-card warning">
              <div class="metric-title">Orta Öncelikli Aksiyon</div>
              <div class="metric-value">{orta}</div>
            </div>""", unsafe_allow_html=True)
        with tc3:
            st.markdown(f"""<div class="metric-card success">
              <div class="metric-title">Standart Aksiyon</div>
              <div class="metric-value">{std}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Şu anda aktif çapraz satış tetikleyicisi bulunmamaktadır. Mizan verinizi güncelleyin.")

    # Pazarlama Özet Raporu İndir
    st.markdown('<div class="section-header">📥 Pazarlama Özet Raporu</div>', unsafe_allow_html=True)
    rapor_rows = []
    for _, r in ist.iterrows():
        q = round(0.6*(r["KKB Ticari Kredi Notu (TKN)"]/1000) + 0.4*(1-r["Ticari Borçluluk Endeksi (TBE)"]/100), 3)
        rapor_rows.append({
            "Firma":         r["Cari Unvanı"],
            "Müşteri mi?":   "Evet" if r["Bankamız Müşterisi mi?"] else "Hayır",
            "DBS Bayi mi?":  "Evet" if r["DBS Anchor Bayi mi?"] else "Hayır",
            "TKN":           r["KKB Ticari Kredi Notu (TKN)"],
            "TBE":           r["Ticari Borçluluk Endeksi (TBE)"],
            "Q Skoru":       q,
            "Segment":       segmentle(r["Yıllık Ciro (TL)"]),
        })
    rapor_df = pd.DataFrame(rapor_rows)
    st.dataframe(rapor_df, use_container_width=True, hide_index=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        rapor_df.to_excel(writer, index=False, sheet_name="Pazarlama Raporu")
        if triggers:
            pd.DataFrame(triggers).to_excel(writer, index=False, sheet_name="Çapraz Satış Tetikleyicileri")
    buf.seek(0)
    st.download_button(
        label="📥 Excel Raporu İndir",
        data=buf,
        file_name="trustgraph_pazarlama_raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
