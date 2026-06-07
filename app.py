
Claude finished the response

import streamlit as st import networkx as nx from pyvis.network import Network import pandas as pd import streamlit.components.v1 as components import tempfile import os # Sayfa Genişlik ve Başlık Ayarı st.set_page_config(layout="wide", page_title="Project TrustGraph - PoC Demo", page_icon="🛡️")

pasted

kodu düzenle

10:02 PM
Kodun neyi düzenlememi istediğinizi biraz daha belirtin — ama bakıyorum, dosyada birkaç açık söz dizimi hatası var (eksik liste/dict değerleri, boş köşeli parantezler). Bunları düzeltip tam çalışır hale mi getireyim?

kodu çalışacak şekilde düzenle hataları gider

10:03 PM

Reading the skill for frontend
Reading the skill for frontend
Kodu inceledim. Tüm hataları giderip eksik verileri tamamlıyorum:


Created a file, read a file
Created a file, read a file
Düzeltilen hatalar şunlardı:

Eksik veriler

Cari_Unvan listesi boştu → 5 örnek firma adı eklendi
Sektor listesi boştu → 5 sektör eklendi (İnşaat, Tekstil, Gıda, Lojistik, Teknoloji)
Söz dizimi hataları

mizan_df["Sektor"].unique() — sütun adı eksikti
mizan_df["Borc_Toplam"] + mizan_df["Alacak_Toplam"] — sütun referansları eksikti
row["Sektor"] — tüm row erişimleri düzeltildi (köşeli parantez eksikti)
selected_shock_sector karşılaştırması "(Seçilmedi)" seçeneğiyle güvene alındı
report_data = [] — boş liste tanımı eksikti
f-string içindeki title_text tek satırdan çok satıra düzgün bölündü
Çalıştırmak için: streamlit run trustgraph_app.py


Trustgraph app
PY 

Want to be notified when Claude responds?




Claude is AI and can make mistakes. Please double-check responses.
Trustgraph app · PY
import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import streamlit.components.v1 as components
import tempfile
import os
 
# Sayfa Genişlik ve Başlık Ayarı
st.set_page_config(layout="wide", page_title="Project TrustGraph - PoC Demo", page_icon="🛡️")
 
st.title("🛡️ Project TrustGraph: Grafik Tabanlı Risk ve Pazarlama Portalı (PoC)")
st.write("Sektörel Krizlerin ve Partner Risklerinin Ekosisteme Canlı Bulaşma Simülasyonu")
 
# --- HAZIR SİMÜLASYON VERİ SETİ ---
if "mizan_data" not in st.session_state:
    st.session_state.mizan_data = pd.DataFrame({
        "Hesap_Kodu": ["120.01.001", "120.01.002", "320.01.001", "320.01.002", "120.01.003"],
        "Cari_Unvan": [
            "Anadolu İnşaat A.Ş.",
            "Karadeniz Tekstil Ltd.",
            "Ege Gıda San. A.Ş.",
            "Marmara Lojistik A.Ş.",
            "İstanbul Teknoloji Ltd."
        ],
        "Sektor": [
            "İnşaat",
            "Tekstil",
            "Gıda",
            "Lojistik",
            "Teknoloji"
        ],
        "Borc_Toplam": [500000.0, 150000.0, 0.0, 0.0, 300000.0],
        "Alacak_Toplam": [0.0, 0.0, 400000.0, 600000.0, 0.0]
    })
 
mizan_df = st.session_state.mizan_data.copy()
 
# --- SOL PANEL: SİMÜLASYON PARAMETRELERİ ---
st.sidebar.header("⚙️ Ekosistem Simülasyon Odası")
 
# Sektör Seçimi ve Şok Oranı
sectors = sorted(list(mizan_df["Sektor"].unique()))
selected_shock_sector = st.sidebar.selectbox(
    "Krize Girecek Sektörü Seçin (Sektörel Şok):",
    ["(Seçilmedi)"] + sectors
)
 
shock_intensity = st.sidebar.slider("Sektörel Kriz Şiddeti (%):", 0, 100, 0)
 
# Risk Bulaşma Parametresi
alpha = st.sidebar.slider("Risk Bulaşma Yayılım Katsayısı (α):", 0.1, 1.0, 0.5)
 
# --- ANALİZ VE RISK HESAPLAMA MOTORU ---
mizan_df["Islem_Hacmi"] = mizan_df["Borc_Toplam"] + mizan_df["Alacak_Toplam"]
total_mizan_volume = mizan_df["Islem_Hacmi"].sum() if mizan_df["Islem_Hacmi"].sum() > 0 else 1.0
 
# 1. Partnerlerin Kendi Bağımsız Risk Puanlarını Hesapla
partner_risks = {}
for idx, row in mizan_df.iterrows():
    node_name = row["Cari_Unvan"]
    base_risk = 15.0
    if row["Sektor"] == selected_shock_sector:
        base_risk = float(shock_intensity)
    partner_risks[node_name] = base_risk
 
