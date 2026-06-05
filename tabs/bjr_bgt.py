import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### ⚖️ BJR terhadap Budget (Kg/Jjg)")

# --- 1. PROSES FILTER TIMEFRAME ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

if pilihan_bulan == 'CAWU I':
    bulan_mtd_list = ['JAN', 'FEB', 'MAR', 'APR']
    bulan_ytd_list = ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II':
    bulan_mtd_list = ['MEI', 'JUN', 'JUL', 'AGS']
    bulan_ytd_list = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III':
    bulan_mtd_list = ['SEP', 'OKT', 'NOV', 'DES']
    bulan_ytd_list = URUTAN_BULAN_STD.copy()
elif pilihan_bulan == 'SEMESTER I':
    bulan_mtd_list = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN']
    bulan_ytd_list = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN']
elif pilihan_bulan == 'SEMESTER II':
    bulan_mtd_list = ['JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
    bulan_ytd_list = URUTAN_BULAN_STD.copy()
else:
    pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan
    bulan_mtd_list = [pilihan_bulan_std]
    if pilihan_bulan_std in URUTAN_BULAN_STD:
        idx_bulan = URUTAN_BULAN_STD.index(pilihan_bulan_std)
        bulan_ytd_list = URUTAN_BULAN_STD[:idx_bulan + 1]
    else:
        bulan_ytd_list = [pilihan_bulan_std]

df_mtd = df_raw[df_raw['Bulan'].isin(bulan_mtd_list)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd_list)].copy()

def clean_general_numeric(df, col_name):
    if col_name in df.columns:
        df[col_name] = df[col_name].astype(str).str.strip()
        df[col_name] = df[col_name].replace({'-': '0', '': '0'}, regex=False)
        df[col_name] = df[col_name].str.replace(',', '.', regex=False)
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
    return df

for col in ['Kg Akt.', 'Jjg Akt.', 'BJR Bgt.']:
    df_mtd = clean_general_numeric(df_mtd, col)
    df_ytd = clean_general_numeric(df_ytd, col)

# --- 2. AGREGASI LEVEL KEBUN ---
df_k_mtd = df_mtd.groupby('Kebun').apply(
    lambda x: pd.Series({
        'Kg Akt.': x['Kg Akt.'].sum(),
        'Jjg Akt.': x['Jjg Akt.'].sum(),
        'Target': (x['BJR Bgt.'] * x['Jjg Akt.']).sum() / x['Jjg Akt.'].sum() if x['Jjg Akt.'].sum() > 0 else 0
    })
).reset_index()
df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Jjg Akt.']
df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

df_k_ytd = df_ytd.groupby('Kebun').apply(
    lambda x: pd.Series({
        'Kg Akt.': x['Kg Akt.'].sum(),
        'Jjg Akt.': x['Jjg Akt.'].sum(),
        'Target': (x['BJR Bgt.'] * x['Jjg Akt.']).sum() / x['Jjg Akt.'].sum() if x['Jjg Akt.'].sum() > 0 else 0
    })
).reset_index()
df_k_ytd['Aktual'] = df_k_ytd['Kg Akt.'] / df_k_ytd['Jjg Akt.']
df_k_ytd['Pct'] = (df_k_ytd['Aktual'] / df_k_ytd['Target'] * 100).fillna(0)

# --- 3. LAYOUT GRAFIK BERSEBELAHAN ---
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.markdown(f"##### 📊 BJR Per Kebun - {pilihan_bulan}")
    fig_mtd = go.Figure()
    fig_mtd.add_trace(go.Bar(x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_k_mtd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=12, family="Arial Black")))
    fig_mtd.add_trace(go.Scatter(x=df_k_mtd["Kebun"], y=[None]*len(df_k_mtd), mode='lines', line=dict(color='#00B050', width=4), name='Budget'))
    for idx, row in df_k_mtd.iterrows():
        fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < 95:
            fig_mtd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_mtd.update_layout(template="plotly_white", yaxis_title="BJR (Kg)", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_mtd, use_container_width=True, key="chart_bjr_bgt_kebun_mtd")

with col_g2:
    st.markdown(f"##### 📊 BJR Per Kebun - s.d {pilihan_bulan}")
    fig_ytd = go.Figure()
    fig_ytd.add_trace(go.Bar(x=df_k_ytd["Kebun"], y=df_k_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_k_ytd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=12, family="Arial Black")))
    fig_ytd.add_trace(go.Scatter(x=df_k_ytd["Kebun"], y=[None]*len(df_k_ytd), mode='lines', line=dict(color='#00B050', width=4), name='Budget'))
    for idx, row in df_k_ytd.iterrows():
        fig_ytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < 95:
            fig_ytd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_ytd.update_layout(template="plotly_white", yaxis_title="BJR (Kg)", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_ytd, use_container_width=True, key="chart_bjr_bgt_kebun_ytd")

