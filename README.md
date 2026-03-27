# Finance AI (FinGraph)

주식·뉴스·SEC 공시를 수집해 LLM으로 분석하고, 결과를 Neo4j 그래프 DB에 저장한 뒤 REST API와 대시보드로 제공하는 파이프라인 프로젝트.

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| **백엔드 API** | FastAPI + Uvicorn |
| **프론트엔드** | Streamlit + streamlit-agraph |
| **그래프 DB** | Neo4j 5 Community (Bolt) |
| **ETL 스케줄러** | Apache Airflow 2 (LocalExecutor, 30분 주기) |
| **Airflow 메타DB** | PostgreSQL 13 |
| **컨테이너** | Docker Compose |
| **LLM** | Google Gemini 2.0 Flash (기본) / OpenAI GPT-4o (fallback) |
| **데이터 수집** | yfinance, feedparser(Google News RSS), SEC EDGAR REST API |
| **HTML 파싱** | BeautifulSoup4 |
| **데이터 직렬화** | Pydantic |
| **환경변수** | python-dotenv |

---

## 주요 컴포넌트

```
src/
├── collectors/
│   ├── stock.py        # yfinance로 종목 기본 정보 수집 (NVDA, AAPL 등 7개 종목)
│   ├── news.py         # Google News RSS → feedparser로 최신 뉴스 수집
│   └── disclosure.py   # SEC EDGAR API로 10-K 원문 수집 및 XBRL 재무 데이터 수집
├── processing/
│   └── extractor.py    # LLM 호출 (이벤트 시그널 추출 / 10-K 기초 분석, 출력 한국어)
├── graph/
│   ├── db.py           # Neo4j 드라이버 싱글턴 + 재시도 로직
│   ├── schema.py       # 제약조건 초기화 (Company, Sector, News, Concept)
│   └── loader.py       # MERGE 기반 노드/엣지 upsert
├── api/
│   └── server.py       # FastAPI 엔드포인트 (/search/{ticker}, /leaders)
├── ui/
│   └── dashboard.py    # Streamlit 대시보드 (그래프 시각화, AI 시그널, 10-K & 재무)
└── etl_pipeline.py     # 파이프라인 진입점 (Airflow DAG에서 호출)

dags/
└── finance_graph_dag.py  # Airflow DAG (30분 간격 ETL)
```

---

## 데이터 흐름

```
[yfinance / Google News RSS / SEC EDGAR]
        ↓ collectors
[LLMProcessor] → Gemini 2.0 Flash (이벤트 시그널, 10-K 요약, 한국어 출력)
        ↓
[Neo4j] ← GraphLoader (MERGE upsert)
        ↓
[FastAPI :8000] → [Streamlit :8501]
```

### Neo4j 노드 & 관계

| 노드 | 주요 속성 |
|------|-----------|
| `Company` | ticker, name, sector |
| `Sector` | name |
| `News` | url, title, date, summary |
| `Signal` | type, summary, sentiment, reason, date |
| `Report` | type(10-K), year, business_summary, risks, competitors |
| `Financials` | revenues(JSON), net_incomes(JSON) |

| 관계 |
|------|
| `Company -[:BELONGS_TO]→ Sector` |
| `News -[:MENTIONS]→ Company` |
| `News -[:REVEALS]→ Signal` |
| `Signal -[:AFFECTS]→ Company` |
| `Company -[:FILED]→ Report` |
| `Company -[:HAS_FINANCIALS]→ Financials` |

---

## 실행 방법

```bash
# 환경변수 설정 (최소 GEMINI_API_KEY 필요)
cp .env.example .env
# GEMINI_API_KEY=...        (필수 — 없으면 Mock 데이터 반환)
# OPENAI_API_KEY=...        (선택 — Gemini 키가 없을 때 GPT-4o fallback)
# ANTHROPIC_API_KEY=...     (선택 — docker-compose에 선언되어 있으나 현재 코드에서 미사용)

# 전체 서비스 실행
docker compose up --build

# 서비스 포트
# Neo4j Browser  : http://localhost:7474
# FastAPI        : http://localhost:8000
# Streamlit      : http://localhost:8501
# Airflow        : http://localhost:8080  (admin / admin)
```


