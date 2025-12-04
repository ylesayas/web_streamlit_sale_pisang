import math
from pathlib import Path
import re

import pandas as pd
import streamlit as st
import altair as alt

# -----------------------------------
# Konfigurasi halaman
# -----------------------------------
st.set_page_config(
    page_title="Dashboard Penjualan Pisang",
    page_icon="🍌",
    layout="wide",
)

# -----------------------------------
# Load CSS eksternal
# -----------------------------------
def load_local_css(file_name: str = "theme.css") -> None:
    try:
        css_path = Path(__file__).parent / file_name
        with css_path.open() as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


load_local_css()

# -----------------------------------
# Sistem PIN
# -----------------------------------
PIN_UMKM = "5454"
PIN_ADMIN = "0708"

if "auth" not in st.session_state:
    st.session_state.auth = None  # None / "umkm" / "admin"

# -----------------------------------
# Halaman login
# -----------------------------------
def login_screen():
    st.markdown(
        """
        <div class="login-card">
          <div class="login-logo-circle">🍌</div>
          <h1>Halaman Masuk Dashboard</h1>
          <p>Masukkan kode akses untuk melihat laporan penjualan pisang.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # input PIN + tombol di tengah, tidak melebar ke samping
    col_left, col_center, col_right = st.columns([2, 3, 2])
    with col_center:
        pin = st.text_input(
            "Kode PIN",
            type="password",
            placeholder="Masukkan kode PIN di sini...",
            key="login_pin",
        )
        if st.button("Masuk", use_container_width=True, key="login_button"):
            if pin == PIN_UMKM:
                st.session_state.auth = "umkm"
                st.rerun()
            elif pin == PIN_ADMIN:
                st.session_state.auth = "admin"
                st.rerun()
            else:
                st.error("PIN salah. Coba lagi.")


if st.session_state.auth is None:
    login_screen()
    st.stop()

MODE_ADMIN = st.session_state.auth == "admin"
MODE_UMKM = st.session_state.auth == "umkm"

# -----------------------------------
# Default profil UMKM
# -----------------------------------
if "umkm_profile" not in st.session_state:
    st.session_state.umkm_profile = {
        "nama_umkm": "Bungo Family",
        "nama_pemilik": "",
        "alamat_singkat": "",
    }

if "show_profile_editor" not in st.session_state:
    st.session_state.show_profile_editor = False

# -----------------------------------
# Helper nama bulan Indonesia
# -----------------------------------
ID_MONTHS = {
    "januari": 1,
    "jan": 1,
    "jan.": 1,
    "februari": 2,
    "feb": 2,
    "maret": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "mei": 5,
    "juni": 6,
    "jun": 6,
    "juli": 7,
    "jul": 7,
    "agustus": 8,
    "agu": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "oktober": 10,
    "okt": 10,
    "november": 11,
    "nov": 11,
    "desember": 12,
    "des": 12,
    "dec": 12,
}

ID_MONTH_NAMES = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def month_name_id(month_num: int) -> str:
    return ID_MONTH_NAMES.get(int(month_num), str(month_num))


# -----------------------------------
# UNIVERSAL EXCEL PARSER
# -----------------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    new_cols = []
    for c in df.columns:
        c_str = str(c).strip()
        c_str = re.sub(r"\s+", "_", c_str)
        c_str = c_str.lower()
        new_cols.append(c_str)
    df.columns = new_cols
    return df


def detect_date_column(df: pd.DataFrame):
    # 1) sudah datetime
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if df[col].notna().sum() >= max(3, len(df) * 0.5):
                return col, df[col]
    # 2) kolom teks dengan kata kunci tanggal
    date_keywords = [
        "tanggal",
        "tgl",
        "date",
        "waktu",
        "period",
        "periode",
        "bulan_tahun",
        "bulan-thn",
        "bulan-tahun",
    ]
    for col in df.columns:
        if any(k in col for k in date_keywords):
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            if parsed.notna().sum() >= max(3, len(df) * 0.5):
                return col, parsed
    return None, None


def detect_year_month(df: pd.DataFrame):
    year_col = None
    month_col = None
    for col in df.columns:
        if any(k in col for k in ["tahun", "year", "thn", "th"]):
            year_col = col
        if any(k in col for k in ["bulan", "month", "bln", "mon"]):
            month_col = col
    return year_col, month_col


def parse_year_month_to_date(df: pd.DataFrame, year_col: str, month_col: str) -> pd.Series:
    years = df[year_col]
    months_raw = df[month_col]

    y = pd.to_numeric(years, errors="coerce")

    # handle tahun 2 digit
    if (y < 100).sum() > 0 and (y < 100).sum() >= len(y) * 0.5:
        y = y.apply(lambda v: 2000 + v if pd.notna(v) else v)

    m = pd.to_numeric(months_raw, errors="coerce")
    mask = m.isna() & months_raw.notna()
    if mask.any():

        def map_month(x):
            if pd.isna(x):
                return math.nan
            s = str(x).strip().lower()
            s2 = re.sub(r"[^\w]+$", "", s)
            return ID_MONTHS.get(s2, math.nan)

        m2 = months_raw[mask].map(map_month)
        m[mask] = m2

    dates = pd.to_datetime({"year": y, "month": m, "day": 1}, errors="coerce")
    return dates


def parse_sales_excel_from_df(df_raw: pd.DataFrame):
    df = normalize_columns(df_raw)

    date_col, date_series = detect_date_column(df)
    if date_series is None:
        year_col, month_col = detect_year_month(df)
        if year_col and month_col:
            dates = parse_year_month_to_date(df, year_col, month_col)
            date_series = dates
            date_col = "tanggal"
        else:
            best_col = None
            best_non_na = 0
            best_parsed = None
            for col in df.columns:
                parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
                non_na = parsed.notna().sum()
                if non_na > best_non_na:
                    best_non_na = non_na
                    best_col = col
                    best_parsed = parsed
            if best_parsed is not None and best_non_na >= max(3, len(df) * 0.5):
                date_col = best_col
                date_series = best_parsed
            else:
                raise ValueError(
                    "Tidak bisa mengenali kolom tanggal/bulan-tahun di file Excel.\n"
                    "Pastikan ada kolom tanggal, atau kolom bulan dan tahun."
                )

    df_base = df.copy()
    df_base["tanggal"] = pd.to_datetime(date_series, errors="coerce")
    df_base = df_base[df_base["tanggal"].notna()].copy()
    df_base = df_base.sort_values("tanggal")

    numeric_cols = [
        c
        for c in df_base.columns
        if c not in ["tanggal", date_col]
        and pd.api.types.is_numeric_dtype(df_base[c])
    ]

    forecast_mean_cols = [
        c for c in numeric_cols if any(k in c for k in ["mean", "forecast", "prediksi"])
    ]
    lower_cols = [
        c
        for c in numeric_cols
        if any(k in c for k in ["lower", "lower_ci", "ci_lower", "bawah"])
    ]
    upper_cols = [
        c
        for c in numeric_cols
        if any(k in c for k in ["upper", "upper_ci", "ci_upper", "atas"])
    ]

    actual_keywords = [
        "actual",
        "aktual",
        "realisasi",
        "penjualan",
        "sales",
        "qty",
        "jumlah",
        "volume",
        "unit",
    ]
    actual_cols = [c for c in numeric_cols if any(k in c for k in actual_keywords)]

    records = []

    # Data aktual
    for col in actual_cols:
        for _, row in df_base.iterrows():
            val = row[col]
            if pd.isna(val):
                continue
            records.append(
                {
                    "tanggal": row["tanggal"],
                    "jenis": "Aktual",
                    "sumber": col,
                    "nilai": float(val),
                    "lower": math.nan,
                    "upper": math.nan,
                }
            )

    # Data prediksi
    if forecast_mean_cols:
        mean_col = forecast_mean_cols[0]
        lower_col = lower_cols[0] if lower_cols else None
        upper_col = upper_cols[0] if upper_cols else None

        for _, row in df_base.iterrows():
            mval = row[mean_col]
            if pd.isna(mval):
                continue
            records.append(
                {
                    "tanggal": row["tanggal"],
                    "jenis": "Prediksi",
                    "sumber": mean_col,
                    "nilai": float(mval),
                    "lower": float(row[lower_col])
                    if lower_col and not pd.isna(row[lower_col])
                    else math.nan,
                    "upper": float(row[upper_col])
                    if upper_col and not pd.isna(row[upper_col])
                    else math.nan,
                }
            )

    # Fallback kalau nggak ketemu apa pun
    if not records and numeric_cols:
        col = numeric_cols[0]
        for _, row in df_base.iterrows():
            val = row[col]
            if pd.isna(val):
                continue
            records.append(
                {
                    "tanggal": row["tanggal"],
                    "jenis": "Aktual",
                    "sumber": col,
                    "nilai": float(val),
                    "lower": math.nan,
                    "upper": math.nan,
                }
            )

    tidy = pd.DataFrame.from_records(records)

    if tidy.empty:
        raise ValueError(
            "File Excel berhasil dibaca, tetapi tidak menemukan kolom angka "
            "untuk penjualan atau prediksi."
        )

    tidy["tanggal"] = pd.to_datetime(tidy["tanggal"])
    tidy = tidy.sort_values(["tanggal", "jenis"]).reset_index(drop=True)

    df_actual = tidy[tidy["jenis"] == "Aktual"].copy()
    df_forecast = tidy[tidy["jenis"] == "Prediksi"].copy()

    return tidy, df_actual, df_forecast


def parse_sales_excel(file_path_or_buffer):
    if isinstance(file_path_or_buffer, (str, Path)):
        df_raw = pd.read_excel(file_path_or_buffer, engine="openpyxl")
    else:
        df_raw = pd.read_excel(file_path_or_buffer, engine="openpyxl")
    return parse_sales_excel_from_df(df_raw)


# -----------------------------------
# Analisis ringkas otomatis
# -----------------------------------
def build_summary(tidy: pd.DataFrame) -> str:
    if tidy.empty:
        return "Data tidak ditemukan di file Excel."

    df_a = tidy[tidy["jenis"] == "Aktual"].copy()
    df_p = tidy[tidy["jenis"] == "Prediksi"].copy()

    lines = []

    if not df_a.empty:
        g = df_a.groupby("tanggal")["nilai"].mean().sort_index()
        first_date = g.index[0]
        last_date = g.index[-1]
        first_val = g.iloc[0]
        last_val = g.iloc[-1]

        if len(g) >= 13:
            recent = g.iloc[-12:].mean()
            prev = g.iloc[-24:-12].mean() if len(g) >= 24 else g.iloc[:-12].mean()
            if prev and not pd.isna(prev) and prev != 0:
                growth = (recent - prev) / prev * 100
                trend_phrase = "meningkat" if growth > 0 else "menurun"
                lines.append(
                    f"Secara umum, rata-rata penjualan aktual {trend_phrase} "
                    f"sekitar {abs(growth):.1f}% dibanding periode sebelumnya."
                )
        else:
            if first_val and first_val != 0:
                growth = (last_val - first_val) / first_val * 100
                trend_phrase = "naik" if growth > 0 else "turun"
                lines.append(
                    f"Selama periode {first_date.year}–{last_date.year}, "
                    f"penjualan aktual {trend_phrase} sekitar {abs(growth):.1f}% "
                    f"dari awal sampai akhir."
                )

        idxmax = g.idxmax()
        vmax = g.max()
        lines.append(
            f"Bulan dengan penjualan aktual tertinggi: "
            f"{month_name_id(idxmax.month)} {idxmax.year} "
            f"(sekitar {vmax:,.0f} unit)."
        )

    if not df_p.empty:
        gp = df_p.groupby("tanggal")["nilai"].mean().sort_index()
        start = gp.index[0]
        end = gp.index[-1]
        lines.append(
            f"Ada prediksi penjualan dari "
            f"{month_name_id(start.month)} {start.year} "
            f"sampai {month_name_id(end.month)} {end.year}."
        )

        idxmax = gp.idxmax()
        vmax = gp.max()
        lines.append(
            f"Bulan prediksi tertinggi: "
            f"{month_name_id(idxmax.month)} {idxmax.year} "
            f"(sekitar {vmax:,.0f} unit)."
        )

        if len(gp) >= 2:
            first_val = gp.iloc[0]
            last_val = gp.iloc[-1]
            if first_val and first_val != 0:
                growth = (last_val - first_val) / first_val * 100
                trend_phrase = "cenderung naik" if growth > 0 else "cenderung turun"
                lines.append(
                    f"Secara garis besar, prediksi {trend_phrase} sekitar "
                    f"{abs(growth):.1f}% dari awal sampai akhir periode."
                )

    if not lines:
        return (
            "Data berhasil dibaca, namun belum ada kolom penjualan "
            "yang bisa dianalisis."
        )

    return " ".join(lines)


# -----------------------------------
# Saran untuk UMKM
# -----------------------------------
def build_umkm_advice(df_forecast: pd.DataFrame, profile: dict = None) -> str:
    if df_forecast is None or df_forecast.empty:
        return "Belum ada data prediksi untuk dibuatkan saran."

    g = df_forecast.sort_values("tanggal")
    peak = g.loc[g["nilai"].idxmax()]
    low = g.loc[g["nilai"].idxmin()]

    nama_umkm = None
    if profile:
        nama_umkm = (profile.get("nama_umkm") or "").strip()

    bullets = []
    if nama_umkm:
        bullets.append(
            f"<li>Untuk <b>{nama_umkm}</b>, hasil prediksi menunjukkan adanya pola naik-turun penjualan antar bulan.</li>"
        )
    else:
        bullets.append(
            "<li>Hasil prediksi menunjukkan adanya pola naik-turun penjualan antar bulan.</li>"
        )

    bullets.append(
        f"<li><b>Bulan paling ramai</b> diperkirakan <b>{peak['tanggal'].strftime('%B %Y')}</b> "
        f"dengan kebutuhan sekitar <b>{int(peak['nilai']):,} unit</b>.</li>"
    )
    bullets.append(
        f"<li><b>Bulan paling sepi</b> diperkirakan <b>{low['tanggal'].strftime('%B %Y')}</b> "
        f"dengan kebutuhan sekitar <b>{int(low['nilai']):,} unit</b>.</li>"
    )
    bullets.append(
        "<li>Tambahkan persiapan bahan menjelang bulan ramai dan kurangi pembelian pada bulan yang sepi "
        "agar stok lebih efisien dan tidak banyak sisa.</li>"
    )
    bullets.append(
        "<li>Pantau kembali penjualan aktual tiap bulan dan bandingkan dengan prediksi "
        "agar keputusan pembelian bahan baku tetap terkontrol.</li>"
    )

    html = "<ul>" + "".join(bullets) + "</ul>"
    return html


# -----------------------------------
# Tandai bulan Ramadhan (Maret–April)
# -----------------------------------
def add_ramadhan_flag(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_ramadhan"] = df["tanggal"].dt.month.isin([3, 4])
    return df


# -----------------------------------
# Grafik utama (historis + forecast)
# -----------------------------------
def create_main_chart(tidy: pd.DataFrame):
    if tidy.empty:
        return None

    df = add_ramadhan_flag(tidy).copy()
    df["is_peak"] = False
    df_pred = df[df["jenis"] == "Prediksi"]
    if not df_pred.empty:
        idx_peak = df_pred["nilai"].idxmax()
        peak_date = df_pred.loc[idx_peak, "tanggal"]
        df.loc[(df["tanggal"] == peak_date) & (df["jenis"] == "Prediksi"), "is_peak"] = True

    base = alt.Chart(df).encode(x=alt.X("tanggal:T", title="Tanggal"))

    color_actual = "#1E5AA8"
    color_forecast = "#F6C453"
    color_ramadhan = "#FFE8A3"
    color_peak = "#FF9F1C"

    band = (
        base.transform_filter(alt.datum.jenis == "Prediksi")
        .mark_area(opacity=0.18)
        .encode(
            y=alt.Y("lower:Q", title="Penjualan"),
            y2="upper:Q",
            color=alt.value(color_forecast),
        )
    )

    line_actual = (
        base.transform_filter(alt.datum.jenis == "Aktual")
        .mark_line(strokeWidth=3)
        .encode(
            y=alt.Y("nilai:Q", title="Penjualan"),
            color=alt.value(color_actual),
            tooltip=[
                alt.Tooltip("tanggal:T", title="Tanggal"),
                alt.Tooltip("nilai:Q", title="Aktual", format=",.0f"),
            ],
        )
    )

    line_pred = (
        base.transform_filter(alt.datum.jenis == "Prediksi")
        .mark_line(strokeDash=[6, 4], strokeWidth=3)
        .encode(
            y="nilai:Q",
            color=alt.value(color_forecast),
            tooltip=[
                alt.Tooltip("tanggal:T", title="Tanggal"),
                alt.Tooltip("nilai:Q", title="Prediksi", format=",.0f"),
                alt.Tooltip("lower:Q", title="Batas bawah", format=",.0f"),
                alt.Tooltip("upper:Q", title="Batas atas", format=",.0f"),
            ],
        )
    )

    ramadhan_points = (
        base.transform_filter(alt.datum.is_ramadhan == True)
        .mark_point(size=90, shape="diamond")
        .encode(
            y="nilai:Q",
            color=alt.value(color_ramadhan),
            tooltip=[
                alt.Tooltip("tanggal:T", title="Tanggal"),
                alt.Tooltip("nilai:Q", title="Nilai", format=",.0f"),
                alt.Tooltip("jenis:N", title="Jenis"),
            ],
        )
    )

    peak_point = (
        base.transform_filter(alt.datum.is_peak == True)
        .mark_point(size=140, shape="circle")
        .encode(
            y="nilai:Q",
            color=alt.value(color_peak),
            tooltip=[
                alt.Tooltip("tanggal:T", title="Bulan puncak"),
                alt.Tooltip("nilai:Q", title="Prediksi tertinggi", format=",.0f"),
            ],
        )
    )

    chart = alt.layer(band, line_actual, line_pred, ramadhan_points, peak_point).resolve_scale(
        y="shared"
    )

    return chart.properties(height=420)


# -----------------------------------
# Grafik YoY (perbandingan antar tahun)
# -----------------------------------
def create_yoy_chart(df_actual: pd.DataFrame):
    if df_actual is None or df_actual.empty:
        return None

    df = df_actual.copy()
    df["tahun"] = df["tanggal"].dt.year.astype(str)
    df["bulan"] = df["tanggal"].dt.month
    df["bulan_nama"] = df["bulan"].apply(month_name_id)

    agg = (
        df.groupby(["tahun", "bulan", "bulan_nama"])["nilai"]
        .mean()
        .reset_index()
        .sort_values(["tahun", "bulan"])
    )

    if agg["tahun"].nunique() <= 1:
        return None

    chart = (
        alt.Chart(agg)
        .mark_line(point=True)
        .encode(
            x=alt.X("bulan_nama:N", title="Bulan", sort=list(ID_MONTH_NAMES.values())),
            y=alt.Y("nilai:Q", title="Rata-rata penjualan"),
            color=alt.Color("tahun:N", title="Tahun"),
            tooltip=[
                alt.Tooltip("tahun:N", title="Tahun"),
                alt.Tooltip("bulan_nama:N", title="Bulan"),
                alt.Tooltip("nilai:Q", title="Rata-rata", format=",.0f"),
            ],
        )
        .properties(height=360)
    )

    return chart


# -----------------------------------
# Top / bottom bulan dari forecast
# -----------------------------------
def get_top_bottom_months(df_forecast: pd.DataFrame, top_n: int = 3):
    if df_forecast is None or df_forecast.empty:
        return None, None

    df = df_forecast.copy().sort_values("tanggal")
    agg = df.groupby("tanggal")["nilai"].mean().reset_index()

    top = agg.nlargest(top_n, "nilai").copy()
    bottom = agg.nsmallest(top_n, "nilai").copy()

    top["Bulan"] = top["tanggal"].dt.strftime("%B %Y")
    bottom["Bulan"] = bottom["tanggal"].dt.strftime("%B %Y")

    top = top[["Bulan", "nilai"]].rename(columns={"nilai": "Prediksi"})
    bottom = bottom[["Bulan", "nilai"]].rename(columns={"nilai": "Prediksi"})

    return top, bottom


# -----------------------------------
# Sidebar
# -----------------------------------
with st.sidebar:
    if MODE_ADMIN:
        st.markdown("**Mode: Admin**")
    else:
        st.markdown("**Mode: UMKM**")

    if st.button("Keluar"):
        st.session_state.auth = None
        st.rerun()

    st.markdown("### Pengaturan Tampilan")
    font_size = st.slider(
        "Ukuran teks (sesuaikan kenyamanan baca)",
        min_value=14,
        max_value=24,
        value=18,
        step=1,
    )

# Global font size
st.markdown(
    f"""
    <style>
    html, body, .stApp {{
        font-size: {font_size}px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------
# Header dashboard
# -----------------------------------
umkm_profile = st.session_state.get("umkm_profile", {})
nama_umkm_disp = umkm_profile.get("nama_umkm") or "UMKM Salai Pisang"

# Header + tombol profil di satu baris
header_col_left, header_col_right = st.columns([5, 1])

with header_col_left:
    st.markdown(
        f"""
        <div class="header-banana">
          <div class="header-left">
            <div class="logo-circle big">🍌</div>
            <div class="title-block">
              <h1>Dashboard Forecast Stok Salai Pisang</h1>
              <p>{nama_umkm_disp} · Perencanaan stok berbasis model SARIMA.</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_col_right:
    if st.button("Profil usaha", key="btn_profil_header"):
        st.session_state.show_profile_editor = True

# -----------------------------------
# Editor profil (muncul saat tombol di klik)
# -----------------------------------
if st.session_state.show_profile_editor:
    st.markdown("### Profil usaha")
    with st.form("form_profil_header"):
        nama_umkm = st.text_input(
            "Nama usaha",
            value=umkm_profile.get("nama_umkm", ""),
        )
        nama_pemilik = st.text_input(
            "Nama pemilik",
            value=umkm_profile.get("nama_pemilik", ""),
        )
        alamat_singkat = st.text_area(
            "Alamat singkat",
            value=umkm_profile.get("alamat_singkat", ""),
            height=80,
        )

        col_simpan, col_batal = st.columns(2)
        simpan = col_simpan.form_submit_button("Simpan perubahan")
        batal = col_batal.form_submit_button("Tutup")

        if simpan:
            st.session_state.umkm_profile = {
                "nama_umkm": (nama_umkm or "UMKM Salai Pisang").strip(),
                "nama_pemilik": (nama_pemilik or "").strip(),
                "alamat_singkat": (alamat_singkat or "").strip(),
            }
            st.session_state.show_profile_editor = False
            st.success("Profil usaha berhasil diperbarui.")
            st.experimental_rerun()
        elif batal:
            st.session_state.show_profile_editor = False
            st.experimental_rerun()

# Card profil ringkas
umkm_profile = st.session_state.umkm_profile
st.markdown(
    f"""
    <div class="analysis-box soft">
      <b>Profil usaha (ringkas)</b><br/>
      Nama usaha: {umkm_profile.get("nama_umkm") or "-"}<br/>
      Pemilik: {umkm_profile.get("nama_pemilik") or "-"}<br/>
      Alamat: {umkm_profile.get("alamat_singkat") or "-"}<br/>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------
# Admin: upload Excel opsional
# -----------------------------------
@st.cache_data(show_spinner=True)
def load_default_data():
    excel_path = Path(__file__).parent / "hasil_prediksi_sarima.xlsx"
    tidy, df_actual, df_forecast = parse_sales_excel(excel_path)
    return tidy, df_actual, df_forecast


tidy_all, df_actual_all, df_forecast_all = load_default_data()

if MODE_ADMIN:
    st.subheader("Kelola data Excel (Admin)")
    st.caption(
        "Bagian ini hanya untuk peneliti atau pemilik usaha jika ingin menguji "
        "atau memperbarui data. Jika tidak diisi, sistem memakai file bawaan di repo."
    )
    uploaded = st.file_uploader(
        "Upload file Excel hasil model SARIMA (opsional)",
        type=["xlsx", "xls"],
    )
    if uploaded is not None:
        try:
            tidy_new, act_new, pred_new = parse_sales_excel(uploaded)
            tidy_all, df_actual_all, df_forecast_all = tidy_new, act_new, pred_new
            st.success("File berhasil dibaca dan digunakan di dashboard.")
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

# -----------------------------------
# Filter fokus tahun (untuk prediksi)
# -----------------------------------
if not df_forecast_all.empty:
    tahun_list = sorted(df_forecast_all["tanggal"].dt.year.unique())
    tahun_label = st.selectbox(
        "Fokus tahun prediksi",
        ["Semua tahun"] + [str(t) for t in tahun_list],
        index=0,
    )
else:
    tahun_label = "Semua tahun"

if tahun_label == "Semua tahun":
    tidy = tidy_all
    df_forecast = df_forecast_all
    df_actual = df_actual_all
else:
    yr = int(tahun_label)
    df_forecast = df_forecast_all[df_forecast_all["tanggal"].dt.year == yr].copy()
    # untuk grafik utama, filter hanya tahun itu
    tidy = tidy_all[tidy_all["tanggal"].dt.year == yr].copy()
    df_actual = df_actual_all[df_actual_all["tanggal"].dt.year == yr].copy()

# -----------------------------------
# Ringkasan singkat di sidebar
# -----------------------------------
with st.sidebar:
    st.markdown("### Ringkasan Singkat")
    try:
        if not df_forecast.empty:
            peak = df_forecast.loc[df_forecast["nilai"].idxmax()]
            st.markdown(
                f"""
                <div class="chip chip-green">
                  <div class="chip-title">Puncak prediksi:</div>
                  <div class="chip-value">{peak['tanggal'].strftime('%B %Y')} — <b>{int(peak['nilai'])} unit</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            low = df_forecast.loc[df_forecast["nilai"].idxmin()]
            st.markdown(
                f"""
                <div class="chip chip-blue">
                  <div class="chip-title">Prediksi terendah:</div>
                  <div class="chip-value">{low['tanggal'].strftime('%B %Y')} — <b>{int(low['nilai'])} unit</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception:
        st.caption("Belum ada ringkasan prediksi.")

    st.markdown("### Sumber Data")
    try:
        total_data = len(tidy_all)
        st.caption(
            "Data penjualan dan prediksi otomatis diambil dari file Excel di dalam sistem. "
            "Pengguna tidak perlu upload file apa pun."
        )
        st.caption(f"Jumlah baris data: {total_data}")
    except Exception:
        st.caption("Dataset tidak terbaca.")

# -----------------------------------
# Ringkasan angka utama (metric cards)
# -----------------------------------
summary_text = build_summary(tidy)

st.markdown("<div class='metric-row'>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    if not df_forecast.empty:
        total_pred = df_forecast["tanggal"].nunique()
        st.metric("Periode prediksi", f"{total_pred} bulan")
    else:
        st.metric("Periode prediksi", "–")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    if not df_forecast.empty:
        peak = df_forecast.loc[df_forecast["nilai"].idxmax()]
        st.metric(
            "Bulan tertinggi",
            f"{int(peak['nilai'])} unit",
            peak["tanggal"].strftime("%B %Y"),
        )
    else:
        st.metric("Bulan tertinggi", "–")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    if not df_forecast.empty:
        first_f = df_forecast.sort_values("tanggal")["nilai"].iloc[0]
        st.metric("Penjualan bulan pertama", f"{int(first_f)} unit")
    else:
        st.metric("Penjualan bulan pertama", "–")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Info grafik
st.markdown(
    """
    <div class="hint-banner">
      • Garis kuning putus-putus = prediksi penjualan  
      • Area kuning = batas bawah & atas prediksi  
      • Titik berbentuk berlian = bulan sekitar Ramadan (perkiraan)
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------
# Layout utama: grafik & panel kanan
# -----------------------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Tren penjualan dan prediksi")
    main_chart = create_main_chart(tidy)
    if main_chart is not None:
        st.altair_chart(main_chart, use_container_width=True)
    else:
        st.warning("Belum ada data untuk ditampilkan di grafik.")

with right_col:
    st.subheader("Saran untuk UMKM")
    umkm_html = build_umkm_advice(df_forecast, umkm_profile)
    st.markdown(
        f"<div class='analysis-box'>{umkm_html}</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Analisis singkat otomatis")
    st.markdown(
        f"<div class='analysis-box'>{summary_text}</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Unduh data dan ringkasan")
    csv_buffer = tidy.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download data (CSV)",
        data=csv_buffer,
        file_name="data_penjualan_pisang.csv",
        mime="text/csv",
    )

    txt_buffer = summary_text.encode("utf-8")
    st.download_button(
        label="📄 Download ringkasan (TXT)",
        data=txt_buffer,
        file_name="ringkasan_penjualan_pisang.txt",
        mime="text/plain",
    )

# -----------------------------------
# Grafik YoY - perbandingan tahun ke tahun
# -----------------------------------
st.markdown("### Perbandingan penjualan tahun ke tahun")
st.caption(
    "Grafik ini membantu membandingkan pola penjualan antar tahun untuk setiap bulan."
)

yoy_chart = create_yoy_chart(df_actual_all)
if yoy_chart is not None:
    st.altair_chart(yoy_chart, use_container_width=True)
else:
    st.caption(
        "Grafik year-to-year akan tampil jika data aktual mencakup lebih dari satu tahun dan ada lebih dari satu tahun berbeda."
    )

# -----------------------------------
# Ringkasan bulan paling ramai & sepi
# -----------------------------------
top3, bottom3 = get_top_bottom_months(df_forecast)

st.markdown("### Ringkasan bulan paling ramai dan sepi")
col_top, col_low = st.columns(2)

with col_top:
    st.markdown("**3 Bulan prediksi tertinggi**")
    if top3 is not None:
        st.dataframe(top3, use_container_width=True, hide_index=True)
    else:
        st.caption("Belum ada data prediksi.")

with col_low:
    st.markdown("**3 Bulan prediksi terendah**")
    if bottom3 is not None:
        st.dataframe(bottom3, use_container_width=True, hide_index=True)
    else:
        st.caption("Belum ada data prediksi.")

# -----------------------------------
# Tabel prediksi detail
# -----------------------------------
with st.expander("Lihat data prediksi (tabel)"):
    if not df_forecast.empty:
        st.dataframe(
            df_forecast[["tanggal", "nilai", "lower", "upper"]].rename(
                columns={
                    "tanggal": "Tanggal",
                    "nilai": "Prediksi",
                    "lower": "Batas bawah",
                    "upper": "Batas atas",
                }
            ),
            use_container_width=True,
        )
    else:
        st.caption("Belum ada data prediksi untuk ditampilkan.")

# -----------------------------------
# Simulasi "what-if" promo penjualan
# -----------------------------------
st.markdown("### Simulasi 'what-if' promo penjualan")

if df_forecast is None or df_forecast.empty:
    st.info("Belum ada data prediksi untuk simulasi.")
else:
    baseline_total = float(df_forecast["nilai"].sum())
    if not math.isfinite(baseline_total) or baseline_total == 0:
        st.info("Data prediksi belum cukup untuk simulasi (total penjualan = 0).")
    else:
        st.caption(
            "Geser persentase di bawah ini untuk mensimulasikan skenario promo "
            "atau perubahan permintaan. Nilai positif artinya permintaan naik, "
            "nilai negatif artinya turun."
        )
        perubahan_pct = st.slider(
            "Perubahan permintaan (%)",
            min_value=-50,
            max_value=50,
            value=0,
            step=1,
        )

        scenario_total = baseline_total * (1 + perubahan_pct / 100.0)
        delta = scenario_total - baseline_total

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total prediksi asli", f"{baseline_total:,.0f} unit")
        with col_b:
            st.metric(
                "Total skenario",
                f"{scenario_total:,.0f} unit",
                f"{perubahan_pct:+.0f}%",
            )
        with col_c:
            st.metric("Perubahan unit", f"{delta:,.0f} unit")
