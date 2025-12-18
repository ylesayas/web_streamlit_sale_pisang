import math
import re
import base64
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
    initial_sidebar_state="expanded",
)

# =========================================================
# LOGO (GAMBAR DARI REPO)
# taruh file di: assets/logo.png
# =========================================================
ASSET_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSET_DIR / "logo.png"

def img_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")

logo_html = "🍌"
if LOGO_PATH.exists():
    logo_b64 = img_to_base64(LOGO_PATH)
    logo_html = f"<img src='data:image/png;base64,{logo_b64}'/>"

# =========================================================
# FULL CSS FINAL (BANANA + FIGMA + UPGRADE SELECTBOX + MENU)
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

.stApp { background: var(--bg); }
.block-container { padding-top: 1.4rem; padding-bottom: 2.2rem; max-width: 1200px; }

h1, h2, h3 { letter-spacing:-0.02em; color: var(--text); }
.small-muted { color: var(--muted); font-size: 0.95rem; }

/* Header */
.header-wrap{
  display:flex; align-items:center; gap:14px;
  background: var(--card);
  border:1px solid var(--border);
  border-radius:22px;
  padding:16px 18px;
  box-shadow: 0 4px 18px rgba(30,30,30,.04);
}
.logo-circle{
  width:48px; height:48px; border-radius:999px;
  display:flex; align-items:center; justify-content:center;
  background: var(--yellow-soft);
  border:1px solid var(--yellow-border);
  font-size:26px;
}
.logo-circle img{
  width: 28px;
  height: 28px;
  object-fit: contain;
}
.header-title{ font-size:1.45rem; font-weight:800; color:var(--text); line-height:1.15; }
.header-sub{ color:var(--muted); font-size:0.95rem; margin-top:4px; }

/* Cards */
.card{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px 18px;
  box-shadow: 0 4px 18px rgba(30,30,30,0.04);
}
.card-title{ color: var(--muted); font-size: 0.95rem; margin-bottom: 6px; }
.card-value{ font-size: 1.9rem; font-weight: 800; color: var(--text); line-height: 1.1; }
.card-sub{ color: var(--muted); font-size: 0.92rem; margin-top: 6px; }
.card-big .card-value{ font-size: 2.3rem; }

/* Filter card */
.filter-card{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 4px 18px rgba(30,30,30,0.04);
}
.filter-title{ font-weight: 800; color: var(--text); font-size: 1.05rem; }
.filter-sub{ color: var(--muted); font-size: 0.92rem; margin-top: 4px; }

/* Banner / info */
.banner, .info-banner{
  display:flex; gap:12px; align-items:flex-start;
  background: var(--yellow-soft);
  border:1px solid var(--yellow-border);
  border-radius:18px;
  padding:14px 16px;
  color:#5a4a20;
}
.info-icon{
  width:34px; height:34px; border-radius:999px;
  background:#ffffff;
  border:1px solid var(--yellow-border);
  display:flex; align-items:center; justify-content:center;
  font-weight:900;
}

/* Mode pill */
.mode-pill{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 10px; border-radius:999px;
  background: var(--yellow-soft);
  border:1px solid var(--yellow-border);
  color:#5a4a20; font-size:.85rem; font-weight:750;
}

/* Buttons */
.stButton button, .stDownloadButton button{
  background: var(--yellow) !important;
  border: 1px solid #E9C84D !important;
  color: var(--text) !important;
  font-weight: 800 !important;
  border-radius: 14px !important;
  padding: 0.62rem 1rem !important;
}
.stButton button:hover, .stDownloadButton button:hover{ filter: brightness(0.97); }

