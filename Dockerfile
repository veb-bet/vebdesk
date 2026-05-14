FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libegl1 \
    libgl1 \
    libxcb-xinerama0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY vebdesk.py .

RUN pip install PyQt6

CMD ["python", "-c", "import vebdesk; print('OK')"]
