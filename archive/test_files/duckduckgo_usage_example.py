"""
duckduckgo_search 사용 방식 설명 및 개선 예제

현재 문제점:
1. 검색 쿼리가 너무 일반적이어서 Apple과 관련 없는 기사가 나옴
2. 영문 기사 필터링이 없음
3. 관련성 필터링이 약함

개선 방안:
1. region='us-en' 설정으로 영문 결과만 가져오기
2. 검색 쿼리를 더 구체적으로 (회사명 + 티커 + 날짜)
3. 결과 필터링 강화 (제목/본문에 티커나 회사명 포함 확인)
"""

from duckduckgo_search import DDGS
import re

def improved_search_example(ticker: str, company_name: str, date_str: str):
    """
    개선된 검색 예제
    
    Args:
        ticker: 주식 티커 (예: 'AAPL')
        company_name: 회사명 (예: 'Apple Inc.')
        date_str: 날짜 (예: '2025-04-09')
    """
    
    # 1. 검색 쿼리 개선
    # 기존: "{Ticker} stock news {Date}" -> 너무 일반적
    # 개선: 회사명과 티커를 모두 포함하고, 더 구체적인 키워드 사용
    company_main = company_name.split()[0] if company_name else ticker  # "Apple Inc." -> "Apple"
    query = f'"{company_main}" {ticker} stock price news {date_str} earnings financial'
    
    print(f"검색 쿼리: {query}")
    
    # 2. DDGS 사용 (region='us-en'으로 영문 결과만)
    with DDGS() as ddgs:
        # region='us-en': 미국 영문 결과만
        # max_results=10: 더 많은 결과를 가져와서 필터링
        results = list(ddgs.text(
            keywords=query,
            region='us-en',  # 영문 결과만
            safesearch='moderate',
            max_results=10
        ))
    
    print(f"\n원본 검색 결과: {len(results)}개")
    
    # 3. 필터링: 관련성 높은 영문 기사만 선택
    filtered_results = []
    
    for result in results:
        title = result.get('title', '')
        body = result.get('body', '')
        href = result.get('href', '')
        
        # 3-1. 영문 기사인지 확인 (한글, 일본어, 중국어 등 제외)
        if not is_english_text(title + ' ' + body):
            continue
        
        # 3-2. 티커나 회사명이 포함되어 있는지 확인
        ticker_upper = ticker.upper()
        company_keywords = [word for word in company_main.split() if len(word) > 2]
        
        has_ticker = ticker_upper in title.upper() or ticker_upper in body.upper()
        has_company = any(keyword.upper() in title.upper() or keyword.upper() in body.upper() 
                         for keyword in company_keywords)
        
        if not (has_ticker or has_company):
            continue
        
        # 3-3. 관련 없는 키워드 제외 (로그인, 다운로드 등)
        exclude_keywords = ['LOGIN', 'PASSWORD', 'DOWNLOAD', 'INSTALL', 'SIGN IN', 
                           'ACCOUNT', 'RECOVER', 'COMMUNITY', 'SUPPORT']
        if any(keyword in title.upper() or keyword in body.upper() for keyword in exclude_keywords):
            continue
        
        # 3-4. 금융 뉴스 사이트 우선 (선택사항)
        finance_sites = ['yahoo.com', 'bloomberg.com', 'reuters.com', 'cnbc.com', 
                        'wsj.com', 'marketwatch.com', 'ft.com', 'forbes.com']
        is_finance_site = any(site in href.lower() for site in finance_sites)
        
        filtered_results.append({
            'title': title,
            'body': body[:200],  # 200자로 제한
            'href': href,
            'relevance_score': calculate_relevance(title, body, ticker, company_main, is_finance_site)
        })
    
    # 관련성 점수 순으로 정렬
    filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    print(f"\n필터링된 결과: {len(filtered_results)}개")
    for i, result in enumerate(filtered_results[:3], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   점수: {result['relevance_score']}")
        print(f"   URL: {result['href']}")
    
    return filtered_results[:3]  # 상위 3개만 반환


def is_english_text(text: str) -> bool:
    """텍스트가 영문인지 확인 (한글, 일본어, 중국어 등 제외)"""
    if not text:
        return False
    
    # 영문, 숫자, 기본 구두점만 포함되어 있는지 확인
    # 한글, 일본어, 중국어 등이 포함되어 있으면 False
    english_pattern = re.compile(r'^[a-zA-Z0-9\s\.,;:!?\'"\-()]+$')
    
    # 샘플링 (처음 100자만 확인)
    sample = text[:100]
    
    # 영문 비율이 80% 이상이면 영문으로 간주
    english_chars = sum(1 for c in sample if c.isascii() and (c.isalpha() or c.isspace() or c in '.,;:!?\'"-()'))
    total_chars = len([c for c in sample if c.isalnum() or c.isspace()])
    
    if total_chars == 0:
        return False
    
    english_ratio = english_chars / total_chars if total_chars > 0 else 0
    
    return english_ratio >= 0.8


def calculate_relevance(title: str, body: str, ticker: str, company_name: str, is_finance_site: bool) -> int:
    """관련성 점수 계산"""
    score = 0
    text = (title + ' ' + body).upper()
    ticker_upper = ticker.upper()
    company_upper = company_name.upper()
    
    # 티커 포함 (높은 가중치)
    if ticker_upper in text:
        score += 10
    
    # 회사명 포함
    if company_upper in text:
        score += 8
    
    # 주식 관련 키워드
    stock_keywords = ['STOCK', 'SHARE', 'PRICE', 'TRADING', 'MARKET', 'EARNINGS', 
                     'REVENUE', 'FINANCIAL', 'INVESTMENT', 'ANALYST', 'RATING']
    for keyword in stock_keywords:
        if keyword in text:
            score += 2
            break
    
    # 금융 사이트 (높은 가중치)
    if is_finance_site:
        score += 5
    
    return score


if __name__ == "__main__":
    # 테스트
    improved_search_example('AAPL', 'Apple Inc.', '2025-04-09')

