# Cocktails Embedding Agent

[Back to main README](../README.md)

The embedding agent consumes chunked cocktail content from Kafka and forwards it to the AI Search embeddings API.

## What It Does

- Consumes `CocktailChunkingModel` messages from Kafka.
- Filters empty chunks before processing.
- Maps chunk payloads into the generated AI Search request models.
- Authenticates with OAuth machine-to-machine tokens.
- Calls the AI Search embeddings endpoint with both bearer auth and `X-Key`.

## AI Integration

This service is AI-adjacent rather than model-hosting.

- It does not run a local embedding model from this repository.
- It sends content to the AI Search API endpoint at `/api/v1/search/embeddings`.
- The embedding request includes structured cocktail metadata and categorized chunks.
- Authentication uses `cezzis-oauth`, `authlib`, and an API key.

That means the model implementation lives behind the AI Search service, while this agent is responsible for event ingestion, request shaping, and authenticated delivery.

## Runtime Stack

- Python 3.12
- Poetry
- Pydantic Settings
- Kafka via `confluent-kafka` and `cezzis-kafka`
- OpenTelemetry via `cezzis-otel`
- HTTPX
- OAuth via `cezzis-oauth` and `authlib`
- Mediatr
- Injector

## Configuration

Configuration is loaded from `.env`, `.env.${ENV}`, and for AI Search options also `.env.loc`.

Core settings:

- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_CONSUMER_GROUP`
- `EMBEDDING_AGENT_ENABLED`
- `EMBEDDING_AGENT_KAFKA_TOPIC_NAME`
- `EMBEDDING_AGENT_KAFKA_NUM_CONSUMERS`
- `EMBEDDING_AGENT_KAFKA_MAX_POLL_INTERVAL_MS`
- `EMBEDDING_AGENT_KAFKA_AUTO_OFFSET_RESET`
- `AISEARCH_API_BASE_URL`
- `AISEARCH_API_TIMEOUT_SECONDS`
- `AISEARCH_API_KEY`
- `OAUTH_DOMAIN`
- `OAUTH_CLIENT_ID`
- `OAUTH_AUDIENCE`
- `OAUTH_WRITE_EMBEDDINGS_SCOPE`

The checked-in local config points the agent at the Cezzis AI Search service and uses `write:embeddings` as the configured OAuth scope.

## Local Development

```bash
cd embedding-agent
poetry install --with dev
poetry run pytest -v test/
poetry run cocktails-embedding-agent
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
cocktails-embedding-agent
```

## Docker

The Docker image is built from a multi-stage Dockerfile.

- Builder image: `python:3.12-bullseye`
- Runtime image: `python:3.12-slim`
- Container entrypoint: `cocktails-embedding-agent`

## CI/CD

The workflow at `.github/workflows/embedding-agent-cicd.yaml`:

- computes a semantic version with GitVersion
- runs build and tests through a shared Python workflow
- builds and pushes the container image to Azure Container Registry
- applies Terraform from `embedding-agent/.iac/terraform`
- creates a release on `main`

Published image repository:

- `acrveceusgloshared001.azurecr.io/cocktailsingestionembeddingagent`

## Deployment

This service is deployed with Argo CD and Kubernetes manifests under `.iac/`.

### CloudSync

Deploy:

```bash
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-cloudsync.yaml
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/image-updater-cloudsync.yaml
```

Remove:

```bash
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-cloudsync.yaml
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/image-updater-cloudsync.yaml
```

### Local

Deploy:

```bash
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-loc.yaml
kubectl apply -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/image-updater-loc.yaml
```

Remove:

```bash
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/cezzis-cocktails-embedding-agent-loc.yaml
kubectl delete -f https://raw.githubusercontent.com/mtnvencenzo/cezzis-com-ingestion-agentic-wf/refs/heads/main/embedding-agent/.iac/argocd/image-updater-loc.yaml
```