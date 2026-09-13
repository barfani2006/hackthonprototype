FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY frontend ./frontend
COPY README.md .
COPY render.yaml .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "-m", "backend.server"]
