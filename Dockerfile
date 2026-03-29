# Reverting to the official OpenEnv base image to restore the dashboard
FROM ghcr.io/meta-pytorch/openenv-base:latest

WORKDIR /app

# Copy the entire project
COPY . /app

# Install dependencies directly on top of the base
RUN pip install --no-cache-dir openenv-core uvicorn fastapi

# Set PYTHONPATH to include /app so server.app can be imported
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose HuggingFace Spaces port
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]