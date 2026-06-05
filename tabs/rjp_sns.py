import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🎯 RJP terhadap Sensus (Jjg/Pkk)")

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

for col in ['Pokok', 'Jjg Akt.', 'Jjg Sns.']:
    df_mtd = clean_general_numeric(df_mtd, col)
    df_ytd = clean_general_numeric(df_ytd, col)

df_mtd = df_mtd[df_mtd['Pokok'] > 0].copy()
df_ytd = df_ytd[df_ytd['Pokok'] > 0].copy()

# --- 2. AGREGASI ---
pokok_kebun_mtd = df_mtd.groupby(['Kebun', 'Afdeling'])['Pokok'].first().reset_index().groupby('Kebun')['Pokok'].sum()
pokok_kebun_ytd = df_ytd.groupby(['Kebun', 'Afdeling'])['Pokok'].first().reset_index().groupby('Kebun')['Pokok'].sum()

df_k_mtd = df_mtd.groupby('Kebun').agg({'Jjg Akt.': 'sum', 'Jjg Sns.': 'sum'}).reset_index()
df_k_mtd['Pokok'] = df_k_mtd['Kebun'].map(pokok_kebun_mtd)
df_k_mtd['Aktual'] = df_k_mtd['Jjg Akt.'] / df_k_mtd['Pokok']
df_k_mtd['Target'] = df_k_mtd['Jjg Sns.'] / df_k_mtd['Pokok']
df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

df_k_ytd = df_ytd.groupby('Kebun').agg({'Jjg Akt.': 'sum', 'Jjg Sns.': 'sum'}).reset_index()
df_k_ytd['Pokok'] = df_k_ytd['Kebun'].map(pokok_kebun_ytd)
df_k_ytd['Aktual'] = df_k_ytd['Jjg Akt.'] / df_k_ytd['Pokok']
df_k_ytd['Target'] = df_k_ytd['Jjg Sns.'] / df_k_ytd['Pokok']
df_k_ytd['Pct'] = (df_k_ytd['Aktual'] / df_k_ytd['Target'] * 100).fillna(0)

