# AgentCore Runtime images must be linux/arm64.
FROM --platform=linux/arm64 public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install '.[ollama,gemini,llama,openai]'

COPY main.py ./

EXPOSE 8080

CMD ["python", "main.py"]
