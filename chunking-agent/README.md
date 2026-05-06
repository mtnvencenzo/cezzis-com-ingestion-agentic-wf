# Cocktails Chunking Agent

[Back to main README](../README.md)

The chunking agent consumes extraction results from Kafka and uses an Ollama-backed LLM to turn free-form cocktail text into structured semantic chunks.

## What It Does

- Consumes `CocktailExtractionModel` messages from Kafka.
- Sends extraction text to a LangChain agent backed by `ChatOllama`.
- Produces structured chunk objects with controlled categories such as ingredients, directions, flavor profile, variations, and historical context.
- Repairs malformed JSON model output when the first pass is invalid.
- Publishes `CocktailChunkingModel` payloads to the next Kafka topic for embedding.

## AI Stack

This service is LLM-driven.

- Model runtime: Ollama
- LangChain packages: `langchain`, `langchain-core`, `langchain-ollama`
- Tracing: `langfuse`
- Default configured model in checked-in local and Kubernetes config: `gemma4:31b`

Current checked-in model-related config includes:

- `CHUNKING_AGENT_LLM_MODEL=gemma4:31b`
- `CHUNKING_AGENT_LLM_MODEL_TEMPERATURE=0.0`
- `CHUNKING_AGENT_LLM_MODEL_NUM_CTX=4096`
- `CHUNKING_AGENT_LLM_MODEL_NUM_PREDICT=3072`
- `CHUNKING_AGENT_LLM_MODEL_TIMEOUT_SECONDS=90`
- `CHUNKING_AGENT_LLM_MODEL_REASONING=false`

The chunking implementation validates allowed categories and retries once with a repair prompt if the first model response is not valid JSON.

## Runtime Stack

- Python 3.12
- Poetry
- Pydantic Settings
- Kafka via `confluent-kafka` and `cezzis-kafka`
- OpenTelemetry via `cezzis-otel`
- Mediatr
- Injector
- HTTPX

## Configuration

Configuration is loaded from `.env` and `.env.${ENV}`.

Core settings:

- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_CONSUMER_GROUP`
- `CHUNKING_AGENT_ENABLED`
- `CHUNKING_AGENT_KAFKA_TOPIC_NAME`
- `CHUNKING_AGENT_KAFKA_RESULTS_TOPIC_NAME`
- `CHUNKING_AGENT_KAFKA_NUM_CONSUMERS`
- `CHUNKING_AGENT_KAFKA_MAX_POLL_INTERVAL_MS`
- `CHUNKING_AGENT_KAFKA_AUTO_OFFSET_RESET`
- `LLM_HOST`
- `LANGFUSE_BASE_URL`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

## Local Development

```bash
cd chunking-agent
poetry install --with dev
poetry run pytest -v test/
poetry run cocktails-chunking-agent
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
cocktails-chunking-agent
```

## Docker

The Docker image is built from a multi-stage Dockerfile.

- Builder image: `python:3.12-bullseye`
- Runtime image: `python:3.12-slim`
- Container entrypoint: `cocktails-chunking-agent`

## CI/CD

The workflow at `.github/workflows/chunking-agent-cicd.yaml`:

- computes a semantic version with GitVersion
- runs build and test steps through a shared Python workflow
- builds and pushes the container image to Azure Container Registry
- creates a release on `main`

Published image repository:

- `acrveceusgloshared001.azurecr.io/cocktailsingestionchunkingagent`

## Deployment

This service is deployed with Argo CD and Kubernetes manifests under `.iac/`.

### CloudSync

Deploy:

```bash
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync.yaml
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-cloudsync.yaml
```

Remove:

```bash
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-cloudsync.yaml
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-cloudsync.yaml
```

### Local

Deploy:

```bash
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc.yaml
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-loc.yaml
```

Remove:

```bash
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/cezzis-cocktails-chunking-agent-loc.yaml
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/chunking-agent/.iac/argocd/image-updater-loc.yaml
```