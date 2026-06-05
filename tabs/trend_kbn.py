import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"].copy()
list_bulan = st.session_state["list_bulan"]
pilihan_target = st.session_state["pilihan_target"]

st.markdown(f"### 📈 Trend Produksi Bulanan Per Kebun ({pilihan_target})")

# --- 1. DETEKSI KOLOM TARGET SECARA DINAMIS MENGGUNAKAN LOGIKA PT KS ---
if pilihan_target == "Budget":
    col_tgt_kg = "Kg Bgt."
    col_tgt_jjg = "Jjg Bgt."
    col_tgt_bjr = "BJR Bgt."
    LABEL_TARGET = "Target Budget"
elif pilihan_target == "Sensus":
    col_tgt_kg = "Kg Sns."
    col_tgt_jjg = "Jjg Sns."
    col_tgt_bjr = "BJR Sns."
    LABEL_TARGET = "Target Sensus"
else:
    col_tgt_kg = "Kg Pot."
    col_tgt_jjg = "Jjg Pot."
    col_tgt_bjr = "BJR Pot."
    LABEL_TARGET = "Target Potensi"

# --- 2. PEMBERSIHAN DATA NUMERIK ---
def clean_general_numeric(df, col_name):
    if col_name in df.columns:
        df[col_name] = df[col_name].astype(str).str.strip()
        df[col_name] = df[col_name].replace({'-': '0', '': '0'}, regex=False)
        df[col_name] = df[col_name].str.replace(',', '.', regex=False)
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
    return df

kolom_wajib = ['Luas', 'Pokok', 'Kg Akt.', 'Jjg Akt.', col_tgt_kg, col_tgt_jjg, col_tgt_bjr]
for col in kolom_wajib:
    df_raw = clean_general_numeric(df_raw, col)

# --- 3. REKONSILIASI KODE BULAN AGUSTUS (AGT -> AGS) ---
if 'Bulan' in df_raw.columns:
    df_raw['Bulan'] = df_raw['Bulan'].astype(str).str.strip().str.upper()
    df_raw['Bulan'] = df_raw['Bulan'].replace({'AGT': 'AGS', 'AGUSTUS': 'AGS'})

# --- 4. FILTER SELECT BOX KEBUN ---
if 'Kebun' in df_raw.columns:
    list_kebun = sorted(list(df_raw['Kebun'].dropna().unique()))
    pilihan_kebun = st.selectbox("📍 Pilih Kebun:", list_kebun, key="trend_kebun_picker")
    df_filtered = df_raw[df_raw['Kebun'] == pilihan_kebun].copy()
else:
    df_filtered = df_raw.copy()

# --- 5. AGREGASI DATA TREN BULANAN JAN - DES ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
df_filtered['Bulan_Idx'] = df_filtered['Bulan'].apply(lambda x: URUTAN_BULAN_STD.index(x) if x in URUTAN_BULAN_STD else 99)
df_filtered = df_filtered[df_filtered['Bulan_Idx'] != 99]

df_trend = df_filtered.groupby(["Bulan_Idx", "Bulan"], observed=False).agg({
    'Kg Akt.': 'sum',
    'Jjg Akt.': 'sum',
    col_tgt_kg: 'sum',
    col_tgt_jjg: 'sum'
}).reset_index()

df_trend = df_trend.sort_values("Bulan_Idx").reset_index(drop=True)

# Ambil Luas dan Pokok tanpa duplikasi/inflasi level Kebun
df_luas = df_filtered.groupby(['Bulan', 'Afdeling'], observed=False)['Luas'].first().reset_index().groupby('Bulan', observed=False)['Luas'].sum().reset_index()
df_pokok = df_filtered.groupby(['Bulan', 'Afdeling'], observed=False)['Pokok'].first().reset_index().groupby('Bulan', observed=False)['Pokok'].sum().reset_index()

df_trend['Luas'] = df_trend['Bulan'].map(df_luas.set_index('Bulan')['Luas']).fillna(0)
df_trend['Pokok'] = df_trend['Bulan'].map(df_pokok.set_index('Bulan')['Pokok']).fillna(0)

# --- 6. HITUNG INDIKATOR UTAMA (Yield, RJP, BJR) ADAPTASI BKB/FFD ---
df_trend["Yield Akt."] = np.where(df_trend['Luas'] > 0, df_trend['Kg Akt.'] / 1000 / df_trend['Luas'], 0)
df_trend["Yield Bgt."] = np.where(df_trend['Luas'] > 0, df_trend[col_tgt_kg] / 1000 / df_trend['Luas'], 0)

df_trend["RJP Akt."] = np.where(df_trend['Pokok'] > 0, df_trend['Jjg Akt.'] / df_trend['Pokok'], np.where(df_trend['Luas'] > 0, df_trend['Jjg Akt.'] / (df_trend['Luas'] * 135), 0))
df_trend["RJP Bgt."] = np.where(df_trend['Pokok'] > 0, df_trend[col_tgt_jjg] / df_trend['Pokok'], np.where(df_trend['Luas'] > 0, df_trend[col_tgt_jjg] / (df_trend['Luas'] * 135), 0))

df_trend["BJR Akt."] = np.where(df_trend['Jjg Akt.'] > 0, df_trend['Kg Akt.'] / df_trend['Jjg Akt.'], 0)
df_trend["BJR Bgt."] = np.where(df_trend['Jjg Akt.'] > 0, df_trend[col_tgt_kg] / df_trend['Jjg Akt.'], df_trend['Bulan'].map(df_filtered.groupby('Bulan', observed=False)[col_tgt_bjr].mean()).fillna(0))

