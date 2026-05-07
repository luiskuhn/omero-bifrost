FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Glencoe-maintained prebuilt Ice wheel for Linux x86_64 + CPython 3.11.
ARG ICE_WHEEL_URL="https://github.com/glencoesoftware/zeroc-ice-py-linux-x86_64/releases/download/20240202/zeroc_ice-3.6.5-cp311-cp311-manylinux_2_28_x86_64.whl"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libssl-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pinned runtime dependencies from repository requirements.
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install "zeroc-ice @ ${ICE_WHEEL_URL}" \
    && pip install -r requirements.txt

# Install omero-bifrost package after dependency environment is pinned.
RUN pip install "git+https://github.com/luiskuhn/omero-bifrost.git@main"

ENTRYPOINT ["omero-bifrost"]
CMD ["--help"]
