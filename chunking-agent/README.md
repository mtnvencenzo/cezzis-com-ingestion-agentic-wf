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

## Getting Started

### Prerequisites
- Python 3.12 through 3.14
- Poetry for dependency management
- Access to the local Kubernetes and Dapr development environment when using the recommended debug workflow

### Install Poetry

Install Poetry once for your Ubuntu user. You can run these commands from any directory:

```bash
sudo apt update
sudo apt install -y pipx
pipx ensurepath
```

Open a new terminal, then install Poetry and verify it:

```bash
pipx install poetry
poetry --version
```

`pipx` keeps Poetry and its own dependencies separate from the system Python and from project dependencies.

### Installation

Run the following commands from this repository's root directory, where `pyproject.toml` is located:

```bash
cd ~/Github/cezzis-com-accounts-api
poetry config virtualenvs.in-project true
poetry env use python3
```

This creates a separate `.venv` directory in the repository. Repeat these project setup commands for each Poetry repository; do not repeat the Poetry installation.

Install dependencies using the standard repository workflow:

```bash
make install
```

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