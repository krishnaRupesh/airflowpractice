import airflow
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago


args = {
    'owner': 'rupesh',
}
with DAG(
        dag_id="first_workflow",
        description="learning airflow",
        schedule_interval="5 5 * * *",
        start_date=days_ago(2)
) as dag:
    run_this_last = DummyOperator(
        task_id="run_this_last"
    )

    run_this = BashOperator(
        bash_command= "echo 5",
        task_id="run_this"
    )

    run_this >> run_this_last
