import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import time
import json

# Add stock module to path for imports
# This allows the app to work both locally and on Streamlit Cloud
current_dir = os.path.dirname(os.path.abspath(__file__))
stock_dir = os.path.join(current_dir, 'stock')
if stock_dir not in sys.path:
    sys.path.insert(0, stock_dir)

# Import from stock module
from data_manager import StockDataManager
from ai_analyst import AIAnalyst
from utils import format_number

# 페이지 설정
st.set_page_config(
    page_title="Stock Deep-Dive AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바
st.sidebar.title("📈 Stock Deep-Dive AI")
st.sidebar.markdown("---")

# API Key 입력 (사용자가 매번 직접 입력)
api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    value="",  # 항상 빈 값으로 시작
    help="Enter your Google Gemini API key to enable AI-powered analysis features.",
    key="api_key_input"
)

if not api_key or not api_key.strip():
    st.sidebar.info("💡 Enter your Gemini API Key to unlock AI analysis features. The app works without it for basic indicators.")

# Ticker 입력
ticker = st.sidebar.text_input(
    "Enter Ticker (e.g., NVDA, AAPL)",
    value="GOOGL",
    help="Enter stock ticker symbol"
).upper()

# 투자 성향 선택
strategy = st.sidebar.radio(
    "Investment Style",
    ["🚀 Growth", "🛡️ Value"],
    help="Select your investment strategy"
)

# 언어 선택
language = st.sidebar.radio(
    "Language",
    ["🇺🇸 English", "🇰🇷 한국어"],
    help="Select report language"
)

# 언어 코드 변환
lang_code = "en" if "English" in language else "ko"

# Gemini 모델 선택
gemini_model = st.sidebar.radio(
    "Gemini Model",
    ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
    help="Select Gemini model (flash-lite is faster but less capable)"
)

# Run Analysis 버튼
run_analysis = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

# 메인 화면
st.title("📈 Stock Deep-Dive AI")
st.markdown("---")

# 세션 상태 초기화
if 'data' not in st.session_state:
    st.session_state.data = None
if 'ai_report' not in st.session_state:
    st.session_state.ai_report = None
if 'ai_score' not in st.session_state:
    st.session_state.ai_score = None
if 'verdict' not in st.session_state:
    st.session_state.verdict = None

# 분석 실행
if run_analysis:
    if not ticker:
        st.error("⚠️ Please enter a ticker symbol.")
        st.stop()
    
    # 진행 상황 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 1. 데이터 수집 (API 키 없이도 실행 가능)
        status_text.text("📊 Collecting data...")
        progress_bar.progress(20)
        
        manager = StockDataManager(ticker)
        
        data = {
            'profile': manager.get_profile(),
            'financials': manager.get_financials(),
            'technicals': manager.get_technicals(),
            'news_context': manager.get_news_context()
        }
        
        st.session_state.data = data
        progress_bar.progress(40)
        
        # 2. AI 분석 (API 키가 있는 경우에만 실행)
        if api_key and api_key.strip():
            try:
                status_text.text("🤖 Running AI analysis...")
                progress_bar.progress(60)
                
                analyst = AIAnalyst(api_key, model_name=gemini_model)
                ai_report = analyst.generate_report(ticker, data, strategy, language=lang_code)
                # 리포트에서 Score와 Verdict 추출
                ai_score, verdict = analyst.extract_score_and_verdict(ai_report)
                
                st.session_state.ai_report = ai_report
                st.session_state.ai_score = ai_score
                st.session_state.verdict = verdict
                
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
            except Exception as ai_error:
                # AI 분석 실패해도 기본 지표는 계속 표시
                st.warning(f"⚠️ AI analysis failed: {str(ai_error)}. Showing basic indicators only.")
                st.session_state.ai_report = None
                st.session_state.ai_score = None
                st.session_state.verdict = None
                progress_bar.progress(100)
                status_text.text("✅ Basic analysis complete!")
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
        else:
            # API 키가 없는 경우 기본 지표만 표시
            st.session_state.ai_report = None
            st.session_state.ai_score = None
            st.session_state.verdict = None
            progress_bar.progress(100)
            status_text.text("✅ Basic analysis complete! (Enter API key for AI analysis)")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Error collecting data: {str(e)}")
        st.stop()

