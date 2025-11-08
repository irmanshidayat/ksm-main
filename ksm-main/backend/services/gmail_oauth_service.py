#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail OAuth Service - Service untuk mengelola Gmail OAuth 2.0 authentication
"""

import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config.database import db
from config.config import Config
from models.knowledge_base import User

# Set environment variable to relax OAuth scope validation
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

logger = logging.getLogger(__name__)

class GmailOAuthService:
    """Service untuk mengelola Gmail OAuth 2.0 authentication"""
    
    def __init__(self):
        self.client_id = Config.GMAIL_CLIENT_ID
        self.client_secret = Config.GMAIL_CLIENT_SECRET
        self.redirect_uri = Config.GMAIL_REDIRECT_URI
        self.scopes = Config.GMAIL_SCOPES.split(',') if Config.GMAIL_SCOPES else [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
        # Gmail API credentials
        self.credentials_file = os.path.join(os.path.dirname(__file__), '..', 'gmail_credentials.json')
        
    def get_authorization_url(self) -> Dict[str, Any]:
        """
        Generate authorization URL untuk OAuth flow
        
        Returns:
            Dict dengan authorization URL dan state
        """
        try:
            # Buat flow dengan scopes yang lebih fleksibel untuk menangani scope openid
            flow_scopes = self.scopes.copy()
            # Tambahkan openid scope jika belum ada untuk menghindari error
            if 'openid' not in flow_scopes:
                flow_scopes.append('openid')
            
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=flow_scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            logger.info(f"✅ Generated Gmail authorization URL")
            
            return {
                'success': True,
                'authorization_url': authorization_url,
                'state': state
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating authorization URL: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating authorization URL: {str(e)}'
            }
    
    def handle_oauth_callback(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth callback dan simpan credentials
        
        Args:
            authorization_code: Authorization code dari callback
            state: State parameter untuk security
            
        Returns:
            Dict dengan status dan user info
        """
        try:
            # Buat flow dengan scopes yang lebih fleksibel untuk menangani scope openid
            flow_scopes = self.scopes.copy()
            # Tambahkan openid scope jika belum ada untuk menghindari error
            if 'openid' not in flow_scopes:
                flow_scopes.append('openid')
            
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=flow_scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange authorization code untuk tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Validasi scope yang diterima - hanya periksa scope yang diperlukan
            received_scopes = credentials.scopes if hasattr(credentials, 'scopes') else []
            required_scopes = set(self.scopes)
            received_scopes_set = set(received_scopes) if received_scopes else set()
            
            # Periksa apakah semua scope yang diperlukan ada
            # Google mungkin menambahkan scope tambahan seperti openid, gmail.readonly, gmail.modify
            # Ini normal dan tidak perlu dianggap sebagai error
            missing_scopes = required_scopes - received_scopes_set
            if missing_scopes:
                logger.warning(f"⚠️ Missing required scopes: {missing_scopes}")
                # Lanjutkan saja karena mungkin masih bisa berfungsi
            
            # Log scope yang diterima untuk debugging
            logger.info(f"✅ Received scopes: {received_scopes}")
            logger.info(f"✅ Required scopes: {list(required_scopes)}")
            
            # Validasi bahwa scope yang diterima mencakup scope minimum yang diperlukan
            # Minimal harus ada gmail.send untuk mengirim email
            essential_scopes = {
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/userinfo.email'
            }
            
            if not essential_scopes.issubset(received_scopes_set):
                missing_essential = essential_scopes - received_scopes_set
                logger.error(f"❌ Missing essential scopes: {missing_essential}")
                return {
                    'success': False,
                    'message': f'Missing essential Gmail scopes: {missing_essential}'
                }
            
            # Get user info
            user_info = self._get_user_info(credentials)
            
            logger.info(f"✅ Gmail OAuth callback successful for user: {user_info.get('email')}")
            
            return {
                'success': True,
                'message': 'Gmail connected successfully',
                'user_info': user_info,
                'credentials': {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling OAuth callback: {str(e)}")
            return {
                'success': False,
                'message': f'Error handling OAuth callback: {str(e)}'
            }
    
    def save_user_gmail_credentials(self, user_id: int, credentials: Dict[str, Any]) -> bool:
        """
        Simpan Gmail credentials ke database
        
        Args:
            user_id: ID user
            credentials: Gmail credentials
            
        Returns:
            Boolean success status
        """
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"❌ User with ID {user_id} not found")
                return False
            
            # Update user dengan Gmail credentials
            user.gmail_access_token = credentials.get('token')
            user.gmail_refresh_token = credentials.get('refresh_token')
            user.gmail_token_expires_at = datetime.fromisoformat(credentials.get('expires_at')) if credentials.get('expires_at') else None
            user.gmail_connected = True
            
            db.session.commit()
            
            logger.info(f"✅ Gmail credentials saved for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving Gmail credentials: {str(e)}")
            db.session.rollback()
            return False
    
    def get_user_gmail_credentials(self, user_id: int) -> Optional[Credentials]:
        """
        Get Gmail credentials untuk user
        
        Args:
            user_id: ID user
            
        Returns:
            Google Credentials object atau None
        """
        try:
            user = User.query.get(user_id)
            if not user or not user.gmail_connected:
                return None
            
            # Buat scopes yang fleksibel untuk menangani scope openid
            flow_scopes = self.scopes.copy()
            if 'openid' not in flow_scopes:
                flow_scopes.append('openid')
            
            credentials = Credentials(
                token=user.gmail_access_token,
                refresh_token=user.gmail_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=flow_scopes
            )
            
            # Refresh token jika expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update token baru ke database
                user.gmail_access_token = credentials.token
                user.gmail_token_expires_at = credentials.expiry
                db.session.commit()
            
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Error getting Gmail credentials: {str(e)}")
            return None
    
    def disconnect_gmail(self, user_id: int) -> bool:
        """
        Disconnect Gmail dari user
        
        Args:
            user_id: ID user
            
        Returns:
            Boolean success status
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Clear Gmail credentials
            user.gmail_access_token = None
            user.gmail_refresh_token = None
            user.gmail_token_expires_at = None
            user.gmail_connected = False
            
            db.session.commit()
            
            logger.info(f"✅ Gmail disconnected for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error disconnecting Gmail: {str(e)}")
            db.session.rollback()
            return False
    
    def send_email_via_gmail_api(self, user_id: int, to_email: str, subject: str, 
                                html_content: str, text_content: str = None,
                                cc_emails: list = None, bcc_emails: list = None) -> Dict[str, Any]:
        """
        Kirim email menggunakan Gmail API
        
        Args:
            user_id: ID user yang mengirim
            to_email: Email penerima
            subject: Subject email
            html_content: HTML content
            text_content: Text content (optional)
            cc_emails: List email CC (optional)
            bcc_emails: List email BCC (optional)
            
        Returns:
            Dict dengan status pengiriman
        """
        try:
            if cc_emails is None:
                cc_emails = []
            if bcc_emails is None:
                bcc_emails = []
                
            credentials = self.get_user_gmail_credentials(user_id)
            if not credentials:
                return {
                    'success': False,
                    'message': 'Gmail not connected or credentials expired'
                }
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create email message
            message = self._create_email_message(to_email, subject, html_content, text_content, cc_emails, bcc_emails)
            
            # Debug logging
            logger.info(f"📧 Gmail OAuth recipients: TO={to_email}, CC={cc_emails}, BCC={bcc_emails}")
            
            # Send main email (TO + CC)
            result = service.users().messages().send(
                userId='me',
                body={'raw': message}
            ).execute()
            
            # Send separate emails for BCC recipients (BCC must be sent separately)
            if bcc_emails:
                for bcc_email in bcc_emails:
                    try:
                        # Create BCC message (same content but only TO the BCC recipient)
                        bcc_message = self._create_email_message(
                            to_email=bcc_email,
                            subject=subject,
                            html_content=html_content,
                            text_content=text_content,
                            cc_emails=[],  # No CC for BCC emails
                            bcc_emails=[]  # No BCC for BCC emails
                        )
                        
                        # Send BCC email
                        bcc_result = service.users().messages().send(
                            userId='me',
                            body={'raw': bcc_message}
                        ).execute()
                        
                        logger.info(f"✅ BCC email sent to {bcc_email}: {bcc_result.get('id')}")
                    except Exception as e:
                        logger.error(f"❌ Failed to send BCC email to {bcc_email}: {str(e)}")
            
            logger.info(f"✅ Email sent via Gmail API: {result.get('id')}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'message_id': result.get('id'),
                'recipient': to_email,
                'cc_recipients': cc_emails,
                'bcc_recipients': bcc_emails,
                'timestamp': datetime.now().isoformat()
            }
            
        except HttpError as e:
            logger.error(f"❌ Gmail API error: {str(e)}")
            return {
                'success': False,
                'message': f'Gmail API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"❌ Error sending email via Gmail API: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }
    
    def _get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user info dari Google API"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture')
            }
        except Exception as e:
            logger.error(f"❌ Error getting user info: {str(e)}")
            return {}
    
    def _create_email_message(self, to_email: str, subject: str, 
                             html_content: str, text_content: str = None,
                             cc_emails: list = None, bcc_emails: list = None) -> str:
        """Create email message untuk Gmail API"""
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if cc_emails is None:
            cc_emails = []
        if bcc_emails is None:
            bcc_emails = []
            
        # Create message
        msg = MIMEMultipart('alternative')
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        
        # Note: BCC recipients are handled separately by Gmail API
        # BCC should not be added to email headers as they are "blind" copies
        
        # Add text part
        if text_content:
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
        
        # Add HTML part
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        return raw_message
    
    def create_message_with_attachments(self, to_email: str, subject: str, 
                                      html_content: str, text_content: str = None,
                                      cc_emails: list = None, bcc_emails: list = None,
                                      attachments: list = None) -> str:
        """Create email message dengan attachments untuk Gmail API"""
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        
        if cc_emails is None:
            cc_emails = []
        if bcc_emails is None:
            bcc_emails = []
        if attachments is None:
            attachments = []
            
        # Create message
        msg = MIMEMultipart('mixed')
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        
        # Note: BCC recipients are handled separately by Gmail API
        # BCC should not be added to email headers as they are "blind" copies
        
        # Create alternative part for text and HTML
        alternative_part = MIMEMultipart('alternative')
        
        # Add text part
        if text_content:
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            alternative_part.attach(text_part)
        
        # Add HTML part
        html_part = MIMEText(html_content, 'html', 'utf-8')
        alternative_part.attach(html_part)
        
        # Attach alternative part to main message
        msg.attach(alternative_part)
        
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
                    logger.info(f"📎 Gmail attachment added: {attachment.original_filename}")
            else:
                logger.warning(f"⚠️ Gmail attachment file not found: {attachment.file_path}")
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        return raw_message