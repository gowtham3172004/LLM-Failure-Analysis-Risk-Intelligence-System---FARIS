# FARIS - LLM Failure Analysis & Risk Intelligence System

<p align="center">
  <img src="docs/logo.png" alt="FARIS Logo" width="200" />
</p>

<p align="center">
  <strong>A production-grade system for understanding WHY Large Language Models fail—not just that they fail.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-documentation">API</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## 🎯 Overview

FARIS (Failure Analysis & Risk Intelligence System) is an intelligent backend system that performs deep analysis of LLM outputs to detect, classify, and explain various types of failures. Unlike simple fact-checking tools, FARIS provides:

- **Root Cause Analysis**: Understand *why* the LLM produced a flawed response
- **Multi-dimensional Detection**: 6 specialized detectors for different failure types
- **Risk Quantification**: Domain-aware risk scoring with confidence intervals
- **Actionable Recommendations**: Specific, prioritized improvement suggestions
- **Pattern Learning**: Vector-based similar failure retrieval

## ✨ Features

### 🔍 Six Specialized Failure Detectors

| Detector | Weight | Description |
|----------|--------|-------------|
| **Hallucination** | 35% | Detects fabricated facts, non-existent entities, false citations |
| **Logical Inconsistency** | 25% | Identifies contradictions, circular reasoning, invalid inferences |
| **Missing Assumptions** | 20% | Finds unstated prerequisites, hidden dependencies, implicit constraints |
| **Overconfidence** | 10% | Catches excessive certainty, ignored uncertainty, inappropriate precision |
| **Scope Violation** | 5% | Detects answers beyond the question scope or capability boundaries |
| **Underspecification** | 5% | Identifies vague answers, missing details, incomplete responses |

### 🏥 Domain-Aware Risk Scoring

Different domains have different tolerance levels for LLM failures:

| Domain | Multiplier | Rationale |
|--------|------------|-----------|
| Medical | 2.0x | Patient safety critical |
| Legal | 1.8x | Liability and compliance |
| Finance | 1.5x | Financial impact |
| Code | 1.3x | Bug and security risks |
| General | 1.0x | Baseline |

### 🔄 Parallel Processing Architecture

FARIS uses LangGraph for orchestrated, parallel execution:

```
                    ┌─────────────┐
                    │   Precheck  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Decompose   │
                    │   Claims    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │Halluc.  │       │ Logic   │       │ Assume  │
   │Detector │       │Detector │       │Detector │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │Overconf.│       │ Scope   │       │ Under   │
   │Detector │       │Detector │       │ spec    │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Aggregate  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
     │   Explain   │ │  Risk   │ │ Recommend   │
     └─────────────┘ │ Score   │ └─────────────┘
                     └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) with LLaMA 3.1:8b model
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/faris.git
cd faris
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up Ollama**
```bash
# Install Ollama from https://ollama.ai/
ollama pull llama3.1:8b
ollama serve  # Start the Ollama server
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

6. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access the API**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f faris

# Stop services
docker-compose down
```

## 📚 API Documentation

### Analyze LLM Response

```http
POST /api/analyze
Content-Type: application/json

{
  "question": "What are the side effects of aspirin?",
  "llm_answer": "Aspirin has no side effects and is completely safe for everyone.",
  "domain": "medical",
  "context": "Patient consultation context",
  "model_metadata": {
    "model_name": "gpt-4",
    "temperature": 0.7
  }
}
```

#### Response

```json
{
  "case_id": "uuid-here",
  "failure_detected": true,
  "failure_types": ["hallucination", "overconfidence"],
  "failures": [
    {
      "type": "hallucination",
      "severity": "critical",
      "confidence": 0.92,
      "description": "The claim that aspirin has 'no side effects' is factually incorrect...",
      "affected_claims": ["Aspirin has no side effects"],
      "evidence": ["Medical literature documents numerous side effects..."]
    }
  ],
  "claims": [
    {
      "text": "Aspirin has no side effects",
      "verifiable": true,
      "verdict": "false",
      "explanation": "This is a factually incorrect statement..."
    }
  ],
  "risk_assessment": {
    "risk_score": 0.87,
    "risk_level": "critical",
    "risk_factors": [
      "High confidence hallucination in medical domain",
      "Patient safety implications"
    ],
    "confidence_interval": {
      "lower": 0.82,
      "upper": 0.92
    }
  },
  "recommendations": [
    {
      "type": "correction",
      "priority": "high",
      "description": "Include known side effects such as...",
      "affected_failures": ["hallucination"],
      "implementation_hint": "Consult medical databases for complete list"
    }
  ],
  "explanation": {
    "summary": "Critical failures detected in medical response...",
    "detailed_analysis": "The response contains dangerous misinformation..."
  }
}
```

### Quick Analysis (No Persistence)

```http
POST /api/analyze/quick
```

Same request/response format, but results are not stored in the database.

### Batch Analysis

```http
POST /api/analyze/batch
Content-Type: application/json

