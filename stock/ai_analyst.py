"""
AIAnalyst: Google Gemini API를 활용한 주식 분석 리포트 생성 클래스
"""

import google.generativeai as genai
from typing import Dict, Any, Optional, Tuple
import json
import pandas as pd
import re

try:
    # Try absolute import first (when stock is a package)
    from stock.utils import format_number, safe_execute
except ImportError:
    # Fallback to relative import (when running from stock directory)
    try:
        from .utils import format_number, safe_execute
    except ImportError:
        # Final fallback: direct import (when stock is in sys.path)
        from utils import format_number, safe_execute


class AIAnalyst:
    """Google Gemini API를 사용하여 주식 분석 리포트를 생성하는 클래스"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Args:
            api_key: Google Gemini API 키
            model_name: 사용할 Gemini 모델명 (기본값: 'gemini-2.5-flash')
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # Gemini API 초기화
        genai.configure(api_key=api_key)
        
        # 모델 설정
        try:
            self.model = genai.GenerativeModel(model_name)
        except Exception as e:
            print(f"Warning: Failed to initialize {model_name}, falling back to gemini-2.5-flash")
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.model_name = 'gemini-2.5-flash'
    
    def generate_report(self, ticker: str, data: Dict[str, Any], strategy: str, language: str = "en") -> str:
        """
        주식 분석 리포트 생성 (단일 API 호출)
        
        Args:
            ticker: 주식 티커 심볼 (예: 'AAPL', 'GOOGL')
            data: StockDataManager에서 수집한 모든 데이터
            strategy: 투자 전략 ('Growth' 또는 'Value')
            language: 리포트 언어 ('en' 또는 'ko')
        
        Returns:
            Markdown 형식의 분석 리포트
        """
        try:
            print("   Generating unified analysis report (single API call)...")
            
            # System Prompt 생성
            system_prompt = self._build_unified_system_prompt(ticker, strategy, language)
            
            # User Prompt 생성 (구조화된 데이터)
            user_prompt = self._build_unified_user_prompt(ticker, data, strategy, language)
            
            # 단일 API 호출
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # Gemini API 호출
                    response = self.model.generate_content([
                        system_prompt,
                        user_prompt
                    ])
                    
                    report = response.text
                    
                    # 리포트 파싱 및 검증
                    parsed_report = self._parse_and_validate_report(report, language)
                    
                    return parsed_report
                    
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(35)
                            continue
                    raise e
            
            return f"# Error Generating Report\n\nAPI call failed after {max_retries} attempts."
            
        except Exception as e:
            return f"# Error Generating Report\n\nAn error occurred: {str(e)}\n\nPlease check your API key and try again."
    
    def _build_unified_system_prompt(self, ticker: str, strategy: str, language: str = "en") -> str:
        """
        통합 분석을 위한 System Prompt 생성
        포렌식 기반, 재무지표 1차 근거, 계산 금지 원칙 적용
        """
        strategy_mode = "Growth" if "Growth" in strategy or "🚀" in strategy else "Value"
        
        if language == "ko":
            prompt = f"""너는 포렌식 기반 주식 분석 AI다. {ticker} 주식을 분석한다.

## 핵심 원칙 (절대 준수)

1. **재무 지표 1차 근거 원칙**
   - 제공된 재무 지표를 1차 근거로 반드시 사용한다
   - 제공되지 않은 재무 데이터를 절대 생성하거나 계산하지 않는다
   - 지표가 부정적인 경우, 긍정적 서사로 이를 상쇄하지 않는다

2. **보조 해석 요소**
   - 거시경제/산업/뉴스 컨텍스트는 해석 보정 용도로만 사용한다
   - 재무 지표와 모순되는 해석을 하지 않는다

3. **데이터 부족 처리**
   - 데이터가 부족하면 분석 한계를 명확히 명시한다
   - "N/A" 지표는 "데이터 부족 - 해당 항목 분석 제외"라고 명시한다

4. **계산 금지**
   - AI는 "계산"이 아닌 "분석"만 수행한다
   - 이미 계산된 지표값을 해석하고 평가만 한다

## 분석 순서 (반드시 이 순서로 사고하고 출력)

