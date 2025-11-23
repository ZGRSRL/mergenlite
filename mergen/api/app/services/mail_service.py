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
    bcc_emails: Optional[List[str]] = None,
    analysis_result_json: Optional[Dict[str, Any]] = None
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
    
    # Analysis result JSON'dan bilgileri al (öncelikli)
    report_data = {}
    if analysis_result_json:
        report_data = analysis_result_json
        logger.info("[Mail Package] Using provided analysis_result_json")
    else:
        # Fallback: Dosya yollarından oku
        pdf_path = folder / "analysis_report.pdf"
        report_json_path = folder / "report.json"
        summary_md_path = folder / "summary.md"
        
        if report_json_path.exists():
            try:
                import json
                with open(report_json_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                logger.info("[Mail Package] Loaded from report.json file")
            except Exception as e:
                logger.warning(f"Could not read report.json: {e}")
    
    # Extract data from analysis result
    opp_info = report_data.get('opportunity', {}) or report_data.get('opportunity_info', {})
    sow_analysis = report_data.get('sow_analysis', {})
    hotel_match = report_data.get('hotels', []) or report_data.get('hotel_match', {})
    
    # If hotel_match is a dict, extract hotels array
    if isinstance(hotel_match, dict):
        hotels = hotel_match.get('hotels', [])
    else:
        hotels = hotel_match if isinstance(hotel_match, list) else []
    
    # Get opportunity details
    opportunity_title = opp_info.get('title', 'N/A')
    solicitation_number = opp_info.get('solicitation_number', 'N/A')
    
    # Extract key information from SOW analysis
    event_details = sow_analysis.get('EventDetails', {}) if sow_analysis else {}
    event_name = event_details.get('EventName', opportunity_title)
    
    # For fit assessment, use a default or extract from analysis
    fit_assessment = report_data.get('fit_assessment', {})
    overall_score = fit_assessment.get('overall_score', 0)
    
    # Create summary from SOW analysis
    summary_text = ""
    if sow_analysis:
        if event_name and event_name != 'N/A':
            summary_text += f"Event: {event_name}\n\n"
        if event_details.get('Dates'):
            dates = event_details.get('Dates', {})
            if isinstance(dates, dict):
                summary_text += f"Dates: {dates.get('Start', 'N/A')} to {dates.get('End', 'N/A')}\n\n"
        if event_details.get('Location'):
            location = event_details.get('Location', {})
            if isinstance(location, dict):
                summary_text += f"Location: {location.get('City', 'N/A')}, {location.get('State', 'N/A')}\n\n"
        
        # Add key requirements
        sleeping_rooms = sow_analysis.get('SleepingRoomRequirements', {})
        if sleeping_rooms:
            summary_text += "Sleeping Room Requirements:\n"
            daily_breakdown = sleeping_rooms.get('DailyBreakdown', [])
            if daily_breakdown:
                summary_text += f"  - {len(daily_breakdown)} days with room requirements\n"
        
        if not summary_text:
            summary_text = "SOW analysis completed. See attached PDF for details."
    else:
        summary_text = "Analysis completed. See attached PDF for details."
    
    # Konu satırı
    if event_name and event_name != 'N/A':
        subject = f"SOW Analysis Report - {event_name[:50]}"
    else:
        subject = f"Opportunity Analysis Report - {opportunity_code}"
    
    # Mail gövdesi (HTML formatında)
    summary_md = ""
    if not analysis_result_json:
        # Only try to read summary.md if we're not using analysis_result_json
        summary_md_path = folder / "summary.md"
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
            <h1>SOW Analysis Report</h1>
            <p><strong>Event:</strong> {event_name}</p>
            <p><strong>Opportunity Code:</strong> {opportunity_code}</p>
            <p><strong>Solicitation Number:</strong> {solicitation_number}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>Executive Summary</h2>
                <pre style="white-space: pre-wrap; background-color: #f9fafb; padding: 15px; border-radius: 5px; font-family: Arial, sans-serif;">{summary_text}</pre>
            </div>
    """
    
    # Add SOW Analysis sections
    if sow_analysis:
        html_body += """
            <div class="section">
                <h3>Key Requirements</h3>
                <ul>
        """
        
        # Add key requirements from SOW
        if event_details.get('Dates'):
            dates = event_details.get('Dates', {})
            if isinstance(dates, dict):
                html_body += f"<li><strong>Dates:</strong> {dates.get('Start', 'N/A')} to {dates.get('End', 'N/A')}</li>\n"
        
        if event_details.get('Location'):
            location = event_details.get('Location', {})
            if isinstance(location, dict):
                html_body += f"<li><strong>Location:</strong> {location.get('City', 'N/A')}, {location.get('State', 'N/A')}</li>\n"
        
        sleeping_rooms = sow_analysis.get('SleepingRoomRequirements', {})
        if sleeping_rooms:
            daily_breakdown = sleeping_rooms.get('DailyBreakdown', [])
            if daily_breakdown:
                html_body += f"<li><strong>Room Requirements:</strong> {len(daily_breakdown)} days with room bookings</li>\n"
        
        html_body += """
                </ul>
            </div>
        """
    
    html_body += """
                </ul>
            </div>
    """
    
    # Hotel Suggestions section removed - hotels will be in separate PDF attachment
    
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
"""
    
    # Hotel suggestions removed from plain text body - hotels will be in separate PDF attachment
    
    text_body += f"""
Please review the attached PDF for complete analysis details.

Generated by MergenLite on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    # Ekler (build_mail_package çağrıldığında attachments parametre olarak eklenecek)
    attachments = []
    
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
        attachments_list = package.get('attachments', [])
        logger.info(f"[Email] Adding {len(attachments_list)} attachments")
        
        if not attachments_list:
            logger.warning("[Email] No attachments in package!")
        else:
            for i, att in enumerate(attachments_list, 1):
                att_path_str = att.get('path', '')
                if not att_path_str:
                    logger.error(f"[Email] Attachment {i} has no path")
                    continue
                
                att_path = Path(att_path_str)
                # Try absolute path first, then relative to /data
                if not att_path.exists():
                    # Try alternative paths
                    alt_paths = [
                        Path('/data') / att_path_str.lstrip('/'),
                        Path('/app') / att_path_str.lstrip('/'),
                        att_path,
                    ]
                    found = False
                    for alt_path in alt_paths:
                        if alt_path.exists():
                            att_path = alt_path
                            found = True
                            logger.info(f"[Email] Found attachment at alternative path: {alt_path}")
                            break
                    
                    if not found:
                        logger.error(f"[Email] Attachment {i} not found: {att_path_str} (tried: {[str(p) for p in alt_paths]})")
                        continue
                
                try:
                    file_size = att_path.stat().st_size
                    filename = att.get('filename', att_path.name)
                    mime_type = att.get('mime_type', 'application/octet-stream')
                    
                    logger.info(f"[Email] Attachment {i}: {filename} ({file_size} bytes) from {att_path}")
                    
                    with open(att_path, 'rb') as f:
                        # Use proper MIME type if available
                        if mime_type.startswith('application/pdf'):
                            part = MIMEBase('application', 'pdf')
                        elif mime_type.startswith('application/json'):
                            part = MIMEBase('application', 'json')
                        else:
                            part = MIMEBase('application', 'octet-stream')
                        
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        part.add_header('Content-Type', mime_type)
                        msg.attach(part)
                    
                    logger.info(f"[Email] ✅ Attachment {i} ({filename}) added successfully")
                except Exception as att_error:
                    logger.error(f"[Email] ❌ Error adding attachment {i} ({att.get('filename', 'unknown')}): {att_error}", exc_info=True)
        
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
        logger.info(f"[Email] Calling server.sendmail()...")
        try:
            send_result = server.sendmail(package['from'], recipients_all, msg.as_string())
            if send_result:
                logger.warning(f"[Email] ⚠️  SMTP sendmail returned non-empty dict (rejected recipients): {send_result}")
            else:
                logger.info(f"[Email] ✅ Message sent via SMTP (sendmail returned empty dict = success)")
        except Exception as send_error:
            logger.error(f"[Email] ❌ SMTP sendmail() failed: {send_error}", exc_info=True)
            raise
        
        server.quit()
        logger.info(f"[Email] ✅ SMTP connection closed")
        
        logger.info(f"[Email] ✅✅✅ Email successfully sent to {package['to']} with {len(package.get('attachments', []))} attachments")
        return True
        
    except smtplib.SMTPAuthenticationError as auth_error:
        logger.error(f"[ERROR] SMTP Authentication failed: {auth_error}", exc_info=True)
        return False
    except smtplib.SMTPRecipientsRefused as recip_error:
        logger.error(f"[ERROR] SMTP Recipients refused: {recip_error}", exc_info=True)
        return False
    except smtplib.SMTPSenderRefused as sender_error:
        logger.error(f"[ERROR] SMTP Sender refused: {sender_error}", exc_info=True)
        return False
    except smtplib.SMTPDataError as data_error:
        logger.error(f"[ERROR] SMTP Data error: {data_error}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"[ERROR] Email send failed: {type(e).__name__}: {e}", exc_info=True)
        return False

