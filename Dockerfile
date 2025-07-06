FROM mcr.microsoft.com/playwright:v1.53.2-jammy

RUN apt-get update && \
    apt-get install -y python3.10 python3-pip && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install playwright

COPY src /app
WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/run.sh"]


