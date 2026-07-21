# Split Models Trade And Data Audit

## Purpose

- 오늘 무엇을 만들었는지 한 장으로 정리한다
- 앞으로는 대표 모델별 실제 매매 종목을 같이 본다
- 백테스트 주가 데이터가 어디서 왔고 파일 상태가 어떤지도 같이 본다

## Scope

- strongest와 current-truth near-miss 축의 최신 보유 종목
- 직전 리밸런스 대비 entered / exited 종목
- strongest 최신 보유 종목 일부의 가격 파일 경로와 기본 무결성 체크

## Why this matters

- 지금까지는 성과 숫자와 기여 종목 해석이 중심이었다
- 하지만 실제로 어떤 종목을 들고 있었는지까지 같이 봐야 신뢰가 생긴다
- 주가 데이터도 외부 API 실시간 조회가 아니라 로컬 cached csv.gz이므로 파일 단위 검증이 가능해야 한다

## Output

- 대표 모델별 latest holdings
- entered / exited symbols
- price file exists / row count / date range / nonpositive close / duplicate date check

## Verdict

- 앞으로 review는 숫자 + 실제 보유 종목 + 데이터 파일 audit를 같이 보는 형태로 가는 게 맞다