def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_bjr_var_fill(val):
    if isinstance(val, (int, float)):
        if val >= -5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        elif -15 <= val < -5: return 'background-color: #FFF2CC; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'
    return ''

# --- 4. DATA TABLES ---
col_t1, col_t2 = st.columns(2)
with col_t1:
    st.markdown(f"##### 📋 Data BJR Per Kebun - {pilihan_bulan}")
    df_t_mtd = df_k_mtd[['Kebun', 'Aktual', 'Target']].copy()
    df_t_mtd.columns = ['Kebun', 'Aktual', 'Budget']
    df_t_mtd['Var'] = df_t_mtd['Aktual'] - df_t_mtd['Budget']
    df_t_mtd['Pct'] = (df_t_mtd['Aktual'] / df_t_mtd['Budget'] * 100) - 100
    
    tot_kg_mtd = df_mtd['Kg Akt.'].sum()
    tot_jjg_mtd = df_mtd['Jjg Akt.'].sum()
    site_akt_mtd = tot_kg_mtd / tot_jjg_mtd if tot_jjg_mtd > 0 else 0
    site_bgt_mtd = (df_mtd['BJR Bgt.'] * df_mtd['Jjg Akt.']).sum() / tot_jjg_mtd if tot_jjg_mtd > 0 else 0
    df_total_mtd = pd.DataFrame([{'Kebun': 'TOTAL SITE', 'Aktual': site_akt_mtd, 'Budget': site_bgt_mtd, 'Var': site_akt_mtd - site_bgt_mtd, 'Pct': (site_akt_mtd / site_bgt_mtd * 100) - 100 if site_bgt_mtd > 0 else 0}])
    
    df_final_mtd = pd.concat([df_t_mtd, df_total_mtd], ignore_index=True)
    df_final_mtd.insert(0, 'No', range(1, len(df_final_mtd) + 1))
    df_final_mtd.columns = ['No', 'Kebun', 'Aktual (Kg)', 'Budget (Kg)', 'Gap (Kg)', 'Var (%)']
    st.dataframe(df_final_mtd.style.format({'Aktual (Kg)': '{:,.2f}', 'Budget (Kg)': '{:,.2f}', 'Gap (Kg)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap (Kg)']).map(style_bjr_var_fill, subset=['Var (%)']).set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key="table_bjr_bgt_kebun_mtd")

with col_t2:
    st.markdown(f"##### 📋 Data BJR Per Kebun - s.d {pilihan_bulan}")
    df_t_ytd = df_k_ytd[['Kebun', 'Aktual', 'Target']].copy()
    df_t_ytd.columns = ['Kebun', 'Aktual', 'Budget']
    df_t_ytd['Var'] = df_t_ytd['Aktual'] - df_t_ytd['Budget']
    df_t_ytd['Pct'] = (df_t_ytd['Aktual'] / df_t_ytd['Budget'] * 100) - 100
    
    tot_kg_ytd = df_ytd['Kg Akt.'].sum()
    tot_jjg_ytd = df_ytd['Jjg Akt.'].sum()
    site_akt_ytd = tot_kg_ytd / tot_jjg_ytd if tot_jjg_ytd > 0 else 0
    site_bgt_ytd = (df_ytd['BJR Bgt.'] * df_ytd['Jjg Akt.']).sum() / tot_jjg_ytd if tot_jjg_ytd > 0 else 0
    df_total_ytd = pd.DataFrame([{'Kebun': 'TOTAL SITE', 'Aktual': site_akt_ytd, 'Budget': site_bgt_ytd, 'Var': site_akt_ytd - site_bgt_ytd, 'Pct': (site_akt_ytd / site_bgt_ytd * 100) - 100 if site_bgt_ytd > 0 else 0}])
    
    df_final_ytd = pd.concat([df_t_ytd, df_total_ytd], ignore_index=True)
    df_final_ytd.insert(0, 'No', range(1, len(df_final_ytd) + 1))
    df_final_ytd.columns = ['No', 'Kebun', 'Aktual (Kg)', 'Budget (Kg)', 'Gap (Kg)', 'Var (%)']
    st.dataframe(df_final_ytd.style.format({'Aktual (Kg)': '{:,.2f}', 'Budget (Kg)': '{:,.2f}', 'Gap (Kg)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap (Kg)']).map(style_bjr_var_fill, subset=['Var (%)']).set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key="table_bjr_bgt_kebun_ytd")

# --- 5. DETAIL PER AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
list_kebun = sorted(df_raw['Kebun'].dropna().unique())
kebun_terpilih = st.selectbox("Pilih Kebun untuk melihat detail Afdeling:", list_kebun, key="sb_bjr_bgt_afd")
df_m_afd = df_mtd[df_mtd['Kebun'] == kebun_terpilih].copy()
df_y_afd = df_ytd[df_ytd['Kebun'] == kebun_terpilih].copy()

