FROM python:3.11.3-alpine3.17 as python-base

RUN apk --no-cache add shadow
RUN addgroup -S appuser && adduser -S appuser -G appuser


# https://python-poetry.org/docs#ci-recommendations
ENV POETRY_VERSION=1.4.2
ENV POETRY_HOME=/home/appuser/poetry
ENV POETRY_VENV=/home/appuser/poetry-venv

# Tell Poetry where to place its cache and virtual environment
ENV POETRY_CACHE_DIR=/home/appuser/.cache



# Create stage for Poetry installation
FROM python-base as poetry-base

# Creating a virtual environment just for poetry and install it with pip
RUN python3 -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install -U pip setuptools \
	&& $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Create a new stage from the base python image
FROM python-base as example-app

# Copy Poetry to app image
COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}

# Add Poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"


WORKDIR /bank_app


# Copy Dependencies
COPY poetry.lock pyproject.toml ./


# Install Dependencies
RUN poetry install --no-interaction --no-cache --without dev


# Copy Application
COPY . /bank_app

RUN chown -R appuser:appuser /bank_app
USER appuser

# Run Application
EXPOSE 5000


CMD [ "poetry", "run", "flask", "--app", "main", "run", "--host", "0.0.0.0" ]