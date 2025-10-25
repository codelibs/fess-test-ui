FROM mcr.microsoft.com/playwright:v1.56.1-jammy

RUN pip install --no-cache-dir playwright

COPY src /app
WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/run.sh"]


