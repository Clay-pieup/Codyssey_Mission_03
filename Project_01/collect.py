"""
네이버 데이터랩 검색어트렌드 수집 스크립트 (미션 A3 · 단계 3)

하는 일
  통영·거제·남해 여행 검색 관심도(주간, 2021~2025)를 한 번의 요청으로 받아
  data/ 폴더에 원본(JSON)과 분석용 표(CSV)로 저장한다.

실행
  (.venv) Project_01> python collect.py
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ── 설정: 분석 조건을 한곳에 모아 둔다 (바꿀 때 여기만 고치면 됨) ──────────
API_URL = "https://naverapihub.apigw.ntruss.com/search-trend/v1/search"

START_DATE = "2021-01-01"
END_DATE = "2025-12-31"
TIME_UNIT = "week"  # date(일) / week(주) / month(월) 중 선택

# 그룹 하나 = 지역 하나. 띄어쓰기만 다른 표현은 같은 관심으로 보고 합산한다.
KEYWORD_GROUPS = [
    {"groupName": "통영", "keywords": ["통영 여행", "통영여행"]},
    {"groupName": "거제", "keywords": ["거제 여행", "거제여행"]},
    {"groupName": "남해", "keywords": ["남해 여행", "남해여행"]},
]

DATA_DIR = Path(__file__).parent / "data"
RAW_PATH = DATA_DIR / "search_trend_raw.json"
CSV_PATH = DATA_DIR / "search_trend_weekly.csv"


def load_keys():
    """.env 파일에서 API 키 두 개를 읽는다. 없으면 이유를 알려 주고 멈춘다."""
    load_dotenv()
    key_id = os.getenv("NAVER_API_KEY_ID", "").strip()
    key = os.getenv("NAVER_API_KEY", "").strip()
    if not key_id or not key:
        sys.exit("[중단] .env 에 NAVER_API_KEY_ID / NAVER_API_KEY 값이 비어 있습니다.")
    return key_id, key


def request_trend(key_id, key):
    """데이터랩에 세 지역을 '한 번에' 요청한다. 따로 요청하면 100 기준이 달라진다."""
    headers = {
        "X-NCP-APIGW-API-KEY-ID": key_id,
        "X-NCP-APIGW-API-KEY": key,
        "Content-Type": "application/json",
    }
    body = {
        "startDate": START_DATE,
        "endDate": END_DATE,
        "timeUnit": TIME_UNIT,
        "keywordGroups": KEYWORD_GROUPS,
    }
    res = requests.post(API_URL, headers=headers, json=body, timeout=15)
    if res.status_code != 200:
        # 키 값은 출력하지 않고, 서버가 알려 준 오류 내용만 보여 준다.
        sys.exit(f"[실패] HTTP {res.status_code}\n{res.text[:500]}")
    return res.json()


def to_table(result_json):
    """응답(지역별 목록 3개)을 '행=주, 열=지역' 표 하나로 바꾼다."""
    rows = []
    for group in result_json["results"]:
        for point in group["data"]:
            rows.append({"period": point["period"], "region": group["title"], "ratio": point["ratio"]})
    long_df = pd.DataFrame(rows)
    # pivot: 세로로 길게 쌓인 (주, 지역, 값)을 주 기준 가로 표로 펼친다.
    # 어느 지역에 특정 주 값이 없으면 그 칸은 빈칸(NaN)이 된다 → 단계 4에서 결측치로 확인.
    wide_df = long_df.pivot(index="period", columns="region", values="ratio")
    wide_df = wide_df[[g["groupName"] for g in KEYWORD_GROUPS]]  # 열 순서 고정
    return wide_df.sort_index()


def main():
    key_id, key = load_keys()
    print(f"요청: {START_DATE} ~ {END_DATE}, 단위={TIME_UNIT}, 지역={len(KEYWORD_GROUPS)}개")
    result_json = request_trend(key_id, key)

    DATA_DIR.mkdir(exist_ok=True)
    # 1) 원본 그대로 저장: 나중에 가공이 틀렸는지 대조할 증거
    RAW_PATH.write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
    # 2) 분석용 표 저장: utf-8-sig 는 엑셀에서 열어도 한글이 깨지지 않게 하는 방식
    table = to_table(result_json)
    table.to_csv(CSV_PATH, encoding="utf-8-sig")

    print(f"저장 완료: {RAW_PATH.name}, {CSV_PATH.name}")
    print(f"행 수(주): {len(table)}  |  기간: {table.index.min()} ~ {table.index.max()}")
    print(f"지역별 빈칸 수: {table.isna().sum().to_dict()}")
    print(table.head())


if __name__ == "__main__":
    main()
