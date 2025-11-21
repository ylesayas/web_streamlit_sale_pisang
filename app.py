import math
from pathlib import Path
from io import BytesIO
import re
from datetime import datetime

import pandas as pd
import streamlit as st

# Optional: Altair untuk grafik (sudah ikut di Streamlit)
import altair as alt

import math
from pathlib import Path
from io import BytesIO
import re
from datetime import datetime

import pandas as pd
import streamlit as st

# Optional: Altair untuk grafik (sudah ikut di Streamlit)
import altair as alt

# ==========================
# SISTEM PIN (UMKM + ADMIN)
# ==========================
PIN_UMKM = "5454"
PIN_ADMIN = "0708"

if "auth" not in st.session_state:
    st.session_state.auth = None  # None / "umkm" / "admin"

def login_screen():
    st.title("🔐 Halaman Masuk")
    st.write("Masukkan kode akses untuk membuka dashboard.")
    pin = st.text_input("Kode PIN", type="password")

    if st.button("Masuk"):
        if pin == PIN_UMKM:
            st.session_state.auth = "umkm"
            st.rerun()
        elif pin == PIN_ADMIN:
            st.session_state.auth = "admin"
            st.rerun()
        else:
            st.error("PIN salah. Coba lagi.")

# Kalau belum login, tampilkan layar PIN dulu
if st.session_state.auth is None:
    login_screen()
    st.stop()

# Penanda mode
MODE_ADMIN = st.session_state.auth == "admin"
MODE_UMKM = st.session_state.auth == "umkm"

# -----------------------------
# Konfigurasi halaman
# -----------------------------
st.set_page_config(
    page_title="Dashboard Penjualan Pisang",
    page_icon="🍌",
    layout="wide",
)


# -----------------------------
# Konfigurasi halaman
# -----------------------------
st.set_page_config(
    page_title="Dashboard Penjualan Pisang",
    page_icon="🍌",
    layout="wide",
)

# -----------------------------
# Load CSS eksternal
# -----------------------------
def load_local_css(file_name: str = "theme.css") -> None:
    try:
        css_path = Path(__file__).parent / file_name
        with css_path.open() as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Kalau CSS belum ada, biarkan saja (app tetap jalan)
        pass

load_local_css()

# -----------------------------
# Helper: Nama bulan Indonesia
# -----------------------------
ID_MONTHS = {
    "januari": 1, "jan": 1, "jan.": 1,
    "februari": 2, "feb": 2, "feb.": 2,
    "maret": 3, "mar": 3, "mar.": 3,
    "april": 4, "apr": 4, "apr.": 4,
    "mei": 5,
    "juni": 6, "jun": 6, "jun.": 6,
    "juli": 7, "jul": 7, "jul.": 7,
    "agustus": 8, "agu": 8, "agu.": 8, "aug": 8, "aug.": 8,
    "september": 9, "sept": 9, "sept.": 9, "sep": 9, "sep.": 9,
    "oktober": 10, "okt": 10, "okt.": 10, "oct": 10, "oct.": 10,
    "november": 11, "nov": 11, "nov.": 11,
    "desember": 12, "des": 12, "des.": 12, "dec": 12, "dec.": 12,
}

ID_MONTH_NAMES = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}

def month_name_id(month_num: int) -> str:
    return ID_MONTH_NAMES.get(int(month_num), str(month_num))


# -----------------------------
# UNIVERSAL EXCEL PARSER
# -----------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, hilangkan spasi berlebih, dsb."""
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
    """Mencari kolom tanggal langsung (datetime atau string yang bisa di-parse)."""
    # 1) Kolom yang sudah datetime
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if df[col].notna().sum() >= max(3, len(df) * 0.5):
                return col, df[col]

    # 2) Kolom dengan kata kunci tanggal/periode
    date_keywords = [
        "tanggal", "tgl", "date", "waktu", "period",
        "periode", "bulan_tahun", "bulan-thn", "bulan-tahun",
    ]
    for col in df.columns:
        if any(k in col for k in date_keywords):
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            if parsed.notna().sum() >= max(3, len(df) * 0.5):
                return col, parsed

    return None, None


