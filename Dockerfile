FROM mcr.microsoft.com/playwright:v1.56.0-noble

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        python3-full \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir playwright==1.56.0

# Ensure browser binaries are installed
RUN playwright install --with-deps chromium

COPY src /app
WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/run.sh"]
