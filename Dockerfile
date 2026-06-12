# Alpine has a much smaller attack surface than Debian slim
FROM python:3.11-alpine

WORKDIR /app

# Alpine uses addgroup/adduser differently
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Install build dependencies needed for some Python packages on Alpine
RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
