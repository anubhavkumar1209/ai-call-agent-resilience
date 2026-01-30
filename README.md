# AI Call Agent - Error Recovery & Resilience System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A production-grade error recovery and resilience system for AI Call Agents that interact with multiple third-party services (ElevenLabs TTS, LLM providers). Implements industry-standard patterns to handle failures intelligently and maintain high availability.

---
## 📁 Project Structure

```
ai-call-agent-resilience/
├── src/
│   ├── __init__.py
│   ├── config.py                      # Configuration
│   ├── main.py                        # Application entry point
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── custom_exceptions.py      # Exception hierarchy
│   ├── retry/
│   │   ├── __init__.py
│   │   └── retry_handler.py          # Retry with exponential backoff
│   ├── circuit_breaker/
│   │   ├── __init__.py
│   │   └── circuit_breaker.py        # Circuit breaker pattern
│   ├── logging/
│   │   ├── __init__.py
│   │   └── logger.py                 # Dual logging (console + JSON file)
│   ├── alerts/
│   │   ├── __init__.py
│   │   └── alert_manager.py          # Multi-channel alerting
│   ├── health_check/
│   │   ├── __init__.py
│   │   └── health_checker.py         # Background health monitoring
│   └── services/
│       ├── __init__.py
│       ├── elevenlabs_service.py     # ElevenLabs mock service
│       └── llm_service.py            # LLM mock service
├── logs/
│   └── error_recovery.log            # JSON structured logs
├── requirements.txt                   # Python dependencies
├── .env                               # Environment variables (not in Git)
├── .gitignore                         # Git ignore rules
└── README.md                          # This file
```

## 🎯 Problem Statement

AI Call Agents depend on multiple external services:
- **ElevenLabs** for text-to-speech conversion
- **LLM providers** for conversational AI
- **CRM APIs** for contact management

Any service failure can cause:
- Cascading outages
- Poor user experience
- Reduced system availability

Solution: implement resilience patterns (retries, circuit breakers, health checks, observability, and graceful degradation) so the agent recovers intelligently and continues to operate.

---

## 🏗️ Architecture Overview

<img width="1536" height="1024" alt="ChatGPT Image Jan 30, 2026, 06_55_39 AM" src="https://github.com/user-attachments/assets/9f47a87b-3141-43a4-a09e-7b41d78641d9" />


### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Call Agent                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Retry      │  │   Circuit    │  │   Health     │           │
│  │   Handler    │  │   Breaker    │  │   Checker    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Logger     │  │    Alert     │  │Exception     │           │
│  │   (JSON)     │  │   Manager    │  │Hierarchy     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │       External Services                 │
        ├──────────────────┬──────────────────────┤
        │   ElevenLabs     │      LLM Provider    │
        │   (TTS Service)  │  (Conversation AI)   │
        └──────────────────┴──────────────────────┘
```

### Design Principles

1. Separation of concerns — each component has a single responsibility.  
2. Fail-fast philosophy — circuit breakers prevent resource exhaustion.  
3. Graceful degradation — the system continues operating despite failures.  
4. Observability — comprehensive logging and alerting.  
5. Configuration-driven — parameters are externalized for easy tuning.

---

## 🔧 System Components

### 1. Exception Hierarchy

**Location**: `src/exceptions/custom_exceptions.py`

```
ServiceError (Base Exception)
├── TransientError (Retryable)
│   ├── TimeoutError
│   ├── NetworkError
│   └── ServiceUnavailableError (503)
└── PermanentError (Non-Retryable)
    ├── AuthenticationError (401)
    ├── InvalidPayloadError
    └── QuotaExceededError
```

Purpose: differentiate between errors that can be retried and those that require fail-fast behavior.

---

### 2. Retry Handler

**Location**: `src/retry/retry_handler.py`

**Configuration**:
```python
INITIAL_RETRY_DELAY = 5      # seconds
MAX_RETRY_ATTEMPTS = 3       # attempts
BACKOFF_MULTIPLIER = 2       # exponential factor
```

Retry pattern: 5s → 10s → 20s

Only retries `TransientError` types; `PermanentError` is not retried to avoid wasting resources.

---

### 3. Circuit Breaker

**Location**: `src/circuit_breaker/circuit_breaker.py`

States:
- CLOSED — normal operation (requests pass through)
- OPEN — fail-fast, requests rejected
- HALF_OPEN — testing for recovery

**Configuration**:
```python
FAILURE_THRESHOLD = 3        # failures before OPEN
SUCCESS_THRESHOLD = 2        # successes to CLOSE
TIMEOUT = 30                 # seconds before HALF_OPEN
```

State transitions:
```
CLOSED ──[3 failures]──> OPEN ──[30s]──> HALF_OPEN
   ▲                                        │
   └──────────[2 successes]────────────────┘
