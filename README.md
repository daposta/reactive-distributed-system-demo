# Payout Service

An event-driven payout processing system built with **FastAPI, Apache Kafka, PostgreSQL, SQLAlchemy, Alembic, and Tazapay**.

The system demonstrates asynchronous payout processing, Kafka-based communication, Tazapay payout integration, webhook-driven status updates, idempotency, and reliable event processing.

## Architecture

The system consists of two FastAPI services:

* **FinService** — initiates payout requests.
* **Payout Service** — processes payouts, communicates with Tazapay, receives Tazapay webhooks, and persists payout status.

Apache Kafka provides asynchronous communication between the services and decouples payout initiation from payout processing.

```text
                         ┌─────────────────────────┐
                         │       FinService        │
                         │        Port 8005        │
                         │                         │
                         │  - REST API             │
                         │  - Kafka Producer       │
                         └────────────┬────────────┘
                                      │
                                      │ payout_initiated
                                      ▼
                         ┌─────────────────────────┐
                         │      Apache Kafka       │
                         │      127.0.0.1:29092    │
                         │                         │
                         │  payout_initiated       │
                         │  webhook topic          │
                         └────────────┬────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────┐
│                    Payout Service                         │
│                       Port 8000                           │
│                                                          │
│  ┌────────────────┐       ┌───────────────────────────┐ │
│  │   REST API     │       │     Payout Consumer       │ │
│  │                │       │                           │ │
│  │ Payout API     │       │ payout_initiated          │ │
│  └───────┬────────┘       └─────────────┬─────────────┘ │
│          │                              │               │
│          │                              ▼               │
│          │                    ┌─────────────────┐       │
│          │                    │   Tazapay API   │       │
│          │                    │                 │       │
│          │                    │ Create Payout   │       │
│          │                    └────────┬────────┘       │
│          │                             │                │
│          │                             │ Webhook        │
│          │                             ▼                │
│          │                    POST /webhook/tazapay     │
│          │                             │                │
│          │                             ▼                │
│          │                    ┌─────────────────┐       │
│          │                    │  Webhook Kafka  │       │
│          │                    │     Producer    │       │
│          │                    └────────┬────────┘       │
│          │                             │                │
│          │                             ▼                │
│          │                    ┌─────────────────┐       │
│          │                    │ Webhook Consumer │       │
│          │                    │                 │       │
│          │                    │ Update payout   │       │
│          │                    │ status          │       │
│          │                    └────────┬────────┘       │
│          │                             │                │
│          │                             ▼                │
│          │                    ┌─────────────────┐       │
│          └───────────────────►│   PostgreSQL    │       │
│                               │                 │       │
│                               │ Payout status   │       │
│                               └─────────────────┘       │
└──────────────────────────────────────────────────────────┘
```

## Running the Services

### Services

| Service        | Description                                                                      |    Port |
| -------------- | -------------------------------------------------------------------------------- | ------: |
| Payout Service | REST API, Kafka producers/consumers, Tazapay integration, and webhook processing |  `8000` |
| FinService     | REST API and Kafka producer used to initiate payouts                             |  `8005` |
| Apache Kafka   | Event streaming and asynchronous communication                                   | `29092` |
| PostgreSQL     | Payout persistence and status tracking                                           |  `5432` |

## Payout Flow

The payout lifecycle is asynchronous and event-driven:

```text
FinService
    │
    │ Create payout request
    ▼
Kafka: payout_initiated
    │
    ▼
Payout Consumer
    │
    │ Call Tazapay
    ▼
Tazapay
    │
    │ Payout created
    ▼
PostgreSQL
    │
    │ Initial payout status
    │
    │
    │ Tazapay webhook
    ▼
POST /webhook/tazapay
    │
    ▼
Kafka: webhook topic
    │
    ▼
Webhook Consumer
    │
    │ Update payout status
    ▼
PostgreSQL
```

### Step-by-step

1. **FinService** receives a payout request.
2. FinService publishes the payout event to Kafka.
3. The event is published to the `payout_initiated` topic.
4. The **Payout Consumer** consumes the event.
5. The Payout Service calls the Tazapay Payout API.
6. Tazapay returns a payout ID.
7. The payout record is persisted with the Tazapay payout ID.
8. Tazapay processes the payout asynchronously.
9. Tazapay sends a webhook when the payout status changes.
10. `POST /webhook/tazapay` receives the webhook.
11. The webhook is validated and published to Kafka.
12. The **Webhook Consumer** consumes the webhook event.
13. The consumer locates the payout using the Tazapay payout ID.
14. PostgreSQL is updated with the new payout status.
15. The Kafka offset is committed after successful processing.

