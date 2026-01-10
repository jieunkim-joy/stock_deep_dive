"""
공통 유틸리티 함수 모듈
코드 중복 제거 및 일관된 예외 처리 제공
"""

from typing import Any, Callable, TypeVar, Optional
import pandas as pd
import logging

# 로깅 설정 (선택적 - 사용하지 않을 경우 INFO 레벨로 설정)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

T = TypeVar('T')


def format_number(value: Any) -> str:
    """
    숫자를 읽기 쉬운 형식으로 포맷팅
    
    Args:
        value: 포맷팅할 숫자 값 (int, float, str, None 등)
    
    Returns:
        포맷팅된 문자열 (예: "1.23B", "500.00M", "N/A")
    """
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
    except (ValueError, TypeError):
        return str(value)


def safe_get_numeric(info: dict, key: str) -> Any:
    """
    딕셔너리에서 안전하게 숫자 값 가져오기
    
    Args:
        info: 정보 딕셔너리
        key: 키 이름
    
    Returns:
        숫자 값 또는 'N/A'
    """
    try:
        value = info.get(key)
        if value is None or pd.isna(value):
            return 'N/A'
        return float(value) if isinstance(value, (int, float)) else value
    except Exception:
        return 'N/A'


def safe_get_latest(series: pd.Series) -> Any:
    """
    시리즈의 최신 값 안전하게 가져오기
    
    Args:
        series: pandas Series
    
    Returns:
        최신 값 (float, int) 또는 'N/A'
    """
    try:
        if series.empty:
            return 'N/A'
        latest = series.iloc[-1]
        if pd.isna(latest):
            return 'N/A'
        return round(float(latest), 2) if isinstance(latest, (int, float)) else latest
    except Exception:
        return 'N/A'


def handle_error(
    error_message: str,
    default_return: T,
    log_error: bool = True,
    reraise: bool = False
) -> Callable:
    """
    예외 처리를 통일하는 데코레이터
    
    Args:
        error_message: 에러 발생 시 로그 메시지
        default_return: 예외 발생 시 반환할 기본값
        log_error: 에러 로깅 여부
        reraise: 예외를 다시 발생시킬지 여부
    
    Returns:
        데코레이터 함수
    
    Usage:
        @handle_error("Error calculating metric", {'latest': 'N/A', 'trend': 'N/A'})
        def calculate_metric():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"{error_message}: {e}")
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    default_return: T,
    error_message: Optional[str] = None,
    log_error: bool = True
) -> T:
    """
    함수 실행을 안전하게 처리하는 헬퍼 함수
    
    Args:
        func: 실행할 함수
        default_return: 예외 발생 시 반환할 기본값
        error_message: 에러 메시지 (기본값: 함수명 사용)
        log_error: 에러 로깅 여부
    
    Returns:
        함수 실행 결과 또는 default_return
    
    Usage:
        result = safe_execute(
            lambda: calculate_ratio(numerator, denominator),
            {'latest': 'N/A', 'trend': 'N/A'},
            "Error calculating ratio"
        )
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            msg = error_message or f"Error in {func.__name__}"
            logger.error(f"{msg}: {e}")
        return default_return


def safe_divide(
    numerator: Any,
    denominator: Any,
    default: str = 'N/A'
) -> Any:
    """
    안전한 나눗셈 연산
    
    Args:
        numerator: 분자
        denominator: 분모
        default: 분모가 0이거나 None일 때 반환할 값
    
    Returns:
        나눗셈 결과 또는 default
    """
    try:
        if (pd.isna(numerator) or pd.isna(denominator) or 
            numerator is None or denominator is None or denominator == 0):
            return default
        return float(numerator) / float(denominator)
    except (ValueError, TypeError, ZeroDivisionError):
        return default

