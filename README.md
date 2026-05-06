
# Cezzis.com Ingestion Agentic Workflow

This repository contains the three services that process cocktail updates into cleaned text, semantic chunks, and embedding requests for downstream search.

## Overview

The pipeline is event-driven and Kafka-based.

1. The extraction agent consumes cocktail update events, fetches the latest cocktail record from the Cocktails API, and produces cleaned extraction text.
2. The chunking agent consumes extraction results and uses an LLM to break the content into category-based chunks.
3. The embedding agent consumes chunking results and submits them to the AI Search embeddings API.

Each service is a standalone Python 3.12 application packaged with Poetry, containerized with Docker, and deployed through Argo CD into Kubernetes.

## Architecture Diagram
![Cezzis platform architecture](./.assets/cezzis-com-agentic-wf.drawio.svg)

## Applications

### Extraction Agent

Location: `extraction-agent/`

Read more: [Extraction Agent README](./extraction-agent/README.md)

- Consumes cocktail update events from Kafka.
- Fetches canonical cocktail content from the Cocktails API.
- Supports two cleaning modes.
- Deterministic cleaning mode removes markdown, HTML, emojis, and JSON-hostile characters.
- Optional AI cleaning mode uses LangChain, LangGraph, Ollama, and MCP tools.
- Publishes cleaned extraction payloads back to Kafka.

### Chunking Agent

Location: `chunking-agent/`

Read more: [Chunking Agent README](./chunking-agent/README.md)

- Consumes extraction results from Kafka.
- Uses an Ollama-hosted chat model through LangChain to generate structured content chunks.
- Validates and repairs model JSON output before publishing results.
- Publishes categorized chunk payloads back to Kafka for embedding.

### Embedding Agent

Location: `embedding-agent/`

Read more: [Embedding Agent README](./embedding-agent/README.md)

- Consumes chunking results from Kafka.
- Maps chunked cocktail payloads into the AI Search embedding request contract.
- Authenticates with OAuth machine-to-machine credentials and an API key.
- Sends embedding payloads to the AI Search API.

## AI Stack

The AI-heavy parts of this repository are the extraction and chunking agents.

### Extraction AI

- `langchain`, `langchain-core`, `langchain-community`, and `langchain-ollama` drive model interaction.
- `langgraph` coordinates the extraction cleaning flow.
- `langchain-mcp-adapters` and `mcp` connect the agent to MCP tools over URL-based transports.
- `langfuse` records traces for LLM calls.
- The checked-in local and Kubernetes config uses `gemma4:31b` as the configured Ollama model.
- The current checked-in local Kubernetes overlay sets `EXTRACTION_AGENT_USE_LLM=false`, so the AI path is implemented but not enabled by default in that environment.

### Chunking AI

- `langchain`, `langchain-core`, and `langchain-ollama` are used for chunk generation.
- The chunking flow runs against Ollama via `ChatOllama`.
- `langfuse` is used for tracing and observability.
- The checked-in local and Kubernetes config uses `gemma4:31b` as the configured chunking model.

### Embedding AI Integration

- The embedding agent does not host or invoke a local embedding model in this repository.
- Instead, it forwards chunked payloads to the AI Search embeddings endpoint at `/api/v1/search/embeddings`.
- Authentication is handled with `cezzis-oauth` and `authlib` plus the configured AI Search API key.

## Tech Stack

### Application Runtime

- Python 3.12
- Poetry
- Pydantic Settings
- Injector
- Mediatr
- HTTPX

### Eventing and Observability

- Apache Kafka
- `confluent-kafka`
- `cezzis-kafka`
- OpenTelemetry
- `cezzis-otel`

### AI and Content Processing

- Ollama
- LangChain
- LangGraph
- Langfuse
- MCP

### Delivery and Deployment

- Docker multi-stage builds
- GitHub Actions
- GitVersion
- Argo CD
- Kubernetes kustomize overlays
- External Secrets
- Azure Container Registry
- Terraform for the embedding agent infrastructure slice under `embedding-agent/.iac/terraform`

## Repository Layout

```text
.
├── chunking-agent/
├── embedding-agent/
├── extraction-agent/
├── .github/workflows/
└── GitVersion.yml
```

Each application contains:

- a `pyproject.toml` package definition
- a `makefile` for install, lint, test, coverage, build, and client code generation tasks
- a Dockerfile
- Kubernetes manifests under `.iac/`
- an application-specific README

## Local Development

Each service loads configuration from `.env` and `.env.${ENV}` through `pydantic-settings`.

Typical workflow per application:

```bash
cd extraction-agent
poetry install --with dev
poetry run pytest -v test/
poetry run cocktails-extraction-agent
```

Console entrypoints:

- `cocktails-extraction-agent`
- `cocktails-chunking-agent`
- `cocktails-embedding-agent`

Useful make targets in each application:

- `make install`
- `make lint`
- `make format`
- `make test`
- `make coverage`
- `make build`

## Deployment

The current deployment model in this repository is Kubernetes-centered.

- Each application has Argo CD application manifests for `loc` and `cloudsync` environments.
- Each application has kustomize-managed Kubernetes manifests under `.iac/k8s-loc` and `.iac/k8s-cloudsync`.
- Container images are built in GitHub Actions and pushed to Azure Container Registry.
- The embedding agent workflow also runs Terraform from `embedding-agent/.iac/terraform`.

GitHub Actions workflows:

- `.github/workflows/extraction-agent-cicd.yaml`
- `.github/workflows/chunking-agent-cicd.yaml`
- `.github/workflows/embedding-agent-cicd.yaml`

## Application Docs

- `extraction-agent/README.md`
- `chunking-agent/README.md`
- `embedding-agent/README.md`

## License

This repository is proprietary software. See `LICENSE`.