1. Macro & Industry Context (거시경제/산업 맥락)
2. Forensic Financial Assessment (재무 포렌식 평가)
3. Strategy Fit Assessment (전략 적합성 평가: {strategy_mode})
4. Technical Timing & Event Risk (기술적 타이밍 및 이벤트 리스크)
5. Entry Strategy & Final Verdict (진입 전략 및 최종 판단)

## 판단 규칙 (중요)

- 포렌식 지표 중 경고 신호가 2개 이상이면 Final Rating을 BUY 이상으로 주지 않는다
- Interest Coverage가 Critical(1.0 미만)이면 무조건 HOLD 또는 SELL
- 실적 발표 D-Day가 7일 이내이면 "Volatility Warning"을 명시하고 Confidence Level을 1단계 낮춘다
- Growth 전략인데 CapEx Growth가 Contracting이면 전략 불일치 리스크를 명확히 서술한다

## 출력 포맷 (반드시 이 구조)

# {ticker} 주식 분석 리포트

## 1. Macro & Industry Context

[거시경제 환경 및 산업 동향 분석]

## 2. Forensic Financial Assessment

[재무 포렌식 평가 - 제공된 지표를 1차 근거로 사용]

## 3. Strategy Fit Assessment

[{strategy_mode} 전략 적합성 평가]

## 4. Technical Timing & Event Risk

[기술적 타이밍 및 이벤트 리스크 분석]

## 5. Entry Strategy & Final Verdict

### Suggested Entry Price
$[구체적인 가격]

### Key Risk Factors
- [리스크 1]
- [리스크 2]
- [리스크 3]

### Final Rating
**[STRONG BUY / BUY / HOLD / SELL]**

### Confidence Level
**[High / Medium / Low]**

[최종 판단 근거 및 종합 의견]

---
**중요**: 모든 분석은 제공된 재무 지표를 1차 근거로 하며, 거시경제/뉴스는 보조 해석 요소일 뿐이다."""
        else:
            prompt = f"""You are a forensic-based stock analysis AI. Analyze {ticker} stock.

## Core Principles (MUST FOLLOW)

1. **Financial Metrics First Principle**
   - Use provided financial metrics as PRIMARY evidence
   - NEVER generate or calculate financial data that is not provided
   - When metrics are negative, do NOT compensate with positive narratives

2. **Auxiliary Interpretation Elements**
   - Macro/industry/news context is for INTERPRETIVE ADJUSTMENT only
   - Do NOT contradict financial metrics with interpretations

3. **Missing Data Handling**
   - When data is insufficient, clearly state analysis limitations
   - For "N/A" metrics, explicitly state "Data Not Available - Analysis Excluded"

4. **No Calculation Rule**
   - AI performs "ANALYSIS" only, NOT "CALCULATION"
   - Interpret and evaluate only the provided calculated metrics

## Analysis Order (MUST think and output in this order)

1. Macro & Industry Context
2. Forensic Financial Assessment
3. Strategy Fit Assessment ({strategy_mode})
4. Technical Timing & Event Risk
5. Entry Strategy & Final Verdict

## Judgment Rules (CRITICAL)

- If 2+ forensic warning signals exist, Final Rating MUST NOT be BUY or higher
- If Interest Coverage is Critical (<1.0), MUST be HOLD or SELL
- If Earnings D-Day ≤ 7 days, MUST state "Volatility Warning" and lower Confidence Level by 1 step
- If Growth strategy but CapEx Growth is Contracting, MUST clearly describe strategy mismatch risk

## Output Format (MUST follow this structure)

# {ticker} Stock Analysis Report

## 1. Macro & Industry Context

[Macroeconomic environment and industry dynamics analysis]

## 2. Forensic Financial Assessment

[Forensic financial evaluation - use provided metrics as PRIMARY evidence]

## 3. Strategy Fit Assessment

[{strategy_mode} strategy fit evaluation]

## 4. Technical Timing & Event Risk

[Technical timing and event risk analysis]

## 5. Entry Strategy & Final Verdict

### Suggested Entry Price
$[Specific price]

### Key Risk Factors
- [Risk 1]
- [Risk 2]
- [Risk 3]

### Final Rating
**[STRONG BUY / BUY / HOLD / SELL]**

### Confidence Level
**[High / Medium / Low]**

[Final judgment rationale and comprehensive opinion]

