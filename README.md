# PCI-DSS Compliant Payment Tokenization Pipeline

A production-grade DevSecOps pipeline that enforces PCI-DSS security controls automatically on every code push.

## What This Project Does

Implements a payment card tokenization service where sensitive card numbers are encrypted with AES-256-GCM and replaced with secure UUID tokens. The CI/CD pipeline enforces security gates that prevent insecure code from ever reaching production. A host-level Monit layer monitors the running service and automatically recovers it from crashes and memory leaks.

> **Current implementation status:** token storage is in-memory (a Python dict in `app/vault.py`), and the API endpoints do not currently enforce API-key authentication. Both were part of the original design and are tracked in the Roadmap section below rather than described as done.

## Architecture

```
Developer pushes code to GitHub
              │
              ▼
┌─────────────────────────────────────┐
│         CircleCI Pipeline           │
│                                      │
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
              │
              ▼
┌─────────────────────────────────────┐
│         Running Service             │
│                                      │
│  FastAPI ──► /tokenize, /detokenize  │
│                  │                   │
│                  ▼                   │
│           AES-256-GCM encrypt        │
│                  │                   │
│                  ▼                   │
│         In-memory token store        │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      Monit (host-level)              │
│                                      │
│  Process check + HTTP /health check  │
│  Memory threshold restart             │
│  Restart-storm alerting               │
└─────────────────────────────────────┘
```

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
| Req 3.4 — Protect stored cardholder data | AES-256-GCM encryption | `app/crypto.py` |
| Req 3.4 — No plain text storage | Token replaces card number | `app/vault.py` |
| Req 3.5 — Protect encryption keys | Key loaded from environment, never hardcoded | `.env` + `app/crypto.py` |
| Req 6.3 — Identify security vulnerabilities | Static code analysis | Semgrep SAST |
| Req 6.4 — Protect public-facing apps | Container vulnerability scan | Trivy |
| Req 7.1 — Restrict access to system components | API key auth (planned — see Roadmap) | — |
| Req 8.2 — No hardcoded credentials | Secret detection on every push | TruffleHog |
| Req 10.2 — Audit trail | Image tagged with Git SHA | Docker Hub + CircleCI |
| Req 12.3 — Controlled production changes | Human approval gate | CircleCI manual approval |

## Security Decisions Made During Build

**AES-GCM over AES-CBC** — Semgrep SAST detected that CBC mode provides no message authentication, meaning encrypted data could be tampered with. Migrated to GCM which provides both confidentiality and integrity (AEAD). Maps to PCI-DSS Req 3.4.

**Alpine over Debian slim** — Trivy detected 2 CRITICAL CVEs (CVE-2026-42496, CVE-2026-8376) in perl-base bundled with python:3.11-slim. Switched to Alpine which does not include Perl, eliminating the vulnerability entirely. Maps to PCI-DSS Req 6.4.

**Non-root container user** — Docker container runs as a non-root user (`appuser`) to limit blast radius if the container is compromised.

## API Endpoints

| Endpoint | Method | Auth Required | Description |
|---|---|---|---|
| `/tokenize` | POST | Not yet enforced | Accepts card number, returns UUID token |
| `/detokenize` | POST | Not yet enforced | Accepts token, returns original card number |
| `/health` | GET | No | Health check |

### Example Usage

Tokenize a card:
```bash
curl -X POST http://localhost:8000/tokenize \
  -H "Content-Type: application/json" \
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
| Self-healing / monitoring | Monit | Free |

## Running Locally

Prerequisites: Python 3.10+

```bash
git clone https://github.com/hemantdeshwal19/payment-tokenization-pipeline
cd payment-tokenization-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set an encryption key (32 bytes)
export ENCRYPTION_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"

# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run tests:
```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `ENCRYPTION_KEY` | Yes | 32-byte key used for AES-256-GCM encryption |
| `ENABLE_LEAK_TEST` | No | Set to `1` to enable the `/leak` test endpoint used to exercise Monit's memory-restart rule. Not present in normal deployments. |

Generate a strong encryption key:
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```

## Project Structure

```
payment-tokenization-pipeline/
├── app/
│   ├── main.py          # FastAPI app: /tokenize, /detokenize, /health, gated /leak
│   ├── vault.py         # In-memory token storage
│   └── crypto.py        # AES-256-GCM encryption
├── tests/
│   └── test_tokenize.py # Unit tests
├── Dockerfile            # Alpine-based non-root container
├── .env.example
└── .circleci/
    └── config.yml        # 5-stage security pipeline
```

## Operational Resilience — Self-Healing with Monit

Most CI/CD pipelines stop at deployment. This project adds a host-level
monitoring layer that detects and automatically recovers from two real
failure modes, using [Monit](https://mmonit.com/monit/) alongside a
systemd-managed deployment of the service.

### What's monitored

The service runs as a systemd unit (`tokenization-pipeline.service`) and
Monit watches it for:

| Check | Condition | Action |
|---|---|---|
| Process liveness | Process missing (crash, OOM-kill, etc.) | Restart via `systemctl start` |
| Application health | `/health` endpoint fails to respond (timeout 5s) | Restart via `systemctl start` |
| Memory growth | RSS > 250 MB sustained for 3 consecutive checks | Restart via `systemctl start` |
| Restart storms | 3 restarts within 5 check cycles | Alert (stop auto-restarting) |

Config (`/etc/monit/conf-enabled/tokenization-pipeline`):

```
check process tokenization-pipeline matching "uvicorn app.main:app"

    start program = "/usr/bin/systemctl start tokenization-pipeline"
    stop program  = "/usr/bin/systemctl stop tokenization-pipeline"

    if failed
        host 127.0.0.1
        port 8000
        protocol http
        request "/health"
        with timeout 5 seconds
    then restart

    if totalmem > 250 MB for 3 cycles then restart

    if 3 restarts within 5 cycles then alert
```

### Why both a process check and an HTTP check

A process can stay alive while the application it's running is no longer
functional — for example, hung on a blocking call. Checking the PID alone
would miss this. Combining a process check with an active HTTP request to
`/health` catches both "the process died" and "the process is alive but
broken" failure modes.

### Tested failure scenarios

**1. Process crash**
```bash
kill -9 <pid>
```
Result: Monit detected the missing process and restarted it via
`systemctl start`. A new PID was assigned and `/health` returned
`{"status":"ok"}` again with no manual intervention.

**2. Memory leak**
A test-only endpoint (`/leak`, gated behind `ENABLE_LEAK_TEST`, absent
from any real deployment) was used to simulate a service leaking memory
under load. Repeated calls grew RSS from **46.9 MB to 333.1 MB**, past
the 250 MB threshold. After memory stayed elevated for 3 consecutive
check cycles, Monit restarted the process automatically — memory
returned to baseline (**~47 MB**) with the service healthy throughout.

### Why this matters

A memory leak that never crashes the process, or a hang that keeps the
port open but stops answering requests, are both realistic production
incidents that basic uptime monitoring (e.g. "is the port open") would
miss entirely. This setup demonstrates detecting and recovering from
both without waiting for a human to notice.

**Note:** the `/leak` endpoint exists only for testing this recovery
behavior and is disabled unless `ENABLE_LEAK_TEST=1` is explicitly set —
it is not present in a normal deployment.

## Roadmap

- [ ] Persist tokens in PostgreSQL instead of in-memory storage
- [ ] API key authentication on `/tokenize` and `/detokenize`
- [ ] Luhn algorithm validation
- [ ] HTTPS with TLS
- [ ] Token expiry
- [ ] Rate limiting
- [ ] Audit logging
- [ ] OWASP ZAP DAST scanning
- [ ] HashiCorp Vault for key management
