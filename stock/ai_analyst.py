"""
AIAnalyst: Google Gemini API를 활용한 주식 분석 리포트 생성 클래스
"""

import google.generativeai as genai
from typing import Dict, Any, Optional
import json
import pandas as pd

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
        주식 분석 리포트 생성 (단계별 API 호출)
        
        Args:
            ticker: 주식 티커 심볼 (예: 'AAPL', 'GOOGL')
            data: StockDataManager에서 수집한 모든 데이터
            strategy: 투자 전략 ('Growth' 또는 'Value')
            language: 리포트 언어 ('en' 또는 'ko')
        
        Returns:
            Markdown 형식의 분석 리포트
        """
        import time
        
        try:
            report_sections = []
            
            # 1. Macro/Industry Analysis
            print("   [1/4] Macro/Industry Analysis...")
            macro_analysis = self._generate_macro_analysis(ticker, data, language)
            report_sections.append(("## Macro & Industry Analysis", macro_analysis))
            time.sleep(2)  # API 호출 간 간격
            
            # 2. Forensic Financial Check
            print("   [2/4] Forensic Financial Check...")
            forensic_analysis = self._generate_forensic_analysis(ticker, data, language)
            report_sections.append(("## Forensic Financial Check", forensic_analysis))
            time.sleep(2)
            
            # 3. Strategy Fit Assessment
            print("   [3/4] Strategy Fit Assessment...")
            strategy_analysis = self._generate_strategy_analysis(ticker, data, strategy, language)
            report_sections.append(("## Strategy Fit Assessment", strategy_analysis))
            time.sleep(2)
            
            # 4. Technical Timing Analysis & Final Verdict
            print("   [4/4] Technical Timing & Final Verdict...")
            timing_analysis = self._generate_timing_verdict(ticker, data, strategy, language)
            report_sections.append(("## Technical Timing Analysis & Final Verdict", timing_analysis))
            
            # 리포트 조합
            if language == "ko":
                report = "# 주식 분석 리포트\n\n"
                report += f"**티커**: {ticker} | **전략**: {strategy}\n\n"
                report += "---\n\n"
                # Executive Summary (간단히)
                profile = data.get('profile', {})
                report += "## 요약\n\n"
                report += f"- **회사명**: {profile.get('longName', 'N/A')} ({ticker})\n"
                report += f"- **섹터**: {profile.get('sector', 'N/A')} | **산업**: {profile.get('industry', 'N/A')}\n"
                report += f"- **현재가**: ${profile.get('currentPrice', 'N/A')} ({profile.get('changePercent', 'N/A')}%)\n\n"
                report += "---\n\n"
            else:
                report = "# Stock Analysis Report\n\n"
                report += f"**Ticker**: {ticker} | **Strategy**: {strategy}\n\n"
                report += "---\n\n"
                # Executive Summary (간단히)
                profile = data.get('profile', {})
                report += "## Executive Summary\n\n"
                report += f"- **Company**: {profile.get('longName', 'N/A')} ({ticker})\n"
                report += f"- **Sector**: {profile.get('sector', 'N/A')} | **Industry**: {profile.get('industry', 'N/A')}\n"
                report += f"- **Current Price**: ${profile.get('currentPrice', 'N/A')} ({profile.get('changePercent', 'N/A')}%)\n\n"
                report += "---\n\n"
            
            # 각 섹션 추가
            for section_title, section_content in report_sections:
                report += f"{section_title}\n\n"
                report += f"{section_content}\n\n"
                report += "---\n\n"
            
            return report
            
        except Exception as e:
            return f"# Error Generating Report\n\nAn error occurred: {str(e)}\n\nPlease check your API key and try again."
    
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
    
    def _generate_macro_analysis(self, ticker: str, data: Dict[str, Any], language: str = "en") -> str:
        """Macro/Industry 분석 생성"""
        import time
        
        profile = data.get('profile', {})
        
        if language == "ko":
            prompt = f"""다음 기업의 거시경제 환경과 산업 동향을 분석해주세요: {ticker}

