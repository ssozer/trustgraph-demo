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
    .metric-card.danger  { border-left-color: #ef4444; background-color: #fef2f2; }
    .metric-card.warning { border-left-color: #f59e0b; background-color: #fffbeb; }
    .metric-card.success { border-left-color: #10b981; }
    .metric-card.purple  { border-left-color: #8b5cf6; background-color: #f5f3ff; }
    .metric-card.blue    { border-left-color: #3b82f6; background-color: #eff6ff; }
    .metric-title { font-size: 12px; color: #475569; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 26px; font-weight: 800; color: #0f172a; margin-top: 4px; }
    .metric-sub   { font-size: 12px; color: #64748b; margin-top: 4px; font-weight: 500; }
    .section-header { font-size: 16px; font-weight: 700; color: #0f172a;
        border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 16px; margin-top: 24px; }
    .header-banner { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        border-radius: 14px; padding: 24px 32px; color: white; margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .header-banner h1 { font-size: 24px; font-weight: 700; margin: 0; letter-spacing: -0.02em; }
    .header-banner p  { font-size: 14px; opacity: 0.85; margin: 6px 0 0; }
    .sektor-badge { display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 700; margin-bottom: 8px; }
    .badge-insaat  { background: #fef3c7; color: #92400e; }
    .badge-tekstil { background: #fce7f3; color: #9d174d; }
    .badge-turizm  { background: #d1fae5; color: #065f46; }
    .badge-otomobil { background: #dbeafe; color: #1e40af; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SEKTÖR VERİ SETLERİ
# ══════════════════════════════════════════════════════════════════════════════
SEKTOR_VERILERI = {
    "🏗️ İnşaat": {
        "renk_kodu": "badge-insaat",
        "merkez_unvan": "Yıldız İnşaat Holding A.Ş.",
        "firmalar": [
            ("Kaya Çimento Sanayi A.Ş.",          "Yapı Malzemeleri",     "320", 40_000_000),
            ("Demirtaş Çelik Konstrüksiyon Ltd.",  "Metal/Demir",          "320", 55_000_000),
            ("Atlas Hafriyat ve Nakliyat A.Ş.",    "Hafriyat/Lojistik",    "320", 25_000_000),
            ("Ege Mekanik ve Tesisat Ltd.",         "Taşeron/Tesisat",      "320", 15_000_000),
            ("Marmara Akaryakıt Dağıtım A.Ş.",     "Enerji",               "320", 12_000_000),
            ("Öncü İş Makinaları Kiralama Ltd.",    "Otomotiv/Kiralama",    "320", 18_000_000),
            ("Dizayn Mimarlık ve Müh. Ltd.",        "Mühendislik/Hizmet",   "320",  5_000_000),
            ("Vadi Yapı Taşeron Hiz. A.Ş.",        "İnşaat/Taşeron",       "320",  9_000_000),
            ("Ankara Prefabrik Yapı Ltd.",          "Yapı Malzemeleri",     "320", 22_000_000),
            ("Güneş Alüminyum Doğrama A.Ş.",       "Doğrama/Pencere",      "320", 11_000_000),
            ("Zirve GYO A.Ş.",                     "Gayrimenkul",          "120", 35_000_000),
            ("Bosphorus Lojistik A.Ş.",            "Lojistik",             "120", 22_000_000),
            ("Metropol Konut Projesi Ltd.",         "Konut Geliştirme",     "120", 48_000_000),
            ("Stargate Rezidans A.Ş.",              "Konut/Ticari",         "120", 31_000_000),
            ("Türkiye Altyapı İnş. A.Ş.",          "Altyapı/Yol",          "120", 27_000_000),
        ],
        "sabitler": [
            ("101.01.001","Tahsil Edilecek Çekler (İnşaat)",   "Finans",        2_500_000.0,  0.0),
            ("102.01.001","Garanti Bankası Vadesiz Mevduat",   "Finans",          400_000.0,  0.0),
            ("102.02.001","Ziraat Bankası Yatırım Fon Hesabı", "Finans",        3_400_000.0,  0.0),
            ("103.01.001","Verilen Çekler ve Ödeme Emirleri",  "Finans",                0.0,  1_200_000.0),
            ("120.01.999","Yurtiçi Alt Bayi Alıcılar (100+)",  "Satış",        18_500_000.0,  0.0),
            ("153.01.001","Depodaki İnşaat Malzemeleri",       "Stok",          1_450_000.0,  0.0),
            ("172.01.001","Yıllara Sair İnşaat Maliyetleri",  "İnşaat",        5_600_000.0,  0.0),
            ("252.01.001","Şantiye Binaları ve Tesisler",      "Duran Varlık", 12_000_000.0,  0.0),
            ("254.01.001","Ticari Araç ve İş Makinaları",      "Duran Varlık",  4_500_000.0,  0.0),
            ("320.01.999","DBS Ana Bayileri (Çelik A.Ş.)",     "Tedarik",               0.0,  6_500_000.0),
            ("335.01.001","Aylık Personel Maaşları",           "İnsan Kay.",            0.0,    850_000.0),
            ("601.01.001","Yurtdışı İhracat Gelirleri",        "Dış Ticaret",           0.0,  3_500_000.0),
            ("600.01.001","Yurtiçi Satışlar",                  "Satış",                 0.0, 15_000_000.0),
        ],
        "potansiyel_musteriler": [
            ("Kartal İnşaat Yatırım A.Ş.",      820, 45_000_000, "Konut"),
            ("Ufuk Yapı Taahhüt Ltd.",           760, 28_000_000, "Altyapı"),
            ("Doruk Prefabrik Sistemler A.Ş.",   710, 19_000_000, "Endüstriyel"),
            ("Anadolu Kiremit Fabrikası",         780, 33_000_000, "Yapı Malzemeleri"),
            ("Mega Beton Santrali A.Ş.",          695, 22_000_000, "Beton"),
            ("Sümer Çatı Sistemleri Ltd.",        740, 14_000_000, "Çatı/Cephe"),
            ("Bozkurt İnşaat Taahhüt A.Ş.",      800, 51_000_000, "Konut/GYO"),
            ("Yeni Nesil Yapı Tek. Ltd.",         725, 17_500_000, "Teknolojik Yapı"),
        ],
    },

    "👗 Tekstil": {
        "renk_kodu": "badge-tekstil",
        "merkez_unvan": "Ege Tekstil Holding A.Ş.",
        "firmalar": [
            ("Bursa İplik Fabrikası A.Ş.",         "İplik/Ham Madde",      "320", 38_000_000),
            ("Adana Pamuk Tarım Koop.",             "Tarım/Ham Madde",      "320", 21_000_000),
            ("Denizli Dokuma Sanayi Ltd.",          "Dokuma/Kumaş",         "320", 29_000_000),
            ("Uludağ Boya ve Kimya A.Ş.",           "Kimya/Boya",           "320", 14_000_000),
            ("İstanbul Ambalaj ve Kargacılık Ltd.", "Lojistik/Ambalaj",     "320",  8_000_000),
            ("Özgün Konfeksiyon Mak. A.Ş.",         "Makine",               "320", 17_000_000),
            ("Batı Enerji Tekstil OSB Ltd.",        "Enerji",               "320",  6_500_000),
            ("Sürat Kargo Lojistik A.Ş.",           "Lojistik",             "320",  9_000_000),
            ("İzmir Fermuar ve Aksesuar Ltd.",      "Aksesuar",             "320",  4_500_000),
            ("Çorlu Yıkama ve Apre Fab. A.Ş.",      "Terbiye/Apre",         "320", 11_000_000),
            ("Modabase Hazır Giyim A.Ş.",           "Perakende/Moda",       "120", 42_000_000),
            ("Efes Dış Ticaret ve İhracat A.Ş.",   "İhracat",              "120", 35_000_000),
            ("Narin Tekstil Mağazacılık Ltd.",      "Mağaza Zinciri",       "120", 26_000_000),
            ("Trendset E-Ticaret A.Ş.",             "E-Ticaret",            "120", 18_000_000),
            ("Prima Denim Üretim A.Ş.",             "Denim/Özel",           "120", 31_000_000),
        ],
        "sabitler": [
            ("101.01.001","Tahsil Edilecek İhracat Çekleri",  "Finans",        1_800_000.0,  0.0),
            ("102.01.001","Akbank Vadesiz TL Hesabı",         "Finans",          320_000.0,  0.0),
            ("102.02.001","HSBC Döviz Yatırım Hesabı",        "Finans",        2_100_000.0,  0.0),
            ("103.01.001","Verilen Çekler (Tedarikçi Öd.)",   "Finans",                0.0,    980_000.0),
            ("120.01.999","Toptan Müşteri Ağı (150+ Mağaza)", "Satış",        22_000_000.0,  0.0),
            ("153.01.001","Mamul ve Yarı Mamul Stok",         "Stok",          3_200_000.0,  0.0),
            ("252.01.001","Fabrika ve Üretim Tesisleri",      "Duran Varlık",  9_500_000.0,  0.0),
            ("254.01.001","Dağıtım Araçları Filosu",          "Duran Varlık",  2_800_000.0,  0.0),
            ("320.01.999","DBS Tedarikçi Ağı (İplik/Kumaş)", "Tedarik",               0.0,  7_200_000.0),
            ("335.01.001","Fabrika Personel Maaşları",        "İnsan Kay.",            0.0,    620_000.0),
            ("601.01.001","AB ve ABD İhracat Gelirleri",      "Dış Ticaret",           0.0,  8_500_000.0),
            ("600.01.001","Yurtiçi Toptancı Satışları",       "Satış",                 0.0, 11_000_000.0),
        ],
        "potansiyel_musteriler": [
            ("Rüzgar Moda Tekstil A.Ş.",          840, 38_000_000, "Hazır Giyim"),
            ("Nil Dokuma ve İhracat Ltd.",         775, 24_000_000, "İhracat Odaklı"),
            ("Olimpos Spor Giyim A.Ş.",            720, 16_500_000, "Sportswear"),
            ("Çukurova Pamuk İşleme San.",         695, 19_000_000, "Ham Madde"),
            ("Süper Denim Fabrikası A.Ş.",         810, 43_000_000, "Denim"),
            ("Altın Nakış İşlemeciliği Ltd.",      750, 11_000_000, "Özel Üretim"),
            ("Moda Koleksiyon Dış Tic. A.Ş.",      800, 29_000_000, "İhracat/Perakende"),
            ("Kent Giyim Mağazaları Zinciri",      730, 35_000_000, "Perakende Zinciri"),
            ("Ata Çorap Örme Sanayi A.Ş.",         680, 13_500_000, "Çorap/Triko"),
            ("Yüksek Mod Tasarım Ev.",              870,  8_000_000, "Butik/Lüks"),
        ],
    },

    "🏨 Turizm": {
        "renk_kodu": "badge-turizm",
        "merkez_unvan": "Akdeniz Turizm ve Otelcilik A.Ş.",
        "firmalar": [
            ("Lara Gıda ve Catering Hiz. A.Ş.",   "Gıda/Catering",        "320", 18_000_000),
            ("Konak Temizlik Hiz. Ltd.",            "Temizlik/Outsource",   "320",  7_000_000),
            ("Antalya Çamaşırhane Endüstrisi",     "Çamaşır/Tekstil",      "320",  4_500_000),
            ("Güneş Güvenlik Sistemleri A.Ş.",     "Güvenlik",             "320",  5_200_000),
            ("Tur-İnşaat Renovasyon Ltd.",          "Tadilat/Bakım",        "320", 11_000_000),
            ("Akdeniz Akaryakıt Dağıtım A.Ş.",     "Enerji",               "320",  9_800_000),
            ("Dijital Menü Rez. Sistemleri",        "Teknoloji",            "320",  3_200_000),
            ("Elit Spa ve Wellness Ekip. Ltd.",     "Ekipman",              "320",  6_100_000),
            ("Travelport Tur Operatörü A.Ş.",      "Tur Operatörü",        "120", 27_000_000),
            ("Booking Network Acentecilik Ltd.",    "Acente/Online",        "120", 19_000_000),
            ("Blue Sea Yat ve Tekne A.Ş.",         "Deniz Turizmi",        "120", 14_000_000),
            ("Prestige Kongre ve Etkinlik Ltd.",    "MICE/Kongre",          "120", 12_500_000),
            ("Belek Golf ve Spor Tesisleri",        "Spor Turizmi",         "120", 16_000_000),
        ],
        "sabitler": [
            ("101.01.001","Tur ve Rezervasyon Çekleri",       "Finans",        1_200_000.0,  0.0),
            ("102.01.001","İş Bankası TL Mevduatı",          "Finans",          550_000.0,  0.0),
            ("102.02.001","Garanti EUR Hesabı (Turizm Gel.)", "Finans",        4_800_000.0,  0.0),
            ("103.01.001","Verilen Çekler (Sezon Alımları)",  "Finans",                0.0,    760_000.0),
            ("120.01.999","Online Acente ve OTA Alıcıları",   "Satış",        31_000_000.0,  0.0),
            ("153.01.001","Stok: Gıda, İçecek, Ambalaj",     "Stok",          2_100_000.0,  0.0),
            ("252.01.001","Otel Binaları ve Tatil Köyleri",   "Duran Varlık", 45_000_000.0,  0.0),
            ("254.01.001","Servis Araçları ve Transfer Filo", "Duran Varlık",  3_600_000.0,  0.0),
            ("320.01.999","DBS Turizm Tedarikçileri",         "Tedarik",               0.0,  5_400_000.0),
            ("335.01.001","Sezonluk Personel Maaşları",       "İnsan Kay.",            0.0,  1_100_000.0),
            ("601.01.001","Yabancı Turist Gelirleri (EUR)",   "Dış Ticaret",           0.0, 12_500_000.0),
            ("600.01.001","Yerli Turizm Gelirleri",           "Satış",                 0.0,  7_800_000.0),
        ],
        "potansiyel_musteriler": [
            ("Alanya Sahil Resort A.Ş.",           855, 22_000_000, "Resort Otel"),
            ("Kapadokya Butik Oteller Ltd.",        790, 9_500_000,  "Butik Otel"),
            ("Bodrum Marina Yatçılık A.Ş.",         740, 13_000_000, "Yat Turizmi"),
            ("Kusadasi Aquapark İşl. Ltd.",         715, 8_200_000,  "Eğlence/Park"),
            ("İstanbul Kongre Tur. A.Ş.",           820, 18_500_000, "MICE/Kongre"),
            ("Fethiye Kamp ve Doğa Tur. Ltd.",      700, 6_800_000,  "Doğa Turizmi"),
            ("Ege Kruvaziyer Terminal A.Ş.",        875, 31_000_000, "Kruvaziyer"),
            ("Göreme Kapadokya Tur Op. Ltd.",       760, 11_000_000, "Kültür Turizmi"),
            ("Antalya GolfRes. Yat. A.Ş.",          810, 25_000_000, "Golf/Spor"),
            ("Black Sea Premium Otelcilik",         730, 14_500_000, "Eko-Turizm"),
            ("Terme & Wellness Spa Zinciri",        780, 19_000_000, "Sağlık Turizmi"),
        ],
    },

    "🚗 Otomobil": {
        "renk_kodu": "badge-otomobil",
        "merkez_unvan": "Türkiye Otomotiv Distribütörleri A.Ş.",
        "firmalar": [
            ("Bursa Pres ve Döküm Sanayi A.Ş.",    "Yan Sanayi/Parça",     "320", 62_000_000),
            ("Sakarya Plastik Otomotiv Ltd.",       "Plastik Parça",        "320", 34_000_000),
            ("Kocaeli Motor ve Şanzıman A.Ş.",      "Motor/Mekanik",        "320", 48_000_000),
            ("Gebze Elektronik Sistemleri Ltd.",    "Elektronik/Otoelektrik","320", 27_000_000),
            ("Ankara Lastik Dağıtım A.Ş.",          "Yedek Parça/Lastik",   "320", 19_000_000),
            ("Kuzey Çelik Sac İşleme Ltd.",         "Metal/Sac",            "320", 41_000_000),
            ("Adapazarı Boyahane Sanayi A.Ş.",      "Boya/Kaplama",         "320", 15_000_000),
            ("İstanbul Lojistik Otomotiv Ltd.",     "Lojistik/Depo",        "320", 22_000_000),
            ("Mega Oto Galeri Zinciri A.Ş.",        "Galeri/Bayi",          "120", 88_000_000),
            ("Ekspres Araç Kiralama Ltd.",          "Kiralık Araç/Filo",    "120", 45_000_000),
            ("Dijital Oto Satış Platformu A.Ş.",    "E-Ticaret/Online",     "120", 33_000_000),
            ("Premium Fleet Filo Yönetimi Ltd.",    "Filo Yönetimi",        "120", 57_000_000),
            ("EV Şarj Ağları ve Teknoloji A.Ş.",    "Elektrikli Araç Altyapı","120", 21_000_000),
        ],
        "sabitler": [
            ("101.01.001","Bayi Satış Çekleri Portföyü",      "Finans",        4_200_000.0,  0.0),
            ("102.01.001","Yapı Kredi Vadesiz Mevduat",       "Finans",          780_000.0,  0.0),
            ("102.02.001","ING Bank EUR Yatırım Hesabı",      "Finans",        5_600_000.0,  0.0),
            ("103.01.001","Verilen Çekler (Tedarikçi Öd.)",   "Finans",                0.0,  2_400_000.0),
            ("120.01.999","Bayilik Ağı Alıcılar (200+ Bayi)","Satış",         65_000_000.0,  0.0),
            ("153.01.001","Araç Stoku ve Yedek Parça Depo",   "Stok",          8_900_000.0,  0.0),
            ("252.01.001","Showroom ve Servis Binaları",      "Duran Varlık",  18_000_000.0,  0.0),
            ("254.01.001","Test ve Hizmet Araçları Filosu",   "Duran Varlık",   7_200_000.0,  0.0),
            ("320.01.999","DBS Yan Sanayi Bayileri",          "Tedarik",               0.0, 12_500_000.0),
            ("335.01.001","Mühendis ve Teknik Personel Maaş", "İnsan Kay.",            0.0,  1_450_000.0),
            ("601.01.001","İhracat / CKD Parça Gelirleri",    "Dış Ticaret",           0.0,  9_200_000.0),
            ("600.01.001","Yurtiçi Araç ve Parça Satışları",  "Satış",                 0.0, 42_000_000.0),
        ],
        "potansiyel_musteriler": [
            ("Anadolu Hasarcar Oto Servis Zinciri", 830, 28_000_000, "Oto Servis"),
            ("Türkiye EV Araç Dağıtım A.Ş.",        875, 55_000_000, "Elektrikli Araç"),
            ("Konya Ticari Araç Bayisi Ltd.",        790, 33_000_000, "Ticari Araç Bayi"),
            ("Hızlı Filo Kiralama A.Ş.",             750, 47_000_000, "Filo Kiralama"),
            ("Yılmaz Lastik ve Yedek Parça A.Ş.",    715, 19_500_000, "Yedek Parça"),
            ("CarTech Dijital Otomotiv Ltd.",         860, 24_000_000, "Teknoloji/Platform"),
            ("Lüks Oto Aksesuar ve Tuning A.Ş.",     700, 12_000_000, "Aksesuar"),
            ("İstanbul Oto Ekspertiz Ağı Ltd.",       780, 16_500_000, "Ekspertiz"),
            ("Güvenli Araç Muayene Merkezi A.Ş.",    730, 21_000_000, "Muayene/Test"),
            ("Şarj Noktası Ağ İşletmecisi Ltd.",     820, 38_000_000, "EV Şarj Altyapı"),
            ("Komşu Motorlu Taşıtlar A.Ş.",          760, 29_000_000, "Çok Markalı Bayi"),
            ("Treyler ve Kamyon Bayii Ltd.",          800, 44_000_000, "Ağır Vasıta"),
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════
def build_mizan(sektor_adi):
    veri = SEKTOR_VERILERI[sektor_adi]
    rows = []
    for idx, (unvan, sek, prefix, hacim) in enumerate(veri["firmalar"]):
        hkod = f"{prefix}.01.{idx+1:03d}"
        borc, alacak = (float(hacim), 0.0) if prefix == "120" else (0.0, float(hacim))
        rows.append((hkod, unvan, sek, borc, alacak))
    for r in veri["sabitler"]:
        rows.append(r)
    return pd.DataFrame(rows, columns=["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"])

def hesapla_bakiye(row):
    prefix = str(row.get("Hesap_Kodu","")).split(".")[0]
    borc   = pd.to_numeric(row.get("Borc_Toplam",   0), errors="coerce") or 0.0
    alacak = pd.to_numeric(row.get("Alacak_Toplam", 0), errors="coerce") or 0.0
    if prefix in ("101","102","120","150","153","172","252","254"): return abs(borc - alacak)
    elif prefix in ("103","300","320","335","600","601"):           return abs(alacak - borc)
    return abs(borc - alacak)

def ensure_kolonlar(df):
    df = df.copy()
    if "Bakiye" not in df.columns:
        df["Bakiye"] = df.apply(hesapla_bakiye, axis=1)
    if "Islem_Hacmi" not in df.columns:
        df["Islem_Hacmi"] = (
            pd.to_numeric(df.get("Borc_Toplam",   0), errors="coerce").fillna(0) +
            pd.to_numeric(df.get("Alacak_Toplam", 0), errors="coerce").fillna(0)
        )
    return df

def init_istihbarat(mizan_df, sektor_adi, n=15):
    random.seed(42)
    _df = ensure_kolonlar(mizan_df.copy())
    firmalar = (
        _df[_df["Hesap_Kodu"].astype(str).str.startswith(("120","320"))]
        .sort_values("Islem_Hacmi", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )
    n_actual = len(firmalar)
    if n_actual == 0:
        return pd.DataFrame()

    tkn_list, sigorta_list, ciro_list, esik_list = [], [], [], []
    for _, row in firmalar.iterrows():
        hacim = row.get("Islem_Hacmi", 0)
        ciro  = int(hacim * random.uniform(1.5, 4.0))
        ciro_list.append(ciro)
        unvan = str(row.get("Cari_Unvan",""))
        risky = any(k in unvan for k in ["Taşeron","Hafriyat","Fabrika","Koop.","OSB"])
        kkb   = random.randint(400, 580) if risky else random.randint(680, 920)
        sig   = random.choice([0, 10, 20]) if risky else random.choice([50, 70, 80, 100])
        tkn_list.append(kkb)
        sigorta_list.append(sig)
        esik_list.append(int(max(15, min(65, (kkb / 1000) * 60))))

    return pd.DataFrame({
        "Cari Unvanı":                         firmalar["Cari_Unvan"].values,
        "KKB Ticari Kredi Notu (TKN)":         tkn_list,
        "Bilanço Direnci / İflas Eşiği (%)":   esik_list,
        "Teminat/Sigorta Kapsamı (%)":          sigorta_list,
        "Bankamız Müşterisi mi?":               [random.choice([True, False]) for _ in range(n_actual)],
        "Tahmini Yıllık Ciro (TL)":            ciro_list,
    })

# ══════════════════════════════════════════════════════════════════════════════
# SOL PANEL — SEKTÖR SEÇİMİ (Yeni ana kontrol)
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## ⚙️ Platform Kontrol Paneli")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🏭 Sektör Seçimi")

SEKTOR_LISTESI = list(SEKTOR_VERILERI.keys())
aktif_sektor = st.sidebar.selectbox(
    "Analiz Edilecek Sektörü Seçin:",
    SEKTOR_LISTESI,
    index=0,
    help="Sektör değiştirdiğinizde tüm mizan, firmalar ve analizler otomatik güncellenir."
)

# Sektör değiştiğinde session_state'i sıfırla
if st.session_state.get("aktif_sektor") != aktif_sektor:
    st.session_state.aktif_sektor    = aktif_sektor
    raw_mizan = build_mizan(aktif_sektor)
    st.session_state.mizan_data      = ensure_kolonlar(raw_mizan)
    st.session_state.istihbarat      = init_istihbarat(st.session_state.mizan_data, aktif_sektor)

# İlk çalışmada da init yap
if "mizan_data" not in st.session_state:
    raw_mizan = build_mizan(aktif_sektor)
    st.session_state.mizan_data = ensure_kolonlar(raw_mizan)
if "istihbarat" not in st.session_state:
    st.session_state.istihbarat = init_istihbarat(st.session_state.mizan_data, aktif_sektor)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Kendi Mizan Dosyanı Yükle")
uploaded = st.sidebar.file_uploader("Excel (.xlsx) Yükle", type=["xlsx"])
if uploaded:
    try:
        raw = pd.read_excel(uploaded)
        if len(raw.columns) >= 5:
            raw = raw.iloc[:, :5]
            raw.columns = ["Hesap_Kodu","Cari_Unvan","Sektor","Borc_Toplam","Alacak_Toplam"]
            raw["Hesap_Kodu"] = raw["Hesap_Kodu"].fillna("000").astype(str)
            raw["Cari_Unvan"] = raw["Cari_Unvan"].fillna("Bilinmeyen").astype(str)
            raw["Sektor"]     = raw["Sektor"].fillna("Diğer").astype(str)
            raw = ensure_kolonlar(raw)
            st.session_state.mizan_data  = raw
            st.session_state.istihbarat  = init_istihbarat(raw, aktif_sektor)
            st.sidebar.success("✅ Mizan başarıyla yüklendi!")
        else:
            st.sidebar.error("Hata: En az 5 kolon olmalı.")
    except Exception as e:
        st.sidebar.error(f"Hata: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌪️ Domino Stres Testi")
ist_df  = st.session_state.istihbarat
f_liste = ["(Seçiniz)"] + (ist_df["Cari Unvanı"].tolist() if not ist_df.empty and "Cari Unvanı" in ist_df.columns else [])
krize_giren = st.sidebar.selectbox("Temerrüde Düşen Firma:", f_liste)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER — Sektör bilgisiyle dinamik
# ══════════════════════════════════════════════════════════════════════════════
merkez_unvan = SEKTOR_VERILERI[aktif_sektor]["merkez_unvan"]
st.markdown(f"""
<div class="header-banner">
  <h1>🛡️ TrustGraph | B2B Ekosistem &amp; Pazarlama Platformu</h1>
  <p>Aktif Sektör: <b>{aktif_sektor}</b> &nbsp;·&nbsp; Merkez Firma: <b>{merkez_unvan}</b> &nbsp;·&nbsp;
     Tedarik Zinciri Stres Testi · Mizan Laboratuvarı · Akıllı Çapraz Satış</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SİMÜLASYON MOTORU
# ══════════════════════════════════════════════════════════════════════════════
mizan_df = st.session_state.mizan_data.copy()

toplam_hacim = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith(("120","320"))]["Islem_Hacmi"].sum() or 0
ciro_bakiye  = mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith(("600","601"))]["Bakiye"].sum() or 0
merkez_ciro  = max(ciro_bakiye, toplam_hacim * 1.5) or 100_000_000

node_status  = {}
banka_kredi_riski = 0.0

node_status["ANA_MUSTERIMIZ"] = {
    "kkb": 750, "teminat": 50, "esik": 50,
    "ciro": merkez_ciro, "kredi_riski": 0,
    "hasar_orani": 0.0, "durum": "Safe",
}

for _, row in ist_df.iterrows():
    unvan  = row.get("Cari Unvanı","")
    hacim  = mizan_df[mizan_df["Cari_Unvan"] == unvan]["Islem_Hacmi"].sum() if "Cari_Unvan" in mizan_df.columns else 0
    ciro   = max(pd.to_numeric(row.get("Tahmini Yıllık Ciro (TL)", hacim*2), errors="coerce") or hacim*2, hacim*1.1)
    kkb    = pd.to_numeric(row.get("KKB Ticari Kredi Notu (TKN)",   500), errors="coerce") or 500
    tem    = pd.to_numeric(row.get("Teminat/Sigorta Kapsamı (%)",     0), errors="coerce") or 0
    esik   = pd.to_numeric(row.get("Bilanço Direnci / İflas Eşiği (%)", 40), errors="coerce") or 40
    limit  = ciro * 0.15
    node_status[unvan] = {"kkb":kkb,"teminat":tem,"esik":esik,"ciro":ciro,
                           "hacim_bizimle":hacim,"kredi_riski":limit,
                           "hasar_orani":0.0,"durum":"Safe"}
    banka_kredi_riski += limit

tekil_npl = 0.0
npl_beklentisi = 0.0

if krize_giren != "(Seçiniz)" and krize_giren in node_status:
    node_status[krize_giren]["hasar_orani"] = 100.0
    node_status[krize_giren]["durum"]       = "Failed"
    tekil_npl       = node_status[krize_giren]["kredi_riski"]
    npl_beklentisi += tekil_npl

    batan_hacim   = node_status[krize_giren]["hacim_bizimle"]
    bagimlilik    = batan_hacim / merkez_ciro
    merkez_hasar  = (100.0 * bagimlilik * ((1000 - node_status["ANA_MUSTERIMIZ"]["kkb"]) / 400.0)
                     * (100 - node_status["ANA_MUSTERIMIZ"]["teminat"]) / 100.0)
    node_status["ANA_MUSTERIMIZ"]["hasar_orani"] += merkez_hasar
    if   node_status["ANA_MUSTERIMIZ"]["hasar_orani"] >= node_status["ANA_MUSTERIMIZ"]["esik"]:      node_status["ANA_MUSTERIMIZ"]["durum"] = "Failed"
    elif node_status["ANA_MUSTERIMIZ"]["hasar_orani"] >= node_status["ANA_MUSTERIMIZ"]["esik"] / 2:  node_status["ANA_MUSTERIMIZ"]["durum"] = "Warning"

    for diger in list(node_status.keys()):
        if diger in ("ANA_MUSTERIMIZ", krize_giren): continue
        if node_status[diger]["kkb"] < 650 or random.random() < 0.35:
            d_bag  = random.uniform(0.60, 0.90) if node_status[diger]["kkb"] < 650 else random.uniform(0.10, 0.30)
            d_kir  = max(0.2, (1000 - node_status[diger]["kkb"]) / 400.0)
            d_tem  = (100 - node_status[diger]["teminat"]) / 100.0
            hasar  = 100.0 * d_bag * d_kir * d_tem
            node_status[diger]["hasar_orani"] += hasar
            if   node_status[diger]["hasar_orani"] >= node_status[diger]["esik"]:      node_status[diger]["durum"] = "Failed"; npl_beklentisi += node_status[diger]["kredi_riski"]
            elif node_status[diger]["hasar_orani"] >= node_status[diger]["esik"] / 2:  node_status[diger]["durum"] = "Warning"

gizli_risk = max(npl_beklentisi - tekil_npl, 0.0)

# ══════════════════════════════════════════════════════════════════════════════
# SEKMELER
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "🌐 Sistemik Stres Testi (Ekosistem Simülatörü)",
    "📊 Mizan Analiz ve İstihbarat Laboratuvarı",
    "🎯 Akıllı Pazarlama ve Çapraz Satış Portalı",
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: STRES TESTİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card blue">
          <div class="metric-title">Banka Toplam Kredi Riski</div>
          <div class="metric-value">₺{banka_kredi_riski/1e6:.1f}M</div>
          <div class="metric-sub">Tüm Ekosistem Limiti</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card warning">
          <div class="metric-title">Tekil NPL (Geleneksel)</div>
          <div class="metric-value">₺{tekil_npl/1e6:.1f}M</div>
          <div class="metric-sub">Sadece Tetiklenen Firma</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card danger">
          <div class="metric-title">TrustGraph Domino NPL</div>
          <div class="metric-value">₺{npl_beklentisi/1e6:.1f}M</div>
          <div class="metric-sub">Zincirleme Batanlar Toplamı</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card purple">
          <div class="metric-title">💡 Yakalanan Gizli Risk</div>
          <div class="metric-value">₺{gizli_risk/1e6:.1f}M</div>
          <div class="metric-sub">Geleneksel Modelin Göremediği Fark</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🕸️ Dinamik Tedarik Zinciri Ağ Haritası</div>', unsafe_allow_html=True)

    G = nx.DiGraph()
    m = node_status["ANA_MUSTERIMIZ"]
    G.add_node(
        merkez_unvan, size=45,
        color="#ef4444" if m["durum"]=="Failed" else ("#f59e0b" if m["durum"]=="Warning" else "#1e3a8a"),
        title=f"<b>{merkez_unvan}</b><br>Bilanço Hasarı: %{m['hasar_orani']:.1f}<br>Durum: {m['durum']}"
    )
    for unvan, data in node_status.items():
        if unvan == "ANA_MUSTERIMIZ": continue
        color = "#ef4444" if data["durum"]=="Failed" else ("#f59e0b" if data["durum"]=="Warning" else "#10b981")
        size  = max(15, min(35, int((data["kredi_riski"] / 5_000_000) * 10) + 15))
        tip   = (f"<b>{unvan}</b><br>KKB: {data['kkb']}<br>"
                 f"Teminat: %{data['teminat']}<br>İflas Eşiği: %{data['esik']}<br>"
                 f"Hasar: %{data['hasar_orani']:.1f}<br>Durum: {data['durum']}")
        G.add_node(unvan, size=size, color=color, title=tip, label=unvan[:18])
        G.add_edge(unvan, merkez_unvan, color="#cbd5e1", width=max(1, int(data["hacim_bizimle"]/10_000_000)))
        if unvan != krize_giren and data["durum"] != "Safe" and krize_giren != "(Seçiniz)":
            G.add_edge(krize_giren, unvan, color="#8b5cf6", dashes=True, width=2)

    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#0f172a", directed=True)
    net.from_nx(G)
    net.set_options("""{"physics":{"barnesHut":{"gravitationalConstant":-12000,"centralGravity":0.3}},"nodes":{"font":{"size":13,"face":"Inter","bold":true}}}""")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        tmp_path = tmp.name
    net.save_graph(tmp_path)
    with open(tmp_path, "r", encoding="utf-8") as f:
        components.html(f.read(), height=520)
    os.unlink(tmp_path)

    # Stres test özet tablosu
    if krize_giren != "(Seçiniz)":
        st.markdown('<div class="section-header">📋 Domino Etki Analizi Tablosu</div>', unsafe_allow_html=True)
        tablo = []
        for unvan, data in node_status.items():
            if unvan == "ANA_MUSTERIMIZ": continue
            if data["durum"] != "Safe":
                tablo.append({
                    "Firma":              unvan,
                    "KKB Notu":           data["kkb"],
                    "Teminat (%)":        data["teminat"],
                    "İflas Eşiği (%)":    data["esik"],
                    "Hasar Oranı (%)":    round(data["hasar_orani"], 1),
                    "Durum":              data["durum"],
                    "Kredi Riski (TL)":   int(data["kredi_riski"]),
                })
        if tablo:
            st.dataframe(pd.DataFrame(tablo).sort_values("Hasar Oranı (%)", ascending=False),
                         use_container_width=True, hide_index=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: LABORATUVAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.markdown('<div class="section-header">📋 Tam Mizan Veri Seti</div>', unsafe_allow_html=True)
        disp = mizan_df.copy()
        disp.columns = ["Hesap Kodu","Cari Unvanı","Sektör","Borç (TL)","Alacak (TL)","Bakiye (TL)","İşlem Hacmi (TL)"]
        st.dataframe(disp.style.format({
            "Borç (TL)":        "{:,.0f}",
            "Alacak (TL)":      "{:,.0f}",
            "Bakiye (TL)":      "{:,.0f}",
            "İşlem Hacmi (TL)": "{:,.0f}",
        }), use_container_width=True, hide_index=True, height=460)

    with col_r:
        st.markdown('<div class="section-header">🔬 İnteraktif İstihbarat Matrisi</div>', unsafe_allow_html=True)
        st.caption("Değerler işlem hacmine göre büyükten küçüğe sıralanmıştır. Tüm alanları düzenleyebilirsiniz.")
        edited = st.data_editor(
            st.session_state.istihbarat,
            use_container_width=True, hide_index=True, height=460,
            column_config={
                "Cari Unvanı":                       st.column_config.TextColumn(disabled=True),
                "KKB Ticari Kredi Notu (TKN)":       st.column_config.NumberColumn(min_value=0,  max_value=1000),
                "Bilanço Direnci / İflas Eşiği (%)": st.column_config.NumberColumn(min_value=5,  max_value=100),
                "Teminat/Sigorta Kapsamı (%)":       st.column_config.NumberColumn(min_value=0,  max_value=100),
                "Bankamız Müşterisi mi?":            st.column_config.CheckboxColumn(),
                "Tahmini Yıllık Ciro (TL)":          st.column_config.NumberColumn(format="₺%d"),
            },
            key="ist_editor"
        )
        st.session_state.istihbarat = edited

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: PAZARLAMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:

    # ── MİZAN ODAKLI TETİKLEYİCİLER ─────────────────────────────────────────
    st.markdown('<div class="section-header">🎯 Modül 1: Mizan Satırlarından Zeki Çapraz Satış</div>', unsafe_allow_html=True)
    triggers = []

    def mizan_bakiye(prefix_tuple):
        return mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith(prefix_tuple)]["Bakiye"].sum()

    # 120 — DBS Ana Bayi
    for _, row in mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("120")].iterrows():
        if any(k in str(row["Cari_Unvan"]) for k in ["100+","150+","200+","Bayi","Ağı","Zinciri"]) or row["Bakiye"] > 10_000_000:
            triggers.append({"Hesap Grubu":"120 — Alıcılar","Tespit":"Geniş alıcı/bayi ağı tespit edildi",
                "Aksiyon":"DBS Ana Bayisi Yapılandırması — Merkezi Limit Tahsisi","Öncelik":"🔴 Yüksek"}); break

    # 320 — DBS Alt Bayi
    for _, row in mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("320")].iterrows():
        if any(k in str(row["Cari_Unvan"]) for k in ["DBS","Ana Bayi","Kuveyt","Bankamız"]):
            triggers.append({"Hesap Grubu":"320 — Satıcılar","Tespit":f"Bankamız DBS ağına bağlı tedarikçi: {row['Cari_Unvan']}",
                "Aksiyon":"DBS Alt Bayisi Olarak Tanımlama ve Otomatik Limit Tahsisi","Öncelik":"🔴 Yüksek"}); break

    # 103 — Çek Karnesi
    cek103 = mizan_bakiye(("103",))
    if cek103 > 0:
        triggers.append({"Hesap Grubu":"103 — Verilen Çekler","Tespit":f"Aktif çek ödemeleri: ₺{cek103:,.0f}",
            "Aksiyon":"Çek Karnesi ve Dijital Çek Finansmanı Ürünleri Teklifi","Öncelik":"🟠 Orta"})

    # 101 — Tahsil Edilecek Çekler
    cek101 = mizan_bakiye(("101",))
    alan120 = mizan_bakiye(("120",)) or 1.0
    if cek101 / alan120 > 0.20:
        triggers.append({"Hesap Grubu":"101 — Tahsil Edilecek Çekler","Tespit":f"Çek portföyü/alacak oranı %{cek101/alan120*100:.0f} (Eşik %20)",
            "Aksiyon":"Çek İskonto (Kırma) ve Alacak Tahsilat Finansmanı","Öncelik":"🟠 Orta"})

    # 102 — Rakip Banka Mevduatı/Yatırım
    for _, row in mizan_df[mizan_df["Hesap_Kodu"].astype(str).str.startswith("102")].iterrows():
        if row["Bakiye"] > 0:
            unvan_lower = str(row["Cari_Unvan"]).lower()
            if any(k in unvan_lower for k in ["yatırım","fon","hisse","portföy"]):
                triggers.append({"Hesap Grubu":"102 — Bankalar (Yatırım)","Tespit":f"Rakip yatırım hesabı: {row['Cari_Unvan']} → ₺{row['Bakiye']:,.0f}",
                    "Aksiyon":"Hisse Senedi / Katılım Fonu / TradePlus Hesap Açılışı","Öncelik":"🔴 Yüksek"})
            else:
                triggers.append({"Hesap Grubu":"102 — Bankalar (Mevduat)","Tespit":f"Rakip banka mevduatı: {row['Cari_Unvan']} → ₺{row['Bakiye']:,.0f}",
                    "Aksiyon":"Katılma Hesabı + Nakit Yönetimi + POS Payı Kapma Kampanyası","Öncelik":"🟢 Standart"})

    # 252 — Gayrimenkul / Sigorta
    bina = mizan_bakiye(("252",))
    if bina > 0:
        triggers.append({"Hesap Grubu":"252 — Binalar/Tesisler","Tespit":f"Aktif tesis/gayrimenkul: ₺{bina:,.0f}",
            "Aksiyon":"İşyeri Paket Sigortası + DASK Yenileme Teklifi","Öncelik":"🟠 Orta"})

    # 254 — Araç Filosu
    tasit = mizan_bakiye(("254",))
    if tasit > 0:
        triggers.append({"Hesap Grubu":"254 — Taşıtlar","Tespit":f"Ticari araç/filo tespiti: ₺{tasit:,.0f}",
            "Aksiyon":"Filo Kasko + Trafik Sigortası + Araç Finansmanı Paketi","Öncelik":"🟢 Standart"})

    # 172 — İnşaat Projesi
    insaat172 = mizan_bakiye(("172",))
    if insaat172 > 0:
        triggers.append({"Hesap Grubu":"172 — Yıllara Sair İnşaat","Tespit":f"Aktif şantiye/proje maliyetleri: ₺{insaat172:,.0f}",
            "Aksiyon":"İnşaat All Risk Sigortası + Proje Mevduat Yönetimi","Öncelik":"🔴 Yüksek"})

    # 153 — Stok Finansmanı
    stok153 = mizan_bakiye(("153",))
    if stok153 > 1_000_000:
        triggers.append({"Hesap Grubu":"153 — Stok","Tespit":f"Yüksek stok değeri: ₺{stok153:,.0f}",
            "Aksiyon":"Stok Teminatlı İşletme Sermayesi Kredisi","Öncelik":"🟠 Orta"})

    # 335 — Personel Maaşları
    maas = mizan_bakiye(("335",))
    if maas > 500_000:
        triggers.append({"Hesap Grubu":"335 — Personel Maaşları","Tespit":f"Yüksek maaş borcu: ₺{maas:,.0f}",
            "Aksiyon":"Maaş Ödemesi Protokolü + Çalışanlara Bireysel Kredi/Kart Satışı","Öncelik":"🟠 Orta"})

    # 601 — İhracat
    ihracat601 = mizan_bakiye(("601",))
    satis_top  = mizan_bakiye(("600","601")) or 1.0
    if ihracat601 / satis_top >= 0.25:
        triggers.append({"Hesap Grubu":"601 — İhracat Gelirleri","Tespit":f"İhracat oranı: %{ihracat601/satis_top*100:.0f} (Eşik %25)",
            "Aksiyon":"Akreditif Finansmanı + FX Forward Döviz Koruması + İhracat Kredisi","Öncelik":"🔴 Yüksek"})

    if triggers:
        t_df = pd.DataFrame(triggers)
        st.dataframe(t_df, use_container_width=True, hide_index=True)
        p1, p2, p3 = st.columns(3)
        y = sum(1 for t in triggers if "Yüksek"   in t["Öncelik"])
        o = sum(1 for t in triggers if "Orta"     in t["Öncelik"])
        s = sum(1 for t in triggers if "Standart" in t["Öncelik"])
        with p1: st.markdown(f"""<div class="metric-card danger"><div class="metric-title">Yüksek Öncelik</div><div class="metric-value">{y}</div></div>""", unsafe_allow_html=True)
        with p2: st.markdown(f"""<div class="metric-card warning"><div class="metric-title">Orta Öncelik</div><div class="metric-value">{o}</div></div>""", unsafe_allow_html=True)
        with p3: st.markdown(f"""<div class="metric-card success"><div class="metric-title">Standart</div><div class="metric-value">{s}</div></div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Aktif tetikleyici yok.")

    # ── YENİ MÜŞTERİ KAZANIM LİSTESİ ────────────────────────────────────────
    st.markdown('<div class="section-header">🟢 Modül 2: Yeni Müşteri Kazanım Listesi (Sıcak Fırsatlar)</div>', unsafe_allow_html=True)
    ist = st.session_state.istihbarat
    if not ist.empty and "Bankamız Müşterisi mi?" in ist.columns:
        potansiyel = ist[
            (~ist["Bankamız Müşterisi mi?"].fillna(False).astype(bool)) &
            (pd.to_numeric(ist["KKB Ticari Kredi Notu (TKN)"], errors="coerce").fillna(0) >= 650)
        ].copy()
        if not potansiyel.empty:
            potansiyel["Aksiyon"] = "📣 Portföy Yöneticisine Ata"
            st.dataframe(potansiyel[["Cari Unvanı","KKB Ticari Kredi Notu (TKN)",
                                     "Tahmini Yıllık Ciro (TL)","Teminat/Sigorta Kapsamı (%)","Aksiyon"]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("Mevcut istihbarat matrisinde kriterlere uyan potansiyel müşteri yok.")
    else:
        st.info("İstihbarat matrisi boş. Sekme 2'den verileri güncelleyin.")

    # ── SEKTÖRE ÖZEL POTANSİYEL MÜŞTERİ LİSTESİ ─────────────────────────────
    st.markdown(f'<div class="section-header">🏆 Modül 3: {aktif_sektor} Sektörü — Hedef Potansiyel Müşteri Havuzu</div>', unsafe_allow_html=True)
    st.caption("Bu liste mizan dışında, pazarlama ekibinin sahaya çıkabileceği bankamız müşterisi olmayan yüksek kaliteli firma havuzudur.")

    pot_list = SEKTOR_VERILERI[aktif_sektor]["potansiyel_musteriler"]
    pot_df   = pd.DataFrame(pot_list, columns=["Firma Adı","KKB Skoru (Tahmini)","Tahmini Ciro (TL)","Alt Sektör"])
    pot_df["Segment"] = pot_df["Tahmini Ciro (TL)"].apply(
        lambda c: "🏢 Kurumsal" if c >= 40_000_000 else ("🏭 Ticari" if c >= 20_000_000 else "🏬 KOBİ")
    )
    pot_df["Öncelikli Ürün"] = pot_df.apply(lambda r: (
        "Proje Finansmanı + DBS" if r["KKB Skoru (Tahmini)"] >= 800 else
        "İşletme Kredisi + Çek Karnesi" if r["KKB Skoru (Tahmini)"] >= 700 else
        "Temel Bankacılık Paketi"
    ), axis=1)
    pot_df["Aksiyon"] = "📞 Ziyaret Planla"
    st.dataframe(
        pot_df.sort_values("KKB Skoru (Tahmini)", ascending=False),
        use_container_width=True, hide_index=True
    )

    # Excel indirme
    st.markdown('<div class="section-header">📥 Rapor İndir</div>', unsafe_allow_html=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        mizan_df.to_excel(writer, index=False, sheet_name="Mizan")
        if not ist.empty:
            ist.to_excel(writer, index=False, sheet_name="İstihbarat Matrisi")
        if triggers:
            pd.DataFrame(triggers).to_excel(writer, index=False, sheet_name="Çapraz Satış Tetikleyicileri")
        pot_df.to_excel(writer, index=False, sheet_name="Potansiyel Müşteriler")
    buf.seek(0)
    st.download_button(
        label=f"📥 {aktif_sektor} Sektörü — Tam Raporu İndir",
        data=buf,
        file_name=f"trustgraph_{aktif_sektor.replace(' ','_').replace('/','')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
