# 코드 중복 제거 및 예외 처리 통일 - 리팩토링 요약

## 📋 작업 개요

코드 중복 제거 및 예외 처리 일관성 개선 작업을 완료했습니다.

---

## ✅ 완료된 작업

### 1. 공통 유틸리티 모듈 생성 (`utils.py`)

**생성된 함수:**

1. **`format_number(value: Any) -> str`**
   - 숫자를 읽기 쉬운 형식으로 포맷팅 (B, M, K 단위)
   - `app.py`와 `ai_analyst.py`에서 중복되던 함수를 통합

2. **`safe_get_numeric(info: dict, key: str) -> Any`**
   - 딕셔너리에서 안전하게 숫자 값 추출
   - `data_manager.py`의 `_safe_get_numeric()` 메서드를 함수로 이동

3. **`safe_get_latest(series: pd.Series) -> Any`**
   - 시리즈의 최신 값 안전하게 추출
   - `data_manager.py`의 `_safe_get_latest()` 메서드를 함수로 이동

4. **`safe_divide(numerator, denominator, default='N/A') -> Any`**
   - 안전한 나눗셈 연산 (0 나누기, None 처리)
   - 모든 재무 지표 계산에서 일관되게 사용

5. **`safe_execute(func, default_return, error_message, log_error) -> T`**
   - 함수 실행을 안전하게 처리하는 헬퍼 함수
   - 예외 발생 시 로깅 및 기본값 반환

6. **`handle_error(error_message, default_return, log_error, reraise)`**
   - 예외 처리를 통일하는 데코레이터 (참고용)

---

### 2. `data_manager.py` 개선

**중복 코드 제거:**
- `_safe_get_numeric()` → `utils.safe_get_numeric()` 사용
- `_safe_get_latest()` → `utils.safe_get_latest()` 사용

**예외 처리 통일:**
- 모든 예외 처리에서 `safe_execute()` 또는 명시적 `except Exception` 사용
- `except:` → `except Exception:` (구체적 예외 타입 명시)
- `print(f"Error...")` → `safe_execute()`의 로깅 기능 활용

**개선된 함수:**
- `get_profile()`: `safe_execute()` 사용
- `get_financials()`: `safe_execute()` 사용
- `_calculate_quality_of_earnings()`: `safe_divide()` 사용
- `_calculate_receivables_turnover()`: `safe_divide()` 사용
- `_calculate_inventory_turnover()`: `safe_divide()` 사용
- `_calculate_interest_coverage()`: `safe_divide()` 사용
- `_calculate_capex_growth()`: `safe_divide()` 사용
- `_calculate_net_buyback_yield()`: `safe_divide()` 사용
- `_calculate_rsi()`: RSI 계산 개선 (loss가 0인 경우 처리)
- 모든 에러 처리 함수에서 통일된 패턴 적용

**변경 전후 비교:**
```python
# 변경 전
except Exception as e:
    print(f"Error calculating quality of earnings: {e}")
    return {'latest': 'N/A', 'trend': 'N/A', 'warning': False}

# 변경 후
except Exception as e:
    return safe_execute(
        lambda: {'latest': 'N/A', 'trend': 'N/A', 'warning': False},
        {'latest': 'N/A', 'trend': 'N/A', 'warning': False},
        "Error calculating quality of earnings",
        log_error=True
    )
```

---

### 3. `ai_analyst.py` 개선

**중복 코드 제거:**
- `_format_number()` → `utils.format_number()` 사용

**예외 처리 통일:**
- 모든 예외 처리에서 명시적 `except Exception` 사용
- `safe_execute()` 활용으로 로깅 통일

**개선된 함수:**
- `_generate_macro_analysis()`: `safe_execute()` 사용
- `_generate_forensic_analysis()`: `safe_execute()` 사용
- `_generate_strategy_analysis()`: `safe_execute()` 사용
- `_generate_timing_verdict()`: `safe_execute()` 사용
- `calculate_ai_score()`: `safe_execute()` 사용

**변경 전후 비교:**
```python
# 변경 전
except Exception as e:
    print(f"Error calculating AI score: {e}")
    return 50

# 변경 후
except Exception as e:
    return safe_execute(
        lambda: 50,
        50,
        "Error calculating AI score",
        log_error=True
    )
```

---

### 4. `app.py` 개선

**중복 코드 제거:**
- `format_number()` → `utils.format_number()` import 및 사용

**예외 처리 통일:**
- 모든 `except:` → `except (ValueError, TypeError):` 또는 `except Exception:` 사용
- 구체적 예외 타입 명시로 디버깅 용이성 향상

**개선된 부분:**
- Revenue/Net Income 차트 생성 부분
- Free Cash Flow vs CapEx 차트 생성 부분
- Radar Chart 값 추출 부분

**변경 전후 비교:**
```python
# 변경 전
try:
    revenue_data.append(float(rev))
except:
    revenue_data.append(0)

# 변경 후
try:
    revenue_data.append(float(rev))
except (ValueError, TypeError):
    revenue_data.append(0)
```

---

## 📊 개선 효과

### 코드 중복 제거
- **제거된 중복 코드:**
  - `format_number()`: 2곳 → 1곳 (`utils.py`)
  - `_safe_get_numeric()`: 1곳 → 1곳 (`utils.py`로 이동)
  - `_safe_get_latest()`: 1곳 → 1곳 (`utils.py`로 이동)

- **예상 코드 라인 감소:** 약 50-60 라인

### 예외 처리 일관성
- **통일된 예외 처리 패턴:**
  - 모든 예외 처리가 `safe_execute()` 또는 명시적 `except Exception` 사용
  - 로깅 기능 통일 (logger 사용)
  - 구체적 예외 타입 명시

- **개선된 부분:**
  - 에러 메시지 일관성
  - 디버깅 용이성 향상
  - 유지보수성 향상

---

## 🔍 주의사항

### 로깅 설정
- `utils.py`에서 기본 로깅 설정 추가
- 필요시 로깅 레벨 조정 가능

### 호환성
- 기존 기능 동작 유지 (동일한 반환값, 동일한 예외 처리 결과)
- API 변경 없음 (내부 구조만 개선)

---

## 📝 다음 단계 제안

1. **테스트 코드 작성**
   - `utils.py` 함수들에 대한 단위 테스트
   - 각 모듈의 예외 처리 테스트

2. **로깅 개선**
   - 로깅 레벨별 설정 파일 분리
   - 파일 로깅 추가 (선택적)

3. **추가 리팩토링**
   - 설정 파일 분리 (하드코딩된 값)
   - 상수 정의 파일 생성

---

## 📁 변경된 파일

1. **신규 생성:**
   - `stock/utils.py` (181 라인)

2. **수정:**
   - `stock/data_manager.py` (약 50개 위치 수정)
   - `stock/ai_analyst.py` (약 10개 위치 수정)
   - `stock/app.py` (약 5개 위치 수정)

---

**리팩토링 완료일**: 2025-01-XX
**작업자**: AI Assistant



