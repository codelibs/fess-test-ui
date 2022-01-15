FROM mcr.microsoft.com/playwright:focal

RUN pip install playwright

COPY src /app
WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/run.sh"]


