# Two-Axis AI Trading Pipeline (Community Edition)

*[한국어는 아래에 있습니다 / Korean version below](#한국어)*

An open-source, bring-your-own-API-keys automated trading pipeline. Data collection, model development, target-portfolio construction, execution, and account reconciliation — you run it on your own machine with your own broker credentials, and you keep 100% control of your own capital. Nobody pools funds, nobody manages anyone else's money.

Currently wired for **Bithumb** (crypto spot) and **KIS / Korea Investment Securities** (Korean & US stocks/ETFs). Contributions for other brokers (Kiwoom, Toss Securities, etc.) are very welcome — see "Adding a new broker" below.

## What this is / isn't

- ✅ Research and engineering reference for building your own automated trading system
- ✅ A place to share and discuss model/strategy ideas with other builders
- ❌ Not a signal service, not investment advice, not a managed fund
- ❌ Nobody here recommends specific trades or manages capital on your behalf — you run your own instance, with your own keys, at your own risk

## Why this one, out of the many trading-bot repos out there

Most backtests that look great fall apart live because of a handful of repeat offenders: data leakage, survivorship bias, unrealistic cost assumptions, and plain overfitting. This pipeline doesn't just run a backtest and hand you the headline number — every candidate model has to survive out-of-sample testing, cost stress, and parameter-sensitivity checks before it's trusted, and the number that actually drives promotion decisions is discounted accordingly. Two real examples from this system's own model registry:

| Market | Raw backtest CAGR | After validation/evidence-adjustment |
|---|---|---|
| BTC (Keltner breakout) | ~102% | **+15.7%** (survived — promoted) |
| ETH (trend channel) | ~154% | **-11.5%** (didn't survive — rejected despite the flashy headline number) |

If a strategy's edge only exists in the raw, undiscounted number, this pipeline is built to catch that before it costs you real money.

## What Is Included

- `root/`: top-level orchestration, dashboard, account-engine, and model-factory scripts.
- `Crypto/`: Bithumb crypto execution/research source code and tests.
- `momentum/`: KIS stock/ETF research and API client source code without `.env` or token cache.
- `ops/`: broker gateway/control-plane source code only.
- `tests/`: top-level tests for the two-axis pipeline.
- `reports/model_factory/`: selected latest model-development report artifacts.
- `public_dashboard_export/`: sanitized dashboard export if present.

## What Is Not Included (and never will be)

- API keys, secrets, `.env`, token caches.
- Any account number/product code.
- Broker private credentials.
- Live runstate approval files.
- Real account snapshots.
- Live order ledgers and broker responses.
- Large raw market-data archives and generated backtest folders.

## Getting Started

1. Fork or clone this repo.
2. Create a Python virtual environment and run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` in your own **private, local, never-committed** checkout, and fill in *your own* broker API keys.
4. Run mock/dry-run tests first. Confirm the pipeline behaves the way you expect before touching a live account.
5. Do not enable live order submission until you've set up your own broker credentials and your own risk policy (position sizing, max drawdown kill-switch, etc.). That part is on you — nobody else is responsible for your capital.

### Live-order safety gate

The autotrade loops default to **dry-run**: they compute what they *would* trade and log that intent, but do not place real orders unless you explicitly pass `--submit`. Without that flag, nothing touches your live account regardless of what your `.env` contains.

There is also a kill switch: create an empty file at `ops/runstate/DISABLE_ALL_TRADING` and every loop will refuse to submit, no matter what flags you pass. Delete the file to re-enable.

Read and understand a loop's `--submit` path before you ever pass that flag with real credentials.

## Adding a new broker (Kiwoom, Toss, or anything else)

The Bithumb and KIS integrations live under `ops/` and `momentum/` — read through those as the reference pattern for how an adapter talks to the shared execution engine (auth, market data pull, order submission, account reconciliation). If you build a working adapter for another broker, a PR is welcome. Please make sure it follows the same rule as everything else here: no real credentials or account data ever committed, dry-run/mock path included, and clear docs on what it does and doesn't do.

## Sharing model ideas

Use the [Discussions tab](../../discussions) on this repo, or [r/TwoAxisTrading](https://www.reddit.com/r/TwoAxisTrading/) on Reddit, to talk strategy ideas, validation methodology, or what broke between backtest and live.

Ground rules: no "buy X now" calls, no promises of returns, back up claims with methodology (walk-forward, cost stress, sample size) — not just a screenshot of a nice equity curve.

## Suggested AI Prompt For A Colleague

```text
Read this repository as a sanitized two-axis trading pipeline.
Explain the BITHUMB_KRW and KIS_COMBINED_KRW architecture, then run only tests or dry-run/mock broker paths.
Do not submit live orders.
Do not ask for real credentials.
Identify the next safest improvements to model validation, idempotency, account reconciliation, and dashboard visibility.
```

## Safety Note

This repository is not financial advice and is not a ready-to-run live trading system. Nobody involved is a licensed investment adviser. Treat it as research and engineering reference material, and treat any capital you connect to it as capital you could lose entirely.

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, modify it, sell what you build on top of it. No warranty, no liability — see the license text for the full terms.

---

# 한국어

*[English version above](#two-axis-ai-trading-pipeline-community-edition)*

각자 자기 브로커 API 키를 등록해서 쓰는 오픈소스 자동매매 파이프라인입니다. 데이터 수집, 모델 개발, 타겟 포트폴리오 구성, 주문 실행, 계좌 정합성 체크까지 — 본인 컴퓨터에서 본인 브로커 자격증명으로 직접 돌리고, 본인 자산은 100% 본인이 통제합니다. 아무도 자금을 모으지 않고, 아무도 남의 돈을 대신 굴리지 않습니다.

현재 **Bithumb**(크립토 현물)과 **한국투자증권(KIS)**(국내/미국 주식·ETF)에 연동돼 있습니다. 키움, 토스 같은 다른 브로커 연동은 커뮤니티 기여로 환영합니다 — 아래 "새 브로커 추가하기" 참고.

## 이게 뭔지 / 뭐가 아닌지

- ✅ 본인만의 자동매매 시스템을 만들기 위한 리서치/엔지니어링 참고자료
- ✅ 다른 개발자들과 모델/전략 아이디어를 공유하고 토론하는 공간
- ❌ 시그널 서비스 아님, 투자자문 아님, 펀드 아님
- ❌ 여기 있는 누구도 특정 종목/코인을 추천하거나 남의 자산을 대신 운용하지 않습니다 — 본인 인스턴스를, 본인 키로, 본인 책임 하에 돌리는 겁니다

## 이미 많은 트레이딩봇 저장소 중에, 왜 이걸 써야 하나

백테스트가 좋아 보이다가 실전에서 무너지는 이유는 대체로 몇 가지로 정해져 있습니다: 데이터 누수, 생존편향, 비현실적인 비용 가정, 그리고 단순 과최적화. 이 파이프라인은 백테스트 돌려서 헤드라인 숫자만 던져주는 게 아니라, **모든 후보 모델이 아웃오브샘플 테스트, 비용 스트레스, 파라미터 민감도 검사를 통과해야만 신뢰**되고, 실제 승격 판단에 쓰이는 숫자는 그에 맞춰 할인됩니다. 이 시스템 자체의 모델 레지스트리에서 나온 실제 사례 두 개:

| 시장 | 원본 백테스트 CAGR | 검증/증거조정 후 |
|---|---|---|
| BTC (Keltner 브레이크아웃) | 약 102% | **+15.7%** (검증 통과 — 승격됨) |
| ETH (추세채널) | 약 154% | **-11.5%** (검증 실패 — 화려한 헤드라인 숫자에도 불구하고 탈락) |

전략의 엣지가 할인 안 된 원본 숫자에만 존재한다면, 이 파이프라인은 그걸 실제 돈 잃기 전에 잡아내도록 설계되어 있습니다.

## 포함된 것

- `root/`: 최상위 오케스트레이션, 대시보드, 계좌 엔진, 모델 팩토리 스크립트
- `Crypto/`: Bithumb 크립토 실행/리서치 소스코드 및 테스트
- `momentum/`: KIS 주식/ETF 리서치 및 API 클라이언트 소스코드 (`.env`나 토큰 캐시 제외)
- `ops/`: 브로커 게이트웨이/제어 플레인 소스코드만
- `tests/`: two-axis 파이프라인 최상위 테스트
- `reports/model_factory/`: 최신 모델 개발 리포트 산출물 일부
- `public_dashboard_export/`: 정제된 대시보드 export(있는 경우)

## 포함 안 된 것 (앞으로도 안 됨)

- API 키, 시크릿, `.env`, 토큰 캐시
- 모든 계좌번호/상품코드
- 브로커 개인 자격증명
- 실계좌 런스테이트 승인 파일
- 실제 계좌 스냅샷
- 실주문 원장 및 브로커 응답
- 대용량 원본 시세 데이터 아카이브 및 생성된 백테스트 폴더

## 시작하는 법

1. 이 저장소를 포크하거나 클론합니다.
2. Python 가상환경을 만들고 `pip install -r requirements.txt`를 실행합니다.
3. 본인의 **비공개, 로컬, 절대 커밋 안 되는** 환경에서 `.env.example`을 `.env`로 복사하고, *본인 소유의* 브로커 API 키를 입력합니다.
4. 먼저 모의/드라이런 테스트를 돌려서, 실계좌 건드리기 전에 파이프라인이 예상대로 작동하는지 확인합니다.
5. 본인 브로커 자격증명과 본인 리스크 정책(포지션 사이징, 최대낙폭 킬스위치 등)을 세팅하기 전에는 실주문 제출을 켜지 마세요. 이 부분은 전적으로 본인 책임입니다 — 아무도 본인 자산을 대신 책임져주지 않습니다.

### 실주문 안전장치

자동매매 루프는 기본값이 **드라이런**입니다: 어떤 매매를 했을지 계산해서 의도만 기록하고, `--submit`을 명시적으로 넘기지 않으면 실제 주문은 내지 않습니다. 이 플래그 없이는 `.env`에 뭐가 들어있든 실계좌에 아무 영향 없습니다.

킬스위치도 있습니다: `ops/runstate/DISABLE_ALL_TRADING`이라는 빈 파일을 만들면, 어떤 플래그를 줘도 모든 루프가 제출을 거부합니다. 다시 켜려면 그 파일을 지우면 됩니다.

실제 자격증명으로 `--submit`을 넘기기 전에, 그 경로가 뭘 하는 건지 반드시 읽고 이해하세요.

## 새 브로커 추가하기 (키움, 토스, 또는 다른 무엇이든)

Bithumb과 KIS 연동은 `ops/`와 `momentum/` 안에 있습니다 — 어댑터가 공유 실행엔진과 어떻게 통신하는지(인증, 시세 수집, 주문 제출, 계좌 정합성) 참고 패턴으로 보시면 됩니다. 다른 브로커용으로 작동하는 어댑터를 만드셨다면 PR 환영합니다. 여기 있는 다른 것들과 같은 규칙을 지켜주세요: 실제 자격증명/계좌 데이터는 절대 커밋 금지, 드라이런/모의 경로 포함, 뭘 하고 뭘 안 하는지 명확한 문서화.

## 모델 아이디어 공유하기

전략 아이디어, 검증 방법론, 백테스트랑 실전이 뭐가 달랐는지 얘기하고 싶으면 이 저장소의 [Discussions 탭](../../discussions)이나 Reddit [r/TwoAxisTrading](https://www.reddit.com/r/TwoAxisTrading/)을 이용하세요.

기본 원칙: "지금 이거 사세요" 식의 콜 금지, 수익 약속 금지, 근사한 자산곡선 스크린샷 하나 말고 방법론(워크포워드, 비용 스트레스, 표본 크기)으로 뒷받침할 것.

## 안전 고지

이 저장소는 투자자문이 아니며, 바로 돌리면 되는 완제품 라이브 트레이딩 시스템도 아닙니다. 관여한 누구도 인가받은 투자자문업자가 아닙니다. 리서치/엔지니어링 참고자료로 취급하시고, 여기 연결하는 어떤 자금이든 전액 잃을 수도 있는 돈으로 간주하세요.

## 라이선스

MIT — [LICENSE](LICENSE) 참고. 자유롭게 쓰고, 포크하고, 수정하고, 이걸로 만든 걸 팔아도 됩니다. 보증도 책임도 없습니다 — 자세한 조건은 라이선스 원문 참고.
