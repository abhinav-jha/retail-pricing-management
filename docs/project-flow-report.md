# Retail Pricing Management – Project Flow Report

## 1) Project Purpose
This project is a retail pricing management system for managing large pricing feeds from stores. The core use cases are:

- Upload pricing CSV files
- Validate and persist pricing records in a database
- Search pricing data by store, SKU, product name, and date
- Update existing price records safely with optimistic locking
- Track import job status asynchronously for large files

The application is designed as a production-style prototype with a browser UI, FastAPI backend, SQLAlchemy ORM, PostgreSQL, Celery worker, and Redis.

## 2) High-Level Architecture

```text
User -> Frontend (HTML/JS) -> FastAPI API -> Service Layer -> Repository Layer -> PostgreSQL
                                  |
                                  +-> Celery worker via Redis -> CSV import processing
```

### Runtime components
- Frontend: static HTML/JavaScript served by FastAPI
- Backend: FastAPI app running on port 8000
- Data layer: PostgreSQL
- Async processing: Celery + Redis
- File uploads: local upload directory in /tmp/retail_pricing_uploads

## 3) Key Files and Their Roles

### Frontend
- [frontend/index.html](../frontend/index.html): main UI layout
- [frontend/app.js](../frontend/app.js): handles upload, search, refresh, and inline price updates
- [frontend/styles.css](../frontend/styles.css): styling

### Backend
- [backend/app/main.py](../backend/app/main.py): app startup and route registration; serves static frontend and health check
- [backend/app/api/pricing.py](../backend/app/api/pricing.py): API endpoints for create, upload, search, get, and update
- [backend/app/services/pricing.py](../backend/app/services/pricing.py): business logic
- [backend/app/repositories/pricing.py](../backend/app/repositories/pricing.py): SQLAlchemy queries and update logic
- [backend/app/models/pricing.py](../backend/app/models/pricing.py): pricing table definition
- [backend/app/models/import_job.py](../backend/app/models/import_job.py): tracking table for CSV imports
- [backend/app/db/database.py](../backend/app/db/database.py): DB engine and session factory
- [backend/app/db/init_db.py](../backend/app/db/init_db.py): creates database tables on startup
- [backend/app/core/config.py](../backend/app/core/config.py): environment-based configuration
- [backend/app/worker.py](../backend/app/worker.py): Celery task that imports CSV records asynchronously
- [backend/tests/test_pricing.py](../backend/tests/test_pricing.py): automated tests for pricing flows

## 4) Data Model
The main table is `pricing` and its fields are defined in [backend/app/models/pricing.py](../backend/app/models/pricing.py):

- id
- store_id
- sku
- product_name
- price
- price_date
- version
- created_at
- updated_at

Important rules:
- `store_id + sku + price_date` is unique
- `version` is used for optimistic concurrency
- `updated_at` automatically changes on edit

The import tracking table is `import_jobs`, defined in [backend/app/models/import_job.py](../backend/app/models/import_job.py):

- id
- file_name
- file_path
- status (`queued`, `processing`, `completed`, `failed`)
- total_rows
- processed_rows
- error_message
- created_at
- updated_at

## 5) End-to-End Request Flow

### A. App startup
When the backend starts, [backend/app/main.py](../backend/app/main.py) runs the startup hook:

- initialize database via `init_db()`
- mount the frontend static assets
- expose `/` to serve the UI
- expose `/api/v1/health` to verify DB connectivity

### B. Frontend load
The browser loads the static frontend from `/`.

`frontend/app.js` immediately calls `loadPricing()`:
- fetches `GET /api/v1/pricing`
- renders results in a table
- displays price update controls and filters

### C. Search flow
The user submits search filters from the UI.

Flow:
1. Frontend serializes filter values from input fields
2. `fetchPricing(params)` calls `GET /api/v1/pricing?store_id=...&sku=...&product_name=...&price_date=...`
3. FastAPI route `search_pricing` receives query params
4. `PricingService.search()` delegates to `PricingRepository.search()`
5. SQLAlchemy builds a filtered query with pagination
6. Rows are returned as JSON
7. Frontend renders them in a table

### D. CSV upload flow
This is the central async workflow.

1. User selects a CSV file in the frontend
2. `frontend/app.js` sends a multipart upload to `POST /api/v1/pricing/upload`
3. Backend validates that the file extension is `.csv`
4. It stores the file in the configured `UPLOAD_DIR`
5. An `ImportJob` record is created with status `queued`
6. The backend calls `process_csv_import.apply_async(args=[job.file_path, job.id])`
7. Celery dispatches the task to Redis and a worker process executes it
8. The worker parses the CSV in batches, converts rows into `Pricing` ORM objects, and inserts them
9. It updates `ImportJob.processed_rows` and final status to `completed` or `failed`
10. Frontend polls `GET /api/v1/pricing/jobs/{job_id}` until completed

