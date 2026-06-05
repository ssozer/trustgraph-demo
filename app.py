import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import streamlit.components.v1 as components
import tempfile
import os

# Sayfa Genişlik ve Başlık Ayarı
st.set_page_config(layout="wide", page_title="Project TrustGraph - B2B Risk Platform", page_icon="🛡️")

st.title("🛡️ Project TrustGraph: Excel Tabanlı B2B Risk ve Pazarlama Portalı")
st.write("Excel Mizan Analizi, Kurumsal KKB, Memzuç ve Medya Duygu Analitiği ile Hibrit Skorlama")


# --- HAZIR VARSAYILAN MİZAN VERİSİ ---
@st.cache_data
def get_mock_mizan():
    # FIX: Boş DataFrame yerine sütunları tanımlı örnek veri döndür
    return pd.DataFrame([
        {"Cari_Unvan": "ABC Holding A.S.", "Hesap_Kodu": "120", "Borc": 500000.0, "Alacak": 300000.0},
        {"Cari_Unvan": "DEF Tedarik Ltd.", "Hesap_Kodu": "320", "Borc": 200000.0, "Alacak": 400000.0},
        {"Cari_Unvan": "GHI Alici A.S.",   "Hesap_Kodu": "120", "Borc": 150000.0, "Alacak": 100000.0},
        {"Cari_Unvan": "JKL Uretici Ltd.", "Hesap_Kodu": "320", "Borc": 300000.0, "Alacak": 250000.0},
        {"Cari_Unvan": "MNO Musteri A.S.", "Hesap_Kodu": "120", "Borc": 400000.0, "Alacak": 350000.0},
    ])


# --- SOL PANEL: DOSYA YÜKLEME VE PARAMETRELER ---
st.sidebar.header("📂 Excel Mizan Analiz Laboratuvarı")
uploaded_file = st.sidebar.file_uploader("Kurumsal Excel Mizanı Yükle (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        mizan_raw = pd.read_excel(uploaded_file)
        st.sidebar.success("Excel başarıyla yüklendi ve parse edildi!")
        mizan_df = mizan_raw.copy()
    except Exception as e:
        st.sidebar.error(f"Excel okunurken hata oluştu. Hazır örnek veri kullanılıyor. Hata: {e}")
        mizan_df = get_mock_mizan()
else:
    st.sidebar.info("Şu an örnek mizan verisi aktif. Kendi Excel'inizi yükleyebilirsiniz.")
    mizan_df = get_mock_mizan()

# İlk N Müşteri/Tedarikçi Seçimi
top_n = st.sidebar.slider("Analiz Edilecek İlk N Cari (Bakiye Büyüklüğüne Göre):", 2, 10, 5)

# --- SKORLAMA AĞIRLIK KAT SAYILARI ---
st.sidebar.subheader("⚙️ Risk Komitesi Ağırlık Katsayıları")
st.sidebar.caption("Toplam katsayının 1.0 olmasına dikkat ediniz.")
w_kkb  = st.sidebar.slider("KKB Skoru Ağırlığı:",          0.0, 1.0, 0.4, 0.05)
w_mem  = st.sidebar.slider("Memzuç Skoru Ağırlığı:",        0.0, 1.0, 0.3, 0.05)
w_news = st.sidebar.slider("Haber/Medya Risk Ağırlığı:",     0.0, 1.0, 0.2, 0.05)
w_con  = st.sidebar.slider("Konsantrasyon Risk Ağırlığı:",   0.0, 1.0, 0.1, 0.05)

total_w = w_kkb + w_mem + w_news + w_con
st.sidebar.write(f"**Toplam Katsayı Gücü:** {round(total_w, 2)}")
if abs(total_w - 1.0) > 0.01:
    st.sidebar.warning("⚠️ Katsayılar toplamı 1.0 olmalıdır! Lütfen ayarlayın.")


# --- ANALİZ MOTORU: BAKIYE VE HACİM HESAPLAMA ---
# FIX: Özgün satır: `mizan_df = (mizan_df - mizan_df["Alacak"]).abs()` → sütun bazlı doğru hesaplama
mizan_df["Bakiye"]      = (mizan_df["Borc"] - mizan_df["Alacak"]).abs()
mizan_df["Islem_Hacmi"] = mizan_df["Borc"] + mizan_df["Alacak"]

# FIX: `mizan_df.str.contains(...)` → doğrusu: sütun üzerinde filtreleme
df_120 = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.contains("120")].sort_values(
    by="Islem_Hacmi", ascending=False).head(top_n)
