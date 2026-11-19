# The python flavour of the Playwright image already ships python3 and pip,
# which saves the apt-get step (about 45 s on a CI runner).
FROM mcr.microsoft.com/playwright/python:v1.56.0-noble

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
