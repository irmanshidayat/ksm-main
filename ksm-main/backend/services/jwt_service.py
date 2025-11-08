from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    get_jwt_identity,
    jwt_required,
    get_jwt
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class JWTService:
    """Service untuk mengelola JWT tokens"""
    
    @staticmethod
    def create_tokens(user_id: int, username: str, role: str):
        """
        Membuat access token dan refresh token untuk user
        
        Args:
            user_id: ID user
            username: Username user
            role: Role user
            
        Returns:
            dict: Berisi access_token, refresh_token, dan expires_in
        """
        try:
            # Ensure user_id is string for JWT identity
            user_id_str = str(user_id)
            
            # Create access token dengan claims
            access_token = create_access_token(
                identity=user_id_str,
                additional_claims={
                    'username': username,
                    'role': role,
                    'type': 'access'
                }
            )
            
            # Create refresh token
            refresh_token = create_refresh_token(
                identity=user_id_str,
                additional_claims={
                    'username': username,
                    'role': role,
                    'type': 'refresh'
                }
            )
            
            # Calculate expiration time (15 minutes)
            expires_in = 15 * 60  # 15 minutes in seconds
            
            logger.info(f"✅ Tokens created for user {username} (ID: {user_id})")
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': expires_in,
                'token_type': 'Bearer'
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating tokens for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def refresh_access_token():
        """
        Refresh access token menggunakan refresh token
        
        Returns:
            dict: Berisi access_token baru dan expires_in
        """
        try:
            from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt
            
            current_user_id = get_jwt_identity()
            current_token = get_jwt()
            
            # Ensure user_id is string
            user_id_str = str(current_user_id) if current_user_id else None
            
            if not user_id_str:
                raise Exception("Invalid user identity")
            
            # Create new access token
            new_access_token = create_access_token(
                identity=user_id_str,
                additional_claims={
                    'username': current_token.get('username', ''),
                    'role': current_token.get('role', ''),
                    'type': 'access'
                }
            )
            
            # Calculate expiration time
            expires_in = 15 * 60  # 15 minutes
            
            logger.info(f"✅ Access token refreshed for user ID: {user_id_str}")
            
            return {
                'access_token': new_access_token,
                'expires_in': expires_in,
                'token_type': 'Bearer'
            }
            
        except Exception as e:
            logger.error(f"❌ Error refreshing access token: {str(e)}")
            raise
    
    @staticmethod
    def get_current_user_info():
        """
        Mendapatkan informasi user dari current token
        
        Returns:
            dict: Berisi user_id, username, dan role
        """
        try:
            current_user_id = get_jwt_identity()
            current_token = get_jwt()
            
            # Ensure user_id is string
            user_id_str = str(current_user_id) if current_user_id else None
            
            return {
                'user_id': user_id_str,
                'username': current_token.get('username', ''),
                'role': current_token.get('role', '')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting current user info: {str(e)}")
            return None
    
    @staticmethod
    def validate_token_structure(token_data):
        """
        Validasi struktur token data
        
        Args:
            token_data: Data token yang akan divalidasi
            
        Returns:
            bool: True jika valid, False jika tidak
        """
        required_fields = ['access_token', 'refresh_token', 'expires_in']
        
        for field in required_fields:
            if field not in token_data:
                logger.error(f"❌ Missing required field: {field}")
                return False
        
        if not isinstance(token_data['expires_in'], int):
            logger.error("❌ expires_in must be an integer")
            return False
        
        return True
    
    @staticmethod
    def log_token_usage(user_id: int, username: str, action: str):
        """
        Log penggunaan token untuk audit
        
        Args:
            user_id: ID user
            username: Username
            action: Action yang dilakukan (login, refresh, logout)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"🔐 Token usage - User: {username} (ID: {user_id}) - Action: {action} - Time: {timestamp}")
    
    @staticmethod
    def create_logout_response():
        """
        Membuat response untuk logout
        
        Returns:
            dict: Response untuk logout
        """
        return {
            'success': True,
            'message': 'Logout berhasil',
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def create_error_response(error_message: str, status_code: int = 400):
        """
        Membuat error response
        
        Args:
            error_message: Pesan error
            status_code: HTTP status code
            
        Returns:
            tuple: (response_dict, status_code)
        """
        return {
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }, status_code