def detect_year_month(df: pd.DataFrame):
    """Mencari kolom tahun & bulan terpisah."""
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

    # Parse tahun jadi angka
    y = pd.to_numeric(years, errors="coerce")

    # Kalau banyak tahun < 100, anggap 2000+ (misal 24 -> 2024)
    if (y < 100).sum() > 0 and (y < 100).sum() >= len(y) * 0.5:
        y = y.apply(lambda v: 2000 + v if pd.notna(v) else v)

    # Parse bulan (angka atau teks Indonesia)
    m = pd.to_numeric(months_raw, errors="coerce")

    mask = m.isna() & months_raw.notna()
    if mask.any():
        def map_month(x):
            if pd.isna(x):
                return math.nan
            s = str(x).strip().lower()
            s2 = re.sub(r"[^\w]+$", "", s)  # buang titik/koma di belakang
            return ID_MONTHS.get(s2, math.nan)

        m2 = months_raw[mask].map(map_month)
        m[mask] = m2

    dates = pd.to_datetime(
        {"year": y, "month": m, "day": 1},
        errors="coerce",
    )
    return dates


def parse_sales_excel_from_df(df_raw: pd.DataFrame):
    """
    Parser universal:
    - Deteksi otomatis kolom tanggal / bulan-tahun (termasuk bulan Indonesia).
    - Hasil akhir: dataframe rapi dengan kolom:
      [tanggal, jenis (Aktual/Prediksi), sumber, nilai, lower, upper]
    """
    df = normalize_columns(df_raw)

    # 1) Cari kolom tanggal langsung
    date_col, date_series = detect_date_column(df)

    # 2) Kalau belum ketemu, coba kombinasikan tahun + bulan
    if date_series is None:
        year_col, month_col = detect_year_month(df)
        if year_col and month_col:
            dates = parse_year_month_to_date(df, year_col, month_col)
            date_series = dates
            date_col = "tanggal"
        else:
            # 3) Terakhir, coba semua kolom string yang bisa di-parse ke tanggal
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
                    "Pastikan ada kolom tanggal, atau kolom bulan & tahun."
                )

    # 3) Bersihkan dan sort berdasarkan tanggal
    df_base = df.copy()
    df_base["tanggal"] = pd.to_datetime(date_series, errors="coerce")
    df_base = df_base[df_base["tanggal"].notna()].copy()
    df_base = df_base.sort_values("tanggal")

    # 4) Deteksi kolom numerik yang relevan
    numeric_cols = [
        c
        for c in df_base.columns
        if c not in ["tanggal", date_col]
        and pd.api.types.is_numeric_dtype(df_base[c])
    ]

    # Kolom prediksi (mean, forecast, prediksi)
    forecast_mean_cols = [
        c
        for c in numeric_cols
        if any(k in c for k in ["mean", "forecast", "prediksi"])
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

    # Kolom penjualan aktual
    actual_keywords = [
        "actual", "aktual", "realisasi", "penjualan", "sales",
        "qty", "jumlah", "volume", "unit",
    ]
    actual_cols = [
        c
        for c in numeric_cols
        if any(k in c for k in actual_keywords)
    ]

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

        # Cocokkan lower/upper jika ada
        lower_col = None
        upper_col = None
        if lower_cols:
            lower_col = lower_cols[0]
        if upper_cols:
            upper_col = upper_cols[0]

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

    # Fallback: kalau belum ada sama sekali, ambil kolom numerik pertama sebagai "Aktual"
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
    """
    Wrapper yang bisa dipakai untuk:
    - path string / Path
    - atau file-like (BytesIO) dari st.file_uploader
    """
    if isinstance(file_path_or_buffer, (str, Path)):
        df_raw = pd.read_excel(file_path_or_buffer, engine="openpyxl")
    else:
        df_raw = pd.read_excel(file_path_or_buffer, engine="openpyxl")

    return parse_sales_excel_from_df(df_raw)


# -----------------------------
# Analisis ringkas otomatis
# -----------------------------
def build_summary(tidy: pd.DataFrame) -> str:
    if tidy.empty:
        return "Data tidak ditemukan di file Excel."

    df_a = tidy[tidy["jenis"] == "Aktual"].copy()
    df_p = tidy[tidy["jenis"] == "Prediksi"].copy()

    lines = []

    # --- Ringkasan data aktual ---
    if not df_a.empty:
        g = df_a.groupby("tanggal")["nilai"].mean().sort_index()
        first_date = g.index[0]
        last_date = g.index[-1]
        first_val = g.iloc[0]
        last_val = g.iloc[-1]

        if len(g) >= 13:
            recent = g.iloc[-12:].mean()
            prev = (
                g.iloc[-24:-12].mean()
                if len(g) >= 24
                else g.iloc[:-12].mean()
            )
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

    # --- Ringkasan data prediksi ---
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


# -----------------------------
# Tandai bulan Ramadhan (perkiraan)
# -----------------------------
def add_ramadhan_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menandai bulan Ramadhan secara sederhana:
    - diasumsikan sekitar bulan Maret–April.
    Ini hanya highlight visual, bukan perhitungan kalender hijriah yang presisi.
    """
    df = df.copy()
    df["is_ramadhan"] = df["tanggal"].dt.month.isin([3, 4])
    return df


# -----------------------------
# Grafik utama (historis + forecast)
# -----------------------------
def create_main_chart(tidy: pd.DataFrame):
    if tidy.empty:
        return None

    df = add_ramadhan_flag(tidy)

    base = alt.Chart(df).encode(
        x=alt.X("tanggal:T", title="Tanggal"),
    )

    # Warna & style
    color_actual = "#1976D2"   # biru
    color_forecast = "#F9A825" # kuning pisang
    color_ramadhan = "#FFB300" # oranye-kuning

    # Band confidence interval untuk prediksi
    band = (
        base.transform_filter(alt.datum.jenis == "Prediksi")
        .mark_area(opacity=0.15)
        .encode(
            y=alt.Y("lower:Q", title="Penjualan"),
            y2="upper:Q",
            color=alt.value(color_forecast),
        )
    )

    # Garis aktual
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

    # Garis prediksi
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

    # Titik highlight Ramadhan
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

    chart = alt.layer(band, line_actual, line_pred, ramadhan_points).resolve_scale(
        y="shared"
    )

    return chart.properties(height=420)


# -----------------------------
# Grafik Year-over-Year
# -----------------------------
def create_yoy_chart(df_actual: pd.DataFrame):
    if df_actual is None or df_actual.empty:
        return None

    df = df_actual.copy()
    df["tahun"] = df["tanggal"].dt.year.astype(str)
    df["bulan"] = df["tanggal"].dt.month
    df["bulan_nama"] = df["bulan"].apply(month_name_id)

    # Hitung rata-rata per bulan per tahun
    agg = (
        df.groupby(["tahun", "bulan", "bulan_nama"])["nilai"]
        .mean()
        .reset_index()
        .sort_values(["tahun", "bulan"])
    )

    if agg["tahun"].nunique() <= 1:
        # Tidak cukup tahun untuk perbandingan
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


# -----------------------------
# Sidebar: Pengaturan tampilan
# -----------------------------
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan Tampilan")
    font_size = st.slider(
        "Ukuran teks (lebih besar untuk orang tua)",
        min_value=14,
        max_value=24,
        value=18,
        step=1,
    )
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

    st.markdown("### 📂 Sumber Data")
    st.caption(
        "Data penjualan & prediksi otomatis diambil dari file Excel "
        "di dalam sistem. UMKM tidak perlu upload file apa pun."
    )

# -----------------------------
# Header: Logo + Judul
# -----------------------------
st.markdown(
    """
    <div class="header-banana">
      <div class="header-left">
        <div class="logo-circle">🍌</div>
        <div class="title-block">
          <h1>Dashboard Penjualan Pisang</h1>
          <p>Melihat tren penjualan & prediksi 12 bulan ke depan untuk UMKM</p>
        </div>
      </div>
      <div class="header-right">
        <div class="tag-pill">Untuk UMKM</div>
        <div class="tag-pill secondary">Mudah dibaca orang tua</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# -----------------------------
# Load data dari file di repo
# -----------------------------
@st.cache_data(show_spinner=True)
def load_data():
    excel_path = Path(__file__).parent / "hasil_prediksi_sarima.xlsx"
    tidy, df_actual, df_forecast = parse_sales_excel(excel_path)
    return tidy, df_actual, df_forecast

try:
    tidy, df_actual, df_forecast = load_data()
except Exception as e:
    st.error(
        "Terjadi masalah saat membaca file Excel bawaan. "
        "Silakan periksa struktur file di repo.\n\n"
        f"Detail: {e}"
    )
    st.stop()

# -----------------------------
# Ringkasan angka utama
# -----------------------------
summary_text = build_summary(tidy)

col1, col2, col3 = st.columns(3)

with col1:
    total_points = tidy["tanggal"].nunique()
    st.metric(label="Jumlah periode dalam data", value=f"{total_points} bulan")

with col2:
    if not df_actual.empty:
        last_actual = (
            df_actual.sort_values("tanggal")
            .groupby("tanggal")["nilai"]
            .mean()
            .iloc[-1]
        )
        st.metric(label="Penjualan aktual terbaru", value=f"{last_actual:,.0f}")
    else:
        st.metric(
            label="Penjualan aktual terbaru",
            value="—",
            delta="Data aktual belum tersedia",
        )

with col3:
    if not df_forecast.empty:
        first_forecast = (
            df_forecast.sort_values("tanggal")
            .groupby("tanggal")["nilai"]
            .mean()
            .iloc[0]
        )
        st.metric(label="Prediksi awal periode", value=f"{first_forecast:,.0f}")
    else:
        st.metric(label="Prediksi awal periode", value="—")

# -----------------------------
# Info "Aktual vs Prediksi"
# -----------------------------
st.info(
    """
    **Keterangan grafik:**

    - Garis **biru tebal** = data penjualan **aktual** (riwayat).
    - Garis **kuning putus-putus** = data **prediksi** 12 bulan ke depan.
    - Area kuning transparan = batas bawah/atas prediksi.
    - Titik **berlian** menandai bulan-bulan yang berada di sekitar **Ramadhan (perkiraan)**.
    """
)

# -----------------------------
# Layout utama: grafik & tabel
# -----------------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Tren penjualan & prediksi 12 bulan")
    main_chart = create_main_chart(tidy)
    if main_chart is not None:
        st.altair_chart(main_chart, use_container_width=True)
    else:
        st.warning("Belum ada data untuk ditampilkan di grafik.")

    if not df_actual.empty:
        st.subheader("Perbandingan tahun ke tahun (Year-over-Year)")
        yoy_chart = create_yoy_chart(df_actual)
        if yoy_chart is not None:
            st.altair_chart(yoy_chart, use_container_width=True)
        else:
            st.caption(
                "Perbandingan tahun ke tahun akan muncul jika data mencakup "
                "lebih dari satu tahun kalender."
            )

with right_col:
    st.subheader("Analisis singkat otomatis")
    st.markdown(f"<div class='analysis-box'>{summary_text}</div>", unsafe_allow_html=True)

    st.subheader("Unduh data & laporan")
    # Download data gabungan
    csv_buffer = tidy.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download data (CSV)",
        data=csv_buffer,
        file_name="data_penjualan_pisang.csv",
        mime="text/csv",
    )

    # Download ringkasan TXT sederhana
    txt_buffer = summary_text.encode("utf-8")
    st.download_button(
        label="📄 Download ringkasan (TXT)",
        data=txt_buffer,
        file_name="ringkasan_penjualan_pisang.txt",
        mime="text/plain",
    )

# -----------------------------
# Tabel data sederhana
# -----------------------------
with st.expander("Lihat data dalam bentuk tabel (opsional)"):
    st.dataframe(
        tidy[["tanggal", "jenis", "nilai", "lower", "upper"]]
        .sort_values(["tanggal", "jenis"])
        .rename(
            columns={
                "tanggal": "Tanggal",
                "jenis": "Jenis",
                "nilai": "Nilai",
                "lower": "Batas bawah",
                "upper": "Batas atas",
            }
        ),
        use_container_width=True,
    )

# -----------------------------
# Mode admin: upload file lain (opsional)
# -----------------------------
with st.expander("Mode admin (opsional) – coba file Excel lain"):
    st.caption(
        "Bagian ini untuk pemilik usaha atau admin yang ingin menguji file Excel lain. "
        "UMKM pengguna utama tidak perlu memakai fitur ini."
    )
    uploaded = st.file_uploader(
        "Upload file Excel baru (opsional)",
        type=["xlsx", "xls"],
    )
    if uploaded is not None:
        try:
            tidy_new, act_new, pred_new = parse_sales_excel(uploaded)
            st.success("File berhasil dibaca dengan parser universal.")
            st.dataframe(
                tidy_new.head(50),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
