# Retail Pricing Management Design

## Context diagram

```text
+----------------------+      CSV feeds       +----------------------+
| Retail Store Teams   | -------------------> | Pricing Upload API    |
| (store data feeds)   |                      | (FastAPI backend)     |
+----------------------+                      +----------+-----------+
                                                          |
                                                          v
                                              +----------------------+
                                              | PostgreSQL database  |
                                              | - store_id           |
                                              | - sku                |
                                              | - product_name       |
                                              | - price              |
                                              | - price_date         |
                                              +----------------------+
                                                          |
                                                          v
                                              +----------------------+
                                              | Search/Edit UI       |
                                              | (browser / frontend) |
                                              +----------------------+
```

## Solution architecture

The application uses a lightweight layered architecture:

1. Presentation layer: a static browser UI served from the FastAPI app
2. API layer: FastAPI endpoints for CSV import, search, and record updates
3. Service layer: business logic for pricing validation and filtering
4. Repository layer: SQLAlchemy access to the pricing table
5. Persistence layer: PostgreSQL in Docker, using SQLAlchemy models

## Design decisions

- PostgreSQL was selected to match the assignment's production-oriented requirement and the Docker stack in the repository.
- SQLAlchemy ORM was used to keep the data model and queries maintainable.
- CSV import was designed to accept standard retail feed columns: Store ID, SKU, Product Name, Price, Date.
- A simple optimistic concurrency check is used for updates by comparing the expected `version` before applying a price change.
- Static frontend assets were kept minimal to reduce deployment complexity while still providing a complete web interface.

## Non-functional considerations

- Scalability: the data model is appropriate for large retail datasets and can be extended with indexing and partitioning later.
- Reliability: validation is performed on import and update inputs to reduce bad data quality.
- Maintainability: code is separated into routes, services, repositories, schemas, and models.
- Performance: search endpoints support filtering and pagination, making the API suitable for larger catalog datasets.

## Assumptions

- Pricing feeds arrive in standard CSV format with one row per record.
- Pricing data is expected to be unique by store + SKU + date.
- The application is designed for internal operational use rather than consumer-facing commerce.
- The system runs behind a secure environment and relies on Docker-based infrastructure for database and cache services.