df_320 = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.contains("320")].sort_values(
    by="Islem_Hacmi", ascending=False).head(top_n)

final_caris = pd.concat([df_120, df_320], ignore_index=True)

total_mizan_volume = mizan_df["Islem_Hacmi"].sum()
if total_mizan_volume == 0:
    total_mizan_volume = 1.0


# --- İNTERAKTİF RİSK GİRDİLERİ ---
st.subheader("📝 İstihbarat Matrisi ve Dynamic Data Editor")
st.write("Sistem, Excel'den en büyük alıcı ve satıcılarınızı ayıkladı. Bu firmalar için KKB, Memzuç ve Haber skorlarını jüri önünde değiştirebilirsiniz:")

if "intelligence_df" not in st.session_state or len(st.session_state.intelligence_df) != len(final_caris):
    intel_records = []  # FIX: `intel_records =` → boş liste eksikti
    for _, row in final_caris.iterrows():
        default_kkb  = 20.0 if "Holding" in row["Cari_Unvan"] or "A.S." in row["Cari_Unvan"] else 50.0
        default_mem  = 15.0 if "A.S."    in row["Cari_Unvan"] else 40.0
        default_news = 10.0 if "A"       in row["Cari_Unvan"] else 60.0

        intel_records.append({
            "Cari Unvanı":                        row["Cari_Unvan"],
            "Hesap Tipi":                         str(row["Hesap_Kodu"]),  # FIX: `row` → row["Hesap_Kodu"]
            "Ticari Hacim (TL)":                  float(row["Islem_Hacmi"]),
            "KKB Risk Puanı (0-100)":             default_kkb,
            "Memzuç Limit/Risk Oranı (0-100)":    default_mem,
            "Medya/Haber Risk Puanı (0-100)":     default_news,
        })
    st.session_state.intelligence_df = pd.DataFrame(intel_records)

edited_intel = st.data_editor(
    st.session_state.intelligence_df,
    use_container_width=True,
    disabled=["Cari Unvanı", "Hesap Tipi", "Ticari Hacim (TL)"],  # FIX: `disabled=` → düzenlenemez sütun listesi
    column_config={
        "KKB Risk Puanı (0-100)":          st.column_config.NumberColumn(min_value=0, max_value=100, step=1, format="%d pts"),
        "Memzuç Limit/Risk Oranı (0-100)": st.column_config.NumberColumn(min_value=0, max_value=100, step=1, format="%d %%"),
        "Medya/Haber Risk Puanı (0-100)":  st.column_config.NumberColumn(min_value=0, max_value=100, step=1, format="%d pts"),
        "Ticari Hacim (TL)":               st.column_config.NumberColumn(format="%d TL"),
    }
)
st.session_state.intelligence_df = edited_intel


# --- HİBRİT RİSK HESAPLAMA ---
calculated_records = []  # FIX: `calculated_records =` → boş liste eksikti
for _, row in edited_intel.iterrows():
    concentration_ratio = (row["Ticari Hacim (TL)"] / total_mizan_volume) * 100.0  # FIX: `row` → row["Ticari Hacim (TL)"]
    con_score = min(concentration_ratio * 2.0, 100.0)

    final_risk = (
        w_kkb  * row["KKB Risk Puanı (0-100)"] +           # FIX: `row` → ilgili sütun adları
        w_mem  * row["Memzuç Limit/Risk Oranı (0-100)"] +
        w_news * row["Medya/Haber Risk Puanı (0-100)"] +
        w_con  * con_score
    )

    calculated_records.append({
        "Firma":                  row["Cari Unvanı"],
        "Hesap Tipi":             row["Hesap Tipi"],          # FIX: `row` → row["Hesap Tipi"]
        "Hacim":                  row["Ticari Hacim (TL)"],   # FIX: `row` → row["Ticari Hacim (TL)"]
        "Konsantrasyon (%)":      round(concentration_ratio, 2),
        "Konsantrasyon Skoru":    round(con_score, 1),
        "Nihai Risk Skoru (%)":   round(final_risk, 1),
    })

results_df = pd.DataFrame(calculated_records)


