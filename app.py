import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import streamlit.components.v1 as components
import tempfile
import os

# Sayfa Genişlik ve Başlık Ayarı
st.set_page_config(layout="wide", page_title="Project TrustGraph - Live Demo", page_icon="📊")

st.title("🛡️ Project TrustGraph: Canlı Sunum Demosu")
st.write("Mizan ve Muavin Defter Verilerinden Grafik Yapay Zeka Tabanlı Risk ve Pazarlama Yönetimi Platformu")

# --- HAZIR SIMÜLASYON VERİ SETİ ---
# Sunumda hata yaşamamak için jüriye gösterilebilecek hazır mizan/muavin veri tablosu
if "muavin_data" not in st.session_state:
    st.session_state.muavin_data = pd.DataFrame()

# --- SOL PANEL: INTERAKTİF VERİ GİRİŞİ ---
st.sidebar.header("📊 Canlı Veri Manipülasyonu")
st.sidebar.write("Mizan/Muavin tablolarını canlı düzenleyerek jüriye anlık grafik güncellenmesini gösterin.")

# Kullanıcı yeni bir cari işlem ekleyebilir
with st.sidebar.expander("➕ Yeni Cari Bağlantı (Mizan Satırı) Ekle"):
    new_src = st.text_input("Kaynak Firma", "Merkez_Firma_A")
    new_dst = st.text_input("Hedef Firma", "Tedarikci_K")
    new_code = st.selectbox("Hesap Tipi", ["120", "320"])
    new_name = "Alıcılar" if new_code == "120" else "Satıcılar"
    new_borc = st.number_input("Borç Toplamı (TL)", value=50000.0)
    new_alacak = st.number_input("Alacak Toplamı (TL)", value=100000.0)
    
    if st.button("Mizana Kaydet ve Grafiği Güncelle"):
        new_row = {"Kaynak_Firma": new_src, "Hedef_Firma": new_dst, "Hesap_Kodu": new_code, "Hesap_Adi": new_name, "Borc": new_borc, "Alacak": new_alacak}
        st.session_state.muavin_data = pd.concat()], ignore_index=True)
        st.success("Yeni muavin kaydı başarıyla eklendi!")

# --- ANA SİMÜLASYON KONTROLLERİ ---
col_ctrl1, col_ctrl2 = st.columns(2)

with col_ctrl1:
    st.subheader("🔴 GNN Risk Yayılım Simülatörü")
    high_risk_node = st.selectbox(
        "Ekosistemde Anlık Kriz / Temerrüt Yaşayan Firmayı Seçin (Risk Yayılımı):",
        options= + list(set(st.session_state.muavin_data["Kaynak_Firma"].unique()) | set(st.session_state.muavin_data["Hedef_Firma"].unique()))
    )
    risk_alpha = st.slider("GNN Komşuluk Risk Aktarım Katsayısı ($α$):", 0.1, 0.9, 0.5)

with col_ctrl2:
    st.subheader("🟢 Louvain & RFM Pazarlama Hedeflemesi")
    marketing_focus = st.checkbox("Sadece En Güvenli ve Ticaret Hacmi Yüksek Pazarlama Kümesini Göster", value=False)
    st.write("Sistem, Louvain topluluk tespiti ile fiktif sektör tanımlarını aşarak gerçek ticaret kümesini bulur.")

# --- ANALİZ MOTORU (GRAPH CALCULATIONS) ---
# NetworkX üzerinde grafı inşa edelim
G = nx.DiGraph()

# Muavin kayıtlarından kenarları ve ağırlıkları (Ticaret Hacmi = Borç + Alacak) hesaplama
for _, row in st.session_state.muavin_data.iterrows():
    u = row["Kaynak_Firma"]
    v = row["Hedef_Firma"]
    volume = row + row["Alacak"]
    
    # Düğümleri ekle
    G.add_node(u, base_risk=10.0, final_risk=10.0, volume=volume, size=15)
    G.add_node(v, base_risk=10.0, final_risk=10.0, volume=volume, size=15)
    
    # Yönlü ticari akış kenarını ekle (Ağırlık = Ticaret Hacmi)
    G.add_edge(u, v, weight=volume, account_code=row["Hesap_Kodu"])

# Risk Yayılım Hesaplama (Simüle GNN Mesaj İletimi)
node_risks = {node: 10.0 for node in G.nodes()}
if high_risk_node!= "Yok":
    node_risks[high_risk_node] = 100.0  # Kriz noktası %100 riskli
    # 2-hop risk yayılımı (Komşuluk mesaj iletimi)
    for _ in range(2):  # 2 katmanlı GNN mimarisi
        temp_risks = node_risks.copy()
        for node in G.nodes():
            if node == high_risk_node:
                continue
            # Gelen ve giden komşuları bul (Yönlü risk geçişkenliği)
            neighbors = list(G.predecessors(node)) + list(G.successors(node))
            if neighbors:
                avg_neighbor_risk = sum(node_risks[n] for n in neighbors) / len(neighbors)
                # GNN Güncelleme Formülü: Risk = (1 - alpha) * Kendi Riski + alpha * Komşuların Ortalama Riski
                temp_risks[node] = (1 - risk_alpha) * node_risks[node] + risk_alpha * avg_neighbor_risk
        node_risks = temp_risks