/* Sidebar */
section[data-testid="stSidebar"]{
  background:#FFFDF7;
  border-right:1px solid var(--border);
}
section[data-testid="stSidebar"] .stButton button{
  background:#ffffff !important;
  border:1px solid var(--border) !important;
  color: var(--text) !important;
  font-weight: 750 !important;
  border-radius: 16px !important;
  padding: 0.65rem 0.9rem !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton button:hover{
  background: var(--yellow-soft) !important;
  border-color: var(--yellow-border) !important;
}
section[data-testid="stSidebar"] hr{
  border: none;
  height: 1px;
  background: var(--border);
  margin: 14px 0;
}

/* Inputs */
label { color: var(--muted) !important; font-weight: 650 !important; }
input, textarea, select { border-radius:14px !important; }

/* Selectbox (BaseWeb) */
div[data-baseweb="select"] > div{
  border-radius: 14px !important;
  border: 1px solid var(--border) !important;
  background: #fff !important;
  box-shadow: none !important;
}
div[data-baseweb="select"] > div:hover{
  border-color: var(--yellow-border) !important;
}
div[data-baseweb="select"] > div:focus-within{
  border-color: var(--yellow) !important;
  box-shadow: 0 0 0 3px rgba(246, 210, 94, 0.25) !important;
}
div[role="listbox"]{
  border-radius: 14px !important;
  border: 1px solid var(--border) !important;
  overflow: hidden !important;
}
div[role="option"]:hover{
  background: var(--yellow-soft) !important;
}

/* Dataframe */
[data-testid="stDataFrame"]{
  border-radius:16px;
  overflow:hidden;
  border:1px solid var(--border);
}

/* Chart */
.vega-embed{ border-radius:18px; }

/* Hide footer */
footer{ visibility:hidden; }
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# MONTH HELPERS (ID)
# =========================================================
ID_MONTHS = {
    "januari": 1, "jan": 1, "jan.": 1,
    "februari": 2, "feb": 2,
    "maret": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "aug": 8,
    "september": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "desember": 12, "des": 12, "dec": 12,
}
ID_MONTH_NAMES = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}
def month_name_id(m: int) -> str:
    return ID_MONTH_NAMES.get(int(m), str(m))

def fmt_int(v: float) -> str:
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return "—"

# =========================================================
# UNIT (Kg <-> Sisir) - patokan UMKM: 450 sisir = 250 kg
# =========================================================
SISIR_PER_KG = 450 / 250  # 1.8
KG_PER_SISIR = 1 / SISIR_PER_KG

def unit_suffix(unit_choice: str) -> str:
    return "sisir" if unit_choice == "Sisir" else "kg"

def convert_value_kg_to_unit(v_kg: float, unit_choice: str) -> float:
    if v_kg is None or (isinstance(v_kg, float) and not math.isfinite(v_kg)):
        return math.nan
    if unit_choice == "Sisir":
        return float(v_kg) * SISIR_PER_KG
    return float(v_kg)

def fmt_dual_units(v_kg: float) -> tuple[str, str]:
    v_sisir = convert_value_kg_to_unit(v_kg, "Sisir")
    return f"{fmt_int(v_kg)} kg", f"{fmt_int(v_sisir)} sisir"