기업 정보:
- 회사명: {profile.get('longName', 'N/A')}
- 섹터: {profile.get('sector', 'N/A')}
- 산업: {profile.get('industry', 'N/A')}
- 국가: {profile.get('country', 'N/A')}
- 시가총액: ${format_number(profile.get('marketCap', 'N/A'))}
- 베타: {profile.get('beta', 'N/A')}

다음 항목에 대해 분석해주세요:
1. 해당 국가/산업에 관련된 거시경제 요인 (금리, 환율 영향)
2. 산업 경쟁 구도 및 시장 포지션
3. 회사의 경쟁 우위(Moat) 및 가치 사슬 위치

한국어로 마크다운 형식으로 출력해주세요. 간결하지만 포괄적으로 작성해주세요."""
        else:
            prompt = f"""Analyze the macroeconomic environment and industry dynamics for {ticker}.

Company Information:
- Name: {profile.get('longName', 'N/A')}
- Sector: {profile.get('sector', 'N/A')}
- Industry: {profile.get('industry', 'N/A')}
- Country: {profile.get('country', 'N/A')}
- Market Cap: ${format_number(profile.get('marketCap', 'N/A'))}
- Beta: {profile.get('beta', 'N/A')}

Provide analysis on:
1. Macroeconomic factors (interest rates, currency impacts) relevant to this country/industry
2. Industry competitive landscape and market position
3. Company's moat and value chain position

Output in English, Markdown format. Be concise but comprehensive."""
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(35)
                        continue
                return safe_execute(
                    lambda: "*Macro analysis unavailable due to API limitations.*",
                    "*Macro analysis unavailable.*",
                    f"Error in macro analysis for {ticker}",
                    log_error=True
                )
        return "*Macro analysis unavailable.*"
    
    def _generate_forensic_analysis(self, ticker: str, data: Dict[str, Any], language: str = "en") -> str:
        """Forensic Financial Check 생성"""
        import time
        
        financials = data.get('financials', {})
        metrics = financials.get('derived_metrics', {})
        
        if language == "ko":
            prompt = f"""다음 기업의 재무 포렌식 분석을 수행해주세요: {ticker}

재무 지표:
- 이익의 질 (OCF/순이익): {metrics.get('quality_of_earnings', {}).get('latest', 'N/A')} (추세: {metrics.get('quality_of_earnings', {}).get('trend', 'N/A')})
- 매출채권 회전율: {metrics.get('receivables_turnover', {}).get('latest', 'N/A')} (추세: {metrics.get('receivables_turnover', {}).get('trend', 'N/A')})
- 재고 회전율: {metrics.get('inventory_turnover', {}).get('latest', 'N/A')} (추세: {metrics.get('inventory_turnover', {}).get('trend', 'N/A')})
- 이자보상배율: {metrics.get('interest_coverage', {}).get('latest', 'N/A')} (상태: {metrics.get('interest_coverage', {}).get('status', 'N/A')})
- 자본지출 성장률: {metrics.get('capex_growth', {}).get('latest', 'N/A')}% (추세: {metrics.get('capex_growth', {}).get('trend', 'N/A')})
- 순 자사주 매입 수익률: {metrics.get('net_buyback_yield', {}).get('latest', 'N/A')}% (상태: {metrics.get('net_buyback_yield', {}).get('status', 'N/A')})

중요: 지표가 "N/A"인 경우, "데이터 부족으로 일부 포렌식 분석이 제외됨"이라고 명시해주세요.

다음 항목을 평가해주세요:
1. 이익의 질 및 잠재적 회계 부정 가능성
2. 활동성 비율 추세 (회전율 하락 = 위험)
3. 재무 안정성
4. 경고 신호 또는 우려사항

한국어로 마크다운 형식으로 출력해주세요. 간결하게 작성해주세요."""
        else:
            prompt = f"""Perform forensic financial analysis for {ticker}.

