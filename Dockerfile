FROM python:3.12-slim


COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/


COPY pyproject.toml uv.lock ./

ENV UV_SYSTEM_PYTHON=1


RUN uv pip install --system --no-cache -r pyproject.toml


WORKDIR /app


COPY . .


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
