#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Domain Service - Service untuk mengelola konfigurasi email domain per user
"""

import logging
import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from flask_jwt_extended import get_jwt_identity
from domains.email.models.email_models import UserEmailDomain
from config.database import db

logger = logging.getLogger(__name__)

class EmailDomainService:
    """Service untuk mengelola konfigurasi email domain per user"""
    
    def __init__(self):
        self.max_configs_per_user = int(os.getenv('EMAIL_DOMAIN_MAX_CONFIGS_PER_USER', '5'))
    
    def _sanitize_smtp_host(self, host: str) -> str:
        """Bersihkan host SMTP dari spasi/awalan protokol/trailing slash."""
        if not host:
            return host
        cleaned = host.strip()
        # Hapus awalan protokol umum jika ada
        for prefix in ('smtp://', 'smtps://', 'http://', 'https://'):
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        # Hapus trailing slash
        while cleaned.endswith('/'):
            cleaned = cleaned[:-1]
        return cleaned

    def _open_smtp_connection(self, host: str, port: int, username: str, password: str) -> smtplib.SMTP:
        """Buka koneksi SMTP sesuai port (SSL 465 atau STARTTLS 587/others) dan lakukan login.
        Mengembalikan instance smtplib.SMTP/SMTP_SSL yang sudah terautentikasi.
        """
        host = self._sanitize_smtp_host(host)
        override_host = os.getenv('EMAIL_DOMAIN_SMTP_HOST_OVERRIDE')
        if override_host:
            cleaned_override = self._sanitize_smtp_host(override_host)
            logger.warning(f"⚠️ Menggunakan SMTP host override dari ENV: {cleaned_override}")
            host = cleaned_override
        else:
            # Fallback: jika host tidak bisa di-resolve, coba IP langsung
            if 'mail.isinvitation.com' in host:
                logger.warning("⚠️ Fallback ke IP server untuk mail.isinvitation.com")
                host = '202.10.43.37'
        
        # Force insecure TLS untuk mengatasi masalah SSL certificate
        insecure_tls = True
        logger.info(f"🔧 SSL Configuration - insecure_tls: {insecure_tls} (forced for testing)")
        
        # Buat context SSL yang tidak memverifikasi sertifikat
        if insecure_tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.set_ciphers('DEFAULT@SECLEVEL=0')
            # Tambahan untuk mengatasi masalah SSL
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
        else:
            context = ssl.create_default_context()
        
        logger.debug(f"SMTP connect target host={host!r} port={port} insecure_tls={insecure_tls} check_hostname={context.check_hostname}")
        
        # Coba koneksi SSL/TLS terlebih dahulu
        try:
            # SSL/TLS langsung (465)
            if int(port) == 465:
                server = smtplib.SMTP_SSL(host, int(port), timeout=20, context=context)
                server.login(username, password)
                return server
            # Default: SMTP, upgrade ke STARTTLS bila memungkinkan/port 587
            server = smtplib.SMTP(host, int(port), timeout=20)
            server.ehlo()
            try:
                if int(port) == 587 or 'starttls' in getattr(server, 'esmtp_features', {}):
                    server.starttls(context=context)
                    server.ehlo()
            except smtplib.SMTPException:
                # Jika STARTTLS gagal, lanjutkan tanpa TLS (beberapa server mungkin tidak memerlukannya)
                pass
            server.login(username, password)
            return server
        except (ssl.SSLError, smtplib.SMTPException) as e:
            logger.warning(f"⚠️ SSL/TLS connection failed: {e}")
            if insecure_tls:
                logger.warning("⚠️ Mencoba koneksi tanpa SSL/TLS...")
                # Fallback: coba koneksi tanpa SSL/TLS
                try:
                    server = smtplib.SMTP(host, int(port), timeout=20)
                    server.ehlo()
                    server.login(username, password)
                    logger.info("✅ Fallback connection berhasil tanpa SSL/TLS")
                    return server
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback connection juga gagal: {fallback_error}")
                    raise e
            else:
                raise e
    
    def create_domain_config(self, user_id: int, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Buat konfigurasi email domain baru
        
        Args:
            user_id: ID user
            domain_data: Data konfigurasi domain
            
        Returns:
            Dict dengan status dan data konfigurasi
        """
        try:
            # Validasi jumlah konfigurasi per user
            existing_configs = UserEmailDomain.query.filter_by(user_id=user_id, is_active=True).count()
            if existing_configs >= self.max_configs_per_user:
                return {
                    'success': False,
                    'message': f'Maksimal {self.max_configs_per_user} konfigurasi domain per user'
                }
            
            # Validasi data input
            required_fields = ['domain_name', 'smtp_server', 'smtp_port', 'username', 'password', 'from_name']
            for field in required_fields:
                if field not in domain_data or not domain_data[field]:
                    return {
                        'success': False,
                        'message': f'Field {field} is required'
                    }
            
            # Cek apakah domain sudah ada untuk user ini
            existing_domain = UserEmailDomain.query.filter_by(
                user_id=user_id,
                domain_name=domain_data['domain_name'],
                is_active=True
            ).first()
            
            if existing_domain:
                return {
                    'success': False,
                    'message': f'Domain {domain_data["domain_name"]} sudah dikonfigurasi untuk user ini'
                }
            
            # Buat konfigurasi baru
            domain_config = UserEmailDomain(
                user_id=user_id,
                domain_name=domain_data['domain_name'],
                smtp_server=domain_data['smtp_server'],
                smtp_port=int(domain_data['smtp_port']),
                username=domain_data['username'],
                from_name=domain_data['from_name'],
                is_active=True,
                is_default=domain_data.get('is_default', False)
            )
            
            # Set password yang dienkripsi
            domain_config.set_password(domain_data['password'])
            
            # Jika ini adalah default, set yang lain menjadi non-default
            if domain_config.is_default:
                UserEmailDomain.query.filter_by(user_id=user_id).update({'is_default': False})
            
            db.session.add(domain_config)
            db.session.commit()
            
            logger.info(f"✅ Domain config created for user {user_id}: {domain_data['domain_name']}")
            
            return {
                'success': True,
                'message': 'Konfigurasi domain berhasil dibuat',
                'data': domain_config.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating domain config: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal membuat konfigurasi domain: {str(e)}'
            }
    
    def test_domain_connection(self, domain_config: UserEmailDomain) -> Dict[str, Any]:
        """
        Test koneksi SMTP domain
        
        Args:
            domain_config: Konfigurasi domain yang akan ditest
            
        Returns:
            Dict dengan status koneksi
        """
        try:
            # Validasi konfigurasi
            validation = domain_config.validate_config()
            if not validation['valid']:
                return {
                    'success': False,
                    'message': f'Konfigurasi tidak valid: {", ".join(validation["errors"])}'
                }
            
            # Decrypt password
            password = domain_config.get_decrypted_password()
            if not password:
                # Cek apakah encryption key ada
                encryption_key = os.getenv('EMAIL_DOMAIN_ENCRYPTION_KEY')
                if not encryption_key:
                    return {
                        'success': False,
                        'message': 'Gagal mendekripsi password: EMAIL_DOMAIN_ENCRYPTION_KEY tidak ditemukan. Pastikan environment variable sudah di-set di .env atau docker-compose.yml',
                        'error_type': 'encryption_key_missing'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Gagal mendekripsi password: Encryption key mungkin berbeda dengan yang digunakan saat enkripsi. Pastikan EMAIL_DOMAIN_ENCRYPTION_KEY sama dengan yang digunakan saat menyimpan password.',
                        'error_type': 'decryption_failed'
                    }
            
            # Test SMTP connection
            with self._open_smtp_connection(
                domain_config.smtp_server,
                domain_config.smtp_port,
                domain_config.username,
                password
            ) as server:
                # Koneksi berhasil jika bisa login; tidak perlu aksi tambahan
                pass
            
            logger.info(f"✅ SMTP connection test successful for {domain_config.domain_name}")
            
            return {
                'success': True,
                'message': 'Koneksi SMTP berhasil',
                'domain': domain_config.domain_name,
                'server': domain_config.smtp_server,
                'port': domain_config.smtp_port
            }
            
        except socket.gaierror as e:
            logger.error(f"❌ DNS resolve failed for {domain_config.smtp_server}: {str(e)}")
            return {
                'success': False,
                'message': 'Hostname SMTP tidak dapat di-resolve. Periksa smtp_server, DNS, atau koneksi internet.',
                'error_type': 'dns_error'
            }
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': 'Autentikasi SMTP gagal. Periksa username dan password.',
                'error_type': 'authentication_error'
            }
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ SMTP Connection failed for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': 'Koneksi ke server SMTP gagal. Periksa server dan port.',
                'error_type': 'connection_error'
            }
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"❌ SMTP server disconnected for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': 'Koneksi SMTP terputus. Coba ulangi atau periksa konfigurasi keamanan (TLS/SSL).',
                'error_type': 'server_disconnected'
            }
        except smtplib.SMTPException as e:
            logger.error(f"❌ General SMTP error for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': f'Kesalahan SMTP: {str(e)}',
                'error_type': 'smtp_error'
            }
        except Exception as e:
            logger.error(f"❌ SMTP test error for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': f'Error testing SMTP: {str(e)}',
                'error_type': 'general_error'
            }
    
    def send_email_via_domain(self, user_id: int, domain_id: int, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kirim email via domain yang dikonfigurasi
        
        Args:
            user_id: ID user
            domain_id: ID konfigurasi domain
            email_data: Data email yang akan dikirim
            
        Returns:
            Dict dengan status pengiriman
        """
        try:
            # Ambil konfigurasi domain
            domain_config = UserEmailDomain.query.filter_by(
                id=domain_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not domain_config:
                return {
                    'success': False,
                    'message': 'Konfigurasi domain tidak ditemukan atau tidak aktif'
                }
            
            # Decrypt password
            password = domain_config.get_decrypted_password()
            if not password:
                # Cek apakah encryption key ada
                encryption_key = os.getenv('EMAIL_DOMAIN_ENCRYPTION_KEY')
                if not encryption_key:
                    return {
                        'success': False,
                        'message': 'Gagal mendekripsi password domain: EMAIL_DOMAIN_ENCRYPTION_KEY tidak ditemukan. Pastikan environment variable sudah di-set di .env atau docker-compose.yml',
                        'error_type': 'encryption_key_missing'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Gagal mendekripsi password domain: Encryption key mungkin berbeda dengan yang digunakan saat enkripsi. Pastikan EMAIL_DOMAIN_ENCRYPTION_KEY sama dengan yang digunakan saat menyimpan password.',
                        'error_type': 'decryption_failed'
                    }
            
            # Validasi data email
            required_fields = ['vendor_email', 'vendor_name', 'items']
            for field in required_fields:
                if field not in email_data:
                    return {
                        'success': False,
                        'message': f'Field {field} is required'
                    }
            
            # Get attachments if provided
            attachments = []
            attachment_ids = email_data.get('attachment_ids', [])
            if attachment_ids:
                from domains.email.models.email_attachment_model import EmailAttachment
                attachments = db.session.query(EmailAttachment).filter(
                    EmailAttachment.id.in_(attachment_ids),
                    EmailAttachment.uploaded_by_user_id == user_id,
                    EmailAttachment.status == 'active'
                ).all()
                
                # Verify all files exist
                for attachment in attachments:
                    if not os.path.exists(attachment.file_path):
                        return {
                            'success': False,
                            'message': f'File attachment tidak ditemukan: {attachment.original_filename}'
                        }
            
            # Generate email content
            html_content = self._generate_email_template(
                email_data['vendor_name'],
                email_data['items'],
                email_data.get('custom_message', ''),
                email_data.get('subject', f"Permintaan Penawaran - {email_data['vendor_name']}")
            )
            
            text_content = self._generate_text_template(
                email_data['vendor_name'],
                email_data['items'],
                email_data.get('custom_message', ''),
                email_data.get('subject', f"Permintaan Penawaran - {email_data['vendor_name']}")
            )
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{domain_config.from_name} <{domain_config.username}>"
            msg['To'] = email_data['vendor_email']
            msg['Subject'] = email_data.get('subject', f"Permintaan Penawaran - {email_data['vendor_name']}")
            
            # Add Message-ID header (required by RFC 5322)
            import uuid
            import socket
            hostname = socket.gethostname()
            message_id = f"<{uuid.uuid4()}@{hostname}>"
            msg['Message-ID'] = message_id
            
            # Add Date header (required by RFC 5322)
            from email.utils import formatdate
            msg['Date'] = formatdate(localtime=True)
            
            # Add CC if provided
            cc_emails = email_data.get('cc_emails', [])
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
                logger.info(f"📧 Domain email CC added: {cc_emails}")
            else:
                logger.info("📧 Domain email: No CC emails provided")
            
            # Get BCC emails (BCC recipients are not visible to other recipients)
            bcc_emails = email_data.get('bcc_emails', [])
            if bcc_emails:
                logger.info(f"📧 Domain email BCC recipients: {bcc_emails}")
            else:
                logger.info("📧 Domain email: No BCC emails provided")
            
            # Add both text and HTML parts
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
                        logger.info(f"📎 Domain attachment added: {attachment.original_filename}")
                else:
                    logger.warning(f"⚠️ Domain attachment file not found: {attachment.file_path}")
            
            # Prepare recipients list (BCC is already defined above)
            recipients = [email_data['vendor_email']] + cc_emails + bcc_emails
            
            # Debug logging for recipients
            logger.info(f"📧 Domain email recipients: TO={email_data['vendor_email']}, CC={cc_emails}, BCC={bcc_emails}")
            logger.info(f"📧 Domain email all recipients: {recipients}")
            
            # Send main email (TO + CC)
            with self._open_smtp_connection(
                domain_config.smtp_server,
                domain_config.smtp_port,
                domain_config.username,
                password
            ) as server:
                # Send main email to TO + CC recipients
                main_recipients = [email_data['vendor_email']] + cc_emails
                server.send_message(msg, to_addrs=main_recipients)
                logger.info(f"📧 Domain main email sent to: {main_recipients}")
                
                # Send separate emails for BCC recipients (BCC must be sent separately)
                if bcc_emails:
                    for bcc_email in bcc_emails:
                        try:
                            # Create BCC message (same content but only TO the BCC recipient)
                            bcc_msg = MIMEMultipart('alternative')
                            bcc_msg['From'] = f"{domain_config.from_name} <{domain_config.username}>"
                            bcc_msg['To'] = bcc_email
                            bcc_msg['Subject'] = msg['Subject']
                            bcc_msg['Date'] = msg['Date']
                            bcc_msg['Message-ID'] = msg['Message-ID']
                            
                            # Add text and HTML parts
                            bcc_msg.attach(text_part)
                            bcc_msg.attach(html_part)
                            
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
                                        bcc_msg.attach(attachment_part)
                            
                            # Send BCC email
                            server.send_message(bcc_msg, to_addrs=[bcc_email])
                            logger.info(f"✅ Domain BCC email sent to: {bcc_email}")
                        except Exception as e:
                            logger.error(f"❌ Failed to send Domain BCC email to {bcc_email}: {str(e)}")
            
            logger.info(f"✅ Email sent via domain {domain_config.domain_name} to {email_data['vendor_email']}")
            
            return {
                'success': True,
                'message': f'Email berhasil dikirim via domain {domain_config.domain_name}',
                'recipient': email_data['vendor_email'],
                'domain': domain_config.domain_name,
                'timestamp': datetime.now().isoformat(),
                'attachments_count': len(attachments)
            }
            
        except socket.gaierror as e:
            logger.error(f"❌ DNS resolve failed for {domain_config.smtp_server}: {str(e)}")
            return {
                'success': False,
                'message': 'Hostname SMTP tidak dapat di-resolve. Periksa smtp_server, DNS, atau koneksi internet.',
                'recipient': email_data.get('vendor_email', 'unknown'),
                'error_type': 'dns_error'
            }
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': 'Autentikasi SMTP gagal. Periksa username dan password.',
                'recipient': email_data.get('vendor_email', 'unknown'),
                'error_type': 'authentication_error'
            }
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ SMTP Connection failed for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': 'Koneksi ke server SMTP gagal. Periksa server dan port.',
                'recipient': email_data.get('vendor_email', 'unknown'),
                'error_type': 'connection_error'
            }
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"❌ SMTP server disconnected for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': 'Koneksi SMTP terputus. Coba ulangi atau periksa konfigurasi keamanan (TLS/SSL).',
                'recipient': email_data.get('vendor_email', 'unknown'),
                'error_type': 'server_disconnected'
            }
        except smtplib.SMTPException as e:
            logger.error(f"❌ General SMTP error for {domain_config.domain_name}: {str(e)}")
            return {
                'success': False,
                'message': f'Kesalahan SMTP: {str(e)}',
                'recipient': email_data.get('vendor_email', 'unknown'),
                'error_type': 'smtp_error'
            }
        except Exception as e:
            logger.error(f"❌ Error sending email via domain: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal mengirim email via domain: {str(e)}',
                'recipient': email_data.get('vendor_email', 'unknown'),
                'error_type': 'general_error'
            }
    
    def get_user_domains(self, user_id: int) -> Dict[str, Any]:
        """
        Ambil semua konfigurasi domain user
        
        Args:
            user_id: ID user
            
        Returns:
            Dict dengan list konfigurasi domain
        """
        try:
            domains = UserEmailDomain.query.filter_by(
                user_id=user_id,
                is_active=True
            ).order_by(UserEmailDomain.is_default.desc(), UserEmailDomain.created_at.desc()).all()
            
            return {
                'success': True,
                'data': [domain.to_dict() for domain in domains],
                'count': len(domains)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user domains: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal mengambil konfigurasi domain: {str(e)}',
                'data': [],
                'count': 0
            }
    
    def set_default_domain(self, user_id: int, domain_id: int) -> Dict[str, Any]:
        """
        Set domain sebagai default untuk user
        
        Args:
            user_id: ID user
            domain_id: ID domain yang akan dijadikan default
            
        Returns:
            Dict dengan status
        """
        try:
            # Cek apakah domain milik user
            domain = UserEmailDomain.query.filter_by(
                id=domain_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not domain:
                return {
                    'success': False,
                    'message': 'Domain tidak ditemukan atau tidak aktif'
                }
            
            # Set semua domain user menjadi non-default
            UserEmailDomain.query.filter_by(user_id=user_id).update({'is_default': False})
            
            # Set domain yang dipilih menjadi default
            domain.is_default = True
            db.session.commit()
            
            logger.info(f"✅ Domain {domain.domain_name} set as default for user {user_id}")
            
            return {
                'success': True,
                'message': f'Domain {domain.domain_name} berhasil dijadikan default'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error setting default domain: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal mengatur domain default: {str(e)}'
            }
    
    def delete_domain_config(self, user_id: int, domain_id: int) -> Dict[str, Any]:
        """
        Hapus konfigurasi domain (soft delete)
        
        Args:
            user_id: ID user
            domain_id: ID domain yang akan dihapus
            
        Returns:
            Dict dengan status
        """
        try:
            domain = UserEmailDomain.query.filter_by(
                id=domain_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not domain:
                return {
                    'success': False,
                    'message': 'Domain tidak ditemukan atau tidak aktif'
                }
            
            # Soft delete
            domain.is_active = False
            db.session.commit()
            
            logger.info(f"✅ Domain {domain.domain_name} deleted for user {user_id}")
            
            return {
                'success': True,
                'message': f'Domain {domain.domain_name} berhasil dihapus'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error deleting domain config: {str(e)}")
            return {
                'success': False,
                'message': f'Gagal menghapus konfigurasi domain: {str(e)}'
            }
    
    def _generate_email_template(self, vendor_name: str, items: List[Dict], 
                                custom_message: str = None, subject: str = None) -> str:
        """Generate HTML email template"""
        
        if not custom_message:
            custom_message = f"""
            <p>Kepada Yth. {vendor_name},</p>
            <p>Kami ingin meminta penawaran untuk barang-barang berikut:</p>
            """
        
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
                    <h2>📧 {subject}</h2>
                    <p><strong>Kepada:</strong> {vendor_name}</p>
                    <p><strong>Tanggal:</strong> {datetime.now().strftime('%d %B %Y')}</p>
                </div>
                
                <div class="content">
                    {custom_message}
                    
                    <h3>📋 Daftar Barang yang Diminta:</h3>
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

Kami ingin meminta penawaran untuk barang-barang berikut:
            """
        
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