---
**IMPORTANT**: All analysis uses provided financial metrics as PRIMARY evidence. Macro/news are auxiliary interpretation elements only."""
        
        return prompt
    
    def _build_unified_user_prompt(self, ticker: str, data: Dict[str, Any], strategy: str, language: str = "en") -> str:
        """
        통합 분석을 위한 User Prompt 생성
        구조화된 JSON 형태로 데이터 제공
        """
        strategy_mode = "Growth" if "Growth" in strategy or "🚀" in strategy else "Value"
        
        # 데이터 구조화
        profile = data.get('profile', {})
        financials = data.get('financials', {})
        technicals = data.get('technicals', {})
        news_context = data.get('news_context', {})
        metrics = financials.get('derived_metrics', {}) if financials else {}
        
        if language == "ko":
            prompt = f"""다음은 {ticker} 주식의 분석 데이터다. 위에서 제시한 원칙과 순서에 따라 종합 분석 리포트를 작성하라.

---

## 기본 정보

- 티커: {ticker}
- 회사명: {profile.get('longName', 'N/A')}
- 섹터: {profile.get('sector', 'N/A')}
- 산업: {profile.get('industry', 'N/A')}
- 국가: {profile.get('country', 'N/A')}
- 시가총액: ${format_number(profile.get('marketCap', 'N/A'))}
- 현재가: ${profile.get('currentPrice', 'N/A')}
- 변동률: {profile.get('changePercent', 'N/A')}%
- 베타: {profile.get('beta', 'N/A')}
- 투자 전략: {strategy_mode}

---

## 재무 포렌식 지표 (1차 근거)

다음 지표값은 이미 계산되어 제공된다. 계산하지 말고 해석만 하라.

- **Quality of Earnings (OCF/순이익)**: {metrics.get('quality_of_earnings', {}).get('latest', 'N/A')} (추세: {metrics.get('quality_of_earnings', {}).get('trend', 'N/A')})
  - 경고: {metrics.get('quality_of_earnings', {}).get('warning', False)}
  
- **Receivables Turnover (매출채권 회전율)**: {metrics.get('receivables_turnover', {}).get('latest', 'N/A')} (추세: {metrics.get('receivables_turnover', {}).get('trend', 'N/A')})
  
- **Inventory Turnover (재고 회전율)**: {metrics.get('inventory_turnover', {}).get('latest', 'N/A')} (추세: {metrics.get('inventory_turnover', {}).get('trend', 'N/A')})
  
- **Interest Coverage Ratio (이자보상배율)**: {metrics.get('interest_coverage', {}).get('latest', 'N/A')} (상태: {metrics.get('interest_coverage', {}).get('status', 'N/A')})
  
- **CapEx Growth (자본지출 성장률)**: {metrics.get('capex_growth', {}).get('latest', 'N/A')}% (추세: {metrics.get('capex_growth', {}).get('trend', 'N/A')})
  
- **Net Buyback Yield (순 자사주 매입 수익률)**: {metrics.get('net_buyback_yield', {}).get('latest', 'N/A')}% (상태: {metrics.get('net_buyback_yield', {}).get('status', 'N/A')})

**중요**: "N/A" 값은 계산 불가능한 지표다. 해당 항목은 분석에서 제외하되, 한계를 명시하라.

---

## 기술적 지표

- **RSI(14)**: {technicals.get('current_rsi', 'N/A')}
  - {f"과매수 (>70)" if isinstance(technicals.get('current_rsi'), (int, float)) and technicals.get('current_rsi') > 70 else f"과매도 (<30)" if isinstance(technicals.get('current_rsi'), (int, float)) and technicals.get('current_rsi') < 30 else "정상 범위"}
  
- **TRIX(30)**: {technicals.get('current_trix', 'N/A')} (신호: {technicals.get('current_trix_signal', 'N/A')})
  
- **이동평균**: 20일=${technicals.get('ma_data', {}).get('MA_20', 'N/A')} | 60일=${technicals.get('ma_data', {}).get('MA_60', 'N/A')} | 120일=${technicals.get('ma_data', {}).get('MA_120', 'N/A')}
  
- **거래량 비율**: {technicals.get('volume_ratio', 'N/A')}
  
- **다음 실적 발표**: {technicals.get('earnings_date', 'N/A')} (D-{technicals.get('earnings_d_day', 'N/A')})
  - {"⚠️ 실적 발표 7일 이내 - 변동성 경고 필요" if technicals.get('earnings_d_day') is not None and technicals.get('earnings_d_day') <= 7 else ""}

