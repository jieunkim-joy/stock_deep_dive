"""
개선된 _get_historical_news_context 메서드

주요 개선사항:
1. region='us-en' 설정으로 영문 결과만 가져오기
2. 검색 쿼리 개선 (회사명 + 티커 + 더 구체적인 키워드)
3. 영문 기사 필터링 강화
4. 관련성 필터링 강화 (티커/회사명 포함 확인)
"""

import pandas as pd
import re
from typing import Dict, Any, List

def _get_historical_news_context_improved(self) -> list:
    """
    개선된 과거 변동성 높은 날짜의 뉴스 검색
    
    주요 개선:
    1. region='us-en'으로 영문 결과만
    2. 검색 쿼리 개선 (회사명 + 티커)
    3. 영문 기사 필터링
    4. 관련성 필터링 강화
    """
    try:
        # 1. 최근 1년 주가 데이터 수집
        hist = self.ticker.history(period="1y", interval="1d")
        
        if hist.empty:
            return []
        
        # 2. 일일 변동률 계산 (절대값 기준)
        hist['Change'] = hist['Close'] - hist['Open']
        hist['Change%'] = ((hist['Close'] - hist['Open']) / hist['Open']) * 100
        hist['AbsChange%'] = abs(hist['Change%'])
        
        # 3. 변동폭이 가장 큰 상위 5일 추출
        top_5_volatile = hist.nlargest(5, 'AbsChange%')
        
        historical_events = []
        
        if not USE_DDG:
            # duckduckgo_search가 설치되지 않은 경우
            for date, row in top_5_volatile.iterrows():
                historical_events.append({
                    'date': date.strftime('%Y-%m-%d') if isinstance(date, pd.Timestamp) else str(date),
                    'change_pct': round(row['Change%'], 2),
                    'search_result': 'Search library not available',
                    'status': 'Library Missing'
                })
            return historical_events
        
        # 4. 회사명 가져오기 (검색 쿼리 개선을 위해)
        company_name = self._get_company_name()
        company_main = company_name.split()[0] if company_name and company_name != 'N/A' else self.ticker_symbol
        
        # 5. 각 날짜별로 duckduckgo_search 실행
        with DDGS() as ddgs:
            for date, row in top_5_volatile.iterrows():
                try:
                    date_str = date.strftime('%Y-%m-%d') if isinstance(date, pd.Timestamp) else str(date)
                    change_pct = round(row['Change%'], 2)
                    
                    # 검색 쿼리 개선: 회사명 + 티커 + 날짜 + 구체적인 키워드
                    query = f'"{company_main}" {self.ticker_symbol} stock price news {date_str} earnings financial market'
                    
                    # 검색 실행 (region='us-en'으로 영문 결과만)
                    search_results = list(ddgs.text(
                        keywords=query,
                        region='us-en',  # 영문 결과만
                        safesearch='moderate',
                        max_results=10  # 더 많은 결과를 가져와서 필터링
                    ))
                    
                    # 영문 기사만 필터링하고 관련성 높은 결과만 선택
                    filtered_results = self._filter_english_relevant_news(
                        search_results, 
                        self.ticker_symbol, 
                        company_main
                    )
                    
                    if filtered_results and len(filtered_results) > 0:
                        summaries = []
                        for result in filtered_results[:3]:  # 최대 3개 결과만
                            summaries.append({
                                'title': result['title'],
                                'snippet': result['body'],
                                'url': result['href']
                            })
                        
                        historical_events.append({
                            'date': date_str,
                            'change_pct': change_pct,
                            'search_result': summaries,
                            'status': 'Success'
                        })
                    else:
                        historical_events.append({
                            'date': date_str,
                            'change_pct': change_pct,
                            'search_result': [],
                            'status': 'No Results'
                        })
                        
                except Exception as e:
                    # 검색 실패 시에도 프로그램이 멈추지 않도록 처리
                    print(f"Error searching for {date}: {e}")
                    date_str = date.strftime('%Y-%m-%d') if isinstance(date, pd.Timestamp) else str(date)
                    change_pct = round(row['Change%'], 2)
                    historical_events.append({
                        'date': date_str,
                        'change_pct': change_pct,
                        'search_result': 'Search Failed',
                        'status': 'Error'
                    })
                    continue
        
        return historical_events
        
    except Exception as e:
        print(f"Error getting historical news context: {e}")
        return []


