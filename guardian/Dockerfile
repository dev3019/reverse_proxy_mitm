FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
  fastapi \
  "uvicorn[standard]" \
  transformers

RUN pip install --no-cache-dir \
  torch --index-url https://download.pytorch.org/whl/cpu

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]