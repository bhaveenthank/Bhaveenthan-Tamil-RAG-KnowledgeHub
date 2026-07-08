FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --break-system-packages \
    beautifulsoup4>=4.12.3 \
    lxml>=5.2.0 \
    requests>=2.32.0

COPY src /app/src
COPY shared/tvu-common/src /app/shared/tvu-common/src
COPY projects/parser/src /app/projects/parser/src
COPY ops/cloudrun /app/ops/cloudrun

ENV PYTHONPATH=/app/projects/parser/src:/app/shared/tvu-common/src:/app/src
ENV TVU_FAILURE_KIND=all
ENV TVU_FETCH_TIMEOUT=20
ENV TVU_FETCH_DELAY=0.5
ENV TVU_PROGRESS_EVERY=25

ENTRYPOINT ["/bin/bash", "/app/ops/cloudrun/fetch_thevaram_failures.sh"]
