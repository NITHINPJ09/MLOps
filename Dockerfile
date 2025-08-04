# syntax=docker/dockerfile:1

FROM python:3.13-slim
WORKDIR /image_classifier
COPY . .
RUN --mount=type=secret,id=ACCOUNT_KEY \
    groupadd -r appuser && \
    useradd -g appuser appuser && \
    chown -R appuser:appuser /image_classifier && \
    pip3 install -r requirements.txt && \
    dvc init --no-scm && \
    dvc remote add -d classifier azure://cifar-classifier-model && \
    dvc remote modify classifier account_name 'cifarmodel' && \
    export STORAGE_ACCOUNT_KEY=$(cat /run/secrets/ACCOUNT_KEY) && \
    dvc remote modify classifier account_key $STORAGE_ACCOUNT_KEY && \
    dvc pull && \
    rm -rf .dvc .dvcignore *.dvc
EXPOSE 8000
USER appuser
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]