{
  "requests": [
    {"question": "...", "llm_answer": "..."},
    {"question": "...", "llm_answer": "..."}
  ]
}
```

### List Analysis Cases

```http
GET /api/cases?page=1&page_size=10&domain=medical&risk_level=high
```

### Get Case Details

```http
GET /api/cases/{case_id}
```

### Get Statistics

```http
GET /api/cases/statistics/summary
```

### Get Failure Taxonomy

```http
GET /api/taxonomy
```

## 🏗️ Architecture

### Project Structure

```
faris/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── analysis.py      # Analysis endpoints
│   │   │   ├── cases.py         # Case management
│   │   │   └── taxonomy.py      # Failure taxonomy
│   │   └── schemas/
│   │       ├── requests.py      # Request models
│   │       └── responses.py     # Response models
│   ├── core/
│   │   ├── embeddings/
│   │   │   └── encoder.py       # SentenceTransformers
│   │   ├── graph/
│   │   │   ├── nodes/
│   │   │   │   ├── detectors/   # 6 failure detectors
│   │   │   │   ├── precheck.py
│   │   │   │   ├── decomposition.py
│   │   │   │   ├── aggregation.py
│   │   │   │   ├── explanation.py
│   │   │   │   ├── risk_scoring.py
│   │   │   │   └── recommendation.py
│   │   │   ├── orchestrator.py  # LangGraph workflow
│   │   │   └── state.py         # Shared state
│   │   └── llm/
│   │       ├── client.py        # Ollama client
│   │       └── prompts.py       # Prompt templates
│   ├── db/
│   │   ├── repositories/
│   │   │   ├── cases.py         # Case CRUD
│   │   │   └── failures.py      # Failure patterns
│   │   ├── vector/
│   │   │   └── chroma.py        # ChromaDB client
│   │   ├── database.py          # SQLAlchemy setup
│   │   └── models.py            # ORM models
│   ├── services/
│   │   └── analysis_service.py  # Business logic
│   ├── config.py                # Settings
│   └── main.py                  # FastAPI app
├── tests/
│   ├── test_api/
│   └── test_core/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI | Async REST API with auto-documentation |
| Orchestration | LangGraph | Graph-based workflow with parallel execution |
| LLM Inference | Ollama | Local LLM hosting (LLaMA 3.1:8b) |
| Database | SQLite/PostgreSQL | Relational data storage |
| Vector Store | ChromaDB | Embedding-based similarity search |
| Embeddings | SentenceTransformers | Text vectorization |
| Validation | Pydantic v2 | Request/Response validation |
| ORM | SQLAlchemy 2.0 | Async database operations |

### Key Design Decisions

1. **Free & Open Source**: Uses only free tools (Ollama, SQLite, ChromaDB) - no paid API dependencies

2. **Parallel Detection**: All 6 detectors run concurrently via asyncio.gather for speed

3. **Deterministic Risk Scoring**: Formula-based scoring (not LLM-generated) for consistency:
   ```
   risk = Σ (confidence × severity_weight × domain_multiplier)
   ```

4. **Claim Decomposition**: Breaks responses into atomic claims for granular analysis

5. **Pattern Learning**: Stores and retrieves similar failure patterns for context

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model for analysis |
| `DATABASE_URL` | `sqlite+aiosqlite:///./faris.db` | Database connection |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | ChromaDB storage path |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

### Failure Weights (Configurable)

```python
FAILURE_WEIGHTS = {
    "hallucination": 0.35,
    "logical_inconsistency": 0.25,
    "missing_assumptions": 0.20,
    "overconfidence": 0.10,
    "scope_violation": 0.05,
    "underspecification": 0.05,
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_analysis.py -v

# Run only unit tests
pytest tests/test_core/ -v
```

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "ollama": "connected",
    "chromadb": "connected"
  }
}
```

### Logging

Logs are structured JSON format:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Analysis completed",
  "case_id": "uuid",
  "duration_ms": 2500,
  "failures_detected": 2
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- [Ollama](https://ollama.ai/) for local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [SentenceTransformers](https://www.sbert.net/) for embeddings

---

<p align="center">
  Built with ❤️ for understanding LLM failures
</p>
