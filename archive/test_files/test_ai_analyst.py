"""
AIAnalyst 테스트 스크립트
"""

from data_manager import StockDataManager
from ai_analyst import AIAnalyst

def test_ai_analyst():
    """AIAnalyst 클래스 테스트"""
    
    print("=" * 80)
    print("AIAnalyst 테스트")
    print("=" * 80)
    
    # API 키 입력 (테스트용 - 실제로는 환경변수나 설정에서 가져와야 함)
    api_key = input("Enter your Google Gemini API Key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("\n⚠️  API Key가 없어 리포트 생성 테스트를 건너뜁니다.")
        print("   AIAnalyst 클래스 구조만 확인합니다.\n")
        
        # 데이터 수집만 테스트
        print("[1] 데이터 수집 테스트")
        manager = StockDataManager("GOOGL")
        
        data = {
            'profile': manager.get_profile(),
            'financials': manager.get_financials(),
            'technicals': manager.get_technicals(),
            'news_context': manager.get_news_context()
        }
        
        print("✓ 데이터 수집 완료!")
        print(f"  - Profile: {len(data['profile'])} 항목")
        print(f"  - Financials: {len(data['financials'])} 섹션")
        print(f"  - Technicals: {len(data['technicals'])} 항목")
        print(f"  - News: {len(data['news_context'])} 섹션")
        
        print("\n[2] AI 점수 계산 테스트")
        try:
            analyst = AIAnalyst("dummy_key_for_test")
            score = analyst.calculate_ai_score(data, "Growth")
            verdict = analyst.get_verdict(score)
            print(f"✓ AI Score: {score}/100")
            print(f"✓ Verdict: {verdict}")
        except Exception as e:
            print(f"⚠️  점수 계산 테스트 실패 (API 키 필요): {e}")
        
        return
    
    # API 키가 있는 경우 실제 리포트 생성 테스트
    try:
        print("\n[1] AIAnalyst 초기화")
        analyst = AIAnalyst(api_key)
        print("✓ AIAnalyst 초기화 성공!")
        
        print("\n[2] 데이터 수집")
        manager = StockDataManager("GOOGL")
        
        data = {
            'profile': manager.get_profile(),
            'financials': manager.get_financials(),
            'technicals': manager.get_technicals(),
            'news_context': manager.get_news_context()
        }
        print("✓ 데이터 수집 완료!")
        
        print("\n[3] AI 점수 계산")
        score = analyst.calculate_ai_score(data, "Growth")
        verdict = analyst.get_verdict(score)
        print(f"✓ AI Score: {score}/100")
        print(f"✓ Verdict: {verdict}")
        
        print("\n[4] 리포트 생성 (Growth 전략)")
        print("   리포트 생성 중... (시간이 걸릴 수 있습니다)")
        report = analyst.generate_report("GOOGL", data, "Growth")
        print("\n" + "=" * 80)
        print("생성된 리포트:")
        print("=" * 80)
        print(report)
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analyst()