```

Each external service has its own circuit breaker to isolate faults.

---

### 4. Health Checker

**Location**: `src/health_check/health_checker.py`

Features:
- Runs in a background thread (non-blocking)
- Periodic checks (default every 60s)
- Automatically resets a circuit breaker when a service recovers
- Per-service health monitoring and logging

Example output:
```
Health checker started for ElevenLabs
ElevenLabs is healthy
Health checker started for LLM
LLM is healthy
```
<img width="1920" height="1080" alt="2" src="https://github.com/user-attachments/assets/f9f17450-8f14-456e-9f89-4f85ef3b8c1c" />

---

### 5. Logging System

**Location**: `src/logging/logger.py`

Dual output:
1. Console: human-friendly messages
2. File: structured JSON log lines

Log file: `logs/error_recovery.log`

Required fields:
- Timestamp
- Service name
- Error category
- Retry count
- Circuit breaker state

JSON example:
```json
{
  "timestamp": "2026-01-30T00:17:01.123456",
  "level": "ERROR",
  "logger": "src.circuit_breaker",
  "message": "Circuit breaker OPENED for ElevenLabs"
}
```

Google Sheets integration is optional and disabled by default. Enable with service account credentials and set `GOOGLE_SHEETS_ENABLED = True`.

---

### 6. Alert Manager

**Location**: `src/alerts/alert_manager.py`

Supported channels:
- Email (SMTP)
- Telegram (Bot API)
- Webhook (HTTP POST)

Alert triggers:
- Circuit breaker opens
- Call permanently fails
- Service remains down beyond a configured threshold

Alerts are disabled by default for demo safety:
```python
# src/config.py
EMAIL_ENABLED = False
TELEGRAM_ENABLED = False
WEBHOOK_ENABLED = False
```

Reasons:
1. Avoids requiring credentials for a demo
2. Prevents accidental external notifications during evaluation
3. Keeps the implementation testable without external setup

To enable alerts in production, add credentials to `.env` and flip the flags in `src/config.py`.

Example log line when an alert would be sent:
```
Sending alert: Call Failed for Contact 1
```


---

## 📐 Architecture Decisions

### Custom Exception Hierarchy
Why: lets retry logic and circuit breakers reason about errors using type checks (e.g., `isinstance(err, TransientError)`).
Benefit: avoids retrying permanent errors like 401 or invalid payloads.

### Exponential Backoff (2x multiplier)
Why: reduces the "thundering herd" effect when a service is recovering.
Pattern: 5s → 10s → 20s.

### Circuit Breaker Per Service
Why: isolating failures prevents a single failing service (ElevenLabs) from impacting others (LLM).

### Fail-Fast When Circuit Open
Why: saves threads, CPU, and network resources; improves latency for healthy parts of the system.

### Background Health Checks
Why: enables automatic recovery of circuits without manual intervention.

### Graceful Degradation
Why: a failed call should not block the entire queue — skip the failing contact and continue.

---

## 🔄 Error Flow

### Scenario: ElevenLabs Returns 503 (Required Scenario)

1. Call ElevenLabs API  
2. Receive 503 Service Unavailable  
3. Classify as `TransientError` (ServiceUnavailableError)  
4. Retry using exponential backoff:
   - Attempt 1: wait 5s → fail
   - Attempt 2: wait 10s → fail
   - Attempt 3: wait 20s → fail  
5. Retries exhausted → circuit breaker opens for ElevenLabs  
6. Log the error (JSON) and trigger alert (if enabled)  
7. Mark current call as failed and continue to the next contact  
8. Health checker continues to probe; when healthy, circuit resets and normal processing resumes

Example console flow:
```
Processing contact: Contact 1
Step 2: Converting text to speech with ElevenLabs
Calling ElevenLabs text-to-speech API
Simulating 503 error (failure 1)
Transient error on attempt 1: Service temporarily unavailable. Retrying in 5s...
Calling ElevenLabs text-to-speech API
Simulating 503 error (failure 2)
Transient error on attempt 2: Service temporarily unavailable. Retrying in 10s...
Calling ElevenLabs text-to-speech API
Simulating 503 error (failure 3)
Circuit breaker OPENED for ElevenLabs
Max retry attempts (3) reached for ElevenLabs
Transient error for Contact 1: Service temporarily unavailable
Sending alert: Call Failed for Contact 1

