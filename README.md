# AI Mail Assistant

An AI-powered mailbox classification backend designed to organize emails across multiple accounts and surface important job-search messages.

The project is currently under active development.

## Features

* Classifies incoming emails into categories such as interviews, rejections, application updates, recruiter follow-ups, and unrecognized messages
* Supports fallback and Anthropic-powered classification modes
* Tracks classification confidence and review status
* Supports secondary email categories
* Provides a manual-review workflow for uncertain classifications
* Uses PostgreSQL for persistent storage
* Includes automated tests for classification behavior and provider failures

## Technology Stack

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Anthropic API
* Pydantic
* Pytest

## Project Structure

```text
app/
├── api/             API routes
├── core/            Configuration and shared application logic
├── db/              Database models and sessions
├── enums/           Classification and status enums
├── integrations/    External email and AI provider integrations
├── schemas/         Request and response schemas
├── services/        Classification and business logic
└── main.py          FastAPI application entry point

tests/
└── unit/            Unit tests
```

## Local Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file:

```bash
copy .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Update the database URL and Anthropic API key when required.

The project can run with the fallback classifier without an Anthropic API key:

```env
AI_CLASSIFIER_MODE="fallback"
```

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

The API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Running Tests

```bash
pytest
```

## Current Status

The backend classification foundation is implemented. Mail-provider authentication, multi-account synchronization, dashboard functionality, and production monitoring are planned as upcoming development phases.
