import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import os
import urllib.request
import urllib.parse
import json
import base64
import re

# ====================================================
# 1. Page Configuration & Enhanced Custom CSS
# ====================================================
st.set_page_config(
    page_title="공모과제 예산 & 지출 통합관리 시스템",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

    html, body, [class*="st-"], [class*="css"] {
        font-family: 'Pretendard', 'Noto Sans KR', -apple-system, sans-serif;
    }

    [data-testid="stIconMaterial"],
    span[data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-symbols-outlined,
    [class*="material-symbols"] {
        font-family: 'Material Symbols Rounded' !important;
    }

    .header-banner {
        background: linear-gradient(120deg, #1B365D 0%, #2C5282 55%, #0F766E 100%);
        padding: 22px 28px;
        border-radius: 14px;
        color: #FFFFFF;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(27, 54, 93, 0.25);
    }
    .header-banner .hb-title { font-size: 23px; font-weight: 800; margin: 0; letter-spacing: -0.3px; }
    .header-banner .hb-sub { font-size: 13px; opacity: 0.85; margin-top: 6px; }
    .header-banner .hb-badge {
        display: inline-block; background: rgba(255,255,255,0.18);
        border-radius: 20px; padding: 3px 12px; font-size: 12px;
        font-weight: 600; margin-right: 6px; backdrop-filter: blur(4px);
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid var(--mc-color, #1B365D);
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        transition: all 0.18s ease;
        margin-bottom: 10px;
    }
    .metric-card:hover { box-shadow: 0 8px 20px rgba(15, 23, 42, 0.13); transform: translateY(-2px); }
    .metric-card .mc-icon { font-size: 17px; }
    .metric-card .mc-label { font-size: 12px; color: #64748B; font-weight: 700; margin-left: 4px; }
    .metric-card .mc-value { font-size: 21px; font-weight: 800; color: #0F172A; margin-top: 6px; letter-spacing: -0.4px; }
    .metric-card .mc-sub { font-size: 11px; color: #94A3B8; margin-top: 3px; }

    .side-summary {
        background: linear-gradient(135deg, #F0F9FF 0%, #F0FDFA 100%);
        border: 1px solid #BAE6FD;
        border-radius: 12px;
        padding: 14px 16px;
        font-size: 12.5px;
        color: #334155;
        line-height: 1.9;
    }
    .side-summary b { color: #0F172A; }
    .side-summary .bar-track { background: #E2E8F0; border-radius: 8px; height: 9px; margin: 6px 0 4px 0; overflow: hidden; }
    .side-summary .bar-fill { height: 100%; border-radius: 8px; transition: width 0.4s; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        height: 40px; white-space: nowrap;
        background-color: #F1F5F9; border-radius: 8px;
        color: #334155; font-weight: 600; padding: 0 14px;
        font-size: 13.5px;
        transition: all 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover { background-color: #E2E8F0; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(120deg, #1B365D, #2C5282) !important;
        color: white !important;
        box-shadow: 0 2px 6px rgba(27,54,93,0.3);
    }

    section[data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    section[data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
        height: 32px; padding: 0 9px; font-size: 12px; white-space: nowrap;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] { font-size: 13px; }

    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
        border-radius: 9px; font-weight: 700; transition: all 0.15s;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(15,23,42,0.15);
    }

    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] { border-radius: 10px; overflow: hidden; }
    div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #E2E8F0; }
    div[data-testid="stMetricValue"] { font-size: 22px; font-weight: 700; color: #1E293B; }

    .sec-title {
        font-size: 16px; font-weight: 800; color: #1B365D;
        border-left: 4px solid #0F766E; padding-left: 10px;
        margin: 4px 0 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================
# 2. Visual Helper Functions & 차년도 기간 정의
# ====================================================

YEAR_PERIODS = {
    1: "2025. 6. ~ 2026. 2.",
    2: "2026. 3. ~ 2027. 2.",
    3: "2027. 3. ~ 2028. 2.",
    4: "2028. 3. ~ 2029. 2.",
    5: "2029. 3. ~ 2030. 2.",
}

def year_label(n):
    try:
        n = int(n)
    except Exception:
        return str(n)
    period = YEAR_PERIODS.get(n, "")
    return f"{n}차년도 ({period})" if period else f"{n}차년도"

def normalize_anchor_text(s):
    if pd.isna(s): return s
    return str(s).replace("RISE", "앵커")

LOGO_HTML = """
<div style="display:flex; align-items:center; gap:10px; margin-bottom:2px;">
  <svg width="44" height="44" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="2" width="44" height="44" rx="11" fill="url(#g1)"/>
    <rect x="11" y="24" width="6" height="13" rx="2" fill="#FFFFFF" opacity="0.95"/>
    <rect x="21" y="17" width="6" height="20" rx="2" fill="#7DD3FC"/>
    <rect x="31" y="10" width="6" height="27" rx="2" fill="#5EEAD4"/>
    <defs>
      <linearGradient id="g1" x1="0" y1="0" x2="48" y2="48">
        <stop stop-color="#1B365D"/><stop offset="1" stop-color="#0F766E"/>
      </linearGradient>
    </defs>
  </svg>
  <div>
    <div style="font-size:16px; font-weight:800; color:#1B365D; line-height:1.2;">예산 &middot; 성과 통합관리</div>
    <div style="font-size:11px; color:#64748B;">앵커 공모과제 실시간 관리 시스템</div>
  </div>
</div>
"""

def won(x):
    try: return f"₩{int(x):,}"
    except Exception: return "₩0"

def metric_card(icon, label, value, sub="", color="#1B365D"):
    return (
        f'<div class="metric-card" style="--mc-color:{color}">'
        f'<span class="mc-icon">{icon}</span><span class="mc-label">{label}</span>'
        f'<div class="mc-value">{value}</div>'
        f'<div class="mc-sub">{sub}</div></div>'
    )

def render_metric_row(cards):
    cols = st.columns(len(cards))
    for col, html in zip(cols, cards):
        with col: st.markdown(html, unsafe_allow_html=True)

def rate_color(rate):
    if rate > 100: return "#E74C3C"
    elif rate >= 85: return "#F1C40F"
    return "#0F766E"

def render_separated_budget_status(alloc, carry, alloc_spent, carry_spent):
    tot_budget = alloc + carry
    tot_spent = alloc_spent + carry_spent
    tot_bal = tot_budget - tot_spent
    tot_rate = (tot_spent / tot_budget * 100) if tot_budget > 0 else 0.0

    alloc_bal = alloc - alloc_spent
    alloc_rate = (alloc_spent / alloc * 100) if alloc > 0 else 0.0

    carry_bal = carry - carry_spent
    carry_rate = (carry_spent / carry * 100) if carry > 0 else 0.0

    def r_col(r): return "#E74C3C" if r > 100 else ("#F1C40F" if r >= 85 else "#0F766E")

    html = f"""
    <div style="display:flex; gap:12px; margin-bottom:15px; flex-wrap:wrap;">
        <div style="flex:1; min-width:220px; background:#F8FAFC; padding:16px; border-radius:12px; border:1px solid #E2E8F0;">
            <div style="font-size:14px; font-weight:800; color:#1E293B; margin-bottom:12px; display:flex; align-items:center; gap:6px;"><span style="font-size:18px;">🔹</span> 당해 배정액 현황</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; color:#475569;"><span>배정 예산</span><b style="font-size:14px;">{won(alloc)}</b></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; color:#475569;"><span>지출 금액</span><b style="color:#0F766E; font-size:14px;">{won(alloc_spent)}</b></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:13px; color:#475569;"><span>예산 잔액</span><b style="color:{'#E74C3C' if alloc_bal < 0 else '#1E293B'}; font-size:14px;">{won(alloc_bal)}</b></div>
            <div style="height:6px; width:100%; background:#E2E8F0; border-radius:3px; overflow:hidden;"><div style="height:100%; width:{min(alloc_rate, 100)}%; background:{r_col(alloc_rate)};"></div></div>
            <div style="text-align:right; font-size:11px; color:#64748B; margin-top:6px;">집행률 <b>{alloc_rate:.1f}%</b></div>
        </div>
        <div style="flex:1; min-width:220px; background:#F8FAFC; padding:16px; border-radius:12px; border:1px solid #E2E8F0;">
            <div style="font-size:14px; font-weight:800; color:#1E293B; margin-bottom:12px; display:flex; align-items:center; gap:6px;"><span style="font-size:18px;">🔸</span> 전년 이월금 현황</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; color:#475569;"><span>이월 예산</span><b style="font-size:14px;">{won(carry)}</b></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; color:#475569;"><span>지출 금액</span><b style="color:#0F766E; font-size:14px;">{won(carry_spent)}</b></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:13px; color:#475569;"><span>예산 잔액</span><b style="color:{'#E74C3C' if carry_bal < 0 else '#1E293B'}; font-size:14px;">{won(carry_bal)}</b></div>
            <div style="height:6px; width:100%; background:#E2E8F0; border-radius:3px; overflow:hidden;"><div style="height:100%; width:{min(carry_rate, 100)}%; background:{r_col(carry_rate)};"></div></div>
            <div style="text-align:right; font-size:11px; color:#64748B; margin-top:6px;">집행률 <b>{carry_rate:.1f}%</b></div>
        </div>
        <div style="flex:1; min-width:220px; background:#F0F9FF; padding:16px; border-radius:12px; border:1px solid #BAE6FD;">
            <div style="font-size:14px; font-weight:800; color:#0369A1; margin-bottom:12px; display:flex; align-items:center; gap:6px;"><span style="font-size:18px;">📊</span> 총 통합 현황</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; color:#0C4A6E;"><span>총 가용예산</span><b style="font-size:14px;">{won(tot_budget)}</b></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; color:#0C4A6E;"><span>총 지출금액</span><b style="font-size:14px;">{won(tot_spent)}</b></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:13px; color:#0C4A6E;"><span>총 남은잔액</span><b style="color:{'#E74C3C' if tot_bal < 0 else '#0284C7'}; font-size:14px;">{won(tot_bal)}</b></div>
            <div style="height:6px; width:100%; background:#BFDBFE; border-radius:3px; overflow:hidden;"><div style="height:100%; width:{min(tot_rate, 100)}%; background:{r_col(tot_rate)};"></div></div>
            <div style="text-align:right; font-size:11px; color:#0284C7; margin-top:6px;">통합 집행률 <b>{tot_rate:.1f}%</b></div>
        </div>
    </div>
    """
    return html.replace('\n', '')

def make_gauge(rate, title="집행률"):
    color = rate_color(rate)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(rate, 1),
        number={"suffix": "%", "font": {"size": 30, "family": "Pretendard"}},
        title={"text": title, "font": {"size": 14, "color": "#475569"}},
        gauge={
            "axis": {"range": [0, max(120, rate + 10)], "tickfont": {"size": 10}},
            "bar": {"color": color, "thickness": 0.75},
            "bgcolor": "#F1F5F9",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 85], "color": "#F0FDFA"},
                {"range": [85, 100], "color": "#FEFCE8"},
                {"range": [100, max(120, rate + 10)], "color": "#FEF2F2"},
            ],
            "threshold": {"line": {"color": "#E74C3C", "width": 3}, "thickness": 0.8, "value": 100},
        }
    ))
    fig.update_layout(height=230, margin=dict(l=25, r=25, t=42, b=8), paper_bgcolor="rgba(0,0,0,0)")
    return fig

def style_fig(fig, h=380, showlegend=True):
    fig.update_layout(
        height=h,
        margin=dict(l=10, r=10, t=36, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Pretendard, Noto Sans KR, sans-serif", size=12),
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(font_family="Pretendard, Noto Sans KR, sans-serif"),
    )
    fig.update_xaxes(gridcolor="#F1F5F9")
    fig.update_yaxes(gridcolor="#F1F5F9")
    return fig

UNIT_COLOR_SEQ = px.colors.qualitative.Vivid + px.colors.qualitative.Bold + px.colors.qualitative.Set2

# ====================================================
# 3. Data Cleaning & Migration
# ====================================================
def safe_get_columns(df, required_cols, default_values=None):
    if df is None or not isinstance(df, pd.DataFrame):
        df = pd.DataFrame()
    df = df.copy()
    if default_values is None: default_values = {}
    for col in required_cols:
        if col not in df.columns:
            def_val = default_values.get(col, 0 if ("예산액" in col or "이월금" in col or "지출액" in col or col == "No") else "")
            df[col] = def_val
    return df[required_cols]

def ensure_business_tag(df, default_business_name, required_cols):
    if df is None or not isinstance(df, pd.DataFrame):
        df = pd.DataFrame()
    df = df.copy()
    if "사업명" not in df.columns:
        df["사업명"] = default_business_name
    else:
        df["사업명"] = df["사업명"].fillna(default_business_name).astype(str).str.strip()
        df["사업명"] = np.where(df["사업명"] == "", default_business_name, df["사업명"])
    df["사업명"] = df["사업명"].map(normalize_anchor_text)
    cols = ["사업명"] + [c for c in required_cols if c != "사업명"]
    return safe_get_columns(df, cols)

def clean_businesses(df):
    default_b = [
        {"사업코드": "4-3", "사업명": "앵커 사업단 (광주형 미래라이프)", "총괄책임자": "", "사업기간": "2025. 6. ~ 2030. 2.", "비고": "메인 사업"},
        {"사업코드": "4-1", "사업명": "Glocal 인재양성 사업 (FSU/GSU)", "총괄책임자": "", "사업기간": "2025. 6. ~ 2030. 2.", "비고": "글로벌 역량 강화 사업"}
    ]
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(default_b)
    df = df.copy()
    expected_cols = ["사업코드", "사업명", "총괄책임자", "사업기간", "비고"]
    df = safe_get_columns(df, expected_cols)

    df["사업코드"] = df["사업코드"].fillna("").astype(str).str.strip()
    df["사업명"] = df["사업명"].fillna("").astype(str).str.strip().map(normalize_anchor_text)
    df["총괄책임자"] = df["총괄책임자"].fillna("").astype(str).str.strip()
    df["사업기간"] = df["사업기간"].fillna("").astype(str).str.strip()
    df["비고"] = df["비고"].fillna("").astype(str).str.strip()

    df = df[df["사업명"] != ""].reset_index(drop=True)
    if df.empty: return pd.DataFrame(default_b)
    return df[expected_cols]

def clean_budget_projects(df, default_b_name):
    expected_cols = ["사업명", "과제코드", "과제/사업단명", "책임자"]
    for i in range(1, 6):
        expected_cols.extend([f"배정예산액_{i}차", f"이월금_{i}차"])
    expected_cols.append("비고")
    
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        df = pd.DataFrame([
            {"사업명": default_b_name, "과제코드": "4-3-0", "과제/사업단명": "사업단 본과제 (4-3 광주형 미래라이프)", "책임자": "", "배정예산액_1차": 140000000, "비고": "본과제"},
            {"사업명": "Glocal 인재양성 사업 (FSU/GSU)", "과제코드": "4-1-1", "과제/사업단명": "FSU 글로벌 현장실습 프로젝트", "책임자": "", "배정예산액_1차": 50000000, "비고": "글로벌 학점 인정"},
        ])
    
    df = df.copy()
    if "배정예산액" in df.columns and "배정예산액_1차" not in df.columns:
        df["배정예산액_1차"] = df["배정예산액"]
        
    df = ensure_business_tag(df, default_b_name, expected_cols)
    
    df["과제코드"] = df["과제코드"].fillna("").astype(str).str.strip()
    df["과제/사업단명"] = df["과제/사업단명"].fillna("").astype(str).str.strip().map(normalize_anchor_text)
    df["책임자"] = df["책임자"].fillna("").astype(str).str.strip()
    
    for c in expected_cols:
        if "배정" in c or "이월" in c:
            df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0).astype(int)
            
    df["비고"] = df["비고"].fillna("").astype(str).str.strip()
    df = df[df["과제/사업단명"] != ""].reset_index(drop=True)
    return df[expected_cols]

def clean_budget_details(df, default_b_name):
    expected_cols = ["사업명", "과제/사업단명", "비목", "보조비목", "보조세목"]
    for i in range(1, 6):
        expected_cols.extend([f"배정예산액_{i}차", f"이월금_{i}차"])
    expected_cols.append("비고")
    
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        df = pd.DataFrame([
            {"사업명": default_b_name, "과제/사업단명": "사업단 본과제 (4-3 광주형 미래라이프)", "비목": "운영비", "보조비목": "일반수용비", "보조세목": "일반수용비(3)", "배정예산액_1차": 50000000, "비고": ""},
        ])
        
    df = df.copy()
    if "배정예산액" in df.columns and "배정예산액_1차" not in df.columns:
        df["배정예산액_1차"] = df["배정예산액"]
        
    df = ensure_business_tag(df, default_b_name, expected_cols)
            
    df["과제/사업단명"] = df["과제/사업단명"].fillna("").astype(str).str.strip().map(normalize_anchor_text)
    df["비목"] = df["비목"].fillna("").astype(str).str.strip()
    df["보조비목"] = df["보조비목"].fillna("").astype(str).str.strip()
    df["보조세목"] = df["보조세목"].fillna("").astype(str).str.strip()
    
    for c in expected_cols:
        if "배정" in c or "이월" in c:
            df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0).astype(int)
            
    df["비고"] = df["비고"].fillna("").astype(str).str.strip()
    
    has_content = (df["과제/사업단명"] != "") & (df["비목"] != "")
    df = df[has_content].reset_index(drop=True)
    return df[expected_cols]

def clean_expenses(df, default_b_name):
    expected_cols = ["No", "집행차수", "재원구분", "지출일자", "사업명", "과제/사업단명", "비목", "보조비목", "보조세목", "지출액", "지출처/적요", "지급상태", "비고"]
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(columns=expected_cols)
        
    df = df.copy()
    
    # 🔴 데이터 마이그레이션 - 빈 데이터프레임 오류 원천 차단
    if "집행차수" not in df.columns:
        df["집행차수"] = "1차년도"
    if "재원구분" not in df.columns:
        df["재원구분"] = "당해 배정액"
        
    df = ensure_business_tag(df, default_b_name, expected_cols)
    
    df["No"] = pd.to_numeric(df.get("No", 0), errors="coerce").fillna(0).astype(int)
    max_existing_no = df["No"].max() if not df.empty else 0
    if max_existing_no <= 0: max_existing_no = 0
    
    for idx, row in df.iterrows():
        if row["No"] <= 0:
            max_existing_no += 1
            df.loc[idx, "No"] = max_existing_no

    df["집행차수"] = df["집행차수"].replace("", "1차년도").fillna("1차년도").astype(str).str.strip()
    df["재원구분"] = df["재원구분"].replace("", "당해 배정액").fillna("당해 배정액").astype(str).str.strip()
    df["지출일자"] = df["지출일자"].fillna(str(datetime.now().date())).astype(str).str.strip()
    df["과제/사업단명"] = df["과제/사업단명"].fillna("").astype(str).str.strip().map(normalize_anchor_text)
    df["비목"] = df["비목"].fillna("").astype(str).str.strip()
    df["보조비목"] = df["보조비목"].fillna("").astype(str).str.strip()
    df["보조세목"] = df["보조세목"].fillna("").astype(str).str.strip()
    df["지출액"] = pd.to_numeric(df["지출액"], errors="coerce").fillna(0).astype(int)
    df["지출처/적요"] = df["지출처/적요"].fillna("").astype(str).str.strip()
    df["지급상태"] = df["지급상태"].fillna("지급완료").astype(str).str.strip()
    df["비고"] = df["비고"].fillna("").astype(str).str.strip()
    
    df = df[df["과제/사업단명"] != ""].reset_index(drop=True)
    return df[expected_cols]

def clean_categories(df):
    expected_cols = ["비목", "보조비목", "보조세목", "설명"]
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame([
            {"비목": "운영비", "보조비목": "일반수용비", "보조세목": "일반수용비(3)", "설명": "일반 수용비 및 운영 경비"},
            {"비목": "운영비", "보조비목": "재료비", "보조세목": "재료비(3)", "설명": "실습 및 과제 수행 재료비"},
            {"비목": "여비", "보조비목": "국내여비", "보조세목": "국내여비(3)", "설명": "국내 출장 경비"},
            {"비목": "인건비", "보조비목": "보수", "보조세목": "보수(1)", "설명": "인건비 및 연구원 보수"}
        ])
    df = df.copy()
    df = safe_get_columns(df, expected_cols)
    df["비목"] = df["비목"].fillna("").astype(str).str.strip()
    df["보조비목"] = df["보조비목"].fillna("").astype(str).str.strip()
    df["보조세목"] = df["보조세목"].fillna("").astype(str).str.strip()
    df["설명"] = df["설명"].fillna("").astype(str).str.strip()
    df = df[(df["비목"] != "") | (df["보조비목"] != "") | (df["보조세목"] != "")].reset_index(drop=True)
    return df[expected_cols]

# ── KPI 로직 ──
KPI_SUB_PREFIXES = ("A:", "B:", "C:", "D:", "E:", "B1:", "B2:", "B3:")

def split_kpi_num(num_str):
    s = str(num_str).strip().upper().replace(" ", "")
    if s in ["", "NAN", "NONE", "-"]: return None, ""
    m = re.match(r"^(\d+)[-–_.]?([A-Z]\d*)?$", s)
    if m:
        base = int(m.group(1))
        suffix = m.group(2) if m.group(2) else ""
        return base, suffix
    m2 = re.search(r"(\d+)", s)
    if m2: return int(m2.group(1)), ""
    return None, ""

def classify_kpi_type(num_str, name_str):
    name_s = str(name_str).strip()
    num_s = str(num_str).strip()
    base, suffix = split_kpi_num(num_s)
    if suffix: return "└ 🔹 세부지표"
    if name_s.startswith(KPI_SUB_PREFIXES): return "└ 🔹 세부지표"
    if base is not None: return "📌 주지표"
    if name_s and name_s[0].isdigit(): return "📌 주지표"
    return "└ 🔹 세부지표"

def parse_kpi_excel(filepath="성과지표.xlsx"):
    expected_order = [
        "No", "지표구분", "단위과제", "지표번호", "지표명", "단위", "가중치",
        "기준값", "목푯값_1차", "목푯값_2차", "목푯값_3차", "목푯값_4차", "목푯값_5차",
        "실적값_1차", "실적값_2차", "실적값_3차", "실적값_4차", "실적값_5차",
        "컨소_기준값", "컨소_목푯값_1차", "컨소_목푯값_2차", "컨소_목푯값_3차", "컨소_목푯값_4차", "컨소_목푯값_5차",
        "컨소_실적값_1차", "컨소_실적값_2차", "컨소_실적값_3차", "컨소_실적값_4차", "컨소_실적값_5차", "비고"
    ]
    if not os.path.exists(filepath):
        return pd.DataFrame(columns=expected_order)
    try:
        xls = pd.ExcelFile(filepath)
        sheet_map = {'전남대학교_공통': '공통', '전남대학교_자율': '자율'}
        all_kpis = []
        for sheet_name, gubun in sheet_map.items():
            if sheet_name in xls.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                data = df.iloc[6:].copy()
                data.columns = [
                    'unused', '단위과제', '지표번호', '지표명', '단위', '가중치',
                    '기준값', '목푯값_1차', '목푯값_2차', '목푯값_3차', '목푯값_4차', '목푯값_5차',
                    '컨소_기준값', '컨소_목푯값_1차', '컨소_목푯값_2차', '컨소_목푯값_3차', '컨소_목푯값_4차', '컨소_목푯값_5차'
                ]
                data = data.drop(columns=['unused'])
                data['지표구분'] = gubun
                for col in ['단위과제', '지표번호', '지표명', '단위', '가중치']:
                    data[col] = data[col].fillna('').astype(str).str.strip()
                data = data[data['지표명'] != ''].reset_index(drop=True)
                for col in data.columns:
                    data[col] = data[col].apply(lambda x: '' if pd.isna(x) else str(x).strip())
                for i in range(1, 6):
                    data[f'실적값_{i}차'] = ''
                    data[f'컨소_실적값_{i}차'] = ''
                data['비고'] = ''
                all_kpis.append(data)
        if not all_kpis:
            return pd.DataFrame(columns=expected_order)
        combined = pd.concat(all_kpis, ignore_index=True)
        combined['No'] = range(1, len(combined) + 1)
        return combined[expected_order]
    except Exception:
        return pd.DataFrame(columns=expected_order)

def clean_kpis(df):
    expected_order = [
        "No", "지표구분", "단위과제", "지표번호", "지표명", "단위", "가중치",
        "기준값", "목푯값_1차", "목푯값_2차", "목푯값_3차", "목푯값_4차", "목푯값_5차",
        "실적값_1차", "실적값_2차", "실적값_3차", "실적값_4차", "실적값_5차",
        "컨소_기준값", "컨소_목푯값_1차", "컨소_목푯값_2차", "컨소_목푯값_3차", "컨소_목푯값_4차", "컨소_목푯값_5차",
        "컨소_실적값_1차", "컨소_실적값_2차", "컨소_실적값_3차", "컨소_실적값_4차", "컨소_실적값_5차", "비고"
    ]
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return parse_kpi_excel()
        
    df = df.copy()
    df = safe_get_columns(df, expected_order)
    
    df["No"] = pd.to_numeric(df["No"], errors="coerce").fillna(0).astype(int)
    max_no = df["No"].max() if not df.empty else 0
    if max_no <= 0: max_no = 0
    for idx, row in df.iterrows():
        if row["No"] <= 0:
            max_no += 1
            df.loc[idx, "No"] = max_no
            
    df["지표명"] = df["지표명"].fillna("").astype(str).str.strip().map(normalize_anchor_text)
    df["단위과제"] = df["단위과제"].fillna("").astype(str).str.strip().map(normalize_anchor_text)
    df["지표구분"] = df["지표구분"].fillna("공통").astype(str).str.strip()
    
    for col in expected_order:
        if col != "No":
            df[col] = df[col].apply(lambda x: "" if (pd.isna(x) or str(x).strip() in ['nan', 'None']) else str(x).strip())
            
    unit_order = []
    for u in df["단위과제"].tolist():
        if u and u not in unit_order: unit_order.append(u)
            
    df["지표구분_order"] = df["지표구분"].map(lambda x: 0 if x == "공통" else 1)
    df["단위과제_order"] = df["단위과제"].map(lambda x: unit_order.index(x) if x in unit_order else 999)
    df["지표번호_num"] = pd.to_numeric(df["지표번호"], errors="coerce").fillna(999)
    
    df = df.sort_values(by=["지표구분_order", "단위과제_order", "지표번호_num", "No"]).reset_index(drop=True)
    df = df.drop(columns=["지표구분_order", "단위과제_order", "지표번호_num"])
    
    df = df[df["지표명"] != ""].reset_index(drop=True)
    return df[expected_order]

def compute_kpi_achievement(df, year_num=1):
    target_col = f"목푯값_{year_num}차"
    actual_col = f"실적값_{year_num}차"
    conso_target_col = f"컨소_목푯값_{year_num}차"
    conso_actual_col = f"컨소_실적값_{year_num}차"
    
    res_df = df.copy()
    
    for col in res_df.columns:
        if col not in ["No", "달성률(%)"]:
            res_df[col] = res_df[col].apply(lambda x: "" if (pd.isna(x) or str(x).strip() in ['nan', 'None']) else str(x).strip())
            
    unit_order = []
    for u in res_df["단위과제"].tolist():
        if u and u not in unit_order: unit_order.append(u)
            
    res_df["지표구분_order"] = res_df["지표구분"].map(lambda x: 0 if x == "공통" else 1)
    res_df["단위과제_order"] = res_df["단위과제"].map(lambda x: unit_order.index(x) if x in unit_order else 999)
    res_df["지표번호_num"] = pd.to_numeric(res_df["지표번호"], errors="coerce").fillna(999)
    
    res_df = res_df.sort_values(by=["지표구분_order", "단위과제_order", "지표번호_num", "No"]).reset_index(drop=True)
    res_df = res_df.drop(columns=["지표구분_order", "단위과제_order", "지표번호_num"])
    
    for (gubun, unit, num), group_indices in res_df.groupby(["지표구분", "단위과제", "지표번호"]).groups.items():
        sub_indices = []
        main_index = None
        for idx in group_indices:
            row = res_df.loc[idx]
            name_s = str(row["지표명"]).strip()
            num_s = str(row["지표번호"]).strip()
            if name_s.startswith(("A:", "B:", "C:", "D:", "B1:", "B2:", "B3:")):
                sub_indices.append(idx)
            elif num_s and num_s.isdigit() and (name_s and name_s[0].isdigit()):
                main_index = idx
            elif main_index is None and idx == group_indices[0]:
                main_index = idx
                
        if main_index is not None and sub_indices:
            sub_weighted_sum = 0.0
            has_any_sub_actual = False
            conso_sub_weighted_sum = 0.0
            has_any_conso_sub_actual = False
            
            for s_idx in sub_indices:
                s_row = res_df.loc[s_idx]
                w_val = s_row["가중치"]
                try: w = float(str(w_val).strip())
                except Exception: w = 1.0
                    
                a_val = s_row.get(actual_col, "")
                try:
                    a_str = str(a_val).replace(',', '').replace('%', '').strip()
                    if a_str != "" and a_str != "-":
                        sub_weighted_sum += float(a_str) * w
                        has_any_sub_actual = True
                except Exception: pass
                    
                ca_val = s_row.get(conso_actual_col, "")
                try:
                    ca_str = str(ca_val).replace(',', '').replace('%', '').strip()
                    if ca_str != "" and ca_str != "-":
                        conso_sub_weighted_sum += float(ca_str) * w
                        has_any_conso_sub_actual = True
                except Exception: pass
                    
            if has_any_sub_actual:
                val = round(sub_weighted_sum, 2)
                res_df.loc[main_index, actual_col] = str(int(val)) if val.is_integer() else str(val)
            if has_any_conso_sub_actual and conso_actual_col in res_df.columns:
                c_val = round(conso_sub_weighted_sum, 2)
                res_df.loc[main_index, conso_actual_col] = str(int(c_val)) if c_val.is_integer() else str(c_val)

    def parse_num(val):
        if pd.isna(val) or val == '' or str(val).strip() in ['-', '미입력', 'nan', 'None']:
            return np.nan
        try:
            return float(str(val).replace(',', '').replace('%', '').strip())
        except Exception:
            return np.nan
            
    targets = res_df[target_col].apply(parse_num) if target_col in res_df.columns else pd.Series(np.nan, index=res_df.index)
    actuals = res_df[actual_col].apply(parse_num) if actual_col in res_df.columns else pd.Series(np.nan, index=res_df.index)
    
    rates = []
    statuses = []
    
    for t, a in zip(targets, actuals):
        if pd.isna(t) or t == 0 or pd.isna(a):
            rates.append(np.nan)
            statuses.append("⚪ 미입력")
        else:
            r = round((a / t) * 100, 1)
            rates.append(r)
            if r >= 100.0: statuses.append("🟢 달성")
            elif r >= 80.0: statuses.append("🟡 진행중")
            else: statuses.append("🔴 미달")
                
    res_df["달성률(%)"] = rates
    res_df["달성상태"] = statuses
    res_df["지표유형"] = [classify_kpi_type(n, m) for n, m in zip(res_df.get("지표번호", ""), res_df.get("지표명", ""))]
    return res_df

# ── Budget Syncing & Carryover Auto Calculation ──
def sync_project_budgets_from_details(p_df, bd_df, default_b_name):
    p_df = p_df.copy()
    if bd_df is None or bd_df.empty: return p_df
    bd_clean = clean_budget_details(bd_df, default_b_name)
    if bd_clean.empty: return p_df
        
    budget_cols = [c for c in bd_clean.columns if "배정예산액" in c or "이월금" in c]
    cat_sums = bd_clean.groupby(["사업명", "과제/사업단명"])[budget_cols].sum().reset_index()
    
    for idx, row in cat_sums.iterrows():
        b_name, p_name = row["사업명"], row["과제/사업단명"]
        p_idx = p_df[(p_df["사업명"] == b_name) & (p_df["과제/사업단명"] == p_name)].index
        if not p_idx.empty:
            for bc in budget_cols:
                if row[bc] > 0: p_df.loc[p_idx[0], bc] = int(row[bc])
    return p_df

def auto_calculate_carryovers(p_df, bd_df, e_df, cur_b):
    p_df = p_df.copy()
    bd_df = bd_df.copy()
    e_b_df = e_df[e_df["사업명"] == cur_b] if not e_df.empty else pd.DataFrame()
    
    for idx in p_df[p_df["사업명"] == cur_b].index:
        p_name = p_df.loc[idx, "과제/사업단명"]
        p_exp = e_b_df[e_b_df["과제/사업단명"] == p_name]
        
        for y in range(2, 6):
            prev_y = y - 1
            prev_alloc = int(p_df.loc[idx, f"배정예산액_{prev_y}차"])
            prev_carry = int(p_df.loc[idx, f"이월금_{prev_y}차"])
            
            # 전년도 잔액을 철저히 분리 계산
            prev_alloc_spent = int(p_exp[(p_exp["집행차수"] == f"{prev_y}차년도") & (p_exp["재원구분"] == "당해 배정액")]["지출액"].sum()) if not p_exp.empty else 0
            prev_carry_spent = int(p_exp[(p_exp["집행차수"] == f"{prev_y}차년도") & (p_exp["재원구분"] == "전년 이월금")]["지출액"].sum()) if not p_exp.empty else 0
            
            alloc_rem = max(0, prev_alloc - prev_alloc_spent)
            carry_rem = max(0, prev_carry - prev_carry_spent)
            
            total_carryover = alloc_rem + carry_rem
            p_df.loc[idx, f"이월금_{y}차"] = total_carryover
            
    for idx in bd_df[bd_df["사업명"] == cur_b].index:
        p_name = bd_df.loc[idx, "과제/사업단명"]
        bimok, bbimok, bsemok = bd_df.loc[idx, "비목"], bd_df.loc[idx, "보조비목"], bd_df.loc[idx, "보조세목"]
        cat_exp = e_b_df[
            (e_b_df["과제/사업단명"] == p_name) & (e_b_df["비목"] == bimok) & 
            (e_b_df["보조비목"] == bbimok) & (e_b_df["보조세목"] == bsemok)
        ]
        for y in range(2, 6):
            prev_y = y - 1
            prev_alloc = int(bd_df.loc[idx, f"배정예산액_{prev_y}차"])
            prev_carry = int(bd_df.loc[idx, f"이월금_{prev_y}차"])
            
            prev_alloc_spent = int(cat_exp[(cat_exp["집행차수"] == f"{prev_y}차년도") & (cat_exp["재원구분"] == "당해 배정액")]["지출액"].sum()) if not cat_exp.empty else 0
            prev_carry_spent = int(cat_exp[(cat_exp["집행차수"] == f"{prev_y}차년도") & (cat_exp["재원구분"] == "전년 이월금")]["지출액"].sum()) if not cat_exp.empty else 0
            
            alloc_rem = max(0, prev_alloc - prev_alloc_spent)
            carry_rem = max(0, prev_carry - prev_carry_spent)
            
            total_carryover = alloc_rem + carry_rem
            bd_df.loc[idx, f"이월금_{y}차"] = total_carryover
            
    return p_df, bd_df

# --- Budget Limit Validation Functions ---
def check_single_expense_budget_limit(b_name, proj_name, fund_source, amount, current_exp_df, current_p_df, current_bd_df, active_year, bimok=None, bojo_bimok=None, bojo_semok=None):
    p_match = current_p_df[(current_p_df["사업명"] == b_name) & (current_p_df["과제/사업단명"] == proj_name)]
    if p_match.empty: return False, "과제를 찾을 수 없습니다."
        
    alloc_c = f"배정예산액_{active_year}차"
    carry_c = f"이월금_{active_year}차"
    
    p_alloc = int(p_match.iloc[0][alloc_c])
    p_carry = int(p_match.iloc[0][carry_c])
    p_budget = p_carry if fund_source == "전년 이월금" else p_alloc
    
    p_exp = current_exp_df[(current_exp_df["사업명"] == b_name) & (current_exp_df["과제/사업단명"] == proj_name) & (current_exp_df["집행차수"] == f"{active_year}차년도") & (current_exp_df["재원구분"] == fund_source)]
    p_spent = int(p_exp["지출액"].sum()) if not p_exp.empty else 0
    p_balance = p_budget - p_spent
    fund_label = "이월금" if fund_source == "전년 이월금" else "당해배정예산"
    
    if amount > p_balance:
        return False, f"🚫 **[과제 {fund_label} 초과]** 지출액(₩{amount:,.0f})이 해당 과제의 **{active_year}차년도 {fund_label} 잔액(₩{p_balance:,.0f})**을 초과합니다! (가용: ₩{p_budget:,.0f}, 지출: ₩{p_spent:,.0f})"
        
    if bimok and bojo_bimok and bojo_semok and not current_bd_df.empty:
        cat_match = current_bd_df[
            (current_bd_df["사업명"] == b_name) & (current_bd_df["과제/사업단명"] == proj_name) &
            (current_bd_df["비목"] == bimok) & (current_bd_df["보조비목"] == bojo_bimok) & (current_bd_df["보조세목"] == bojo_semok)
        ]
        if not cat_match.empty:
            c_alloc = int(cat_match.iloc[0][alloc_c])
            c_carry = int(cat_match.iloc[0][carry_c])
            c_budget = c_carry if fund_source == "전년 이월금" else c_alloc
            
            if c_budget > 0 or p_budget > 0:
                cat_exp = p_exp[(p_exp["비목"] == bimok) & (p_exp["보조비목"] == bojo_bimok) & (p_exp["보조세목"] == bojo_semok)] if not p_exp.empty else pd.DataFrame()
                c_spent = int(cat_exp["지출액"].sum()) if not cat_exp.empty else 0
                c_balance = c_budget - c_spent
                if c_budget > 0 and amount > c_balance:
                    return False, f"🚫 **[세목 {fund_label} 초과]** 지출액(₩{amount:,.0f})이 [{bimok} > {bojo_semok}]의 **{active_year}차년도 {fund_label} 잔액(₩{c_balance:,.0f})**을 초과합니다! (가용: ₩{c_budget:,.0f}, 지출: ₩{c_spent:,.0f})"
    return True, ""

def validate_all_expenses_against_budgets(cand_expenses_df, current_p_df, current_bd_df):
    errors = []
    if cand_expenses_df is None or cand_expenses_df.empty: return True, []
    cand_df = cand_expenses_df.copy()
    cand_df["지출액"] = pd.to_numeric(cand_df["지출액"], errors="coerce").fillna(0).astype(int)
    
    proj_spent = cand_df.groupby(["사업명", "과제/사업단명", "집행차수", "재원구분"])["지출액"].sum().reset_index()
    for idx, row in proj_spent.iterrows():
        b_name, p_name, y_str, f_src, t_spent = row["사업명"], row["과제/사업단명"], row["집행차수"], row["재원구분"], row["지출액"]
        y_num = str(y_str).replace("차년도", "").strip()
        p_match = current_p_df[(current_p_df["사업명"] == b_name) & (current_p_df["과제/사업단명"] == p_name)]
        if not p_match.empty and f"배정예산액_{y_num}차" in p_match.columns:
            p_alloc = int(p_match.iloc[0][f"배정예산액_{y_num}차"])
            p_carry = int(p_match.iloc[0][f"이월금_{y_num}차"])
            p_budget = p_carry if f_src == "전년 이월금" else p_alloc
            if t_spent > p_budget:
                excess = t_spent - p_budget
                errors.append(f"• [{b_name}] {p_name} ({y_str} / {f_src}): 가용 ₩{p_budget:,.0f} < 지출 ₩{t_spent:,.0f} (₩{excess:,.0f} 초과)")
                
    if not current_bd_df.empty:
        cat_spent = cand_df.groupby(["사업명", "과제/사업단명", "집행차수", "재원구분", "비목", "보조비목", "보조세목"])["지출액"].sum().reset_index()
        for idx, row in cat_spent.iterrows():
            b_name, p_name, y_str, f_src = row["사업명"], row["과제/사업단명"], row["집행차수"], row["재원구분"]
            bimok_n, bb_name, bs_name, c_spent = row["비목"], row["보조비목"], row["보조세목"], row["지출액"]
            y_num = str(y_str).replace("차년도", "").strip()
            
            bd_match = current_bd_df[
                (current_bd_df["사업명"] == b_name) & (current_bd_df["과제/사업단명"] == p_name) &
                (current_bd_df["비목"] == bimok_n) & (current_bd_df["보조비목"] == bb_name) & (current_bd_df["보조세목"] == bs_name)
            ]
            if not bd_match.empty and f"배정예산액_{y_num}차" in bd_match.columns:
                c_alloc = int(bd_match.iloc[0][f"배정예산액_{y_num}차"])
                c_carry = int(bd_match.iloc[0][f"이월금_{y_num}차"])
                c_budget = c_carry if f_src == "전년 이월금" else c_alloc
                if c_budget > 0 and c_spent > c_budget:
                    excess = c_spent - c_budget
                    errors.append(f"• [{b_name}] {p_name} ({y_str} / {f_src}) [{bimok_n} > {bs_name}]: 세목 가용 ₩{c_budget:,.0f} < 지출 ₩{c_spent:,.0f} (₩{excess:,.0f} 초과)")
                    
    if errors: return False, errors
    return True, []

# --- GitHub REST API Auto-Commit Engine ---
def push_file_to_github_api(token, repo, path, content_str, commit_message="Auto-sync budget data"):
    if not token or not repo: return False, "GitHub Token or Repo name is empty."
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "Streamlit-Budget-App"}
    sha = None
    req_get = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req_get) as response:
            if response.status == 200: sha = json.loads(response.read().decode("utf-8")).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404: return False, f"HTTP Error {e.code}: {e.reason}"
    except Exception as e: return False, str(e)
    content_b64 = base64.b64encode(content_str.encode("utf-8-sig")).decode("utf-8")
    payload = {"message": commit_message, "content": content_b64}
    if sha: payload["sha"] = sha
    data_bytes = json.dumps(payload).encode("utf-8")
    req_put = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req_put) as response:
            if response.status in [200, 201]: return True, "Successfully committed to GitHub!"
            else: return False, f"Unexpected status: {response.status}"
    except urllib.error.HTTPError as e: return False, f"GitHub Error {e.code}: {e.reason}"
    except Exception as e: return False, str(e)

def sync_all_to_github():
    try:
        gh_token = st.secrets.get("GITHUB_TOKEN") or st.secrets.get("github", {}).get("TOKEN")
        gh_repo = st.secrets.get("GITHUB_REPO") or st.secrets.get("github", {}).get("REPO")
    except Exception:
        return False, "❌ .streamlit/secrets.toml 파일이 없거나 올바르게 설정되지 않았습니다."
        
    if not gh_token or not gh_repo: return False, "깃허브 토큰 또는 저장소 이름이 설정되지 않았습니다."
    files_to_sync = {
        "businesses.csv": st.session_state["businesses"].to_csv(index=False, encoding="utf-8-sig"),
        "budget_projects.csv": st.session_state["budget_projects"].to_csv(index=False, encoding="utf-8-sig"),
        "categories.csv": st.session_state["categories"].to_csv(index=False, encoding="utf-8-sig"),
        "expenses.csv": st.session_state["expenses"].to_csv(index=False, encoding="utf-8-sig"),
        "budget_details.csv": st.session_state["budget_details"].to_csv(index=False, encoding="utf-8-sig"),
        "kpis.csv": st.session_state["kpis"].to_csv(index=False, encoding="utf-8-sig")
    }
    failed_files = []
    for filename, csv_str in files_to_sync.items():
        ok, msg = push_file_to_github_api(gh_token, gh_repo, filename, csv_str, commit_message=f"Auto-update {filename} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        if not ok: failed_files.append(f"{filename}: {msg}")
    if failed_files: return False, "\n".join(failed_files)
    return True, "모든 CSV 데이터가 깃허브 저장소로 성공적으로 동기화되었습니다!"

# Safe Data Loader
def load_data():
    b_df = pd.read_csv("businesses.csv") if os.path.exists("businesses.csv") else pd.DataFrame()
    b_clean = clean_businesses(b_df)
    default_b_name = b_clean.iloc[0]["사업명"]

    p_df = pd.read_csv("budget_projects.csv") if os.path.exists("budget_projects.csv") else pd.DataFrame()
    c_df = pd.read_csv("categories.csv") if os.path.exists("categories.csv") else pd.DataFrame()
    e_df = pd.read_csv("expenses.csv") if os.path.exists("expenses.csv") else pd.DataFrame()
    bd_df = pd.read_csv("budget_details.csv") if os.path.exists("budget_details.csv") else pd.DataFrame()
    kpi_df = pd.read_csv("kpis.csv") if os.path.exists("kpis.csv") else pd.DataFrame()

    p_clean = clean_budget_projects(p_df, default_b_name)
    c_clean = clean_categories(c_df)
    e_clean = clean_expenses(e_df, default_b_name)
    bd_clean = clean_budget_details(bd_df, default_b_name)
    k_clean = clean_kpis(kpi_df)
    p_synced = sync_project_budgets_from_details(p_clean, bd_clean, default_b_name)

    return b_clean, p_synced, c_clean, e_clean, bd_clean, k_clean

if "businesses" not in st.session_state or "budget_projects" not in st.session_state:
    b, p, c, e, bd, k = load_data()
    st.session_state["businesses"] = b
    st.session_state["budget_projects"] = p
    st.session_state["categories"] = c
    st.session_state["expenses"] = e
    st.session_state["budget_details"] = bd
    st.session_state["kpis"] = k

def get_default_b_name():
    b_df = st.session_state.get("businesses", pd.DataFrame())
    if not b_df.empty and "사업명" in b_df.columns: return b_df.iloc[0]["사업명"]
    return "앵커 사업단 (광주형 미래라이프)"

if "selected_business" not in st.session_state:
    st.session_state["selected_business"] = get_default_b_name()
st.session_state["selected_business"] = normalize_anchor_text(st.session_state["selected_business"])

if "menu_selection" not in st.session_state: st.session_state["menu_selection"] = "📊 통합 대시보드"
if "selected_project_nav" not in st.session_state:
    cur_b = st.session_state["selected_business"]
    p_df = st.session_state["budget_projects"]
    p_names = p_df[p_df["사업명"] == cur_b]["과제/사업단명"].tolist() if (not p_df.empty and "사업명" in p_df.columns) else []
    st.session_state["selected_project_nav"] = p_names[0] if p_names else "선택 가능 과제 없음"

if "auto_github_sync" not in st.session_state: st.session_state["auto_github_sync"] = False
if "last_saved" not in st.session_state: st.session_state["last_saved"] = "-"
if "last_github_sync" not in st.session_state: st.session_state["last_github_sync"] = "-"

def save_and_sync_all(toast_msg="💾 저장이 완료되었습니다."):
    def_b = get_default_b_name()
    st.session_state["businesses"] = clean_businesses(st.session_state["businesses"])
    st.session_state["budget_projects"] = clean_budget_projects(st.session_state["budget_projects"], def_b)
    st.session_state["categories"] = clean_categories(st.session_state["categories"])
    st.session_state["expenses"] = clean_expenses(st.session_state["expenses"], def_b)
    st.session_state["budget_details"] = clean_budget_details(st.session_state["budget_details"], def_b)
    st.session_state["kpis"] = clean_kpis(st.session_state["kpis"])

    st.session_state["budget_projects"] = sync_project_budgets_from_details(
        st.session_state["budget_projects"], st.session_state["budget_details"], def_b
    )

    try:
        st.session_state["businesses"].to_csv("businesses.csv", index=False, encoding="utf-8-sig")
        st.session_state["budget_projects"].to_csv("budget_projects.csv", index=False, encoding="utf-8-sig")
        st.session_state["categories"].to_csv("categories.csv", index=False, encoding="utf-8-sig")
        st.session_state["expenses"].to_csv("expenses.csv", index=False, encoding="utf-8-sig")
        st.session_state["budget_details"].to_csv("budget_details.csv", index=False, encoding="utf-8-sig")
        st.session_state["kpis"].to_csv("kpis.csv", index=False, encoding="utf-8-sig")
        st.session_state["last_saved"] = datetime.now().strftime("%m/%d %H:%M:%S")
    except Exception: pass

    if st.session_state.get("auto_github_sync", False):
        try:
            ok, _msg = sync_all_to_github()
            if ok: st.session_state["last_github_sync"] = datetime.now().strftime("%m/%d %H:%M:%S")
        except Exception: pass
    try: st.toast(toast_msg, icon="✅")
    except Exception: pass

def get_bimok_list(cur_b=None):
    c_df = st.session_state.get("categories", pd.DataFrame())
    if not c_df.empty and "비목" in c_df.columns:
        opts = [x for x in c_df["비목"].dropna().unique().tolist() if str(x).strip() != ""]
        if opts: return opts
    return ["운영비", "인건비", "여비"]

def get_bojo_bimok_list(cur_b_or_bimok, selected_bimok=None):
    target_bimok = selected_bimok if selected_bimok is not None else cur_b_or_bimok
    c_df = st.session_state.get("categories", pd.DataFrame())
    if not c_df.empty and all(c in c_df.columns for c in ["비목", "보조비목"]):
        filtered = c_df[c_df["비목"] == target_bimok]
        if not filtered.empty:
            opts = [x for x in filtered["보조비목"].dropna().unique().tolist() if str(x).strip() != ""]
            if opts: return opts
    return ["일반수용비"]

def get_bojo_semok_list(arg1, arg2, arg3=None):
    if arg3 is not None: target_bimok, target_bojo_bimok = arg2, arg3
    else: target_bimok, target_bojo_bimok = arg1, arg2
    c_df = st.session_state.get("categories", pd.DataFrame())
    if not c_df.empty and all(c in c_df.columns for c in ["비목", "보조비목", "보조세목"]):
        filtered = c_df[(c_df["비목"] == target_bimok) & (c_df["보조비목"] == target_bojo_bimok)]
        if not filtered.empty:
            opts = [x for x in filtered["보조세목"].dropna().unique().tolist() if str(x).strip() != ""]
            if opts: return opts
    return ["일반수용비(3)"]

# ====================================================
# 4. Sidebar Navigation & Active Business/Year Selector
# ====================================================
with st.sidebar:
    st.markdown(LOGO_HTML, unsafe_allow_html=True)
    st.divider()

    st.markdown("#### 📅 현재 관리 차수 설정")
    selected_year_str = st.selectbox("1~5차년도 (전체 메뉴 일괄 연동)", ["1차년도", "2차년도", "3차년도", "4차년도", "5차년도"], index=0, key="global_year_select")
    active_year = int(selected_year_str.replace("차년도", ""))
    st.caption(f"🗓️ 기간: **{YEAR_PERIODS.get(active_year, '')}**")
    
    if active_year < 5:
        with st.expander(f"🔄 {active_year}차 ➔ {active_year+1}차 데이터 복사", expanded=False):
            st.caption(f"현재 선택된 사업의 **{active_year}차년도 배정예산**과 **목표값**을 **{active_year+1}차년도**로 복사합니다. (비어있는 칸만 안전하게 채웁니다.)")
            copy_confirm = st.checkbox("안내를 확인했습니다.", key="chk_copy_data")
            if st.button(f"🚀 {active_year+1}차년도로 복사 실행", disabled=not copy_confirm, use_container_width=True):
                bp = st.session_state["budget_projects"].copy()
                if not bp.empty and f"배정예산액_{active_year}차" in bp.columns:
                    bp[f"배정예산액_{active_year+1}차"] = np.where(bp[f"배정예산액_{active_year+1}차"] == 0, bp[f"배정예산액_{active_year}차"], bp[f"배정예산액_{active_year+1}차"])
                    st.session_state["budget_projects"] = bp

                bd = st.session_state["budget_details"].copy()
                if not bd.empty and f"배정예산액_{active_year}차" in bd.columns:
                    bd[f"배정예산액_{active_year+1}차"] = np.where(bd[f"배정예산액_{active_year+1}차"] == 0, bd[f"배정예산액_{active_year}차"], bd[f"배정예산액_{active_year+1}차"])
                    st.session_state["budget_details"] = bd

                kpis = st.session_state["kpis"].copy()
                if not kpis.empty and f"목푯값_{active_year}차" in kpis.columns:
                    kpis[f"목푯값_{active_year+1}차"] = np.where(
                        (kpis[f"목푯값_{active_year+1}차"] == "") | kpis[f"목푯값_{active_year+1}차"].isna(),
                        kpis[f"목푯값_{active_year}차"],
                        kpis[f"목푯값_{active_year+1}차"]
                    )
                    st.session_state["kpis"] = kpis
                
                save_and_sync_all(f"✅ {active_year}차년도 데이터가 {active_year+1}차년도로 성공적으로 복사되었습니다!")
                st.rerun()

    st.divider()

    b_df_sidebar = st.session_state["businesses"]
    b_list = b_df_sidebar["사업명"].tolist() if not b_df_sidebar.empty else [get_default_b_name()]
    cur_b_idx = b_list.index(st.session_state["selected_business"]) if st.session_state["selected_business"] in b_list else 0
    selected_b = st.selectbox("🏢 관리 사업(프로젝트 그룹) 선택", b_list, index=cur_b_idx, key="sidebar_business_selectbox")
    st.session_state["selected_business"] = selected_b

    with st.expander("⚙️ 사업 신규 추가 / 수정 / 삭제", expanded=False):
        b_tab1, b_tab2, b_tab3 = st.tabs(["➕ 추가", "✏️ 수정", "🗑️ 삭제"])
        with b_tab1:
            with st.form("form_add_business", clear_on_submit=True):
                nb_code = st.text_input("사업 코드 (예: 4-5)")
                nb_name = st.text_input("사업명 (프로젝트 그룹명)")
                nb_leader = st.text_input("총괄 책임자")
                nb_period = st.text_input("사업 기간", value="2025. 6. ~ 2030. 2.")
                nb_note = st.text_input("비고 메모")
                if st.form_submit_button("🚀 사업 등록 완료"):
                    if not nb_name: st.error("사업명을 입력해주세요.")
                    else:
                        new_b_row = {"사업코드": nb_code, "사업명": nb_name, "총괄책임자": nb_leader, "사업기간": nb_period, "비고": nb_note}
                        st.session_state["businesses"] = pd.concat([st.session_state["businesses"], pd.DataFrame([new_b_row])], ignore_index=True)
                        st.session_state["selected_business"] = nb_name
                        save_and_sync_all(f"✅ '{nb_name}' 사업이 등록되었습니다!")
                        st.rerun()

        with b_tab2:
            b_info_match = b_df_sidebar[b_df_sidebar["사업명"] == selected_b]
            if not b_info_match.empty:
                cur_b_row = b_info_match.iloc[0]
                with st.form("form_edit_business"):
                    eb_code = st.text_input("사업 코드", value=str(cur_b_row.get("사업코드", "")))
                    eb_name = st.text_input("사업명", value=selected_b)
                    eb_leader = st.text_input("총괄 책임자", value=str(cur_b_row.get("총괄책임자", "")))
                    eb_period = st.text_input("사업 기간", value=str(cur_b_row.get("사업기간", "")))
                    eb_note = st.text_input("비고 메모", value=str(cur_b_row.get("비고", "")))
                    if st.form_submit_button("💾 사업 정보 수정 저장"):
                        main_b = st.session_state["businesses"].copy()
                        b_idx = main_b[main_b["사업명"] == selected_b].index
                        if not b_idx.empty:
                            main_b.loc[b_idx[0], ["사업코드", "사업명", "총괄책임자", "사업기간", "비고"]] = [eb_code, eb_name, eb_leader, eb_period, eb_note]
                            if eb_name != selected_b:
                                for state_key in ["budget_projects", "expenses", "budget_details"]:
                                    df_k = st.session_state[state_key].copy()
                                    if not df_k.empty and "사업명" in df_k.columns:
                                        df_k.loc[df_k["사업명"] == selected_b, "사업명"] = eb_name
                                        st.session_state[state_key] = df_k
                                st.session_state["selected_business"] = eb_name
                            st.session_state["businesses"] = main_b
                            save_and_sync_all("✅ 사업 정보가 수정되었습니다!")
                            st.rerun()

        with b_tab3:
            st.warning("주의: 이 사업을 삭제하면 등록된 사업 목록에서 제외됩니다.")
            del_child_data = st.checkbox("이 사업에 속한 과제, 예산, 지출 내역도 함께 삭제하기", value=True)
            del_confirm_b = st.checkbox("네, 삭제 내용을 확인했습니다. (필수 체크)", key="chk_del_business_confirm")
            if st.button("🔴 선택 사업 삭제 실행", key="btn_del_business", disabled=not del_confirm_b):
                st.session_state["businesses"] = st.session_state["businesses"][st.session_state["businesses"]["사업명"] != selected_b]
                if del_child_data:
                    for state_key in ["budget_projects", "expenses", "budget_details"]:
                        df_k = st.session_state[state_key]
                        if not df_k.empty and "사업명" in df_k.columns:
                            st.session_state[state_key] = df_k[df_k["사업명"] != selected_b]
                st.session_state["selected_business"] = get_default_b_name()
                save_and_sync_all(f"🗑️ '{selected_b}' 사업이 삭제되었습니다.")
                st.rerun()

    st.divider()

    nav_options = [
        "📊 통합 대시보드",
        "🔍 과제별 상세 관리",
        "💰 예산 편성 및 사업단 관리",
        "📝 지출 내역 입력 및 수정",
        "🎯 성과지표 관리",
        "🏷️ 예산 세목 기준표 설정",
        "📁 엑셀 내보내기 & 백업"
    ]
    current_idx = nav_options.index(st.session_state["menu_selection"]) if st.session_state["menu_selection"] in nav_options else 0
    menu = st.radio("📌 메뉴 선택", nav_options, index=current_idx, key="menu_radio_input")
    st.session_state["menu_selection"] = menu

    st.divider()

    cur_p_df = st.session_state["budget_projects"]
    cur_e_df = st.session_state["expenses"]

    b_p_df = cur_p_df[cur_p_df["사업명"] == selected_b] if not cur_p_df.empty else pd.DataFrame()
    b_e_df = cur_e_df[(cur_e_df["사업명"] == selected_b) & (cur_e_df["집행차수"] == selected_year_str)] if not cur_e_df.empty else pd.DataFrame()

    t_budget_allocate = b_p_df[f"배정예산액_{active_year}차"].sum() if not b_p_df.empty and f"배정예산액_{active_year}차" in b_p_df.columns else 0
    t_budget_carryover = b_p_df[f"이월금_{active_year}차"].sum() if not b_p_df.empty and f"이월금_{active_year}차" in b_p_df.columns else 0
    
    if "재원구분" not in b_e_df.columns:
        b_e_df["재원구분"] = "당해 배정액"
        
    t_alloc_spent = int(b_e_df[b_e_df["재원구분"] == "당해 배정액"]["지출액"].sum()) if not b_e_df.empty else 0
    t_carry_spent = int(b_e_df[b_e_df["재원구분"] == "전년 이월금"]["지출액"].sum()) if not b_e_df.empty else 0

    st.markdown(f"### 📈 {selected_year_str} 현황 요약")
    st.markdown(render_separated_budget_status(t_budget_allocate, t_budget_carryover, t_alloc_spent, t_carry_spent), unsafe_allow_html=True)
    st.divider()

    with st.expander("☁️ 저장 & GitHub 동기화 설정", expanded=False):
        st.toggle("저장 시 GitHub 자동 동기화", key="auto_github_sync", help="끄면 로컬 CSV에만 저장되어 처리 속도가 빨라집니다. 필요할 때 아래 수동 동기화를 이용하세요.")
        if st.button("🔄 지금 GitHub에 수동 동기화", use_container_width=True):
            with st.spinner("GitHub 동기화 중..."):
                ok, msg = sync_all_to_github()
            if ok:
                st.session_state["last_github_sync"] = datetime.now().strftime("%m/%d %H:%M:%S")
                st.success(msg)
            else: st.error(msg)
        st.caption(f"💾 마지막 로컬 저장: {st.session_state['last_saved']}")
        st.caption(f"☁️ 마지막 GitHub 동기화: {st.session_state['last_github_sync']}")

cur_b = st.session_state["selected_business"]

st.markdown(f"""
<div class="header-banner">
    <span class="hb-badge">🏢 {cur_b}</span>
    <span class="hb-badge">📅 {selected_year_str} ({YEAR_PERIODS.get(active_year, '')})</span>
    <div class="hb-title" style="margin-top:10px;">💼 예산 · 지출 · 성과 통합관리 시스템</div>
    <div class="hb-sub">좌측 패널에서 연도(1~5차)를 전환하면 모든 대시보드와 입력란이 해당 차년도로 자동 연동됩니다.</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# PAGE 1: 📊 통합 대시보드
# ----------------------------------------------------
if st.session_state["menu_selection"] == "📊 통합 대시보드":
    st.markdown(f'<div class="sec-title">📊 [{cur_b}] {selected_year_str} 전체 예산 및 과제/세목별 집행 현황</div>', unsafe_allow_html=True)
    
    st.markdown(render_separated_budget_status(t_budget_allocate, t_budget_carryover, t_alloc_spent, t_carry_spent), unsafe_allow_html=True)
    st.divider()
    
    p_df = st.session_state["budget_projects"]
    e_df = st.session_state["expenses"]
    bd_df = st.session_state["budget_details"]
    
    p_b_df = p_df[p_df["사업명"] == cur_b].copy() if not p_df.empty else pd.DataFrame()
    e_b_df = e_df[(e_df["사업명"] == cur_b) & (e_df["집행차수"] == selected_year_str)].copy() if not e_df.empty else pd.DataFrame()
    bd_b_df = bd_df[bd_df["사업명"] == cur_b].copy() if not bd_df.empty else pd.DataFrame()
    
    exp_summary = e_b_df.groupby("과제/사업단명")["지출액"].sum().reset_index() if not e_b_df.empty else pd.DataFrame(columns=["과제/사업단명", "지출액"])
    dash_df = pd.merge(p_b_df, exp_summary, on="과제/사업단명", how="left").fillna({"지출액": 0})
    
    alloc_col = f"배정예산액_{active_year}차"
    carry_col = f"이월금_{active_year}차"
    
    if alloc_col not in dash_df.columns: dash_df[alloc_col] = 0
    if carry_col not in dash_df.columns: dash_df[carry_col] = 0
    
    dash_df["총가용예산"] = dash_df[alloc_col].astype(int) + dash_df[carry_col].astype(int)
    dash_df["지출액"] = dash_df["지출액"].astype(int)
    dash_df["잔액"] = dash_df["총가용예산"] - dash_df["지출액"]
    dash_df["집행률(%)"] = np.where(dash_df["총가용예산"] > 0, (dash_df["지출액"] / dash_df["총가용예산"] * 100).round(1), 0.0)
    dash_df["상태"] = dash_df["집행률(%)"].apply(lambda r: "🔴 초과집행" if r > 100 else ("🟡 집행임박" if r >= 85 else "🟢 정상"))
    
    col_l, col_r = st.columns([1.1, 0.9])
    
    with col_l:
        st.markdown(f"#### 🏢 세부 과제별 {selected_year_str} 집행 현황")
        view_dash = safe_get_columns(dash_df, ["과제코드", "과제/사업단명", "책임자", "총가용예산", "지출액", "잔액", "집행률(%)", "상태"])
        st.dataframe(
            view_dash,
            use_container_width=True,
            column_config={
                "총가용예산": st.column_config.NumberColumn("가용예산합계", format="₩%,d"),
                "지출액": st.column_config.NumberColumn("지출액합계", format="₩%,d"),
                "잔액": st.column_config.NumberColumn("잔액합계", format="₩%,d"),
                "집행률(%)": st.column_config.ProgressColumn("집행률", format="%.1f%%", min_value=0, max_value=100)
            },
            hide_index=True
        )
        
        st.markdown("##### 🔍 선택한 과제 상세페이지로 즉시 이동")
        p_list_dash = dash_df["과제/사업단명"].tolist() if not dash_df.empty else []
        if p_list_dash:
            c_select_p, c_btn_jump = st.columns([2.5, 1])
            with c_select_p:
                jump_p_name = st.selectbox("상세 관리할 과제를 선택하세요", options=p_list_dash, key="dash_jump_selectbox")
            with c_btn_jump:
                st.write("") 
                if st.button("🚀 상세 관리로 이동", key="btn_jump_to_detail"):
                    st.session_state["selected_project_nav"] = jump_p_name
                    st.session_state["menu_selection"] = "🔍 과제별 상세 관리"
                    st.rerun()

    with col_r:
        st.markdown(f"#### 📈 {selected_year_str} 예산 vs 지출 비교")
        if not dash_df.empty:
            fig = px.bar(
                dash_df,
                y="과제코드",
                x=["총가용예산", "지출액"],
                barmode="group",
                orientation="h",
                labels={"value": "금액(원)", "variable": "구분", "과제코드": "과제코드"},
                color_discrete_map={"총가용예산": "#1B365D", "지출액": "#0F766E"}
            )
            fig.update_traces(hovertemplate="%{y}<br>₩%{x:,.0f}<extra></extra>")
            st.plotly_chart(style_fig(fig, h=420), use_container_width=True)

    st.divider()
    st.markdown(f"#### 🏷️ [{cur_b}] 비목/보조비목/보조세목별 {selected_year_str} 통합 현황")
    
    if not bd_b_df.empty and all(c in bd_b_df.columns for c in ["비목", "보조비목", "보조세목", alloc_col, carry_col]):
        bd_b_df["세목_가용예산"] = bd_b_df[alloc_col].fillna(0).astype(int) + bd_b_df[carry_col].fillna(0).astype(int)
        global_bd_sum = bd_b_df.groupby(["비목", "보조비목", "보조세목"])["세목_가용예산"].sum().reset_index()
    else:
        global_bd_sum = pd.DataFrame(columns=["비목", "보조비목", "보조세목", "세목_가용예산"])
        
    if not e_b_df.empty and all(c in e_b_df.columns for c in ["비목", "보조비목", "보조세목", "지출액"]):
        global_exp_sum = e_b_df.groupby(["비목", "보조비목", "보조세목"])["지출액"].sum().reset_index()
    else:
        global_exp_sum = pd.DataFrame(columns=["비목", "보조비목", "보조세목", "지출액"])
    
    global_cat_merged = pd.merge(
        global_bd_sum, global_exp_sum, on=["비목", "보조비목", "보조세목"], how="outer"
    ).fillna({"세목_가용예산": 0, "지출액": 0})
    
    global_cat_merged["세목_가용예산"] = pd.to_numeric(global_cat_merged["세목_가용예산"], errors="coerce").fillna(0).astype(int)
    global_cat_merged["지출액"] = pd.to_numeric(global_cat_merged["지출액"], errors="coerce").fillna(0).astype(int)
    global_cat_merged["잔액"] = global_cat_merged["세목_가용예산"] - global_cat_merged["지출액"]
    global_cat_merged["집행률(%)"] = np.where(global_cat_merged["세목_가용예산"] > 0, (global_cat_merged["지출액"] / global_cat_merged["세목_가용예산"] * 100).round(1), 0.0)
    
    col_cat_t, col_cat_c = st.columns([1.1, 0.9])
    
    with col_cat_t:
        view_global_cat = safe_get_columns(global_cat_merged, ["비목", "보조비목", "보조세목", "세목_가용예산", "지출액", "잔액", "집행률(%)"])
        st.dataframe(
            view_global_cat,
            use_container_width=True,
            column_config={
                "세목_가용예산": st.column_config.NumberColumn("가용예산", format="₩%,d"),
                "지출액": st.column_config.NumberColumn("총 지출액", format="₩%,d"),
                "잔액": st.column_config.NumberColumn("잔액", format="₩%,d"),
                "집행률(%)": st.column_config.ProgressColumn("집행률", format="%.1f%%", min_value=0, max_value=100)
            },
            hide_index=True
        )
        
    with col_cat_c:
        viz_tab1, viz_tab2 = st.tabs(["🍩 비목별 지출 비율", "🗺️ 지출 트리맵"])
        with viz_tab1:
            if not global_cat_merged.empty and global_cat_merged["지출액"].sum() > 0:
                fig_pie = px.pie(
                    global_cat_merged, values="지출액", names="비목", hole=0.55,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                fig_pie.add_annotation(text=f"총 지출<br><b>{won(global_cat_merged['지출액'].sum())}</b>", showarrow=False, font=dict(size=13))
                st.plotly_chart(style_fig(fig_pie, h=330, showlegend=False), use_container_width=True)
            else:
                st.info("💡 지출 데이터가 없어 차트를 표시할 수 없습니다.")
        with viz_tab2:
            if not e_b_df.empty and e_b_df["지출액"].sum() > 0:
                tree_src = e_b_df.copy()
                for c in ["비목", "보조비목", "과제/사업단명"]:
                    if c in tree_src.columns: tree_src[c] = tree_src[c].replace("", "(미지정)").fillna("(미지정)")
                fig_tree = px.treemap(tree_src, path=["비목", "보조비목", "과제/사업단명"], values="지출액", color="지출액", color_continuous_scale="Teal")
                fig_tree.update_traces(hovertemplate="%{label}<br>₩%{value:,.0f}<extra></extra>")
                st.plotly_chart(style_fig(fig_tree, h=330, showlegend=False), use_container_width=True)
            else:
                st.info("💡 지출 데이터가 없어 트리맵을 표시할 수 없습니다.")

# ----------------------------------------------------
# PAGE 2: 🔍 과제별 상세 관리
# ----------------------------------------------------
elif st.session_state["menu_selection"] == "🔍 과제별 상세 관리":
    st.markdown(f'<div class="sec-title">🔍 [{cur_b}] 과제별 예산 & 지출 상세 관리</div>', unsafe_allow_html=True)
    st.info("💡 왼쪽 패널에서 선택한 연도의 배정예산, 이월금, 지출내역만을 실시간으로 조회하고 수정합니다.")
    
    p_df = st.session_state["budget_projects"]
    e_df = st.session_state["expenses"]
    bd_df = st.session_state["budget_details"]
    
    p_b_df = p_df[p_df["사업명"] == cur_b].copy() if not p_df.empty else pd.DataFrame()
    e_b_df = e_df[(e_df["사업명"] == cur_b) & (e_df["집행차수"] == selected_year_str)].copy() if not e_df.empty else pd.DataFrame()
    bd_b_df = bd_df[bd_df["사업명"] == cur_b].copy() if not bd_df.empty else pd.DataFrame()
    
    proj_names = p_b_df["과제/사업단명"].tolist() if not p_b_df.empty else ["등록된 과제 없음"]
    
    default_index = 0
    if st.session_state["selected_project_nav"] in proj_names:
        default_index = proj_names.index(st.session_state["selected_project_nav"])
        
    selected_proj = st.selectbox("🎯 상세 관리할 과제/사업단 선택", proj_names, index=default_index, key="detail_proj_selectbox")
    st.session_state["selected_project_nav"] = selected_proj
    
    if selected_proj and selected_proj != "등록된 과제 없음":
        proj_info = p_b_df[p_b_df["과제/사업단명"] == selected_proj].iloc[0]
        proj_code = str(proj_info.get("과제코드", ""))
        proj_leader = str(proj_info.get("책임자", ""))
        
        alloc_col = f"배정예산액_{active_year}차"
        carry_col = f"이월금_{active_year}차"
        
        proj_alloc = int(proj_info.get(alloc_col, 0))
        proj_carry = int(proj_info.get(carry_col, 0))
        proj_note = str(proj_info.get("비고", ""))
        
        proj_exp = e_b_df[e_b_df["과제/사업단명"] == selected_proj].copy() if not e_b_df.empty else pd.DataFrame()
        if "재원구분" not in proj_exp.columns: proj_exp["재원구분"] = "당해 배정액"
        
        exp_alloc_spent = int(proj_exp[proj_exp["재원구분"] == "당해 배정액"]["지출액"].sum()) if not proj_exp.empty else 0
        exp_carry_spent = int(proj_exp[proj_exp["재원구분"] == "전년 이월금"]["지출액"].sum()) if not proj_exp.empty else 0
        
        st.markdown(f"### 📌 [{proj_code}] {selected_proj}")
        st.caption(f"**과제 책임자:** {proj_leader if proj_leader else '미지정'} | **비고/메모:** {proj_note if proj_note else '없음'}")
        
        st.markdown(render_separated_budget_status(proj_alloc, proj_carry, exp_alloc_spent, exp_carry_spent), unsafe_allow_html=True)
            
        p_tab1, p_tab2, p_tab3, p_tab4 = st.tabs([
            f"📊 {selected_year_str} 세목 예산 관리",
            f"📝 {selected_year_str} 지출 내역",
            "➕ 이 과제에 지출 추가",
            "⚙️ 이 과제 기본정보 수정"
        ])
        
        with p_tab1:
            st.markdown(f"##### 📊 '{selected_proj}' 비목 · 보조세목별 {selected_year_str} 편성 & 집행 현황")
            st.caption("💡 **표에서 행(Row) 가장 앞쪽 빈 칸을 선택한 후 키보드의 Delete 키를 누르고 '💾 저장'을 클릭**하면 해당 연도의 세목 예산이 0원으로 초기화(삭제)됩니다. 다른 연도에는 영향을 주지 않습니다.")
            
            proj_bd = bd_b_df[bd_b_df["과제/사업단명"] == selected_proj].copy() if not bd_b_df.empty else pd.DataFrame()
            
            if not proj_exp.empty:
                e_alloc = proj_exp[proj_exp["재원구분"] == "당해 배정액"].groupby(["비목", "보조비목", "보조세목"])["지출액"].sum().reset_index().rename(columns={"지출액": "배정지출액"})
                e_carry = proj_exp[proj_exp["재원구분"] == "전년 이월금"].groupby(["비목", "보조비목", "보조세목"])["지출액"].sum().reset_index().rename(columns={"지출액": "이월지출액"})
            else:
                e_alloc = pd.DataFrame(columns=["비목", "보조비목", "보조세목", "배정지출액"])
                e_carry = pd.DataFrame(columns=["비목", "보조비목", "보조세목", "이월지출액"])
            
            if not proj_bd.empty:
                mask_active = (pd.to_numeric(proj_bd[alloc_col], errors="coerce").fillna(0) > 0) | \
                              (pd.to_numeric(proj_bd[carry_col], errors="coerce").fillna(0) > 0)
                proj_bd_active = proj_bd[mask_active].copy()
            else:
                proj_bd_active = pd.DataFrame()
                
            proj_bd_sub = safe_get_columns(proj_bd_active, ["비목", "보조비목", "보조세목", alloc_col, carry_col, "비고"])
            
            merged_cat_proj = pd.merge(proj_bd_sub, e_alloc, on=["비목", "보조비목", "보조세목"], how="outer")
            merged_cat_proj = pd.merge(merged_cat_proj, e_carry, on=["비목", "보조비목", "보조세목"], how="outer")
            merged_cat_proj = merged_cat_proj.fillna({alloc_col: 0, carry_col: 0, "배정지출액": 0, "이월지출액": 0, "비고": ""})
            
            merged_cat_proj[alloc_col] = pd.to_numeric(merged_cat_proj[alloc_col], errors="coerce").fillna(0).astype(int)
            merged_cat_proj[carry_col] = pd.to_numeric(merged_cat_proj[carry_col], errors="coerce").fillna(0).astype(int)
            
            merged_cat_proj["세목가용예산"] = merged_cat_proj[alloc_col] + merged_cat_proj[carry_col]
            merged_cat_proj["총지출액"] = merged_cat_proj["배정지출액"] + merged_cat_proj["이월지출액"]
            merged_cat_proj["배정잔액"] = merged_cat_proj[alloc_col] - merged_cat_proj["배정지출액"]
            merged_cat_proj["이월잔액"] = merged_cat_proj[carry_col] - merged_cat_proj["이월지출액"]
            merged_cat_proj["총잔액"] = merged_cat_proj["세목가용예산"] - merged_cat_proj["총지출액"]
            merged_cat_proj["집행률(%)"] = np.where(merged_cat_proj["세목가용예산"] > 0, (merged_cat_proj["총지출액"] / merged_cat_proj["세목가용예산"] * 100).round(1), 0.0)
            
            st.markdown("###### 🔍 [조회] 세목별 당해배정 및 이월금 대비 지출 현황")
            view_summary_cat = safe_get_columns(merged_cat_proj, ["비목", "보조비목", "보조세목", alloc_col, "배정지출액", carry_col, "이월지출액", "총잔액", "집행률(%)"])
            st.dataframe(
                view_summary_cat,
                use_container_width=True,
                column_config={
                    alloc_col: st.column_config.NumberColumn("당해배정", format="₩%,d"),
                    "배정지출액": st.column_config.NumberColumn("당해배정 지출", format="₩%,d"),
                    carry_col: st.column_config.NumberColumn("전년이월", format="₩%,d"),
                    "이월지출액": st.column_config.NumberColumn("전년이월 지출", format="₩%,d"),
                    "총잔액": st.column_config.NumberColumn("총 잔액", format="₩%,d"),
                    "집행률(%)": st.column_config.ProgressColumn("집행률", format="%.1f%%", min_value=0, max_value=100)
                },
                hide_index=True
            )
            
            st.divider()
            st.markdown("###### ✏️ [수정] 세목별 예산 배정액 & 이월금 편집 표")
            
            bimok_opts = get_bimok_list()
            c_df = st.session_state["categories"]
            all_bojo_bimoks = c_df["보조비목"].dropna().unique().tolist() if not c_df.empty and "보조비목" in c_df.columns else ["일반수용비"]
            all_bojo_semoks = c_df["보조세목"].dropna().unique().tolist() if not c_df.empty and "보조세목" in c_df.columns else ["일반수용비(3)"]
            
            editable_bd = safe_get_columns(proj_bd_active, ["비목", "보조비목", "보조세목", alloc_col, carry_col, "비고"]).reset_index(drop=True)
            
            edited_bd_proj = st.data_editor(
                editable_bd,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "비목": st.column_config.SelectboxColumn("비목", options=bimok_opts),
                    "보조비목": st.column_config.SelectboxColumn("보조비목", options=all_bojo_bimoks),
                    "보조세목": st.column_config.SelectboxColumn("보조세목", options=all_bojo_semoks),
                    alloc_col: st.column_config.NumberColumn("당해배정예산(원)", format="₩%,d", min_value=0, step=100000, default=0),
                    carry_col: st.column_config.NumberColumn("전년이월금(원)", format="₩%,d", min_value=0, step=100000, default=0),
                    "비고": st.column_config.TextColumn("비고 메모")
                },
                key=f"editor_cat_bd_{cur_b}_{selected_proj}_{active_year}"
            )
            
            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button(f"💾 {selected_year_str} 세목 예산 및 이월금 저장", key="btn_save_proj_bd"):
                    main_bd = st.session_state["budget_details"].copy()
                    
                    # 1. 🗑️ 삭제된 항목의 당해년도 예산만 0으로 초기화
                    view_keys = set(editable_bd["비목"].fillna("") + "|" + editable_bd["보조비목"].fillna("") + "|" + editable_bd["보조세목"].fillna(""))
                    edited_keys = set(edited_bd_proj["비목"].fillna("") + "|" + edited_bd_proj["보조비목"].fillna("") + "|" + edited_bd_proj["보조세목"].fillna(""))
                    deleted_keys = view_keys - edited_keys
                    
                    mask_proj = (main_bd["사업명"] == cur_b) & (main_bd["과제/사업단명"] == selected_proj)
                    for m_idx, m_row in main_bd[mask_proj].iterrows():
                        m_key = str(m_row.get("비목","")).strip() + "|" + str(m_row.get("보조비목","")).strip() + "|" + str(m_row.get("보조세목","")).strip()
                        if m_key in deleted_keys:
                            main_bd.loc[m_idx, alloc_col] = 0
                            main_bd.loc[m_idx, carry_col] = 0
                            
                    # 2. 업데이트 및 신규 추가
                    for idx, row in edited_bd_proj.iterrows():
                        bimok_val = str(row.get("비목", "")).strip()
                        if not bimok_val: continue
                        bb_val = str(row.get("보조비목", "")).strip()
                        bs_val = str(row.get("보조세목", "")).strip()
                        
                        match = main_bd[
                            (main_bd["사업명"] == cur_b) & (main_bd["과제/사업단명"] == selected_proj) & 
                            (main_bd["비목"] == bimok_val) & (main_bd["보조비목"] == bb_val) & (main_bd["보조세목"] == bs_val)
                        ]
                        
                        new_alloc = pd.to_numeric(row.get(alloc_col, 0), errors="coerce")
                        new_carry = pd.to_numeric(row.get(carry_col, 0), errors="coerce")
                        if pd.isna(new_alloc): new_alloc = 0
                        if pd.isna(new_carry): new_carry = 0
                        
                        if not match.empty:
                            m_idx = match.index[0]
                            main_bd.loc[m_idx, alloc_col] = int(new_alloc)
                            main_bd.loc[m_idx, carry_col] = int(new_carry)
                            main_bd.loc[m_idx, "비고"] = str(row.get("비고", "")).strip()
                        else:
                            new_row = {
                                "사업명": cur_b, "과제/사업단명": selected_proj, "비목": bimok_val, 
                                "보조비목": bb_val, "보조세목": bs_val, 
                                alloc_col: int(new_alloc), carry_col: int(new_carry), 
                                "비고": str(row.get("비고", "")).strip()
                            }
                            # 다른 차수 기본값 0 채우기
                            for y in range(1, 6):
                                if y != active_year:
                                    new_row[f"배정예산액_{y}차"] = 0
                                    new_row[f"이월금_{y}차"] = 0
                            main_bd = pd.concat([main_bd, pd.DataFrame([new_row])], ignore_index=True)
                            
                    st.session_state["budget_details"] = clean_budget_details(main_bd, cur_b)
                    save_and_sync_all(f"✅ '{selected_proj}' {selected_year_str} 예산이 안전하게 저장되었습니다!")
                    st.rerun()
                    
            with c_btn2:
                if st.button("🔄 이전 연도 잔액을 이월금으로 자동 편성하기"):
                    p_df, bd_df = auto_calculate_carryovers(st.session_state["budget_projects"], st.session_state["budget_details"], st.session_state["expenses"], cur_b)
                    st.session_state["budget_projects"] = p_df
                    st.session_state["budget_details"] = bd_df
                    save_and_sync_all("✅ 전년도 예산 잔액이 이월금으로 자동 일괄 반영되었습니다!")
                    st.rerun()

            with st.expander("🗑️ 세목 예산 편성 목록에서 직접 선택하여 삭제하기", expanded=False):
                st.caption(f"아래 목록에서 삭제할 항목을 선택하면 **{selected_year_str}에서만 0원 처리**되며, 다른 연도의 예산은 유지됩니다.")
                bd_now_filtered = st.session_state["budget_details"]
                bd_now_filtered = bd_now_filtered[(bd_now_filtered["사업명"] == cur_b) & (bd_now_filtered["과제/사업단명"] == selected_proj)]
                
                mask_has_budget = (pd.to_numeric(bd_now_filtered[alloc_col], errors="coerce").fillna(0) > 0) | \
                                  (pd.to_numeric(bd_now_filtered[carry_col], errors="coerce").fillna(0) > 0)
                bd_now_filtered = bd_now_filtered[mask_has_budget]
                
                if bd_now_filtered.empty:
                    st.info(f"현재 {selected_year_str}에 배정된 세목 예산이 없습니다.")
                else:
                    del_bd_opts = {
                        f"[{r['비목']} > {r['보조세목']}] 당해배정: {won(r.get(alloc_col, 0))} / 전년이월: {won(r.get(carry_col, 0))}": idx
                        for idx, r in bd_now_filtered.iterrows()
                    }
                    selected_del_bd = st.multiselect("삭제할 항목 선택", list(del_bd_opts.keys()), key="del_bd_multi")
                    del_confirm_bd = st.checkbox("네, 선택한 항목의 당해년도 예산을 삭제(0원)합니다. (필수 체크)", key="chk_del_bd_confirm")
                    if st.button("🔴 선택 세목 삭제 실행", disabled=(not selected_del_bd or not del_confirm_bd), key="btn_del_bd_multi"):
                        drop_idxs = [del_bd_opts[k] for k in selected_del_bd]
                        for m_idx in drop_idxs:
                            st.session_state["budget_details"].loc[m_idx, alloc_col] = 0
                            st.session_state["budget_details"].loc[m_idx, carry_col] = 0
                        st.session_state["budget_details"] = clean_budget_details(st.session_state["budget_details"], cur_b)
                        save_and_sync_all(f"🗑️ 선택한 세목 예산이 {selected_year_str}에서 삭제되었습니다.")
                        st.rerun()

        with p_tab2:
            st.markdown(f"##### 📝 '{selected_proj}' 지출 내역 ({selected_year_str} 필터됨)")
            st.caption("💡 **표에서 지울 행(Row)을 선택한 후 키보드의 Delete 키를 누르고 '💾 지출 내역 변경사항 저장'을 클릭**하면 해당 내역이 완전히 삭제됩니다. 또는 하단의 목록 선택 삭제를 이용하세요.")
            
            view_proj_exp = safe_get_columns(proj_exp, ["No", "재원구분", "지출일자", "비목", "보조비목", "보조세목", "지출액", "지출처/적요", "지급상태", "비고"]).reset_index(drop=True)
            
            # 연번 숨김 처리 및 삭제 추적용 리스트
            displayed_exp_nos_p2 = [int(x) for x in pd.to_numeric(view_proj_exp["No"], errors="coerce").dropna().tolist()] if "No" in view_proj_exp.columns else []

            bimoks = get_bimok_list()
            c_df = st.session_state["categories"]
            all_bojo_bimoks = c_df["보조비목"].dropna().unique().tolist() if not c_df.empty and "보조비목" in c_df.columns else ["일반수용비"]
            all_bojo_semoks = c_df["보조세목"].dropna().unique().tolist() if not c_df.empty and "보조세목" in c_df.columns else ["일반수용비(3)"]
            
            if not view_proj_exp.empty and "No" in view_proj_exp.columns:
                view_proj_exp["No"] = pd.to_numeric(view_proj_exp["No"], errors="coerce").fillna(0).astype(int)
                view_proj_exp_indexed = view_proj_exp.set_index("No")
            else:
                view_proj_exp_indexed = view_proj_exp
                
            edited_exp_p2 = st.data_editor(
                view_proj_exp,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "No": None, # 화면에서 완벽하게 숨김
                    "재원구분": st.column_config.SelectboxColumn("재원구분", options=["당해 배정액", "전년 이월금"]),
                    "지출액": st.column_config.NumberColumn("지출액(원)", min_value=0, step=1000, format="₩%,d"),
                    "비목": st.column_config.SelectboxColumn("비목", options=bimoks),
                    "보조비목": st.column_config.SelectboxColumn("보조비목", options=all_bojo_bimoks),
                    "보조세목": st.column_config.SelectboxColumn("보조세목", options=all_bojo_semoks),
                    "지급상태": st.column_config.SelectboxColumn("지급상태", options=["지급완료", "결재대기", "보완요청", "지급취소"])
                },
                key=f"editor_{cur_b}_{selected_proj}_{active_year}"
            )
            
            if st.button(f"💾 이 과제의 {selected_year_str} 지출 내역 저장", key="btn_save_proj_exp"):
                main_e = st.session_state["expenses"].copy()
                
                # 🗑️ 삭제 감지
                edited_no_series = pd.to_numeric(edited_exp_p2.get("No", pd.Series(dtype=float)), errors="coerce")
                remaining_nos = set(int(x) for x in edited_no_series.dropna().tolist())
                deleted_nos = [n for n in displayed_exp_nos_p2 if n not in remaining_nos]
                
                if deleted_nos:
                    main_e = main_e[~main_e["No"].isin(deleted_nos)].reset_index(drop=True)
                
                edited_clean_exp = clean_expenses(edited_exp_p2, cur_b)
                edited_clean_exp["사업명"] = cur_b
                edited_clean_exp["과제/사업단명"] = selected_proj
                edited_clean_exp["집행차수"] = selected_year_str
                
                max_no = main_e["No"].max() if (not main_e.empty and "No" in main_e.columns) else 0
                if max_no <= 0: max_no = 0
                    
                for idx, row in edited_clean_exp.iterrows():
                    if row["No"] <= 0 or (row["No"] in main_e["No"].values and not (view_proj_exp["No"] == row["No"]).any()):
                        max_no += 1
                        edited_clean_exp.loc[idx, "No"] = max_no
                
                mask = (main_e["사업명"] == cur_b) & (main_e["과제/사업단명"] == selected_proj) & (main_e["집행차수"] == selected_year_str)
                cand_main_e = pd.concat([main_e[~mask], edited_clean_exp], ignore_index=True)
                
                is_valid, errs = validate_all_expenses_against_budgets(cand_main_e, st.session_state["budget_projects"], st.session_state["budget_details"])
                
                if not is_valid:
                    error_msg = "🚫 **[지출 초과 오류]** 수정하신 지출 내역이 예산을 초과하여 저장할 수 없습니다!\n\n"
                    for e in errs: error_msg += f"{e}\n"
                    st.error(error_msg)
                else:
                    st.session_state["expenses"] = clean_expenses(cand_main_e, cur_b)
                    save_and_sync_all("✅ 지출 내역이 성공적으로 저장 및 연동되었습니다!")
                    st.rerun()
                    
            with st.expander("🗑️ 지출 내역 목록에서 직접 선택하여 삭제하기", expanded=False):
                st.caption("위 표에서 지우는 대신 아래 목록에서 여러 항목을 직접 선택하여 안전하게 완전히 지울 수도 있습니다.")
                if proj_exp.empty:
                    st.info("삭제할 수 있는 지출 내역이 없습니다.")
                else:
                    del_exp_opts = {
                        f"[{r.get('재원구분', '당해 배정액')}] {r['지출일자']} | {r['비목']}>{r['보조세목']} | ₩{int(r['지출액']):,}": int(r["No"])
                        for _, r in proj_exp.iterrows()
                    }
                    selected_del_exp = st.multiselect("삭제할 지출 항목 선택", list(del_exp_opts.keys()), key="exp_del_multi_p2")
                    del_confirm_exp_p2 = st.checkbox(f"네, 선택한 {len(selected_del_exp)}건의 지출 내역을 완전히 삭제합니다. (필수 체크)", key="chk_del_exp_p2")
                    if st.button(f"🔴 선택 지출 내역 {len(selected_del_exp)}건 삭제 실행", disabled=(not del_confirm_exp_p2 or not selected_del_exp), key="btn_del_exp_p2"):
                        del_exp_nos = [del_exp_opts[lbl] for lbl in selected_del_exp]
                        all_e_now = st.session_state["expenses"]
                        st.session_state["expenses"] = all_e_now[~all_e_now["No"].isin(del_exp_nos)].reset_index(drop=True)
                        save_and_sync_all(f"🗑️ 지출 내역 {len(del_exp_nos)}건이 완전히 삭제되었습니다.")
                        st.rerun()

        with p_tab3:
            st.markdown(f"##### ➕ '{selected_proj}' 전용 {selected_year_str} 지출 등록")
            
            cat_c1, cat_c2, cat_c3 = st.columns(3)
            with cat_c1:
                p_bimok = st.selectbox("비목 (대분류)", options=get_bimok_list(), key=f"p_bimok_{selected_proj}")
            with cat_c2:
                p_bojo_bimok_opts = get_bojo_bimok_list(p_bimok)
                p_bojo_bimok = st.selectbox("보조비목 (중분류)", options=p_bojo_bimok_opts, key=f"p_bojo_{selected_proj}")
            with cat_c3:
                p_bojo_semok_opts = get_bojo_semok_list(p_bimok, p_bojo_bimok)
                p_bojo_semok = st.selectbox("보조세목 (소분류)", options=p_bojo_semok_opts, key=f"p_semok_{selected_proj}")
                
            with st.form(key=f"form_add_{selected_proj}"):
                fc1, fc2 = st.columns(2)
                with fc1:
                    ins_date = st.date_input("지출일자", datetime.now())
                    ins_amount = st.number_input("지출 금액 (원)", min_value=0, step=10000, value=50000)
                    ins_fund = st.selectbox("재원 구분 (예산 출처)", ["당해 배정액", "전년 이월금"])
                with fc2:
                    ins_status = st.selectbox("지급 상태", ["지급완료", "결재대기", "보완요청", "지급취소"])
                    ins_desc = st.text_input("지출처 / 적요 내용", placeholder="예: 사업 관련 연구자문료 지급")
                    ins_note = st.text_input("비고", placeholder="예: 법인카드 결제")
                    
                sub_btn = st.form_submit_button("🚀 이 과제에 지출 등록")
                
                if sub_btn:
                    is_valid, err_msg = check_single_expense_budget_limit(
                        cur_b, selected_proj, ins_fund, int(ins_amount), st.session_state["expenses"],
                        st.session_state["budget_projects"], st.session_state["budget_details"], active_year,
                        bimok=p_bimok, bojo_bimok=p_bojo_bimok, bojo_semok=p_bojo_semok
                    )
                    
                    if not is_valid:
                        error_lines = err_msg.split('\n')
                        for line in error_lines: st.error(line)
                    else:
                        main_e = st.session_state["expenses"].copy()
                        max_no = main_e["No"].max() if not main_e.empty else 0
                        new_row = {
                            "No": int(max_no) + 1, "집행차수": selected_year_str, "재원구분": ins_fund, "지출일자": str(ins_date),
                            "사업명": cur_b, "과제/사업단명": selected_proj, "비목": p_bimok, "보조비목": p_bojo_bimok,
                            "보조세목": p_bojo_semok, "지출액": int(ins_amount), "지출처/적요": ins_desc,
                            "지급상태": ins_status, "비고": ins_note
                        }
                        st.session_state["expenses"] = pd.concat([main_e, pd.DataFrame([new_row])], ignore_index=True)
                        save_and_sync_all(f"✅ '{selected_proj}' 과제에 ₩{ins_amount:,.0f} 지출이 등록되었습니다!")
                        st.rerun()

        with p_tab4:
            st.markdown(f"##### ⚙️ '{selected_proj}' 과제 기본 정보 및 {selected_year_str} 예산/이월금 수정")
            with st.form(key=f"form_edit_proj_info"):
                ec1, ec2, ec3 = st.columns([1,1,1])
                with ec1:
                    new_code = st.text_input("과제 코드", value=proj_code)
                    new_name = st.text_input("과제 / 사업단명", value=selected_proj)
                    new_leader = st.text_input("과제 책임자", value=proj_leader)
                with ec2:
                    new_alloc = st.number_input(f"당해 배정예산 ({active_year}차)", min_value=0, step=1000000, value=proj_alloc)
                    new_carry = st.number_input(f"전년 이월금 ({active_year}차)", min_value=0, step=1000000, value=proj_carry)
                with ec3:
                    new_note = st.text_area("비고 메모", value=proj_note, height=108)
                    
                btn_upd_p = st.form_submit_button("💾 과제 정보 수정 저장")
                
                if btn_upd_p:
                    main_p = st.session_state["budget_projects"].copy()
                    idx = main_p[(main_p["사업명"] == cur_b) & (main_p["과제/사업단명"] == selected_proj)].index
                    if not idx.empty:
                        main_p.loc[idx[0], "과제코드"] = new_code
                        main_p.loc[idx[0], "과제/사업단명"] = new_name
                        main_p.loc[idx[0], "책임자"] = new_leader
                        main_p.loc[idx[0], alloc_col] = new_alloc
                        main_p.loc[idx[0], carry_col] = new_carry
                        main_p.loc[idx[0], "비고"] = new_note
                        
                        if new_name != selected_proj:
                            for state_key in ["expenses", "budget_details"]:
                                df_k = st.session_state[state_key].copy()
                                if not df_k.empty and "과제/사업단명" in df_k.columns:
                                    df_k.loc[(df_k["사업명"] == cur_b) & (df_k["과제/사업단명"] == selected_proj), "과제/사업단명"] = new_name
                                    st.session_state[state_key] = df_k
                            st.session_state["selected_project_nav"] = new_name
                            
                        st.session_state["budget_projects"] = main_p
                        save_and_sync_all("✅ 과제 예산 및 기본 정보가 성공적으로 수정되었습니다!")
                        st.rerun()

# ----------------------------------------------------
# PAGE 3: 💰 예산 편성 및 사업단 관리
# ----------------------------------------------------
elif st.session_state["menu_selection"] == "💰 예산 편성 및 사업단 관리":
    st.markdown(f'<div class="sec-title">💰 [{cur_b}] 과제 등록 및 {selected_year_str} 예산/이월금 총괄 관리</div>', unsafe_allow_html=True)
    st.info(f"💡 현재 **{selected_year_str}** 모드입니다. 전체 사업단의 당해년도 예산액과 이월금을 한눈에 확인하고 일괄 수정할 수 있습니다.")

    tab1, tab2, tab3 = st.tabs(["➕ 신규 과제/사업단 추가", f"✏️ {selected_year_str} 전체 예산/이월금 종합 수정", "🗑️ 과제 삭제"])
    
    p_b_df = st.session_state["budget_projects"][st.session_state["budget_projects"]["사업명"] == cur_b].copy() if not st.session_state["budget_projects"].empty else pd.DataFrame()
    
    with tab1:
        st.markdown(f"##### 📌 [{cur_b}] 신규 세부과제 등록")
        with st.form("add_project_form", clear_on_submit=True):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                p_code = st.text_input("과제 코드 (예: 4-3-12)")
                p_name = st.text_input("과제 / 사업단명")
            with col_b:
                p_leader = st.text_input("과제 책임자")
                p_alloc = st.number_input(f"{selected_year_str} 당해 배정액 (원)", min_value=0, step=1000000, value=10000000)
                p_carry = st.number_input(f"{selected_year_str} 전년 이월금 (원)", min_value=0, step=1000000, value=0)
            with col_c:
                p_note = st.text_area("비고 / 메모", height=108)
                
            submit_proj = st.form_submit_button("🚀 과제 등록 완료")
            if submit_proj:
                if not p_name and not p_code:
                    st.error("과제 코드 또는 과제/사업단명을 입력해주세요.")
                else:
                    new_proj = {"사업명": cur_b, "과제코드": p_code, "과제/사업단명": p_name, "책임자": p_leader, "비고": p_note}
                    for y in range(1, 6):
                        new_proj[f"배정예산액_{y}차"] = p_alloc if y == active_year else 0
                        new_proj[f"이월금_{y}차"] = p_carry if y == active_year else 0
                    
                    st.session_state["budget_projects"] = pd.concat([st.session_state["budget_projects"], pd.DataFrame([new_proj])], ignore_index=True)
                    save_and_sync_all(f"✅ '{p_name}' 과제가 성공적으로 등록되었습니다!")
                    st.rerun()

    with tab2:
        st.caption("💡 **표에서 행을 지우고 저장하면 해당 과제의 1~5차 전체 데이터가 삭제됩니다.** (단순 예산만 0원 처리하려면 표의 숫자를 0으로 바꾸어 저장하세요.)")
        alloc_c = f"배정예산액_{active_year}차"
        carry_c = f"이월금_{active_year}차"
        
        view_p_editable = safe_get_columns(p_b_df, ["과제코드", "과제/사업단명", "책임자", alloc_c, carry_c, "비고"]).reset_index(drop=True)
        
        edited_proj_df = st.data_editor(
            view_p_editable,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "과제코드": st.column_config.TextColumn("과제코드"),
                "과제/사업단명": st.column_config.TextColumn("과제/사업단명"),
                "책임자": st.column_config.TextColumn("책임자"),
                alloc_c: st.column_config.NumberColumn("당해배정예산(원)", format="₩%,d", min_value=0, step=100000),
                carry_c: st.column_config.NumberColumn("이월금(원)", format="₩%,d", min_value=0, step=100000),
                "비고": st.column_config.TextColumn("비고")
            },
            disabled=False,
            key=f"proj_editor_page3_{cur_b}_{active_year}"
        )
        
        c_btn1, c_btn2 = st.columns([1,1])
        with c_btn1:
            if st.button(f"💾 {selected_year_str} 과제별 예산/이월금 정보 저장"):
                main_p = st.session_state["budget_projects"].copy()
                
                # 🗑️ 삭제 감지 (과제 완전 삭제)
                view_names = set(view_p_editable["과제/사업단명"].dropna().tolist())
                edited_names = set(edited_proj_df["과제/사업단명"].dropna().tolist())
                deleted_names = view_names - edited_names
                
                if deleted_names:
                    main_p = main_p[~((main_p["사업명"] == cur_b) & (main_p["과제/사업단명"].isin(deleted_names)))]
                
                for idx, row in edited_proj_df.iterrows():
                    p_name_val = str(row.get("과제/사업단명", "")).strip()
                    if not p_name_val: continue
                    match = main_p[(main_p["사업명"] == cur_b) & (main_p["과제/사업단명"] == p_name_val)]
                    
                    new_alloc = pd.to_numeric(row.get(alloc_c, 0), errors="coerce")
                    new_carry = pd.to_numeric(row.get(carry_c, 0), errors="coerce")
                    if pd.isna(new_alloc): new_alloc = 0
                    if pd.isna(new_carry): new_carry = 0
                    
                    if not match.empty:
                        m_idx = match.index[0]
                        main_p.loc[m_idx, "과제코드"] = str(row.get("과제코드", ""))
                        main_p.loc[m_idx, "책임자"] = str(row.get("책임자", ""))
                        main_p.loc[m_idx, alloc_c] = int(new_alloc)
                        main_p.loc[m_idx, carry_c] = int(new_carry)
                        main_p.loc[m_idx, "비고"] = str(row.get("비고", ""))
                    else:
                        new_row = {"사업명": cur_b, "과제/사업단명": p_name_val, "과제코드": str(row.get("과제코드", "")), "책임자": str(row.get("책임자", "")), alloc_c: int(new_alloc), carry_c: int(new_carry), "비고": str(row.get("비고", ""))}
                        for y in range(1, 6):
                            if y != active_year:
                                new_row[f"배정예산액_{y}차"] = 0
                                new_row[f"이월금_{y}차"] = 0
                        main_p = pd.concat([main_p, pd.DataFrame([new_row])], ignore_index=True)
                
                st.session_state["budget_projects"] = clean_budget_projects(main_p, cur_b)
                save_and_sync_all("✅ 예산 편성 정보가 업데이트되었습니다!")
                st.rerun()
                
        with c_btn2:
            if st.button("🔄 전년도 잔액을 이월금으로 일괄 자동 계산하기"):
                p_df, bd_df = auto_calculate_carryovers(st.session_state["budget_projects"], st.session_state["budget_details"], st.session_state["expenses"], cur_b)
                st.session_state["budget_projects"] = p_df
                st.session_state["budget_details"] = bd_df
                save_and_sync_all("✅ 전년도 예산 잔액이 이월금으로 자동 일괄 반영되었습니다!")
                st.rerun()

    with tab3:
        st.markdown(f"##### 🗑️ [{cur_b}] 세부과제 삭제")
        p_opts = p_b_df["과제/사업단명"].tolist() if not p_b_df.empty else []
        if not p_opts:
            st.info("삭제할 수 있는 과제가 없습니다.")
        else:
            del_target = st.selectbox("삭제할 과제/사업단 선택", p_opts, key="del_tab_select_p3")
            del_exp_flag = st.checkbox("해당 과제의 세목 예산 및 지출 내역도 함께 삭제하기", value=True, key="del_tab_check_p3")
            del_confirm_p3 = st.checkbox("네, 삭제 내용을 확인했습니다. (필수 체크)", key="chk_del_proj_p3")
            if st.button("🔴 과제 삭제 실행", key="btn_del_tab_p3", disabled=not del_confirm_p3):
                main_p = st.session_state["budget_projects"]
                st.session_state["budget_projects"] = main_p[~((main_p["사업명"] == cur_b) & (main_p["과제/사업단명"] == del_target))]
                if del_exp_flag:
                    main_e = st.session_state["expenses"]
                    st.session_state["expenses"] = main_e[~((main_e["사업명"] == cur_b) & (main_e["과제/사업단명"] == del_target))]
                    main_bd = st.session_state["budget_details"]
                    st.session_state["budget_details"] = main_bd[~((main_bd["사업명"] == cur_b) & (main_bd["과제/사업단명"] == del_target))]
                save_and_sync_all(f"🗑️ '{del_target}' 과제가 정상적으로 삭제되었습니다.")
                st.rerun()

# ----------------------------------------------------
# PAGE 4: 📝 지출 내역 입력 및 수정
# ----------------------------------------------------
elif st.session_state["menu_selection"] == "📝 지출 내역 입력 및 수정":
    st.markdown(f'<div class="sec-title">📝 [{cur_b}] 전체 지출 내역 입력 및 통합 관리</div>', unsafe_allow_html=True)

    tab_exp1, tab_exp2 = st.tabs(["➕ 신규 지출 등록 (예산 & 세목 연동)", "✏️ 전체 지출 내역 실시간 에디터"])

    p_b_df = st.session_state["budget_projects"][st.session_state["budget_projects"]["사업명"] == cur_b] if not st.session_state["budget_projects"].empty else pd.DataFrame()
    proj_list = p_b_df["과제/사업단명"].tolist() if not p_b_df.empty else ["선택가능 과제없음"]

    with tab_exp1:
        st.markdown(f"##### 📥 [{cur_b}] {selected_year_str} 신규 지출 등록 (실시간 배정액 · 현재 잔액 표시)")

        c_proj_select, c_space = st.columns([2, 1])
        with c_proj_select:
            e_proj = st.selectbox("🎯 관련 과제/사업단 선택", proj_list, key="main_input_eproj")

        p_df = st.session_state["budget_projects"]
        e_df = st.session_state["expenses"]
        bd_df = st.session_state["budget_details"]

        p_match = p_df[(p_df["사업명"] == cur_b) & (p_df["과제/사업단명"] == e_proj)] if not p_df.empty else pd.DataFrame()
        p_alloc = int(p_match.iloc[0][f"배정예산액_{active_year}차"]) if not p_match.empty and f"배정예산액_{active_year}차" in p_match.columns else 0
        p_carry = int(p_match.iloc[0][f"이월금_{active_year}차"]) if not p_match.empty and f"이월금_{active_year}차" in p_match.columns else 0
        p_budget = p_alloc + p_carry
        
        p_exp = e_df[(e_df["사업명"] == cur_b) & (e_df["과제/사업단명"] == e_proj) & (e_df["집행차수"] == selected_year_str)] if not e_df.empty else pd.DataFrame()
        p_alloc_spent = int(p_exp[p_exp["재원구분"] == "당해 배정액"]["지출액"].sum()) if not p_exp.empty else 0
        p_carry_spent = int(p_exp[p_exp["재원구분"] == "전년 이월금"]["지출액"].sum()) if not p_exp.empty else 0

        st.markdown("###### 💳 선택 과제 종합 예산 및 집행 현황")
        st.markdown(render_separated_budget_status(p_alloc, p_carry, p_alloc_spent, p_carry_spent), unsafe_allow_html=True)
        st.divider()

        st.markdown("###### 🏷️ 예산 세목 선택 (비목 ➔ 보조비목 ➔ 보조세목 연동)")
        cat_c1, cat_c2, cat_c3 = st.columns(3)
        with cat_c1:
            sel_bimok = st.selectbox("비목 (대분류)", options=get_bimok_list(), key="main_sel_bimok")
        with cat_c2:
            bojo_bimok_opts = get_bojo_bimok_list(sel_bimok)
            sel_bojo_bimok = st.selectbox("보조비목 (중분류)", options=bojo_bimok_opts, key="main_sel_bojo_bimok")
        with cat_c3:
            bojo_semok_opts = get_bojo_semok_list(sel_bimok, sel_bojo_bimok)
            sel_bojo_semok = st.selectbox("보조세목 (소분류)", options=bojo_semok_opts, key="main_sel_bojo_semok")

        cat_match = bd_df[
            (bd_df["사업명"] == cur_b) & (bd_df["과제/사업단명"] == e_proj) &
            (bd_df["비목"] == sel_bimok) & (bd_df["보조비목"] == sel_bojo_bimok) & (bd_df["보조세목"] == sel_bojo_semok)
        ] if not bd_df.empty else pd.DataFrame()

        c_alloc = int(cat_match.iloc[0][f"배정예산액_{active_year}차"]) if not cat_match.empty and f"배정예산액_{active_year}차" in cat_match.columns else 0
        c_carry = int(cat_match.iloc[0][f"이월금_{active_year}차"]) if not cat_match.empty and f"이월금_{active_year}차" in cat_match.columns else 0
        c_budget = c_alloc + c_carry
        
        cat_exp = p_exp[
            (p_exp["비목"] == sel_bimok) & (p_exp["보조비목"] == sel_bojo_bimok) & (p_exp["보조세목"] == sel_bojo_semok)
        ] if not p_exp.empty else pd.DataFrame()
        
        c_alloc_spent = int(cat_exp[cat_exp["재원구분"] == "당해 배정액"]["지출액"].sum()) if not cat_exp.empty else 0
        c_carry_spent = int(cat_exp[cat_exp["재원구분"] == "전년 이월금"]["지출액"].sum()) if not cat_exp.empty else 0
        c_balance = c_budget - (c_alloc_spent + c_carry_spent)

        if c_budget > 0:
            st.info(f"📌 **[{sel_bimok} > {sel_bojo_semok}] 세목 {selected_year_str} 예산 현황**\n"
                    f"• 당해 배정액: 가용 **{won(c_alloc)}** | 지출 **{won(c_alloc_spent)}** | 잔액 **{won(c_alloc - c_alloc_spent)}**\n\n"
                    f"• 전년 이월금: 가용 **{won(c_carry)}** | 지출 **{won(c_carry_spent)}** | 잔액 **{won(c_carry - c_carry_spent)}**")
        else:
            st.caption(f"ℹ️ 선택 세목의 별도 예산 편성이 없는 경우, 과제 전체 잔액 한도 내에서 지출할 수 있습니다.")

        st.divider()

        st.markdown("###### 📝 지출 상세 정보 입력")
        with st.form("add_expense_form_main", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                e_date = st.date_input("지출 일자", datetime.now())
                e_amount = st.number_input("지출 금액 (원)", min_value=0, step=10000, value=50000)
                e_fund = st.selectbox("재원 구분 (예산 출처)", ["당해 배정액", "전년 이월금"])
            with col2:
                e_status = st.selectbox("지급 상태", ["지급완료", "결재대기", "보완요청", "지급취소"])
                e_details = st.text_input("지출처 / 적요 내용", placeholder="예: 5월 실무협의회 회의비 결제")
            with col3:
                e_notes = st.text_input("비고 (증빙 구분 등)", placeholder="예: 법인카드 / E나라도움")
                st.write("")

            submit_exp = st.form_submit_button(f"🚀 이 과제에 {selected_year_str} 지출 등록")

            if submit_exp:
                is_valid, err_msg = check_single_expense_budget_limit(
                    cur_b, e_proj, e_fund, int(e_amount), st.session_state["expenses"],
                    st.session_state["budget_projects"], st.session_state["budget_details"], active_year,
                    bimok=sel_bimok, bojo_bimok=sel_bojo_bimok, bojo_semok=sel_bojo_semok
                )

                if not is_valid:
                    error_lines = err_msg.split('\n')
                    for line in error_lines: st.error(line)
                else:
                    main_e = st.session_state["expenses"].copy()
                    max_no = main_e["No"].max() if not main_e.empty else 0
                    new_exp = {
                        "No": int(max_no) + 1, "집행차수": selected_year_str, "재원구분": e_fund, "지출일자": str(e_date),
                        "사업명": cur_b, "과제/사업단명": e_proj, "비목": sel_bimok, "보조비목": sel_bojo_bimok,
                        "보조세목": sel_bojo_semok, "지출액": int(e_amount), "지출처/적요": ins_desc,
                        "지급상태": e_status, "비고": e_notes
                    }
                    st.session_state["expenses"] = pd.concat([main_e, pd.DataFrame([new_exp])], ignore_index=True)
                    save_and_sync_all(f"✅ '{selected_proj}' 과제에 ₩{ins_amount:,.0f} 지출이 등록되었습니다!")
                    st.rerun()

    with tab_exp2:
        st.markdown(f"##### ✏️ [{cur_b}] 전체 지출 내역 에디터")
        st.caption("💡 **표에서 가장 앞쪽 빈 칸을 선택한 후 키보드의 Delete 키를 누르고 '💾 지출 내역 변경사항 저장'을 클릭**하면 해당 지출 내역이 시스템에서 완전히 삭제됩니다.")

        e_b_df = st.session_state["expenses"][st.session_state["expenses"]["사업명"] == cur_b] if not st.session_state["expenses"].empty else pd.DataFrame()

        col_f0, col_f1, col_f2, col_f3 = st.columns([1, 1.2, 1, 1])
        with col_f0:
            all_years = ["전체 차수", "1차년도", "2차년도", "3차년도", "4차년도", "5차년도"]
            idx_y = all_years.index(selected_year_str) if selected_year_str in all_years else 0
            filter_year = st.selectbox("집행차수 필터", options=all_years, index=idx_y)
        with col_f1:
            filter_proj = st.multiselect("과제/사업단 필터", options=proj_list, default=[])
        with col_f2:
            filter_status = st.multiselect("지급상태 필터", options=["지급완료", "결재대기", "보완요청", "지급취소"], default=[])
        with col_f3:
            search_kw = st.text_input("🔎 지출처/적요 키워드 검색", placeholder="예: 회의비", key="exp_search_kw")

        view_exp_df = e_b_df.copy()
        
        # 🔴 [마이그레이션 보강] 과거 데이터에 집행차수가 없을 경우 KeyError 원천 방지
        if "집행차수" not in view_exp_df.columns: view_exp_df["집행차수"] = "1차년도"
        if "재원구분" not in view_exp_df.columns: view_exp_df["재원구분"] = "당해 배정액"
            
        if filter_year != "전체 차수":
            view_exp_df = view_exp_df[view_exp_df["집행차수"] == filter_year]
        if filter_proj:
            view_exp_df = view_exp_df[view_exp_df["과제/사업단명"].isin(filter_proj)]
        if filter_status:
            view_exp_df = view_exp_df[view_exp_df["지급상태"].isin(filter_status)]
        if search_kw:
            view_exp_df = view_exp_df[view_exp_df["지출처/적요"].astype(str).str.contains(search_kw, case=False, na=False)]

        f_total = int(pd.to_numeric(view_exp_df.get("지출액", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not view_exp_df.empty else 0
        st.caption(f"📋 필터 결과: **{len(view_exp_df)}건** | 합계 **{won(f_total)}**")

        view_exp_df = safe_get_columns(view_exp_df, ["No", "집행차수", "재원구분", "지출일자", "과제/사업단명", "비목", "보조비목", "보조세목", "지출액", "지출처/적요", "지급상태", "비고"]).reset_index(drop=True)
        displayed_exp_nos = [int(x) for x in pd.to_numeric(view_exp_df["No"], errors="coerce").dropna().tolist()] if "No" in view_exp_df.columns else []

        all_bimoks = get_bimok_list()
        c_df = st.session_state["categories"]
        all_bojo_bimoks = c_df["보조비목"].dropna().unique().tolist() if not c_df.empty and "보조비목" in c_df.columns else ["일반수용비"]
        all_bojo_semoks = c_df["보조세목"].dropna().unique().tolist() if not c_df.empty and "보조세목" in c_df.columns else ["일반수용비(3)"]

        edited_exp_df = st.data_editor(
            view_exp_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "No": None,
                "집행차수": st.column_config.SelectboxColumn("집행차수", options=["1차년도", "2차년도", "3차년도", "4차년도", "5차년도"]),
                "재원구분": st.column_config.SelectboxColumn("재원구분", options=["당해 배정액", "전년 이월금"]),
                "지출액": st.column_config.NumberColumn("지출액(원)", format="₩%,d", min_value=0, step=1000),
                "과제/사업단명": st.column_config.SelectboxColumn("과제/사업단명", options=proj_list),
                "비목": st.column_config.SelectboxColumn("비목", options=all_bimoks),
                "보조비목": st.column_config.SelectboxColumn("보조비목", options=all_bojo_bimoks),
                "보조세목": st.column_config.SelectboxColumn("보조세목", options=all_bojo_semoks),
                "지급상태": st.column_config.SelectboxColumn("지급상태", options=["지급완료", "결재대기", "보완요청", "지급취소"])
            },
            key=f"exp_editor_main_{cur_b}"
        )

        save_clicked_main = st.button("💾 지출 내역 변경사항 저장", key="btn_save_all_exp")

        if save_clicked_main:
            main_e = st.session_state["expenses"].copy()
            
            # 🗑️ [삭제 감지] 표에서 지워진 항목 제거
            edited_no_series = pd.to_numeric(edited_exp_df.get("No", pd.Series(dtype=float)), errors="coerce")
            remaining_nos = set(int(x) for x in edited_no_series.dropna().tolist())
            deleted_nos = [n for n in displayed_exp_nos if n not in remaining_nos]
            if deleted_nos:
                main_e = main_e[~main_e["No"].isin(deleted_nos)].reset_index(drop=True)
            
            edited_clean_e = clean_expenses(edited_exp_df, cur_b)
            
            max_no = main_e["No"].max() if not main_e.empty else 0
            for idx, row in edited_clean_e.iterrows():
                if row["No"] <= 0 or (row["No"] in main_e["No"].values and not (view_exp_df["No"] == row["No"]).any()):
                    max_no += 1
                    edited_clean_e.loc[idx, "No"] = max_no

            mask = (main_e["사업명"] == cur_b)
            if filter_year != "전체 차수": mask &= (main_e["집행차수"] == filter_year)
            if filter_proj: mask &= main_e["과제/사업단명"].isin(filter_proj)
            if filter_status: mask &= main_e["지급상태"].isin(filter_status)
            if search_kw: mask &= main_e["지출처/적요"].astype(str).str.contains(search_kw, case=False, na=False)

            main_e = main_e[~mask]
            cand_main_e = pd.concat([main_e, edited_clean_e], ignore_index=True)

            is_valid, errs = validate_all_expenses_against_budgets(
                cand_main_e, st.session_state["budget_projects"], st.session_state["budget_details"]
            )

            if not is_valid:
                error_msg = "🚫 **[지출 초과 오류]** 수정하신 지출 내역이 재원(배정액/이월금) 한도를 초과하여 저장할 수 없습니다!\n"
                for e in errs: error_msg += f"\n{e}"
                st.error(error_msg)
            else:
                st.session_state["expenses"] = clean_expenses(cand_main_e, cur_b)
                save_and_sync_all("✅ 전체 지출 내역이 성공적으로 업데이트되었습니다!")
                st.rerun()

        with st.expander("🗑️ 지출 내역 목록에서 직접 선택하여 삭제하기", expanded=False):
            st.caption("위의 에디터 표에서 지우는 대신 아래 목록에서 삭제할 항목을 직접 선택하여 안전하게 완전히 삭제할 수 있습니다.")
            e_b_now = st.session_state["expenses"][st.session_state["expenses"]["사업명"] == cur_b] if not st.session_state["expenses"].empty else pd.DataFrame()
            if e_b_now.empty:
                st.info("삭제할 수 있는 지출 내역이 없습니다.")
            else:
                del_exp_opts = {
                    f"[{r.get('집행차수','1차년도')}-{r.get('재원구분','당해 배정액')}] {r['지출일자']} | {str(r['과제/사업단명'])[:15]} | {r['비목']}>{r['보조세목']} | ₩{int(r['지출액']):,}": int(r["No"])
                    for _, r in e_b_now.iterrows()
                }
                selected_del_exp_labels = st.multiselect("삭제할 지출 항목 선택 (복수 선택 가능)", options=list(del_exp_opts.keys()), key="exp_del_multiselect")
                del_confirm_exp = st.checkbox(f"네, 선택한 {len(selected_del_exp_labels)}건의 지출 내역을 삭제합니다. (필수 체크)", key="chk_del_exp_confirm")
                
                if st.button(f"🔴 선택한 지출 내역 {len(selected_del_exp_labels)}건 삭제 실행", key="btn_del_selected_expenses", disabled=(not del_confirm_exp or len(selected_del_exp_labels) == 0)):
                    del_exp_nos = [del_exp_opts[lbl] for lbl in selected_del_exp_labels]
                    all_e_now = st.session_state["expenses"]
                    st.session_state["expenses"] = all_e_now[~all_e_now["No"].isin(del_exp_nos)].reset_index(drop=True)
                    save_and_sync_all(f"🗑️ 지출 내역 {len(del_exp_nos)}건이 삭제되었습니다.")
                    st.rerun()

# ----------------------------------------------------
# PAGE 5: 🎯 성과지표 관리
# ----------------------------------------------------
elif st.session_state["menu_selection"] == "🎯 성과지표 관리":
    st.markdown('<div class="sec-title">🎯 앵커 사업 성과지표(KPI) 통합 관리 대시보드</div>', unsafe_allow_html=True)
    st.info("💡 성과지표가 **1순위 단위과제 번호(1-1 → 1-2 → 2-1…) → 2순위 지표번호** 순으로 자동 정렬됩니다. 지표번호에 알파벳이 붙으면(예: **2-A, 2-B**) 해당 숫자 주지표(**2**)의 세부지표로 인식되며, 세부지표 실적 작성 시 가중치가 적용되어 주지표 실적값으로 자동 합산·저장됩니다.")

    kpi_df = st.session_state["kpis"].copy()

    f_col1, f_col2, f_col3 = st.columns([1.6, 1.8, 1.2])
    with f_col1:
        st.info(f"📅 연도: **{selected_year_str} ({YEAR_PERIODS.get(active_year, '')})**")
    with f_col2:
        all_unit_projs = ["전체 단위과제"] + (kpi_df["단위과제"].unique().tolist() if not kpi_df.empty and "단위과제" in kpi_df.columns else [])
        unit_filter = st.selectbox("🏢 단위과제 필터", all_unit_projs, key="kpi_unit_filter_new")
    with f_col3:
        gubun_filter = st.selectbox("🏷️ 지표 구분 필터", ["전체", "공통", "자율"], key="kpi_gubun_filter_new")

    kpi_calc = compute_kpi_achievement(kpi_df, active_year)

    filtered_kpis = kpi_calc.copy()
    if gubun_filter != "전체": filtered_kpis = filtered_kpis[filtered_kpis["지표구분"] == gubun_filter]
    if unit_filter != "전체 단위과제": filtered_kpis = filtered_kpis[filtered_kpis["단위과제"] == unit_filter]

    tot_cnt = len(filtered_kpis)
    valid_rates = filtered_kpis["달성률(%)"].dropna()
    avg_rate = round(valid_rates.mean(), 1) if not valid_rates.empty else 0.0

    success_cnt = len(filtered_kpis[filtered_kpis["달성상태"] == "🟢 달성"])
    progress_cnt = len(filtered_kpis[filtered_kpis["달성상태"] == "🟡 진행중"])
    warning_cnt = len(filtered_kpis[filtered_kpis["달성상태"] == "🔴 미달"])
    empty_cnt = len(filtered_kpis[filtered_kpis["달성상태"] == "⚪ 미입력"])

    render_metric_row([
        metric_card("📊", f"{selected_year_str} 평균 달성률", f"{avg_rate:.1f}%" if not valid_rates.empty else "미집계", f"총 {tot_cnt}개 지표 · {YEAR_PERIODS.get(active_year, '')}", "#1B365D"),
        metric_card("🟢", "목표 달성 완료", f"{success_cnt} 개", "", "#2ECC71"),
        metric_card("🟡", "목표 임박/진행중", f"{progress_cnt} 개", "", "#F1C40F"),
        metric_card("🔴", "목표 미달 (주의)", f"{warning_cnt} 개", "", "#E74C3C"),
        metric_card("⚪", "실적 미입력", f"{empty_cnt} 개", "", "#94A3B8"),
    ])

    st.divider()

    col_chart_l, col_chart_r = st.columns([1.35, 0.65])

    with col_chart_l:
        st.markdown(f"#### 📈 {selected_year_str} 달성률 시각화")
        chart_tab1, chart_tab2 = st.tabs(["🎯 단위과제별 · 지표별 달성률", "📊 단위과제 평균 비교"])

        with chart_tab1:
            plot_src = filtered_kpis.copy()
            plot_src = plot_src[plot_src["달성률(%)"].notna()].copy()

            if not plot_src.empty:
                plot_src["지표라벨"] = plot_src.apply(
                    lambda r: f"[{str(r['지표번호'])}] {str(r['지표명'])[:20]}{'…' if len(str(r['지표명'])) > 20 else ''}", axis=1
                )
                dup_mask = plot_src["지표라벨"].duplicated(keep=False)
                plot_src.loc[dup_mask, "지표라벨"] = plot_src.loc[dup_mask].apply(
                    lambda r: f"{r['지표라벨']} (No.{int(r['No'])})", axis=1
                )
                plot_src["단위과제_약칭"] = plot_src["단위과제"].apply(
                    lambda x: str(x)[:16] + "…" if len(str(x)) > 16 else str(x)
                )

                label_order = plot_src["지표라벨"].tolist()

                fig_kpi_detail = px.bar(
                    plot_src, y="지표라벨", x="달성률(%)", color="단위과제_약칭",
                    orientation="h", text="달성률(%)",
                    labels={"지표라벨": "성과지표", "달성률(%)": "달성률(%)", "단위과제_약칭": "단위과제"},
                    color_discrete_sequence=UNIT_COLOR_SEQ,
                    hover_data={"단위과제_약칭": True, "달성상태": True, "지표유형": True}
                )
                fig_kpi_detail.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
                fig_kpi_detail.update_yaxes(categoryorder="array", categoryarray=label_order[::-1])
                fig_kpi_detail.add_vline(
                    x=100, line_dash="dash", line_color="#E74C3C", line_width=2,
                    annotation_text="목표 100%", annotation_position="top"
                )
                dyn_h = max(360, 30 * len(plot_src) + 130)
                st.plotly_chart(style_fig(fig_kpi_detail, h=dyn_h), use_container_width=True)
                st.caption("🎨 막대 색상 = 단위과제 구분 · 빨간 점선 = 목표(100%) · 정렬 순서 = 단위과제 번호 → 지표번호")
            else:
                st.info(f"💡 {selected_year_str}에 등록된 실적값이 아직 없어 차트를 생성하지 않았습니다. 아래 표에 실적값을 입력해보세요.")

        with chart_tab2:
            if not filtered_kpis.empty and "단위과제" in filtered_kpis.columns:
                unit_agg = filtered_kpis.groupby("단위과제", sort=False)["달성률(%)"].mean().reset_index()
                unit_agg["평균달성률(%)"] = unit_agg["달성률(%)"].fillna(0).round(1)
                unit_agg["단위과제_약칭"] = unit_agg["단위과제"].apply(lambda x: str(x)[:22] + "…" if len(str(x)) > 22 else str(x))

                if not unit_agg.empty and unit_agg["평균달성률(%)"].sum() > 0:
                    fig_kpi_bar = px.bar(
                        unit_agg, x="단위과제_약칭", y="평균달성률(%)", text="평균달성률(%)",
                        labels={"단위과제_약칭": "단위과제명", "평균달성률(%)": "평균 달성률(%)"},
                        color="단위과제_약칭", color_discrete_sequence=UNIT_COLOR_SEQ
                    )
                    fig_kpi_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
                    fig_kpi_bar.add_hline(
                        y=100, line_dash="dash", line_color="#E74C3C", line_width=2,
                        annotation_text="목표 100%", annotation_position="top left"
                    )
                    st.plotly_chart(style_fig(fig_kpi_bar, h=380, showlegend=False), use_container_width=True)
                else:
                    st.info(f"💡 {selected_year_str}에 등록된 실적값이 아직 없어 차트를 생성하지 않았습니다.")

    with col_chart_r:
        st.markdown(f"#### 🍰 {selected_year_str} 달성 상태 분포")
        status_df = filtered_kpis["달성상태"].value_counts().reset_index()
        status_df.columns = ["달성상태", "수량"]

        fig_pie_status = px.pie(
            status_df, values="수량", names="달성상태", hole=0.5, color="달성상태",
            color_discrete_map={"🟢 달성": "#2ecc71", "🟡 진행중": "#f1c40f", "🔴 미달": "#e74c3c", "⚪ 미입력": "#bdc3c7"}
        )
        st.plotly_chart(style_fig(fig_pie_status, h=350), use_container_width=True)

    st.divider()

    st.markdown(f"##### ✏️ [{selected_year_str}] 성과지표 목표 및 실적 편집 표")
    st.caption("💡 연번(No)은 자동 관리됩니다 — 새 행은 연번을 비워두고 내용만 입력하면 자동 부여됩니다. 지표번호가 **2-A, 2-B**처럼 알파벳이 붙으면 주지표 **2**의 세부지표(└ 🔹)로 인식되어 가중치 합산이 적용됩니다. 표 가장 좌측 빈칸을 누르고 `Delete`키로 행을 삭제한 후 저장할 수도 있습니다.")

    target_c = f"목푯값_{active_year}차"
    actual_c = f"실적값_{active_year}차"
    conso_target_c = f"컨소_목푯값_{active_year}차"
    conso_actual_c = f"컨소_실적값_{active_year}차"

    disp_cols = [
        "No", "지표유형", "지표구분", "단위과제", "지표번호", "지표명", "단위", "가중치", "기준값",
        target_c, actual_c, "달성률(%)", "달성상태", "컨소_기준값", conso_target_c, conso_actual_c, "비고"
    ]
    disp_cols = [c for c in disp_cols if c in filtered_kpis.columns]

    view_kpis = filtered_kpis[disp_cols].copy().reset_index(drop=True)
    displayed_kpi_nos = [int(x) for x in pd.to_numeric(view_kpis["No"], errors="coerce").dropna().tolist()] if "No" in view_kpis.columns else []

    for c in view_kpis.columns:
        if c not in ["No", "달성률(%)"]:
            view_kpis[c] = view_kpis[c].apply(lambda x: "" if (pd.isna(x) or str(x).strip() in ['nan', 'None']) else str(x).strip())

    edited_kpi_df = st.data_editor(
        view_kpis,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "No": None, # 화면에서 완벽하게 숨김
            "지표유형": st.column_config.TextColumn("지표유형", disabled=True),
            "달성률(%)": st.column_config.NumberColumn("달성률(%)", format="%.1f%%", disabled=True),
            "달성상태": st.column_config.TextColumn("달성상태", disabled=True),
            target_c: st.column_config.TextColumn(f"목푯값({active_year}차)"),
            actual_c: st.column_config.TextColumn(f"실적값({active_year}차)"),
            conso_target_c: st.column_config.TextColumn(f"컨소 목푯값({active_year}차)"),
            conso_actual_c: st.column_config.TextColumn(f"컨소 실적값({active_year}차)")
        },
        key=f"editor_kpis_v4_{active_year}_{gubun_filter}_{unit_filter}"
    )

    if st.button(f"💾 {selected_year_str} 성과지표 변경사항 저장", key="btn_save_kpis_v4"):
        edited_rows = edited_kpi_df.copy()
        main_kpis = st.session_state["kpis"].copy()

        edited_no_series = pd.to_numeric(edited_rows.get("No", pd.Series(dtype=float)), errors="coerce")
        remaining_nos = set(int(x) for x in edited_no_series.dropna().tolist())
        deleted_nos = [n for n in displayed_kpi_nos if n not in remaining_nos]
        if deleted_nos:
            main_kpis = main_kpis[~main_kpis["No"].isin(deleted_nos)].reset_index(drop=True)

        editable_cols = [c for c in edited_rows.columns if c not in ["No", "지표유형", "달성률(%)", "달성상태"]]
        new_row_cnt = 0
        
        for idx, row in edited_rows.iterrows():
            no_val = pd.to_numeric(pd.Series([row.get("No")]), errors="coerce").iloc[0]

            if pd.notna(no_val) and int(no_val) in main_kpis["No"].values:
                match_idx = main_kpis[main_kpis["No"] == int(no_val)].index
                if not match_idx.empty:
                    for col in editable_cols:
                        if col in main_kpis.columns:
                            main_kpis.loc[match_idx[0], col] = row[col]
            else:
                name_chk = str(row.get("지표명", "")).strip()
                if name_chk in ["", "nan", "None"]: continue  
                max_kpi_no = int(pd.to_numeric(main_kpis["No"], errors="coerce").max()) if not main_kpis.empty else 0
                new_row = {c: row.get(c, "") for c in editable_cols if c in main_kpis.columns}
                new_row["No"] = max_kpi_no + 1
                main_kpis = pd.concat([main_kpis, pd.DataFrame([new_row])], ignore_index=True)
                new_row_cnt += 1

        cleaned_kpis = clean_kpis(main_kpis)
        rolled = compute_kpi_achievement(cleaned_kpis, active_year)
        for sync_col in [actual_c, conso_actual_c]:
            if sync_col in rolled.columns and sync_col in cleaned_kpis.columns:
                val_map = dict(zip(rolled["No"], rolled[sync_col]))
                cleaned_kpis[sync_col] = cleaned_kpis["No"].map(val_map).fillna(cleaned_kpis[sync_col])

        st.session_state["kpis"] = cleaned_kpis

        msg_parts = []
        if new_row_cnt: msg_parts.append(f"신규 {new_row_cnt}건")
        if deleted_nos: msg_parts.append(f"삭제 {len(deleted_nos)}건")
        extra = f" ({' · '.join(msg_parts)})" if msg_parts else ""
        save_and_sync_all(f"✅ {selected_year_str} 성과지표가 저장되었습니다!{extra} (주지표 자동 합산 반영)")
        st.rerun()

    with st.expander("🗑️ 성과지표 선택 삭제 (목록에서 여러 지표 한 번에 삭제)", expanded=False):
        st.caption("삭제할 지표를 목록에서 선택한 뒤 확인 체크박스를 체크하고 삭제 버튼을 누르세요. 삭제 즉시 데이터베이스에 반영됩니다.")
        main_kpis_now = st.session_state["kpis"]
        if main_kpis_now.empty:
            st.info("삭제할 수 있는 성과지표가 없습니다.")
        else:
            del_candidates = main_kpis_now.copy()
            if gubun_filter != "전체": del_candidates = del_candidates[del_candidates["지표구분"] == gubun_filter]
            if unit_filter != "전체 단위과제": del_candidates = del_candidates[del_candidates["단위과제"] == unit_filter]

            if del_candidates.empty:
                st.info("현재 필터 조건에 해당하는 지표가 없습니다.")
            else:
                del_options = {
                    f"[{r['지표구분']}] {str(r['단위과제'])[:18]} | {str(r['지표번호'])} {str(r['지표명'])[:30]}": int(r["No"])
                    for _, r in del_candidates.iterrows()
                }
                selected_del_labels = st.multiselect("삭제할 지표 선택 (복수 선택 가능)", options=list(del_options.keys()), key="kpi_del_multiselect")
                del_confirm_kpi = st.checkbox(f"네, 선택한 {len(selected_del_labels)}개 지표를 삭제하는 것을 확인했습니다. (필수 체크)", key="chk_del_kpi_confirm")

                if st.button(f"🔴 선택한 지표 {len(selected_del_labels)}건 삭제 실행", key="btn_del_kpis", disabled=(not del_confirm_kpi or len(selected_del_labels) == 0)):
                    del_nos = [del_options[lbl] for lbl in selected_del_labels]
                    st.session_state["kpis"] = main_kpis_now[~main_kpis_now["No"].isin(del_nos)].reset_index(drop=True)
                    save_and_sync_all(f"🗑️ 성과지표 {len(del_nos)}건이 삭제되었습니다.")
                    st.rerun()

# ----------------------------------------------------
# PAGE 6: 🏷️ 예산 세목 기준표 설정
# ----------------------------------------------------
elif st.session_state["menu_selection"] == "🏷️ 예산 세목 기준표 설정":
    st.markdown('<div class="sec-title">🏷️ 공통 예산 세목 기준표 설정 (모든 관리 사업 연동)</div>', unsafe_allow_html=True)
    st.info("💡 모든 관리 사업에서 공통으로 사용할 예산 항목 체계(비목, 보조비목, 보조세목)를 설정합니다. 여기서 설정/수정/추가된 비목 체계는 모든 사업의 지출 입력 및 예산 편성에 즉시 공유 및 반영됩니다.")

    c_df = st.session_state["categories"]
    view_cat_df = safe_get_columns(c_df, ["비목", "보조비목", "보조세목", "설명"]).reset_index(drop=True)

    col_tree, col_edit = st.columns([0.8, 1.2])

    with col_tree:
        st.markdown("###### 🌳 현재 비목 체계 미리보기")
        if not view_cat_df.empty:
            tree_cat_src = view_cat_df.copy()
            for c in ["비목", "보조비목", "보조세목"]:
                tree_cat_src[c] = tree_cat_src[c].replace("", "(미지정)").fillna("(미지정)")
            tree_cat_src["cnt"] = 1
            fig_cat_tree = px.treemap(
                tree_cat_src, path=["비목", "보조비목", "보조세목"], values="cnt",
                color="비목", color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_cat_tree.update_traces(hovertemplate="%{label}<extra></extra>")
            st.plotly_chart(style_fig(fig_cat_tree, h=380, showlegend=False), use_container_width=True)
        else:
            st.info("등록된 비목 체계가 없습니다.")

    with col_edit:
        st.markdown("###### ✏️ 비목 체계 편집")
        st.caption("💡 **표에서 행(Row) 가장 앞쪽 빈 칸을 선택한 후 키보드의 Delete 키를 누르고 '💾 공통 비목 체계 저장'을 클릭**하면 해당 비목이 삭제됩니다. 하단 목록에서 선택 삭제할 수도 있습니다.")
        
        edited_cat_df = st.data_editor(
            view_cat_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            height=340,
            key="cat_editor_global_master"
        )

        if st.button("💾 공통 비목 체계 저장", key="btn_save_categories"):
            st.session_state["categories"] = clean_categories(edited_cat_df)
            save_and_sync_all("✅ 공통 예산 세목 기준표가 업데이트되었습니다! 모든 사업에 반영됩니다.")
            st.rerun()
            
        with st.expander("🗑️ 공통 비목 체계 목록에서 직접 선택하여 삭제하기", expanded=False):
            st.caption("위의 에디터 표에서 지우는 대신 아래 목록에서 삭제할 비목을 직접 선택하여 안전하게 삭제할 수 있습니다.")
            cat_now = st.session_state["categories"]
            if cat_now.empty:
                st.info("삭제할 비목 체계가 없습니다.")
            else:
                del_cat_opts = {
                    f"[{r['비목']}] {r['보조비목']} > {r['보조세목']}": idx
                    for idx, r in cat_now.iterrows()
                }
                selected_del_cat = st.multiselect("삭제할 비목 선택 (복수 선택 가능)", list(del_cat_opts.keys()), key="del_cat_multi")
                del_confirm_cat = st.checkbox(f"네, 선택한 {len(selected_del_cat)}건의 비목을 삭제합니다. (필수 체크)", key="chk_del_cat_confirm")
                if st.button(f"🔴 선택 비목 {len(selected_del_cat)}건 삭제 실행", disabled=(not del_confirm_cat or not selected_del_cat), key="btn_del_cat_multi"):
                    drop_idxs = [del_cat_opts[k] for k in selected_del_cat]
                    st.session_state["categories"] = cat_now.drop(index=drop_idxs).reset_index(drop=True)
                    save_and_sync_all("🗑️ 선택한 공통 비목이 삭제되었습니다.")
                    st.rerun()

# ----------------------------------------------------
# PAGE 7: 📁 엑셀 내보내기 & 백업
# ----------------------------------------------------
elif st.session_state["menu_selection"] == "📁 엑셀 내보내기 & 백업":
    st.markdown('<div class="sec-title">📁 데이터 내보내기 및 복원</div>', unsafe_allow_html=True)
    st.markdown("웹에 작성된 모든 예산 및 지출 내역, 성과지표를 **엑셀 파일(.xlsx)** 형태로 다운로드하거나, 이전 데이터를 복원할 수 있습니다.")

    col_exp1, col_exp2, col_imp = st.columns([1, 1, 1])

    with col_exp1:
        st.markdown(f"#### 📥 [{cur_b}] 엑셀 내보내기")
        st.write("현재 선택된 사업의 데이터만 멀티 탭 엑셀 파일로 다운로드합니다.")

        buffer_b = io.BytesIO()
        with pd.ExcelWriter(buffer_b, engine="openpyxl") as writer:
            p_b = st.session_state["budget_projects"][st.session_state["budget_projects"]["사업명"] == cur_b]
            bd_b = st.session_state["budget_details"][st.session_state["budget_details"]["사업명"] == cur_b]
            e_b = st.session_state["expenses"][st.session_state["expenses"]["사업명"] == cur_b]
            c_b = st.session_state["categories"]
            k_b = st.session_state["kpis"]

            p_b.to_excel(writer, sheet_name="과제별_총예산", index=False)
            bd_b.to_excel(writer, sheet_name="세목별_예산편성", index=False)
            e_b.to_excel(writer, sheet_name="지출내역", index=False)
            c_b.to_excel(writer, sheet_name="예산비목기준표", index=False)
            k_b.to_excel(writer, sheet_name="성과지표_현황", index=False)

        st.download_button(
            label=f"⬇️ '{cur_b}' 엑셀 다운로드 (.xlsx)",
            data=buffer_b.getvalue(),
            file_name=f"{cur_b}_예산_지출_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_exp2:
        st.markdown("#### 🌐 전체 사업 통합 엑셀 내보내기")
        st.write("등록된 모든 사업/프로젝트 그룹 및 성과지표 데이터를 통합 엑셀 파일로 다운로드합니다.")

        buffer_all = io.BytesIO()
        with pd.ExcelWriter(buffer_all, engine="openpyxl") as writer:
            st.session_state["businesses"].to_excel(writer, sheet_name="사업목록_마스터", index=False)
            st.session_state["budget_projects"].to_excel(writer, sheet_name="전체_과제별_총예산", index=False)
            st.session_state["budget_details"].to_excel(writer, sheet_name="전체_세목별_예산편성", index=False)
            st.session_state["expenses"].to_excel(writer, sheet_name="전체_지출내역", index=False)
            st.session_state["categories"].to_excel(writer, sheet_name="공통_예산비목기준표", index=False)
            st.session_state["kpis"].to_excel(writer, sheet_name="전체_성과지표_마스터", index=False)

        st.download_button(
            label="⬇️ 전체 사업 통합 엑셀 다운로드 (.xlsx)",
            data=buffer_all.getvalue(),
            file_name=f"공모과제_전체사업통합_예산_지출_성과지표_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_imp:
        st.markdown("#### 📤 데이터 업로드 복원")
        st.write("백업해둔 CSV 데이터를 업로드하여 지출 내역을 복원합니다.")
        uploaded_file = st.file_uploader("CSV 파일 선택", type=["csv"])
        if uploaded_file is not None:
            try:
                up_df = pd.read_csv(uploaded_file)
                st.write("업로드된 데이터 미리보기:", up_df.head(3))
                st.warning("⚠️ 복원 시 현재 지출 내역이 업로드한 데이터로 **전체 교체**됩니다.")
                restore_confirm = st.checkbox("네, 기존 지출 내역이 교체됨을 확인했습니다. (필수 체크)", key="chk_restore_confirm")
                if st.button("이 데이터로 지출내역 교체하기", disabled=not restore_confirm):
                    st.session_state["expenses"] = clean_expenses(up_df, cur_b)
                    save_and_sync_all("✅ 지출 내역이 복원되었습니다!")
                    st.rerun()
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")