---

## 보조 해석 요소 (거시경제/산업/뉴스)

### 최근 뉴스 (Top 3)
"""
            recent_news = news_context.get('recent_news', [])[:3] if news_context else []
            if recent_news:
                for i, news in enumerate(recent_news, 1):
                    prompt += f"{i}. {news.get('title', 'N/A')} ({news.get('publisher', 'N/A')}, {news.get('publishTime', 'N/A')})\n"
            else:
                prompt += "뉴스 데이터 없음\n"
            
            prompt += """
### 주요 변동일 이벤트 (Top 5)
"""
            historical_events = news_context.get('historical_events', [])[:5] if news_context else []
            if historical_events:
                for i, event in enumerate(historical_events, 1):
                    prompt += f"{i}. {event.get('date', 'N/A')}: {event.get('change_pct', 'N/A')}% (종가: ${event.get('close_price', 'N/A')})\n"
            else:
                prompt += "이벤트 데이터 없음\n"
            
            prompt += """
---

위 데이터를 바탕으로 System Prompt의 원칙과 순서에 따라 종합 분석 리포트를 작성하라.
재무 지표를 1차 근거로 사용하고, 거시경제/뉴스는 보조 해석 요소로만 활용하라."""
        else:
            prompt = f"""Below is the analysis data for {ticker} stock. Generate a comprehensive analysis report following the principles and order specified above.

---

## Basic Information

- Ticker: {ticker}
- Company Name: {profile.get('longName', 'N/A')}
- Sector: {profile.get('sector', 'N/A')}
- Industry: {profile.get('industry', 'N/A')}
- Country: {profile.get('country', 'N/A')}
- Market Cap: ${format_number(profile.get('marketCap', 'N/A'))}
- Current Price: ${profile.get('currentPrice', 'N/A')}
- Change %: {profile.get('changePercent', 'N/A')}%
- Beta: {profile.get('beta', 'N/A')}
- Investment Strategy: {strategy_mode}

---

## Forensic Financial Metrics (PRIMARY EVIDENCE)

The following metrics are already calculated and provided. DO NOT calculate - interpret only.

- **Quality of Earnings (OCF/Net Income)**: {metrics.get('quality_of_earnings', {}).get('latest', 'N/A')} (Trend: {metrics.get('quality_of_earnings', {}).get('trend', 'N/A')})
  - Warning: {metrics.get('quality_of_earnings', {}).get('warning', False)}
  
- **Receivables Turnover**: {metrics.get('receivables_turnover', {}).get('latest', 'N/A')} (Trend: {metrics.get('receivables_turnover', {}).get('trend', 'N/A')})
  
- **Inventory Turnover**: {metrics.get('inventory_turnover', {}).get('latest', 'N/A')} (Trend: {metrics.get('inventory_turnover', {}).get('trend', 'N/A')})
  
- **Interest Coverage Ratio**: {metrics.get('interest_coverage', {}).get('latest', 'N/A')} (Status: {metrics.get('interest_coverage', {}).get('status', 'N/A')})
  
- **CapEx Growth**: {metrics.get('capex_growth', {}).get('latest', 'N/A')}% (Trend: {metrics.get('capex_growth', {}).get('trend', 'N/A')})
  
- **Net Buyback Yield**: {metrics.get('net_buyback_yield', {}).get('latest', 'N/A')}% (Status: {metrics.get('net_buyback_yield', {}).get('status', 'N/A')})

**IMPORTANT**: "N/A" values indicate uncalculable metrics. Exclude from analysis but clearly state the limitation.

---

## Technical Indicators

- **RSI(14)**: {technicals.get('current_rsi', 'N/A')}
  - {f"Overbought (>70)" if isinstance(technicals.get('current_rsi'), (int, float)) and technicals.get('current_rsi') > 70 else f"Oversold (<30)" if isinstance(technicals.get('current_rsi'), (int, float)) and technicals.get('current_rsi') < 30 else "Normal Range"}
  
- **TRIX(30)**: {technicals.get('current_trix', 'N/A')} (Signal: {technicals.get('current_trix_signal', 'N/A')})
  
- **Moving Averages**: 20d=${technicals.get('ma_data', {}).get('MA_20', 'N/A')} | 60d=${technicals.get('ma_data', {}).get('MA_60', 'N/A')} | 120d=${technicals.get('ma_data', {}).get('MA_120', 'N/A')}
  