# =========================================================
# UI HELPERS
# =========================================================
def card(title: str, value: str, sub: str = "", big: bool = False):
    extra = "card-big" if big else ""
    st.markdown(
        f"""
        <div class="card {extra}">
          <div class="card-title">{title}</div>
          <div class="card-value">{value}</div>
          <div class="card-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def empty_state(title="Data belum tersedia", desc="Coba pilih tahun/bulan lain atau ganti data prediksi (Admin)."):
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">{title}</div>
          <div class="small-muted">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def to_excel_bytes(df: pd.DataFrame, sheet_name="Data"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# =========================================================
# UNIVERSAL EXCEL PARSER
# =========================================================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        re.sub(r"\s+", "_", str(c).strip()).lower()
        for c in df.columns
    ]
    return df

def detect_date_column(df: pd.DataFrame):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if df[col].notna().sum() >= max(3, len(df) * 0.5):
                return col, df[col]

    date_keywords = ["tanggal", "tgl", "date", "waktu", "period", "periode", "bulan_tahun", "bulan-tahun", "bulan_thn"]
    for col in df.columns:
        if any(k in col for k in date_keywords):
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            if parsed.notna().sum() >= max(3, len(df) * 0.5):
                return col, parsed
    return None, None

def detect_year_month(df: pd.DataFrame):
    year_col, month_col = None, None
    for col in df.columns:
        if any(k in col for k in ["tahun", "year", "thn", "th"]):
            year_col = col
        if any(k in col for k in ["bulan", "month", "bln", "mon"]):
            month_col = col
    return year_col, month_col

def parse_year_month_to_date(df: pd.DataFrame, year_col: str, month_col: str) -> pd.Series:
    y = pd.to_numeric(df[year_col], errors="coerce")
    if (y < 100).sum() > 0 and (y < 100).sum() >= len(y) * 0.5:
        y = y.apply(lambda v: 2000 + v if pd.notna(v) else v)

    months_raw = df[month_col]
    m = pd.to_numeric(months_raw, errors="coerce")
    mask = m.isna() & months_raw.notna()
    if mask.any():
        def map_month(x):
            if pd.isna(x): return math.nan
            s = str(x).strip().lower()
            s2 = re.sub(r"[^\w]+$", "", s)
            return ID_MONTHS.get(s2, math.nan)
        m[mask] = months_raw[mask].map(map_month)

    return pd.to_datetime({"year": y, "month": m, "day": 1}, errors="coerce")

def parse_excel_from_df(df_raw: pd.DataFrame):
    df = normalize_columns(df_raw)

    date_col, date_series = detect_date_column(df)
    if date_series is None:
        year_col, month_col = detect_year_month(df)
        if year_col and month_col:
            date_series = parse_year_month_to_date(df, year_col, month_col)
            date_col = "tanggal"
        else:
            best_col, best_non_na, best_parsed = None, 0, None
            for col in df.columns:
                parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
                non_na = parsed.notna().sum()
                if non_na > best_non_na:
                    best_non_na, best_col, best_parsed = non_na, col, parsed
            if best_parsed is not None and best_non_na >= max(3, len(df) * 0.5):
                date_col, date_series = best_col, best_parsed
            else:
                raise ValueError(
                    "Tidak bisa mengenali kolom tanggal/bulan-tahun.\n"
                    "Pastikan ada kolom tanggal, atau kolom bulan dan tahun."
                )

    df_base = df.copy()
    df_base["tanggal"] = pd.to_datetime(date_series, errors="coerce")
    df_base = df_base[df_base["tanggal"].notna()].copy().sort_values("tanggal")

    numeric_cols = [
        c for c in df_base.columns
        if c not in ["tanggal", date_col] and pd.api.types.is_numeric_dtype(df_base[c])
    ]

    forecast_cols = [c for c in numeric_cols if any(k in c for k in ["mean", "forecast", "prediksi"])]
    lower_cols = [c for c in numeric_cols if any(k in c for k in ["lower", "bawah", "min"])]
    upper_cols = [c for c in numeric_cols if any(k in c for k in ["upper", "atas", "max"])]

    actual_keywords = ["actual", "aktual", "realisasi", "pemakaian", "kebutuhan", "volume", "qty", "jumlah"]
    actual_cols = [c for c in numeric_cols if any(k in c for k in actual_keywords)]

    records = []

    # Aktual (opsional)
    for col in actual_cols:
        for _, row in df_base.iterrows():
            val = row[col]
            if pd.isna(val):
                continue
            records.append({
                "tanggal": row["tanggal"],
                "jenis": "Aktual",
                "nilai": float(val),
                "min": math.nan,
                "max": math.nan,
            })

    # Perkiraan (prediksi)
    if forecast_cols:
        mean_col = forecast_cols[0]
        low_col = lower_cols[0] if lower_cols else None
        up_col = upper_cols[0] if upper_cols else None

        for _, row in df_base.iterrows():
            mval = row[mean_col]
            if pd.isna(mval):
                continue
            records.append({
                "tanggal": row["tanggal"],
                "jenis": "Perkiraan",
                "nilai": float(mval),
                "min": float(row[low_col]) if low_col and not pd.isna(row[low_col]) else math.nan,
                "max": float(row[up_col]) if up_col and not pd.isna(row[up_col]) else math.nan,
            })

    # Fallback
    if not records and numeric_cols:
        col = numeric_cols[0]
        for _, row in df_base.iterrows():
            val = row[col]
            if pd.isna(val):
                continue
            records.append({
                "tanggal": row["tanggal"],
                "jenis": "Perkiraan",
                "nilai": float(val),
                "min": math.nan,
                "max": math.nan,
            })

    tidy = pd.DataFrame.from_records(records)
    if tidy.empty:
        raise ValueError("File terbaca, tapi tidak menemukan kolom angka untuk ditampilkan.")

    tidy["tanggal"] = pd.to_datetime(tidy["tanggal"])
    tidy = tidy.sort_values(["tanggal", "jenis"]).reset_index(drop=True)

    df_actual = tidy[tidy["jenis"] == "Aktual"].copy()
    df_pred = tidy[tidy["jenis"] == "Perkiraan"].copy()
    return tidy, df_actual, df_pred

def parse_excel(file_path_or_buffer):
    df_raw = pd.read_excel(file_path_or_buffer, engine="openpyxl")
    return parse_excel_from_df(df_raw)

# =========================================================
# CHARTS (BULAN + HOVER ANGKA, IKUT SATUAN)
# =========================================================
def make_line_month_chart(df_pred_year: pd.DataFrame, unit_choice: str):
    if df_pred_year is None or df_pred_year.empty:
        return None

    u = unit_suffix(unit_choice)

    d = df_pred_year.copy()
    d["bulan"] = d["tanggal"].dt.to_period("M").dt.to_timestamp()
    agg = d.groupby("bulan", as_index=False)["nilai"].mean().sort_values("bulan")
    agg["nilai_u"] = agg["nilai"].apply(lambda x: convert_value_kg_to_unit(x, unit_choice))

    base = alt.Chart(agg).encode(
        x=alt.X("bulan:T", title="", axis=alt.Axis(format="%b %Y"))
    )

    line = base.mark_line(strokeWidth=3).encode(
        y=alt.Y("nilai_u:Q", title=u),
        color=alt.value("#F6D25E"),
        tooltip=[
            alt.Tooltip("bulan:T", title="Bulan", format="%B %Y"),
            alt.Tooltip("nilai_u:Q", title=f"Perkiraan ({u})", format=",.0f"),
        ],
    )

    nearest = alt.selection_point(on="mouseover", fields=["bulan"], nearest=True, empty=False)

    points = base.mark_point(size=80, opacity=0).add_params(nearest)
    highlight = (
        base.mark_point(size=90)
        .encode(y="nilai_u:Q", color=alt.value("#F6D25E"))
        .transform_filter(nearest)
    )
    rule = base.mark_rule(color="#cdbf9b").encode(x="bulan:T").transform_filter(nearest)
    text = (
        base.mark_text(align="left", dx=10, dy=-10)
        .encode(
            y="nilai_u:Q",
            text=alt.Text("nilai_u:Q", format=",.0f"),
            color=alt.value("#2A241C"),
        )
        .transform_filter(nearest)
    )

    chart = (
        alt.layer(line, points, highlight, rule, text)
        .properties(height=420)
        .configure_view(stroke=None)
        .configure_axis(
            gridColor="#efe6d7",
            tickColor="#efe6d7",
            domainColor="#efe6d7",
            labelColor="#6f675c",
            titleColor="#6f675c",
        )
    )
    return chart

def make_bar_month_chart(df_pred_year: pd.DataFrame, unit_choice: str):
    if df_pred_year is None or df_pred_year.empty:
        return None

    u = unit_suffix(unit_choice)

    d = df_pred_year.copy()
    d["bulan"] = d["tanggal"].dt.month
    d["bulan_nama"] = d["bulan"].apply(month_name_id)
    agg = d.groupby(["bulan", "bulan_nama"], as_index=False)["nilai"].mean().sort_values("bulan")
    agg["nilai_u"] = agg["nilai"].apply(lambda x: convert_value_kg_to_unit(x, unit_choice))

    chart = (
        alt.Chart(agg)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("bulan_nama:N", title="", sort=list(ID_MONTH_NAMES.values())),
            y=alt.Y("nilai_u:Q", title=u),
            tooltip=[
                alt.Tooltip("bulan_nama:N", title="Bulan"),
                alt.Tooltip("nilai_u:Q", title=f"Perkiraan ({u})", format=",.0f"),
            ],
            color=alt.value("#F6D25E"),
        )
        .properties(height=360)
        .configure_view(stroke=None)
        .configure_axis(
            gridColor="#efe6d7",
            tickColor="#efe6d7",
            domainColor="#efe6d7",
            labelColor="#6f675c",
            titleColor="#6f675c",
        )
    )
    return chart

# =========================================================
# TABLE (kg base)
# =========================================================
def month_table(df_pred: pd.DataFrame, year: int):
    d = df_pred[df_pred["tanggal"].dt.year == year].copy()
    if d.empty:
        return d

    d["Bulan"] = d["tanggal"].dt.month.apply(month_name_id)
    out = d.groupby(["Bulan"], as_index=False).agg(
        Perkiraan_kg=("nilai", "mean"),
        Min_kg=("min", "mean"),
        Maks_kg=("max", "mean"),
    )

    if "Min_kg" in out.columns and out["Min_kg"].isna().all():
        out = out.drop(columns=["Min_kg"])
    if "Maks_kg" in out.columns and out["Maks_kg"].isna().all():
        out = out.drop(columns=["Maks_kg"])

    return out

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data(show_spinner=True)
def load_default_data():
    excel_path = Path(__file__).parent / "hasil_prediksi_sarima.xlsx"
    if not excel_path.exists():
        raise FileNotFoundError("File 'hasil_prediksi_sarima.xlsx' tidak ditemukan di folder yang sama dengan app.py")
    return parse_excel(excel_path)

if "data_override" not in st.session_state:
    st.session_state.data_override = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "mode_umkm" not in st.session_state:
    st.session_state.mode_umkm = True

tidy_all, df_actual_all, df_pred_all = load_default_data()
if st.session_state.data_override is not None:
    tidy_all, df_actual_all, df_pred_all = st.session_state.data_override

# =========================================================
# SIDEBAR (UMKM LABELS)
# =========================================================
with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <div class="logo-circle">{logo_html}</div>
          <div>
            <div style="font-weight:800;color:#2a241c;line-height:1.1;">Sale Pisang</div>
            <div class="small-muted" style="margin-top:2px;">Dashboard UMKM</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    mode_umkm = st.toggle("Mode UMKM", value=st.session_state.mode_umkm, key="mode_umkm")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<span class='mode-pill'>MODE: {'UMKM' if mode_umkm else 'Admin'}</span>",
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    def go(p):
        st.session_state.page = p
        st.rerun()

    st.markdown("### Menu")

    is_dash = (st.session_state.page == "Dashboard")
    is_detail = (st.session_state.page == "Detail")
    is_upload = (st.session_state.page == "Upload")

    label_dash = "🏠  Beranda" + (" ✅" if is_dash else "")
    label_detail = "📊  Lihat Rincian Bulanan" + (" ✅" if is_detail else "")

    if st.button(label_dash, use_container_width=True, key="nav_dash"):
        go("Dashboard")
    if st.button(label_detail, use_container_width=True, key="nav_detail"):
        go("Detail")

    if not mode_umkm:
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("### Admin")

        label_upload = "⬆️  Ganti Data Prediksi" + (" ✅" if is_upload else "")
        if st.button(label_upload, use_container_width=True, key="nav_upload"):
            go("Upload")

        st.markdown(
            "<div class='small-muted' style='margin-top:8px;'>"
            "Menu ini untuk mengganti file prediksi (hasil hitung di luar web)."
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='small-muted'>Tips: Pilih tahun, bulan, satuan → klik <b>Tampilkan</b>.</div>",
        unsafe_allow_html=True
    )

page = st.session_state.page
if st.session_state.mode_umkm and page == "Upload":
    st.session_state.page = "Dashboard"
    st.rerun()

# =========================================================
# HEADER
# =========================================================
st.markdown(
    f"""
    <div class="header-wrap">
      <div class="logo-circle">{logo_html}</div>
      <div>
        <div class="header-title">Berapa Pisang yang Perlu Disiapkan?</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")

st.markdown(
    """
    <div class="info-banner">
      <div class="info-icon">i</div>
      <div>
        Pilih <b>tahun</b>, <b>bulan</b>, dan <b>satuan</b>, lalu klik <b>Tampilkan</b>.  
        (Arahkan mouse ke garis kuning untuk melihat angka tiap bulan)
      </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")

# =========================================================
# FILTER CARD + SUBMIT (Tahun + Bulan + Satuan)
# =========================================================
years_available = sorted(df_pred_all["tanggal"].dt.year.unique()) if not df_pred_all.empty else []
if not years_available:
    empty_state("Tidak ada data prediksi", "Cek file Excel bawaan atau ganti data prediksi (Admin).")
    st.stop()

if "filter_year" not in st.session_state:
    st.session_state.filter_year = years_available[0]
if "filter_month" not in st.session_state:
    st.session_state.filter_month = "Semua Bulan"
if "filter_unit" not in st.session_state:
    st.session_state.filter_unit = "Kg"

st.markdown("<div class='filter-card'>", unsafe_allow_html=True)
with st.form("form_filter"):
    cA, cB, cC, cU, cD = st.columns([2.0, 1.0, 1.0, 1.0, 1.0])

    with cA:
        st.markdown("<div class='filter-title'>Pilih Periode</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='filter-sub'>Tentukan tahun, bulan, dan satuan untuk melihat perkiraan kebutuhan.</div>",
            unsafe_allow_html=True
        )

    with cB:
        year = st.selectbox(
            "Tahun",
            years_available,
            index=years_available.index(st.session_state.filter_year),
        )

    with cC:
        month_options = ["Semua Bulan"] + [month_name_id(m) for m in range(1, 13)]
        month = st.selectbox(
            "Bulan",
            month_options,
            index=month_options.index(st.session_state.filter_month),
        )

    with cU:
        unit = st.selectbox(
            "Satuan (untuk grafik)",
            ["Kg", "Sisir"],
            index=["Kg", "Sisir"].index(st.session_state.filter_unit),
        )

    with cD:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        submit = st.form_submit_button("Tampilkan")

st.markdown("</div>", unsafe_allow_html=True)
st.write("")

if submit:
    st.session_state.filter_year = year
    st.session_state.filter_month = month
    st.session_state.filter_unit = unit

year = st.session_state.filter_year
month_name = st.session_state.filter_month
unit_choice = st.session_state.filter_unit
u = unit_suffix(unit_choice)

df_pred_year = df_pred_all[df_pred_all["tanggal"].dt.year == int(year)].copy()

# =========================================================
# PAGE: BERANDA (Dashboard)
# =========================================================
if page == "Dashboard":
    st.markdown("### Jawaban cepat")
    st.markdown(
        "<div class='small-muted'>Angka ini bisa dipakai untuk rencana belanja bahan baku. (Ditampilkan dalam kg & sisir)</div>",
        unsafe_allow_html=True
    )
    st.write("")

    if month_name == "Semua Bulan":
        card("Perkiraan pisang yang perlu disiapkan", "Pilih bulan", "Contoh: Juli 2026", big=True)
    else:
        month_num = [k for k, v in ID_MONTH_NAMES.items() if v == month_name][0]
        df_month = df_pred_year[df_pred_year["tanggal"].dt.month == int(month_num)].copy()

        if df_month.empty:
            card("Perkiraan pisang yang perlu disiapkan", "Data belum ada", "Coba pilih bulan lain.", big=True)
        else:
            v_kg = float(df_month["nilai"].mean())
            text_kg, text_sisir = fmt_dual_units(v_kg)

            card(
                "Perkiraan pisang yang perlu disiapkan",
                f"± {text_kg}<br><span style='font-size:0.98rem;color:#7A736A;'>≈ {text_sisir}</span>",
                f"Bulan {month_name} {year}",
                big=True
            )

    st.write("")
    st.markdown("### Perkiraan kebutuhan pisang per bulan")
    st.markdown(
        "<div class='small-muted'>Arahkan mouse ke garis kuning untuk melihat angka tiap bulan.</div>",
        unsafe_allow_html=True
    )
    st.write("")

    chart = make_line_month_chart(df_pred_year, unit_choice)
    if chart is None:
        empty_state("Grafik belum tersedia", "Data prediksi untuk tahun ini belum ada.")
    else:
        st.altair_chart(chart, use_container_width=True)

    st.write("")
    st.markdown(
        """
        <div class="banner">
          Untuk melihat tabel lengkap (kg & sisir) dan ringkasan setahun, buka menu <b>Lihat Rincian Bulanan</b>.
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# PAGE: RINCIAN (Detail)
# =========================================================
elif page == "Detail":
    st.markdown("### Rincian kebutuhan pisang per bulan")
    st.markdown(
        "<div class='small-muted'>Bagian ini menampilkan angka perkiraan untuk setiap bulan sebagai panduan belanja (kg & sisir).</div>",
        unsafe_allow_html=True
    )
    st.write("")

    if df_pred_year.empty:
        empty_state("Data tahun ini belum ada", "Coba pilih tahun lain.")
        st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Grafik ringkas per bulan")
    st.markdown(
        "<div class='small-muted'>Grafik mengikuti satuan pilihan di filter (kg / sisir).</div>",
        unsafe_allow_html=True
    )
    bar = make_bar_month_chart(df_pred_year, unit_choice)
    if bar is not None:
        st.altair_chart(bar, use_container_width=True)
    else:
        st.caption("Grafik belum tersedia.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")

    st.markdown("### Tabel perkiraan kebutuhan per bulan (kg & sisir)")
    tbl = month_table(df_pred_all, int(year))
    if tbl.empty:
        st.caption("Belum ada data prediksi.")
    else:
        tbl_show = tbl.copy()

        # bikin versi sisir dari kolom kg (selalu tampil dua-duanya)
        for col in ["Perkiraan_kg", "Min_kg", "Maks_kg"]:
            if col in tbl_show.columns:
                tbl_show[col.replace("_kg", "_sisir")] = tbl_show[col].apply(
                    lambda x: convert_value_kg_to_unit(x, "Sisir")
                )

        tbl_show = tbl_show.rename(columns={
            "Perkiraan_kg": "Perkiraan (kg)",
            "Min_kg": "Min (kg)",
            "Maks_kg": "Maks (kg)",
            "Perkiraan_sisir": "Perkiraan (sisir)",
            "Min_sisir": "Min (sisir)",
            "Maks_sisir": "Maks (sisir)",
        })

        st.dataframe(tbl_show, use_container_width=True, hide_index=True)

    st.write("")
    g = df_pred_year.groupby("tanggal")["nilai"].mean().sort_index()
    total_year_kg = float(df_pred_year["nilai"].sum())
    avg_month_kg = float(g.mean())
    idx_peak = g.idxmax()
    peak_val_kg = float(g.max())

    total_year_sisir = convert_value_kg_to_unit(total_year_kg, "Sisir")
    avg_month_sisir = convert_value_kg_to_unit(avg_month_kg, "Sisir")
    peak_val_sisir = convert_value_kg_to_unit(peak_val_kg, "Sisir")

    c1, c2, c3 = st.columns(3)
    with c1:
        card("Total kebutuhan 1 tahun", f"{fmt_int(total_year_kg)} kg<br><span style='font-size:0.98rem;color:#7A736A;'>≈ {fmt_int(total_year_sisir)} sisir</span>", f"Tahun {year}")
    with c2:
        card("Rata-rata per bulan", f"{fmt_int(avg_month_kg)} kg<br><span style='font-size:0.98rem;color:#7A736A;'>≈ {fmt_int(avg_month_sisir)} sisir</span>", "Sebagai patokan belanja")
    with c3:
        card("Bulan kebutuhan tertinggi", month_name_id(idx_peak.month), f"± {fmt_int(peak_val_kg)} kg<br><span style='font-size:0.98rem;color:#7A736A;'>≈ {fmt_int(peak_val_sisir)} sisir</span>")

    st.write("")
    st.markdown("### Saran untuk usaha")
    st.markdown(
        "- Siapkan stok pisang lebih awal menjelang bulan dengan kebutuhan tertinggi.\n"
        "- Saat memasuki bulan yang lebih sepi, belanja bahan baku bisa dikurangi.\n"
        "- Gunakan angka ini sebagai panduan, lalu sesuaikan dengan kondisi penjualan nyata."
    )

    st.write("")
    if not tbl.empty:
        # export: dua satuan juga
        export_df = tbl.copy()
        for col in ["Perkiraan_kg", "Min_kg", "Maks_kg"]:
            if col in export_df.columns:
                export_df[col.replace("_kg", "_sisir")] = export_df[col].apply(
                    lambda x: convert_value_kg_to_unit(x, "Sisir")
                )

        export_df = export_df.rename(columns={
            "Perkiraan_kg": "Perkiraan_kg",
            "Min_kg": "Min_kg",
            "Maks_kg": "Maks_kg",
            "Perkiraan_sisir": "Perkiraan_sisir",
            "Min_sisir": "Min_sisir",
            "Maks_sisir": "Maks_sisir",
        })

        xlsx_bytes = to_excel_bytes(export_df, sheet_name=f"Rincian_{year}")
        st.download_button(
            "⬇️ Unduh tabel rincian (kg & sisir)",
            data=xlsx_bytes,
            file_name=f"rincian_kebutuhan_{year}_kg_sisir.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

# =========================================================
# PAGE: UPLOAD (Admin)
# =========================================================
elif page == "Upload":
    st.markdown("## Ganti Data Prediksi")
    st.markdown(
        "<div class='small-muted'>Unggah file Excel hasil perhitungan.</div>",
        unsafe_allow_html=True
    )
    st.write("")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Upload file Excel")
    st.markdown(
        "<div class='small-muted'>Setelah upload, cek preview. Kalau sudah benar, klik <b>Konfirmasi & Simpan</b>.</div>",
        unsafe_allow_html=True
    )
    st.write("")

    uploaded = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx", "xls"], label_visibility="collapsed")

    if uploaded is None:
        st.markdown(
            "<div class='banner'>Tips: pastikan ada kolom tanggal/periode dan kolom angka perkiraan.</div>",
            unsafe_allow_html=True
        )
    else:
        try:
            tidy_new, act_new, pred_new = parse_excel(uploaded)

            st.write("Preview data perkiraan (5 baris):")
            st.dataframe(pred_new.head(5), use_container_width=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Batal", use_container_width=True):
                    st.stop()
            with col2:
                if st.button("Konfirmasi & Simpan", use_container_width=True):
                    st.session_state.data_override = (tidy_new, act_new, pred_new)
                    st.success("Berhasil! Data dashboard sudah diperbarui.")
                    st.session_state.page = "Dashboard"
                    st.rerun()

        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


