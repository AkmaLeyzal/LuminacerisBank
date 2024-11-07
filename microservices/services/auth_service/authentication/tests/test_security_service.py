
# authentication/tests/test_security_service.py
from authentication.services.security_service import SecurityService
from django.core.cache import cache

class TestSecurityService:
    def test_rate_limit(self):
        """Test rate limiting functionality"""
        key = 'test_rate'
        
        # Should allow first 6 attempts
        for _ in range(6):
            assert SecurityService.check_rate_limit(key, 6, 300)
        
        # Should block 7th attempt
        assert not SecurityService.check_rate_limit(key, 6, 300)

    def test_device_id_generation(self):
        """Test device ID generation"""
        device_info1 = {
            'user_agent': 'Chrome',
            'platform': 'Windows',
            'browser': 'Chrome',
            'version': '90.0'
        }
        
        device_info2 = {
            'user_agent': 'Firefox',
            'platform': 'Mac',
            'browser': 'Firefox',
            'version': '88.0'
        }
        
        # Same device info should generate same ID
        assert SecurityService.generate_device_id(device_info1) == \
               SecurityService.generate_device_id(device_info1)
        
        # Different device info should generate different IDs
        assert SecurityService.generate_device_id(device_info1) != \
               SecurityService.generate_device_id(device_info2)