# --- 3. LAYOUT GRAFIK BERSEBELAHAN ---
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.markdown(f"##### 📊 Janjang/Pokok Per Kebun - {pilihan_bulan}")
    fig_mtd = go.Figure()
    fig_mtd.add_trace(go.Bar(x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_k_mtd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=12, family="Arial Black")))
    fig_mtd.add_trace(go.Scatter(x=df_k_mtd["Kebun"], y=[None]*len(df_k_mtd), mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
    for idx, row in df_k_mtd.iterrows():
        fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < 95 or row["Pct"] > 105:
            fig_mtd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_mtd.update_layout(template="plotly_white", yaxis_title="Janjang / Pokok", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_mtd, use_container_width=True, key="chart_rjp_sns_kebun_mtd")

with col_g2:
    st.markdown(f"##### 📊 Janjang/Pokok Per Kebun - s.d {pilihan_bulan}")
    fig_ytd = go.Figure()
    fig_ytd.add_trace(go.Bar(x=df_k_ytd["Kebun"], y=df_k_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_k_ytd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=12, family="Arial Black")))
    fig_ytd.add_trace(go.Scatter(x=df_k_ytd["Kebun"], y=[None]*len(df_k_ytd), mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
    for idx, row in df_k_ytd.iterrows():
        fig_ytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < 95 or row["Pct"] > 105:
            fig_ytd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_ytd.update_layout(template="plotly_white", yaxis_title="Janjang / Pokok", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_ytd, use_container_width=True, key="chart_rjp_sns_kebun_ytd")

def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_var_fill_koreksi(val):
    if isinstance(val, (int, float)):
        if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
        elif -5 <= val <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'
    return ''

# --- 4. DATA TABLES ---
col_t1, col_t2 = st.columns(2)
with col_t1:
    st.markdown(f"##### 📋 Data Janjang/Pokok Per Kebun - {pilihan_bulan}")
    df_t_mtd = df_k_mtd[['Kebun', 'Aktual', 'Target']].copy()
    df_t_mtd.columns = ['Kebun', 'Aktual', 'Sensus']
    df_t_mtd['Var'] = df_t_mtd['Aktual'] - df_t_mtd['Sensus']
    df_t_mtd['Pct'] = (df_t_mtd['Aktual'] / df_t_mtd['Sensus'] * 100) - 100
    
    # Perbaikan Perhitungan Baris Total (Bebas Error Kamus Python)
    tot_pkk_mtd = pokok_kebun_mtd.sum()
    tot_akt_mtd = df_mtd['Jjg Akt.'].sum() / tot_pkk_mtd if tot_pkk_mtd > 0 else 0
    tot_sns_mtd = df_mtd['Jjg Sns.'].sum() / tot_pkk_mtd if tot_pkk_mtd > 0 else 0
    df_total_mtd = pd.DataFrame([{
        'Kebun': 'TOTAL SITE', 
        'Aktual': tot_akt_mtd, 
        'Sensus': tot_sns_mtd, 
        'Var': tot_akt_mtd - tot_sns_mtd, 
        'Pct': (tot_akt_mtd / tot_sns_mtd * 100) - 100 if tot_sns_mtd > 0 else 0
    }])
    
    df_final_mtd = pd.concat([df_t_mtd, df_total_mtd], ignore_index=True)
    df_final_mtd.insert(0, 'No', range(1, len(df_final_mtd) + 1))
    df_final_mtd.columns = ['No', 'Kebun', 'Aktual (Jjg/Pkk)', 'Sensus (Jjg/Pkk)', 'Gap', 'Var (%)']
    st.dataframe(df_final_mtd.style.format({'Aktual (Jjg/Pkk)': '{:,.2f}', 'Sensus (Jjg/Pkk)': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap']).map(style_var_fill_koreksi, subset=['Var (%)']).set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key="table_rjp_sns_kebun_mtd")

with col_t2:
    st.markdown(f"##### 📋 Data Janjang/Pokok Per Kebun - s.d {pilihan_bulan}")
    df_t_ytd = df_k_ytd[['Kebun', 'Aktual', 'Target']].copy()
    df_t_ytd.columns = ['Kebun', 'Aktual', 'Sensus']
    df_t_ytd['Var'] = df_t_ytd['Aktual'] - df_t_ytd['Sensus']
    df_t_ytd['Pct'] = (df_t_ytd['Aktual'] / df_t_ytd['Sensus'] * 100) - 100
    
    tot_pkk_ytd = pokok_kebun_ytd.sum()
    tot_akt_ytd = df_ytd['Jjg Akt.'].sum() / tot_pkk_ytd if tot_pkk_ytd > 0 else 0
    tot_sns_ytd = df_ytd['Jjg Sns.'].sum() / tot_pkk_ytd if tot_pkk_ytd > 0 else 0
    df_total_ytd = pd.DataFrame([{
        'Kebun': 'TOTAL SITE', 
        'Aktual': tot_akt_ytd, 
        'Sensus': tot_sns_ytd, 
        'Var': tot_akt_ytd - tot_sns_ytd, 
        'Pct': (tot_akt_ytd / tot_sns_ytd * 100) - 100 if tot_sns_ytd > 0 else 0
    }])
    
    df_final_ytd = pd.concat([df_t_ytd, df_total_ytd], ignore_index=True)
    df_final_ytd.insert(0, 'No', range(1, len(df_final_ytd) + 1))
    df_final_ytd.columns = ['No', 'Kebun', 'Aktual (Jjg/Pkk)', 'Sensus (Jjg/Pkk)', 'Gap', 'Var (%)']
    st.dataframe(df_final_ytd.style.format({'Aktual (Jjg/Pkk)': '{:,.2f}', 'Sensus (Jjg/Pkk)': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap']).map(style_var_fill_koreksi, subset=['Var (%)']).set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key="table_rjp_sns_kebun_ytd")

# --- AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
list_kebun = sorted(df_raw['Kebun'].dropna().unique())
kebun_terpilih = st.selectbox("Pilih Kebun untuk melihat detail Afdeling:", list_kebun, key="sb_rjp_sns_afd")
df_m_afd = df_mtd[df_mtd['Kebun'] == kebun_terpilih].copy()
df_y_afd = df_ytd[df_ytd['Kebun'] == kebun_terpilih].copy()

if not df_m_afd.empty:
    df_a_mtd = df_m_afd.groupby('Afdeling').agg({'Jjg Akt.': 'sum', 'Jjg Sns.': 'sum'}).reset_index()
    df_a_mtd['Pokok'] = df_a_mtd['Afdeling'].map(df_m_afd.groupby('Afdeling')['Pokok'].first())
    df_a_mtd['Aktual'] = df_a_mtd['Jjg Akt.'] / df_a_mtd['Pokok']
    df_a_mtd['Target'] = df_a_mtd['Jjg Sns.'] / df_a_mtd['Pokok']
    df_a_mtd['Pct'] = (df_a_mtd['Aktual'] / df_a_mtd['Target'] * 100).fillna(0)

    df_a_ytd = df_y_afd.groupby('Afdeling').agg({'Jjg Akt.': 'sum', 'Jjg Sns.': 'sum'}).reset_index()
    df_a_ytd['Pokok'] = df_a_ytd['Afdeling'].map(df_y_afd.groupby('Afdeling')['Pokok'].first())
    df_a_ytd['Aktual'] = df_a_ytd['Jjg Akt.'] / df_a_ytd['Pokok']
    df_a_ytd['Target'] = df_a_ytd['Jjg Sns.'] / df_a_ytd['Pokok']
    df_a_ytd['Pct'] = (df_a_ytd['Aktual'] / df_a_ytd['Target'] * 100).fillna(0)

    col_ga1, col_ga2 = st.columns(2)
    with col_ga1:
        st.markdown(f"##### 📊 Janjang/Pokok Per Afdeling ({kebun_terpilih}) - {pilihan_bulan}")
        fig_amtd = go.Figure()
        fig_amtd.add_trace(go.Bar(x=df_a_mtd["Afdeling"], y=df_a_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_a_mtd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=11, family="Arial Black")))
        fig_amtd.add_trace(go.Scatter(x=df_a_mtd["Afdeling"], y=[None]*len(df_a_mtd), mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
        for idx, row in df_a_mtd.iterrows():
            fig_amtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
            if row["Pct"] < 95 or row["Pct"] > 105:
                fig_amtd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
        fig_amtd.update_layout(template="plotly_white", yaxis_title="Janjang / Pokok", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_amtd, use_container_width=True, key="chart_rjp_sns_afd_mtd")

    with col_ga2:
        st.markdown(f"##### 📊 Janjang/Pokok Per Afdeling ({kebun_terpilih}) - s.d {pilihan_bulan}")
        fig_aytd = go.Figure()
        fig_aytd.add_trace(go.Bar(x=df_a_ytd["Afdeling"], y=df_a_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_a_ytd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=11, family="Arial Black")))
        fig_aytd.add_trace(go.Scatter(x=df_a_ytd["Afdeling"], y=[None]*len(df_a_ytd), mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
        for idx, row in df_a_ytd.iterrows():
            fig_aytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
            if row["Pct"] < 95 or row["Pct"] > 105:
                fig_aytd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
        fig_aytd.update_layout(template="plotly_white", yaxis_title="Janjang / Pokok", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_aytd, use_container_width=True, key="chart_rjp_sns_afd_ytd")

    col_ta1, col_ta2 = st.columns(2)
    with col_ta1:
        df_ta_mtd = df_a_mtd[['Afdeling', 'Aktual', 'Target']].copy()
        df_ta_mtd.columns = ['Afdeling', 'Aktual', 'Sensus']
        df_ta_mtd['Var'] = df_ta_mtd['Aktual'] - df_ta_mtd['Sensus']
        df_ta_mtd['Pct'] = (df_ta_mtd['Aktual'] / df_ta_mtd['Sensus'] * 100) - 100
        df_ta_mtd.insert(0, 'No', range(1, len(df_ta_mtd) + 1))
        df_ta_mtd.columns = ['No', 'Afdeling', 'Aktual (Jjg/Pkk)', 'Sensus (Jjg/Pkk)', 'Gap', 'Var (%)']
        st.dataframe(df_ta_mtd.style.format({'Aktual (Jjg/Pkk)': '{:,.2f}', 'Sensus (Jjg/Pkk)': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap']).map(style_var_fill_koreksi, subset=['Var (%)']), use_container_width=True, hide_index=True, key="table_rjp_sns_afd_mtd")
    
    with col_ta2:
        df_ta_ytd = df_a_ytd[['Afdeling', 'Aktual', 'Target']].copy()
        df_ta_ytd.columns = ['Afdeling', 'Aktual', 'Sensus']
        df_ta_ytd['Var'] = df_ta_ytd['Aktual'] - df_ta_ytd['Sensus']
        df_ta_ytd['Pct'] = (df_ta_ytd['Aktual'] / df_ta_ytd['Sensus'] * 100) - 100
        df_ta_ytd.insert(0, 'No', range(1, len(df_ta_ytd) + 1))
        df_ta_ytd.columns = ['No', 'Afdeling', 'Aktual (Jjg/Pkk)', 'Sensus (Jjg/Pkk)', 'Gap', 'Var (%)']
        st.dataframe(df_ta_ytd.style.format({'Aktual (Jjg/Pkk)': '{:,.2f}', 'Sensus (Jjg/Pkk)': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap']).map(style_var_fill_koreksi, subset=['Var (%)']), use_container_width=True, hide_index=True, key="table_rjp_sns_afd_ytd")