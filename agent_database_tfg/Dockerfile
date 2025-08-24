# --- Fase 1: Construcción ---
    FROM python:3.12 as builder

    
    WORKDIR /usr/src/app


    ENV PYTHONDONTWRITEBYTECODE 1


    ENV PYTHONUNBUFFERED 1


    RUN python -m venv /opt/venv


    ENV PATH="/opt/venv/bin:$PATH"


    COPY requirements.txt .


    RUN pip install --no-cache-dir -r requirements.txt
    
    # --- Fase 2: Producción ---
    FROM python:3.12-slim


    WORKDIR /agent


    COPY --from=builder /opt/venv /opt/venv
    COPY . .


    ENV PATH="/opt/venv/bin:$PATH"


    EXPOSE 8001


    CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001", "main:app"]