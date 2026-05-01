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

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY src /app
# Bake the extracted Fess labels (populated by extract_labels.sh on the
# host before `docker compose up --build`) into the image. Bind-mounting
# ./labels via compose breaks under Jenkins Docker-in-Docker because the
# host daemon cannot see paths inside the Jenkins container's workspace.
COPY labels /labels
WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/run.sh"]