Financial Metrics:
- Quality of Earnings (OCF/Net Income): {metrics.get('quality_of_earnings', {}).get('latest', 'N/A')} (Trend: {metrics.get('quality_of_earnings', {}).get('trend', 'N/A')})
- Receivables Turnover: {metrics.get('receivables_turnover', {}).get('latest', 'N/A')} (Trend: {metrics.get('receivables_turnover', {}).get('trend', 'N/A')})
- Inventory Turnover: {metrics.get('inventory_turnover', {}).get('latest', 'N/A')} (Trend: {metrics.get('inventory_turnover', {}).get('trend', 'N/A')})
- Interest Coverage Ratio: {metrics.get('interest_coverage', {}).get('latest', 'N/A')} (Status: {metrics.get('interest_coverage', {}).get('status', 'N/A')})
- CapEx Growth: {metrics.get('capex_growth', {}).get('latest', 'N/A')}% (Trend: {metrics.get('capex_growth', {}).get('trend', 'N/A')})
- Net Buyback Yield: {metrics.get('net_buyback_yield', {}).get('latest', 'N/A')}% (Status: {metrics.get('net_buyback_yield', {}).get('status', 'N/A')})

IMPORTANT: If any metric shows "N/A", explicitly state "Data Not Available - Some forensic analysis excluded due to missing data".

Evaluate:
1. Earnings quality and potential accounting irregularities
2. Activity ratios trends (declining turnover = risk)
3. Financial stability
4. Red flags or concerns

Output in English, Markdown format. Be concise."""
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(35)
                        continue
                return safe_execute(
                    lambda: "*Forensic analysis unavailable due to API limitations.*",
                    "*Forensic analysis unavailable.*",
                    f"Error in forensic analysis for {ticker}",
                    log_error=True
                )
        return "*Forensic analysis unavailable.*"
    
    def _generate_strategy_analysis(self, ticker: str, data: Dict[str, Any], strategy: str, language: str = "en") -> str:
        """Strategy Fit Assessment 생성"""
        import time
        
        strategy_mode = "Growth" if "Growth" in strategy or "🚀" in strategy else "Value"
        financials = data.get('financials', {})
        metrics = financials.get('derived_metrics', {})
        profile = data.get('profile', {})
        
        if language == "ko":
            prompt = f"""다음 기업이 {strategy_mode} 투자 전략에 적합한지 평가해주세요: {ticker}

회사: {profile.get('longName', 'N/A')}
현재 전략 모드: {strategy_mode}

주요 지표:
- 자본지출 성장률: {metrics.get('capex_growth', {}).get('latest', 'N/A')}% (추세: {metrics.get('capex_growth', {}).get('trend', 'N/A')})
- 순 자사주 매입 수익률: {metrics.get('net_buyback_yield', {}).get('latest', 'N/A')}% (상태: {metrics.get('net_buyback_yield', {}).get('status', 'N/A')})
- 시가총액: ${format_number(profile.get('marketCap', 'N/A'))}
"""
            
            if strategy_mode == "Growth":
                prompt += """
다음 항목에 집중해주세요:
- 매출 성장 추세
- 자본지출 확장
- 시장 점유율 잠재력
- 혁신/R&D 투자
"""
            else:
                prompt += """
다음 항목에 집중해주세요:
- 자유현금흐름 창출
- 배당 수익률
- 자사주 매입 프로그램
- 부채 감소
- 밸류에이션 지표
"""
            
            prompt += "\n한국어로 마크다운 형식으로 출력해주세요. 간결하게 작성해주세요."
        else:
            prompt = f"""Assess {ticker} fit for {strategy_mode} investment strategy.

Company: {profile.get('longName', 'N/A')}
Current Strategy Mode: {strategy_mode}

