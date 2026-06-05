import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"].copy()
pilihan_target = st.session_state["pilihan_target"]

st.markdown(f"### 📈 Trend Produksi Bulanan Per Kebun ({pilihan_target})")

# --- 1. DETEKSI KOLOM DINAMIS TARGET ---
if pilihan_target == "Budget":
    col_tgt_kg = "Kg Bgt."
    col_tgt_jjg = "Jjg Bgt."
    col_tgt_bjr = "BJR Bgt."
elif pilihan_target == "Sensus":
    col_tgt_kg = "Kg Sns."
    col_tgt_jjg = "Jjg Sns."
    col_tgt_bjr = "BJR Sns."
else:
    col_tgt_kg = "Kg Pot."
    col_tgt_jjg = "Jjg Pot."
    col_tgt_bjr = "BJR Pot."

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

# --- 3. REKONSILIASI BULAN AGUSTUS (PENTING!) ---
if 'Bulan' in df_raw.columns:
    df_raw['Bulan'] = df_raw['Bulan'].astype(str).str.strip().str.upper()
    df_raw['Bulan'] = df_raw['Bulan'].replace({'AGT': 'AGS', 'AGUSTUS': 'AGS'})

# --- 4. FILTER KEBUN ---
list_kebun = sorted(df_raw['Kebun'].dropna().unique())
kebun_terpilih = st.selectbox("Pilih Kebun untuk melihat grafik tren:", list_kebun, key="sb_trend_kbn")
df_filtered = df_raw[df_raw['Kebun'] == kebun_terpilih].copy()

# --- 5. AGREGASI BULANAN JAN - DES ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
df_filtered['Bulan'] = pd.Categorical(df_filtered['Bulan'], categories=URUTAN_BULAN_STD, ordered=True)

df_group = df_filtered.groupby('Bulan', observed=False).agg({
    'Kg Akt.': 'sum',
    'Jjg Akt.': 'sum',
    col_tgt_kg: 'sum',
    col_tgt_jjg: 'sum'
}).reset_index()

df_luas = df_filtered.groupby(['Bulan', 'Afdeling'], observed=False)['Luas'].first().reset_index().groupby('Bulan', observed=False)['Luas'].sum().reset_index()
df_pokok = df_filtered.groupby(['Bulan', 'Afdeling'], observed=False)['Pokok'].first().reset_index().groupby('Bulan', observed=False)['Pokok'].sum().reset_index()

df_group['Luas'] = df_group['Bulan'].map(df_luas.set_index('Bulan')['Luas'])
df_group['Pokok'] = df_group['Bulan'].map(df_pokok.set_index('Bulan')['Pokok'])

# --- 6. KALKULASI RASIO & PERSENTASE TREN ---
df_group['Yield_Akt'] = df_group['Kg Akt.'] / df_group['Luas'] / 1000
df_group['Yield_Tgt'] = df_group[col_tgt_kg] / df_group['Luas'] / 1000
df_group['Yield_Pct'] = (df_group['Yield_Akt'] / df_group['Yield_Tgt'] * 100).fillna(0)

df_group['RJP_Akt'] = df_group['Jjg Akt.'] / df_group['Pokok']
df_group['RJP_Tgt'] = df_group[col_tgt_jjg] / df_group['Pokok']
df_group['RJP_Pct'] = (df_group['RJP_Akt'] / df_group['RJP_Tgt'] * 100).fillna(0)

df_group['BJR_Akt'] = df_group['Kg Akt.'] / df_group['Jjg Akt.']
df_group['BJR_Tgt'] = df_group[col_tgt_kg] / df_group['Jjg Akt.']
bjr_mean_raw = df_filtered.groupby('Bulan', observed=False)[col_tgt_bjr].mean()
df_group['BJR_Tgt'] = df_group['BJR_Tgt'].replace([np.inf, -np.inf], np.nan).fillna(df_group['Bulan'].map(bjr_mean_raw)).fillna(0)
df_group['BJR_Pct'] = (df_group['BJR_Akt'] / df_group['BJR_Tgt'] * 100).fillna(0)

