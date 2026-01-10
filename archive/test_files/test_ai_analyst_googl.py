"""
AIAnalyst GOOGL 테스트 스크립트
"""

from data_manager import StockDataManager
from ai_analyst import AIAnalyst

def test_ai_analyst_googl():
    """GOOGL 티커로 AIAnalyst 테스트"""
    
    print("=" * 80)
    print("AIAnalyst 테스트 - GOOGL")
    print("=" * 80)
    
    api_key = "AIzaSyAOmZJFTplfHjXVW4ZXn2v_V6LXiHO43F0"
    
    try:
        print("\n[1] AIAnalyst 초기화")
        analyst = AIAnalyst(api_key)
        print("✓ AIAnalyst 초기화 성공!")
        
        print("\n[2] 데이터 수집 중...")
        manager = StockDataManager("GOOGL")
        
        print("  - Profile 수집 중...")
        profile = manager.get_profile()
        
        print("  - Financials 수집 중...")
        financials = manager.get_financials()
        
        print("  - Technicals 수집 중...")
        technicals = manager.get_technicals()
        
        print("  - News Context 수집 중...")
        news_context = manager.get_news_context()
        
        data = {
            'profile': profile,
            'financials': financials,
            'technicals': technicals,
            'news_context': news_context
        }
        print("✓ 데이터 수집 완료!")
        
        print("\n[3] AI 점수 계산")
        score_growth = analyst.calculate_ai_score(data, "Growth")
        verdict_growth = analyst.get_verdict(score_growth)
        print(f"✓ Growth 전략 - AI Score: {score_growth}/100")
        print(f"✓ Growth 전략 - Verdict: {verdict_growth}")
        
        score_value = analyst.calculate_ai_score(data, "Value")
        verdict_value = analyst.get_verdict(score_value)
        print(f"✓ Value 전략 - AI Score: {score_value}/100")
        print(f"✓ Value 전략 - Verdict: {verdict_value}")
        
        print("\n[4] 리포트 생성 (Growth 전략)")
        print("   리포트 생성 중... (시간이 걸릴 수 있습니다)")
        report_growth = analyst.generate_report("GOOGL", data, "Growth")
        print("\n" + "=" * 80)
        print("생성된 리포트 (Growth 전략):")
        print("=" * 80)
        print(report_growth)
        print("=" * 80)
        
        print("\n[5] 리포트 생성 (Value 전략)")
        print("   리포트 생성 중... (시간이 걸릴 수 있습니다)")
        report_value = analyst.generate_report("GOOGL", data, "Value")
        print("\n" + "=" * 80)
        print("생성된 리포트 (Value 전략):")
        print("=" * 80)
        print(report_value)
        print("=" * 80)
        
        print("\n" + "=" * 80)
        print("테스트 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analyst_googl()

