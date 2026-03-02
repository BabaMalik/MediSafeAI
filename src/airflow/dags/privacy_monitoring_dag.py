"""
Privacy Monitoring DAG
Monitor and track differential privacy budget usage
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from pathlib import Path
import json
import logging

# Default arguments
default_args = {
    'owner': 'medisafe',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'email': ['admin@medisafe.ai'],
}

dag = DAG(
    'privacy_monitoring',
    default_args=default_args,
    description='Monitor differential privacy budget usage',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['privacy', 'monitoring', 'compliance'],
)


def check_privacy_budget(**context):
    """Check cumulative privacy budget usage by querying privacy_operations table"""
    logger = logging.getLogger(__name__)
    logger.info("Checking privacy budget usage...")

    report = {
        'date': datetime.now().isoformat(),
        'total_operations': 0,
        'cumulative_epsilon': 0.0,
        'cumulative_delta': 0.0,
        'max_epsilon': 10.0,
        'budget_remaining': 10.0,
        'status': 'healthy'
    }

    try:
        from sqlalchemy import create_engine, text
        import os

        db_url = os.getenv(
            'DATABASE_URL',
            'postgresql://medisafe_user:medisafe_password@localhost:5432/medisafe_db'
        )
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) as total_ops, "
                "COALESCE(SUM(epsilon), 0) as total_epsilon, "
                "COALESCE(SUM(delta), 0) as total_delta "
                "FROM privacy_operations "
                "WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'"
            ))
            row = result.fetchone()

            if row:
                report['total_operations'] = row[0]
                report['cumulative_epsilon'] = float(row[1])
                report['cumulative_delta'] = float(row[2])
                report['budget_remaining'] = report['max_epsilon'] - report['cumulative_epsilon']

                if report['budget_remaining'] <= 0:
                    report['status'] = 'exceeded'
                elif report['cumulative_epsilon'] / report['max_epsilon'] > 0.8:
                    report['status'] = 'warning'

        engine.dispose()

    except Exception as e:
        logger.warning(f"Could not query database, using defaults: {e}")
        report['status'] = 'unknown'

    logger.info(f"Privacy Budget Status: {json.dumps(report, indent=2)}")

    # Save report to file
    report_dir = Path('/opt/airflow/data/reports')
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f'privacy_budget_{datetime.now().strftime("%Y%m%d")}.json'
    report_file.write_text(json.dumps(report, indent=2))

    return report


def alert_if_budget_exceeded(**context):
    """Alert if privacy budget is exceeded or nearing threshold"""
    logger = logging.getLogger(__name__)
    ti = context['task_instance']
    report = ti.xcom_pull(task_ids='check_budget')

    threshold = 0.8  # Alert at 80% budget usage

    if report.get('status') == 'unknown':
        logger.warning("Privacy budget status unknown - database may be unavailable")
        return

    usage_ratio = report['cumulative_epsilon'] / report['max_epsilon'] if report['max_epsilon'] > 0 else 0

    if report.get('status') == 'exceeded':
        message = (
            f"CRITICAL: Privacy budget EXCEEDED!\n"
            f"Cumulative epsilon: {report['cumulative_epsilon']:.2f} / {report['max_epsilon']:.2f}\n"
            f"Total operations (30d): {report['total_operations']}\n"
            f"Action required: Stop all privacy operations until budget is reviewed."
        )
        logger.error(message)
        _send_alert(subject="[CRITICAL] MediSafeAI Privacy Budget Exceeded", body=message)

    elif usage_ratio > threshold:
        message = (
            f"WARNING: Privacy budget usage above {threshold * 100:.0f}%!\n"
            f"Cumulative epsilon: {report['cumulative_epsilon']:.2f} / {report['max_epsilon']:.2f}\n"
            f"Budget remaining: {report['budget_remaining']:.2f}\n"
            f"Total operations (30d): {report['total_operations']}"
        )
        logger.warning(message)
        _send_alert(subject="[WARNING] MediSafeAI Privacy Budget High Usage", body=message)

    else:
        logger.info(
            f"Privacy budget within acceptable limits: "
            f"{report['cumulative_epsilon']:.2f} / {report['max_epsilon']:.2f} "
            f"({usage_ratio * 100:.1f}% used)"
        )


def _send_alert(subject, body):
    """Send email alert for privacy budget issues"""
    logger = logging.getLogger(__name__)
    try:
        import os
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        smtp_from = os.getenv('SMTP_FROM', 'noreply@medisafe.ai')
        alert_email = os.getenv('ALERT_EMAIL', 'admin@medisafe.ai')

        if not smtp_user or not smtp_password:
            logger.warning(f"SMTP not configured, logging alert instead: {subject}")
            logger.warning(body)
            return

        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_from
        msg['To'] = alert_email

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Alert sent to {alert_email}: {subject}")

    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        logger.warning(f"Alert (unsent): {subject}\n{body}")


task_check_budget = PythonOperator(
    task_id='check_budget',
    python_callable=check_privacy_budget,
    dag=dag,
)

task_alert = PythonOperator(
    task_id='alert_if_exceeded',
    python_callable=alert_if_budget_exceeded,
    dag=dag,
)

task_check_budget >> task_alert