# ==========================================
# GRAPH 1: TREND YIELD (TON/HA)
# ==========================================
st.markdown("---")
st.subheader("📊 TREND YIELD (TON/HA)")
fig_yld = go.Figure()
fig_yld.add_trace(go.Bar(x=df_group["Bulan"], y=df_group["Yield_Akt"], name="Aktual", marker_color="#28348A", width=0.4))
fig_yld.add_trace(go.Scatter(x=df_group["Bulan"], y=df_group["Yield_Tgt"], mode='lines+markers', name=pilihan_target, line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))))

for idx, row in df_group.iterrows():
    if row["Yield_Akt"] > 0:
        fig_yld.add_annotation(x=row["Bulan"], y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=20, textangle=-90, font=dict(color="white", size=10, family="Arial Black"))
        if row["Yield_Pct"] < 95:
            fig_yld.add_annotation(x=row["Bulan"], y=row["Yield_Tgt"], ax=row["Bulan"], ay=row["Yield_Akt"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.0, arrowwidth=2, arrowcolor='#FF0000')

fig_yld.update_layout(template="plotly_white", yaxis_title="Ton / Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_yld, use_container_width=True, key="chart_trend_kbn_yield")

# ==========================================
# GRAPH 2: TREND RJP (JJG/POKOK)
# ==========================================
st.markdown("---")
st.subheader("📊 TREND RJP (JANJANG/POKOK)")
fig_rjp = go.Figure()
fig_rjp.add_trace(go.Bar(x=df_group["Bulan"], y=df_group["RJP_Akt"], name="Aktual", marker_color="#28348A", width=0.4))
fig_rjp.add_trace(go.Scatter(x=df_group["Bulan"], y=df_group["RJP_Tgt"], mode='lines+markers', name=pilihan_target, line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))))

for idx, row in df_group.iterrows():
    if row["RJP_Akt"] > 0:
        fig_rjp.add_annotation(x=row["Bulan"], y=0, text=f"{row['RJP_Pct']:.1f}%", showarrow=False, yshift=20, textangle=-90, font=dict(color="white", size=10, family="Arial Black"))
        if row["RJP_Pct"] < 95:
            fig_rjp.add_annotation(x=row["Bulan"], y=row["RJP_Tgt"], ax=row["Bulan"], ay=row["RJP_Akt"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.0, arrowwidth=2, arrowcolor='#FF0000')

fig_rjp.update_layout(template="plotly_white", yaxis_title="Janjang / Pokok", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_rjp, use_container_width=True, key="chart_trend_kbn_rjp")

# ==========================================
# GRAPH 3: TREND BJR (KG/JJG)
# ==========================================
st.markdown("---")
st.subheader("⚖️ TREND BJR (KG/JANJANG)")
fig_bjr = go.Figure()
fig_bjr.add_trace(go.Bar(x=df_group["Bulan"], y=df_group["BJR_Akt"], name="Aktual", marker_color="#28348A", width=0.4))
fig_bjr.add_trace(go.Scatter(x=df_group["Bulan"], y=df_group["BJR_Tgt"], mode='lines+markers', name=pilihan_target, line=dict(color='#00B050', width=3, shape='spline'), marker=dict(size=6, color='#FFFF00', line=dict(color='#00B050', width=1))))

for idx, row in df_group.iterrows():
    if row["BJR_Akt"] > 0:
        fig_bjr.add_annotation(x=row["Bulan"], y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=20, textangle=-90, font=dict(color="white", size=10, family="Arial Black"))
        if row["BJR_Pct"] < 95:
            fig_bjr.add_annotation(x=row["Bulan"], y=row["BJR_Tgt"], ax=row["Bulan"], ay=row["BJR_Akt"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.0, arrowwidth=2, arrowcolor='#FF0000')

fig_bjr.update_layout(template="plotly_white", yaxis_title="Berat (Kg)", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
st.plotly_chart(fig_bjr, use_container_width=True, key="chart_trend_kbn_bjr")