- **Volume Ratio**: {technicals.get('volume_ratio', 'N/A')}
  
- **Next Earnings**: {technicals.get('earnings_date', 'N/A')} (D-{technicals.get('earnings_d_day', 'N/A')})
  - {"⚠️ Earnings within 7 days - Volatility Warning Required" if technicals.get('earnings_d_day') is not None and technicals.get('earnings_d_day') <= 7 else ""}

---

## Auxiliary Interpretation Elements (Macro/Industry/News)

### Recent News (Top 3)
"""
            recent_news = news_context.get('recent_news', [])[:3] if news_context else []
            if recent_news:
                for i, news in enumerate(recent_news, 1):
                    prompt += f"{i}. {news.get('title', 'N/A')} ({news.get('publisher', 'N/A')}, {news.get('publishTime', 'N/A')})\n"
            else:
                prompt += "No news data available\n"
            
            prompt += """
### Top Volatile Dates (Top 5)
"""
            historical_events = news_context.get('historical_events', [])[:5] if news_context else []
            if historical_events:
                for i, event in enumerate(historical_events, 1):
                    prompt += f"{i}. {event.get('date', 'N/A')}: {event.get('change_pct', 'N/A')}% (Close: ${event.get('close_price', 'N/A')})\n"
            else:
                prompt += "No event data available\n"
            
            prompt += """
---

Based on the above data, generate a comprehensive analysis report following the principles and order in the System Prompt.
Use financial metrics as PRIMARY evidence. Use macro/news as auxiliary interpretation elements only."""
        
        return prompt
    
    def _parse_and_validate_report(self, report: str, language: str = "en") -> str:
        """
        리포트를 파싱하고 검증하여 섹션별 구조 확인
        
        Args:
            report: AI가 생성한 리포트 텍스트
            language: 리포트 언어
        
        Returns:
            검증된 리포트 텍스트
        """
        required_sections = [
            "## 1. Macro & Industry Context",
            "## 2. Forensic Financial Assessment",
            "## 3. Strategy Fit Assessment",
            "## 4. Technical Timing & Event Risk",
            "## 5. Entry Strategy & Final Verdict"
        ]
        
        # 섹션 존재 여부 확인
        missing_sections = []
        for section in required_sections:
            if section not in report:
                missing_sections.append(section)
        
        # Final Verdict 필수 요소 확인
        has_entry_price = "Suggested Entry Price" in report or "Suggested Entry" in report
        has_rating = any(rating in report.upper() for rating in ["STRONG BUY", "BUY", "HOLD", "SELL"])
        has_confidence = any(conf in report for conf in ["Confidence Level", "High", "Medium", "Low"])
        
        # 경고 메시지 생성 (필요시) - 디버깅용
        warnings = []
        if missing_sections:
            warnings.append(f"Missing sections: {', '.join(missing_sections)}")
        if not has_entry_price:
            warnings.append("Missing: Suggested Entry Price")
        if not has_rating:
            warnings.append("Missing: Final Rating")
        if not has_confidence:
            warnings.append("Missing: Confidence Level")
        
        # 리포트 반환 (경고가 있어도 원본 반환, 향후 개선 가능)
        # 실제 운영 환경에서는 warnings를 로깅하거나 사용자에게 표시할 수 있음
        if warnings:
            # 로깅만 하고 리포트는 그대로 반환 (디버깅 편의성)
            print(f"⚠️ Report validation warnings: {' | '.join(warnings)}")
        
        return report
    
    def parse_report_sections(self, report: str) -> Dict[str, str]:
        """
        리포트를 섹션별로 파싱하여 반환 (디버깅 및 분석용)
        
        Args:
            report: 생성된 리포트 텍스트
        
        Returns:
            섹션별 텍스트를 담은 딕셔너리
        """
        
        sections = {
            "macro": "",
            "forensic": "",
            "strategy": "",
            "technical": "",
            "verdict": ""
        }
        
        # 섹션별 정규식 패턴
        patterns = {
            "macro": r'##\s*1\.\s*Macro\s+&\s+Industry\s+Context(.*?)(?=##\s*2\.|$)',
            "forensic": r'##\s*2\.\s*Forensic\s+Financial\s+Assessment(.*?)(?=##\s*3\.|$)',
            "strategy": r'##\s*3\.\s*Strategy\s+Fit\s+Assessment(.*?)(?=##\s*4\.|$)',
            "technical": r'##\s*4\.\s*Technical\s+Timing\s+&\s+Event\s+Risk(.*?)(?=##\s*5\.|$)',
            "verdict": r'##\s*5\.\s*Entry\s+Strategy\s+&\s+Final\s+Verdict(.*?)$'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, report, re.DOTALL | re.IGNORECASE)
            if match:
                sections[key] = match.group(1).strip()
        
        return sections
    
    def _build_system_prompt(self, ticker: str, data: Dict[str, Any], strategy: str) -> str:
        """
        시스템 프롬프트 생성 (PRD의 '5. AI 분석 로직' 반영)
        """
        strategy_mode = "Growth" if "Growth" in strategy or "🚀" in strategy else "Value"
        
        prompt = f"""You are a Chief Investment Officer (CIO) and Forensic Accountant analyzing {ticker} stock.

