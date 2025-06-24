FROM apache/airflow:3.0.2-python3.9

USER root

RUN apt-get update && \
    apt-get install -y ca-certificates curl openssl \
                       gcc g++ libffi-dev libssl-dev make build-essential && \
    update-ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

COPY scripts /opt/airflow/scripts

COPY models /opt/airflow/models

USER root

RUN chown -R airflow: /opt/airflow/models

USER airflow