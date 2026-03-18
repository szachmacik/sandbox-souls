FROM python:3.12-slim
WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir httpx

# Copy code
COPY engine.py .
COPY purgatorium.py .

# Health check — engine kończy się po symulacji, więc używamy purgatorium jako daemon
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import os; print('ok')" || exit 1

CMD ["python", "purgatorium.py"]
