# yfinance Library Technical Documentation for Stock Deep-Dive AI

이 문서는 'Stock Deep-Dive AI' 개발을 위해 `yfinance` 라이브러리의 핵심 기능, 데이터 구조, 모범 사례를 정의합니다. Cursor AI는 이 문서를 참조하여 주식 분석 도구의 코드를 생성해야 합니다.

## 1. 개요 (Overview)
`yfinance`는 Yahoo Finance의 공개 API를 통해 주식 시장 데이터, 재무 제표, 기업 정보 등을 가져오는 파이썬 라이브러리입니다.

- **패키지 명:** `yfinance`
- **일반적 import:** `import yfinance as yf`

## 2. 핵심 모듈 및 사용법 (Core Modules)

### A. Ticker 모듈 (단일 종목 분석)
특정 종목의 상세 데이터를 가져올 때 사용합니다. 'Stock Deep-Dive'의 개별 기업 분석 기능에 필수적입니다.

```python
msft = yf.Ticker("MSFT")

주요 속성 (Attributes) 및 메서드:
기업 기본 정보 (info):

msft.info: 딕셔너리 형태. sector, industry, marketCap, trailingPE, forwardPE, auditRisk 등 수백 가지 메타데이터 포함.

과거 시세 데이터 (history):

가장 중요한 메서드. DataFrame(Open, High, Low, Close, Volume, Dividends, Stock Splits) 반환.

period: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max".

interval: "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo".

# 예시: 최근 1년간의 일별 데이터
hist = msft.history(period="1y")
재무 제표 (Financials) - DataFrame 반환:

손익계산서: msft.income_stmt (연간), msft.quarterly_income_stmt (분기).

대차대조표: msft.balance_sheet (연간), msft.quarterly_balance_sheet (분기).

현금흐름표: msft.cashflow (연간), msft.quarterly_cashflow (분기).

주의: 열(Columns)은 날짜이며, 행(Index)은 계정 항목임.

주주 정보 (Holders):

msft.major_holders: 주요 주주 정보.

msft.institutional_holders: 기관 투자자 정보.

msft.mutualfund_holders: 뮤추얼 펀드 보유 정보.

msft.insider_transactions: 내부자 거래 내역.

애널리스트 및 뉴스:

msft.recommendations: 애널리스트 추천 등급 (Strong Buy, Buy, Hold 등).

msft.upgrades_downgrades: 등급 상향/하향 내역.

msft.news: 관련 뉴스 리스트 (딕셔너리 리스트 형태).

옵션 (Options):

msft.options: 옵션 만기일 리스트.

msft.option_chain(date): 특정 만기일의 콜/풋 옵션 데이터.

B. Download 모듈 (대량 데이터/포트폴리오)
여러 종목의 가격 데이터를 한 번에 가져와 비교 분석할 때 사용합니다.


data = yf.download(
    tickers = "SPY AAPL MSFT",  # 공백으로 구분된 문자열 또는 리스트
    period = "1y",
    interval = "1d",
    group_by = 'ticker',        # 'ticker' 또는 'column'
    auto_adjust = True,         # 배당/분할 수정 주가 반영 여부
    prepost = False,            # 장전/장후 거래 포함 여부
    threads = True,             # 멀티스레딩 사용
)
3. 고급 기능 및 최적화 (Advanced Usage)
Yahoo Finance API는 과도한 요청 시 IP 차단(Rate Limiting)이 발생할 수 있습니다. 안정적인 'Stock Deep-Dive AI'를 위해 **캐싱(Caching)**과 세션 관리를 반드시 구현해야 합니다.

A. RequestsCache를 이용한 캐싱 (필수)
requests_cache 라이브러리를 사용하여 API 호출 횟수를 줄이고 응답 속도를 높여야 합니다.


from requests import Session
from requests_cache import CachedSession

# 캐시 세션 생성 (예: sqlite DB에 저장, 유효기간 1일)
session = CachedSession('yfinance.cache', expire_after=3600*24)

# 사용자 에이전트 헤더 설정 (차단 방지)
session.headers['User-agent'] = 'my-stock-deep-dive-ai/1.0'

# Ticker 생성 시 session 전달
msft = yf.Ticker("MSFT", session=session)
B. 예외 처리 (Error Handling)
데이터가 없거나 티커가 상장 폐지된 경우 빈 DataFrame이나 None이 반환될 수 있습니다.

history() 호출 후 if df.empty: 체크 필수.

info 키 접근 시 try-except 블록이나 .get() 메서드 사용 권장 (모든 종목이 모든 info 키를 갖지 않음).

4. 데이터 구조 예시 (Data Examples)
Financials DataFrame 구조
msft.income_stmt 호출 시: | Index | 2023-06-30 | 2022-06-30 | ... | | :--- | :--- | :--- | :--- | | Total Revenue | 211915000000 | 198270000000 | ... | | Net Income | 72361000000 | 72738000000 | ... |

분석 시 .T (Transpose)를 사용하여 시계열 분석을 용이하게 하는 것이 좋음.

5. Stock Deep-Dive AI 구현 가이드라인
데이터 검증: yf.download나 Ticker 데이터 수신 후 반드시 데이터 존재 여부를 검증할 것.

재무 비율 계산: info에서 제공하지 않는 심층 비율(예: F-Score, Altman Z-Score)은 financials와 balance_sheet의 원본 데이터를 이용해 직접 계산 로직을 구현할 것.

날짜 처리: 모든 날짜 데이터는 pandas.Timestamp 또는 datetime 객체로 통일하여 처리할 것.

섹터 비교: Ticker("종목").info['sector']를 통해 경쟁사(Peers)를 식별하고 비교 분석 기능을 구현할 것.

Reference Docs:

https://ranaroussi.github.io/yfinance/index.html

https://ranaroussi.github.io/yfinance/advanced/index.html

https://ranaroussi.github.io/yfinance/reference/index.html