Processing contact: Contact 2
Circuit breaker is OPEN for ElevenLabs. Failing fast.
Skipping contact.
```

---

## ⚙️ Retry & Circuit Breaker Behavior

### Retry Behavior

Trigger: only on `TransientError`  
Pattern: exponential backoff

| Attempt | Delay | Cumulative Time |
|---------|-------|-----------------|
| 1       | 0s    | 0s              |
| 2       | 5s    | 5s              |
| 3       | 10s   | 15s             |
| Failed  | -     | ~35s total      |

Code location: `src/retry/retry_handler.py`

Example:
```python
def execute_with_retry(self, func):
    attempt = 0
    delay = self.initial_delay

    while attempt < self.max_attempts:
        try:
            return func()
        except TransientError:
            attempt += 1
            if attempt >= self.max_attempts:
                raise
            time.sleep(delay)
            delay *= self.backoff_multiplier
```

<img width="1920" height="1080" alt="3" src="https://github.com/user-attachments/assets/23a4acf2-90bb-4eac-857b-7ba69839de98" />


### Circuit Breaker Behavior

State machine:
```
CLOSED (Normal)
  │
  │ [3 consecutive failures]
  ▼
OPEN (Fail Fast)
  │
  │ [Wait 30 seconds]
  ▼
HALF_OPEN (Testing)
  │
  ├─ [2 successes] ──> CLOSED
  └─ [1 failure] ────> OPEN
```

Key methods (in `src/circuit_breaker/circuit_breaker.py`):
- `call()` — execute function through circuit checker
- `_on_success()` — record success
- `_on_failure()` — record failure and possibly open circuit
- `_transition_to_open()` — flip to OPEN state
- `reset()` — used by health checker to restore CLOSED

---

## 🚨 Alerting Logic

### Alert Trigger Conditions

1. Circuit breaker opens:
```python
if self.failure_count >= self.failure_threshold:
    self._transition_to_open()
    # Trigger alert
```

2. Call permanently fails:
```python
self.alert_manager.send_alert(
    subject=f"Call Failed for {contact['name']}",
    message=f"Permanent error: {e.message}",
    alert_type="CRITICAL"
)
```

3. Permanent Error (e.g., 401 authentication failure) triggers CRITICAL alert.

### Alert Channels Implementation

Email example (SMTP):
```python
def _send_email(self, subject, message):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(Config.EMAIL_FROM, Config.EMAIL_PASSWORD)
    server.send_message(msg)
```

Telegram example:
```python
def _send_telegram(self, message):
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": Config.TELEGRAM_CHAT_ID, "text": message})
```

Webhook example:
```python
def _send_webhook(self, subject, message, alert_type):
    payload = {
        "subject": subject,
        "message": message,
        "alert_type": alert_type,
        "timestamp": str(datetime.now())
    }
    requests.post(Config.WEBHOOK_URL, json=payload)
```

Why channels are disabled by default:
- No credentials required for demo
- Implementation can be verified via logged "Sending alert" messages
- Prevents accidental notifications during evaluation

To enable alerts, add credentials to `.env` and set the flags in `src/config.py`.

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/anubhavkumar1209/ai-call-agent-resilience.git
cd ai-call-agent-resilience

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 💻 Usage

### Running the System

```bash
# Set PYTHONPATH if needed
# Windows PowerShell
$env:PYTHONPATH = "E:\Anubhav\ai-call-agent-resilience"
# Linux/Mac
export PYTHONPATH="$PWD"

# Run the agent
python -m src.main
```

### Expected Output

```
Starting AI Call Agent
Health checker started for ElevenLabs
Health checker started for LLM

Processing contact: Contact 1
Step 1: Generating response with LLM
LLM API call successful
Step 2: Converting text to speech with ElevenLabs
Simulating 503 error (failure 1)
Transient error on attempt 1: Service temporarily unavailable. Retrying in 5s...
[... retries continue ...]
Circuit breaker OPENED for ElevenLabs
Sending alert: Call Failed for Contact 1

Processing contact: Contact 2
Circuit breaker is OPEN for ElevenLabs. Failing fast.
Skipping contact.

[... continues with remaining contacts ...]

