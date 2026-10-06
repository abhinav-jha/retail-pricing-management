# Retail Pricing Management

A web-based retail pricing management application designed to allow users to upload, search, and manage pricing data across a large retail store network.

This project is developed as part of a technical case study for a retail organization operating across approximately 3,000 stores and multiple countries.

## Problem Statement

Retail stores periodically provide pricing feeds containing:

- Store ID
- SKU
- Product Name
- Price
- Date

The application provides a centralized platform to:

1. Upload pricing feeds using CSV files.
2. Persist pricing information.
3. Search pricing records using multiple criteria.
4. Edit and save individual pricing records.
5. Process large pricing feeds reliably.
6. Provide a scalable architecture suitable for a large retail organization.

---

# Architecture

The initial solution is designed around a React frontend, FastAPI backend, PostgreSQL database, Redis, background workers, and object storage.

```text
                         ┌───────────────┐
                         │     User      │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │   React SPA   │
                         └───────┬───────┘
                                 │ HTTPS
                                 ▼
                         ┌───────────────┐
                         │ ALB / Gateway │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    FastAPI    │
                         │      API      │
                         └───────┬───────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
                 ▼               ▼               ▼
          ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
          │ PostgreSQL  │ │    Redis    │ │    S3       │
          │             │ │             │ │             │
          │ Pricing     │ │ Cache /     │ │ CSV Files   │
          │ Data        │ │ Task Broker │ │             │
          └─────────────┘ └──────┬──────┘ └─────────────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ Celery Worker │
                         │               │
                         │ CSV Processing│
                         └───────────────┘
```

---

# Technology Stack

## Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Celery
- Redis

## Frontend

- React
- TypeScript
- HTML / CSS

## Infrastructure

- Docker
- AWS
- S3
- Application Load Balancer

## Testing

- Pytest

---

# Core Features

## 1. Pricing Feed Upload

Users can upload pricing feeds using CSV files.

Expected CSV format:

```csv
Store ID,SKU,Product Name,Price,Date
1001,SKU001,