## Kafka

Kafka is used to decouple payout initiation, payout processing, and webhook processing.

### Topics

| Topic              | Producer       | Consumer         | Purpose                          |
| ------------------ | -------------- | ---------------- | -------------------------------- |
| `payout_initiated` | FinService     | Payout Service   | Initiates payout processing      |
| `WEBHOOK_TOPIC`    | Payout Service | Webhook Consumer | Processes Tazapay webhook events |

The actual webhook topic is configured through the `WEBHOOK_TOPIC` environment variable.

### Consumer Groups

The payout and webhook consumers use separate consumer groups:

```text
Payout Consumer
    │
    └── payout-consumer-group


Webhook Consumer
    │
    └── webhook-consumer-group
```

Separate consumer groups ensure that payout events and webhook events are processed independently.

### Kafka Producer Configuration

The producer uses:

```text
acks=all
enable.idempotence=true
retries=5
delivery.timeout.ms=120000
request.timeout.ms=30000
```

These settings provide stronger delivery guarantees and allow transient Kafka failures to be retried.

### Kafka Message Keys

Payout and webhook events should use the payout/reference ID as the Kafka message key:

```python
key=str(request_id).encode("utf-8")
```

Using the same key for events associated with the same payout allows Kafka to route them to the same partition, helping preserve ordering for that payout.

## Webhook Processing

Tazapay sends payout status updates to:

```text
POST /webhook/tazapay
```

The webhook endpoint performs minimal processing and publishes the event to Kafka.

```text
                     Tazapay
                         │
                         │ HTTP POST
                         ▼
              /webhook/tazapay
                         │
                         │ Validate
                         ▼
                    Kafka Topic
                         │
                         ▼
                Webhook Consumer
                         │
                         │ Find payout
                         ▼
                    PostgreSQL
                         │
                         │ Update status
                         ▼
                  Payout Record
```

Keeping the webhook endpoint lightweight prevents slow database or business processing from unnecessarily delaying the webhook response.

If the event cannot be durably handed off to Kafka, the endpoint should return a non-success response so that the webhook provider can retry the event.

## Webhook Payload

A Tazapay webhook event has a structure similar to:

```json
{
  "type": "payout.succeeded",
  "data": {
    "id": "pot_xxxxxxxxx",
    "status": "succeeded"
  }
}
```

The Tazapay payout ID is extracted from:

```text
data.id
```

and is used to locate the corresponding payout in PostgreSQL.

## Pydantic Serialization

Webhook events are represented as Pydantic models.

They must be serialized before being passed to Kafka.

Use:

```python
value=payload.model_dump_json().encode("utf-8")
```

Do not use:

```python
json.dumps(payload)
```

because a Pydantic model is not directly JSON serializable by Python's standard `json` module.

Alternatively:

```python
json.dumps(
    payload.model_dump(mode="json")
).encode("utf-8")
```

can be used.

## Kafka Offset Management

Kafka consumers use manual offset commits:

```text
                    poll message
                         │
                         ▼
                  Process message
                         │
              ┌──────────┴──────────┐
              │                     │
           Failure               Success
              │                     │
              ▼                     ▼
       Do not commit         Update database
                                    │
                                    ▼
                              Commit offset
```

This provides **at-least-once processing semantics**.

If processing fails, the Kafka offset is not committed, allowing the message to be processed again.

The important rule is:

> Only commit the Kafka message after the corresponding business operation has completed successfully.

## Idempotency

Payout processing is designed to be safe against retries.

Payout requests use an idempotency key derived from the payout reference:

```http
Idempotency-Key: <reference_id>
```

This allows the same logical payout request to be safely retried without unintentionally creating multiple payouts.

Webhook processing should also be idempotent because webhook providers may retry events.

A webhook for the same payout may therefore be received more than once.

The database update should safely handle duplicate events.

## Tazapay Integration

The Payout Service communicates with Tazapay using HTTP Basic Authentication.

The payout request contains the required payout and beneficiary information and includes an idempotency key.