# Hitung Persentase Variansi (Format +/-)
df_trend["Yield_Pct"] = np.where(df_trend["Yield Bgt."] > 0, (df_trend["Yield Akt."] / df_trend["Yield Bgt."] * 100) - 100, 0)
df_trend["RJP_Pct"] = np.where(df_trend["RJP Bgt."] > 0, (df_trend["RJP Akt."] / df_trend["RJP Bgt."] * 100) - 100, 0)
df_trend["BJR_Pct"] = np.where(df_trend["BJR Bgt."] > 0, (df_trend["BJR Akt."] / df_trend["BJR Bgt."] * 100) - 100, 0)


# --- 7. FUNGSI SUNTIK VERTIKAL DROP LINES KONDISIONAL ---
def tambah_garis_hubung(fig, df, col_akt, col_bgt):
    for idx, row in df.iterrows():
        if row[col_akt] == 0:  # Lewati bulan yang belum memiliki realisasi
            continue
        warna_garis = "#C62828" if row[col_akt] < row[col_bgt] else "#FFD600"
        fig.add_trace(go.Scatter(
            x=[row["Bulan"], row["Bulan"]],
            y=[row[col_bgt], row[col_akt]],
            mode="lines",
            line=dict(color=warna_garis, width=2, dash="dot"),
            showlegend=False,
            hoverinfo="skip"
        ))

# =========================================================================
# 📉 GRAFIK 1: TREND YIELD (TON/HA)
# =========================================================================
st.markdown("---")
st.subheader("TREND YIELD (TON/HA)")
fig_yield = go.Figure()

# Garis Aktual (Biru Tua, Marker Lingkaran Merah)
df_yld_real = df_trend[df_trend["Yield Akt."] > 0]
fig_yield.add_trace(go.Scatter(
    x=df_yld_real["Bulan"], y=df_yld_real["Yield Akt."], mode='lines+markers', name="Aktual",
    line=dict(color='#28348A', width=3, shape='spline'), marker=dict(size=8, color='#C62828', symbol='circle')
))

# Garis Target (Hijau, Marker Kuning Cerah)
fig_yield.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["Yield Bgt."], mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))
))

tambah_garis_hubung(fig_yield, df_trend, "Yield Akt.", "Yield Bgt.")

for idx, row in df_trend.iterrows():
    if row["Yield Akt."] > 0:
        fig_yield.add_annotation(
            x=row["Bulan"], y=max(row["Yield Akt."], row["Yield Bgt."]),
            text=f"{row['Yield_Pct']:+.1f}%", showarrow=False, yshift=15,
            font=dict(color="#28348A", size=10, weight="bold")
        )

fig_yield.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", height=350)
st.plotly_chart(fig_yield, use_container_width=True, key="chart_trend_kbn_yield_line")


# =========================================================================
# 🌱 GRAFIK 2: TREND RJP (JANJANG/POKOK)
# =========================================================================
st.markdown("---")
st.subheader("TREND RJP (JANJANG/POKOK)")
fig_rjp = go.Figure()

df_rjp_real = df_trend[df_trend["RJP Akt."] > 0]
fig_rjp.add_trace(go.Scatter(
    x=df_rjp_real["Bulan"], y=df_rjp_real["RJP Akt."], mode='lines+markers', name="Aktual",
    line=dict(color='#28348A', width=3, shape='spline'), marker=dict(size=8, color='#C62828', symbol='circle')
))

fig_rjp.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["RJP Bgt."], mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))
))

tambah_garis_hubung(fig_rjp, df_trend, "RJP Akt.", "RJP Bgt.")

for idx, row in df_trend.iterrows():
    if row["RJP Akt."] > 0:
        fig_rjp.add_annotation(
            x=row["Bulan"], y=max(row["RJP Akt."], row["RJP Bgt."]),
            text=f"{row['RJP_Pct']:+.1f}%", showarrow=False, yshift=15,
            font=dict(color="#28348A", size=10, weight="bold")
        )

fig_rjp.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", height=350)
st.plotly_chart(fig_rjp, use_container_width=True, key="chart_trend_kbn_rjp_line")


# =========================================================================
# ⚖️ GRAFIK 3: TREND BJR (KG/JJG)
# =========================================================================
st.markdown("---")
st.subheader("TREND BJR (KG/JJG)")
fig_bjr = go.Figure()

df_bjr_real = df_trend[df_trend["BJR Akt."] > 0]
fig_bjr.add_trace(go.Scatter(
    x=df_bjr_real["Bulan"], y=df_bjr_real["BJR Akt."], mode='lines+markers', name="Aktual",
    line=dict(color='#28348A', width=3, shape='spline'), marker=dict(size=8, color='#C62828', symbol='circle')
))

fig_bjr.add_trace(go.Scatter(
    x=df_trend["Bulan"], y=df_trend["BJR Bgt."], mode='lines+markers', name=LABEL_TARGET,
    line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))
))

tambah_garis_hubung(fig_bjr, df_trend, "BJR Akt.", "BJR Bgt.")

for idx, row in df_trend.iterrows():
    if row["BJR Akt."] > 0:
        fig_bjr.add_annotation(
            x=row["Bulan"], y=max(row["BJR Akt."], row["BJR Bgt."]),
            text=f"{row['BJR_Pct']:+.1f}%", showarrow=False, yshift=15,
            font=dict(color="#28348A", size=10, weight="bold")
        )

fig_bjr.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", height=350)
st.plotly_chart(fig_bjr, use_container_width=True, key="chart_trend_kbn_bjr_line")