# GO/STOP 판단층 공식 규격

## 1. Purpose
- 수동 주문 직전에 신호·포트폴리오·주문표가 서로 정합인지 확인하고 실행 여부를 한 줄로 결정하기 위해 필요하다.
- 잘못된 날짜/불일치/누락을 사전에 차단해 운영 실수를 줄인다.
- 운영자가 빠르게 “오늘 실행해도 되는지” 판단할 수 있게 한다.

## 2. Required Inputs
- `backtests\kis_shadow_ops_summary.csv`: 시스템 건강/일일 체크 결과 요약.
- `backtests\kis_shadow_health.csv`: 데이터·리드니스 최신성 상태.
- `backtests\kis_shadow_portfolio.csv`: 오늘 기준 포트폴리오 구성.
- `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv` 또는 `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`: 실제 수동 주문표.
- `docs\etf_riskbudget_micro_live_runbook.md`: 실행 절차 정의(버전/경로/우선순위).

## 3. Decision Rules
**GO 조건**
1) 모든 입력 파일이 존재하고 읽을 수 있다.
2) `kis_shadow_health`에서 `SourceFresh=1` AND `ReadinessFresh=1`.
3) `kis_shadow_ops_summary`에서 `DailyCheckStatus=GO` AND `HealthStatus=OK`.
4) `kis_shadow_portfolio`의 기준일이 주문표의 `TradeDate`와 일치한다.
5) 주문표의 총 비중/수량이 포트폴리오와 정합(종목/ETF 코드 및 비중 범위 허용오차 내).
6) 런북에 명시된 주문표 유형(초기/리밸런스)과 실제 주문표 파일이 일치한다.

**STOP 조건**
7) 입력 파일 하나라도 누락/읽기 실패.
8) 건강/리드니스 상태가 비정상(`SourceFresh=0` 또는 `ReadinessFresh=0` 또는 `HealthStatus!=OK`).
9) `DailyCheckStatus!=GO`.
10) 포트폴리오 기준일과 주문표 `TradeDate` 불일치.
11) 주문표와 포트폴리오 종목/ETF 코드 불일치 또는 비중 합계가 허용오차 초과.

**판단 불가 조건**
12) 위 판단을 위해 필요한 필드가 누락되었거나 의미가 불명확한 경우.

## 4. Output Fields
- `Decision` (GO/STOP/판단 불가)
- `DecisionDate`
- `PortfolioAsOfDate`
- `OrderSheetTradeDate`
- `HealthStatus`
- `DailyCheckStatus`
- `SourceFresh` / `ReadinessFresh`
- `PortfolioFile`
- `OrderSheetFile`
- `RunbookVersion`
- `MismatchSummary`
- `BlockingReason`

## 5. Failure Cases
- 주문표 TradeDate가 오늘/포트폴리오와 어긋남.
- 포트폴리오 구성과 주문표 종목 불일치.
- 건강 체크 OK인데 실제 리드니스 파일이 오래된 값.
- 런북에서 요구한 주문표 유형과 실제 파일이 다름.
- 비중 합계가 1.0에서 크게 벗어남.

## 6. What This Layer Must Not Do
- 신호 계산/수정
- 포트폴리오 변경
- 주문표 생성/수정
- 체결 기록 생성
- 수동 주문 대신 실행
- 리밸런스 규칙 변경
- 수수료/슬리피지 재계산
- 미국/뉴스 트랙 결합

## 7. Single First Implementation Target
- `GO_STOP_report_spec.md` (GO/STOP 판단 규칙과 입력 정합성 기준을 명문화한 단일 문서)