def _filter_english_relevant_news(self, search_results: List[Dict], ticker: str, company_name: str) -> List[Dict]:
    """
    영문 기사만 필터링하고 관련성 높은 뉴스만 선택
    
    Args:
        search_results: duckduckgo_search 결과 리스트
        ticker: 주식 티커 (예: 'AAPL')
        company_name: 회사명 (예: 'Apple')
    
    Returns:
        필터링된 결과 리스트
    """
    if not search_results:
        return []
    
    filtered = []
    ticker_upper = ticker.upper()
    company_upper = company_name.upper() if company_name else ''
    
    # 제외할 키워드 (관련 없는 결과 필터링)
    exclude_keywords = ['LOGIN', 'PASSWORD', 'DOWNLOAD', 'INSTALL', 'SIGN IN', 
                       'ACCOUNT', 'RECOVER', 'COMMUNITY', 'SUPPORT', 'HELP',
                       'SENHA', 'CONTA', 'CUENTA', 'アカウント', 'ログイン']
    
    for result in search_results:
        title = result.get('title', '')
        body = result.get('body', '')
        href = result.get('href', '')
        
        # 1. 영문 기사인지 확인
        if not self._is_english_text(title + ' ' + body):
            continue
        
        # 2. 제외 키워드 확인
        text_upper = (title + ' ' + body).upper()
        if any(keyword in text_upper for keyword in exclude_keywords):
            continue
        
        # 3. 티커나 회사명이 포함되어 있는지 확인 (필수)
        has_ticker = ticker_upper in title.upper() or ticker_upper in body.upper()
        has_company = company_upper and (company_upper in title.upper() or company_upper in body.upper())
        
        if not (has_ticker or has_company):
            continue
        
        # 4. 관련성 점수 계산
        relevance_score = self._calculate_relevance_score(
            title, body, href, ticker_upper, company_upper
        )
        
        # 관련성 점수가 5 이상인 결과만 선택
        if relevance_score >= 5:
            filtered.append({
                'title': title,
                'body': body[:200] if len(body) > 200 else body,  # 200자로 제한
                'href': href,
                'relevance_score': relevance_score
            })
    
    # 관련성 점수 순으로 정렬
    filtered.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return filtered


def _is_english_text(self, text: str) -> bool:
    """
    텍스트가 영문인지 확인
    
    한글, 일본어, 중국어 등이 포함되어 있으면 False 반환
    """
    if not text:
        return False
    
    # 샘플링 (처음 200자만 확인)
    sample = text[:200]
    
    # 영문 문자 비율 계산
    english_chars = sum(1 for c in sample if c.isascii() and (c.isalpha() or c.isspace() or c in '.,;:!?\'"-()'))
    total_chars = len([c for c in sample if c.isalnum() or c.isspace() or c in '.,;:!?\'"-()'])
    
    if total_chars == 0:
        return False
    
    # 영문 비율이 85% 이상이면 영문으로 간주
    english_ratio = english_chars / total_chars if total_chars > 0 else 0
    
    return english_ratio >= 0.85


def _calculate_relevance_score(self, title: str, body: str, href: str, 
                               ticker: str, company_name: str) -> int:
    """
    검색 결과의 관련성 점수 계산
    
    점수가 높을수록 더 관련성 높은 뉴스
    """
    score = 0
    text = (title + ' ' + body).upper()
    
    # 1. 티커 포함 (가장 높은 가중치)
    if ticker in title:
        score += 10  # 제목에 티커가 있으면 높은 점수
    elif ticker in body:
        score += 5   # 본문에 티커가 있으면 중간 점수
    
    # 2. 회사명 포함
    if company_name:
        if company_name in title:
            score += 8
        elif company_name in body:
            score += 4
    
    # 3. 주식 관련 키워드
    stock_keywords = ['STOCK', 'SHARE', 'PRICE', 'TRADING', 'MARKET', 'EARNINGS', 
                     'REVENUE', 'FINANCIAL', 'INVESTMENT', 'ANALYST', 'RATING', 
                     'DIVIDEND', 'EQUITY', 'SHARES']
    for keyword in stock_keywords:
        if keyword in title or keyword in body:
            score += 2
            break
    
    # 4. 금융 뉴스 사이트 (높은 가중치)
    finance_sites = ['yahoo.com', 'bloomberg.com', 'reuters.com', 'cnbc.com', 
                    'wsj.com', 'marketwatch.com', 'ft.com', 'forbes.com',
                    'seekingalpha.com', 'benzinga.com', 'thestreet.com', 
                    'investing.com', 'fool.com']
    for site in finance_sites:
        if site in href.lower():
            score += 5  # 금융 사이트는 높은 가중치
            break
    
    return score

