# Multi-stage build - use ubuntu with pre-installed tools for speed
FROM python:3.12-bullseye AS builder

# Setup poetry for build and dependency management
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create true
RUN poetry config installer.parallel true

# Set working directory
WORKDIR /app/src

# Copy only dependency files first (for better caching)
COPY ./pyproject.toml ./poetry.lock ./README.md ./
COPY ./src/cocktails_chunking_agent/ ./cocktails_chunking_agent/

# Install dependencies with caching optimizations
RUN poetry install --only=main

# Build the application
RUN poetry build -o dist -v

# Final stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy and install the built package efficiently
COPY --from=builder /app/src/dist/*.tar.gz ./
RUN pip install --no-cache-dir --disable-pip-version-check *.tar.gz && rm *.tar.gz

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run the application using the installed package
CMD ["cocktails_chunking_agent"]