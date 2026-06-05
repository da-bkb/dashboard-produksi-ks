import streamlit as st
import pandas as pd
import os
import numpy as np
import socket

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Production Kelapa Sawit - PT KS",
    page_icon="🌴",
    layout="wide"
)

# --- 2. DETEKSI ENVIRONMENT ---
def is_local_environment():
    hostname = socket.gethostname().upper()
    if "LAPTOP" in hostname or "DESKTOP" in hostname or "LOCAL" in hostname:
        return True
    return False

IS_LOCAL = is_local_environment()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- 4. FUNGSI LOADING DATA + REKONSILIASI AGUSTUS (AGT -> AGS) ---
@st.cache_data(ttl=3600)
def load_data(tipe_target):
    if tipe_target == "Budget":
        file_name = "Rekap26_KS_Bgt.csv"
        nama_target = "BUDGET"
    elif tipe_target == "Sensus":
        file_name = "Rekap26_KS_Sns.csv"
        nama_target = "SENSUS"
    else: 
        file_name = "Rekap26_KS_Pot.csv"
        nama_target = "POTENSI"
        
    if not os.path.exists(file_name):
        return pd.DataFrame(), nama_target

    try:
        df = pd.read_csv(file_name, sep=";", decimal=",", engine="python")
    except Exception:
        df = pd.read_csv(file_name, sep=",", decimal=",", engine="python")
        
    df.columns = df.columns.str.strip()
    
    # Standardisasi Nama Bulan: Ubah AGT hasil input CSV menjadi AGS agar seragam dengan sistem
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
        df['Bulan'] = df['Bulan'].replace({'AGT': 'AGS', 'AGUSTUS': 'AGS'})
        
    return df, nama_target


def aplikasi_utama():
    st.markdown("<h1 style='text-align: center; color: #1E5631;'>🌴 DASHBOARD PRODUKSI PT KS</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 👤 Sesi Pengguna")
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
            
    st.markdown("---")

    # --- 6. SUSUNAN FILTER UTAMA ---
    col1, col2, col3 = st.columns([1.8, 1.2, 1.5])

    with col1:
        pilihan_target = st.radio(
            "🎯 Capaian terhadap :",
            ["Budget", "Sensus", "Potensi"],
            horizontal=True,
            key="global_target_type_picker_ks"
        )

    df_raw, nama_target_label = load_data(pilihan_target)

    if df_raw.empty:
        st.error(f"⚠️ Berkas data `{pilihan_target}` tidak ditemukan! Pastikan file CSV diletakkan di folder yang sama.")
        st.stop()

    with col2:
        # Urutan daftar pilihan di drop-down menggunakan AGS
        URUTAN_BULAN_DISPLAY = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
        opsi_tambahan = ["CAWU I", "CAWU II", "CAWU III", "SEMESTER I", "SEMESTER II"]
        list_bulan = URUTAN_BULAN_DISPLAY + opsi_tambahan
        
        pilihan_bulan = st.selectbox(
            "📅 Bulan Analisis:", 
            list_bulan, 
            index=4, # Default ke MEI
            key="global_month_picker_ks"
        )

    with col3:
        menu_analisis = st.selectbox(
            "📊 Pilih Menu Analisis:",
            ["Yield", "RJP", "BJR", "Trend per Kebun", "Trend per Afdeling"],
            key="menu_dashboard_navigator_ks"
        )

    st.markdown("---") 

    st.session_state["df_raw"] = df_raw
    st.session_state["pilihan_bulan"] = pilihan_bulan
    st.session_state["list_bulan"] = list_bulan
    st.session_state["pilihan_target"] = pilihan_target

    global_context = globals().copy()
    global_context.update(locals())

    if menu_analisis == "Yield":
        if pilihan_target == "Budget":
            file_tab = "tabs/yield_bgt.py"
        elif pilihan_target == "Sensus":
            file_tab = "tabs/yield_sns.py"
        else:
            file_tab = "tabs/yield_pot.py"
            
    elif menu_analisis == "RJP":
        if pilihan_target == "Budget":
            file_tab = "tabs/rjp_bgt.py"
        elif pilihan_target == "Sensus":
            file_tab = "tabs/rjp_sns.py"
        else:
            file_tab = "tabs/rjp_pot.py"
            
    elif menu_analisis == "BJR":
        if pilihan_target == "Budget":
            file_tab = "tabs/bjr_bgt.py"
        elif pilihan_target == "Sensus":
            file_tab = "tabs/bjr_sns.py"
        else:
            file_tab = "tabs/bjr_pot.py"
            
    elif menu_analisis == "Trend per Kebun":
        file_tab = "tabs/trend_kbn.py"
    elif menu_analisis == "Trend per Afdeling":
        file_tab = "tabs/trend_afd.py"

    if os.path.exists(file_tab):
        try:
            with open(file_tab, "r", encoding="utf-8") as f:
                code = f.read()
            exec(code, global_context)
        except Exception as e:
            st.error(f"💥 Gagal mengeksekusi sub-menu {menu_analisis} pada data {pilihan_target}: {e}")
    else:
        st.warning(f"⚠️ Berkas analisis `{file_tab}` tidak ditemukan di folder 'tabs/'.")


# --- GERBANG LOGIN ---
if not st.session_state["logged_in"]:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1E5631;'>🔐 KUNCI AKSES PT KS</h2>", unsafe_allow_html=True)
        
        with st.form("login_form_ks"):
            username = st.text_input("Username :")
            password = st.text_input("Password :", type="password")
            submit_button = st.form_submit_button("Masuk Ke System 🚀", use_container_width=True)
            
            if submit_button:
                if username == "AGRO.KS" and password == "Kumai2026.":
                    st.session_state["logged_in"] = True
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("⚠️ Kredensial Salah!")
else:
    aplikasi_utama()