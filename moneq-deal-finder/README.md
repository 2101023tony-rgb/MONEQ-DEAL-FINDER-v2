# MONEQ DEAL FINDER — AI 리셀 차익 분석 & 꿀매물 자동 탐색 플랫폼

**MONEQ DEAL FINDER**는 사용자가 보유 예산만 입력하면 실제 연동 가능한 시세 데이터와 매물 피드를 분석해 **예상 순이익 및 수익률이 가장 높은 리셀 상품과 매물을 자동 추천**해 주는 풀스택 PWA(Progressive Web App) 플랫폼입니다.

---

## 1. 아키텍처 및 데이터 연동 현실성 고지

본 프로젝트는 **무단 크롤링 및 플랫폼 접근 제한 우회를 엄격히 금지**하며, 실제 운영 가능한 공식 API·허용 피드 기반 어댑터 패턴(`DataSourceAdapter`)으로 설계되었습니다.

| 연동 대상 | 현재 공식 지원 여부 (2026년 기준) | 본 프로젝트 구현 상태 | 대안 및 실연동 방법 |
| :--- | :--- | :--- | :--- |
| **네이버 쇼핑 검색 API** | **공식 무료 OpenAPI 지원** (`openapi.naver.com/v1/search/shop.json`) | **실제 API 연동 구현 완료** (`NaverShoppingAdapter`) | 네이버 개발자 센터에서 무료 Client ID/Secret 발급 후 `.env`에 입력 즉시 실데이터 조회 가능 |
| **Google Gemini API** | **공식 무료 티어 지원** (`gemini-2.5-flash`) | **실제 AI 분석 연동 구현 완료** (`GeminiAnalyzer`) | Google AI Studio에서 무료 API 키 발급 후 `.env`에 입력 시 시세 분석·판매글 자동 생성 작동 |
| **당근 (Karrot)** | 일반 개인용 중고매물 검색/등록 공개 API **미제공** (광고주용 OpenAPI만 베타 제공) | **[미연동 / 공식 파트너십·수동 피드 어댑터 구조]** (`DaangnOfficialAdapter`) | 무단 크롤링 대신 ① 제휴 파트너 API 키 연동 슬롯, ② 사용자 직접 URL/CSV 임포트, ③ 데모/테스트용 샘플 데이터(명확히 라벨링됨) 제공 |
| **번개장터 (Bunjang)** | 일반 공개 매물 검색/자동 등록 API **미제공** (제휴 파트너 전용 API 운영) | **[미연동 / 공식 파트너십·수동 피드 어댑터 구조]** (`BunjangOfficialAdapter`) | 제휴 승인 후 발급받는 Partner Token 입력 슬롯 제공 + 미연동 시 명확한 안내 및 복사형 판매글 생성기 제공 |

> **투명성 원칙:** API 키가 설정되지 않았거나 공식 API가 없는 플랫폼의 매물은 UI와 API 응답에 `[SAMPLE / 테스트 데이터]` 배지가 명시적으로 표시되며, 시세 데이터가 없는 상품은 임의로 가격을 지어내지 않고 **`데이터 부족`** 상태를 반환합니다.

---

## 2. 폴더 구조

```text
moneq-deal-finder/
├── frontend/                     # GitHub Pages 정적 배포 가능 프론트엔드 (PWA)
│   ├── index.html                # 메인 대시보드 & 5대 핵심 기능 UI
│   ├── manifest.json             # iOS/Android 홈 화면 설치(PWA) 매니페스트
│   ├── sw.js                     # 오프라인 캐싱 및 푸시 알림용 Service Worker
│   ├── public/icons/icon.svg     # 앱 아이콘
│   ├── css/style.css             # 다크 네이비 & 네온 그린 금융 터미널 스타일
│   └── js/
│       ├── config.js             # 백엔드 API 엔드포인트 설정
│       ├── api.js                # 백엔드 통신 및 오프라인/데모 폴백 클라이언트
│       └── app.js                # UI 렌더링, 차익 계산기, PWA 설치 핸들러
├── backend/                      # FastAPI 기반 Python 백엔드 (Render / Koyeb / Railway 무료 배포)
│   ├── app/
│   │   ├── main.py               # FastAPI 엔트리포인트, CORS, Rate Limit, 스케줄러
│   │   ├── config.py             # 환경변수 관리 (.env)
│   │   ├── database.py           # SQLite (로컬) / PostgreSQL (운영) DB 연결 및 테이블 초기화
│   │   ├── models.py             # Pydantic 요청/응답 스키마
│   │   ├── adapters/
│   │   │   ├── base.py           # 표준 매물 어댑터 인터페이스
│   │   │   ├── naver_api.py      # [실연동] 네이버 쇼핑 검색 공식 OpenAPI 어댑터
│   │   │   └── marketplace.py    # 당근/번개장터 공식 파트너 슬롯 & 명시적 샘플 데이터 어댑터
│   │   └── services/
│   │       ├── profit_calc.py    # 순이익·수익률 정밀 계산 엔진
│   │       ├── ai_engine.py      # [실연동] Gemini API 기반 시세 분석 & 판매글 생성기
│   │       └── scanner.py        # 카테고리별 자동 꿀매물 탐색 및 중복 방지(Deduplication) 워커
│   ├── tests/
│   │   └── test_core.py          # 수익 계산, 중복 방지, API 엔드포인트 자동화 테스트
│   ├── requirements.txt          # Python 의존성 목록
│   └── .env.example              # 환경변수 템플릿
├── .gitignore
└── README.md                     # 설치, 실행, 무료 배포 가이드
```

---

## 3. 수익 분석 공식

모든 매물과 AI 추천 상품은 다음 공식을 엄격히 적용하여 순이익과 수익률을 산출합니다.

- **예상 순이익** = `예상 판매가격 - 매입가격 - 플랫폼 수수료 - 배송비 - 기타 비용`
- **예상 수익률 (%)** = `(예상 순이익 ÷ 매입가격) × 100`

---

## 4. 로컬 설치 및 실행 방법

### 4-1. 백엔드 실행 (Python 3.10+)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, GEMINI_API_KEY 입력 (미입력 시에도 안전 모드로 동작)

uvicorn app.main:app --reload --port 8000
```
- API 문서(Swagger UI): `http://localhost:8000/docs`

### 4-2. 프론트엔드 실행
```bash
cd frontend
python -m http.server 3000
```
- 브라우저 접속: `http://localhost:3000`
- **아이폰(iOS) 홈 화면 설치(PWA):** Safari로 접속 → 하단 `공유` 아이콘 → `홈 화면에 추가` 선택

---

## 5. 무료 클라우드 배포 가이드 (GitHub + Render/Vercel)

1. **GitHub 저장소 업로드**: 본 폴더 전체를 GitHub 새 저장소에 Push 합니다.
2. **프론트엔드 (GitHub Pages 무료 배포)**:
   - GitHub 저장소 `Settings` → `Pages` → Source를 `Deploy from a branch` 선택 후 `/frontend` 지정.
   - `frontend/js/config.js`의 `API_BASE_URL`을 배포된 백엔드 URL로 수정합니다.
3. **백엔드 (Render / Koyeb / Railway 무료 티어 배포)**:
   - GitHub 저장소 연결 후 Root Directory를 `backend`로 설정.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables에 `.env` 항목 등록.
