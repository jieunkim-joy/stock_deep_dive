# duckduckgo_search 사용 방식 및 개선 가이드

## 현재 사용 방식

```python
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text(
        keywords=f"{ticker} stock news {date}",
        max_results=3
    ))
```

## 문제점

1. **다국어 결과**: `region` 파라미터를 설정하지 않아 한글, 일본어, 중국어 등 다양한 언어의 결과가 나옴
2. **관련성 낮음**: 검색 쿼리가 너무 일반적이어서 Apple과 관련 없는 기사가 포함됨
3. **필터링 부족**: 영문 기사만 필터링하는 로직이 없음

## 개선 방안

### 1. region='us-en' 설정
```python
results = list(ddgs.text(
    keywords=query,
    region='us-en',  # 영문 결과만 (하지만 완벽하지 않음)
    max_results=10
))
```

### 2. 검색 쿼리 개선
```python
# 기존: "AAPL stock news 2025-04-09"
# 개선: '"Apple" AAPL stock price news 2025-04-09 earnings financial market'
query = f'"{company_main}" {ticker} stock price news {date_str} earnings financial market'
```

### 3. 영문 필터링 함수 추가
```python
def _is_english_text(self, text: str) -> bool:
    """텍스트가 영문인지 확인 (85% 이상 영문 문자)"""
    sample = text[:200]
    english_chars = sum(1 for c in sample if c.isascii() and (c.isalpha() or c.isspace()))
    total_chars = len([c for c in sample if c.isalnum() or c.isspace()])
    english_ratio = english_chars / total_chars if total_chars > 0 else 0
    return english_ratio >= 0.85
```

### 4. 관련성 필터링 강화
- 티커나 회사명이 제목/본문에 포함되어 있는지 확인 (필수)
- 주식 관련 키워드 확인
- 금융 뉴스 사이트 우선
- 관련 없는 키워드 제외 (로그인, 다운로드 등)

## 적용 방법

`data_manager.py`의 `_get_historical_news_context` 메서드를 아래 개선된 버전으로 교체하세요.

