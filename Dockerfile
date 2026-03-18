FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir httpx
COPY engine.py .
COPY purgatorium.py .
HEALTHCHECK --interval=60s --timeout=10s --retries=3 CMD python -c "import httpx" || exit 1
CMD ["python", "engine.py"]
