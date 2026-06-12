# PCI-DSS Compliant Payment Tokenization Pipeline

A production-grade DevSecOps pipeline that enforces PCI-DSS security controls automatically on every code push.

## What This Project Does

Implements a payment card tokenization service where sensitive card numbers are encrypted with AES-256-GCM and replaced with secure UUID tokens. The CI/CD pipeline enforces security gates that prevent insecure code from ever reaching production.

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

## Pipeline Security Gates

| Gate | Tool | What It Checks |
|---|---|---|
| Secret Scanning | TruffleHog | Blocks if API keys or credentials found in code |
| SAST | Semgrep | Blocks if insecure code patterns detected |
| Unit Tests | pytest | Blocks if any of 9 tests fail |
| Container Scan | Trivy | Blocks if CRITICAL CVEs found in Docker image |
| Manual Approval | CircleCI | Requires human sign-off before production deploy |

## PCI-DSS Control Mapping

| PCI DSS Requirement | Control | Enforced By |
|---|---|---|
| Req 3.4 — Protect stored cardholder data | AES-256-GCM encryption | `app/crypto.py` |
| Req 3.4 — No plain text storage | Token replaces card number | `app/vault.py` |
| Req 6.3 — Identify security vulnerabilities | Static code analysis | Semgrep SAST |
| Req 6.4 — Protect public-facing apps | Container vulnerability scan | Trivy |
| Req 8.2 — No hardcoded credentials | Secret detection on every push | TruffleHog |
| Req 10.2 — Audit trail | Image tagged with Git SHA | Docker Hub + CircleCI |
| Req 12.3 — Controlled production changes | Human approval gate | CircleCI manual approval |

## Security Decisions Made During Build

**AES-GCM over AES-CBC** — Semgrep SAST detected that CBC mode provides no message authentication, meaning encrypted data could be tampered with by an attacker. Migrated to GCM which provides both confidentiality and integrity (AEAD).

**Alpine over Debian slim** — Trivy detected 2 CRITICAL CVEs (CVE-2026-42496, CVE-2026-8376) in perl-base bundled with python:3.11-slim. Switched to Alpine which does not include Perl, eliminating the vulnerability entirely.

**Non-root container user** — Docker container runs as a non-root user (appuser) to limit blast radius if the container is compromised.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/tokenize` | POST | Accepts card number, returns UUID token |
| `/detokenize` | POST | Accepts token, returns original card number |
| `/health` | GET | Health check |

## Free Tool Stack

| Purpose | Tool | Cost |
|---|---|---|
| CI/CD | CircleCI Free Tier | 6,000 credits/month |
| Secret Scanning | TruffleHog OSS | Free |
| SAST | Semgrep OSS | Free |
| Container Scanning | Trivy | Free |
| Image Registry | Docker Hub | Free |
| Backend | Python + FastAPI | Free |

## Running Locally

```bash
git clone https://github.com/hemantdeshwal19/payment-tokenization-pipeline
cd payment-tokenization-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests:
```bash
pytest tests/ -v
```

## Project Structure
payment-tokenization-pipeline/

├── app/

│   ├── main.py          # FastAPI tokenization service

│   ├── vault.py         # In-memory token vault

│   └── crypto.py        # AES-256-GCM encryption

├── tests/

│   └── test_tokenize.py # 9 unit tests

├── Dockerfile           # Alpine-based container

└── .circleci/

└── config.yml       # 5-stage security pipeline
