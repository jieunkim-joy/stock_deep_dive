"""
StockDataManager: 주식 데이터 수집 및 분석 클래스
yfinance를 활용하여 재무 데이터, 기술적 지표 등을 수집하고 계산합니다.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import warnings
from datetime import datetime, date

# duckduckgo_search 라이브러리
try:
    from duckduckgo_search import DDGS
    USE_DDG = True
except ImportError:
    USE_DDG = False
    print("Warning: duckduckgo_search not installed. Historical news search will be disabled.")

# pandas-ta가 Python 3.14를 지원하지 않으므로 직접 계산
try:
    import pandas_ta as ta
    USE_PANDAS_TA = True
except ImportError:
    USE_PANDAS_TA = False

warnings.filterwarnings('ignore')


class StockDataManager:
    """주식 데이터 수집 및 분석을 담당하는 클래스"""
    
    def __init__(self, ticker_symbol: str):
        """
        Args:
            ticker_symbol: 주식 티커 심볼 (예: 'AAPL', 'NVDA')
        """
        self.ticker_symbol = ticker_symbol.upper()
        
        # 최신 yfinance는 자체적으로 세션을 관리하므로 session 파라미터 제거
        # Ticker 객체 초기화
        self.ticker = yf.Ticker(self.ticker_symbol)
    
    def get_profile(self) -> Dict[str, Any]:
        """
        기업 기본 정보 및 거시 정보 수집
        
        Returns:
            Dict containing: sector, industry, country, marketCap, beta, 
                           longName, currentPrice, previousClose 등
        """
        try:
            info = self.ticker.info
            
            if not info or len(info) == 0:
                return self._empty_profile()
            
            profile = {
                'ticker': self.ticker_symbol,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'N/A'),
                'marketCap': self._safe_get_numeric(info, 'marketCap'),
                'beta': self._safe_get_numeric(info, 'beta'),
                'longName': info.get('longName', info.get('shortName', 'N/A')),
                'currentPrice': self._safe_get_numeric(info, 'currentPrice'),
                'previousClose': self._safe_get_numeric(info, 'previousClose'),
                'currency': info.get('currency', 'USD'),
            }
            
            # Change % 계산
            if profile['currentPrice'] != 'N/A' and profile['previousClose'] != 'N/A':
                try:
                    change_pct = ((profile['currentPrice'] - profile['previousClose']) 
                                 / profile['previousClose']) * 100
                    profile['changePercent'] = round(change_pct, 2)
                except (TypeError, ZeroDivisionError):
                    profile['changePercent'] = 'N/A'
            else:
                profile['changePercent'] = 'N/A'
            
            return profile
            
        except Exception as e:
            print(f"Error in get_profile: {e}")
            return self._empty_profile()
    
    def get_financials(self) -> Dict[str, Any]:
        """
        재무제표 데이터 및 파생 지표 계산 (최근 3년 연간 + 쿼터별)
        
        Returns:
            Dict containing:
            - raw_data: 
                - annual: income_stmt, balance_sheet, cashflow (DataFrame)
                - quarterly: income_stmt, balance_sheet, cashflow (DataFrame)
            - derived_metrics: 5가지 파생 지표
        """
        try:
            # 원본 재무제표 데이터 수집 (연간)
            income_stmt = self.ticker.income_stmt
            balance_sheet = self.ticker.balance_sheet
            cashflow = self.ticker.cashflow
            
            # 쿼터별 재무제표 데이터 수집
            quarterly_income_stmt = self.ticker.quarterly_income_stmt
            quarterly_balance_sheet = self.ticker.quarterly_balance_sheet
            quarterly_cashflow = self.ticker.quarterly_cashflow
            
            # 데이터 유효성 검사
            if (income_stmt is None or income_stmt.empty or 
                balance_sheet is None or balance_sheet.empty or 
                cashflow is None or cashflow.empty):
                return self._empty_financials()
            
            # 최근 3년 데이터만 추출 (열이 날짜이므로)
            income_stmt_3yr = income_stmt.iloc[:, :3] if income_stmt.shape[1] >= 3 else income_stmt
            balance_sheet_3yr = balance_sheet.iloc[:, :3] if balance_sheet.shape[1] >= 3 else balance_sheet
            cashflow_3yr = cashflow.iloc[:, :3] if cashflow.shape[1] >= 3 else cashflow
            
            # Transpose하여 날짜를 행(Index)으로 변환 (시계열 분석 용이)
            income_stmt_transposed = income_stmt_3yr.T
            balance_sheet_transposed = balance_sheet_3yr.T
            cashflow_transposed = cashflow_3yr.T
            
            # 쿼터별 데이터 처리 (최근 12쿼터 = 3년)
            quarterly_income_transposed = pd.DataFrame()
            quarterly_balance_transposed = pd.DataFrame()
            quarterly_cashflow_transposed = pd.DataFrame()
            
            if quarterly_income_stmt is not None and not quarterly_income_stmt.empty:
                quarterly_income_12q = quarterly_income_stmt.iloc[:, :12] if quarterly_income_stmt.shape[1] >= 12 else quarterly_income_stmt
                quarterly_income_transposed = quarterly_income_12q.T
            
            if quarterly_balance_sheet is not None and not quarterly_balance_sheet.empty:
                quarterly_balance_12q = quarterly_balance_sheet.iloc[:, :12] if quarterly_balance_sheet.shape[1] >= 12 else quarterly_balance_sheet
                quarterly_balance_transposed = quarterly_balance_12q.T
            
            if quarterly_cashflow is not None and not quarterly_cashflow.empty:
                quarterly_cashflow_12q = quarterly_cashflow.iloc[:, :12] if quarterly_cashflow.shape[1] >= 12 else quarterly_cashflow
                quarterly_cashflow_transposed = quarterly_cashflow_12q.T
            
            # 파생 지표 계산 (연간 데이터 기준)
            derived_metrics = self._calculate_derived_metrics(
                income_stmt_transposed,
                balance_sheet_transposed,
                cashflow_transposed
            )
            
            return {
                'raw_data': {
                    'annual': {
                        'income_stmt': income_stmt_transposed,
                        'balance_sheet': balance_sheet_transposed,
                        'cashflow': cashflow_transposed
                    },
                    'quarterly': {
                        'income_stmt': quarterly_income_transposed,
                        'balance_sheet': quarterly_balance_transposed,
                        'cashflow': quarterly_cashflow_transposed
                    }
                },
                'derived_metrics': derived_metrics
            }
            
        except Exception as e:
            print(f"Error in get_financials: {e}")
            return self._empty_financials()
    
    def _calculate_derived_metrics(self, income_stmt: pd.DataFrame, 
                                   balance_sheet: pd.DataFrame, 
                                   cashflow: pd.DataFrame) -> Dict[str, Any]:
        """
        PRD에 명시된 5가지 파생 지표 계산
        
        1. Quality of Earnings: OCF / Net Income
        2. Activity (Turnover): Receivables Turnover, Inventory Turnover
        3. Stability: Interest Coverage Ratio
        4. Growth/Capex: CapEx Growth
        5. Shareholder Return: Net Buyback Yield
        """
        metrics = {}
        
        # 1. Quality of Earnings: OCF / Net Income
        metrics['quality_of_earnings'] = self._calculate_quality_of_earnings(
            cashflow, income_stmt
        )
        
        # 2. Activity (Turnover)
        metrics['receivables_turnover'] = self._calculate_receivables_turnover(
            income_stmt, balance_sheet
        )
        metrics['inventory_turnover'] = self._calculate_inventory_turnover(
            income_stmt, balance_sheet
        )
        
        # 3. Stability: Interest Coverage Ratio
        metrics['interest_coverage'] = self._calculate_interest_coverage(income_stmt)
        
        # 4. Growth/Capex: CapEx Growth
        metrics['capex_growth'] = self._calculate_capex_growth(cashflow)
        
        # 5. Shareholder Return: Net Buyback Yield
        metrics['net_buyback_yield'] = self._calculate_net_buyback_yield(
            cashflow, balance_sheet
        )
        
        return metrics
    
    def _calculate_quality_of_earnings(self, cashflow: pd.DataFrame, 
                                       income_stmt: pd.DataFrame) -> Dict[str, Any]:
        """OCF / Net Income 계산"""
        try:
            # 최신 연도 데이터 (첫 번째 행)
            latest_year = cashflow.index[0] if len(cashflow) > 0 else None
            
            if latest_year is None:
                return {'latest': 'N/A', 'trend': 'N/A', 'warning': False}
            
            # Operating Cash Flow 찾기 (다양한 키 이름 대응)
            ocf_keys = ['Operating Cash Flow', 'Total Cash From Operating Activities', 
                       'OperatingCashFlow', 'Cash from Operating Activities']
            ocf = None
            for key in ocf_keys:
                if key in cashflow.columns:
                    ocf = cashflow.loc[latest_year, key]
                    break
            
            # Net Income 찾기
            ni_keys = ['Net Income', 'NetIncome', 'Net Income Common Stockholders']
            net_income = None
            for key in ni_keys:
                if key in income_stmt.columns:
                    net_income = income_stmt.loc[latest_year, key]
                    break
            
            if ocf is None or net_income is None:
                return {'latest': 'N/A', 'trend': 'N/A', 'warning': False}
            
            # NaN 또는 0 체크
            if pd.isna(ocf) or pd.isna(net_income) or net_income == 0:
                return {'latest': 'N/A', 'trend': 'N/A', 'warning': False}
            
            ratio = ocf / net_income
            warning = ratio < 1.0  # 1.0 미만 시 Warning
            
            # 추세 계산 (3년 데이터가 있는 경우)
            trend = 'N/A'
            if len(cashflow) >= 2 and len(income_stmt) >= 2:
                try:
                    prev_year = cashflow.index[1]
                    prev_ocf = None
                    prev_ni = None
                    
                    for key in ocf_keys:
                        if key in cashflow.columns:
                            prev_ocf = cashflow.loc[prev_year, key]
                            break
                    for key in ni_keys:
                        if key in income_stmt.columns:
                            prev_ni = income_stmt.loc[prev_year, key]
                            break
                    
                    if (prev_ocf is not None and prev_ni is not None and 
                        not pd.isna(prev_ocf) and not pd.isna(prev_ni) and prev_ni != 0):
                        prev_ratio = prev_ocf / prev_ni
                        if ratio > prev_ratio:
                            trend = 'Improving'
                        elif ratio < prev_ratio:
                            trend = 'Declining'
                        else:
                            trend = 'Stable'
                except:
                    pass
            
            return {
                'latest': round(ratio, 2),
                'trend': trend,
                'warning': warning
            }
            
        except Exception as e:
            print(f"Error calculating quality of earnings: {e}")
            return {'latest': 'N/A', 'trend': 'N/A', 'warning': False}
    
    def _calculate_receivables_turnover(self, income_stmt: pd.DataFrame, 
                                       balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Receivables Turnover = Revenue / Receivables"""
        try:
            latest_year = income_stmt.index[0] if len(income_stmt) > 0 else None
            if latest_year is None:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            # Revenue 찾기
            revenue_keys = ['Total Revenue', 'Revenue', 'Revenues', 'Net Sales']
            revenue = None
            for key in revenue_keys:
                if key in income_stmt.columns:
                    revenue = income_stmt.loc[latest_year, key]
                    break
            
            # Receivables 찾기
            receivables_keys = ['Receivables', 'Accounts Receivable', 
                              'Net Receivables', 'AccountsReceivable']
            receivables = None
            for key in receivables_keys:
                if key in balance_sheet.columns:
                    receivables = balance_sheet.loc[latest_year, key]
                    break
            
            if revenue is None or receivables is None:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            if pd.isna(revenue) or pd.isna(receivables) or receivables == 0:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            turnover = revenue / receivables
            
            # 추세 계산
            trend = 'N/A'
            if len(income_stmt) >= 2 and len(balance_sheet) >= 2:
                try:
                    prev_year = income_stmt.index[1]
                    prev_revenue = None
                    prev_receivables = None
                    
                    for key in revenue_keys:
                        if key in income_stmt.columns:
                            prev_revenue = income_stmt.loc[prev_year, key]
                            break
                    for key in receivables_keys:
                        if key in balance_sheet.columns:
                            prev_receivables = balance_sheet.loc[prev_year, key]
                            break
                    
                    if (prev_revenue is not None and prev_receivables is not None and
                        not pd.isna(prev_revenue) and not pd.isna(prev_receivables) and 
                        prev_receivables != 0):
                        prev_turnover = prev_revenue / prev_receivables
                        if turnover > prev_turnover:
                            trend = 'Improving'
                        elif turnover < prev_turnover:
                            trend = 'Declining'
                        else:
                            trend = 'Stable'
                except:
                    pass
            
            return {
                'latest': round(turnover, 2),
                'trend': trend
            }
            
        except Exception as e:
            print(f"Error calculating receivables turnover: {e}")
            return {'latest': 'N/A', 'trend': 'N/A'}
    
    def _calculate_inventory_turnover(self, income_stmt: pd.DataFrame, 
                                      balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Inventory Turnover = COGS / Inventory"""
        try:
            latest_year = income_stmt.index[0] if len(income_stmt) > 0 else None
            if latest_year is None:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            # COGS 찾기
            cogs_keys = ['Cost Of Goods Sold', 'Cost of Revenue', 'COGS', 
                        'CostOfGoodsSold', 'Cost of Goods Sold']
            cogs = None
            for key in cogs_keys:
                if key in income_stmt.columns:
                    cogs = income_stmt.loc[latest_year, key]
                    break
            
            # Inventory 찾기
            inventory_keys = ['Inventory', 'Inventories', 'Total Inventory']
            inventory = None
            for key in inventory_keys:
                if key in balance_sheet.columns:
                    inventory = balance_sheet.loc[latest_year, key]
                    break
            
            if cogs is None or inventory is None:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            if pd.isna(cogs) or pd.isna(inventory) or inventory == 0:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            turnover = cogs / inventory
            
            # 추세 계산
            trend = 'N/A'
            if len(income_stmt) >= 2 and len(balance_sheet) >= 2:
                try:
                    prev_year = income_stmt.index[1]
                    prev_cogs = None
                    prev_inventory = None
                    
                    for key in cogs_keys:
                        if key in income_stmt.columns:
                            prev_cogs = income_stmt.loc[prev_year, key]
                            break
                    for key in inventory_keys:
                        if key in balance_sheet.columns:
                            prev_inventory = balance_sheet.loc[prev_year, key]
                            break
                    
                    if (prev_cogs is not None and prev_inventory is not None and
                        not pd.isna(prev_cogs) and not pd.isna(prev_inventory) and 
                        prev_inventory != 0):
                        prev_turnover = prev_cogs / prev_inventory
                        if turnover > prev_turnover:
                            trend = 'Improving'
                        elif turnover < prev_turnover:
                            trend = 'Declining'
                        else:
                            trend = 'Stable'
                except:
                    pass
            
            return {
                'latest': round(turnover, 2),
                'trend': trend
            }
            
        except Exception as e:
            print(f"Error calculating inventory turnover: {e}")
            return {'latest': 'N/A', 'trend': 'N/A'}
    
    def _calculate_interest_coverage(self, income_stmt: pd.DataFrame) -> Dict[str, Any]:
        """Interest Coverage Ratio = EBIT / Interest Expense"""
        try:
            latest_year = income_stmt.index[0] if len(income_stmt) > 0 else None
            if latest_year is None:
                return {'latest': 'N/A', 'status': 'N/A'}
            
            # EBIT 찾기
            ebit_keys = ['EBIT', 'Earnings Before Interest And Taxes', 
                        'Operating Income', 'Income Before Tax']
            ebit = None
            for key in ebit_keys:
                if key in income_stmt.columns:
                    ebit = income_stmt.loc[latest_year, key]
                    break
            
            # Interest Expense 찾기
            interest_keys = ['Interest Expense', 'InterestExpense', 
                           'Total Interest Expense', 'Interest And Debt Expense']
            interest_expense = None
            for key in interest_keys:
                if key in income_stmt.columns:
                    interest_expense = income_stmt.loc[latest_year, key]
                    break
            
            if ebit is None or interest_expense is None:
                return {'latest': 'N/A', 'status': 'N/A'}
            
            if pd.isna(ebit) or pd.isna(interest_expense) or interest_expense == 0:
                return {'latest': 'N/A', 'status': 'N/A'}
            
            ratio = ebit / abs(interest_expense)  # Interest Expense는 음수일 수 있음
            
            # 상태 판단 (5.0 이상이면 안정적)
            status = 'Strong' if ratio >= 5.0 else 'Weak' if ratio >= 1.0 else 'Critical'
            
            return {
                'latest': round(ratio, 2),
                'status': status
            }
            
        except Exception as e:
            print(f"Error calculating interest coverage: {e}")
            return {'latest': 'N/A', 'status': 'N/A'}
    
    def _calculate_capex_growth(self, cashflow: pd.DataFrame) -> Dict[str, Any]:
        """CapEx Growth 계산 (연간 성장률)"""
        try:
            if len(cashflow) < 2:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            # Capital Expenditure 찾기
            capex_keys = ['Capital Expenditure', 'CapitalExpenditure', 
                         'Capital Expenditures', 'Purchase Of Property Plant And Equipment']
            capex_latest = None
            capex_prev = None
            
            latest_year = cashflow.index[0]
            prev_year = cashflow.index[1]
            
            for key in capex_keys:
                if key in cashflow.columns:
                    capex_latest = cashflow.loc[latest_year, key]
                    capex_prev = cashflow.loc[prev_year, key]
                    break
            
            if capex_latest is None or capex_prev is None:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            if pd.isna(capex_latest) or pd.isna(capex_prev) or capex_prev == 0:
                return {'latest': 'N/A', 'trend': 'N/A'}
            
            # CapEx는 일반적으로 음수로 표시됨 (지출이므로)
            capex_latest = abs(capex_latest)
            capex_prev = abs(capex_prev)
            
            growth_rate = ((capex_latest - capex_prev) / capex_prev) * 100
            
            trend = 'Expanding' if growth_rate > 0 else 'Contracting' if growth_rate < 0 else 'Stable'
            
            return {
                'latest': round(growth_rate, 2),
                'trend': trend
            }
            
        except Exception as e:
            print(f"Error calculating capex growth: {e}")
            return {'latest': 'N/A', 'trend': 'N/A'}
    
    def _calculate_net_buyback_yield(self, cashflow: pd.DataFrame, 
                                     balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Net Buyback Yield = (Repurchase - Issuance) / Market Cap"""
        try:
            latest_year = cashflow.index[0] if len(cashflow) > 0 else None
            if latest_year is None:
                return {'latest': 'N/A', 'status': 'N/A'}
            
            # Stock Repurchase 찾기
            repurchase_keys = ['Purchase Of Common Stock', 'Common Stock Repurchased', 
                             'Repurchase Of Common Stock', 'Stock Repurchase']
            repurchase = None
            for key in repurchase_keys:
                if key in cashflow.columns:
                    repurchase = cashflow.loc[latest_year, key]
                    break
            
            # Stock Issuance 찾기
            issuance_keys = ['Sale Of Common Stock', 'Common Stock Issued', 
                           'Issuance Of Common Stock']
            issuance = None
            for key in issuance_keys:
                if key in cashflow.columns:
                    issuance = cashflow.loc[latest_year, key]
                    break
            
            # Market Cap은 profile에서 가져와야 하지만, 여기서는 간단히 처리
            # 실제로는 get_profile()에서 가져온 marketCap을 사용하는 것이 좋음
            net_buyback = 0
            if repurchase is not None and not pd.isna(repurchase):
                net_buyback += abs(repurchase)  # Repurchase는 음수일 수 있음
            if issuance is not None and not pd.isna(issuance):
                net_buyback -= abs(issuance)  # Issuance는 양수일 수 있음
            
            # Market Cap 가져오기
            try:
                info = self.ticker.info
                market_cap = info.get('marketCap', None)
                
                if market_cap is None or pd.isna(market_cap) or market_cap == 0:
                    return {'latest': 'N/A', 'status': 'N/A'}
                
                yield_pct = (net_buyback / market_cap) * 100
                status = 'Positive' if net_buyback > 0 else 'Negative' if net_buyback < 0 else 'Neutral'
                
                return {
                    'latest': round(yield_pct, 4),  # 소수점 4자리 (퍼센트)
                    'status': status
                }
            except:
                return {'latest': 'N/A', 'status': 'N/A'}
            
        except Exception as e:
            print(f"Error calculating net buyback yield: {e}")
            return {'latest': 'N/A', 'status': 'N/A'}
    
    def get_technicals(self) -> Dict[str, Any]:
        """
        기술적 지표 계산
        
        Returns:
            Dict containing: RSI, TRIX, MA lines, Volume ratio, Earnings D-Day
        """
        try:
            # 주가 데이터 수집 (최소 1년, 기술적 지표 계산을 위해 충분한 기간 필요)
            hist = self.ticker.history(period="1y", interval="1d")
            
            if hist.empty:
                return {
                    'error': 'No price data available',
                    'price_data': None
                }
            
            # 기술적 지표 계산
            if USE_PANDAS_TA:
                # RSI(14)
                hist['RSI'] = ta.rsi(hist['Close'], length=14)
                
                # TRIX(30) - 추세 전환 시그널
                trix_df = ta.trix(hist['Close'], length=30)
                if not trix_df.empty:
                    hist['TRIX'] = trix_df.iloc[:, 0] if len(trix_df.columns) > 0 else None
                    hist['TRIX_Signal'] = trix_df.iloc[:, 1] if len(trix_df.columns) > 1 else None
                
                # 이동평균선
                hist['MA_20'] = ta.sma(hist['Close'], length=20)
                hist['MA_60'] = ta.sma(hist['Close'], length=60)
                hist['MA_120'] = ta.sma(hist['Close'], length=120)
            else:
                # pandas-ta 없이 직접 계산
                # RSI(14) 계산
                hist['RSI'] = self._calculate_rsi(hist['Close'], period=14)
                
                # TRIX(30) 계산
                trix_result = self._calculate_trix(hist['Close'], period=30)
                hist['TRIX'] = trix_result['trix']
                hist['TRIX_Signal'] = trix_result['signal']
                
                # 이동평균선 (SMA)
                hist['MA_20'] = hist['Close'].rolling(window=20, min_periods=1).mean()
                hist['MA_60'] = hist['Close'].rolling(window=60, min_periods=1).mean()
                hist['MA_120'] = hist['Close'].rolling(window=120, min_periods=1).mean()
            
            # 거래량 비율 (20일 평균 대비 현재 거래량)
            hist['Volume_MA20'] = hist['Volume'].rolling(window=20, min_periods=1).mean()
            hist['Volume_Ratio'] = hist['Volume'] / hist['Volume_MA20']
            
            # 현재 값 추출 (최신 데이터)
            current_rsi = self._safe_get_latest(hist['RSI'])
            current_trix = self._safe_get_latest(hist['TRIX']) if 'TRIX' in hist.columns else 'N/A'
            current_trix_signal = self._safe_get_latest(hist['TRIX_Signal']) if 'TRIX_Signal' in hist.columns else 'N/A'
            
            ma_data = {
                'MA_20': self._safe_get_latest(hist['MA_20']),
                'MA_60': self._safe_get_latest(hist['MA_60']),
                'MA_120': self._safe_get_latest(hist['MA_120'])
            }
            
            volume_ratio = self._safe_get_latest(hist['Volume_Ratio'])
            
            # Earnings D-Day 계산
            earnings_info = self._get_earnings_d_day()
            
            return {
                'price_data': hist,
                'current_rsi': current_rsi,
                'current_trix': current_trix,
                'current_trix_signal': current_trix_signal,
                'ma_data': ma_data,
                'volume_ratio': volume_ratio,
                'earnings_date': earnings_info.get('date'),
                'earnings_d_day': earnings_info.get('d_day')
            }
            
        except Exception as e:
            print(f"Error in get_technicals: {e}")
            return {
                'error': str(e),
                'price_data': None
            }
    
    def _get_earnings_d_day(self) -> Dict[str, Any]:
        """다음 실적 발표일까지 남은 일수 계산"""
        try:
            calendar = self.ticker.calendar
            
            # calendar가 None이거나 빈 dict인 경우
            if calendar is None:
                return {'date': None, 'd_day': None}
            
            earnings_date = None
            
            # calendar가 dict 형태인 경우
            if isinstance(calendar, dict):
                # 'Earnings Date' 키가 있는 경우
                if 'Earnings Date' in calendar:
                    earnings_date_raw = calendar['Earnings Date']
                    # Earnings Date가 리스트인 경우 (예: [datetime.date(2026, 2, 5)])
                    if isinstance(earnings_date_raw, list) and len(earnings_date_raw) > 0:
                        earnings_date = earnings_date_raw[0]  # 첫 번째 날짜 사용
                    else:
                        earnings_date = earnings_date_raw
                # 다른 키들을 확인
                elif len(calendar) > 0:
                    # 첫 번째 값을 시도
                    first_key = list(calendar.keys())[0]
                    earnings_date = calendar[first_key]
            # calendar가 DataFrame인 경우
            elif isinstance(calendar, pd.DataFrame):
                if calendar.empty:
                    return {'date': None, 'd_day': None}
                # 'Earnings Date' 컬럼이 있는 경우
                if 'Earnings Date' in calendar.columns:
                    earnings_date = calendar['Earnings Date'].iloc[0]
                # 첫 번째 행의 첫 번째 값이 날짜인 경우
                elif len(calendar) > 0 and len(calendar.columns) > 0:
                    first_value = calendar.iloc[0, 0]
                    earnings_date = first_value
            
            if earnings_date is None:
                return {'date': None, 'd_day': None}
            
            # D-Day 계산
            today = pd.Timestamp.now()
            
            # datetime.date를 pd.Timestamp로 변환
            if isinstance(earnings_date, date):
                earnings_date = pd.Timestamp(earnings_date)
            elif isinstance(earnings_date, str):
                try:
                    earnings_date = pd.Timestamp(earnings_date)
                except:
                    return {'date': None, 'd_day': None}
            elif not isinstance(earnings_date, pd.Timestamp):
                try:
                    earnings_date = pd.Timestamp(earnings_date)
                except:
                    return {'date': None, 'd_day': None}
            
            d_day = (earnings_date - today).days
            
            return {
                'date': earnings_date.strftime('%Y-%m-%d') if isinstance(earnings_date, pd.Timestamp) else str(earnings_date),
                'd_day': d_day
            }
            
        except Exception as e:
            print(f"Error getting earnings D-Day: {e}")
            import traceback
            traceback.print_exc()
            return {'date': None, 'd_day': None}
    
    def get_news_context(self) -> Dict[str, Any]:
        """
        뉴스 컨텍스트 수집 (최신 뉴스 + 과거 변동성 높은 날짜의 뉴스)
        
        Returns:
            Dict containing:
            - recent_news: 최신 10개 뉴스 리스트
            - historical_events: 과거 변동성 높은 날짜별 뉴스 검색 결과
        """
        try:
            # 1. Recent News: 최신 10개 뉴스
            recent_news = self._get_recent_news()
            
            # 2. Historical Context: 변동성 높은 날짜의 뉴스 검색
            historical_events = self._get_historical_news_context()
            
            return {
                'recent_news': recent_news,
                'historical_events': historical_events
            }
            
        except Exception as e:
            print(f"Error in get_news_context: {e}")
            return {
                'recent_news': [],
                'historical_events': []
            }
    
    def _get_recent_news(self) -> list:
        """최신 10개 뉴스 수집"""
        try:
            news_list = self.ticker.news
            
            if not news_list or len(news_list) == 0:
                return []
            
            # 최신 10개만 추출
            recent_news = []
            for item in news_list[:10]:
                try:
                    # yfinance news 구조: item['content'] 안에 실제 뉴스 정보가 있음
                    content = item.get('content', {})
                    
                    title = content.get('title', 'N/A')
                    pub_date = content.get('pubDate', 'N/A')
                    provider = content.get('provider', {})
                    publisher_name = provider.get('displayName', 'N/A') if isinstance(provider, dict) else 'N/A'
                    
                    # URL 추출
                    canonical_url = content.get('canonicalUrl', {})
                    link = canonical_url.get('url', 'N/A') if isinstance(canonical_url, dict) else 'N/A'
                    
                    # Summary 추출
                    summary = content.get('summary', 'N/A')
                    
                    news_item = {
                        'title': title,
                        'link': link,
                        'publisher': publisher_name,
                        'publishTime': pub_date,
                        'summary': summary
                    }
                    
                    # publishTime을 읽기 쉬운 형식으로 변환 (ISO 형식인 경우)
                    if news_item['publishTime'] != 'N/A':
                        try:
                            # ISO 형식 문자열을 파싱
                            if 'T' in str(news_item['publishTime']):
                                dt = datetime.fromisoformat(str(news_item['publishTime']).replace('Z', '+00:00'))
                                news_item['publishTime'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    
                    recent_news.append(news_item)
                except Exception as e:
                    print(f"Error processing news item: {e}")
                    continue
            
            return recent_news
            
        except Exception as e:
            print(f"Error getting recent news: {e}")
            return []
    
    def _get_historical_news_context(self) -> list:
        """
        과거 변동성 높은 날짜 추출 (뉴스 검색 없이 날짜와 변동률만)
        
        최근 1년 내 주가 변동폭(Change %) 상위 5일을 추출하여 반환
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
            
            # 4. 날짜와 변동률만 추출
            for date, row in top_5_volatile.iterrows():
                date_str = date.strftime('%Y-%m-%d') if isinstance(date, pd.Timestamp) else str(date)
                change_pct = round(row['Change%'], 2)
                
                historical_events.append({
                    'date': date_str,
                    'change_pct': change_pct,
                    'close_price': round(row['Close'], 2),
                    'volume': int(row['Volume']) if not pd.isna(row['Volume']) else 'N/A'
                })
            
            return historical_events
            
        except Exception as e:
            print(f"Error getting historical news context: {e}")
            return []
    
    def _get_company_name(self) -> str:
        """회사명 가져오기 (검색 쿼리 개선을 위해)"""
        try:
            info = self.ticker.info
            if info:
                # longName 또는 shortName 사용
                company_name = info.get('longName') or info.get('shortName') or 'N/A'
                return company_name
            return 'N/A'
        except:
            return 'N/A'
    
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
            
            # 3. 티커나 회사명이 포함되어 있는지 확인
            has_ticker = ticker_upper in title.upper() or ticker_upper in body.upper()
            has_company = company_upper and (company_upper in title.upper() or company_upper in body.upper())
            
            # 4. 관련성 점수 계산
            relevance_score = self._calculate_relevance_score(
                title, body, href, ticker_upper, company_upper
            )
            
            # 티커나 회사명이 있으면 추가 점수 부여
            if has_ticker:
                relevance_score += 5  # 티커 포함은 높은 가중치
            if has_company:
                relevance_score += 3  # 회사명 포함은 중간 가중치
            
            # 관련성 점수가 6 이상인 결과만 선택
            # 티커/회사명이 있으면 우선, 없어도 금융 사이트에서 주식 관련 키워드가 있으면 허용
            is_finance_site = any(site in href.lower() for site in ['yahoo.com', 'bloomberg.com', 'reuters.com', 'cnbc.com', 
                                                                    'wsj.com', 'marketwatch.com', 'ft.com', 'forbes.com',
                                                                    'seekingalpha.com', 'benzinga.com', 'thestreet.com', 
                                                                    'investing.com', 'fool.com'])
            has_stock_keyword = any(kw in (title + ' ' + body).upper() for kw in ['STOCK', 'SHARE', 'PRICE', 'EARNINGS', 'REVENUE', 'FINANCIAL', 'TRADING', 'MARKET'])
            
            # 티커나 회사명이 있으면 기준 완화, 금융 사이트면 추가 허용
            if (has_ticker or has_company) and relevance_score >= 6:
                pass  # 통과
            elif is_finance_site and has_stock_keyword and relevance_score >= 7:
                pass  # 통과
            else:
                continue  # 필터링
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
        
        # 비영문 문자 패턴 확인 (스웨덴어, 독일어 등 특수문자 포함)
        non_english_patterns = ['å', 'ä', 'ö', 'Å', 'Ä', 'Ö', 'ü', 'Ü', 'é', 'É', 'ñ', 'Ñ', 'ç', 'Ç']
        if any(pattern in sample for pattern in non_english_patterns):
            # 스웨덴어 등 비영문 문자가 있으면 추가 검증
            # 하지만 일부 금융 용어에는 포함될 수 있으므로 완전히 제외하지는 않음
            pass
        
        # 영문 문자 비율 계산
        english_chars = sum(1 for c in sample if c.isascii() and (c.isalpha() or c.isspace() or c in '.,;:!?\'"-()'))
        total_chars = len([c for c in sample if c.isalnum() or c.isspace() or c in '.,;:!?\'"-()'])
        
        if total_chars == 0:
            return False
        
        # 영문 비율이 90% 이상이면 영문으로 간주 (기준 상향: 85% -> 90%)
        english_ratio = english_chars / total_chars if total_chars > 0 else 0
        
        # URL에 비영문 도메인이 있으면 제외
        if 'svenskafans.com' in text.lower() or 'zhihu.com' in text.lower():
            return False
        
        return english_ratio >= 0.90
    
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
    
    # Helper Methods
    def _safe_get_numeric(self, info: Dict, key: str) -> Any:
        """안전하게 숫자 값 가져오기"""
        try:
            value = info.get(key)
            if value is None or pd.isna(value):
                return 'N/A'
            return float(value) if isinstance(value, (int, float)) else value
        except:
            return 'N/A'
    
    def _safe_get_latest(self, series: pd.Series) -> Any:
        """시리즈의 최신 값 안전하게 가져오기"""
        try:
            if series.empty:
                return 'N/A'
            latest = series.iloc[-1]
            if pd.isna(latest):
                return 'N/A'
            return round(float(latest), 2) if isinstance(latest, (int, float)) else latest
        except:
            return 'N/A'
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI(Relative Strength Index) 직접 계산"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([np.nan] * len(prices), index=prices.index)
    
    def _calculate_trix(self, prices: pd.Series, period: int = 30) -> Dict[str, pd.Series]:
        """TRIX(Triple Exponential Average) 직접 계산"""
        try:
            # EMA 계산 함수
            def ema(series, period):
                return series.ewm(span=period, adjust=False).mean()
            
            # Triple EMA
            ema1 = ema(prices, period)
            ema2 = ema(ema1, period)
            ema3 = ema(ema2, period)
            
            # TRIX = (EMA3 - 이전 EMA3) / 이전 EMA3 * 100
            trix = ((ema3 - ema3.shift(1)) / ema3.shift(1)) * 100
            
            # Signal = TRIX의 EMA (일반적으로 9일)
            signal = ema(trix, 9)
            
            return {
                'trix': trix,
                'signal': signal
            }
        except:
            empty_series = pd.Series([np.nan] * len(prices), index=prices.index)
            return {
                'trix': empty_series,
                'signal': empty_series
            }
    
    def _empty_profile(self) -> Dict[str, Any]:
        """빈 프로필 반환"""
        return {
            'ticker': self.ticker_symbol,
            'sector': 'N/A',
            'industry': 'N/A',
            'country': 'N/A',
            'marketCap': 'N/A',
            'beta': 'N/A',
            'longName': 'N/A',
            'currentPrice': 'N/A',
            'previousClose': 'N/A',
            'changePercent': 'N/A',
            'currency': 'USD'
        }
    
    def _empty_financials(self) -> Dict[str, Any]:
        """빈 재무 데이터 반환"""
        return {
            'raw_data': {
                'annual': {
                    'income_stmt': pd.DataFrame(),
                    'balance_sheet': pd.DataFrame(),
                    'cashflow': pd.DataFrame()
                },
                'quarterly': {
                    'income_stmt': pd.DataFrame(),
                    'balance_sheet': pd.DataFrame(),
                    'cashflow': pd.DataFrame()
                }
            },
            'derived_metrics': {
                'quality_of_earnings': {'latest': 'N/A', 'trend': 'N/A', 'warning': False},
                'receivables_turnover': {'latest': 'N/A', 'trend': 'N/A'},
                'inventory_turnover': {'latest': 'N/A', 'trend': 'N/A'},
                'interest_coverage': {'latest': 'N/A', 'status': 'N/A'},
                'capex_growth': {'latest': 'N/A', 'trend': 'N/A'},
                'net_buyback_yield': {'latest': 'N/A', 'status': 'N/A'}
            }
        }
