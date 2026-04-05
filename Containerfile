FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen

COPY editor.py .

ENV MARIMO_SKIP_UPDATE_CHECK=1

# Auth handled by oauth2-proxy upstream — no token needed
CMD ["uv", "run", "marimo", "run", "editor.py", \
     "--host", "0.0.0.0", "--port", "2719", "--no-token"]
