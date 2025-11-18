#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mail Package Builder
Analiz raporunu mail paketi olarak hazırlar
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

def build_mail_package(
    opportunity_code: str,
    folder_path: str,
    to_email: str,
    from_email: Optional[str] = None,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Mail paketi oluştur
    
    Args:
        opportunity_code: Fırsat kodu
        folder_path: Fırsat klasörü yolu
        to_email: Alıcı e-posta
        from_email: Gönderen e-posta (opsiyonel)
        cc_emails: CC listesi (opsiyonel)
        bcc_emails: BCC listesi (opsiyonel)
    
    Returns:
        Mail paketi dict
    """
    folder = Path(folder_path)
    
    # Dosya yolları
    pdf_path = folder / "analysis_report.pdf"
    report_json_path = folder / "report.json"
    summary_md_path = folder / "summary.md"
    
    # Report JSON'dan bilgileri al
    report_data = {}
    if report_json_path.exists():
        try:
            import json
            with open(report_json_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read report.json: {e}")
    
    opp_info = report_data.get('opportunity_info', {})
    fit_assessment = report_data.get('fit_assessment', {})
    overall_score = fit_assessment.get('overall_score', 0)
    
    # Konu satırı
    subject = f"Opportunity Analysis Report - {opportunity_code} (Score: {overall_score}/100)"
    
    # Mail gövdesi (HTML formatında)
    summary_md = ""
    if summary_md_path.exists():
        try:
            with open(summary_md_path, 'r', encoding='utf-8') as f:
                summary_md = f.read()
        except Exception as e:
            logger.warning(f"Could not read summary.md: {e}")
    
    # HTML body oluştur
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #1e40af; color: white; padding: 20px; border-radius: 5px; }}
            .content {{ padding: 20px; }}
            .score {{ font-size: 24px; font-weight: bold; color: {'#059669' if overall_score >= 70 else '#dc2626' if overall_score < 50 else '#f59e0b'}; }}
            .section {{ margin: 20px 0; padding: 15px; background-color: #f9fafb; border-left: 4px solid #1e40af; }}
            .footer {{ margin-top: 30px; padding: 15px; background-color: #f3f4f6; font-size: 12px; color: #6b7280; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #1e40af; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Opportunity Analysis Report</h1>
            <p><strong>Opportunity Code:</strong> {opportunity_code}</p>
            <p><strong>Solicitation Number:</strong> {opp_info.get('solicitation_number', 'N/A')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>Executive Summary</h2>
                <p class="score">Overall Fit Score: {overall_score}/100</p>
                <p>{fit_assessment.get('summary', 'No summary available')}</p>
            </div>
            
            <div class="section">
                <h3>Strengths</h3>
                <ul>
    """
    
    for strength in fit_assessment.get('strengths', [])[:5]:
        html_body += f"<li>{strength}</li>\n"
    
    html_body += """
                </ul>
            </div>
            
            <div class="section">
                <h3>Risks</h3>
                <ul>
    """
    
    for risk in fit_assessment.get('risks', [])[:5]:
        html_body += f"<li>{risk}</li>\n"
    
    html_body += """
                </ul>
            </div>
    """
    
    if fit_assessment.get('blocking_issues'):
        html_body += """
            <div class="section">
                <h3>Blocking Issues</h3>
                <ul>
        """
        for issue in fit_assessment.get('blocking_issues', [])[:5]:
            html_body += f"<li style='color: #dc2626;'>{issue}</li>\n"
        html_body += """
                </ul>
            </div>
        """
    
    # Summary markdown'ı HTML'e çevir (basit)
    if summary_md:
        html_body += f"""
            <div class="section">
                <h3>Detailed Summary</h3>
                <pre style="white-space: pre-wrap; background-color: #f9fafb; padding: 15px; border-radius: 5px;">{summary_md}</pre>
            </div>
        """
    
    html_body += f"""
        </div>
        
        <div class="footer">
            <p>This report was generated by MergenLite on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Please review the attached PDF for complete analysis details.</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text body (fallback)
    text_body = f"""
Opportunity Analysis Report
===========================

Opportunity Code: {opportunity_code}
Solicitation Number: {opp_info.get('solicitation_number', 'N/A')}
Title: {opp_info.get('title', 'N/A')}

Overall Fit Score: {overall_score}/100

Summary:
{fit_assessment.get('summary', 'No summary available')}

Strengths:
{chr(10).join('• ' + s for s in fit_assessment.get('strengths', [])[:5])}

Risks:
{chr(10).join('• ' + r for r in fit_assessment.get('risks', [])[:5])}

Please review the attached PDF for complete analysis details.

Generated by MergenLite on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    # Ekler
    attachments = []
    if pdf_path.exists():
        attachments.append({
            'path': str(pdf_path),
            'filename': f"analysis_report_{opportunity_code}.pdf",
            'mime_type': 'application/pdf'
        })
    
    # SOW PDF'lerini de ekle (varsa)
    sow_hotel_pdf_path = folder / f"sow_hotel_{opportunity_code}.pdf"
    if sow_hotel_pdf_path.exists():
        attachments.append({
            'path': str(sow_hotel_pdf_path),
            'filename': f"sow_{opportunity_code}.pdf",
            'mime_type': 'application/pdf'
        })
        logger.info(f"[Mail Package] Added SOW PDF: {sow_hotel_pdf_path}")
    
    # Internal SOW PDF'i de ekle (varsa)
    sow_internal_pdf_path = folder / f"sow_internal_{opportunity_code}.pdf"
    if sow_internal_pdf_path.exists():
        attachments.append({
            'path': str(sow_internal_pdf_path),
            'filename': f"sow_internal_{opportunity_code}.pdf",
            'mime_type': 'application/pdf'
        })
        logger.info(f"[Mail Package] Added Internal SOW PDF: {sow_internal_pdf_path}")
    
    # Mail paketi
    package = {
        'to': to_email,
        'from': from_email or 'noreply@mergenlite.com',
        'cc': cc_emails or [],
        'bcc': bcc_emails or [],
        'subject': subject,
        'html_body': html_body,
        'text_body': text_body,
        'attachments': attachments,
        'opportunity_code': opportunity_code,
        'generated_at': datetime.now().isoformat()
    }
    
    logger.info(f"[OK] Mail package created for {opportunity_code}")
    return package

def send_email_via_smtp(package: Dict[str, Any], smtp_config: Dict[str, Any]) -> bool:
    """
    SMTP ile mail gönder (örnek implementasyon)
    
    Args:
        package: build_mail_package() çıktısı
        smtp_config: SMTP ayarları {
            'host': 'smtp.office365.com',
            'port': 587,
            'username': 'user@domain.com',
            'password': 'password',
            'use_tls': True
        }
    
    Returns:
        True if successful
    """
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        
        # Mail oluştur
        msg = MIMEMultipart('alternative')
        msg['From'] = package['from']
        msg['To'] = package['to']
        msg['Subject'] = package['subject']
        
        if package['cc']:
            msg['Cc'] = ', '.join(package['cc'])
        
        # Body ekle
        msg.attach(MIMEText(package['text_body'], 'plain'))
        msg.attach(MIMEText(package['html_body'], 'html'))
        
        # Ekler
        logger.info(f"[Email] Adding {len(package.get('attachments', []))} attachments")
        for i, att in enumerate(package.get('attachments', []), 1):
            att_path = Path(att['path'])
            if not att_path.exists():
                logger.error(f"[Email] Attachment {i} not found: {att_path}")
                continue
            try:
                file_size = att_path.stat().st_size
                logger.info(f"[Email] Attachment {i}: {att['filename']} ({file_size} bytes) from {att_path}")
                with open(att['path'], 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {att["filename"]}'
                    )
                    msg.attach(part)
                logger.info(f"[Email] ✅ Attachment {i} added successfully")
            except Exception as att_error:
                logger.error(f"[Email] ❌ Error adding attachment {i} ({att['filename']}): {att_error}", exc_info=True)
        
        # SMTP bağlantısı
        logger.info(f"[Email] Connecting to SMTP server: {smtp_config.get('host')}:{smtp_config.get('port')}")
        logger.info(f"[Email] Using TLS: {smtp_config.get('use_tls')}")
        logger.info(f"[Email] From: {package['from']}, To: {package['to']}")
        
        if smtp_config.get('use_tls'):
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            logger.info(f"[Email] Starting TLS...")
            server.starttls()
            logger.info(f"[Email] TLS started")
        else:
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            logger.info(f"[Email] Connected without TLS")
        
        logger.info(f"[Email] Logging in as {smtp_config['username']}...")
        server.login(smtp_config['username'], smtp_config['password'])
        logger.info(f"[Email] ✅ Login successful")
        
        # Gönder
        recipients = [package['to']]
        if package.get('cc'):
            recipients.extend(package['cc'] if isinstance(package['cc'], list) else [package['cc']])
        if package.get('bcc'):
            recipients.extend(package['bcc'] if isinstance(package['bcc'], list) else [package['bcc']])
        # BCC'yi mesajdan çıkar (SMTP protokolü gereği)
        recipients_all = recipients.copy()
        logger.info(f"[Email] Sending to recipients: {recipients_all}")
        
        # Mesajda sadece TO ve CC görünür
        server.sendmail(package['from'], recipients_all, msg.as_string())
        logger.info(f"[Email] ✅ Message sent via SMTP")
        server.quit()
        logger.info(f"[Email] ✅ SMTP connection closed")
        
        logger.info(f"[Email] ✅✅✅ Email successfully sent to {package['to']} with {len(package.get('attachments', []))} attachments")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Email send failed: {e}", exc_info=True)
        return False