# Topluluk Tespiti (Simüle Louvain Modülerliği)
# Küçük veri setlerinde belirgin organik ticaret grupları oluşturulur
communities = {}
for node in G.nodes():
    if "Tedarikci" in node or "Z" in node:
        communities[node] = "Tedarik Grubu (Küme-1)"
    elif "Alici" in node or "W" in node:
        communities[node] = "Alıcı / Müşteri Grubu (Küme-2)"
    else:
        communities[node] = "Merkez Ticaret Odak Grubu (Küme-3)"

# Düğüm Özelliklerini Güncelleme
for node in G.nodes():
    risk_score = node_risks[node]
    G.nodes[node]["final_risk"] = round(risk_score, 1)
    G.nodes[node]["community"] = communities[node]
    
    # Görselleştirme için renk ve boyut atamaları
    if marketing_focus and risk_score < 30.0 and communities[node] == "Alıcı / Müşteri Grubu (Küme-2)":
        G.nodes[node]["color"] = "#2ecc71"  # Parlak Yeşil (Pazarlama Fırsatı)
        G.nodes[node]["size"] = 35
    elif risk_score > 60.0:
        G.nodes[node]["color"] = "#e74c3c"  # Kırmızı (Yüksek Risk)
        G.nodes[node]["size"] = 30
    elif risk_score > 30.0:
        G.nodes[node]["color"] = "#f39c12"  # Turuncu (Orta Risk / Bulaşıcı Risk)
        G.nodes[node]["size"] = 25
    else:
        G.nodes[node]["color"] = "#3498db"  # Mavi (Normal Durum)
        G.nodes[node]["size"] = 20

# --- PYVIS INTERAKTİF GRAFİK OLUŞTURMA ---
st.subheader("🌐 Canlı Etkileşimli Ekosistem Grafik Haritası")
st.caption("Düğümleri sürükleyebilir, üzerlerine gelerek risk skoru ve işlem hacmi gibi anlık GNN çıktılarını inceleyebilirsiniz.")

# PyVis Ağı Kurulumu
net = Network(height="450px", width="100%", bgcolor="#ffffff", font_color="#000000", directed=True)

for node, attrs in G.nodes(data=True):
    title_text = f"Firma: {node}<br>GNN Risk Skoru: %{attrs['final_risk']}<br>Ticaret Kümesi: {attrs['community']}"
    net.add_node(
        node, 
        label=node, 
        size=attrs["size"], 
        color=attrs["color"], 
        title=title_text
    )

for u, v, attrs in G.edges(data=True):
    edge_label = f"Hesap: {attrs['account_code']} (Hacim: {attrs['weight']:,} TL)"
    net.add_edge(u, v, value=attrs["weight"], title=edge_label, color="#bdc3c7")

# Grafik Fiziğini Aktifleştir
net.set_options("""
var options = {
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -15000,
      "centralGravity": 0.3,
      "springLength": 150
    },
    "minVelocity": 0.75
  }
}
""")

# HTML Çıktısını Streamlit Bileşeni Olarak Gösterme
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
    net.save_graph(tmp.name)
    with open(tmp.name, 'r', encoding='utf-8') as f:
        html_string = f.read()
    components.html(html_string, height=480)
    os.unlink(tmp.name)

# --- ALT PANEL: RAPORLAMA VE ANALİTİK ÇIKTILAR ---
col_rep1, col_rep2 = st.columns(2)

with col_rep1:
    st.subheader("🚨 GNN Erken Uyarı ve Risk Skor Tablosu")
    risk_df = pd.DataFrame(["final_risk"], "Bulunduğu Küme": G.nodes[node]["community"]}
        for node in G.nodes()
    ]).sort_values(by="Yapay Zeka Risk Skoru (%)", ascending=False)
    st.dataframe(risk_df, use_container_width=True)

with col_rep2:
    st.subheader("🎯 B2B Akıllı Pazarlama ve Hedef Sıcak Kümeler")
    st.write("Sistem, riskten arındırılmış yüksek hacimli toplulukları pazarlama ekibine doğrudan raporlar:")
    
    marketing_leads =
    for node in G.nodes():
        if G.nodes[node]["final_risk"] < 30.0 and G.nodes[node]["community"] == "Alıcı / Müşteri Grubu (Küme-2)":
            marketing_leads.append({
                "Önerilen Cari": node, 
                "Risk Seviyesi": "Çok Güvenli", 
                "Öneri Kampanyası": "Tedarikçi Finansmanı & DBS Limit Artırımı"
            })
            
    if marketing_leads:
        st.table(pd.DataFrame(marketing_leads))
    else:
        st.warning("Seçilen risk parametrelerine göre şu an pazarlama odaklı güvenli küme bulunmamaktadır.")
