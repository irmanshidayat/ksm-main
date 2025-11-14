#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Service - Service untuk mengirim email otomatis ke vendor
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import json
from flask_jwt_extended import get_jwt_identity
from domains.auth.services.gmail_oauth_service import GmailOAuthService
from models import EmailLog
from config.database import db
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class EmailService:
    """Service untuk mengirim email ke vendor"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@ksm.com')
        self.from_name = os.getenv('FROM_NAME', 'KSM Procurement System')
        
        # Initialize Gmail OAuth service
        self.gmail_oauth_service = GmailOAuthService()
    
    def send_vendor_email(self, vendor_email: str, vendor_name: str, 
                         items: List[Dict], custom_message: str = None, 
                         subject: str = None, cc_emails: List[str] = None,
                         bcc_emails: List[str] = None, user_id: int = None, 
                         use_gmail_api: bool = True) -> Dict[str, Any]:
        """
        Kirim email penawaran ke vendor
        
        Args:
            vendor_email: Email vendor
            vendor_name: Nama vendor
            items: List barang yang diminta
            custom_message: Pesan custom dari user
            subject: Subject email (optional, default akan dibuat otomatis)
            cc_emails: List email CC (optional)
            bcc_emails: List email BCC (optional)
            user_id: ID user yang mengirim (untuk Gmail API)
            use_gmail_api: Apakah menggunakan Gmail API atau SMTP
            
        Returns:
            Dict dengan status pengiriman
        """
        try:
            # Set default values
            if cc_emails is None:
                cc_emails = []
            if bcc_emails is None:
                bcc_emails = []
            if subject is None:
                subject = f"Permintaan Penawaran - {vendor_name}"
            
            # Generate email content
            html_content = self._generate_email_template(vendor_name, items, custom_message, subject)
            text_content = self._generate_text_template(vendor_name, items, custom_message, subject)
            
            # Create email log entry
            email_log = EmailLog(
                user_id=user_id,
                vendor_email=vendor_email,
                subject=subject,
                status='pending'
            )
            db.session.add(email_log)
            db.session.commit()
            
            # Try Gmail API first if user_id provided and use_gmail_api is True
            if use_gmail_api and user_id:
                result = self._send_via_gmail_api(user_id, vendor_email, subject, html_content, text_content, cc_emails, bcc_emails)
                if result['success']:
                    # Update email log
                    email_log.status = 'sent'
                    email_log.message_id = result.get('message_id')
                    email_log.sent_at = datetime.now()
                    db.session.commit()
                    
                    logger.info(f"✅ Email berhasil dikirim via Gmail API ke {vendor_email}")
                    return result
                else:
                    # Log Gmail API failure but continue to SMTP fallback
                    logger.warning(f"⚠️ Gmail API failed: {result.get('message', 'Unknown error')}")
            
            # Fallback to SMTP
            result = self._send_via_smtp(vendor_email, subject, html_content, text_content, cc_emails, bcc_emails)
            
            if result['success']:
                # Update email log
                email_log.status = 'sent'
                email_log.sent_at = datetime.now()
                db.session.commit()
                
                logger.info(f"[SUCCESS] Email berhasil dikirim via SMTP ke {vendor_email}")
            else:
                # Update email log with error
                email_log.status = 'failed'
                email_log.error_message = result.get('message', 'Unknown error')
                db.session.commit()
                
                # If both Gmail API and SMTP failed, provide helpful error message
                if result.get('error_type') == 'smtp_config_error':
                    result['message'] = 'Email tidak dapat dikirim karena konfigurasi email belum lengkap. Silakan hubungi administrator untuk mengatur konfigurasi email.'
                elif result.get('error_type') == 'gmail_credentials_error':
                    result['message'] = 'Email tidak dapat dikirim karena Gmail tidak terhubung dan SMTP tidak dikonfigurasi. Silakan hubungkan Gmail atau hubungi administrator untuk mengatur SMTP.'
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Error sending email to {vendor_email}: {str(e)}")
            
            # Update email log with error
            if 'email_log' in locals():
                email_log.status = 'failed'
                email_log.error_message = str(e)
                db.session.commit()
            
            return {
                'success': False,
                'message': f'Gagal mengirim email: {str(e)}',
                'recipient': vendor_email,
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_via_gmail_api(self, user_id: int, to_email: str, subject: str, 
                           html_content: str, text_content: str, 
                           cc_emails: List[str] = None, bcc_emails: List[str] = None) -> Dict[str, Any]:
        """Send email via Gmail API"""
        try:
            if cc_emails is None:
                cc_emails = []
            if bcc_emails is None:
                bcc_emails = []
                
            result = self.gmail_oauth_service.send_email_via_gmail_api(
                user_id, to_email, subject, html_content, text_content, cc_emails, bcc_emails
            )
            
            # If Gmail API fails due to credentials issue, return specific error
            if not result['success'] and 'credentials' in result['message'].lower():
                return {
                    'success': False,
                    'message': 'Gmail tidak terhubung atau credentials expired. Silakan hubungkan ulang Gmail atau gunakan SMTP.',
                    'error_type': 'gmail_credentials_error'
                }
                
            return result
        except Exception as e:
            logger.error(f"❌ Gmail API error: {str(e)}")
            return {
                'success': False,
                'message': f'Gmail API error: {str(e)}',
                'error_type': 'gmail_api_error'
            }
    
    def _send_via_smtp(self, to_email: str, subject: str, 
                      html_content: str, text_content: str,
                      cc_emails: List[str] = None, bcc_emails: List[str] = None) -> Dict[str, Any]:
        """Send email via SMTP (fallback method)"""
        try:
            if cc_emails is None:
                cc_emails = []
            if bcc_emails is None:
                bcc_emails = []
            
            # Check if SMTP credentials are properly configured
            if (self.smtp_username == 'your-email@gmail.com' or 
                self.smtp_password == 'your-app-password' or
                not self.smtp_username or not self.smtp_password):
                return {
                    'success': False,
                    'message': 'SMTP credentials tidak dikonfigurasi dengan benar. Silakan hubungi administrator untuk mengatur SMTP settings.',
                    'error_type': 'smtp_config_error'
                }
                
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add CC if provided
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add both text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Prepare recipients list (TO + CC + BCC)
            recipients = [to_email] + cc_emails + bcc_emails
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg, to_addrs=recipients)
            
            return {
                'success': True,
                'message': 'Email berhasil dikirim via SMTP',
                'recipient': to_email,
                'cc_recipients': cc_emails,
                'bcc_recipients': bcc_emails,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            return {
                'success': False,
                'message': f'SMTP error: {str(e)}',
                'recipient': to_email,
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_email_template(self, vendor_name: str, items: List[Dict], 
                                custom_message: str = None, subject: str = None) -> str:
        """Generate HTML email template"""
        
        # Default message jika tidak ada custom message
        if not custom_message:
            custom_message = f"""
            <p>Kepada Yth. {vendor_name},</p>
            <p>Kami dari KSM Procurement System ingin meminta penawaran untuk barang-barang berikut:</p>
            """
        
        # Default subject jika tidak ada
        if not subject:
            subject = f"Permintaan Penawaran - {vendor_name}"
        
        # Check if custom_message contains HTML table (contains <table> tag)
        # If it contains HTML table, use it as is
        # If it contains plain text table (with spacing or | or + but no <table>), wrap in <pre> tag
        if custom_message:
            if '<table' in custom_message.lower() or '<p>' in custom_message.lower():
                # It's HTML, use it as is
                custom_message_html = custom_message
            elif '|' in custom_message or '+' in custom_message:
                # It's plain text table with lines, wrap in <pre> tag
                formatted_message = custom_message.replace('\\n', '\n')
                import html
                escaped_message = html.escape(formatted_message)
                custom_message_html = f'<pre style="font-family: monospace; white-space: pre-wrap; background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">{escaped_message}</pre>'
            elif 'Nama Barang' in custom_message and ('Quantity' in custom_message or 'Kategori' in custom_message):
                # It's plain text table without lines (just spacing), wrap in <pre> tag to preserve spacing
                formatted_message = custom_message.replace('\\n', '\n')
                import html
                escaped_message = html.escape(formatted_message)
                custom_message_html = f'<pre style="font-family: monospace; white-space: pre-wrap; background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">{escaped_message}</pre>'
            else:
                # Regular text, convert newlines to <br> tags
                import html
                escaped_message = html.escape(custom_message)
                formatted_message = escaped_message.replace('\\n', '<br>').replace('\n', '<br>')
                custom_message_html = f'<p>{formatted_message}</p>'
        else:
            custom_message_html = custom_message
        
        # Generate items table
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{item.get('nama_barang', '-')}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item.get('spesifikasi', '-')}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item.get('quantity', '-')}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item.get('satuan', '-')}</td>
            </tr>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .content {{ margin-bottom: 20px; }}
                .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .items-table th {{ background-color: #007bff; color: white; padding: 12px; text-align: left; }}
                .items-table td {{ padding: 8px; border: 1px solid #ddd; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>[EMAIL] {subject}</h2>
                    <p><strong>Dari:</strong> KSM Procurement System</p>
                    <p><strong>Kepada:</strong> {vendor_name}</p>
                    <p><strong>Tanggal:</strong> {datetime.now().strftime('%d %B %Y')}</p>
                </div>
                
                <div class="content">
                    {custom_message_html}
                    
                    <h3>[LIST] Daftar Barang yang Diminta:</h3>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th>Nama Barang</th>
                                <th>Spesifikasi</th>
                                <th>Quantity</th>
                                <th>Satuan</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <p><strong>Catatan:</strong> Mohon kirimkan penawaran harga untuk barang-barang di atas sesuai dengan spesifikasi yang diminta.</p>
                </div>
                
                <div class="footer">
                    <p>Email ini dikirim secara otomatis dari KSM Procurement System.</p>
                    <p>Jika ada pertanyaan, silakan hubungi tim procurement kami.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_text_template(self, vendor_name: str, items: List[Dict], 
                              custom_message: str = None, subject: str = None) -> str:
        """Generate plain text email template"""
        
        if not custom_message:
            custom_message = f"""
