# Stock Deep-Dive AI MVP 아키텍처 분석

## 📋 목차
1. [데이터 수집 및 처리 흐름](#1-데이터-수집-및-처리-흐름)
2. [AI 분석 프로세스](#2-ai-분석-프로세스)
3. [UI 표현 방식](#3-ui-표현-방식)
4. [주요 발견 사항 및 개선 포인트](#4-주요-발견-사항-및-개선-포인트)

---

## 1. 데이터 수집 및 처리 흐름

### 1.1 데이터 소스 및 수집 방식

**데이터 소스:**
- **yfinance**: 주식 시장 데이터, 재무제표, 뉴스, 캘린더 정보
- **pandas-ta** (옵션): 기술적 지표 계산 (없을 경우 직접 계산)

**데이터 수집 클래스: `StockDataManager`**

#### A. 기본 정보 수집 (`get_profile()`)
```python
# yfinance.ticker.info 활용
- sector, industry, country
- marketCap, beta
- longName, currentPrice, previousClose
- changePercent (자동 계산)
```

**처리 방식:**
- `info` 딕셔너리에서 직접 추출
- `None`/`NaN` 값은 `'N/A'`로 처리
- Change %는 `(currentPrice - previousClose) / previousClose * 100`로 계산

---

#### B. 재무 데이터 수집 및 파생 지표 계산 (`get_financials()`)

**원본 데이터 (Raw Data):**
```python
# 연간 재무제표 (최근 3년)
- income_stmt (손익계산서)
- balance_sheet (재무상태표)
- cashflow (현금흐름표)

# 쿼터별 재무제표 (최근 12쿼터 = 3년)
- quarterly_income_stmt
- quarterly_balance_sheet
- quarterly_cashflow
```

**데이터 구조 변환:**
- 원본 DataFrame은 컬럼이 날짜, 행이 재무 항목
- `T (Transpose)` 후: **행(Index) = 날짜, 컬럼 = 재무 항목**으로 변환
- 시계열 분석 용이하도록 구조 변경

**파생 지표 (Derived Metrics) - 6가지:**

1. **Quality of Earnings** (`_calculate_quality_of_earnings`)
   - 공식: `OCF / Net Income`
   - Warning: < 1.0일 경우 경고 플래그
   - 추세: 3년 데이터 비교하여 Improving/Declining/Stable 판별

2. **Receivables Turnover** (`_calculate_receivables_turnover`)
   - 공식: `Revenue / Receivables`
   - 추세: Improving/Declining/Stable

3. **Inventory Turnover** (`_calculate_inventory_turnover`)
   - 공식: `COGS / Inventory`
   - 추세: Improving/Declining/Stable

4. **Interest Coverage Ratio** (`_calculate_interest_coverage`)
   - 공식: `EBIT / Interest Expense`
   - 상태: Strong (≥5.0) / Weak (≥1.0) / Critical (<1.0)

5. **CapEx Growth** (`_calculate_capex_growth`)
   - 공식: `((Current CapEx - Previous CapEx) / Previous CapEx) * 100`
   - 추세: Expanding/Contracting/Stable

6. **Net Buyback Yield** (`_calculate_net_buyback_yield`)
   - 공식: `(Repurchase - Issuance) / Market Cap * 100`
   - 상태: Positive/Negative/Neutral

**에러 처리:**
- 모든 지표 계산 시 `None`, `NaN`, 분모가 `0`인 경우 → `'N/A'` 반환
- 예외 발생 시 빈 구조체 반환 (에러 없이 계속 진행)

**특징:**
- 재무 항목명이 다양한 경우 대응 (다양한 키 이름 체크)
  - 예: OCF → `['Operating Cash Flow', 'Total Cash From Operating Activities', ...]`
  - 예: Net Income → `['Net Income', 'NetIncome', ...]`

---

#### C. 기술적 지표 수집 (`get_technicals()`)

**원본 데이터:**
- `ticker.history(period="1y", interval="1d")`: 1년간 일봉 데이터

**계산 지표:**

1. **RSI(14)**
   - pandas-ta 사용 가능 시: `ta.rsi(Close, length=14)`
   - 없을 경우: `_calculate_rsi()` 직접 계산

2. **TRIX(30)**
   - pandas-ta 사용 가능 시: `ta.trix(Close, length=30)`
   - 없을 경우: `_calculate_trix()` 직접 계산
   - TRIX Signal: TRIX의 9일 EMA

3. **Moving Averages**
   - MA_20, MA_60, MA_120 (Simple Moving Average)

4. **Volume Ratio**
   - 현재 거래량 / 20일 평균 거래량

5. **Earnings D-Day**
   - `ticker.calendar`에서 Earnings Date 추출
   - 오늘로부터 남은 일수 계산

**반환 데이터:**
```python
{
    'price_data': hist (DataFrame),
    'current_rsi': float,
    'current_trix': float,
    'current_trix_signal': float,
    'ma_data': {'MA_20': float, 'MA_60': float, 'MA_120': float},
    'volume_ratio': float,
    'earnings_date': str,
    'earnings_d_day': int
}
```

---

#### D. 뉴스 컨텍스트 수집 (`get_news_context()`)

**최신 뉴스 (`_get_recent_news`):**
- `ticker.news`: 최신 10개 뉴스
- 추출 정보:
  - title, link, publisher, publishTime, summary

**과거 변동성 높은 날짜 (`_get_historical_news_context`):**
- 1년간 주가 데이터에서 일일 변동률(Change %) 계산
- 절대값 기준 상위 5일 추출
- 각 날짜별 정보:
  - date, change_pct, close_price, volume

**참고:**
- PRD에서 요구한 `duckduckgo_search`를 통한 과거 날짜 키워드 검색은 현재 **구현되지 않음**
- 대신 변동성 높은 날짜만 추출 (뉴스 검색 없음)

---

### 1.2 데이터 처리 특징

**안전한 값 추출:**
- `_safe_get_numeric()`: info 딕셔너리에서 안전하게 숫자 추출
- `_safe_get_latest()`: 시리즈의 최신 값 안전하게 추출
- 모든 계산 함수에서 예외 처리 및 `'N/A'` 반환

**데이터 구조:**
- 재무제표는 Transpose하여 시계열 분석 용이하게 구성
- 파생 지표는 딕셔너리 구조로 추세/상태 정보 포함

---

## 2. AI 분석 프로세스

### 2.1 AI 엔진
- **Google Gemini API** (`gemini-2.5-flash` 또는 `gemini-2.5-flash-lite`)
- 모델 선택 가능 (사이드바에서)

### 2.2 리포트 생성 방식

**메서드: `generate_report()`**

**4단계로 나누어 순차적 API 호출:**

#### Step 1: Macro/Industry Analysis (`_generate_macro_analysis`)
**전달 데이터:**
- Company Name, Sector, Industry, Country, Market Cap, Beta

**AI 프롬프트 요청 사항:**
1. 해당 국가/산업의 거시경제 요인 (금리, 환율)
2. 산업 경쟁 구도 및 시장 포지션
3. 회사의 경쟁 우위(Moat) 및 가치 사슬 위치

**출력:** 거시경제 및 산업 분석 텍스트

---

#### Step 2: Forensic Financial Check (`_generate_forensic_analysis`)
**전달 데이터:**
- 6가지 포렌식 지표 (Quality of Earnings, Turnover 지표, Interest Coverage, CapEx Growth, Net Buyback Yield)
- 각 지표의 값, 추세, 상태

**AI 프롬프트 요청 사항:**
1. 이익의 질 및 잠재적 회계 부정 가능성
2. 활동성 비율 추세 (회전율 하락 = 위험)
3. 재무 안정성
4. 경고 신호 또는 우려사항

**특별 지시:**
- 지표가 "N/A"인 경우: "Data Not Available - Some forensic analysis excluded due to missing data" 명시

**출력:** 재무 포렌식 분석 텍스트

---

#### Step 3: Strategy Fit Assessment (`_generate_strategy_analysis`)
**전달 데이터:**
- 투자 전략 (Growth / Value)
- CapEx Growth, Net Buyback Yield, Market Cap

**Growth Mode 프롬프트:**
- 매출 성장 추세
- 자본지출 확장
- 시장 점유율 잠재력
- 혁신/R&D 투자

**Value Mode 프롬프트:**
- 자유현금흐름 창출
- 배당 수익률
- 자사주 매입 프로그램
- 부채 감소
- 밸류에이션 지표

**출력:** 전략 적합성 평가 텍스트

---

#### Step 4: Technical Timing & Final Verdict (`_generate_timing_verdict`)
**전달 데이터:**
- Current Price
- RSI(14), TRIX(30), Signal
- MA (20d, 60d, 120d)
- Volume Ratio
- Next Earnings (D-Day)
- Recent News Headlines (Top 3)

**AI 프롬프트 요청 사항:**
1. 기술적 타이밍 분석 (RSI, TRIX, MA 신호)
2. 실적 발표 근접 경고 (D-Day ≤ 7일: "Volatility Warning - Wait and See")
3. 구체적인 진입가 제안 ($)
4. 최종 판단: **STRONG BUY** / **BUY** / **HOLD** / **SELL**

**출력:** 기술적 타이밍 분석 및 최종 판단 텍스트

---

### 2.3 리포트 구성

**구성:**
```markdown
# Stock Analysis Report

**Ticker**: {ticker} | **Strategy**: {strategy}
---

## Executive Summary
- Company, Sector, Industry, Current Price

---

## Macro & Industry Analysis
{Step 1 결과}

---

## Forensic Financial Check
{Step 2 결과}

---

## Strategy Fit Assessment
{Step 3 결과}

---

## Technical Timing Analysis & Final Verdict
{Step 4 결과}

---
```

**언어 지원:**
- 영어 (기본) / 한국어 (선택 가능)

**API 호출 제어:**
- 각 단계 사이 `time.sleep(2)` (Rate Limiting 대응)
- 429 에러 시 재시도 (최대 2회, 35초 대기)

---

### 2.4 AI 점수 계산 (`calculate_ai_score`)

**점수 기준 (0-100):**

1. **Quality of Earnings**
   - ≥ 1.2: +10점
   - ≥ 1.0: +5점
   - < 0.8: -10점

2. **Interest Coverage**
   - ≥ 5.0: +10점
   - ≥ 1.0: +5점
   - < 1.0: -10점

3. **RSI**
   - 30 ≤ RSI ≤ 70: +5점
   - RSI < 30 (Oversold): +10점
   - RSI > 70 (Overbought): -5점

4. **Earnings D-Day**
   - > 7일: +5점
   - ≤ 7일: -5점

5. **Strategy별 추가 점수**
   - Growth: CapEx Growth > 0 → +5점
   - Value: Net Buyback Yield Positive → +5점

**최종 판단 (`get_verdict`):**
- 80점 이상: 🟢 STRONG BUY
- 65점 이상: 🟢 BUY
- 45점 이상: 🟡 HOLD
- 45점 미만: 🔴 SELL

---

## 3. UI 표현 방식

### 3.1 레이아웃 구조

**사이드바 (Sidebar):**
- Title: "📈 Stock Deep-Dive AI"
- Gemini API Key 입력 (password 타입)
- Ticker 입력
- Investment Style 라디오 버튼 (🚀 Growth / 🛡️ Value)
- Language 라디오 버튼 (🇺🇸 English / 🇰🇷 한국어)
- Gemini Model 라디오 버튼 (flash / flash-lite)
- "Run Analysis" 버튼

**메인 영역:**

#### Header
- 4개 컬럼:
  1. Company (longName)
  2. Ticker
  3. Current Price (Change %)
  4. AI Score (0-100)
- Verdict 배지 (🟢 STRONG BUY / 🟡 HOLD / 🔴 SELL)

#### 탭 구조 (4개)

---

### 3.2 Tab 1: Executive Summary

**표시 내용:**
1. **AI 리포트 전체** (Markdown 렌더링)
   - `st.session_state.ai_report`를 `st.markdown()`으로 표시

2. **Performance Radar Chart** (Plotly)
   - 5개 축: Growth, Stability, Profitability, Momentum, Value
   - 값 계산:
     - Growth: CapEx Growth
     - Stability: Interest Coverage
     - Profitability: Quality of Earnings
     - Momentum: RSI
     - Value: Net Buyback Yield
   - N/A 값은 50으로 대체

---

### 3.3 Tab 2: Macro & Industry

**표시 내용:**
1. **AI 리포트에서 Macro 섹션 추출**
   - `st.session_state.ai_report`에서 "## Macro & Industry Analysis" 섹션 찾아서 표시
   - 문자열 파싱으로 섹션 추출

2. **Company Profile 테이블**
   - Sector, Industry, Country
   - Market Cap, Beta

---

### 3.4 Tab 3: Financials

**표시 내용:**

1. **Forensic Check 테이블** (DataFrame)
   - 6개 지표:
     - Quality of Earnings (OCF/Net Income)
     - Receivables Turnover
     - Inventory Turnover
     - Interest Coverage Ratio
     - CapEx Growth
     - Net Buyback Yield
   - 컬럼: Metric, Value, Trend, Status (✅/⚠️/🔴)

2. **Revenue & Net Income Chart** (Plotly Bar Chart)
   - 3년간 연간 데이터
   - Transpose된 DataFrame에서 날짜별 Revenue, Net Income 추출
   - Grouped Bar Chart

3. **Free Cash Flow vs CapEx Chart** (Plotly Line Chart)
   - 3년간 연간 데이터
   - FCF 계산: OCF - CapEx (또는 직접 사용 가능한 경우)
   - CapEx는 절댓값으로 표시 (음수인 경우)

---

### 3.5 Tab 4: Technicals

**표시 내용:**

1. **Price Chart with Moving Averages** (Plotly Candlestick)
   - Candlestick 차트 (1년 데이터)
   - MA 라인 (20d, 60d, 120d)
   - Historical Events 핀 (📌)
     - 변동성 높은 날짜에 다이아몬드 마커 표시
     - 상승: 초록색, 하락: 빨간색

2. **RSI Indicator Sub-chart** (Plotly Subplot)
   - 상단: Close Price (Line)
   - 하단: RSI(14) (Line)
   - 수평선: Overbought (70, 빨강), Oversold (30, 초록)

3. **TRIX Indicator Sub-chart** (Plotly Subplot)
   - 상단: Close Price (Line)
   - 하단: TRIX(30) (Line), TRIX Signal (Dashed Line)
   - Zero Line 표시

4. **Technical Indicators Summary**
   - 4개 컬럼: RSI(14), TRIX(30), Volume Ratio, Next Earnings

5. **Earnings Alert** (Warning)
   - D-Day ≤ 7일: "⚠️ Earnings Alert: Next earnings in X days. High volatility expected."

6. **Recent News Feed** (Expander)
   - 최신 5개 뉴스
   - 각 뉴스: Title (Expander), Publisher, PublishTime, Link, Summary

---

### 3.3 세션 상태 관리

**Streamlit Session State:**
```python
- st.session_state.data: 수집된 모든 데이터
- st.session_state.ai_report: AI 리포트 텍스트
- st.session_state.ai_score: AI 점수 (0-100)
- st.session_state.verdict: 최종 판단 (STRONG BUY 등)
```

**데이터 플로우:**
1. "Run Analysis" 클릭
2. `StockDataManager`로 데이터 수집 → `st.session_state.data` 저장
3. `AIAnalyst`로 리포트 생성 → `st.session_state.ai_report` 저장
4. 점수 계산 → `st.session_state.ai_score` 저장
5. Verdict 결정 → `st.session_state.verdict` 저장
6. 탭에서 데이터 읽어서 표시

---

## 4. 주요 발견 사항 및 개선 포인트

### 4.1 데이터 수집 관련

**✅ 잘 구현된 부분:**
- 안전한 에러 처리 (`'N/A'` 반환)
- 다양한 재무 항목명 대응
- 데이터 구조 변환 (Transpose)로 시계열 분석 용이

**⚠️ 개선 필요 사항:**

1. **과거 뉴스 검색 미구현**
   - PRD에서 요구한 `duckduckgo_search`를 통한 과거 변동성 높은 날짜의 키워드 검색이 구현되지 않음
   - 현재는 변동성 높은 날짜만 추출 (뉴스 내용 없음)

2. **데이터 캐싱 없음**
   - 같은 티커 재분석 시 매번 yfinance API 호출
   - `requests-cache`는 requirements.txt에 있지만 활용 안 함

3. **쿼터별 데이터 활용 안 함**
   - 쿼터별 재무제표는 수집하지만 실제 분석에서 사용하지 않음

4. **뉴스 Sentiment 분석 없음**
   - 뉴스는 수집하지만 감정 분석(Positive/Negative)을 하지 않음
   - PRD에서 요구한 "Sentiment Tags" 없음

---

### 4.2 AI 분석 관련

**✅ 잘 구현된 부분:**
- 4단계로 나누어 체계적 분석
- Strategy별 차별화된 프롬프트
- Rate Limiting 대응 (재시도 로직)

**⚠️ 개선 필요 사항:**

1. **프롬프트 최적화 부족**
   - 시스템 프롬프트(`_build_system_prompt`)를 생성하지만 실제로 사용하지 않음
   - 각 단계별 프롬프트가 간단하여 컨텍스트가 제한적

2. **데이터 전달 방식 비효율**
   - 모든 데이터를 문자열로 변환하여 프롬프트에 포함
   - 큰 데이터셋의 경우 토큰 낭비 가능

3. **AI 점수 계산 단순**
   - Rule-based 계산 (AI 활용 없음)
   - PRD에서 요구한 "Radar Chart" 값과 점수 계산 방식 불일치

4. **Executive Summary 미세분화**
   - 현재는 전체 리포트 표시
   - PRD에서 요구한 "3-bullet summary (Key Strength, Main Risk, Action Plan)" 없음

---

### 4.3 UI 표현 관련

**✅ 잘 구현된 부분:**
- 4개 탭으로 명확한 구조
- Plotly 차트 활용 (인터랙티브)
- 에러 처리 및 안내 메시지

**⚠️ 개선 필요 사항:**

1. **AI 리포트 파싱 방식 취약**
   - `st.session_state.ai_report`에서 문자열 검색으로 섹션 추출
   - AI 출력 형식이 바뀌면 파싱 실패 가능

2. **Radar Chart 값 임의 조정**
   - N/A 값은 50으로 대체 (의미 없음)
   - 실제 지표 값을 0-100 스케일로 정규화 필요

3. **뉴스 Sentiment 표시 없음**
   - PRD에서 요구한 "Sentiment Tags [Positive/Negative]" 없음

4. **Peer Comparison 없음**
   - PRD에서 요구한 "Peer Comparison: Simple metrics comparison table" 없음

5. **이벤트 핀 상세 정보 없음**
   - 차트에 표시는 하지만 해당 날짜의 뉴스/이벤트 정보 없음

6. **진행 상황 표시 개선 필요**
   - Progress Bar와 Status Text는 있지만 각 단계별 세부 진행 상황 없음

---

### 4.4 코드 품질 관련

**⚠️ 개선 필요 사항:**

1. **에러 처리 일관성**
   - 일부 함수는 예외를 출력만 하고, 일부는 반환
   - 통일된 에러 처리 패턴 필요

2. **코드 중복**
   - `_format_number()`가 `app.py`와 `ai_analyst.py`에 중복
   - `_calculate_rsi()`, `_calculate_trix()` 등이 `data_manager.py`와 `app.py`에 중복 구현

3. **하드코딩된 값**
   - 차트 색상, 임계값 등이 하드코딩
   - 설정 파일로 분리 필요

4. **테스트 코드 없음**
   - 단위 테스트, 통합 테스트 없음

---

## 5. 데이터 플로우 다이어그램

```
User Input (Ticker, Strategy)
    ↓
app.py: Run Analysis Button
    ↓
StockDataManager 초기화
    ↓
├── get_profile() → yfinance.ticker.info
├── get_financials() → yfinance 재무제표 + 파생 지표 계산
├── get_technicals() → yfinance.history + 기술적 지표 계산
└── get_news_context() → yfinance.news + 변동성 높은 날짜 추출
    ↓
st.session_state.data 저장
    ↓
AIAnalyst 초기화 (Gemini API)
    ↓
generate_report() (4단계 순차 호출)
    ├── _generate_macro_analysis()
    ├── _generate_forensic_analysis()
    ├── _generate_strategy_analysis()
    └── _generate_timing_verdict()
    ↓
st.session_state.ai_report 저장
    ↓
calculate_ai_score() → Rule-based 점수 계산
    ↓
get_verdict() → 최종 판단
    ↓
UI 렌더링 (4개 탭)
    ├── Executive Summary (AI 리포트 + Radar Chart)
    ├── Macro & Industry (AI 리포트 섹션 + Profile)
    ├── Financials (Forensic Table + Charts)
    └── Technicals (Price Chart + Indicators + News)
```

---

## 6. 개선 우선순위 제안

### High Priority
1. **AI 리포트 파싱 개선**: 구조화된 출력 또는 JSON 응답 요청
2. **뉴스 Sentiment 분석 추가**: AI 또는 라이브러리 활용
3. **Executive Summary 세부화**: 3-bullet summary 생성
4. **Radar Chart 값 정규화**: 실제 지표를 0-100 스케일로 변환

### Medium Priority
5. **과거 뉴스 검색 구현**: duckduckgo_search 활용
6. **데이터 캐싱**: 같은 티커 재분석 시 캐시 활용
7. **Peer Comparison 추가**: 동일 산업 종목 비교
8. **프롬프트 최적화**: 시스템 프롬프트 활용 및 컨텍스트 확장

### Low Priority
9. **코드 리팩토링**: 중복 제거, 에러 처리 통일
10. **테스트 코드 작성**: 단위 테스트, 통합 테스트
11. **설정 파일 분리**: 하드코딩된 값 관리

---

**분석 완료일**: 2025-01-XX
**분석 대상**: `/Users/reo.kim/Desktop/재무제표 분석 봇/stock` 폴더

