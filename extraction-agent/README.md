# Cocktails Extraction Agent

[Back to main README](../README.md)

The extraction agent consumes cocktail update events, fetches the latest cocktail record from the Cocktails API, cleans the content, and publishes extraction results for downstream chunking.

## What It Does

- Consumes cocktail update messages from Kafka.
- Fetches the authoritative cocktail payload from the Cocktails API.
- Prevents duplicate near-term processing with a configurable cooldown.
- Produces cleaned plain-text extraction content.
- Publishes `CocktailExtractionModel` payloads back to Kafka.

## AI Stack

This service has both deterministic and AI-assisted cleaning paths.

### Deterministic Cleaning Path

When `EXTRACTION_AGENT_USE_LLM=false`, the agent uses built-in tools to clean content without a model:

- markdown removal
- HTML tag removal
- emoji removal
- JSON special character cleanup

This path is currently what the checked-in local Kubernetes config enables.

### AI-Assisted Cleaning Path

When `EXTRACTION_AGENT_USE_LLM=true`, the agent switches to an MCP-backed LLM workflow.

- Model runtime: Ollama
- LangChain packages: `langchain`, `langchain-core`, `langchain-community`, `langchain-ollama`
- Graph orchestration: `langgraph`
- MCP integration: `langchain-mcp-adapters`, `mcp`
- Tracing: `langfuse`
- Default configured model in checked-in local and Kubernetes config: `gemma4:31b`
- Default MCP transport in checked-in config: `streamable_http`

The LLM cleaner builds a LangGraph workflow, binds tools exposed by the MCP server, and iterates through tool calls until it has final cleaned text or reaches its safety limit.

Current checked-in model-related config includes:

- `EXTRACTION_AGENT_LLM_MODEL=gemma4:31b`
- `EXTRACTION_AGENT_LLM_MODEL_TEMPERATURE=0.0`
- `EXTRACTION_AGENT_LLM_MODEL_NUM_CTX=8196`
- `EXTRACTION_AGENT_LLM_MODEL_NUM_PREDICT=1024`
- `EXTRACTION_AGENT_LLM_GRAPH_TIMEOUT_SECONDS=90`
- `EXTRACTION_AGENT_LLM_MODEL_REASONING=false`

## Runtime Stack

- Python 3.12
- Poetry
- Pydantic Settings
- Kafka via `confluent-kafka` and `cezzis-kafka`
- OpenTelemetry via `cezzis-otel`
- HTTPX
- Mediatr
- Injector
- Cocktails API generated client models

## Configuration

Configuration is loaded from `.env` and `.env.${ENV}`.

Core settings:

- `COCKTAILS_API_BASE_URL`
- `COCKTAILS_API_X_KEY`
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_CONSUMER_GROUP`
- `EXTRACTION_AGENT_ENABLED`
- `EXTRACTION_AGENT_KAFKA_TOPIC_NAME`
- `EXTRACTION_AGENT_KAFKA_RESULTS_TOPIC_NAME`
- `EXTRACTION_AGENT_KAFKA_NUM_CONSUMERS`
- `EXTRACTION_AGENT_KAFKA_MAX_POLL_INTERVAL_MS`
- `EXTRACTION_AGENT_KAFKA_AUTO_OFFSET_RESET`
- `EXTRACTION_AGENT_COCKTAIL_REPROCESS_COOLDOWN_SECONDS`
- `EXTRACTION_AGENT_USE_LLM`
- `LLM_HOST`
- `EXTRACTION_AGENT_LLM_MCP_URL`
- `EXTRACTION_AGENT_LLM_MCP_TRANSPORT`
- `LANGFUSE_BASE_URL`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

## Local Development

```bash
cd extraction-agent
poetry install --with dev
poetry run pytest -v test/
poetry run cocktails-extraction-agent
```

Useful commands:

```bash
make install
make lint
make format
make test
make coverage
make build
```

The package exposes the console script:

```bash
cocktails-extraction-agent
```

## Docker

The Docker image is built from a multi-stage Dockerfile.

- Builder image: `python:3.12-bullseye`
- Runtime image: `python:3.12-slim`
- Container entrypoint: `cocktails-extraction-agent`

## CI/CD

The workflow at `.github/workflows/extraction-agent-cicd.yaml`:

- computes a semantic version with GitVersion
- runs build and tests through a shared Python workflow
- builds and pushes the container image to Azure Container Registry
- creates a release on `main`

Published image repository:

- `acrveceusgloshared001.azurecr.io/cocktailsingestionextractionagent`

## Deployment

This service is deployed with Argo CD and Kubernetes manifests under `.iac/`.

### CloudSync

Deploy:

```bash
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync.yaml
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-cloudsync.yaml
```

Remove:

```bash
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-cloudsync.yaml
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-cloudsync.yaml
```

### Local

Deploy:

```bash
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc.yaml
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-loc.yaml
```

Remove:

```bash
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/cezzis-cocktails-extraction-agent-loc.yaml
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/extraction-agent/.iac/argocd/image-updater-loc.yaml
```

The Argo CD Application manifests include the `resources-finalizer.argocd.argoproj.io` finalizer, so deleting the Application also cascades deletion of the managed Kubernetes resources.