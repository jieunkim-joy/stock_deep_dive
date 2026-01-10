"""
StockDataManager 테스트 스크립트
AAPL 티커로 모든 메서드 테스트
"""

from data_manager import StockDataManager
import json
import pandas as pd

def test_stock_data_manager():
    """GOOGL 티커로 모든 메서드 테스트"""
    
    print("=" * 80)
    print("StockDataManager 테스트 시작 (GOOGL)")
    print("=" * 80)
    
    # StockDataManager 초기화
    print("\n[1] StockDataManager 초기화 중...")
    manager = StockDataManager("GOOGL")
    print(f"✓ Ticker: {manager.ticker_symbol}")
    
    # 1. get_profile 테스트
    print("\n" + "=" * 80)
    print("[2] get_profile() 테스트")
    print("=" * 80)
    try:
        profile = manager.get_profile()
        print("\n✓ get_profile() 성공!")
        print("\n결과:")
        for key, value in profile.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"✗ get_profile() 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. get_financials 테스트
    print("\n" + "=" * 80)
    print("[3] get_financials() 테스트")
    print("=" * 80)
    try:
        financials = manager.get_financials()
        print("\n✓ get_financials() 성공!")
        
        # Raw Data 확인
        print("\n[Raw Data - Annual]")
        annual_data = financials['raw_data']['annual']
        print(f"  Income Statement shape: {annual_data['income_stmt'].shape}")
        print(f"  Balance Sheet shape: {annual_data['balance_sheet'].shape}")
        print(f"  Cash Flow shape: {annual_data['cashflow'].shape}")
        
        print("\n[Raw Data - Quarterly]")
        quarterly_data = financials['raw_data']['quarterly']
        print(f"  Income Statement shape: {quarterly_data['income_stmt'].shape}")
        print(f"  Balance Sheet shape: {quarterly_data['balance_sheet'].shape}")
        print(f"  Cash Flow shape: {quarterly_data['cashflow'].shape}")
        
        # Derived Metrics 확인
        print("\n[Derived Metrics]")
        metrics = financials['derived_metrics']
        
        print("\n  1. Quality of Earnings:")
        qoe = metrics['quality_of_earnings']
        print(f"     Latest: {qoe['latest']}")
        print(f"     Trend: {qoe['trend']}")
        print(f"     Warning: {qoe['warning']}")
        
        print("\n  2. Receivables Turnover:")
        rt = metrics['receivables_turnover']
        print(f"     Latest: {rt['latest']}")
        print(f"     Trend: {rt['trend']}")
        
        print("\n  3. Inventory Turnover:")
        it = metrics['inventory_turnover']
        print(f"     Latest: {it['latest']}")
        print(f"     Trend: {it['trend']}")
        
        print("\n  4. Interest Coverage Ratio:")
        ic = metrics['interest_coverage']
        print(f"     Latest: {ic['latest']}")
        print(f"     Status: {ic['status']}")
        
        print("\n  5. CapEx Growth:")
        capex = metrics['capex_growth']
        print(f"     Latest: {capex['latest']}%")
        print(f"     Trend: {capex['trend']}")
        
        print("\n  6. Net Buyback Yield:")
        buyback = metrics['net_buyback_yield']
        print(f"     Latest: {buyback['latest']}%")
        print(f"     Status: {buyback['status']}")
        
        # 재무제표 샘플 데이터 출력
        if not annual_data['income_stmt'].empty:
            print("\n[Income Statement 샘플 - 최근 3년 (Annual)]")
            print(annual_data['income_stmt'][['Total Revenue', 'Net Income']].head())
        
        if not quarterly_data['income_stmt'].empty:
            print("\n[Income Statement 샘플 - 최근 4쿼터 (Quarterly)]")
            print(quarterly_data['income_stmt'][['Total Revenue', 'Net Income']].head())
            
    except Exception as e:
        print(f"✗ get_financials() 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. get_technicals 테스트
    print("\n" + "=" * 80)
    print("[4] get_technicals() 테스트")
    print("=" * 80)
    try:
        technicals = manager.get_technicals()
        
        if 'error' in technicals:
            print(f"✗ get_technicals() 오류: {technicals['error']}")
        else:
            print("\n✓ get_technicals() 성공!")
            
            print("\n[기술적 지표]")
            print(f"  Current RSI(14): {technicals['current_rsi']}")
            print(f"  Current TRIX(30): {technicals['current_trix']}")
            print(f"  Current TRIX Signal: {technicals['current_trix_signal']}")
            
            print("\n[이동평균선]")
            ma = technicals['ma_data']
            print(f"  MA_20: {ma['MA_20']}")
            print(f"  MA_60: {ma['MA_60']}")
            print(f"  MA_120: {ma['MA_120']}")
            
            print(f"\n  Volume Ratio (20일 평균 대비): {technicals['volume_ratio']}")
            
            print("\n[Earnings 정보]")
            print(f"  Earnings Date: {technicals['earnings_date']}")
            print(f"  Earnings D-Day: {technicals['earnings_d_day']}")
            
            # Price Data 샘플 출력
            if technicals['price_data'] is not None:
                price_df = technicals['price_data']
                print(f"\n[Price Data 샘플 - 최근 5일]")
                print(price_df[['Close', 'Volume', 'RSI', 'MA_20', 'MA_60']].tail())
                
    except Exception as e:
        print(f"✗ get_technicals() 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. get_news_context 테스트
    print("\n" + "=" * 80)
    print("[5] get_news_context() 테스트")
    print("=" * 80)
    try:
        news_context = manager.get_news_context()
        print("\n✓ get_news_context() 성공!")
        
        # Recent News 확인
        print("\n[Recent News]")
        recent_news = news_context.get('recent_news', [])
        print(f"  총 {len(recent_news)}개 뉴스 수집")
        if len(recent_news) > 0:
            print("\n  최신 뉴스 샘플 (최대 3개):")
            for i, news in enumerate(recent_news[:3], 1):
                print(f"\n  {i}. {news.get('title', 'N/A')}")
                print(f"     Publisher: {news.get('publisher', 'N/A')}")
                print(f"     Published: {news.get('publishTime', 'N/A')}")
                print(f"     Link: {news.get('link', 'N/A')}")
        
        # Historical Events 확인
        print("\n[Historical Events - Top 5 Volatile Dates]")
        historical_events = news_context.get('historical_events', [])
        print(f"  총 {len(historical_events)}개 이벤트 분석")
        if len(historical_events) > 0:
            for i, event in enumerate(historical_events, 1):
                print(f"\n  {i}. Date: {event.get('date', 'N/A')}")
                print(f"     Change: {event.get('change_pct', 'N/A')}%")
                print(f"     Close Price: ${event.get('close_price', 'N/A')}")
                print(f"     Volume: {event.get('volume', 'N/A'):,}" if event.get('volume') != 'N/A' else f"     Volume: {event.get('volume', 'N/A')}")
                    
    except Exception as e:
        print(f"✗ get_news_context() 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)

if __name__ == "__main__":
    test_stock_data_manager()

