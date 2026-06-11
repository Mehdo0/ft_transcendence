FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
COPY docker/wheels/ /wheels/
RUN pip install --no-cache-dir /wheels/torch*.whl -r requirements.txt
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--proxy-headers", \
     "--forwarded-allow-ips=*", \
     "--reload"]
