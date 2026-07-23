"""
PDF and CSV Export Report Generation Service.
Uses ReportLab for PDF rendering and the standard csv library for spreadsheet formatting.
"""
import os
import csv
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)

from app.models.customer import Customer
from app.models.alert import Alert

class ReportService:
    """
    Handles file export jobs (PDF generation, CSV generation) and stores them on disk.
    """
    
    @staticmethod
    def generate_pdf_report(report_id: int, title: str, file_path: str, parameters: dict) -> str:
        """
        Creates a PDF report showing flagged customer risk statistics.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Define clean, professional color palette styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor("#1A365D"), # Slate Navy
            spaceAfter=15
        )
        
        body_style = styles['Normal']
        
        story = []
        
        # Title block
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
        story.append(Spacer(1, 20))
        
        # Summary description
        desc_text = "This report summarizes anomalous consumption metrics, high-risk flags, and unresolved alerts tracked by the DeepGuard core system."
        story.append(Paragraph(desc_text, body_style))
        story.append(Spacer(1, 15))
        
        # Create a table showing high-risk customer alerts
        data = [
            ["Alert ID", "Customer Code", "Severity", "Status", "Date Flagged"]
        ]
        
        # Query database alerts
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()
        for alert in alerts:
            # Safely fetch customer details
            customer = Customer.query.get(alert.customer_id)
            code = customer.customer_code if customer else f"ID {alert.customer_id}"
            data.append([
                str(alert.id),
                code,
                alert.severity.upper(),
                alert.status.upper(),
                alert.created_at.strftime('%Y-%m-%d')
            ])
            
        if len(data) == 1:
            data.append(["No records", "-", "-", "-", "-"])
            
        t = Table(data, colWidths=[60, 100, 100, 100, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), # Medium Blue
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ]))
        
        story.append(t)
        
        # Build document
        doc.build(story)
        logger.info(f"PDF Report generated successfully at {file_path}")
        return file_path

    @staticmethod
    def generate_csv_report(report_id: int, file_path: str, parameters: dict) -> str:
        """
        Creates a raw CSV data export for spreadsheet parsing.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Customer ID", "Customer Code", "Name", "Region", "Connection Type", "Account Status"])
            
            customers = Customer.query.all()
            for c in customers:
                writer.writerow([
                    c.id,
                    c.customer_code,
                    c.name,
                    c.region,
                    c.connection_type,
                    c.account_status
                ])
                
        logger.info(f"CSV Report generated successfully at {file_path}")
        return file_path
ClassInstance = ReportService()