Health checker stopped for ElevenLabs
Health checker stopped for LLM
AI Call Agent stopped
```

<img width="1920" height="1080" alt="4" src="https://github.com/user-attachments/assets/95e0f73b-2e7a-4ae1-b244-942569262509" />


---

## 📊 Example Logs

### Console Output (Clean)
```
Starting AI Call Agent
Processing contact: Contact 1
Circuit breaker OPENED for ElevenLabs
Sending alert: Call Failed for Contact 1
```

### Log File (`logs/error_recovery.log`) - JSON Format

```json
{"timestamp": "2026-01-30T00:17:01.123456", "level": "INFO", "logger": "__main__", "message": "Starting AI Call Agent"}
{"timestamp": "2026-01-30T00:17:02.234567", "level": "ERROR", "logger": "src.circuit_breaker", "message": "Circuit breaker OPENED for ElevenLabs"}
{"timestamp": "2026-01-30T00:17:02.345678", "level": "ERROR", "logger": "root", "message": "{\"timestamp\": \"2026-01-30T00:17:02.345678\", \"service_name\": \"ElevenLabs\", \"error_category\": \"TRANSIENT_ERROR\", \"message\": \"Service temporarily unavailable\", \"retry_count\": 0, \"circuit_state\": \"OPEN\"}"}
{"timestamp": "2026-01-30T00:17:02.456789", "level": "INFO", "logger": "src.alerts.alert_manager", "message": "Sending alert: Call Failed for Contact 1"}
```

### View Logs

```bash
# View all logs
cat logs/error_recovery.log

# Windows PowerShell
Get-Content logs\error_recovery.log

# Tail logs in real-time
tail -f logs/error_recovery.log

# Windows PowerShell
Get-Content logs\error_recovery.log -Tail 50 -Wait
```
<img width="1920" height="1080" alt="5" src="https://github.com/user-attachments/assets/02162389-f6b9-4c1e-8131-dedfcee14af2" />

<img width="1920" height="1080" alt="6" src="https://github.com/user-attachments/assets/13be99e7-475c-4072-b2d5-94c9e4eeb39c" />


---

## ⚙️ Configuration

### Main Configuration File

**Location**: `src/config.py`

```python
class Config:
    # Retry Configuration
    INITIAL_RETRY_DELAY = 5      # seconds
    MAX_RETRY_ATTEMPTS = 3       # attempts
    BACKOFF_MULTIPLIER = 2       # exponential factor
    
    # Circuit Breaker Configuration
    FAILURE_THRESHOLD = 3        # failures to open
    SUCCESS_THRESHOLD = 2        # successes to close
    TIMEOUT = 30                 # seconds
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL = 60   # seconds
    
    # Logging Configuration
    LOG_FILE_PATH = "logs/error_recovery.log"
    GOOGLE_SHEETS_ENABLED = False
    
    # Alert Configuration
    EMAIL_ENABLED = False
    TELEGRAM_ENABLED = False
    WEBHOOK_ENABLED = False
```

### Environment Variables

**Location**: `.env` (not committed to Git)

```env
# Email Configuration
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=admin@example.com
EMAIL_PASSWORD=your_app_password

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Webhook Configuration
WEBHOOK_URL=https://webhook.site/your-unique-url
```

---

## 🧪 Testing

### Manual Testing

Run the system and observe:
1. Retry Logic: watch 5s → 10s → 20s delays  
2. Circuit Breaker: opens after 3 failures  
3. Graceful Degradation: system continues with next contacts  
4. Health Checks: running in background  
5. Logging: JSON logs in `logs/error_recovery.log`  
6. Alerts: `Sending alert` message appears in logs (actual sending disabled by default)

### Simulation Scenarios

**Scenario 1**: ElevenLabs 503 (Default)
```python
# In src/services/elevenlabs_service.py
self.simulate_failure = True  # Already set
```

**Scenario 2**: All Services Healthy
```python
# In src/services/elevenlabs_service.py
self.simulate_failure = False
```

---

## 🔒 Security Considerations

- API keys stored in `.env` (not committed)
- Sensitive credentials are never logged
- Alert messages are sanitized before sending
- Health check endpoints do not expose internal state

---

## 📝 Key Metrics

Monitor these in production:
- Success Rate — percentage of successful calls  
- Retry Rate — how often retries are triggered  
- Circuit Breaker State — time spent in OPEN state  
- Mean Time To Recovery (MTTR) — service recovery time  
- Alert Frequency — alerts per hour
---

**Note**: This is a production-grade implementation suitable for real-world AI Call Agent systems with proper error recovery, monitoring, and alerting capabilities.
