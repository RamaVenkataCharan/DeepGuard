"""
Asynchronous report generation tasks for Celery.
"""
import os
from app.extensions import celery, db
from app.models.report import Report
from app.services.report_service import ReportService
import logging

logger = logging.getLogger(__name__)

@celery.task(name="tasks.generate_report_async")
def generate_report_async(report_id: int):
    """
    Celery task running report rendering in background to avoid blocking API responses.
    """
    logger.info(f"Starting background report generation for report ID: {report_id}...")
    
    report = Report.query.get(report_id)
    if not report:
        logger.error(f"Report ID {report_id} not found in database.")
        return "Report not found"
        
    fmt = report.format.lower()
    filename = f"report_{report.id}.{fmt}"
    file_path = os.path.abspath(os.path.join("./reports", filename))
    
    try:
        report.status = "generating"
        db.session.commit()
        
        if fmt == "pdf":
            ReportService.generate_pdf_report(report.id, report.title, file_path, report.parameters)
        else:
            ReportService.generate_csv_report(report.id, file_path, report.parameters)
            
        report.status = "completed"
        report.file_path = file_path
        report.file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        db.session.commit()
        logger.info(f"Report ID {report_id} completed successfully.")
        
    except Exception as e:
        report.status = "failed"
        report.error_message = str(e)
        db.session.commit()
        logger.error(f"Report ID {report_id} failed: {str(e)}")
        return f"Failed: {str(e)}"
        
    return f"Completed report ID {report_id}"
