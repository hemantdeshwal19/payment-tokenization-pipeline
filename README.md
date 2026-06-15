# PCI-DSS Compliant Payment Tokenization Pipeline

A production-grade DevSecOps pipeline that enforces PCI-DSS security controls automatically on every code push.

## What This Project Does

Implements a payment card tokenization service where sensitive card numbers are encrypted with AES-256-GCM and replaced with secure UUID tokens. Tokens are persisted in PostgreSQL and protected behind API key authentication. The CI/CD pipeline enforces security gates that prevent insecure code from ever reaching production.

## Architecture
Developer pushes code to GitHub

↓

┌─────────────────────────────────────┐

│         CircleCI Pipeline           │

│                                     │

│  secret-scan ──┐                    │

│                ├── test ──          │

│  sast-scan   ──┘        │           │

│                         ▼           │

│                  build-and-scan     │

│                         │           │

│                         ▼           │

│                  hold-for-approval  │

│                         │           │

│                         ▼           │

│                      deploy         │

└─────────────────────────────────────┘

↓

┌─────────────────────────────────────┐

│         Running Service             │

│                                     │

│  FastAPI ──► Auth Gate              │

│                  │                  │

│                  ▼                  │

│           AES-256-GCM encrypt       │

│                  │                  │

│                  ▼                  │

│            PostgreSQL vault         │

└─────────────────────────────────────┘

## Pipeline Security Gates

| Gate | Tool | What It Checks |
|---|---|---|
| Secret Scanning | TruffleHog | Blocks if API keys or credentials found in code |
| SAST | Semgrep | Blocks if insecure code patterns detected |
| Unit Tests | pytest (12 tests) | Blocks if any test fails |
| Container Scan | Trivy | Blocks if CRITICAL CVEs found in Docker image |
| Manual Approval | CircleCI | Requires human sign-off before production deploy |

## PCI-DSS Control Mapping

| PCI DSS Requirement | Control | Enforced By |
|---|---|---|
| Req 3.4 — Protect stored cardholder data | AES-256-GCM encryption | app/crypto.py |
| Req 3.4 — No plain text storage | Token replaces card number | app/vault.py |
| Req 3.5 — Protect encryption keys | Key loaded from environment, never hardcoded | .env + app/crypto.py |
| Req 6.3 — Identify security vulnerabilities | Static code analysis | Semgrep SAST |
| Req 6.4 — Protect public-facing apps | Container vulnerability scan | Trivy |
| Req 7.1 — Restrict access to system components | API key required on all sensitive endpoints | app/auth.py |
| Req 8.2 — No hardcoded credentials | Secret detection on every push | TruffleHog |
| Req 10.2 — Audit trail | Image tagged with Git SHA | Docker Hub + CircleCI |
| Req 12.3 — Controlled production changes | Human approval gate | CircleCI manual approval |

## Security Decisions Made During Build

**AES-GCM over AES-CBC** — Semgrep SAST detected that CBC mode provides no message authentication, meaning encrypted data could be tampered with. Migrated to GCM which provides both confidentiality and integrity (AEAD). Maps to PCI-DSS Req 3.4.

**Alpine over Debian slim** — Trivy detected 2 CRITICAL CVEs (CVE-2026-42496, CVE-2026-8376) in perl-base bundled with python:3.11-slim. Switched to Alpine which does not include Perl, eliminating the vulnerability entirely. Maps to PCI-DSS Req 6.4.

**Non-root container user** — Docker container runs as a non-root user (appuser) to limit blast radius if the container is compromised.

**PostgreSQL persistent storage** — Replaced in-memory token store with PostgreSQL. Tokens now survive server restarts and are stored encrypted. The raw card number never touches the database. Maps to PCI-DSS Req 3.4.

**API Key Authentication** — All sensitive endpoints require a valid X-API-Key header. Keys are loaded from environment variables, never hardcoded. Comparison uses secrets.compare_digest to prevent timing attacks. Maps to PCI-DSS Req 7.1.

## API Endpoints

| Endpoint | Method | Auth Required | Description |
|---|---|---|---|
| /tokenize | POST | Yes - X-API-Key | Accepts card number, returns UUID token |
| /detokenize | POST | Yes - X-API-Key | Accepts token, returns original card number |
| /health | GET | No | Health check |

### Example Usage

Tokenize a card:
```bash
curl -X POST http://localhost:8000/tokenize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"card_number": "4111111111111111"}'
```

Response:
```json
{"token": "8fb65a64-8551-4d27-96e4-79f7137add81"}
```

Detokenize:
```bash
curl -X POST http://localhost:8000/detokenize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"token": "8fb65a64-8551-4d27-96e4-79f7137add81"}'
```

Response:
```json
{"card_number": "4111111111111111"}
```

## Free Tool Stack

| Purpose | Tool | Cost |
|---|---|---|
| CI/CD | CircleCI Free Tier | 6,000 credits/month |
| Secret Scanning | TruffleHog OSS | Free |
| SAST | Semgrep OSS | Free |
| Container Scanning | Trivy | Free |
| Image Registry | Docker Hub | Free |
| Backend | Python + FastAPI | Free |
| Database | PostgreSQL | Free |

## Running Locally

Prerequisites: Python 3.10+, PostgreSQL

```bash
git clone https://github.com/hemantdeshwal19/payment-tokenization-pipeline
cd payment-tokenization-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your values

# Set up PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE tokenizer_db;"
sudo -u postgres psql -c "CREATE USER tokenizer_user WITH PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tokenizer_db TO tokenizer_user;"

# Start the server
uvicorn app.main:app --reload
```

Run tests:
```bash
pytest tests/ -v
```

## Environment Variables

Create a .env file — never commit this:
API_KEY=your-generated-api-key

DATABASE_URL=postgresql://tokenizer_user:password@localhost/tokenizer_db

ENCRYPTION_KEY=your-32-byte-encryption-key

Generate a strong API key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Project Structure
payment-tokenization-pipeline/

├── app/

│   ├── main.py          # FastAPI app with lifespan handler

│   ├── auth.py          # API key authentication

│   ├── vault.py         # PostgreSQL token storage

│   ├── database.py      # SQLAlchemy models and session

│   └── crypto.py        # AES-256-GCM encryption

├── tests/

│   └── test_tokenize.py # 12 unit tests including auth tests

├── Dockerfile           # Alpine-based non-root container

├── .env.example         # Environment variable template

└── .circleci/

└── config.yml       # 5-stage security pipeline

## Roadmap

- [ ] Luhn algorithm validation
- [ ] HTTPS with TLS
- [ ] Token expiry
- [ ] Rate limiting
- [ ] Audit logging
- [ ] OWASP ZAP DAST scanning
- [ ] HashiCorp Vault for key management
