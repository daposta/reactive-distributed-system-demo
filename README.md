## Running the Services

This project consists of two FastAPI services that communicate through Apache Kafka.

### Services

| Service | Description | Port |
|---|---|---|
| Payout Service | REST API, Kafka Producer, and Kafka Consumer | `8000` |
| FinService | REST API and Kafka Producer | `8005` |

### Architecture

```text
┌─────────────────────────────┐
│       Payout Service        │
│          Port 8000          │
│                             │
│  - REST API                 │
│  - Kafka Producer           │
│  - Kafka Consumer           │
└──────────────┬──────────────┘
               │
               │ Apache Kafka
               │
       ┌───────┴────────┐
       │                │
payout_initiate   payout_initiated
       │                │
       └───────┬────────┘
               │
┌──────────────▼──────────────┐
│         FinService          │
│          Port 8005          │
│                             │
│  - REST API                 │
│  - Kafka Producer           │
└─────────────────────────────┘