Your role combines:
1. **Macro Strategist**: Analyze macroeconomic factors (interest rates, currency, industry dynamics)
2. **Forensic Accountant**: Evaluate earnings quality and detect potential accounting irregularities

## Analysis Framework

### 1. Macro/Industry Analysis
- Analyze macroeconomic environment based on the company's Country and Industry
- Discuss interest rate policies, currency impacts, and industry competitive landscape
- Evaluate the company's market position, moat, and value chain position

### 2. Forensic Check
- Evaluate "Quality of Earnings" using Operating Cash Flow (OCF) / Net Income ratio
- Analyze activity ratios (Receivables Turnover, Inventory Turnover) for trends
- Assess stability through Interest Coverage Ratio
- **IMPORTANT**: If any financial metric shows "N/A", explicitly state in the report: "Data Not Available - Some forensic analysis excluded due to missing data"
- Flag potential accounting irregularities if ratios indicate red flags

### 3. Strategy Fit Analysis
**Current Strategy Mode: {strategy_mode}**

"""
        
        if strategy_mode == "Growth":
            prompt += """- **Growth Mode Focus:**
  - Revenue growth trends and sustainability
  - PEG ratio (if available)
  - Capital Expenditure expansion and scalability
  - Market share expansion potential
  - Innovation and R&D investment
"""
        else:
            prompt += """- **Value Mode Focus:**
  - Free Cash Flow generation and sustainability
  - Dividend yield and payout ratio
  - Share buyback programs (Net Buyback Yield)
  - Debt reduction trends
  - Valuation metrics (P/E, P/B, etc.)
"""
        
        prompt += """
### 4. Timing Verdict
- **Earnings Proximity Warning**: If Earnings D-Day is 7 days or less, recommend "Volatility Warning - Wait and See"
- Combine RSI, TRIX signals, and news sentiment to determine entry timing
- Provide specific entry price recommendation ($)
- Final recommendation: **STRONG BUY** / **BUY** / **HOLD** / **SELL**

## Output Format Requirements

1. **Language**: All output must be in English
2. **Format**: Use clear Markdown formatting with headers, bullet points, and tables where appropriate
3. **Structure**: Follow this structure:
   - Executive Summary (3-4 bullet points)
   - Macro/Industry Analysis
   - Forensic Financial Check
   - Strategy Fit Assessment
   - Technical Timing Analysis
   - Final Verdict & Entry Recommendation

4. **Data Handling**: 
   - When data is "N/A", clearly state "Data Not Available" and explain the limitation
   - Do not make assumptions about missing data
   - Focus analysis on available data points

