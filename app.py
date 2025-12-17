import math
import re
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st
import altair as alt

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Prediksi Kebutuhan Pisang",
    page_icon="🍌",
    layout="wide",
)

# =========================================================
# BANANA THEME CSS (FINAL)
# =========================================================
st.markdown(
"""
<style>
:root{
  --bg:#FBF7EF;
  --card:#FFFFFF;
  --border:#F1E7D6;
  --text:#2A241C;
  --muted:#7A736A;
  --yellow:#F6D25E;
  --yellow-soft:#FFF4CC;
  --yellow-border:#F0E0A8;
}

.stApp{background:var(--bg);}
.block-container{padding-top:1.4rem;padding-bottom:2.2rem;}

h1,h2,h3{letter-spacing:-0.02em;color:var(--text);}
.small-muted{color:var(--muted);font-size:.95rem;}

.card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:20px;
  padding:18px;
  box-shadow:0 4px 18px rgba(30,30,30,.04);
}
.card-title{color:var(--muted);font-size:.95rem;}
.card-value{font-size:1.9rem;font-weight:800;color:var(--text);}
.card-sub{color:var(--muted);font-size:.92rem;margin-top:6px;}
.card-big .card-value{font-size:2.3rem;}

.filter-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:20px;
  padding:16px;
  box-shadow:0 4px 18px rgba(30,30,30,.04);
}
.filter-title{font-weight:800;color:var(--text);}
.filter-sub{color:var(--muted);font-size:.92rem;}

.banner{
  background:var(--yellow-soft);
  border:1px solid var(--yellow-border);
  border-radius:18px;
  padding:14px 16px;
  color:#5a4a20;
}

.stButton button,.stDownloadButton button{
  background:var(--yellow)!important;
  border:1px solid #E9C84D!important;
  color:var(--text)!important;
  font-weight:700!important;
  border-radius:14px!important;
}

section[data-testid="stSidebar"]{
  background:#FFFDF7;
  border-right:1px solid var(--border);
}

[data-testid="stDataFrame"]{
  border-radius:16px;
  border:1px solid var(--border);
}

footer{visibility:hidden;}
</style>
""",
unsafe_allow_html=True
)

# =========================================================
# MONTH HELPERS
# =========================================================
ID_MONTH_NAMES = {
    1:"Januari",2:"Februari",3:"Maret",4:"April",
    5:"Mei",6:"Juni",7:"Juli",8:"Agustus",
    9:"September",10:"Oktober",11:"November",12:"Desember"
}
def month_name_id(m): return ID_MONTH_NAMES.get(int(m), str(m))

# =========================================================
# UI CARD
# =========================================================
def card(title,value,sub="",big=False):
    cls="card card-big" if big else "card"
    st.markdown(f"""
    <div class="{cls}">
      <div class="card-title">{title}</div>
      <div class="card-value">{value}</div>
      <div class="card-sub">{sub}</div>
    </div>
    """,unsafe_allow_html=True)

# =========================================================
# EXCEL PARSER (SARIMA RESULT)
# =========================================================
def parse_excel(path):
    df=pd.read_excel(path)
    df.columns=[c.lower() for c in df.columns]
    df["tanggal"]=pd.to_datetime(df.iloc[:,0])
    df=df.rename(columns={
        df.columns[1]:"nilai",
        df.columns[2] if len(df.columns)>2 else "": "min",
        df.columns[3] if len(df.columns)>3 else "": "max"
    })
    return df

@st.cache_data
def load_data():
    return parse_excel(Path(__file__).parent/"hasil_prediksi_sarima.xlsx")

df_all=load_data()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## 🍌 Dashboard Pisang")
    page=st.radio("Menu",["Dashboard","Detail Prediksi"],index=0)

# =========================================================
# HEADER
# =========================================================
st.markdown("## Berapa Pisang yang Perlu Disiapkan?")
st.markdown(
    "<div class='small-muted'>Dashboard ini membantu UMKM menentukan jumlah bahan baku berdasarkan hasil prediksi.</div>",
    unsafe_allow_html=True
)
st.write("")

# =========================================================
# FILTER + SUBMIT
# =========================================================
years=sorted(df_all["tanggal"].dt.year.unique())
if "f_year" not in st.session_state: st.session_state.f_year=years[0]
if "f_month" not in st.session_state: st.session_state.f_month="Semua Bulan"

st.markdown("<div class='filter-card'>",unsafe_allow_html=True)
with st.form("filter"):
    a,b,c,d=st.columns([2,1,1,1])
    with a:
        st.markdown("<div class='filter-title'>Pilih Periode</div>",unsafe_allow_html=True)
        st.markdown("<div class='filter-sub'>Tentukan tahun dan bulan.</div>",unsafe_allow_html=True)
    with b:
        year=st.selectbox("Tahun",years,index=years.index(st.session_state.f_year))
    with c:
        months=["Semua Bulan"]+[month_name_id(m) for m in range(1,13)]
        month=st.selectbox("Bulan",months,index=months.index(st.session_state.f_month))
    with d:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        submit=st.form_submit_button("Tampilkan")
st.markdown("</div>",unsafe_allow_html=True)

if submit:
    st.session_state.f_year=year
    st.session_state.f_month=month

year=st.session_state.f_year
month=st.session_state.f_month

df_year=df_all[df_all["tanggal"].dt.year==year]

# =========================================================
# DASHBOARD PAGE
# =========================================================
if page=="Dashboard":
    st.write("")
    if month=="Semua Bulan":
        card(
            "Perkiraan pisang yang perlu disiapkan",
            "Pilih bulan",
            "Contoh: Juli 2026",
            big=True
        )
    else:
        m=[k for k,v in ID_MONTH_NAMES.items() if v==month][0]
        val=df_year[df_year["tanggal"].dt.month==m]["nilai"].mean()
        card(
            "Perkiraan pisang yang perlu disiapkan",
            f"± {val:,.0f} kg",
            f"Bulan {month} {year}",
            big=True
        )

    st.write("")
    st.markdown("### Perkiraan kebutuhan pisang per bulan")
    chart=alt.Chart(df_year).mark_line(strokeWidth=3).encode(
        x="tanggal:T",
        y="nilai:Q",
        tooltip=["tanggal:T","nilai:Q"]
    )
    st.altair_chart(chart,use_container_width=True)

# =========================================================
# DETAIL PAGE
# =========================================================
else:
    st.markdown("### Detail Prediksi")
    st.markdown("<div class='small-muted'>Rincian angka per bulan untuk perencanaan stok.</div>",unsafe_allow_html=True)
    st.write("")

    tbl=df_year.copy()
    tbl["Bulan"]=tbl["tanggal"].dt.month.apply(month_name_id)
    tbl=tbl[["Bulan","nilai"]].rename(columns={"nilai":"Prediksi (kg)"})
    st.dataframe(tbl,use_container_width=True,hide_index=True)

    total=df_year["nilai"].sum()
    avg=df_year["nilai"].mean()
    peak=df_year.loc[df_year["nilai"].idxmax()]

    st.write("")
    c1,c2,c3=st.columns(3)
    with c1: card("Total 1 Tahun",f"{total:,.0f} kg",f"Tahun {year}")
    with c2: card("Rata-rata / Bulan",f"{avg:,.0f} kg","Patokan belanja")
    with c3: card("Bulan Tersibuk",month_name_id(peak["tanggal"].month),f"± {peak['nilai']:,.0f} kg")