# 2. Ekosistem Bulaşıcılık Riskiyle Merkez Firma Riskini Hesapla (Message Passing)
bulaşan_toplam_risk = 0.0
for idx, row in mizan_df.iterrows():
    node_name = row["Cari_Unvan"]
    ciro_payi = row["Islem_Hacmi"] / total_mizan_volume
    bulaşan_toplam_risk += (partner_risks[node_name] * ciro_payi) * alpha
 
merkez_final_risk = min(round(bulaşan_toplam_risk, 1), 100.0)
 
# --- İNTERAKTİF GRAFİK HARİTASI (NETWORKX & PYVIS) ---
st.subheader("🌐 Canlı Etkileşimli B2B Ekosistem Grafik Haritası")
st.caption("Sol panelden sektörel şok uyguladığınızda partner düğümlerinin ve ortadaki Merkez Firma'nın renk değişimini izleyin:")
 
G = nx.DiGraph()
main_firm = "Merkez_Firma_A"
 
# Merkez Düğümü Rengi (risk durumuna göre dinamik)
if merkez_final_risk > 50.0:
    merkez_color = "#e74c3c"   # Kırmızı
elif merkez_final_risk > 20.0:
    merkez_color = "#f39c12"   # Turuncu
else:
    merkez_color = "#2c3e50"   # Koyu Lacivert
 
G.add_node(
    main_firm,
    size=35,
    color=merkez_color,
    title=f"Merkez Firma A<br>Toplam Bulaşan Risk: %{merkez_final_risk}",
    type="main"
)
 
# Partner Düğümlerini Ekle
for idx, row in mizan_df.iterrows():
    node_name = row["Cari_Unvan"]
    risk = partner_risks[node_name]
    ciro_percent = round((row["Islem_Hacmi"] / total_mizan_volume) * 100, 1)
 
    if risk > 60.0:
        color = "#e74c3c"
        size = 28
    elif risk > 30.0:
        color = "#f39c12"
        size = 23
    else:
        color = "#2ecc71"
        size = 18
 
    title_text = (
        f"Firma: {node_name}<br>"
        f"Sektör: {row['Sektor']}<br>"
        f"Ciro Payı: %{ciro_percent}<br>"
        f"Kendi Riski: %{risk}"
    )
    G.add_node(node_name, size=size, color=color, title=title_text, type="partner")
 
    if "120" in str(row["Hesap_Kodu"]):
        G.add_edge(main_firm, node_name)
    else:
        G.add_edge(node_name, main_firm)
 
# PyVis Render
net = Network(height="430px", width="100%", bgcolor="#ffffff", font_color="#000000", directed=True)
 
for node, attrs in G.nodes(data=True):
    net.add_node(node, label=node, size=attrs["size"], color=attrs["color"], title=attrs["title"])
 
for u, v in G.edges():
    net.add_edge(u, v, color="#bdc3c7", width=2)
 
net.set_options("""
var options = {
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -12000,
      "centralGravity": 0.3,
      "springLength": 160
    }
  }
}
""")
 
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
    net.save_graph(tmp.name)
    with open(tmp.name, "r", encoding="utf-8") as f:
        html_string = f.read()
    components.html(html_string, height=450)
    os.unlink(tmp.name)
 
# --- RAPORLAMA PANELLERİ ---
col_rep1, col_rep2 = st.columns(2)
 
with col_rep1:
    st.subheader("📊 Ekosistem Risk Dağılım Raporu")
    report_data = []
    for idx, row in mizan_df.iterrows():
        node_name = row["Cari_Unvan"]
        report_data.append({
            "Partner Firma": node_name,
            "Sektör": row["Sektor"],
            "Ciro Payı (%)": round((row["Islem_Hacmi"] / total_mizan_volume) * 100, 1),
            "Kendi Risk Puanı (%)": partner_risks[node_name]
        })
    st.dataframe(pd.DataFrame(report_data), use_container_width=True, hide_index=True)
 
with col_rep2:
    st.subheader("💡 Yönetim Komitesi Karar Destek Çıktısı")
    st.metric("Merkez Firma Toplam Risk Endeksi", f"%{merkez_final_risk}")
 
    if merkez_final_risk > 40.0:
        st.error(
            "⚠️ ACİL DURUM: Ekosistem risk seviyesi kritik eşiği aşmıştır! "
            "Sektörel daralma Merkez Firma'yı doğrudan tehdit etmektedir. "
            "Tedarikçi çeşitlendirmesi ve alacak sigortası yapılması önerilir."
        )
    elif merkez_final_risk > 15.0:
        st.warning(
            "⚡ YAKIN İZLEME: Bulaşıcı risk artış eğilimindedir. "
            "Portföy limit artışları askıya alınmalıdır."
        )
    else:
        st.success(
            "✅ GÜVENLİ EKOSİSTEM: Şirket ekosistemi ve ticari ağ yapısı son derece sağlıklıdır. "
            "DBS ve çapraz satış kampanyaları başlatılabilir."
        )
 
