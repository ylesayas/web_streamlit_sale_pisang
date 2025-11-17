# app.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# -----------------------------
# Configuration / Theme colors
# -----------------------------
ACCENT = "#FFCC4D"   # soft yellow/gold for highlights
BG = "#FFFFFF"       # white
CARD_BG = "#F6F7F9"  # light grey card background
LINE_COLOR = "#2B7AEE"  # soft blue for main lines

st.set_page_config(page_title="Sistem Prediksi Stok Pisang — Bungo Family",
                   layout="wide",
                   initial_sidebar_state="auto")

# Admin password (change before deploy if needed)
ADMIN_PASSWORD = "admin123"

# Data directory & server file path
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
FORECAST_PATH = DATA_DIR / "forecast.xlsx"  # file saved by admin upload
HIST_PATH = DATA_DIR / "historical.xlsx"    # optional historical actuals (admin can upload)

# -----------------------------
# Helper functions
# -----------------------------
def save_uploaded_file(uploaded_file, destination_path: Path):
    try:
        if uploaded_file.name.lower().endswith((".xlsx", ".xls")):
            with open(destination_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        else:
            # assume csv
            df = pd.read_csv(uploaded_file)
            df.to_excel(destination_path, index=False)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan file: {e}")
        return False

def load_forecast(path: Path):
    if not path.exists():
        return None
    try:
        df = pd.read_excel(path)
    except Exception:
        try:
            df = pd.read_csv(path)
        except Exception:
            st.error("File forecast tidak bisa dibaca. Format harus .xlsx atau .csv")
            return None
    # detect date column
    df_cols_lower = [c.lower() for c in df.columns]
    date_col = None
    for cand in ["date", "tanggal", "ds", "periode", "periode_date", "index"]:
        if cand in df_cols_lower:
            date_col = df.columns[df_cols_lower.index(cand)]
            break
    if date_col is None:
        # fallback to first column
        date_col = df.columns[0]
    # convert date
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except Exception:
        # try parsing by month-year if needed
        try:
            df[date_col] = pd.to_datetime(df[date_col].astype(str), errors='coerce')
        except:
            pass
    df = df.rename(columns={date_col: "date"})
    df = df.set_index("date").sort_index()
    # locate mean/prediction column
    col_map = {c: c for c in df.columns}
    for c in df.columns:
        cl = c.lower()
        if ("mean" in cl) or ("pred" in cl) or ("yhat" in cl) or ("forecast" in cl):
            col_map[c] = "mean"
        if ("lower" in cl) and ("ci" in cl or "conf" in cl or "lower" in cl):
            col_map[c] = "lower"
        if ("upper" in cl) and ("ci" in cl or "conf" in cl or "upper" in cl):
            col_map[c] = "upper"
    df = df.rename(columns=col_map)
    # ensure numeric
    if "mean" not in df.columns:
        numeric_cols = df.select_dtypes(include=np.number).columns
        if len(numeric_cols) > 0:
            df = df.rename(columns={numeric_cols[0]: "mean"})
    return df

def load_historical(path: Path):
    if not path.exists():
        return None
    try:
        df = pd.read_excel(path)
    except Exception:
        try:
            df = pd.read_csv(path)
        except Exception:
            return None
    # detect date & actual columns similar to forecast
    df_cols_lower = [c.lower() for c in df.columns]
    date_col = None
    for cand in ["date", "tanggal", "ds", "periode", "index"]:
        if cand in df_cols_lower:
            date_col = df.columns[df_cols_lower.index(cand)]
            break
    if date_col is None:
        date_col = df.columns[0]
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except:
        pass
    df = df.rename(columns={date_col: "date"})
    df = df.set_index("date").sort_index()
    # find actual column
    for c in df.columns:
        if ("jumlah" in c.lower()) or ("actual" in c.lower()) or ("sisir" in c.lower()) or ("y" == c.lower()):
            df = df.rename(columns={c: "actual"})
            break
    return df

def create_plot(forecast_df, historical_df=None, highlight_months=None):
    fig = go.Figure()
    # historical line
    if historical_df is not None and "actual" in historical_df.columns:
        fig.add_trace(go.Scatter(
            x=historical_df.index, y=historical_df["actual"],
            mode="lines+markers", name="Actual", line=dict(color="gray"), marker=dict(size=6)
        ))
    # forecast line
    fig.add_trace(go.Scatter(
        x=forecast_df.index, y=forecast_df["mean"],
        mode="lines+markers", name="Forecast", line=dict(color=LINE_COLOR, width=3), marker=dict(size=6)
    ))
    # confidence interval
    if "lower" in forecast_df.columns and "upper" in forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=list(forecast_df.index) + list(forecast_df.index[::-1]),
            y=list(forecast_df["upper"]) + list(forecast_df["lower"][::-1]),
            fill="toself", fillcolor="rgba(255,204,77,0.15)", line=dict(color="rgba(255,204,77,0)"),
            showlegend=True, name="Confidence Interval"
        ))
    # highlight months (e.g., Ramadan) as vertical shapes
    if highlight_months:
        shapes = []
        annotations = []
        for dt in forecast_df.index:
            if dt.month in highlight_months:
                shapes.append(dict(type="rect",
                                   x0=dt - pd.Timedelta(days=15), x1=dt + pd.Timedelta(days=15),
                                   y0=0, y1=max(forecast_df["mean"].max(), (historical_df["actual"].max() if historical_df is not None and "actual" in historical_df.columns else 0)) * 1.4,
                                   fillcolor="rgba(255,204,77,0.12)", line=dict(width=0)))
        if shapes:
            fig.update_layout(shapes=shapes)
    fig.update_layout(
        margin=dict(l=40, r=20, t=50, b=40),
        paper_bgcolor=BG, plot_bgcolor=BG,
        xaxis=dict(title="Periode", showgrid=True, rangeslider=dict(visible=True)),
        yaxis=dict(title="Jumlah Pisang (sisir)", showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def forecast_insights(forecast_df):
    # basic numeric summary and simple textual insights
    mean_vals = forecast_df["mean"].values
    avg = float(np.round(np.mean(mean_vals), 2))
    mx = int(np.max(mean_vals))
    mn = int(np.min(mean_vals))
    peak_idx = forecast_df["mean"].idxmax()
    try:
        peak_str = peak_idx.strftime("%B %Y")
    except:
        peak_str = str(peak_idx)
    # percent change next month vs current month
    if len(forecast_df) >= 2:
        cur = forecast_df["mean"].iloc[0]
        nxt = forecast_df["mean"].iloc[1]
        pct_next = float(np.round((nxt - cur) / max(1, cur) * 100, 2))
    else:
        pct_next = 0.0
    text_lines = [
        f"Rata-rata prediksi 12 bulan: {avg} sisir/bulan.",
        f"Perkiraan tertinggi: {mx} sisir pada {peak_str}. Perkiraan terendah: {mn} sisir.",
        f"Perubahan bulan terdekat → berikutnya: {pct_next}%."
    ]
    return "\n".join(text_lines)

def df_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=True, sheet_name="forecast")
        writer.save()
    return output.getvalue()

def compare_prev_year(forecast_df, historical_df=None):
    # compare average last year (if available) vs forecast average (next 12 months)
    result = {}
    forecast_avg = float(np.round(forecast_df["mean"].mean(),2))
    result["forecast_avg"] = forecast_avg
    # try historical df for last year's same months average
    if historical_df is not None and "actual" in historical_df.columns:
        try:
            last_year = sorted(list(set(historical_df.index.year)))[-1]
            hist_last_year = historical_df[historical_df.index.year == last_year]
            hist_avg = float(np.round(hist_last_year["actual"].mean(),2))
            result["historical_last_year_avg"] = hist_avg
            result["pct_diff"] = float(np.round((forecast_avg - hist_avg)/max(1, hist_avg)*100,2))
        except Exception:
            result["historical_last_year_avg"] = None
            result["pct_diff"] = None
    else:
        result["historical_last_year_avg"] = None
        result["pct_diff"] = None
    return result

# -----------------------------
# Sidebar & Role selection
# -----------------------------
st.sidebar.title("Pengaturan")
role = st.sidebar.radio("Masuk sebagai:", ("UMKM (Viewer)", "Admin (Upload)"))

st.markdown(f"<div style='background:{CARD_BG}; padding:12px; border-radius:8px'>"
            f"<h2 style='color:#222;'>Sistem Prediksi Stok Pisang — Bungo Family</h2>"
            f"<p style='color:#333; margin-top:-10px'>Dashboard visualisasi hasil peramalan SARIMA. UMKM hanya melihat. Admin dapat mengunggah file prediksi.</p>"
            "</div>", unsafe_allow_html=True)

# -----------------------------
# ADMIN PAGE
# -----------------------------
if role == "Admin (Upload)":
    st.header("🔐 Halaman Admin — Upload Hasil Prediksi")
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        pwd = st.text_input("Masukkan password admin:", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("Login berhasil. Anda dapat mengunggah file hasil prediksi.")
            else:
                st.error("Password salah. Silakan coba lagi.")
        st.stop()

    st.info("Upload file hasil prediksi (format .xlsx atau .csv). File ini akan disimpan di server aplikasi dan dipakai sebagai sumber data untuk halaman UMKM.")

    uploaded = st.file_uploader("Pilih file hasil prediksi (.xlsx/.csv)", type=["xlsx","csv"])
    if uploaded:
        ok = save_uploaded_file(uploaded, FORECAST_PATH)
        if ok:
            st.success(f"File berhasil diunggah sebagai `{FORECAST_PATH.name}`.")
            # preview
            df_preview = load_forecast(FORECAST_PATH)
            if df_preview is not None:
                st.subheader("Preview data yang diunggah")
                st.dataframe(df_preview.reset_index().head(50))
                st.download_button("⬇️ Download file forecast (server)", data=open(FORECAST_PATH, "rb"), file_name="forecast.xlsx")
    st.markdown("---")
    st.subheader("Upload Data Historis (opsional)")
    hist_file = st.file_uploader("File historical (opsional, beri nama historical.xlsx)", type=["xlsx","csv"], key="hist")
    if hist_file:
        ok2 = save_uploaded_file(hist_file, HIST_PATH)
        if ok2:
            st.success("Data historis berhasil diunggah.")
    st.markdown("---")
    st.write("Catatan:")
    st.write("- Ganti password admin dengan mengubah variabel ADMIN_PASSWORD di file app.py sebelum deploy jika ingin lebih aman.")
    st.stop()

# -----------------------------
# UMKM VIEWER PAGE
# -----------------------------
st.title("📊 Dashboard — UMKM Bungo Family")
st.markdown("Halaman ini menampilkan hasil prediksi yang diunggah oleh admin. UMKM HANYA MELIHAT. Jika belum ada, hubungi admin.")

# Load data
forecast_df = load_forecast(FORECAST_PATH)
historical_df = load_historical(HIST_PATH)

if forecast_df is None:
    st.warning("Belum ada file prediksi di server. Silakan hubungi admin untuk mengunggah file prediksi.")
    st.stop()

# Controls for viewer (simple)
st.sidebar.markdown("---")
st.sidebar.header("Pengaturan Tampilan (Viewer)")
# Ramadan months config (admin/viewer can set)
ramadan_input = st.sidebar.text_input("Bulan Ramadan (pisahkan koma, default: 4)", value="4")
try:
    highlight_months = [int(x.strip()) for x in ramadan_input.split(",") if x.strip().isdigit()]
except:
    highlight_months = [4]

# Thresholds for stock alerts
st.sidebar.markdown("---")
threshold = st.sidebar.number_input("Ambang stok aman (sisir)", value=200, step=1)
safety_pct = st.sidebar.number_input("Safety stock (%) untuk rekomendasi", value=10, step=1)

# Sidebar navigation
page = st.sidebar.selectbox("Menu", ["Dashboard Utama", "Grafik", "Tabel Prediksi", "Perbandingan Tahun", "Insight Tren", "Download", "Tentang"])

# Top metrics
col1, col2, col3, col4 = st.columns([1.2,1,1,1])
with col1:
    st.metric("Periode (baris prediksi)", value=len(forecast_df))
with col2:
    st.metric("Rata-rata (sisir/bln)", value=float(np.round(forecast_df["mean"].mean(),2)))
with col3:
    # show last forecast value
    lastv = int(round(forecast_df["mean"].iloc[0])) if len(forecast_df)>0 else "-"
    st.metric("Prediksi periode terdekat", value=f"{lastv} sisir")
with col4:
    st.metric("Theme", value="White / Grey / Yellow")

st.markdown("---")

# Page: Dashboard Utama
if page == "Dashboard Utama":
    st.subheader("Grafik utama: Actual vs Forecast (interactive)")
    fig_main = create_plot(forecast_df, historical_df, highlight_months)
    st.plotly_chart(fig_main, use_container_width=True)

    st.markdown("**Ringkasan singkat**")
    st.info(forecast_insights(forecast_df))

    # Stock alert (next period)
    st.subheader("Peringatan Stok & Rekomendasi")
    next_idx = forecast_df.index[0] if len(forecast_df)>0 else None
    if next_idx:
        next_val = int(round(forecast_df["mean"].iloc[0]))
        st.write(f"Periode terdekat: **{next_idx.strftime('%B %Y')}** — Prediksi **{next_val} sisir**")
        if next_val <= threshold:
            st.warning(f"⚠️ Risiko kekurangan stok! Prediksi {next_val} ≤ ambang {threshold}.")
            recommended = int(np.ceil(next_val * (1 + safety_pct/100)))
            st.info(f"Rekomendasi pembelian: **{recommended} sisir** (termasuk safety {safety_pct}%).")
        else:
            st.success("Stok diperkirakan cukup berdasarkan ambang yang ditentukan.")

# Page: Grafik
elif page == "Grafik":
    st.subheader("Grafik Interaktif (zoomable)")
    fig_zoom = create_plot(forecast_df, historical_df, highlight_months)
    fig_zoom.update_layout(title="Actual vs Forecast (gunakan range slider / zoom)", height=580)
    st.plotly_chart(fig_zoom, use_container_width=True)

# Page: Tabel Prediksi
elif page == "Tabel Prediksi":
    st.subheader("Tabel Hasil Prediksi (12 bulan)")
    st.dataframe(forecast_df.reset_index().rename(columns={'index':'date'}).head(300))

# Page: Perbandingan Tahun
elif page == "Perbandingan Tahun":
    st.subheader("Perbandingan Tahun Sebelumnya vs Rata-rata Prediksi")
    comp = compare_prev_year(forecast_df, historical_df)
    st.write(f"- Rata-rata prediksi 12 bln: **{comp['forecast_avg']} sisir/bln**")
    if comp.get("historical_last_year_avg") is not None:
        st.write(f"- Rata-rata aktual tahun terakhir: **{comp['historical_last_year_avg']} sisir/bln**")
        st.write(f"- Perbedaan: **{comp['pct_diff']}%**")
    else:
        st.info("Data historis tidak tersedia untuk perbandingan. Admin dapat upload `historical.xlsx` jika ingin perbandingan otomatis.")

# Page: Insight Tren
elif page == "Insight Tren":
    st.subheader("Insight Otomatis & Penjelasan Sederhana")
    st.write("Penjelasan singkat (bahasa gampang untuk UMKM):")
    st.markdown(f"- {forecast_insights(forecast_df)}")
    st.markdown("- **Kenapa angka ini penting?** Karena membantu merencanakan pembelian pisang agar produksi tidak terganggu.")
    st.markdown("- **Catatan praktis:** Jika prediksi melebihi ambang stok, persiapkan pesanan lebih awal.")

# Page: Download
elif page == "Download":
    st.subheader("Unduh Hasil Prediksi")
    csv_bytes = forecast_df.to_csv(index=True).encode("utf-8")
    st.download_button("⬇️ Download sebagai CSV", data=csv_bytes, file_name="prediksi_sarima.csv", mime="text/csv")
    excel_bytes = df_to_excel_bytes(forecast_df)
    st.download_button("⬇️ Download sebagai Excel", data=excel_bytes, file_name="prediksi_sarima.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Page: Tentang
elif page == "Tentang":
    st.subheader("Tentang Sistem")
    st.markdown("""
    **Nama Sistem:** Sistem Prediksi Stok Pisang — Bungo Family  
    **Tujuan:** Menyediakan visualisasi hasil peramalan SARIMA untuk membantu UMKM merencanakan pembelian bahan baku.  
    **Catatan:** Pemodelan SARIMA dilakukan secara terpisah (Google Colab). Web ini bersifat *display-only*.  
    """)
    st.markdown("**Cara update data:** Admin upload file hasil prediksi (admin panel). Jika admin berhenti, pemilik UMKM dapat menunjuk orang lain untuk upload file.")

st.markdown("---")
# UAT simple
st.subheader("Form UAT (untuk dokumentasi pengujian)")
with st.form("uat_form"):
    name = st.text_input("Nama penguji (mis: Oom Budi)")
    ease = st.slider("Kemudahan penggunaan (1=Sulit,5=Mudah)", 1,5,4)
    clarity = st.slider("Kejelasan informasi (1=Buram,5=Jelas)",1,5,4)
    useful = st.slider("Kegunaan rekomendasi pembelian (1=Tidak,5=Sangat)",1,5,4)
    notes = st.text_area("Komentar / saran")
    submitted = st.form_submit_button("Kirim & Download bukti UAT")
if submitted:
    uat_df = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name, "ease": ease, "clarity": clarity, "useful": useful, "notes": notes
    }])
    st.success("Terima kasih, hasil UAT sudah tercatat. Silakan download.")
    st.download_button("⬇️ Download Hasil UAT (CSV)", data=uat_df.to_csv(index=False).encode("utf-8"),
                       file_name=f"uat_{name or 'responden'}.csv", mime="text/csv")

# Footer
st.markdown("<div style='text-align:center; color:#666; font-size:12px; margin-top:12px'>"
            "Dibangun menggunakan Streamlit • Hasil prediksi SARIMA diproses terpisah di Google Colab</div>",
            unsafe_allow_html=True)
