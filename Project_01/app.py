"""
검색 관심도 대시보드 (미션 A3 보너스 · 단계 10)

하는 일
  data/search_trend_weekly.csv 를 읽어, 기간·지역·집계 단위를 바꿔 가며
  검색 관심도 추이를 확인하는 웹 화면을 띄운다. API는 호출하지 않는다.

실행
  (.venv) Project_01> streamlit run app.py
  → 브라우저가 자동으로 열린다. 종료는 터미널에서 Ctrl+C.
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib import font_manager

COLORS = {"통영": "#3B5BDB", "거제": "#E8590C", "남해": "#099268"}
DATA_PATH = Path(__file__).parent / "data" / "search_trend_weekly.csv"


def set_korean_font():
    """그래프의 한글이 네모로 깨지지 않도록 설치된 한글 글꼴을 지정한다."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic", "DejaVu Sans"]:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


@st.cache_data                      # 같은 파일을 매번 다시 읽지 않도록 결과를 재사용
def load_data():
    return pd.read_csv(DATA_PATH, index_col="period", parse_dates=["period"],
                       encoding="utf-8-sig")


set_korean_font()
st.set_page_config(page_title="남해안 여행지 검색 관심도", layout="wide")
st.title("남해안 3개 여행지 검색 관심도")
st.caption("출처: 네이버 데이터랩 검색어트렌드 · 값은 조회 기간 내 최댓값을 100으로 둔 상대 지수")

df = load_data()

# ── 왼쪽 필터 영역 ────────────────────────────────────────────────
with st.sidebar:
    st.header("조건")
    지역들 = st.multiselect("지역", list(df.columns), default=list(df.columns))
    첫해, 끝해 = int(df.index.year.min()), int(df.index.year.max())
    # 첫해(2020)는 경계 주 1개뿐이라 기본 선택에서 제외한다
    시작, 종료 = st.slider("기간(연도)", 첫해, 끝해, (min(2021, 끝해), 끝해))
    단위 = st.radio("집계 단위", ["주간", "월간"], horizontal=True)
    창 = st.slider("이동평균 창(구간 수)", 1, 26, 12,
                   help="집계 단위가 주간이면 '주', 월간이면 '개월'로 적용된다. 1이면 이동평균 없이 원본 그대로 본다")

if not 지역들:
    st.warning("지역을 하나 이상 선택하세요.")
    st.stop()

# ── 선택 조건 적용 ────────────────────────────────────────────────
표 = df.loc[str(시작):str(종료), 지역들]
if 단위 == "월간":
    표 = 표.resample("MS").mean()        # MS = 매월 1일 기준으로 묶기
선 = 표.rolling(window=창, center=True, min_periods=max(1, 창 // 2)).mean()

# ── 요약 숫자 ────────────────────────────────────────────────────
칸 = st.columns(len(지역들))
for 칸하나, 지역 in zip(칸, 지역들):
    칸하나.metric(f"{지역} 평균", f"{표[지역].mean():.1f}",
                  f"최고 {표[지역].max():.1f}")

# ── 그래프 ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4.5))
for 지역 in 지역들:
    ax.plot(표.index, 표[지역], color=COLORS[지역], alpha=0.25, linewidth=1.1)
    ax.plot(선.index, 선[지역], color=COLORS[지역], linewidth=2.2, label=지역)
ax.set_ylabel("검색 관심도")
ax.legend(frameon=False, ncol=len(지역들))
ax.grid(axis="y", alpha=0.25)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
st.pyplot(fig)

# ── 월별 평균 ────────────────────────────────────────────────────
st.subheader("월별 평균")
월별 = 표.groupby(표.index.month).mean().round(1)
월별.index.name = "월"

# 지역끼리 '비교'가 목적이므로 쌓지 않고 나란히 놓는다.
# (쌓아 그리면 세 지역의 합처럼 보여, 7월 막대가 100을 넘는 것처럼 읽힌다)
fig2, ax2 = plt.subplots(figsize=(11, 3.6))
막대폭 = 0.8 / len(지역들)
for 번호, 지역 in enumerate(지역들):
    위치 = 월별.index + (번호 - (len(지역들) - 1) / 2) * 막대폭
    ax2.bar(위치, 월별[지역], width=막대폭, color=COLORS[지역], label=지역)
ax2.set_xticks(range(1, 13))
ax2.set_xticklabels([f"{m}월" for m in range(1, 13)])
ax2.set_ylabel("월평균 관심도")
ax2.legend(frameon=False, ncol=len(지역들))
ax2.grid(axis="y", alpha=0.25)
for side in ["top", "right"]:
    ax2.spines[side].set_visible(False)
st.pyplot(fig2)

with st.expander("선택한 구간의 원본 데이터 보기"):
    st.dataframe(표.round(1))