5. **Tone**: Professional, analytical, and actionable
"""
        
        return prompt
    
    def _build_user_prompt(self, data: Dict[str, Any]) -> str:
        """
        사용자 프롬프트 생성 (데이터 요약 - 간결하게)
        """
        prompt = "## Stock Analysis Data for AI Analysis\n\n"
        
        # Profile 정보
        profile = data.get('profile', {})
        if profile:
            prompt += "## Company Profile\n"
            prompt += f"- **Company Name**: {profile.get('longName', 'N/A')}\n"
            prompt += f"- **Ticker**: {profile.get('ticker', 'N/A')}\n"
            prompt += f"- **Sector**: {profile.get('sector', 'N/A')}\n"
            prompt += f"- **Industry**: {profile.get('industry', 'N/A')}\n"
            prompt += f"- **Country**: {profile.get('country', 'N/A')}\n"
            prompt += f"- **Market Cap**: ${format_number(profile.get('marketCap', 'N/A'))}\n"
            prompt += f"- **Current Price**: ${profile.get('currentPrice', 'N/A')}\n"
            prompt += f"- **Change %**: {profile.get('changePercent', 'N/A')}%\n"
            prompt += f"- **Beta**: {profile.get('beta', 'N/A')}\n\n"
        
        # Financials 정보
        financials = data.get('financials', {})
        if financials:
            prompt += "## Financial Metrics\n\n"
            
            # Derived Metrics (간결하게)
            metrics = financials.get('derived_metrics', {})
            if metrics:
                prompt += "### Forensic Metrics\n"
                qoe = metrics.get('quality_of_earnings', {})
                rt = metrics.get('receivables_turnover', {})
                it = metrics.get('inventory_turnover', {})
                ic = metrics.get('interest_coverage', {})
                capex = metrics.get('capex_growth', {})
                buyback = metrics.get('net_buyback_yield', {})
                
                prompt += f"Quality of Earnings: {qoe.get('latest', 'N/A')} (Trend: {qoe.get('trend', 'N/A')})"
                if qoe.get('warning'):
                    prompt += " ⚠️"
                prompt += "\n"
                prompt += f"Receivables Turnover: {rt.get('latest', 'N/A')} ({rt.get('trend', 'N/A')}) | "
                prompt += f"Inventory Turnover: {it.get('latest', 'N/A')} ({it.get('trend', 'N/A')})\n"
                prompt += f"Interest Coverage: {ic.get('latest', 'N/A')} ({ic.get('status', 'N/A')}) | "
                prompt += f"CapEx Growth: {capex.get('latest', 'N/A')}% ({capex.get('trend', 'N/A')})\n"
                prompt += f"Net Buyback Yield: {buyback.get('latest', 'N/A')}% ({buyback.get('status', 'N/A')})\n\n"
            
            # Raw Data 요약 (간결하게)
            raw_data = financials.get('raw_data', {})
            annual_data = raw_data.get('annual', {})
            if annual_data and not annual_data.get('income_stmt', pd.DataFrame()).empty:
                income_stmt = annual_data['income_stmt']
                prompt += "### Annual Financial Summary\n"
                try:
                    if 'Total Revenue' in income_stmt.columns:
                        latest_revenue = income_stmt['Total Revenue'].iloc[0]
                        prompt += f"- Revenue: ${format_number(latest_revenue)}\n"
                    if 'Net Income' in income_stmt.columns:
                        latest_ni = income_stmt['Net Income'].iloc[0]
                        prompt += f"- Net Income: ${format_number(latest_ni)}\n"
                except Exception:
                    pass
                prompt += "\n"
        
        # Technicals 정보 (간결하게)
        technicals = data.get('technicals', {})
        if technicals and not technicals.get('error'):
            prompt += "## Technical Indicators\n"
            rsi = technicals.get('current_rsi', 'N/A')
            rsi_status = ""
            if rsi != 'N/A':
                if rsi > 70:
                    rsi_status = " (Overbought)"
                elif rsi < 30:
                    rsi_status = " (Oversold)"
            prompt += f"RSI(14): {rsi}{rsi_status} | TRIX(30): {technicals.get('current_trix', 'N/A')} | Signal: {technicals.get('current_trix_signal', 'N/A')}\n"
            
            ma_data = technicals.get('ma_data', {})
            prompt += f"MA: 20d=${ma_data.get('MA_20', 'N/A')} | 60d=${ma_data.get('MA_60', 'N/A')} | 120d=${ma_data.get('MA_120', 'N/A')} | Volume Ratio: {technicals.get('volume_ratio', 'N/A')}\n"
            
            earnings_date = technicals.get('earnings_date')
            earnings_d_day = technicals.get('earnings_d_day')
            if earnings_date:
                prompt += f"Next Earnings: {earnings_date}"
                if earnings_d_day is not None:
                    prompt += f" (D-{earnings_d_day})"
                    if earnings_d_day <= 7:
                        prompt += " ⚠️"
                prompt += "\n"
            prompt += "\n"
        
        # News 정보 (간결하게)
        news_context = data.get('news_context', {})
        if news_context:
            recent_news = news_context.get('recent_news', [])
            if recent_news:
                prompt += "## Recent News (Top 3)\n"
                for i, news in enumerate(recent_news[:3], 1):
                    prompt += f"{i}. {news.get('title', 'N/A')} ({news.get('publisher', 'N/A')}, {news.get('publishTime', 'N/A')})\n"
                prompt += "\n"
            
            historical_events = news_context.get('historical_events', [])
            if historical_events:
                prompt += "## Top 5 Volatile Dates\n"
                for i, event in enumerate(historical_events[:5], 1):
                    prompt += f"{i}. {event.get('date', 'N/A')}: {event.get('change_pct', 'N/A')}% (${event.get('close_price', 'N/A')})\n"
                prompt += "\n"
        
        prompt += "\n---\n\n"
        prompt += "Analyze the above data and provide a comprehensive stock analysis report."
        
        return prompt
    
    
    def extract_score_and_verdict(self, report: str) -> Tuple[int, str]:
        """
        리포트에서 Score와 Verdict 추출
        리포트의 Final Rating을 기반으로 점수 계산
        
        Args:
            report: 생성된 리포트 텍스트
        
        Returns:
            (score: int, verdict: str) 튜플
        """
        try:
            
            # Verdict 추출 (Final Rating 섹션에서 찾기)
            verdict = None
            report_upper = report.upper()
            
            # "Final Rating" 섹션 찾기
            final_rating_match = re.search(
                r'(?:final\s+rating|final\s+verdict)[:\*\s]*\*?\*?([A-Z\s]+)\*?\*?',
                report_upper,
                re.IGNORECASE | re.MULTILINE
            )
            
            if final_rating_match:
                rating_text = final_rating_match.group(1).strip()
                if "STRONG" in rating_text and "BUY" in rating_text:
                    verdict = "🟢 STRONG BUY"
                    score = 85
                elif "BUY" in rating_text:
                    verdict = "🟢 BUY"
                    score = 70
                elif "HOLD" in rating_text:
                    verdict = "🟡 HOLD"
                    score = 50
                elif "SELL" in rating_text:
                    verdict = "🔴 SELL"
                    score = 30
            else:
                # Final Rating 섹션을 못 찾은 경우, 전체 리포트에서 검색
                if "**STRONG BUY**" in report or "STRONG BUY" in report_upper:
                    verdict = "🟢 STRONG BUY"
                    score = 85
                elif "**BUY**" in report or (report_upper.find("FINAL RATING") != -1 and "BUY" in report_upper):
                    verdict = "🟢 BUY"
                    score = 70
                elif "**HOLD**" in report or "HOLD" in report_upper:
                    verdict = "🟡 HOLD"
                    score = 50
                elif "**SELL**" in report or "SELL" in report_upper:
                    verdict = "🔴 SELL"
                    score = 30
                else:
                    # Verdict를 찾을 수 없는 경우 기본값
                    verdict = "🟡 HOLD"
                    score = 50
            
            # Confidence Level에 따라 점수 조정
            confidence_match = re.search(
                r'confidence\s+level[:\s]*\*?\*?([A-Z]+)\*?\*?',
                report_upper,
                re.IGNORECASE | re.MULTILINE
            )
            
            if confidence_match:
                confidence = confidence_match.group(1).strip()
                if "LOW" in confidence:
                    score -= 10
                elif "HIGH" in confidence:
                    score += 5
            
            # 점수 범위 제한
            score = max(0, min(100, score))
            
            return score, verdict
            
        except Exception as e:
            return safe_execute(
                lambda: (50, "🟡 HOLD"),
                (50, "🟡 HOLD"),
                f"Error extracting score and verdict: {str(e)}",
                log_error=True
            )
    
    def calculate_ai_score(self, data: Dict[str, Any], strategy: str) -> int:
        """
        [Deprecated] 리포트 기반 점수 추출 사용 권장
        호환성을 위해 유지하지만, extract_score_and_verdict 사용 권장
        """
        return 50  # 기본값 반환
    
    def get_verdict(self, score: int) -> str:
        """
        [Deprecated] 리포트 기반 verdict 추출 사용 권장
        호환성을 위해 유지하지만, extract_score_and_verdict 사용 권장
        """
        return "🟡 HOLD"  # 기본값 반환

