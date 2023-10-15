FROM python:3.11.4-slim-bullseye AS builder
# tell pipenv to create virtualenv in the current directory
ENV PIPENV_VENV_IN_PROJECT=1
RUN pip install 'pipenv~=2023.7.11'
WORKDIR /app
COPY Pipfile Pipfile.lock /app/
# create .venv
RUN pipenv sync

FROM python:3.11.4-slim-bullseye
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
CMD ["/app/.venv/bin/python", "-m", "analytics"]
