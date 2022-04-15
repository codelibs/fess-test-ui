FROM mcr.microsoft.com/playwright:v1.21.0-focal

RUN apt-get update && \
    apt-get install -y python3.8 python3-pip && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install playwright

COPY src /app
WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/run.sh"]