Example:

```text
Payout Service
      │
      │ HTTPS
      │ Basic Authentication
      │ Idempotency-Key
      ▼
Tazapay Payout API
      │
      ▼
Tazapay Payout
```

### Tazapay API Errors

HTTP errors from Tazapay are logged with the HTTP status and response body.

For example:

```text
Tazapay API error:
status=400
response=<error response>
```

The error is then propagated to the caller instead of being silently swallowed.

## Database

PostgreSQL is used to persist payout information and track payout status.

SQLAlchemy is used as the database ORM and Alembic is used for database migrations.

The payout record contains information such as:

* Internal payout/reference ID
* Tazapay payout ID
* Payout status
* Payment service ID
* Amount/currency information
* Other payout metadata

The Tazapay payout ID is used when processing webhook status updates.

## Database Transactions

Webhook processing should update the payout inside a database transaction.

The expected flow is:

```text
Kafka Message
     │
     ▼
Parse Webhook
     │
     ▼
Find Payout
     │
     ▼
Update Payout
     │
     ▼
Commit Database Transaction
     │
     ▼
Commit Kafka Offset
```

If the database transaction fails:

```text
Kafka Message
     │
     ▼
Database Update
     │
     X
 Transaction Failed
     │
     ▼
Kafka Offset NOT Committed
```

The message can then be retried.

## Reliability

The system uses several reliability mechanisms:

* Kafka `acks=all`
* Kafka producer idempotence
* Kafka producer retries
* Kafka message keys
* Manual Kafka offset commits
* At-least-once event processing
* Payout API idempotency keys
* PostgreSQL transactions
* Asynchronous payout processing
* Webhook-driven status updates
* Idempotent webhook processing

These mechanisms help protect the payout workflow against transient failures, duplicate messages, and retry scenarios.

## Local Development

### Prerequisites

Install the following:

* Python 3.13+
* PostgreSQL
* Apache Kafka
* Git

### Start Infrastructure

Start PostgreSQL and Kafka before starting the application services.

Kafka is expected to be available at:

```text
127.0.0.1:29092
```

PostgreSQL is expected to be available through the configured `DATABASE_URL`.

### Payout Service

```bash
cd payout-service

source .venv/bin/activate

uvicorn src.main:app --reload --port 8000
```

The service will be available at:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

### FinService

```bash
cd finservice

source .venv/bin/activate

uvicorn src.main:app --reload --port 8005
```

The service will be available at:

```text
http://localhost:8005
```

## Environment Variables

The Payout Service requires configuration similar to:

```env
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<database>

TAZAPAY_API_KEY=<your-api-key>
TAZAPAY_API_SECRET=<your-api-secret>
TAZAPAY_PAYOUT_ENDPOINT=<tazapay-payout-endpoint>

PAYOUT_TOPIC=payout_initiated
WEBHOOK_TOPIC=<webhook-topic>

PAYOUT_CONSUMER_GROUP=payout-consumer-group
WEBHOOK_CONSUMER_GROUP=webhook-consumer-group

KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:29092
```

Never commit API credentials or other secrets to source control.

Add `.env` to `.gitignore`:

```gitignore
.env
```

## Database Migrations

Alembic is used to manage database schema changes.

Create a migration:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback the latest migration:

```bash
alembic downgrade -1
```

## API

The Payout Service exposes the following primary endpoints:

```text
GET  /health
POST /webhook/tazapay
```

Additional payout endpoints may be exposed depending on the current application configuration.

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Project Structure

A simplified project structure:

```text
payout-service/
├── src/
│   ├── core/
│   │   ├── database.py
│   │   ├── producer.py
│   │   ├── payout_consumer.py
│   │   ├── webhook_consumer.py
│   │   └── settings.py
│   │
│   ├── models/
│   │   └── ...
│   │
│   ├── routes/
│   │   ├── payout.py
│   │   └── webhook.py
│   │
│   ├── schemas/
│   │   ├── payout.py
│   │   ├── payment_service.py
│   │   └── webhook.py
│   │
│   ├── services/
│   │   ├── payout.py
│   │   ├── tazapay.py
│   │   └── webhook.py
│   │
│   └── main.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
├── .env
├── .gitignore
├── alembic.ini
└── README.md
```

## Application Lifecycle

Both Kafka consumers are started with the FastAPI application lifecycle.

