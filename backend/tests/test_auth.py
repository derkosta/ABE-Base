"""
Tests for authentication functionality
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_user,
    get_current_user
)
from app.models.user import User, UserRole
from fastapi import HTTPException


class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_password_hashing_different_salts(self):
        """Test that same password produces different hashes"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """Test JWT token functionality"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid_token"
        payload = verify_token(invalid_token)
        
        assert payload is None

    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        data = {"sub": "testuser"}
        # Create token with very short expiry
        expires_delta = timedelta(milliseconds=1)
        token = create_access_token(data, expires_delta)
        
        # Wait for token to expire
        import time
        time.sleep(0.01)
        
        payload = verify_token(token)
        assert payload is None


class TestAuthentication:
    """Test authentication functionality"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def test_user(self):
        """Test user object"""
        return User(
            id="test-id",
            username="testuser",
            role=UserRole.USER,
            password_hash=get_password_hash("test_password"),
            is_active=True
        )

    def test_authenticate_user_valid(self, mock_db, test_user):
        """Test authentication with valid credentials"""
        mock_db.query.return_value.filter.return_value.first.return_value = test_user
        
        result = authenticate_user(mock_db, "testuser", "test_password")
        assert result == test_user

    def test_authenticate_user_invalid_password(self, mock_db, test_user):
        """Test authentication with invalid password"""
        mock_db.query.return_value.filter.return_value.first.return_value = test_user
        
        result = authenticate_user(mock_db, "testuser", "wrong_password")
        assert result is False

    def test_authenticate_user_nonexistent(self, mock_db):
        """Test authentication with nonexistent user"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = authenticate_user(mock_db, "nonexistent", "password")
        assert result is False

    def test_authenticate_user_inactive(self, mock_db, test_user):
        """Test authentication with inactive user"""
        test_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = test_user
        
        result = authenticate_user(mock_db, "testuser", "test_password")
        assert result is False


class TestGetCurrentUser:
    """Test get_current_user dependency"""

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request"""
        request = Mock()
        request.cookies = {}
        request.headers = {}
        return request

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def test_user(self):
        """Test user object"""
        return User(
            id="test-id",
            username="testuser",
            role=UserRole.USER,
            password_hash=get_password_hash("test_password"),
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_request, mock_db, test_user):
        """Test get_current_user with valid token"""
        token = create_access_token({"sub": "testuser"})
        mock_request.cookies = {"access_token": token}
        mock_db.query.return_value.filter.return_value.first.return_value = test_user
        
        # Mock the dependency injection
        with patch('app.core.auth.get_db', return_value=iter([mock_db])):
            result = await get_current_user(mock_request, None, mock_db)
            assert result == test_user

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, mock_request, mock_db):
        """Test get_current_user with no token"""
        with patch('app.core.auth.get_db', return_value=iter([mock_db])):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None, mock_db)
            
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_request, mock_db):
        """Test get_current_user with invalid token"""
        mock_request.cookies = {"access_token": "invalid_token"}
        
        with patch('app.core.auth.get_db', return_value=iter([mock_db])):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None, mock_db)
            
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, mock_request, mock_db):
        """Test get_current_user with nonexistent user"""
        token = create_access_token({"sub": "nonexistent"})
        mock_request.cookies = {"access_token": token}
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.core.auth.get_db', return_value=iter([mock_db])):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None, mock_db)
            
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, mock_request, mock_db, test_user):
        """Test get_current_user with inactive user"""
        test_user.is_active = False
        token = create_access_token({"sub": "testuser"})
        mock_request.cookies = {"access_token": token}
        mock_db.query.return_value.filter.return_value.first.return_value = test_user
        
        with patch('app.core.auth.get_db', return_value=iter([mock_db])):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None, mock_db)
            
            assert exc_info.value.status_code == 401
