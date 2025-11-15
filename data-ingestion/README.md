# Cezzis.com Cocktails RAG - Data Ingestion Agentic Workflow

> Intelligent multi-agent system for processing cocktail data in the Cezzis.com RAG solution.

[![CI](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/actions/workflows/cezzis-data-ingestion-agentic-wf-cicd.yaml/badge.svg?branch=main)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/actions/workflows/cezzis-data-ingestion-agentic-wf-cicd.yaml)
[![Release](https://img.shields.io/github/v/release/mtnvencenzo/cezzis-com-cocktails-rag-agent?include_prereleases)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
[![Last commit](https://img.shields.io/github/last-commit/mtnvencenzo/cezzis-com-cocktails-rag-agent?branch=main)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/commits/main)
[![Issues](https://img.shields.io/github/issues/mtnvencenzo/cezzis-com-cocktails-rag-agent)](https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent/issues)
[![Project](https://img.shields.io/badge/project-Cezzis.com%20Cocktails-181717?logo=github&logoColor=white)](https://github.com/users/mtnvencenzo/projects/2)
[![Website](https://img.shields.io/badge/website-cezzis.com-2ea44f?logo=google-chrome&logoColor=white)](https://www.cezzis.com)

An intelligent agentic workflow system that processes cocktail data updates through a multi-agent pipeline. Each agent specializes in different aspects of data processing, from extraction and validation to embedding generation, creating a robust and scalable RAG data ingestion solution.

## 🤖 Agentic Workflow Architecture

The system implements an **agentic workflow** pattern with specialized agents:

### 🔍 **Extraction Agent**
- **Purpose**: Consumes raw cocktail data from Kafka, validates and cleanses it
- **Input**: `cocktails-update-topic` (JSON arrays from Cezzis API)
- **Processing**: Schema validation, data cleaning, error handling
- **Output**: Clean cocktail data to `cocktails-embeddings-topic`

### 🧠 **Embedding Agent** 
- **Purpose**: Processes cleaned data for vector embeddings and semantic search
- **Input**: `cocktails-embeddings-topic` (validated cocktail models)
- **Processing**: Text preparation for embedding, metadata extraction
- **Output**: Prepared for vector database storage

### 🔄 **Agent Orchestration**
- Both agents run concurrently using `asyncio.gather()`
- Built-in **OpenTelemetry** tracing for distributed observability
- **Kafka-based** communication with automatic retry and error handling
- **Graceful shutdown** handling with proper cleanup


## 🧩 Cezzis.com RAG Ecosystem

This application is part of a multi-service RAG solution:

- **data-ingestion-agentic-workflow** (this app) – Multi-agent pipeline for processing cocktail data
  - *Extraction Agent* – Data validation and cleaning
  - *Embedding Agent* – Vector embedding preparation
- **vector-storage** *(coming soon)* – Manages vector embeddings and similarity search
- **query-processor** *(coming soon)* – Handles semantic search queries and retrieval
- **rag-orchestrator** *(coming soon)* – Coordinates retrieval and generation for AI responses

Related repositories:
- [**cocktails-api**](https://github.com/mtnvencenzo/cezzis-com-cocktails-api) – ASP.NET Core backend and REST API
- [**cocktails-mcp**](https://github.com/mtnvencenzo/cezzis-com-cocktails-mcp) – Model Context Protocol server for AI agents
- [**cocktails-web**](https://github.com/mtnvencenzo/cezzis-com-cocktails-web) – React SPA for the public experience
- [**shared-infrastructure**](https://github.com/mtnvencenzo/shared-infrastructure) – Global Terraform modules

## ☁️ Cloud-Native Infrastructure (Azure)

Infrastructure is provisioned with Terraform and deployed into Azure:

- **Azure Container Apps** – Hosts the agentic workflow with auto-scaling
- **Azure Event Hubs / Apache Kafka** – Event streaming platform for cocktail updates
- **Azure Container Registry** – Stores container images published from CI/CD
- **Azure Key Vault** – Secure secrets management (Kafka credentials, OTEL tokens)
- **Azure Monitor + OpenTelemetry** – Distributed tracing and observability across agents
- **Azure AI Search** *(future)* – Vector storage and semantic search capabilities

## 🔄 Data Flow

```
Cocktails API → Kafka Topic → Extraction Agent → Embedding Agent → Vector Store
                   ↑              ↓                    ↓
            (update-topic)  (validation &         (embedding
                           transformation)      preparation)
                              ↓
                      (embeddings-topic)
```

### Processing Pipeline:
1. **Ingest**: Cocktails API publishes data updates to `cocktails-update-topic`
2. **Extract**: Extraction Agent validates and cleanses incoming data
3. **Transform**: Data normalized using auto-generated Pydantic models from OpenAPI spec
4. **Route**: Clean data forwarded to `cocktails-embeddings-topic`
5. **Prepare**: Embedding Agent prepares data for vector generation
6. **Output**: Processed data ready for vector storage and semantic search

### Agent Communication:
- **Asynchronous** processing with proper backpressure handling
- **Distributed tracing** via OpenTelemetry for end-to-end observability  
- **Error isolation** - failures in one agent don't affect others
- **Scalable** - each agent can be scaled independently

## 🛠️ Technology Stack

### Core Framework
- **Language**: Python 3.12+
- **Architecture**: Multi-agent agentic workflow with asyncio orchestration
- **Configuration**: Pydantic Settings with type-safe environment variable handling
- **Message Streaming**: Apache Kafka via confluent-kafka with async processing
- **Data Models**: Auto-generated from Cezzis API OpenAPI specification

### Agent Infrastructure
- **Agent Communication**: Kafka-based event streaming between extraction and embedding agents
- **Observability**: OpenTelemetry with distributed tracing and structured logging
- **Error Handling**: Graceful degradation with individual agent error isolation
- **Concurrency**: Async/await patterns with configurable consumer scaling

### Development & Deployment
- **Build System**: Poetry for dependency management with multi-stage Docker builds
- **Testing**: pytest with pytest-mock for comprehensive unit test coverage
- **Code Quality**: ruff for linting and formatting with type checking via mypy
- **CI/CD**: GitHub Actions with automated testing, containerization, and Azure deployment

## 🏗️ Project Structure

```text
data-ingestion/
├── data_ingestion_agentic_workflow/
│   ├── app.py                          # Main orchestrator - runs both agents
│   ├── agents/                         # Agent implementations
│   │   ├── extraction_agent/
│   │   │   ├── ext_agent_runner.py      # Extraction agent entry point
│   │   │   ├── ext_agent_options.py     # Extraction agent configuration
│   │   │   ├── ext_agent_evt_receiver.py   # Kafka message processing logic
│   │   │   └── test_*.py                    # Unit tests for extraction agent
│   │   └── embedding_agent/
│   │       ├── emb_agent_runner.py      # Embedding agent entry point
│   │       ├── emb_agent_options.py     # Embedding agent configuration
│   │       └── emb_agent_evt_receiver.py   # Kafka message processing logic
│   ├── models/
│   │   └── cocktail_models.py              # Auto-generated from Cezzis API OpenAPI
│   └── behaviors/
│       └── otel/                           # OpenTelemetry configuration
│           └── otel_options.py
├── pyproject.toml                     # Poetry project configuration
├── poetry.lock                        # Locked dependency versions
├── Dockerfile                         # Multi-stage production container
├── .dockerignore                      # Docker build exclusions
├── .ruff.toml                        # Code formatting and linting config
├── pytest.ini                        # Test runner configuration
├── makefile                          # Development automation
└── README.md                         # This file
```

### Key Components:
- **🎯 app.py**: Main orchestrator that launches both agents concurrently
- **🤖 agents/**: Self-contained agent implementations with individual configurations
- **📊 models/**: Auto-generated Pydantic models from the Cezzis API OpenAPI specification
- **🔍 behaviors/**: Cross-cutting concerns like observability and configuration

## 🚀 Development Setup

### 1) Prerequisites
- **Python 3.12+** - Required for the agentic workflow
- **Poetry** - For dependency management (automatically installs if using Make)
- **Docker & Docker Compose** - For local Kafka and containerized testing
- **Make** - For development automation
- **Optional**: Azure CLI for cloud deployment

### 2) Quick Start
```bash
# Clone and enter the project
git clone https://github.com/mtnvencenzo/cezzis-com-cocktails-rag-agent.git
cd cezzis-com-cocktails-rag-agent/data-ingestion

# Install dependencies and run tests
make all

# Generate fresh data models from Cezzis API
make models
```

### 3) Manual Setup
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Generate models from Cezzis API OpenAPI spec
poetry run datamodel-codegen \
    --url "https://api.cezzis.com/prd/cocktails/api-docs/v1/scalar/v1/openapi.json" \
    --input-file-type openapi \
    --output data_ingestion_agentic_workflow/models/cocktail_models.py \
    --output-model-type pydantic_v2.BaseModel \
    --field-constraints --use-default \
    --use-schema-description \
    --target-python-version 3.12
```

### 4) Environment Configuration
Create a `.env.local` file for local development:

```env
# Required: Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=cezzis-ingestion-agentic-workflow
KAFKA_EXTRACTION_TOPIC_NAME=cocktails-update-topic
KAFKA_EMBEDDING_TOPIC_NAME=cocktails-embeddings-topic
KAFKA_NUM_CONSUMERS=1

# Required: OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=cezzis-ingestion-agentic-workflow
OTEL_SERVICE_NAMESPACE=cezzis
OTEL_OTLP_AUTH_HEADER=Bearer your-token-here

# Optional: Environment
ENV=local
```

## 🧪 Testing & Code Quality

### Running Tests
```bash
# Run all tests with coverage
make test

# Run tests with coverage reporting
make coverage

# Run tests for a specific agent
poetry run pytest data_ingestion_agentic_workflow/agents/extraction_agent/test_*.py -v

# Run with verbose output and specific patterns
poetry run pytest -v -k "extraction"
```

### Code Quality Checks
```bash
# Format and lint code
make standards

# Run individual tools
make lint     # Run ruff linting
make format   # Run ruff formatting

# Type checking (via pyright in IDE or manually)
poetry run mypy data_ingestion_agentic_workflow/
```

### Coverage Reports
Coverage reports are generated in:
- **Terminal**: Summary during test runs
- **XML**: `coverage.xml` for CI/CD systems
- **HTML**: `htmlcov/index.html` for detailed browsing

### Test Structure
- **Unit Tests**: Individual agent functionality testing
- **Integration Tests**: Agent-to-agent communication
- **Configuration Tests**: Environment variable validation
- **Mocking**: Kafka consumers and producers for isolated testing

## 📋 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | Yes | - | Kafka broker addresses (comma-separated) |
| `KAFKA_CONSUMER_GROUP` | Yes | - | Consumer group ID for both agents |
| `KAFKA_EXTRACTION_TOPIC_NAME` | Yes | - | Topic for raw cocktail data (input) |
| `KAFKA_EMBEDDING_TOPIC_NAME` | Yes | - | Topic for processed data (between agents) |
| `KAFKA_NUM_CONSUMERS` | No | `1` | Number of consumer instances per agent |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Yes | - | OpenTelemetry OTLP exporter endpoint |
| `OTEL_SERVICE_NAME` | Yes | - | Service name for telemetry |
| `OTEL_SERVICE_NAMESPACE` | Yes | - | Service namespace for telemetry |
| `OTEL_OTLP_AUTH_HEADER` | Yes | - | Authorization header for OTLP |
| `ENV` | No | `unknown` | Environment identifier (local, dev, prod) |

### Pydantic Settings

Configuration is managed via agent-specific options classes:
- **Type-safe** configuration with validation
- **Environment-specific** `.env` file loading (`.env.{ENV}`)
- **Singleton pattern** for configuration caching
- **Validation** ensures all required settings are provided

## 🐳 Docker Deployment

### Pull models into Ollama
```bash
docker exec ollama ollama pull llama3.2:3b
```


### Building and Running Locally
```bash
# Build optimized production image
docker build -t cezzis-ingestion-agentic-workflow:latest .

# Run with environment configuration
docker run -d \
  -e ENV=local \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318 \
  -e OTEL_SERVICE_NAME=cezzis-ingestion-agentic-workflow \
  -e OTEL_SERVICE_NAMESPACE=cezzis \
  -e OTEL_OTLP_AUTH_HEADER="Bearer 00d164bd-2d3d-4d62-8280-e507637def73" \
  -e KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:39092 \
  -e KAFKA_CONSUMER_GROUP=cezzis-ingestion-agentic-workflow \
  -e KAFKA_EXTRACTION_TOPIC_NAME=cocktails-update-topic \
  -e KAFKA_EMBEDDING_TOPIC_NAME=cocktails-embeddings-topic \
  -e KAFKA_NUM_CONSUMERS=1 \
  -e OLLAMA_HOST=host.docker.internal:11434 \
  --name cezzis-ingestion-agentic-workflow \
  cezzis-ingestion-agentic-workflow:latest
```

### Running from Azure Container Registry
```bash
# Authenticate with Azure
az login
az acr login -n acrveceusgloshared001

# Run production image
docker run -d \
  -e ENV=local \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318 \
  -e OTEL_SERVICE_NAME=cezzis-ingestion-agentic-workflow \
  -e OTEL_SERVICE_NAMESPACE=cezzis \
  -e OTEL_OTLP_AUTH_HEADER="Bearer 00d164bd-2d3d-4d62-8280-e507637def73" \
  -e KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:39092 \
  -e KAFKA_CONSUMER_GROUP=cezzis-ingestion-agentic-workflow \
  -e KAFKA_EXTRACTION_TOPIC_NAME=cocktails-update-topic \
  -e KAFKA_EMBEDDING_TOPIC_NAME=cocktails-embeddings-topic \
  -e KAFKA_NUM_CONSUMERS=1 \
  -e OLLAMA_HOST=host.docker.internal:11434 \
  --name cezzis-ingestion-agentic-workflow \
  acrveceusgloshared001.azurecr.io/cocktailsdataingestionagenticwf:latest
```

### Docker Optimizations
The Dockerfile uses **multi-stage builds** for optimal performance:
- **Builder stage**: Uses `python:3.12-bullseye` with build tools pre-installed
- **Production stage**: Minimal `python:3.12-slim` for smaller runtime footprint
- **Poetry optimization**: Dependencies installed with `--only=main` and parallel processing
- **Layer caching**: Dependency installation separated from code changes for faster rebuilds
## 🤝 Development Workflow

### Make Commands
The project includes a comprehensive `makefile` for development automation:

```bash
make install     # Install all dependencies via Poetry
make update      # Update all dependencies to latest versions
make build       # Build the Python package
make lint        # Run ruff linting with automatic fixes
make format      # Format code with ruff
make standards   # Run both linting and formatting
make test        # Run all tests
make coverage    # Run tests with detailed coverage reporting
make models      # Generate fresh data models from Cezzis API
make all         # Install → models → standards → coverage → build
```

### Data Model Regeneration
The cocktail data models are auto-generated from the Cezzis API OpenAPI specification:

```bash
# Regenerate models when the API changes
make models

# Manual generation with custom parameters
poetry run datamodel-codegen \
    --url "https://api.cezzis.com/prd/cocktails/api-docs/v1/scalar/v1/openapi.json" \
    --input-file-type openapi \
    --output data_ingestion_agentic_workflow/models/cocktail_models.py \
    --output-model-type pydantic_v2.BaseModel \
    --field-constraints --use-default
```

### CI/CD Pipeline
GitHub Actions workflow (`cezzis-data-ingestion-agentic-wf-cicd.yaml`):
- **📦 Build**: Poetry dependency installation and package building
- **🧪 Test**: Comprehensive test suite with coverage reporting
- **📊 Quality**: Code linting and formatting checks
- **🐳 Docker**: Multi-stage container build and push to Azure Container Registry
- **🚀 Release**: Automatic GitHub releases on main branch

## 📄 License

This project is licensed under the MIT License. All rights reserved. See [LICENSE](../../LICENSE) for details.

---

**Part of the Cezzis.com Cocktails ecosystem – Empowering cocktail discovery through intelligent agentic workflows 🍸🤖**