Key Metrics:
- CapEx Growth: {metrics.get('capex_growth', {}).get('latest', 'N/A')}% (Trend: {metrics.get('capex_growth', {}).get('trend', 'N/A')})
- Net Buyback Yield: {metrics.get('net_buyback_yield', {}).get('latest', 'N/A')}% (Status: {metrics.get('net_buyback_yield', {}).get('status', 'N/A')})
- Market Cap: ${format_number(profile.get('marketCap', 'N/A'))}
"""
            
            if strategy_mode == "Growth":
                prompt += """
Focus on:
- Revenue growth trends
- Capital expenditure expansion
- Market share potential
- Innovation/R&D investment
"""
            else:
                prompt += """
Focus on:
- Free Cash Flow generation
- Dividend yield
- Share buyback programs
- Debt reduction
- Valuation metrics
"""
            
            prompt += "\nOutput in English, Markdown format. Be concise."
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(35)
                        continue
                return safe_execute(
                    lambda: "*Strategy analysis unavailable due to API limitations.*",
                    "*Strategy analysis unavailable.*",
                    f"Error in strategy analysis for {ticker}",
                    log_error=True
                )
        return "*Strategy analysis unavailable.*"
    
    def _generate_timing_verdict(self, ticker: str, data: Dict[str, Any], strategy: str, language: str = "en") -> str:
        """Technical Timing Analysis & Final Verdict 생성"""
        import time
        
        technicals = data.get('technicals', {})
        news_context = data.get('news_context', {})
        profile = data.get('profile', {})
        
        if language == "ko":
            prompt = f"""다음 기업의 기술적 타이밍 분석 및 최종 투자 판단을 제공해주세요: {ticker}

현재가: ${profile.get('currentPrice', 'N/A')}

기술적 지표:
- RSI(14): {technicals.get('current_rsi', 'N/A')}
- TRIX(30): {technicals.get('current_trix', 'N/A')} (신호: {technicals.get('current_trix_signal', 'N/A')})
- 이동평균: 20일=${technicals.get('ma_data', {}).get('MA_20', 'N/A')} | 60일=${technicals.get('ma_data', {}).get('MA_60', 'N/A')} | 120일=${technicals.get('ma_data', {}).get('MA_120', 'N/A')}
- 거래량 비율: {technicals.get('volume_ratio', 'N/A')}
- 다음 실적 발표: {technicals.get('earnings_date', 'N/A')} (D-{technicals.get('earnings_d_day', 'N/A')})
"""
            
            if news_context.get('recent_news'):
                prompt += "\n최근 뉴스 헤드라인:\n"
                for i, news in enumerate(news_context.get('recent_news', [])[:3], 1):
                    prompt += f"{i}. {news.get('title', 'N/A')}\n"
            
            prompt += """
다음 항목을 제공해주세요:
1. 기술적 타이밍 분석 (RSI, TRIX, 이동평균 신호)
2. 실적 발표 근접 경고 (D-Day ≤ 7일인 경우 "변동성 경고 - 관망 권고")
3. 구체적인 진입가 제안 ($)
4. 최종 판단: **강력 매수** / **매수** / **보유** / **매도**

한국어로 마크다운 형식으로 출력해주세요. 간결하고 실행 가능하게 작성해주세요."""
        else:
            prompt = f"""Provide technical timing analysis and final investment verdict for {ticker}.

Current Price: ${profile.get('currentPrice', 'N/A')}

Technical Indicators:
- RSI(14): {technicals.get('current_rsi', 'N/A')}
- TRIX(30): {technicals.get('current_trix', 'N/A')} (Signal: {technicals.get('current_trix_signal', 'N/A')})
- MA: 20d=${technicals.get('ma_data', {}).get('MA_20', 'N/A')} | 60d=${technicals.get('ma_data', {}).get('MA_60', 'N/A')} | 120d=${technicals.get('ma_data', {}).get('MA_120', 'N/A')}
- Volume Ratio: {technicals.get('volume_ratio', 'N/A')}
- Next Earnings: {technicals.get('earnings_date', 'N/A')} (D-{technicals.get('earnings_d_day', 'N/A')})
"""
            
            if news_context.get('recent_news'):
                prompt += "\nRecent News Headlines:\n"
                for i, news in enumerate(news_context.get('recent_news', [])[:3], 1):
                    prompt += f"{i}. {news.get('title', 'N/A')}\n"
            
            prompt += """
