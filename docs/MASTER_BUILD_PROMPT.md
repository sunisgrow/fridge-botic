# MASTER BUILD PROMPT

Purpose

This file is the main orchestration prompt for an autonomous coding agent.
It instructs the agent how to read the repository documentation and generate
the entire production system step by step.

The agent must treat this repository as a specification-driven project.

---

# Agent Role

You are an autonomous senior software engineer responsible
for generating a production-ready Telegram bot system for
fridge inventory management.

Your job is to:

read the repository documentation
generate code modules
run tests
fix errors
continue until the project is complete.

---

# Project Overview

The system is a Telegram bot that helps users manage food stored in a fridge.

Main capabilities:

product tracking
expiration notifications
DataMatrix scanning
product recognition from photos
receipt scanning
recipe recommendations
shopping list generation
food waste analytics

---

# Architecture Summary

System components:

Telegram Bot Service
API Backend
PostgreSQL Database
Redis Queue
Background Workers
ML Modules
Data Pipelines

Refer to:

SYSTEM_ARCHITECTURE.md
SERVICE_DEPENDENCIES.md
ARCHITECTURE_DECISIONS.md

---

# Domain Model

All data entities are defined in:

DOMAIN_MODEL.md

You must generate database models,
ORM mappings and API schemas
based on this file.

---

# API Contracts

All endpoints must follow:

API_CONTRACTS.md

Generate FastAPI routers
matching these contracts.

---

# Development Rules

All generated code must follow:

CODE_GENERATION_RULES.md

Required architecture layers:

routers
services
repositories
models
schemas

---

# Task Execution

Tasks are defined in:

TASK_QUEUE.md

You must execute them sequentially.

For each task:

generate code
run tests
fix failures
commit progress

---

# Code Templates

Reusable templates for modules
are defined in:

MODULE_TEMPLATES.md

Use them when generating new modules.

---

# Telegram Bot Interface

All bot dialogs and flows are defined in:

UI_DIALOG_MAP.md

Generate handlers and FSM dialogs accordingly.

---

# Image and Scan Features

Implement image and barcode processing
based on:

SCAN_PIPELINE.md
IMAGE_PRODUCT_RECOGNITION.md
RECEIPT_SCANNER.md

---

# Data Pipelines

Product catalog and recipe datasets
must follow pipelines defined in:

DATA_PIPELINES.md

Generate import scripts and workers.

---

# Analytics

User behavior analytics and food waste statistics
must follow:

FRIDGE_ANALYTICS.md

Generate analytics tables and workers.

---

# Event System

Internal events must follow:

EVENT_SCHEMA.md

Implement event emission and subscriptions.

---

# CI/CD

Continuous integration rules are defined in:

CI_PIPELINE.md

Ensure repository contains:

CI configuration
Docker containers
test automation

---

# Testing

Testing strategy is defined in:

TEST_STRATEGY.md

You must generate:

unit tests
integration tests
API tests

Minimum coverage: 80%.

---

# Performance and Scaling

System must follow scaling rules in:

PERFORMANCE_SCALING.md

Design services to be stateless and horizontally scalable.

---

# Build Loop

Repeat the following process until all tasks are completed.

Step 1

Read next task from TASK_QUEUE.md.

Step 2

Identify required modules and dependencies.

Step 3

Generate code using templates.

Step 4

Add tests for generated modules.

Step 5

Run test suite.

Step 6

If tests fail:

analyze errors
fix implementation
re-run tests

Step 7

Commit generated code.

---

# Completion Criteria

Project is complete when:

all tasks executed
tests pass
CI pipeline succeeds
docker-compose starts system successfully.

---

# Final Validation

The system must support:

running API server
running Telegram bot
running background workers
processing product scans
sending expiration notifications
generating recipe recommendations
building shopping lists
displaying analytics.

---

# Output Requirements

Generated code must be:

modular
typed
documented
production-ready.

Follow best practices of Python backend development.