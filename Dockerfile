FROM python:3.12-slim
 
ENV POETRY_VERSION=1.8.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
 
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"
 
WORKDIR /app
 
RUN adduser --disabled-password --gecos "" appuser
 
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main
 
COPY app.py .
 
RUN chown -R appuser:appuser /app
USER appuser
 
ENV PORT=5000
ENV VERSION=1.0.0
# API_KEY must be supplied at runtime — no default
 
EXPOSE 5000
 
CMD ["python", "app.py"]