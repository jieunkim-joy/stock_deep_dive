"""
Stock Deep-Dive AI - Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_manager import StockDataManager
from ai_analyst import AIAnalyst
import time

# Helper function
def format_number(value):
    """숫자를 읽기 쉬운 형식으로 포맷팅"""
    if value == 'N/A' or value is None:
        return 'N/A'
    
    try:
        num = float(value)
        if abs(num) >= 1e12:
            return f"{num/1e12:.2f}T"
        elif abs(num) >= 1e9:
            return f"{num/1e9:.2f}B"
        elif abs(num) >= 1e6:
            return f"{num/1e6:.2f}M"
        elif abs(num) >= 1e3:
            return f"{num/1e3:.2f}K"
        else:
            return f"{num:.2f}"
    except:
        return str(value)

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

# API Key 입력
api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    help="Enter your Google Gemini API key"
)

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
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
        st.stop()
    
    if not ticker:
        st.error("⚠️ Please enter a ticker symbol.")
        st.stop()
    
    # 진행 상황 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 1. 데이터 수집
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
        
        # 2. AI 분석
        status_text.text("🤖 Running AI analysis...")
        progress_bar.progress(60)
        
        analyst = AIAnalyst(api_key, model_name=gemini_model)
        ai_report = analyst.generate_report(ticker, data, strategy, language=lang_code)
        ai_score = analyst.calculate_ai_score(data, strategy)
        verdict = analyst.get_verdict(ai_score)
        
        st.session_state.ai_report = ai_report
        st.session_state.ai_score = ai_score
        st.session_state.verdict = verdict
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
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
    
    # Verdict 배지
    if st.session_state.verdict:
        st.markdown(f"### {st.session_state.verdict}")
    
    st.markdown("---")
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Executive Summary", "🌍 Macro & Industry", "💰 Financials", "📊 Technicals"])
    
    # Tab 1: Executive Summary
    with tab1:
        st.header("Executive Summary")
        
        if st.session_state.ai_report:
            # AI 리포트에서 Executive Summary 추출 (간단히 전체 리포트 표시)
            st.markdown(st.session_state.ai_report)
        else:
            st.info("Run analysis to see the executive summary.")
        
        # Radar Chart (간단한 버전)
        if st.session_state.ai_score is not None:
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
                except:
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
        else:
            st.info("Run analysis to see macro & industry analysis.")
        
        # Peer Comparison (간단한 버전)
        st.subheader("Company Profile")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Sector:** {profile.get('sector', 'N/A')}")
            st.write(f"**Industry:** {profile.get('industry', 'N/A')}")
            st.write(f"**Country:** {profile.get('country', 'N/A')}")
        with col2:
            st.write(f"**Market Cap:** ${format_number(profile.get('marketCap', 'N/A'))}")
            st.write(f"**Beta:** {profile.get('beta', 'N/A')}")
    
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
                            except:
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
                            except:
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
                            except:
                                fcf = None
                    
                    if pd.notna(fcf) and fcf != 'N/A':
                        try:
                            fcf_data.append(float(fcf))
                        except:
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
                        except:
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

else:
    st.info("👈 Enter a ticker symbol and click 'Run Analysis' to start.")