Provide:
1. Technical timing analysis (RSI, TRIX, MA signals)
2. Earnings proximity warning (if D-Day ≤ 7, recommend "Volatility Warning - Wait and See")
3. Specific entry price recommendation ($)
4. Final verdict: **STRONG BUY** / **BUY** / **HOLD** / **SELL**

Output in English, Markdown format. Be concise and actionable."""
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(35)
                        continue
                return safe_execute(
                    lambda: "*Timing analysis unavailable due to API limitations.*",
                    "*Timing analysis unavailable.*",
                    f"Error in timing analysis for {ticker}",
                    log_error=True
                )
        return "*Timing analysis unavailable.*"
    
    def calculate_ai_score(self, data: Dict[str, Any], strategy: str) -> int:
        """
        AI 점수 계산 (0-100)
        
        Args:
            data: StockDataManager에서 수집한 데이터
            strategy: 투자 전략 ('Growth' 또는 'Value')
        
        Returns:
            0-100 사이의 점수
        """
        try:
            score = 50  # 기본 점수
            
            financials = data.get('financials', {})
            metrics = financials.get('derived_metrics', {})
            technicals = data.get('technicals', {})
            
            # Quality of Earnings 점수
            qoe = metrics.get('quality_of_earnings', {})
            if qoe.get('latest') != 'N/A':
                qoe_value = qoe.get('latest', 1.0)
                if qoe_value >= 1.2:
                    score += 10
                elif qoe_value >= 1.0:
                    score += 5
                elif qoe_value < 0.8:
                    score -= 10
            
            # Interest Coverage 점수
            ic = metrics.get('interest_coverage', {})
            if ic.get('latest') != 'N/A':
                ic_value = ic.get('latest', 0)
                if ic_value >= 5.0:
                    score += 10
                elif ic_value >= 1.0:
                    score += 5
                else:
                    score -= 10
            
            # RSI 점수
            if technicals.get('current_rsi') != 'N/A':
                rsi = technicals.get('current_rsi', 50)
                if 30 <= rsi <= 70:
                    score += 5
                elif rsi < 30:
                    score += 10  # Oversold = 매수 기회
                elif rsi > 70:
                    score -= 5  # Overbought
            
            # Earnings D-Day 점수
            earnings_d_day = technicals.get('earnings_d_day')
            if earnings_d_day is not None:
                if earnings_d_day > 7:
                    score += 5  # Earnings가 멀면 안정적
                elif earnings_d_day <= 7:
                    score -= 5  # Earnings가 가까우면 변동성 위험
            
            # Strategy별 점수
            strategy_mode = "Growth" if "Growth" in strategy or "🚀" in strategy else "Value"
            
            if strategy_mode == "Growth":
                capex = metrics.get('capex_growth', {})
                if capex.get('latest') != 'N/A':
                    capex_value = capex.get('latest', 0)
                    if capex_value > 0:
                        score += 5
            else:  # Value
                buyback = metrics.get('net_buyback_yield', {})
                if buyback.get('latest') != 'N/A' and buyback.get('status') == 'Positive':
                    score += 5
            
            # 점수 범위 제한 (0-100)
            score = max(0, min(100, score))
            
            return score
            
        except Exception as e:
            return safe_execute(
                lambda: 50,
                50,
                "Error calculating AI score",
                log_error=True
            )
    
    def get_verdict(self, score: int) -> str:
        """
        점수 기반 최종 판단
        
        Args:
            score: AI 점수 (0-100)
        
        Returns:
            'STRONG BUY', 'BUY', 'HOLD', 'SELL'
        """
        if score >= 80:
            return "🟢 STRONG BUY"
        elif score >= 65:
            return "🟢 BUY"
        elif score >= 45:
            return "🟡 HOLD"
        else:
            return "🔴 SELL"

