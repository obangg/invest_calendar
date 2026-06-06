#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
미국주식 투자 캘린더 자동 생성기
- 실적 발표일: yfinance로 자동 수집
- 경제지표(FOMC/CPI/PCE): 아래 고정 목록 (연 1회 정도 갱신)
실행하면 calendar.ics 파일이 생성/갱신됩니다.
"""

from datetime import datetime, timedelta
import uuid
import yfinance as yf

# ════════════════════════════════════════════════════════════
#  여기만 수정하세요
# ════════════════════════════════════════════════════════════

# ① 관심 종목: 티커와 한글 이름. 추가하려면 줄 하나만 더 넣으면 됩니다.
TICKERS = {
    "NVDA": "엔비디아",
    "AVGO": "브로드컴",
    "ARM":  "암 홀딩스",
    "FLNC": "플루언스 에너지",
    "BE":   "블룸에너지",
    "ASTS": "AST스페이스모바일",
    "RKLB": "로켓랩",
    "RDDT": "레딧",
    # "TSLA": "테슬라",      ← 이런 식으로 추가
}

# ② 경제지표 고정 일정 (미국 동부시간 기준)
#    형식: (제목, "YYYY-MM-DD HH:MM", 설명)
ECON_EVENTS = [
    # FOMC (정책성명 14:00 ET)
    ("🏦 [FOMC] 6월 금리결정 + 점도표",  "2026-06-17 14:00", "FOMC 성명 14:00 ET, 기자회견 14:30 ET. 점도표(SEP) 동반."),
    ("🏦 [FOMC] 7월 금리결정",          "2026-07-29 14:00", "FOMC 성명 14:00 ET, 기자회견 14:30 ET."),
    ("🏦 [FOMC] 9월 금리결정 + 점도표",  "2026-09-16 14:00", "FOMC 성명 14:00 ET, 기자회견 14:30 ET. 점도표(SEP) 동반."),
    ("🏦 [FOMC] 10월 금리결정",         "2026-10-28 14:00", "FOMC 성명 14:00 ET, 기자회견 14:30 ET."),
    ("🏦 [FOMC] 12월 금리결정 + 점도표", "2026-12-09 14:00", "FOMC 성명 14:00 ET, 기자회견 14:30 ET. 점도표(SEP) 동반."),

    # CPI (08:30 ET)
    ("📈 [CPI] 5월 소비자물가지수",  "2026-06-10 08:30", "BLS CPI 발표 08:30 ET."),
    ("📈 [CPI] 6월 소비자물가지수",  "2026-07-14 08:30", "BLS CPI 발표 08:30 ET."),
    ("📈 [CPI] 7월 소비자물가지수",  "2026-08-12 08:30", "BLS CPI 발표 08:30 ET."),
    ("📈 [CPI] 8월 소비자물가지수",  "2026-09-11 08:30", "BLS CPI 발표 08:30 ET."),
    ("📈 [CPI] 9월 소비자물가지수",  "2026-10-14 08:30", "BLS CPI 발표 08:30 ET."),
    ("📈 [CPI] 10월 소비자물가지수", "2026-11-10 08:30", "BLS CPI 발표 08:30 ET."),
    ("📈 [CPI] 11월 소비자물가지수", "2026-12-10 08:30", "BLS CPI 발표 08:30 ET."),

    # PCE = Personal Income and Outlays (08:30 ET)
    ("💵 [PCE] 5월 개인소비지출 물가지수",  "2026-06-25 08:30", "BEA 발표 08:30 ET. 근원 PCE는 연준 최우선 지표."),
    ("💵 [PCE] 6월 개인소비지출 물가지수",  "2026-07-30 08:30", "BEA 발표 08:30 ET. 근원 PCE 주목."),
    ("💵 [PCE] 7월 개인소비지출 물가지수",  "2026-08-26 08:30", "BEA 발표 08:30 ET. 근원 PCE 주목."),
    ("💵 [PCE] 8월 개인소비지출 물가지수",  "2026-09-30 08:30", "BEA 발표 08:30 ET. 근원 PCE 주목."),
    ("💵 [PCE] 9월 개인소비지출 물가지수",  "2026-10-29 08:30", "BEA 발표 08:30 ET. 근원 PCE 주목."),
    ("💵 [PCE] 10월 개인소비지출 물가지수", "2026-11-25 08:30", "BEA 발표 08:30 ET. 근원 PCE 주목."),
    ("💵 [PCE] 11월 개인소비지출 물가지수", "2026-12-23 08:30", "BEA 발표 08:30 ET. 근원 PCE 주목."),
]

OUTPUT_FILE = "calendar.ics"
CAL_NAME = "미국주식 투자 캘린더"

# ════════════════════════════════════════════════════════════
#  이 아래는 건드릴 필요 없습니다
# ════════════════════════════════════════════════════════════


def fetch_earnings():
    """yfinance로 각 종목의 다음 실적일 수집. 실패한 종목은 건너뜀."""
    events = []
    for ticker, kor in TICKERS.items():
        try:
            cal = yf.Ticker(ticker).calendar
            dates = None
            if isinstance(cal, dict):
                dates = cal.get("Earnings Date")
            if not dates:
                print(f"  [건너뜀] {ticker}: 실적일 데이터 없음")
                continue
            # 리스트면 첫 항목 사용
            d = dates[0] if isinstance(dates, (list, tuple)) else dates
            # date/datetime 모두 대응
            dt = datetime(d.year, d.month, d.day, 16, 30)  # 장 마감 후로 표기
            title = f"📊 [어닝] {ticker} {kor}"
            desc = f"{kor}({ticker}) 실적 발표 예상. yfinance 자동 수집 — 회사 공식 공지로 확정 시 며칠 달라질 수 있음."
            events.append((title, dt, dt + timedelta(minutes=30), desc))
            print(f"  [수집] {ticker}: {dt.date()}")
        except Exception as e:
            print(f"  [오류] {ticker}: {e}")
    return events


def build_econ():
    events = []
    for title, dtstr, desc in ECON_EVENTS:
        dt = datetime.strptime(dtstr, "%Y-%m-%d %H:%M")
        events.append((title, dt, dt + timedelta(minutes=30), desc))
    return events


def esc(t):
    return t.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def fmt(dt):
    return dt.strftime("%Y%m%dT%H%M%S")


VTIMEZONE = """BEGIN:VTIMEZONE
TZID:America/New_York
X-LIC-LOCATION:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE"""


def build_ics(events):
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//Investment Calendar//KR//", "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH", f"X-WR-CALNAME:{CAL_NAME}",
        "X-WR-TIMEZONE:America/New_York",
    ]
    lines += VTIMEZONE.split("\n")
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for title, start, end, desc in events:
        lines += [
            "BEGIN:VEVENT", f"UID:{uuid.uuid4()}@invest-cal",
            f"DTSTAMP:{stamp}",
            f"DTSTART;TZID=America/New_York:{fmt(start)}",
            f"DTEND;TZID=America/New_York:{fmt(end)}",
            f"SUMMARY:{esc(title)}", f"DESCRIPTION:{esc(desc)}",
            "TRANSP:TRANSPARENT",
            "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY",
            f"DESCRIPTION:{esc('[내일] ' + title)}", "END:VALARM",
            "BEGIN:VALARM", "TRIGGER:-PT1H", "ACTION:DISPLAY",
            f"DESCRIPTION:{esc('[1시간 후] ' + title)}", "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


if __name__ == "__main__":
    print("실적일 수집 중...")
    earnings = fetch_earnings()
    econ = build_econ()
    all_events = earnings + econ
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(build_ics(all_events))
    print(f"\n완료: {OUTPUT_FILE} (실적 {len(earnings)}건 + 경제지표 {len(econ)}건 = 총 {len(all_events)}건)")