Kepada Yth. {vendor_name},

Kami dari KSM Procurement System ingin meminta penawaran untuk barang-barang berikut:
            """
        
        # Default subject jika tidak ada
        if not subject:
            subject = f"Permintaan Penawaran - {vendor_name}"
        
        # Generate items text
        items_text = ""
        for i, item in enumerate(items, 1):
            items_text += f"""
{i}. {item.get('nama_barang', '-')}
   Spesifikasi: {item.get('spesifikasi', '-')}
   Quantity: {item.get('quantity', '-')} {item.get('satuan', '-')}
            """
        
        text_template = f"""
{'-' * 50}
{subject}
{'-' * 50}

Dari: KSM Procurement System
Kepada: {vendor_name}
Tanggal: {datetime.now().strftime('%d %B %Y')}

{custom_message}

DAFTAR BARANG YANG DIMINTA:
{items_text}

Catatan: Mohon kirimkan penawaran harga untuk barang-barang di atas sesuai dengan spesifikasi yang diminta.

{'-' * 50}
Email ini dikirim secara otomatis dari KSM Procurement System.
Jika ada pertanyaan, silakan hubungi tim procurement kami.
{'-' * 50}
        """
        
        return text_template
    
    def get_email_templates(self) -> Dict[str, Any]:
        """Get available email templates"""
        return {
            'templates': [
                {
                    'id': 'default',
                    'name': 'Template Default',
                    'description': 'Template standar untuk permintaan penawaran'
                },
                {
                    'id': 'urgent',
                    'name': 'Template Urgent',
                    'description': 'Template untuk permintaan mendesak'
                },
                {
                    'id': 'follow_up',
                    'name': 'Template Follow Up',
                    'description': 'Template untuk follow up penawaran'
                }
            ]
        }
    
    def validate_email_config(self) -> Dict[str, Any]:
        """Validate email configuration"""
        try:
            # Test SMTP connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            
            return {
                'success': True,
                'message': 'Email configuration valid',
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Email configuration invalid: {str(e)}',
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port
            }
    
    def send_vendor_email_with_attachments(self, vendor_email: str, vendor_name: str, 
                                         items: List[Dict], custom_message: str = None, 
                                         subject: str = None, cc_emails: List[str] = None,
                                         bcc_emails: List[str] = None, attachments: List = None,
                                         user_id: int = None, use_gmail_api: bool = True) -> Dict[str, Any]:
        """
        Kirim email penawaran ke vendor dengan attachment
        
        Args:
            vendor_email: Email vendor
            vendor_name: Nama vendor
            items: List barang yang diminta
            custom_message: Pesan custom dari user
            subject: Subject email (optional, default akan dibuat otomatis)
            cc_emails: List email CC (optional)
            bcc_emails: List email BCC (optional)
            attachments: List EmailAttachment objects
            user_id: ID user yang mengirim (untuk Gmail API)
            use_gmail_api: Apakah menggunakan Gmail API atau SMTP
            
        Returns:
            Dict dengan status pengiriman
        """
        try:
            # Set default values
            if cc_emails is None:
                cc_emails = []
            if bcc_emails is None:
                bcc_emails = []
            if attachments is None:
                attachments = []
            if subject is None:
                subject = f"Permintaan Penawaran - {vendor_name}"
            
            # Generate email content
            html_content = self._generate_email_template(vendor_name, items, custom_message, subject)
            text_content = self._generate_text_template(vendor_name, items, custom_message, subject)
            
            # Create email log entry
            email_log = EmailLog(
                user_id=user_id,
                vendor_email=vendor_email,
                subject=subject,
                status='pending'
            )
            db.session.add(email_log)
            db.session.commit()
            
            # Try Gmail API first if user_id provided and use_gmail_api is True
            if use_gmail_api and user_id:
                result = self._send_via_gmail_api_with_attachments(user_id, vendor_email, subject, html_content, text_content, cc_emails, bcc_emails, attachments)
                if result['success']:
                    # Update email log
                    email_log.status = 'sent'
                    email_log.message_id = result.get('message_id')
                    email_log.sent_at = datetime.now()
                    db.session.commit()
                    
                    logger.info(f"✅ Email dengan {len(attachments)} attachment berhasil dikirim via Gmail API ke {vendor_email}")
                    return result
                else:
                    # Log Gmail API failure but continue to SMTP fallback
                    logger.warning(f"⚠️ Gmail API failed: {result.get('message', 'Unknown error')}")
            
            # Fallback to SMTP
            result = self._send_via_smtp_with_attachments(vendor_email, subject, html_content, text_content, cc_emails, bcc_emails, attachments)
            
            if result['success']:
                # Update email log
                email_log.status = 'sent'
                email_log.sent_at = datetime.now()
                db.session.commit()
                
                logger.info(f"✅ Email dengan {len(attachments)} attachment berhasil dikirim via SMTP ke {vendor_email}")
            else:
                # Update email log with error
                email_log.status = 'failed'
                email_log.error_message = result.get('message', 'Unknown error')
                db.session.commit()
                
                # If both Gmail API and SMTP failed, provide helpful error message
                if result.get('error_type') == 'smtp_config_error':
                    result['message'] = 'Email tidak dapat dikirim karena konfigurasi email belum lengkap. Silakan hubungi administrator untuk mengatur konfigurasi email.'
                elif result.get('error_type') == 'gmail_credentials_error':
                    result['message'] = 'Email tidak dapat dikirim karena Gmail tidak terhubung dan SMTP tidak dikonfigurasi. Silakan hubungkan Gmail atau hubungi administrator untuk mengatur SMTP.'
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending email with attachments to {vendor_email}: {str(e)}")
            
            # Update email log with error
            if 'email_log' in locals():
                email_log.status = 'failed'
                email_log.error_message = str(e)
                db.session.commit()
            
            return {
                'success': False,
                'message': f'Gagal mengirim email dengan attachment: {str(e)}',
                'recipient': vendor_email,
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_via_gmail_api_with_attachments(self, user_id: int, to_email: str, subject: str, 
                                           html_content: str, text_content: str, 
                                           cc_emails: List[str], bcc_emails: List[str], 
                                           attachments: List) -> Dict[str, Any]:
        """Send email via Gmail API with attachments"""
        try:
            # Get user credentials
            credentials = self.gmail_oauth_service.get_user_gmail_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'message': 'Gmail tidak terhubung atau credentials tidak tersedia. Silakan hubungkan Gmail terlebih dahulu.',
                    'error_type': 'gmail_credentials_error'
                }
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=credentials)

            # Create message
            raw_message = self.gmail_oauth_service.create_message_with_attachments(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                attachments=attachments
            )
            
            # Debug logging
            logger.info(f"📧 Gmail API recipients: TO={to_email}, CC={cc_emails}, BCC={bcc_emails}")
            
            # Send main email (TO + CC)
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Send separate emails for BCC recipients (BCC must be sent separately)
            if bcc_emails:
                for bcc_email in bcc_emails:
                    try:
                        # Create BCC message with attachments (same content but only TO the BCC recipient)
                        bcc_message = self.gmail_oauth_service.create_message_with_attachments(
                            to_email=bcc_email,
                            subject=subject,
                            html_content=html_content,
                            text_content=text_content,
                            cc_emails=[],  # No CC for BCC emails
                            bcc_emails=[],  # No BCC for BCC emails
                            attachments=attachments
                        )
                        
                        # Send BCC email
                        bcc_result = service.users().messages().send(
                            userId='me',
                            body={'raw': bcc_message}
                        ).execute()
                        
                        logger.info(f"✅ BCC email with attachments sent to {bcc_email}: {bcc_result.get('id')}")
                    except Exception as e:
                        logger.error(f"❌ Failed to send BCC email with attachments to {bcc_email}: {str(e)}")
            
            return {
                'success': True,
                'message': 'Email berhasil dikirim via Gmail API',
                'message_id': result.get('id'),
                'recipient': to_email,
                'timestamp': datetime.now().isoformat(),
                'attachments_count': len(attachments)
            }
            
        except Exception as e:
            logger.error(f"❌ Error sending via Gmail API with attachments: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal mengirim via Gmail API: {str(e)}',
                'error_type': 'gmail_api_error'
            }
    
    def _send_via_smtp_with_attachments(self, to_email: str, subject: str, 
                                      html_content: str, text_content: str, 
                                      cc_emails: List[str], bcc_emails: List[str], 
                                      attachments: List) -> Dict[str, Any]:
        """Send email via SMTP with attachments"""
        try:
            # Check SMTP configuration
            if not self.smtp_username or not self.smtp_password:
                return {
                    'success': False,
                    'message': 'SMTP tidak dikonfigurasi',
                    'error_type': 'smtp_config_error'
                }
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add CC and BCC
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            if bcc_emails:
                msg['Bcc'] = ', '.join(bcc_emails)
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments
            for attachment in attachments:
                if os.path.exists(attachment.file_path):
                    with open(attachment.file_path, 'rb') as f:
                        attachment_part = MIMEBase('application', 'octet-stream')
                        attachment_part.set_payload(f.read())
                        encoders.encode_base64(attachment_part)
                        attachment_part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment.original_filename}'
                        )
                        msg.attach(attachment_part)
                        logger.info(f"📎 Attachment added: {attachment.original_filename}")
                else:
                    logger.warning(f"⚠️ Attachment file not found: {attachment.file_path}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # Prepare recipients
                recipients = [to_email]
                if cc_emails:
                    recipients.extend(cc_emails)
                if bcc_emails:
                    recipients.extend(bcc_emails)
                
                server.send_message(msg, to_addrs=recipients)
            
            return {
                'success': True,
                'message': 'Email berhasil dikirim via SMTP',
                'recipient': to_email,
                'timestamp': datetime.now().isoformat(),
                'attachments_count': len(attachments)
            }
            
        except Exception as e:
            logger.error(f"❌ Error sending via SMTP with attachments: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal mengirim via SMTP: {str(e)}',
                'error_type': 'smtp_error'
            }