# Stage 1: Build stage with Poetry
FROM python:3.10-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only files needed for dependency installation
COPY poetry.lock pyproject.toml ./

# Install dependencies
# --no-root: Don't install the project itself, only dependencies
# --no-dev: Don't install development dependencies
RUN poetry install --no-root --no-dev

# Stage 2: Final production image
FROM python:3.10-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Set the PATH to include the venv's bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application code
COPY ./app ./app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
