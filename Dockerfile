FROM python:3.11-bullseye

RUN apt-get update && pip install poetry && useradd -d /home/app -U -m -u 1234 app

WORKDIR /app/

COPY --chown=app:app ./ ./

USER app

RUN poetry install


ENTRYPOINT ["poetry", "run", "python", "main.py"]