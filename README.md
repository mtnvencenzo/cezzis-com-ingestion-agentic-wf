
# Cezzis.com Cocktails RAG Agent

> Part of the broader Cezzis.com digital experience for discovering and sharing cocktail recipes through AI-powered semantic search and retrieval-augmented generation.

[![CI](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/actions/workflows/cezzis-rag-data-extraction-cicd.yaml/badge.svg?branch=main)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/actions/workflows/cezzis-rag-data-extraction-cicd.yaml)
[![Release](https://img.shields.io/github/v/release/mtnvencenzo/cezzis-com-cocktails-rag-agent?include_prereleases)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/releases)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
[![Last commit](https://img.shields.io/github/last-commit/mtnvencenzo/cezzis-com-cocktails-rag-agent?branch=main)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/commits/main)
[![Issues](https://img.shields.io/github/issues/mtnvencenzo/cezzis-com-cocktails-rag-agent)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/issues)
[![Project](https://img.shields.io/badge/project-Cezzis.com%20Cocktails-181717?logo=github&logoColor=white)](https://github.com/users/mtnvencenzo/projects/2)
[![Website](https://img.shields.io/badge/website-cezzis.com-2ea44f?logo=google-chrome&logoColor=white)](https://www.cezzis.com)

**End-to-end Retrieval-Augmented Generation (RAG) solution for semantic search and AI-powered cocktail discovery on [cezzis.com](https://cezzis.com).**

## 📖 Overview

This repository contains multiple interconnected services that work together to provide advanced semantic search and conversational AI capabilities for cocktail discovery. The solution processes real-time cocktail updates, generates vector embeddings, and enables natural language queries over the entire cocktail database.

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Cocktails API  │─────▶│  Kafka/EventHub  │─────▶│ Data Extraction │
│                 │      │  (cocktails-topic)│      │     Agent       │
└─────────────────┘      └──────────────────┘      └────────┬────────┘
                                                              │
                                                              ▼
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   AI Services   │◀─────│  Vector Storage  │◀─────│   Embedding     │
│  (Ollama/TEI)   │      │    (Qdrant)      │      │    Pipeline     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────────┐
│     RAG Query Orchestrator (Future)     │
│  Semantic Search & Conversational Q&A   │
└─────────────────────────────────────────┘
```

## 🧩 Applications

### Data Ingestion

#### 📥 [Data Extraction Agent](./data-ingestion/data-extraction-agent)
**Status:** ✅ Active Development

A Kafka consumer that processes cocktail data updates in real-time:
- Consumes messages from Kafka topics
- Extracts and validates cocktail data
- Prepares data for vectorization
- Handles graceful shutdown and offset management

**Tech Stack:** Python 3.12, Kafka (confluent-kafka), Pydantic, pytest

**[View Documentation →](./data-ingestion/data-extraction-agent/README.md)**

### Vector Storage & Embeddings *(Coming Soon)*

#### 🔢 Embedding Pipeline
**Status:** 🚧 Planned

Generates high-quality vector embeddings for cocktail data:
- Integrates with TEI (Text Embeddings Inference)
- Uses BAAI/bge-m3 model for advanced embeddings
- Processes cocktail names, ingredients, descriptions
- Stores vectors in Qdrant

#### 💾 Vector Storage Service
**Status:** 🚧 Planned

Manages vector database operations:
- Qdrant vector database integration
- Similarity search capabilities
- Vector indexing and updates
- Query optimization

### Query & Retrieval *(Coming Soon)*

#### 🔍 Query Processor
**Status:** 🚧 Planned

Handles semantic search queries:
- Natural language query processing
- Vector similarity search
- Result ranking and filtering
- Context retrieval for RAG

#### 🤖 RAG Orchestrator
**Status:** 🚧 Planned

Coordinates retrieval and generation:
- Integrates with Ollama for LLM inference
- Combines retrieved context with user queries
- Generates conversational responses
- REST API for semantic search and Q&A

## 🧩 Cezzis.com Project Ecosystem

This RAG solution works alongside several sibling repositories:

- **cocktails-rag-agent** (this repo) – RAG solution for semantic search and AI-powered discovery
- [**cocktails-mcp**](https://github.com/mtnvencenzo/cezzis-com-cocktails-mcp) – Model Context Protocol server for AI agents
- [**cocktails-api**](https://github.com/mtnvencenzo/cezzis-com-cocktails-api) – ASP.NET Core backend and REST API
- [**cocktails-web**](https://github.com/mtnvencenzo/cezzis-com-cocktails-web) – React SPA for the public experience
- [**cocktails-common**](https://github.com/mtnvencenzo/cezzis-com-cocktails-common) – Shared libraries and utilities
- [**shared-infrastructure**](https://github.com/mtnvencenzo/shared-infrastructure) – Global Terraform modules

## ☁️ Cloud Infrastructure (Azure)

Infrastructure is provisioned with Terraform and deployed into Azure:

- **Azure Container Apps** – Hosts all microservices with auto-scaling
- **Azure Event Hubs / Kafka** – Event streaming for real-time data ingestion
- **Azure Container Registry** – Stores container images
- **Azure Key Vault** – Manages secrets and credentials
- **Azure Monitor** – Telemetry and observability via OpenTelemetry
- **Azure AI Search** *(planned)* – Alternative/complement to Qdrant for vector search

## ✨ Features

### Current (Data Extraction Agent)
- ✅ **Real-time Data Ingestion:** Kafka consumer for cocktail updates
- ✅ **Type-safe Configuration:** Pydantic-based settings with validation
- ✅ **Graceful Shutdown:** Proper signal handling and cleanup
- ✅ **Comprehensive Testing:** Unit tests with pytest and pytest-mock
- ✅ **CI/CD Pipeline:** Automated build, test, and deployment
- ✅ **Container Ready:** Docker and Kubernetes deployment

### Planned
- 🚧 **Semantic Search:** Vector similarity search for cocktails
- 🚧 **Conversational Q&A:** Natural language queries with LLM responses
- 🚧 **Advanced Embeddings:** BAAI/bge-m3 via TEI for high-quality vectors
- 🚧 **RAG Pipeline:** Full retrieval-augmented generation workflow
- 🚧 **API Gateway:** REST API for search and conversational interfaces
- 🚧 **Monitoring Dashboard:** Real-time metrics and observability

## 🛠️ Tech Stack

### Data Ingestion
- **Python 3.12+** – Modern Python with type hints
- **Apache Kafka** – Event streaming via confluent-kafka
- **Pydantic** – Configuration and data validation

### Vector & Embeddings (Planned)
- **Qdrant** – Vector database for similarity search
- **TEI (Text Embeddings Inference)** – Embedding service
- **BAAI/bge-m3** – State-of-the-art multilingual embeddings

### AI & Generation (Planned)
- **Ollama** – Local LLM inference
- **RAG Framework** – Custom retrieval-augmented generation

### Infrastructure
- **Azure Container Apps** – Serverless containers
- **Azure Event Hubs** – Managed Kafka
- **Azure Key Vault** – Secrets management
- **Terraform** – Infrastructure as Code
- **GitHub Actions** – CI/CD automation

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- Make (build automation)
- Azure CLI (for cloud deployment)

### Quick Start - Data Extraction Agent

1. **Clone the repository**
   ```bash
   git clone https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent.git
   cd cezzis-com-cocktails-rag-agent/data-ingestion/data-extraction-agent
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   ```bash
   # Create .env file
   cat > .env << EOF
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   KAFKA_CONSUMER_GROUP=extraction-group
   KAFKA_TOPIC_NAME=cocktails-topic
   EOF
   ```

5. **Run tests**
   ```bash
   make test
   ```

6. **Start the application**
   ```bash
   python src/app.py
   ```

For detailed setup and configuration, see the [Data Extraction Agent documentation](./data-ingestion/data-extraction-agent/README.md).


## 📦 CI/CD

GitHub Actions workflows automate:

- **Build & Test**: Run tests, linting, and code quality checks
- **Docker**: Build and push container images to ACR
- **Release**: Semantic versioning and GitHub releases
- **Deploy**: Deploy to Azure Container Apps (future)

See [`.github/workflows/`](./.github/workflows/) for pipeline definitions.


## 📄 License

This project is proprietary software. All rights reserved. See [LICENSE](LICENSE) for details.

---

**Part of the Cezzis.com Cocktails ecosystem – Empowering cocktail discovery through AI and semantic search 🍸**