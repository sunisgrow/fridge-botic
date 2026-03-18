# Architecture Decisions

Purpose

Record architectural decisions that guide code generation and system evolution.

Each decision follows ADR format.

---

# ADR-001

Title

Use Python for core backend

Status

Accepted

Reason

Python provides strong ecosystem for:

FastAPI
AI/ML
image processing

---

# ADR-002

Title

Use FastAPI for backend API

Status

Accepted

Reason

High performance
Async support
Automatic OpenAPI generation

---

# ADR-003

Title

Use aiogram for Telegram bot

Status

Accepted

Reason

Modern async Telegram framework
FSM support
Easy scaling

---

# ADR-004

Title

Use PostgreSQL as primary database

Status

Accepted

Reason

Strong relational model
JSON support
High reliability

---

# ADR-005

Title

Use Redis for task queue

Status

Accepted

Reason

Fast in-memory queue
Easy worker integration

---

# ADR-006

Title

Separate workers from API

Status

Accepted

Reason

Heavy tasks must not block API.

Examples

image processing
GTIN import
analytics

---

# ADR-007

Title

Use modular service architecture

Status

Accepted

Structure

routers
services
repositories
models

---

# ADR-008

Title

Use event-driven internal architecture

Status

Accepted

Reason

Allows async processing of:

scan events
expiration events
analytics events