# --- İNTERAKTİF EKOSİSTEM HARİTASI ---
st.subheader("🌐 Canlı Etkileşimli B2B Ekosistem Grafik Haritası")
st.caption("Müşteri mizanından çıkan ticari bağlar. Merkez firmadan müşterilere (Mavi oklar) ve tedarikçilerden merkez firmaya (Gri oklar) giden nakit/hizmet akışları:")

G = nx.DiGraph()
main_firm = "Merkez_Firma_A"
G.add_node(main_firm, size=35, color="#2c3e50", title="Analiz Edilen Ana Firma (Merkez_Firma_A)", final_risk=0.0, type="main")

for _, row in results_df.iterrows():
    node_name = row["Firma"]
    risk = row["Nihai Risk Skoru (%)"]  # FIX: `row` → row["Nihai Risk Skoru (%)"]

    if risk > 60.0:
        color = "#e74c3c"
        size  = 30
    elif risk > 30.0:
        color = "#f39c12"
        size  = 24
    else:
        color = "#2ecc71"
        size  = 20

    title_text = (
        f"Firma: {node_name}<br>"
        f"Ciro Payı: %{row['Konsantrasyon (%)']}<br>"   # FIX: `row['Konsantrasyon']` → row["Konsantrasyon (%)"]
        f"Nihai Risk Skoru: %{risk}"
    )
    G.add_node(node_name, size=size, color=color, title=title_text, final_risk=risk, type="partner")

    if "120" in str(row["Hesap Tipi"]):   # FIX: `row` → row["Hesap Tipi"]
        G.add_edge(main_firm, node_name, weight=row["Hacim"])
    else:
        G.add_edge(node_name, main_firm, weight=row["Hacim"])

net = Network(height="450px", width="100%", bgcolor="#ffffff", font_color="#000000", directed=True)

for node, attrs in G.nodes(data=True):
    net.add_node(node, label=node, size=attrs["size"], color=attrs["color"], title=attrs["title"])

for u, v, attrs in G.edges(data=True):
    net.add_edge(u, v, color="#95a5a6", width=2)

net.set_options("""
var options = {
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -10000,
      "centralGravity": 0.25,
      "springLength": 180
    }
  }
}
""")

with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
    net.save_graph(tmp.name)
    with open(tmp.name, 'r', encoding='utf-8') as f:
        html_string = f.read()
    components.html(html_string, height=480)
    os.unlink(tmp.name)


# --- ALT PANEL: RAPORLAMA ---
col_rep1, col_rep2 = st.columns(2)

with col_rep1:
    st.subheader("🚨 GNN Erken Uyarı ve Risk Skor Tablosu")
    # FIX: `results_df]` → köşeli parantez fazlasıydı
    st.dataframe(
        results_df.sort_values(by="Nihai Risk Skoru (%)", ascending=False),
        use_container_width=True,
        hide_index=True
    )

with col_rep2:
    st.subheader("🎯 Akıllı Pazarlama ve Limit Artırım Kararları")
    st.write("Sistem, riskten arındırılmış yüksek cirolu/güvenli toplulukları pazarlama ekiplerine otomatik raporlar:")

    marketing_actions = []  # FIX: `marketing_actions =` → boş liste eksikti
    for _, row in results_df.iterrows():
        risk      = row["Nihai Risk Skoru (%)"]   # FIX: `row` → row["Nihai Risk Skoru (%)"]
        hesap     = str(row["Hesap Tipi"])         # FIX: `row` → row["Hesap Tipi"]

        if risk < 35.0 and "120" in hesap:
            marketing_actions.append({
                "Önerilen Firma":   row["Firma"],
                "Öncelik":          "Yüksek (Güvenli Alıcı)",
                "Öneri Aksiyonu":   "Çapraz Satış & DBS Limit Artırımı",
            })
        elif risk > 60.0:
            marketing_actions.append({
                "Önerilen Firma":   row["Firma"],
                "Öncelik":          "KRİZ ALARMI",
                "Öneri Aksiyonu":   "Tedarik Risk Azaltma & Alacak Sigortası Talebi",
            })

    if marketing_actions:
        st.table(pd.DataFrame(marketing_actions))
    else:
        st.info("Aksiyona gerek duyulacak uç değerde bir firma bulunmamaktadır.")