### E. Worker processing flow
The Celery task is implemented in [backend/app/worker.py](../backend/app/worker.py):

- read CSV with `csv.DictReader`
- validate expected headers: `Store ID, SKU, Product Name, Price, Date`
- skip empty rows
- convert values to Python types
- insert records in batches of 1000 for performance
- update import job state as processing/completed/failed

This pattern helps avoid blocking the main API request when a large CSV file is being imported.

### F. Price update flow
The UI allows a user to edit a row and save a new price.

1. Frontend reads the row ID, current version, and entered price
2. It sends `PUT /api/v1/pricing/{pricing_id}` with JSON body `{ price, version }`
3. FastAPI endpoint `update_pricing` calls `PricingService.update_price`
4. Repository checks:
   - record exists
   - current database version matches the version the client submitted
5. If matched, it updates the `price`, increments `version`, updates `updated_at`, and commits
6. If not matched, it returns conflict

This is optimistic concurrency: the user is prevented from overwriting another edit without noticing.

## 6) Why the Architecture Fits the Problem

### Layered design
- API layer handles HTTP concerns
- Service layer handles business rules
- Repository layer isolates database logic
- Model layer defines DB schema
- Worker layer handles long-running processing asynchronously

### Why Celery + Redis
Large CSV imports should not block the API request. A queue lets the app accept the upload quickly and process heavy work in the background.

### Why PostgreSQL
The system is designed around production-like retail data volume, transactional integrity, and indexing support.

### Why optimistic locking
This avoids overwriting price changes when multiple users edit the same pricing record near-simultaneously.

## 7) Interview Questions and Answers

### Q1. What is the main purpose of this project?
This project is a retail pricing management app that lets teams upload pricing CSV feeds, store them reliably, search them by store/SKU/date, and update prices while keeping data consistent.

### Q2. How does the project work end-to-end?
A user uploads a CSV from the frontend. The backend validates the file, saves it to disk, creates an import job record, and enqueues a Celery task. The worker reads the CSV, parses rows, stores them in PostgreSQL, and updates job status. The UI polls the API until the import is complete and then refreshes the pricing list.

### Q3. Which technologies are used?
Python, FastAPI, SQLAlchemy, PostgreSQL, Celery, Redis, HTML/CSS/JavaScript, Docker, Pytest.

### Q4. What is the role of FastAPI here?
FastAPI provides the REST API for pricing creation, search, upload, status checks, and updates. It also serves the static frontend and health-check endpoints.

### Q5. What is the role of the Celery worker?
The worker executes CSV imports asynchronously in the background to avoid blocking the API and to support large-volume processing.

### Q6. What is the database schema for pricing records?
The pricing table stores store ID, SKU, product name, price, price date, version, and timestamps. It enforces uniqueness across store + SKU + price date.

### Q7. How does the app handle concurrency on updates?
It uses a version column and compares the client version against the current database version before allowing an update. If they differ, it rejects the update to prevent accidental overwrite.

### Q8. Why is the CSV import asynchronous?
Because ingesting large files may take time and should not block the user or the API. Async processing improves responsiveness and hides long-running work behind a status job.

### Q9. How does the frontend interact with the backend?
The browser uses fetch calls to the API: upload, search, job-status polling, and price updates.

### Q10. What happens if an import fails?
The worker catches errors, marks the job as `failed`, stores an error message in `ImportJob.error_message`, and returns the failure details. The frontend then displays the failure status.

### Q11. What are the key trade-offs in this design?
- Simple and easy to understand for a case study
- Good for moderate to large retail feeds
- Minimal complexity but not yet fully production-scale for all enterprise concerns like S3 storage, secure auth, orchestration, and indexing strategy

### Q12. Where would you improve this project next?
- Use S3 for uploaded files instead of local disk
- Add authentication and authorization
- Add proper logging and metrics
- Improve search performance with indexes and maybe full-text search
- Add more validation, retries, and rate limiting
- Use an actual production queue and deployment stack

## 8) Project Flow Summary
The system is a classic layered web app:

- frontend collects user actions
- FastAPI exposes APIs
- SQLAlchemy interacts with PostgreSQL
- Celery handles heavy background work
- Redis acts as the task broker
- import jobs track progress and failures

This makes the project easy to explain in interviews because it shows a clear separation of concerns, a realistic data model, and a scalable pattern for asynchronous processing.
