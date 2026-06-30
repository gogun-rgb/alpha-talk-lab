# AlphaTalk Lab

![CI](https://github.com/gogun-rgb/alpha-talk-lab/actions/workflows/ci.yml/badge.svg)

> 자연어 투자 질문을 실제 시장 데이터와 뉴스에 연결해 검증 가능한 투자 가설로 변환하는 리서치 도구

AlphaTalk Lab은 “엔비디아와 AMD 최근 흐름을 비교해줘” 같은 질문을 두 개의 미국 주식 티커, 분석 기간, 가격 지표, 뉴스 키워드, 검증 가능한 투자 가설로 바꾸는 포트폴리오 프로젝트입니다.

## 문제 정의

초보 투자자는 가격 차트, 뉴스, 지표, 가설 검증을 따로 확인해야 합니다. 이 프로젝트는 매수·매도 추천 대신 `데이터 -> 관찰 -> 가설 -> 반대 근거 -> 검증 방법` 흐름을 한 화면에서 제공합니다.

## 핵심 차별점

- 숫자 계산은 Python에서 수행하고 AI가 계산하지 않습니다.
- 실제 가격 데이터와 가설을 UI에서 분리합니다.
- OpenAI API가 없어도 규칙 기반 분석으로 작동합니다.
- 뉴스 본문을 무단 크롤링하지 않고 제공 가능한 메타데이터만 사용합니다.

## 주요 기능

- 자연어 질문 또는 직접 티커 입력
- 최근 1개월, 3개월, 6개월, 1년 분석
- yfinance 기반 일별 가격 수집
- 누적 수익률, 연환산 변동성, 최대 낙폭, 상승 거래일 비율, 상관계수 계산
- 시작값 100 기준 정규화 가격 차트
- 종목별 뉴스 제목과 키워드
- 투자 가설, 반대 근거, 백테스트 아이디어
- 두 종목의 추세·모멘텀·위험·상대 강도를 기반으로 한 기술적 매력도 비교
- Markdown 리서치 노트 복사 및 다운로드
- 로딩, 오류, 뉴스 없음, OpenAI 미설정 상태 처리

기술적 매력도는 매수 추천 점수가 아닙니다. 최근 가격 데이터를 여러 규칙으로 요약하여 두 종목의 상대적인 기술적 상태를 비교합니다.

## 화면 흐름

1. 질문과 티커, 기간 입력
2. 질문에서 종목과 기간 인식
3. 백엔드가 가격 및 뉴스 데이터를 수집
4. Python이 모든 지표를 계산
5. OpenAI 또는 규칙 기반 엔진이 리서치 노트를 생성
6. 대시보드에서 데이터, 뉴스, 가설, 한계를 구분해 표시

## 기술 스택

- Frontend: Next.js, TypeScript, App Router, Tailwind CSS, Recharts, Vitest
- Backend: Python, FastAPI, Pandas, NumPy, yfinance, Pydantic, pytest
- AI: OpenAI API optional structured JSON output
- Scripts: Windows PowerShell

## 시스템 구조

```text
alpha-talk-lab/
├─ frontend/
├─ backend/
├─ docs/
├─ scripts/
├─ .env.example
├─ docker-compose.yml
└─ README.md
```

## 데이터 처리 과정

백엔드는 두 종목의 일별 가격을 yfinance에서 가져오고 공통 거래일로 정렬합니다. 이후 정규화 가격과 핵심 지표를 계산합니다. 뉴스는 yfinance가 제공하는 제목, 출처, 날짜, URL 중심으로 사용합니다.

## 자연어 파싱 방식

티커 인식은 직접 입력값을 최우선으로 사용하고, 질문 안에서는 `$NVDA`처럼 명시된 티커, 회사명 사전, 일반 대문자 티커 후보 순으로 처리합니다. `AI`, `CEO`, `ETF`, `GPU` 같은 일반 약어는 자동 티커 후보에서 제외합니다. 자동 인식 결과가 부족하거나 애매하면 화면에서 직접 수정할 수 있습니다.

## 뉴스 없는 경우

뉴스가 없거나 한 종목에만 뉴스가 있는 경우에도 가격 분석은 정상 작동합니다. 두 종목 모두 뉴스가 없으면 뉴스 기반 가설과 뉴스 이벤트 스터디를 만들지 않고 가격 기반 가설로 대체합니다. 한 종목만 뉴스가 있으면 두 종목의 뉴스 빈도나 키워드 차이를 단정하지 않고 한계를 표시합니다.

## AI가 담당하는 부분

OpenAI API가 설정된 경우, 이미 계산된 지표와 실제 뉴스 제목만 입력받아 관찰, 가설, 반대 근거, 검증 방법을 구조화합니다. 응답은 Pydantic JSON 구조 검증과 의미 검증을 통과해야 합니다.

## AI 검증 방식

- JSON 구조 검증
- 뉴스 가용성 검증
- 요청한 두 종목 외의 티커 검증
- 추천·목표주가·수익 보장 표현 검증
- 백엔드 계산값과 충돌하는 퍼센트 수치 검증
- 실패 시 한 번 재시도 후 규칙 기반 리서치 노트로 fallback

## Python이 담당하는 계산

누적 수익률, 일별 수익률, 연환산 변동성, 최대 낙폭, 상승 거래일 비율, 상관계수, 정규화 가격은 모두 `backend/app/services/metrics.py`에서 계산합니다. 기술적 매력도 점수는 `backend/app/services/technical_analysis.py`에서 추세, 모멘텀, 위험, 상대 강도를 규칙 기반으로 계산합니다.

## 사실과 가설 분리 방식

결과 화면은 확인된 가격 데이터, 뉴스 기반 정보, 검증되지 않은 가설, 위험 및 한계를 별도 섹션으로 표시합니다. 가설 카드에는 “검증되지 않은 가설” 배지를 표시합니다.

## 화면 예시

<!-- 실제 실행 화면 촬영 후 docs/images/input-screen.png를 추가하세요. -->
<!-- 실제 실행 화면 촬영 후 docs/images/research-result.png를 추가하세요. -->
<!-- 실제 데모 녹화 후 docs/images/demo.gif를 추가하세요. -->

## 설치 방법

PowerShell에서:

```powershell
cd D:\CodexProjects\alpha-talk-lab
.\scripts\setup.ps1
Copy-Item .env.example .env
```

OpenAI를 사용하려면 `.env`의 `OPENAI_API_KEY`에 값을 입력합니다. 키가 없어도 규칙 기반 분석은 작동합니다.

## 실행 방법

```powershell
cd D:\CodexProjects\alpha-talk-lab
.\scripts\dev.ps1
```

브라우저에서 `http://localhost:3000`을 엽니다. 백엔드는 `http://localhost:8000`에서 실행됩니다.
해당 포트가 이미 사용 중이면 `scripts/dev.ps1`이 3001/8001처럼 가까운 대체 포트를 선택해 출력합니다.

개별 실행:

```powershell
cd D:\CodexProjects\alpha-talk-lab\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd D:\CodexProjects\alpha-talk-lab\frontend
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
pnpm dev
```

위 첫 번째 명령에서 PowerShell이 경로 공백을 잘못 해석하면 다음을 사용합니다.

```powershell
& "D:\CodexProjects\alpha-talk-lab\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
```

## 환경변수

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

실제 API 키와 `.env` 파일은 Git에 포함하지 않습니다.

## 테스트 방법

전체 검증:

```powershell
cd D:\CodexProjects\alpha-talk-lab
.\scripts\test.ps1
```

개별 검증:

```powershell
cd D:\CodexProjects\alpha-talk-lab\backend
..\.venv\Scripts\python.exe -m pytest
```

```powershell
cd D:\CodexProjects\alpha-talk-lab\frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

## API 설명

- `GET /health`: 상태 확인
- `GET /api/tickers/validate?ticker=NVDA`: 티커 검증
- `POST /api/query/parse`: 자연어 질문에서 티커와 기간 추출
- `POST /api/research/compare`: 두 종목 비교 분석과 기술적 매력도 비교

자세한 내용은 `docs/api.md`를 확인하세요.

## 현재 한계

- yfinance 데이터 품질과 지연 가능성에 영향을 받습니다.
- 뉴스 데이터가 종목별로 충분하지 않을 수 있습니다.
- 뉴스 제목 기반 분석은 기사 본문 맥락을 반영하지 못합니다.
- 기술적 매력도 가중치는 경험적 규칙이며 실제 유효성은 별도 백테스트가 필요합니다.
- 백테스트 아이디어는 실행 코드가 아니라 검증 설계입니다.
- 미국 주식 2개 비교에 초점을 둔 MVP입니다.

## 향후 개선 계획

- 벤치마크 ETF 대비 초과수익률 분석
- 뉴스 이벤트 스터디 자동화
- 더 긴 기간의 로컬 캐시
- 결과 공유용 정적 리포트 생성
- 검증용 백테스트 엔진 추가

## 투자 자문 면책

이 프로젝트는 교육 및 리서치 보조 목적의 소프트웨어입니다. 어떤 결과도 매수·매도 추천, 목표주가, 수익 보장, 투자 자문을 의미하지 않습니다. 모든 투자 판단은 사용자의 책임입니다.
