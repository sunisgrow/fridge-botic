# System Architecture

Architecture of the Fridge Telegram Bot platform.

Goal:
scalable architecture capable of handling thousands of users and image scans.

---

## High Level Architecture

```
Telegram
    │
    ▼
Bot Service
    │
    ▼
API Backend
    │
    ├── Database (PostgreSQL)
    │
    └── Queue/Cache (Redis)
            │
            ▼
        Background Workers
```

---

## Services

### Bot Service

Responsible for Telegram communication.

Tech stack:
- aiogram 3.x

Functions:
- command handlers
- FSM dialogues
- image receiving
- API calls

---

### API Backend

Business logic layer.

Tech stack:
- FastAPI
- SQLAlchemy
- Pydantic

Responsibilities:
- product management
- fridge management
- GTIN lookup
- DataMatrix processing
- notification scheduling

---

### Database

PostgreSQL

Stores:
- users
- products
- GTIN catalog
- fridge items
- scan logs
- recipes

---

### Queue / Cache

Redis

Used for:
- task queue
- caching GTIN lookups
- FSM state storage
- rate limiting

---

## Workers

### Scan Worker

Processes image recognition tasks.

Pipeline:
```
image
  → preprocessing
  → decode DataMatrix
  → extract GS1 fields
  → save result
```

---

### Notification Worker

Runs periodic checks for expiration dates.

Algorithm:
```
SELECT fridge_items
WHERE expiration_date <= today + notification_days

Send Telegram notifications
```

---

### Import Worker

Imports large GTIN datasets.

Sources:
- Open Food Facts
- Retail catalogs
- Internal dataset

---

## Infrastructure

Recommended deployment:
Docker Compose

Services:
```
docker-compose.yml

services:
  - bot
  - api
  - postgres
  - redis
  - worker-scan
  - worker-notification
  - worker-import
  - scheduler
```

---

## Scaling

### Bot Service
Horizontal scaling via multiple instances

### API
Stateless, can scale horizontally

### Workers
Multiple instances allowed for parallel processing

### Database
Read replicas possible for high load

---

## Monitoring

Recommended tools:
- Prometheus
- Grafana

Metrics to track:
- API response time
- scan queue length
- worker failures
- notifications sent
- database connections

---

## Security

### Authentication
Based on Telegram ID

### Rate Limiting
Implemented via Redis

### Input Validation
Pydantic schemas

### SQL Injection Prevention
SQLAlchemy parameterized queries

---

## Data Flow

### Add Product Flow
```
User
  → Bot Handler
  → API Client
  → API Router
  → Service Layer
  → Repository
  → Database
```

### Scan Flow
```
User sends photo
  → Bot receives image
  → API /scan endpoint
  → Queue task
  → Scan Worker
  → Decode DataMatrix
  → Extract GTIN
  → Lookup product
  → Create fridge item
  → Notify user
```

### Notification Flow
```
Scheduler (daily)
  → Notification Worker
  → Query expiring items
  → Send Telegram messages
  → Log results
```

---

## Technology Decisions

### Why aiogram?
- Native async support
- FSM for dialogues
- Large community
- Well documented

### Why FastAPI?
- High performance
- Async native
- Auto documentation
- Type hints support

### Why PostgreSQL?
- Relational data model
- ACID compliance
- Good indexing
- JSON support if needed

### Why Redis?
- Fast in-memory operations
- Queue support
- Caching capabilities
- FSM state storage

---

## Deployment Architecture

### Development
```
Local Docker Compose
  - Single container per service
  - Shared volumes for logs
  - Local PostgreSQL and Redis
```

### Production
```
Kubernetes / Docker Swarm
  - Multiple bot replicas
  - API with load balancer
  - Managed PostgreSQL
  - Managed Redis
  - Worker auto-scaling
```

---

## Failure Handling

### Bot Service
- Auto-restart on crash
- Connection retry logic

### API
- Health checks
- Graceful shutdown
- Error logging

### Workers
- Task retry with exponential backoff
- Dead letter queue for failed tasks

### Database
- Connection pooling
- Transaction rollback on error

---

## Performance Targets

| Metric | Target |
|--------|--------|
| API response time | < 100ms |
| Scan processing | < 5s |
| Notification delivery | < 10s |
| GTIN lookup | < 10ms |
| Concurrent users | 1000+ |

---

## API Gateway

For production deployment, consider adding:
- Nginx reverse proxy
- Rate limiting
- SSL termination
- Static file serving

---

## Logging

### Log Levels
- ERROR: Critical failures
- WARNING: Recoverable issues
- INFO: Important events
- DEBUG: Development details

### Log Storage
- Structured JSON logs
- Centralized l