# 데이터가 있으면 탭 표시
if st.session_state.data:
    data = st.session_state.data
    profile = data.get('profile', {})
    
    # 헤더 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Company", profile.get('longName', 'N/A'))
    with col2:
        st.metric("Ticker", ticker)
    with col3:
        current_price = profile.get('currentPrice', 'N/A')
        change_pct = profile.get('changePercent', 'N/A')
        if current_price != 'N/A' and change_pct != 'N/A':
            st.metric("Current Price", f"${current_price:.2f}", f"{change_pct:.2f}%")
        else:
            st.metric("Current Price", "N/A")
    with col4:
        if st.session_state.ai_score is not None:
            st.metric("AI Score", f"{st.session_state.ai_score}/100")
        else:
            st.metric("AI Score", "N/A")
    
    # Verdict 배지 (API 키가 있고 AI 분석이 완료된 경우에만 표시)
    if st.session_state.verdict:
        st.markdown(f"### {st.session_state.verdict}")
    elif not api_key or not api_key.strip():
        st.info("💡 Enter your Gemini API Key in the sidebar to get AI analysis and investment verdict.")
    
    st.markdown("---")
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Executive Summary", "🌍 Macro & Industry", "💰 Financials", "📊 Technicals", "📊 Raw Data"])
    
    # Tab 1: Executive Summary
    with tab1:
        st.header("Executive Summary")
        
        if st.session_state.ai_report:
            # AI 리포트에서 Executive Summary 추출 (간단히 전체 리포트 표시)
            st.markdown(st.session_state.ai_report)
        elif not api_key or not api_key.strip():
            st.info("💡 **AI Report Not Available**\n\nTo view AI-powered analysis and insights, please enter your Gemini API Key in the sidebar and run the analysis again.")
            st.markdown("---")
            st.subheader("Quick Summary (Basic Indicators)")
            financials = data.get('financials', {})
            metrics = financials.get('derived_metrics', {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Company:** {profile.get('longName', 'N/A')}")
                st.write(f"**Sector:** {profile.get('sector', 'N/A')}")
                st.write(f"**Industry:** {profile.get('industry', 'N/A')}")
                st.write(f"**Market Cap:** ${format_number(profile.get('marketCap', 'N/A'))}")
            with col2:
                qoe = metrics.get('quality_of_earnings', {})
                ic = metrics.get('interest_coverage', {})
                st.write(f"**Quality of Earnings:** {qoe.get('latest', 'N/A')}")
                st.write(f"**Interest Coverage:** {ic.get('latest', 'N/A')} ({ic.get('status', 'N/A')})")
                st.write(f"**Current Price:** ${profile.get('currentPrice', 'N/A')}")
        else:
            st.info("Run analysis to see the executive summary.")
        
        # Radar Chart (간단한 버전) - 항상 표시 (데이터가 있을 때만)
        if st.session_state.data:
            st.subheader("Performance Radar")
            
            # 간단한 지표 계산
            financials = data.get('financials', {})
            metrics = financials.get('derived_metrics', {})
            technicals = data.get('technicals', {})
            
            # 지표 값 추출 (N/A 처리)
            def safe_get(value, default=50):
                if value == 'N/A' or value is None:
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            growth_score = safe_get(metrics.get('capex_growth', {}).get('latest', 50), 50)
            stability_score = safe_get(metrics.get('interest_coverage', {}).get('latest', 50), 50)
            profitability_score = safe_get(metrics.get('quality_of_earnings', {}).get('latest', 50), 50)
            momentum_score = safe_get(technicals.get('current_rsi', 50), 50)
            value_score = safe_get(metrics.get('net_buyback_yield', {}).get('latest', 50), 50)
            
            # Radar Chart
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=[growth_score, stability_score, profitability_score, momentum_score, value_score],
                theta=['Growth', 'Stability', 'Profitability', 'Momentum', 'Value'],
                fill='toself',
                name='Performance'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Performance Radar Chart"
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            if not api_key or not api_key.strip():
                st.caption("💡 Note: Enter your Gemini API Key for AI-powered analysis and investment verdict.")
    
    # Tab 2: Macro & Industry
    with tab2:
        st.header("Macro & Industry Analysis")
        
        if st.session_state.ai_report:
            # AI 리포트에서 Macro 섹션 추출
            report = st.session_state.ai_report
            macro_section = ""
            
            # Macro 섹션 찾기
            if "## Macro & Industry Analysis" in report:
                start_idx = report.find("## Macro & Industry Analysis")
                end_idx = report.find("---", start_idx + 1)
                if end_idx == -1:
                    end_idx = report.find("## Forensic", start_idx + 1)
                if end_idx != -1:
                    macro_section = report[start_idx:end_idx]
                else:
                    macro_section = report[start_idx:]
            
            if macro_section:
                st.markdown(macro_section)
            else:
                st.info("Macro analysis section not found in report.")
        elif not api_key or not api_key.strip():
            st.info("💡 **AI-Powered Macro Analysis Not Available**\n\nTo view AI-powered macroeconomic and industry analysis, please enter your Gemini API Key in the sidebar and run the analysis again.")
            st.markdown("---")
        
        # Peer Comparison (간단한 버전) - 항상 표시
        st.subheader("Company Profile")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Sector:** {profile.get('sector', 'N/A')}")
            st.write(f"**Industry:** {profile.get('industry', 'N/A')}")
            st.write(f"**Country:** {profile.get('country', 'N/A')}")
        with col2:
            st.write(f"**Market Cap:** ${format_number(profile.get('marketCap', 'N/A'))}")
            st.write(f"**Beta:** {profile.get('beta', 'N/A')}")
        
        if not api_key or not api_key.strip():
            st.info("💡 Enter your Gemini API Key to see detailed macro analysis including interest rates, currency impacts, and competitive landscape.")
    
    # Tab 3: Financials
    with tab3:
        st.header("Financial Health")
        
        financials = data.get('financials', {})
        metrics = financials.get('derived_metrics', {})
        raw_data = financials.get('raw_data', {})
        annual_data = raw_data.get('annual', {})
        
        # Forensic Check Table
        st.subheader("Forensic Check")
        
        forensic_data = []
        
        # Quality of Earnings
        qoe = metrics.get('quality_of_earnings', {})
        qoe_value = qoe.get('latest', 'N/A')
        qoe_status = "✅" if (qoe_value != 'N/A' and isinstance(qoe_value, (int, float)) and qoe_value >= 1.0) else "⚠️" if qoe.get('warning') else "N/A"
        forensic_data.append({
            "Metric": "Quality of Earnings (OCF/Net Income)",
            "Value": qoe_value if qoe_value != 'N/A' else "N/A",
            "Trend": qoe.get('trend', 'N/A'),
            "Status": qoe_status
        })
        
        # Receivables Turnover
        rt = metrics.get('receivables_turnover', {})
        forensic_data.append({
            "Metric": "Receivables Turnover",
            "Value": rt.get('latest', 'N/A'),
            "Trend": rt.get('trend', 'N/A'),
            "Status": "✅" if rt.get('trend') == 'Improving' else "⚠️" if rt.get('trend') == 'Declining' else "N/A"
        })
        
        # Inventory Turnover
        it = metrics.get('inventory_turnover', {})
        forensic_data.append({
            "Metric": "Inventory Turnover",
            "Value": it.get('latest', 'N/A'),
            "Trend": it.get('trend', 'N/A'),
            "Status": "✅" if it.get('trend') == 'Improving' else "⚠️" if it.get('trend') == 'Declining' else "N/A"
        })
        
        # Interest Coverage
        ic = metrics.get('interest_coverage', {})
        forensic_data.append({
            "Metric": "Interest Coverage Ratio",
            "Value": ic.get('latest', 'N/A'),
            "Trend": ic.get('status', 'N/A'),
            "Status": "✅" if ic.get('status') == 'Strong' else "⚠️" if ic.get('status') == 'Weak' else "🔴" if ic.get('status') == 'Critical' else "N/A"
        })
        
        # CapEx Growth
        capex = metrics.get('capex_growth', {})
        forensic_data.append({
            "Metric": "CapEx Growth",
            "Value": f"{capex.get('latest', 'N/A')}%" if capex.get('latest') != 'N/A' else "N/A",
            "Trend": capex.get('trend', 'N/A'),
            "Status": "✅" if capex.get('trend') == 'Expanding' else "N/A"
        })
        
        # Net Buyback Yield
        buyback = metrics.get('net_buyback_yield', {})
        forensic_data.append({
            "Metric": "Net Buyback Yield",
            "Value": f"{buyback.get('latest', 'N/A')}%" if buyback.get('latest') != 'N/A' else "N/A",
            "Trend": buyback.get('status', 'N/A'),
            "Status": "✅" if buyback.get('status') == 'Positive' else "N/A"
        })
        
        df_forensic = pd.DataFrame(forensic_data)
        st.dataframe(df_forensic, use_container_width=True, hide_index=True)
        
        # Revenue & Net Income Chart
        st.subheader("Revenue & Net Income (3 Years)")
        
        if annual_data and not annual_data.get('income_stmt', pd.DataFrame()).empty:
            income_stmt = annual_data['income_stmt']
            
            try:
                # 데이터 구조: 인덱스가 날짜, 컬럼이 재무 항목
                dates = []
                revenue_data = []
                net_income_data = []
                
                # 인덱스에서 날짜 추출
                for date in income_stmt.index:
                    dates.append(str(date)[:10])  # 날짜만 추출 (YYYY-MM-DD)
                    
                    # Total Revenue 추출
                    if 'Total Revenue' in income_stmt.columns:
                        rev = income_stmt.loc[date, 'Total Revenue']
                        if pd.notna(rev) and rev != 'N/A':
                            try:
                                revenue_data.append(float(rev))
                            except (ValueError, TypeError):
                                revenue_data.append(0)
                        else:
                            revenue_data.append(0)
                    else:
                        revenue_data.append(0)
                    
                    # Net Income 추출
                    if 'Net Income' in income_stmt.columns:
                        ni = income_stmt.loc[date, 'Net Income']
                        if pd.notna(ni) and ni != 'N/A':
                            try:
                                net_income_data.append(float(ni))
                            except (ValueError, TypeError):
                                net_income_data.append(0)
                        else:
                            net_income_data.append(0)
                    else:
                        net_income_data.append(0)
                
                if dates and (any(revenue_data) or any(net_income_data)):
                    fig_financials = go.Figure()
                    
                    if any(revenue_data):
                        fig_financials.add_trace(
                            go.Bar(name="Revenue", x=dates, y=revenue_data, marker_color='blue')
                        )
                    
                    if any(net_income_data):
                        fig_financials.add_trace(
                            go.Bar(name="Net Income", x=dates, y=net_income_data, marker_color='green')
                        )
                    
                    fig_financials.update_layout(
                        title="Annual Revenue & Net Income",
                        xaxis_title="Year",
                        yaxis_title="Amount ($)",
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig_financials, use_container_width=True)
                else:
                    st.info("Financial data not available for charting.")
                    
            except Exception as e:
                st.warning(f"Could not create financial chart: {str(e)}")
        else:
            st.info("Financial data not available.")
        
        # Free Cash Flow vs CapEx Chart
        st.subheader("Free Cash Flow vs CapEx")
        
        if annual_data and not annual_data.get('cashflow', pd.DataFrame()).empty:
            cashflow = annual_data['cashflow']
            
            try:
                dates = []
                fcf_data = []
                capex_data = []
                
                # 데이터 구조: 인덱스가 날짜, 컬럼이 재무 항목
                for date in cashflow.index:
                    dates.append(str(date)[:10])  # 날짜만 추출
                    
                    # Free Cash Flow (직접 사용 가능)
                    fcf = None
                    if 'Free Cash Flow' in cashflow.columns:
                        fcf = cashflow.loc[date, 'Free Cash Flow']
                    else:
                        # Free Cash Flow = Operating Cash Flow - CapEx (계산)
                        ocf = None
                        capex = None
                        
                        if 'Operating Cash Flow' in cashflow.columns:
                            ocf = cashflow.loc[date, 'Operating Cash Flow']
                        elif 'Cash Flow From Continuing Operating Activities' in cashflow.columns:
                            ocf = cashflow.loc[date, 'Cash Flow From Continuing Operating Activities']
                        
                        if 'Capital Expenditure' in cashflow.columns:
                            capex = cashflow.loc[date, 'Capital Expenditure']
                        
                        if pd.notna(ocf) and ocf != 'N/A' and pd.notna(capex) and capex != 'N/A':
                            try:
                                fcf = float(ocf) - abs(float(capex))
                            except (ValueError, TypeError):
                                fcf = None
                    
                    if pd.notna(fcf) and fcf != 'N/A':
                        try:
                            fcf_data.append(float(fcf))
                        except (ValueError, TypeError):
                            fcf_data.append(0)
                    else:
                        fcf_data.append(0)
                    
                    # Capital Expenditure (음수이므로 절댓값 사용)
                    capex = None
                    if 'Capital Expenditure' in cashflow.columns:
                        capex = cashflow.loc[date, 'Capital Expenditure']
                    
                    if pd.notna(capex) and capex != 'N/A':
                        try:
                            capex_data.append(abs(float(capex)))  # CapEx는 음수로 저장되므로 절댓값
                        except (ValueError, TypeError):
                            capex_data.append(0)
                    else:
                        capex_data.append(0)
                
                if dates:
                    fig_cashflow = go.Figure()
                    
                    fig_cashflow.add_trace(go.Scatter(
                        x=dates,
                        y=fcf_data,
                        mode='lines+markers',
                        name='Free Cash Flow',
                        line=dict(color='green', width=2)
                    ))
                    
                    fig_cashflow.add_trace(go.Scatter(
                        x=dates,
                        y=capex_data,
                        mode='lines+markers',
                        name='CapEx',
                        line=dict(color='orange', width=2)
                    ))
                    
                    fig_cashflow.update_layout(
                        title="Free Cash Flow vs CapEx",
                        xaxis_title="Year",
                        yaxis_title="Amount ($)",
                        height=400
                    )
                    
                    st.plotly_chart(fig_cashflow, use_container_width=True)
                else:
                    st.info("Cash flow data not available for charting.")
                    
            except Exception as e:
                st.warning(f"Could not create cash flow chart: {str(e)}")
        else:
            st.info("Cash flow data not available.")
    
    # Tab 4: Technicals
    with tab4:
        st.header("Timing & Technical Analysis")
        
        technicals = data.get('technicals', {})
        
        if technicals.get('error'):
            st.error(f"Error loading technical data: {technicals.get('error')}")
        else:
            # Price Chart with MA Lines
            st.subheader("Price Chart with Moving Averages")
            
            try:
                # StockDataManager에서 가져온 데이터로 차트 생성
                manager = StockDataManager(ticker)
                hist = manager.ticker.history(period="1y", interval="1d")
                
                if not hist.empty:
                    fig_price = go.Figure()
                    
                    # Candlestick
                    fig_price.add_trace(go.Candlestick(
                        x=hist.index,
                        open=hist['Open'],
                        high=hist['High'],
                        low=hist['Low'],
                        close=hist['Close'],
                        name='Price'
                    ))
                    
                    # Moving Averages (실제 계산된 값 사용)
                    ma_data = technicals.get('ma_data', {})
                    
                    # MA 계산 (hist 데이터에서)
                    if len(hist) >= 20:
                        hist['MA_20'] = hist['Close'].rolling(window=20).mean()
                        if ma_data.get('MA_20') != 'N/A':
                            fig_price.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['MA_20'],
                                mode='lines',
                                name='MA 20',
                                line=dict(color='blue', width=2)
                            ))
                    
                    if len(hist) >= 60:
                        hist['MA_60'] = hist['Close'].rolling(window=60).mean()
                        if ma_data.get('MA_60') != 'N/A':
                            fig_price.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['MA_60'],
                                mode='lines',
                                name='MA 60',
                                line=dict(color='orange', width=2)
                            ))
                    
                    if len(hist) >= 120:
                        hist['MA_120'] = hist['Close'].rolling(window=120).mean()
                        if ma_data.get('MA_120') != 'N/A':
                            fig_price.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['MA_120'],
                                mode='lines',
                                name='MA 120',
                                line=dict(color='red', width=2)
                            ))
                    
                    # Historical Events 표시
                    news_context = data.get('news_context', {})
                    historical_events = news_context.get('historical_events', [])
                    for event in historical_events[:5]:
                        event_date = pd.to_datetime(event.get('date', ''))
                        if event_date in hist.index:
                            change_pct = event.get('change_pct', 0)
                            color = 'red' if change_pct < 0 else 'green'
                            fig_price.add_trace(go.Scatter(
                                x=[event_date],
                                y=[hist.loc[event_date, 'Close']],
                                mode='markers',
                                marker=dict(size=15, color=color, symbol='diamond'),
                                name=f"Event: {change_pct:.2f}%",
                                showlegend=False
                            ))
                    
                    fig_price.update_layout(
                        title="Stock Price with Moving Averages",
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        height=500,
                        xaxis_rangeslider_visible=False
                    )
                    
                    st.plotly_chart(fig_price, use_container_width=True)
                else:
                    st.info("Price data not available.")
                    
            except Exception as e:
                st.warning(f"Could not create price chart: {str(e)}")
            
            # RSI Sub-chart
            st.subheader("RSI Indicator")
            
            try:
                # Historical RSI 계산
                manager = StockDataManager(ticker)
                hist = manager.ticker.history(period="1y", interval="1d")
                
                if not hist.empty and len(hist) >= 14:
                    # RSI 계산 (14일)
                    delta = hist['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    current_rsi = technicals.get('current_rsi', 'N/A')
                    
                    # Price & RSI 차트 (2개 subplot)
                    fig_rsi = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('Price', f'RSI(14) - Current: {current_rsi:.2f}' if current_rsi != 'N/A' else 'RSI(14)'),
                        row_heights=[0.6, 0.4],
                        vertical_spacing=0.1
                    )
                    
                    # Price 차트
                    fig_rsi.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=hist['Close'],
                            name='Close Price',
                            line=dict(color='blue', width=1)
                        ),
                        row=1, col=1
                    )
                    
                    # RSI 차트
                    fig_rsi.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=rsi,
                            name='RSI',
                            line=dict(color='purple', width=2)
                        ),
                        row=2, col=1
                    )
                    
                    # Overbought/Oversold lines
                    fig_rsi.add_hline(
                        y=70,
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Overbought (70)",
                        row=2, col=1
                    )
                    fig_rsi.add_hline(
                        y=30,
                        line_dash="dash",
                        line_color="green",
                        annotation_text="Oversold (30)",
                        row=2, col=1
                    )
                    
                    fig_rsi.update_layout(
                        title="Price & RSI(14) Indicator",
                        height=600,
                        showlegend=True,
                        xaxis_rangeslider_visible=False
                    )
                    
                    fig_rsi.update_yaxes(title_text="Price ($)", row=1, col=1)
                    fig_rsi.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
                    fig_rsi.update_xaxes(title_text="Date", row=2, col=1)
                    
                    st.plotly_chart(fig_rsi, use_container_width=True)
                else:
                    st.info("RSI data not available (insufficient historical data).")
                    
            except Exception as e:
                st.warning(f"Could not create RSI chart: {str(e)}")
            
            # TRIX Sub-chart
            st.subheader("TRIX Indicator")
            
            try:
                # Historical TRIX 계산
                manager = StockDataManager(ticker)
                hist = manager.ticker.history(period="1y", interval="1d")
                
                if not hist.empty and len(hist) >= 30:
                    # TRIX 계산 (30일 EMA의 3차 지수 이동평균)
                    # 1. 30일 EMA
                    ema1 = hist['Close'].ewm(span=30, adjust=False).mean()
                    # 2. EMA의 EMA
                    ema2 = ema1.ewm(span=30, adjust=False).mean()
                    # 3. EMA의 EMA의 EMA
                    ema3 = ema2.ewm(span=30, adjust=False).mean()
                    # 4. TRIX = (EMA3 - 이전 EMA3) / 이전 EMA3 * 100
                    trix = ((ema3 - ema3.shift(1)) / ema3.shift(1)) * 100
                    # 5. TRIX Signal (TRIX의 9일 EMA)
                    trix_signal = trix.ewm(span=9, adjust=False).mean()
                    
                    current_trix = technicals.get('current_trix', 'N/A')
                    current_trix_signal = technicals.get('current_trix_signal', 'N/A')
                    
                    # Price & TRIX 차트 (2개 subplot)
                    fig_trix = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('Price', f'TRIX(30) - Current: {current_trix:.4f}' if current_trix != 'N/A' else 'TRIX(30)'),
                        row_heights=[0.6, 0.4],
                        vertical_spacing=0.1
                    )
                    
                    # Price 차트
                    fig_trix.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=hist['Close'],
                            name='Close Price',
                            line=dict(color='blue', width=1)
                        ),
                        row=1, col=1
                    )
                    
                    # TRIX 차트
                    fig_trix.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=trix,
                            name='TRIX',
                            line=dict(color='purple', width=2)
                        ),
                        row=2, col=1
                    )
                    
                    # TRIX Signal 라인
                    fig_trix.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=trix_signal,
                            name='TRIX Signal',
                            line=dict(color='orange', width=1, dash='dash')
                        ),
                        row=2, col=1
                    )
                    
                    # Zero line
                    fig_trix.add_hline(
                        y=0,
                        line_dash="dot",
                        line_color="gray",
                        annotation_text="Zero Line",
                        row=2, col=1
                    )
                    
                    fig_trix.update_layout(
                        title="Price & TRIX(30) Indicator",
                        height=600,
                        showlegend=True,
                        xaxis_rangeslider_visible=False
                    )
                    
                    fig_trix.update_yaxes(title_text="Price ($)", row=1, col=1)
                    fig_trix.update_yaxes(title_text="TRIX", row=2, col=1)
                    fig_trix.update_xaxes(title_text="Date", row=2, col=1)
                    
                    st.plotly_chart(fig_trix, use_container_width=True)
                else:
                    st.info("TRIX data not available (insufficient historical data).")
                    
            except Exception as e:
                st.warning(f"Could not create TRIX chart: {str(e)}")
            
            # Technical Indicators Summary
            st.subheader("Technical Indicators Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                rsi = technicals.get('current_rsi', 'N/A')
                rsi_status = ""
                if rsi != 'N/A':
                    if rsi > 70:
                        rsi_status = " (Overbought)"
                    elif rsi < 30:
                        rsi_status = " (Oversold)"
                st.metric("RSI(14)", f"{rsi}{rsi_status}" if rsi != 'N/A' else "N/A")
            
            with col2:
                trix = technicals.get('current_trix', 'N/A')
                st.metric("TRIX(30)", f"{trix}" if trix != 'N/A' else "N/A")
            
            with col3:
                volume_ratio = technicals.get('volume_ratio', 'N/A')
                st.metric("Volume Ratio", f"{volume_ratio}" if volume_ratio != 'N/A' else "N/A")
            
            with col4:
                earnings_d_day = technicals.get('earnings_d_day', 'N/A')
                earnings_date = technicals.get('earnings_date', 'N/A')
                if earnings_d_day != 'N/A' and earnings_date != 'N/A':
                    st.metric("Next Earnings", f"{earnings_date} (D-{earnings_d_day})")
                else:
                    st.metric("Next Earnings", "N/A")
            
            # Earnings Alert
            if technicals.get('earnings_d_day') is not None and technicals.get('earnings_d_day') <= 7:
                st.warning(f"⚠️ Earnings Alert: Next earnings in {technicals.get('earnings_d_day')} days. High volatility expected.")
            
            # News Feed
            st.subheader("Recent News")
            news_context = data.get('news_context', {})
            recent_news = news_context.get('recent_news', [])
            
            if recent_news:
                for i, news in enumerate(recent_news[:5], 1):
                    with st.expander(f"{i}. {news.get('title', 'N/A')}"):
                        st.write(f"**Publisher:** {news.get('publisher', 'N/A')}")
                        st.write(f"**Published:** {news.get('publishTime', 'N/A')}")
                        st.write(f"**Link:** {news.get('link', 'N/A')}")
                        if news.get('summary') and news.get('summary') != 'N/A':
                            st.write(f"**Summary:** {news.get('summary')}")
            else:
                st.info("No recent news available.")
    
    # Tab 5: Raw Data
    with tab5:
        st.header("📊 Raw Data")
        st.markdown("View all raw data collected for detailed analysis.")
        st.markdown("---")
        
        # 1. Profile (Company Info) - Raw
        with st.expander("📌 Company Profile (Raw)", expanded=False):
            st.subheader("Company Profile Data")
            profile_raw = data.get('profile', {})
            if profile_raw:
                # 딕셔너리를 JSON 형태로 표시
                st.json(profile_raw)
            else:
                st.info("Profile data not available.")
        
        # 2. Annual Financial Statements
        with st.expander("📈 Annual Financial Statements", expanded=False):
            financials = data.get('financials', {})
            raw_data = financials.get('raw_data', {})
            annual_data = raw_data.get('annual', {})
            
            # Income Statement
            st.subheader("Income Statement (Annual)")
            income_stmt = annual_data.get('income_stmt', pd.DataFrame())
            if not income_stmt.empty:
                st.dataframe(income_stmt, use_container_width=True, height=400)
                # CSV 다운로드 버튼
                csv_income = income_stmt.to_csv()
                st.download_button(
                    label="📥 Download Income Statement as CSV",
                    data=csv_income,
                    file_name=f"{ticker}_income_statement_annual.csv",
                    mime="text/csv"
                )
            else:
                st.info("Income statement data not available.")
            
            st.markdown("---")
            
            # Balance Sheet
            st.subheader("Balance Sheet (Annual)")
            balance_sheet = annual_data.get('balance_sheet', pd.DataFrame())
            if not balance_sheet.empty:
                st.dataframe(balance_sheet, use_container_width=True, height=400)
                csv_balance = balance_sheet.to_csv()
                st.download_button(
                    label="📥 Download Balance Sheet as CSV",
                    data=csv_balance,
                    file_name=f"{ticker}_balance_sheet_annual.csv",
                    mime="text/csv"
                )
            else:
                st.info("Balance sheet data not available.")
            
            st.markdown("---")
            
            # Cash Flow
            st.subheader("Cash Flow Statement (Annual)")
            cashflow = annual_data.get('cashflow', pd.DataFrame())
            if not cashflow.empty:
                st.dataframe(cashflow, use_container_width=True, height=400)
                csv_cashflow = cashflow.to_csv()
                st.download_button(
                    label="📥 Download Cash Flow as CSV",
                    data=csv_cashflow,
                    file_name=f"{ticker}_cashflow_annual.csv",
                    mime="text/csv"
                )
            else:
                st.info("Cash flow data not available.")
        
        # 3. Quarterly Financial Statements
        with st.expander("📊 Quarterly Financial Statements", expanded=False):
            quarterly_data = raw_data.get('quarterly', {})
            
            # Quarterly 데이터 상태 표시
            quarterly_status = financials.get('quarterly_data_status', {})
            if quarterly_status:
                st.markdown("### 📋 Quarterly Data Status")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Has Data", "✅ Yes" if quarterly_status.get('has_data') else "❌ No")
                    st.metric("Total Quarters", quarterly_status.get('total_quarters', 0))
                with col2:
                    st.write(f"**Income Stmt Periods:** {quarterly_status.get('income_stmt_periods', 0)}")
                    st.write(f"**Balance Sheet Periods:** {quarterly_status.get('balance_sheet_periods', 0)}")
                    st.write(f"**Cash Flow Periods:** {quarterly_status.get('cashflow_periods', 0)}")
                with col3:
                    if quarterly_status.get('earliest_date'):
                        st.write(f"**Earliest Date:** {quarterly_status.get('earliest_date')}")
                    if quarterly_status.get('latest_date'):
                        st.write(f"**Latest Date:** {quarterly_status.get('latest_date')}")
                    if quarterly_status.get('missing_data'):
                        st.warning(f"⚠️ Missing: {', '.join(quarterly_status.get('missing_data', []))}")
                
                if not quarterly_status.get('has_data'):
                    st.info("💡 **Note:** yfinance does not provide quarterly financial data for this ticker, or the data is not available. This is a limitation of the data source, not a bug in the application.")
                
                st.markdown("---")
            
            # Quarterly Income Statement
            st.subheader("Income Statement (Quarterly)")
            q_income_stmt = quarterly_data.get('income_stmt', pd.DataFrame())
            if not q_income_stmt.empty:
                st.dataframe(q_income_stmt, use_container_width=True, height=400)
                csv_q_income = q_income_stmt.to_csv()
                st.download_button(
                    label="📥 Download Quarterly Income Statement as CSV",
                    data=csv_q_income,
                    file_name=f"{ticker}_income_statement_quarterly.csv",
                    mime="text/csv"
                )
            else:
                st.info("Quarterly income statement data not available.")
            
            st.markdown("---")
            
            # Quarterly Balance Sheet
            st.subheader("Balance Sheet (Quarterly)")
            q_balance_sheet = quarterly_data.get('balance_sheet', pd.DataFrame())
            if not q_balance_sheet.empty:
                st.dataframe(q_balance_sheet, use_container_width=True, height=400)
                csv_q_balance = q_balance_sheet.to_csv()
                st.download_button(
                    label="📥 Download Quarterly Balance Sheet as CSV",
                    data=csv_q_balance,
                    file_name=f"{ticker}_balance_sheet_quarterly.csv",
                    mime="text/csv"
                )
            else:
                st.info("Quarterly balance sheet data not available.")
            
            st.markdown("---")
            
            # Quarterly Cash Flow
            st.subheader("Cash Flow Statement (Quarterly)")
            q_cashflow = quarterly_data.get('cashflow', pd.DataFrame())
            if not q_cashflow.empty:
                st.dataframe(q_cashflow, use_container_width=True, height=400)
                csv_q_cashflow = q_cashflow.to_csv()
                st.download_button(
                    label="📥 Download Quarterly Cash Flow as CSV",
                    data=csv_q_cashflow,
                    file_name=f"{ticker}_cashflow_quarterly.csv",
                    mime="text/csv"
                )
            else:
                st.info("Quarterly cash flow data not available.")
        
        # 4. Derived Metrics (Raw) - 추세 포함
        with st.expander("🔢 Derived Metrics with Trends", expanded=False):
            st.subheader("Calculated Financial Metrics")
            
            # 연간 추세
            st.markdown("### 📈 Annual Trends")
            metrics_annual = financials.get('derived_metrics', {})
            if metrics_annual:
                # 테이블 형태로 표시
                metrics_list = []
                for metric_name, metric_data in metrics_annual.items():
                    if isinstance(metric_data, dict):
                        metrics_list.append({
                            "Metric": metric_name.replace('_', ' ').title(),
                            "Latest Value": metric_data.get('latest', 'N/A'),
                            "Trend/Status": metric_data.get('trend', metric_data.get('status', 'N/A')),
                            "Warning": metric_data.get('warning', False) if 'warning' in metric_data else 'N/A',
                            "Has Time Series": len(metric_data.get('time_series', [])) > 0
                        })
                
                if metrics_list:
                    df_metrics = pd.DataFrame(metrics_list)
                    st.dataframe(df_metrics, use_container_width=True, hide_index=True)
                    
                    # 추세 차트
                    st.markdown("#### Annual Trend Charts")
                    charts_created = 0
                    for metric_name, metric_data in metrics_annual.items():
                        if isinstance(metric_data, dict) and 'time_series' in metric_data:
                            time_series = metric_data.get('time_series', [])
                            if time_series and len(time_series) > 1:  # 최소 2개 데이터 포인트 필요
                                try:
                                    df_trend = pd.DataFrame(time_series)
                                    if 'date' in df_trend.columns and 'value' in df_trend.columns:
                                        # 날짜 순서 정렬 (최신이 앞)
                                        df_trend = df_trend.sort_values('date', ascending=False)
                                        
                                        fig = go.Figure()
                                        fig.add_trace(go.Scatter(
                                            x=df_trend['date'],
                                            y=df_trend['value'],
                                            mode='lines+markers',
                                            name=metric_name.replace('_', ' ').title(),
                                            line=dict(width=2)
                                        ))
                                        fig.update_layout(
                                            title=f"{metric_name.replace('_', ' ').title()} - Annual Trend",
                                            xaxis_title="Date",
                                            yaxis_title="Value",
                                            height=300,
                                            xaxis_tickangle=-45
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                        charts_created += 1
                                except Exception as e:
                                    st.warning(f"Could not create chart for {metric_name}: {str(e)}")
                    
                    if charts_created == 0:
                        st.info("No trend charts available (insufficient data points)")
            else:
                st.info("Annual derived metrics not available.")
            
            # 쿼터별 추세
            st.markdown("---")
            st.markdown("### 📊 Quarterly Trends")
            metrics_quarterly = financials.get('derived_metrics_quarterly', {})
            if metrics_quarterly:
                # 테이블 형태로 표시
                q_metrics_list = []
                for metric_name, metric_data in metrics_quarterly.items():
                    if isinstance(metric_data, dict):
                        q_metrics_list.append({
                            "Metric": metric_name.replace('_', ' ').title(),
                            "Latest Value": metric_data.get('latest', 'N/A'),
                            "Trend/Status": metric_data.get('trend', metric_data.get('status', 'N/A'))
                        })
                
                if q_metrics_list:
                    df_q_metrics = pd.DataFrame(q_metrics_list)
                    st.dataframe(df_q_metrics, use_container_width=True, hide_index=True)
                    
                    # 쿼터별 추세 차트
                    st.markdown("#### Quarterly Trend Charts")
                    q_charts_created = 0
                    for metric_name, metric_data in metrics_quarterly.items():
                        if isinstance(metric_data, dict) and 'time_series' in metric_data:
                            time_series = metric_data.get('time_series', [])
                            if time_series and len(time_series) > 1:  # 최소 2개 데이터 포인트 필요
                                try:
                                    df_trend = pd.DataFrame(time_series)
                                    if 'date' in df_trend.columns and 'value' in df_trend.columns:
                                        # 날짜 순서 정렬 (최신이 앞)
                                        df_trend = df_trend.sort_values('date', ascending=False)
                                        
                                        fig = go.Figure()
                                        fig.add_trace(go.Scatter(
                                            x=df_trend['date'],
                                            y=df_trend['value'],
                                            mode='lines+markers',
                                            name=metric_name.replace('_', ' ').title(),
                                            line=dict(width=2, color='orange')
                                        ))
                                        fig.update_layout(
                                            title=f"{metric_name.replace('_', ' ').title()} - Quarterly Trend",
                                            xaxis_title="Quarter",
                                            yaxis_title="Value",
                                            height=300,
                                            xaxis_tickangle=-45
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                        q_charts_created += 1
                                except Exception as e:
                                    st.warning(f"Could not create quarterly chart for {metric_name}: {str(e)}")
                    
                    if q_charts_created == 0:
                        st.info("No quarterly trend charts available (insufficient data points)")
            else:
                st.info("💡 Quarterly trends are not available. This may be because:\n"
                       "- yfinance does not provide quarterly financial data for this ticker\n"
                       "- The quarterly data is incomplete\n"
                       "- The ticker is too new or delisted")
            
            # JSON Export
            st.markdown("---")
            with st.expander("📋 Raw JSON Data", expanded=False):
                import json
                all_metrics = {
                    'annual': metrics_annual,
                    'quarterly': metrics_quarterly
                }
                st.json(all_metrics)
        
        # 5. Technical Indicators (Raw)
        with st.expander("📈 Technical Indicators (Raw)", expanded=False):
            technicals = data.get('technicals', {})
            
            if technicals.get('error'):
                st.error(f"Error loading technical data: {technicals.get('error')}")
            else:
                st.subheader("Price Data & Technical Indicators")
                
                # Price Data DataFrame
                price_data = technicals.get('price_data')
                if price_data is not None and not price_data.empty:
                    st.markdown("### Historical Price Data")
                    # 주요 컬럼만 표시 (너무 많으면 성능 저하)
                    display_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    if 'RSI' in price_data.columns:
                        display_cols.append('RSI')
                    if 'TRIX' in price_data.columns:
                        display_cols.append('TRIX')
                    if 'MA_20' in price_data.columns:
                        display_cols.extend(['MA_20', 'MA_60', 'MA_120'])
                    
                    available_cols = [col for col in display_cols if col in price_data.columns]
                    if available_cols:
                        st.dataframe(price_data[available_cols], use_container_width=True, height=400)
                        csv_price = price_data[available_cols].to_csv()
                        st.download_button(
                            label="📥 Download Price Data as CSV",
                            data=csv_price,
                            file_name=f"{ticker}_price_data.csv",
                            mime="text/csv"
                        )
                    else:
                        st.dataframe(price_data, use_container_width=True, height=400)
                else:
                    st.info("Price data not available.")
                
                st.markdown("---")
                
                # Current Technical Indicators
                st.markdown("### Current Technical Indicator Values")
                tech_summary = {
                    "RSI(14)": technicals.get('current_rsi', 'N/A'),
                    "TRIX(30)": technicals.get('current_trix', 'N/A'),
                    "TRIX Signal": technicals.get('current_trix_signal', 'N/A'),
                    "Volume Ratio": technicals.get('volume_ratio', 'N/A'),
                    "MA 20": technicals.get('ma_data', {}).get('MA_20', 'N/A'),
                    "MA 60": technicals.get('ma_data', {}).get('MA_60', 'N/A'),
                    "MA 120": technicals.get('ma_data', {}).get('MA_120', 'N/A'),
                    "Earnings Date": technicals.get('earnings_date', 'N/A'),
                    "Earnings D-Day": technicals.get('earnings_d_day', 'N/A')
                }
                
                df_tech = pd.DataFrame(list(tech_summary.items()), columns=["Indicator", "Value"])
                st.dataframe(df_tech, use_container_width=True, hide_index=True)
        
        # 6. News Context (Raw)
        with st.expander("📰 News Context (Raw)", expanded=False):
            news_context = data.get('news_context', {})
            
            # Recent News
            st.subheader("Recent News (Raw)")
            recent_news = news_context.get('recent_news', [])
            if recent_news:
                st.json(recent_news)
                
                # 테이블 형태로도 표시
                st.markdown("### Recent News Table")
                news_table = []
                for news in recent_news:
                    news_table.append({
                        "Title": news.get('title', 'N/A'),
                        "Publisher": news.get('publisher', 'N/A'),
                        "Published": news.get('publishTime', 'N/A'),
                        "Link": news.get('link', 'N/A')[:50] + "..." if news.get('link', 'N/A') != 'N/A' and len(news.get('link', '')) > 50 else news.get('link', 'N/A')
                    })
                if news_table:
                    df_news = pd.DataFrame(news_table)
                    st.dataframe(df_news, use_container_width=True, hide_index=True)
            else:
                st.info("Recent news not available.")
            
            st.markdown("---")
            
            # Historical Events
            st.subheader("Historical Volatile Events")
            historical_events = news_context.get('historical_events', [])
            if historical_events:
                st.json(historical_events)
                
                # 테이블 형태로도 표시
                st.markdown("### Historical Events Table")
                events_table = []
                for event in historical_events:
                    events_table.append({
                        "Date": event.get('date', 'N/A'),
                        "Change %": event.get('change_pct', 'N/A'),
                        "Close Price": event.get('close_price', 'N/A'),
                        "Volume": event.get('volume', 'N/A')
                    })
                if events_table:
                    df_events = pd.DataFrame(events_table)
                    st.dataframe(df_events, use_container_width=True, hide_index=True)
            else:
                st.info("Historical events data not available.")
        
        # 7. All Raw Data (JSON Export)
        with st.expander("💾 Export All Raw Data", expanded=False):
            st.subheader("Export All Data as JSON")
            st.markdown("Download all collected raw data in JSON format for external analysis.")
            
            try:
                # 전체 데이터를 JSON으로 변환 (DataFrame은 dict로 변환)
                export_data = {}
                export_data['profile'] = data.get('profile', {})
                
                # Financials - DataFrame을 dict로 변환
                financials_export = {}
                raw_data_export = {}
                
                # Annual
                annual_export = {}
                for key, df in raw_data.get('annual', {}).items():
                    if not df.empty:
                        annual_export[key] = df.to_dict('index')
                raw_data_export['annual'] = annual_export
                
                # Quarterly
                quarterly_export = {}
                for key, df in raw_data.get('quarterly', {}).items():
                    if not df.empty:
                        quarterly_export[key] = df.to_dict('index')
                raw_data_export['quarterly'] = quarterly_export
                
                financials_export['raw_data'] = raw_data_export
                financials_export['derived_metrics'] = financials.get('derived_metrics', {})
                export_data['financials'] = financials_export
                
                # Technicals - DataFrame 제외하고 dict만
                technicals_export = {k: v for k, v in technicals.items() if k != 'price_data'}
                if price_data is not None and not price_data.empty:
                    technicals_export['price_data_sample'] = price_data.head(100).to_dict('index')  # 샘플만
                export_data['technicals'] = technicals_export
                
                export_data['news_context'] = news_context
                
                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="📥 Download All Raw Data as JSON",
                    data=json_str,
                    file_name=f"{ticker}_raw_data.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error preparing export data: {str(e)}")
                st.info("Please try exporting individual data sections above.")

else:
    st.info("👈 Enter a ticker symbol and click 'Run Analysis' to start.")

