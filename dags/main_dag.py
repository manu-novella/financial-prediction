from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess


def run_script(script_name: str):
    '''Calls a script to run from within an Airflow DAG.'''

    path = f'/opt/airflow/scripts/{script_name}'
    subprocess.run(['python', path], check=True)


default_args = {
    'owner': 'airflow',
    'retries': 0
}

with DAG(
    dag_id='financial_prediction_dag',
    default_args=default_args,
    description='Pipeline for financial prediction',
    schedule='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:
        
    asset_price_etl = PythonOperator(
        task_id='asset_price_etl',
        python_callable=run_script,
        op_kwargs={
            'script_name': 'asset_price_etl.py'
        }
    )

    sentiment_sources_etl = PythonOperator(
        task_id='sentiment_sources_etl',
        python_callable=run_script,
        op_kwargs={
            'script_name': 'sentiment_sources_etl.py'
        }
    )

    technical_analysis_etl = PythonOperator(
        task_id='technical_analysis_etl',
        python_callable=run_script,
        op_kwargs={
            'script_name': 'technical_analysis_etl.py'
        }
    )

    sentiment_analysis_etl = PythonOperator(
        task_id='sentiment_analysis_etl',
        python_callable=run_script,
        op_kwargs={
            'script_name': 'sentiment_analysis_etl.py'
        }
    )

    feature_matrix_build = PythonOperator(
        task_id='feature_matrix_build',
        python_callable=run_script,
        op_kwargs={
            'script_name': 'feature_matrix_build.py'
        }
    )
    
    model_training = PythonOperator(
        task_id='model_training',
        python_callable=run_script,
        op_kwargs={
            'script_name': 'model_training.py'
        }
    )

    
    asset_price_etl >> technical_analysis_etl
    sentiment_sources_etl >> sentiment_analysis_etl
    [technical_analysis_etl, sentiment_analysis_etl] >> feature_matrix_build >> model_training