```text
FastAPI Startup
      │
      ├───────────────┐
      │               │
      ▼               ▼
Payout Consumer   Webhook Consumer
      │               │
      ▼               ▼
payout_initiated   webhook topic
      │               │
      └───────┬───────┘
              │
              ▼
       Application Running
              │
              ▼
       FastAPI Shutdown
              │
              ▼
       Stop Consumers
              │
              ▼
       Close Kafka Consumers
```

Consumers are stopped gracefully when the application shuts down.

## Consumer Processing

The payout consumer processes payout initiation events:

```text
Kafka
  │
  │ payout_initiated
  ▼
Payout Consumer
  │
  ▼
Validate Message
  │
  ▼
Call Tazapay
  │
  ▼
Persist Payout
  │
  ▼
Commit Kafka Offset
```

The webhook consumer processes Tazapay status updates:

```text
Kafka
  │
  │ webhook event
  ▼
Webhook Consumer
  │
  ▼
Validate Message
  │
  ▼
Find Payout
  │
  ▼
Update Status
  │
  ▼
Commit Transaction
  │
  ▼
Commit Kafka Offset
```

## Error Handling

Application errors should not be silently swallowed.

For Kafka consumers, a failed business operation should prevent the corresponding Kafka offset from being committed.

```text
Processing succeeds
        │
        ▼
Commit offset


Processing fails
        │
        ▼
Do not commit offset
        │
        ▼
Message can be retried
```

For webhook requests, if the event cannot be durably handed off to Kafka, the endpoint should return an error response rather than `200 OK`.

This allows the webhook provider to retry the event.

## Testing

Run the test suite with:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific test:

```bash
pytest tests/test_payout.py -v
```

## Tazapay Sandbox

The Tazapay sandbox is used for development and testing.

A payout request can be successfully submitted by the application but later require funding on the Tazapay side.

For example, the Tazapay dashboard may show:

```text
Requires Funding
```

This indicates a Tazapay account funding/balance issue rather than necessarily indicating a problem with:

* FastAPI
* Kafka
* PostgreSQL
* Pydantic validation
* The webhook consumer

Ensure the Tazapay sandbox account is appropriately provisioned before testing the complete payout lifecycle.

## End-to-End Flow

The complete system flow is:

```text
┌──────────────┐
│  FinService  │
└──────┬───────┘
       │
       │ payout request
       ▼
┌──────────────────────┐
│ Kafka                │
│ payout_initiated     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Payout Consumer      │
└──────────┬───────────┘
           │
           │ HTTP
           ▼
┌──────────────────────┐
│ Tazapay              │
│ Payout API           │
└──────────┬───────────┘
           │
           │ payout created
           ▼
┌──────────────────────┐
│ PostgreSQL            │
│ Initial Status        │
└──────────────────────┘

           Tazapay
              │
              │ webhook
              ▼
┌──────────────────────┐
│ FastAPI               │
│ /webhook/tazapay      │
└──────────┬───────────┘
           │
           │ publish
           ▼
┌──────────────────────┐
│ Kafka                 │
│ webhook topic         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Webhook Consumer      │
└──────────┬───────────┘
           │
           │ update status
           ▼
┌──────────────────────┐
│ PostgreSQL            │
│ Final Payout Status   │
└──────────────────────┘
```

## Design Goals

The project demonstrates the following backend engineering concepts:

* Event-driven architecture
* Asynchronous processing
* Kafka producers and consumers
* At-least-once message processing
* Idempotent payment operations
* Webhook processing
* Distributed system reliability
* Database transactions
* API integration
* Retry handling
* Message ordering
* Separation of concerns
* FastAPI application lifecycle management
* PostgreSQL persistence
* SQLAlchemy ORM
* Alembic migrations

## Future Improvements

Potential improvements include:

* Webhook signature verification
* Persistent webhook idempotency records
* Dead-letter Kafka topics
* Retry/backoff policies
* Kafka producer delivery confirmation
* Kafka consumer health/readiness checks
* Connection pooling for Tazapay HTTP clients
* Shared `aiohttp.ClientSession`
* Distributed tracing
* Metrics and observability
* Structured logging
* Prometheus/Grafana integration
* OpenTelemetry instrumentation
* Integration tests using Testcontainers
* Docker Compose for the complete local environment
* Automated CI/CD

```
```