if not df_m_afd.empty:
    df_a_mtd = df_m_afd.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Jjg Akt.': 'sum', 'BJR Bgt.': 'mean'}).reset_index()
    df_a_mtd['Aktual'] = df_a_mtd['Kg Akt.'] / df_a_mtd['Jjg Akt.']
    df_a_mtd.rename(columns={'BJR Bgt.': 'Target'}, inplace=True)
    df_a_mtd['Pct'] = (df_a_mtd['Aktual'] / df_a_mtd['Target'] * 100).fillna(0)

    df_a_ytd = df_y_afd.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Jjg Akt.': 'sum', 'BJR Bgt.': 'mean'}).reset_index()
    df_a_ytd['Aktual'] = df_a_ytd['Kg Akt.'] / df_a_ytd['Jjg Akt.']
    df_a_ytd.rename(columns={'BJR Bgt.': 'Target'}, inplace=True)
    df_a_ytd['Pct'] = (df_a_ytd['Aktual'] / df_a_ytd['Target'] * 100).fillna(0)

    col_ga1, col_ga2 = st.columns(2)
    with col_ga1:
        st.markdown(f"##### 📊 BJR Per Afdeling ({kebun_terpilih}) - {pilihan_bulan}")
        fig_amtd = go.Figure()
        fig_amtd.add_trace(go.Bar(x=df_a_mtd["Afdeling"], y=df_a_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_a_mtd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=11, family="Arial Black")))
        fig_amtd.add_trace(go.Scatter(x=df_a_mtd["Afdeling"], y=[None]*len(df_a_mtd), mode='lines', line=dict(color='#00B050', width=4), name='Budget'))
        for idx, row in df_a_mtd.iterrows():
            fig_amtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
            if row["Pct"] < 95:
                fig_amtd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
        fig_amtd.update_layout(template="plotly_white", yaxis_title="BJR (Kg)", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_amtd, use_container_width=True, key="chart_bjr_bgt_afd_mtd")

    with col_ga2:
        st.markdown(f"##### 📊 BJR Per Afdeling ({kebun_terpilih}) - s.d {pilihan_bulan}")
        fig_aytd = go.Figure()
        fig_aytd.add_trace(go.Bar(x=df_a_ytd["Afdeling"], y=df_a_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_a_ytd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=11, family="Arial Black")))
        fig_aytd.add_trace(go.Scatter(x=df_a_ytd["Afdeling"], y=[None]*len(df_a_ytd), mode='lines', line=dict(color='#00B050', width=4), name='Budget'))
        for idx, row in df_a_ytd.iterrows():
            fig_aytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
            if row["Pct"] < 95:
                fig_aytd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
        fig_aytd.update_layout(template="plotly_white", yaxis_title="BJR (Kg)", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_aytd, use_container_width=True, key="chart_bjr_bgt_afd_ytd")

    col_ta1, col_ta2 = st.columns(2)
    with col_ta1:
        df_ta_mtd = df_a_mtd[['Afdeling', 'Aktual', 'Target']].copy()
        df_ta_mtd.columns = ['Afdeling', 'Aktual', 'Budget']
        df_ta_mtd['Gap'] = df_ta_mtd['Aktual'] - df_ta_mtd['Budget']
        df_ta_mtd['Var (%)'] = (df_ta_mtd['Aktual'] / df_ta_mtd['Budget'] * 100) - 100
        df_ta_mtd.insert(0, 'No', range(1, len(df_ta_mtd) + 1))
        st.dataframe(df_ta_mtd.style.format({'Aktual': '{:,.2f}', 'Budget': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap']).map(style_bjr_var_fill, subset=['Var (%)']), use_container_width=True, hide_index=True, key="table_bjr_bgt_afd_mtd")

    with col_ta2:
        df_ta_ytd = df_a_ytd[['Afdeling', 'Aktual', 'Target']].copy()
        df_ta_ytd.columns = ['Afdeling', 'Aktual', 'Budget']
        df_ta_ytd['Gap'] = df_ta_ytd['Aktual'] - df_ta_ytd['Budget']
        df_ta_ytd['Var (%)'] = (df_ta_ytd['Aktual'] / df_ta_ytd['Budget'] * 100) - 100
        df_ta_ytd.insert(0, 'No', range(1, len(df_ta_ytd) + 1))
        st.dataframe(df_ta_ytd.style.format({'Aktual': '{:,.2f}', 'Budget': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap']).map(style_bjr_var_fill, subset=['Var (%)']), use_container_width=True, hide_index=True, key="table_bjr_bgt_afd_ytd")