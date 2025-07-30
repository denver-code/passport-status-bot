FROM python:3.12 AS python-base

ENV POETRY_VERSION=2.1.0
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Poetry install stage
FROM python-base AS poetry-base
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Final image
FROM python-base

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential libzbar-dev ffmpeg libsm6 libxext6 libgl1 fonts-unifont && \
    rm -rf /var/lib/apt/lists/*

# Copy poetry venv from poetry-base
COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}

# Set the working directory inside the container
WORKDIR /app

# Copy dependency files first to cache dependencies
COPY pyproject.toml README.md ./

# Lock dependencies
RUN poetry lock

# [OPTIONAL] Validate the project is properly configured
RUN poetry check

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root --without dev

# Install Playwright and browsers
RUN poetry run pip install --no-cache-dir playwright \
    && poetry run playwright install chromium

# Install new version of cloudscraper from GitHub because it's not in the PyPI
RUN poetry run pip install git+https://github.com/VeNoMouS/cloudscraper.git@3.0.0

# Copy app source code
COPY . .

# Run app
CMD ["poetry", "run", "python", "-m", "bot"]
