import os
from dotenv import load_dotenv

# Try to load from multiple env files
for env_file in ['.env', 'config.env']:
    if os.path.exists(env_file):
        load_dotenv(env_file)
        break

class Config:
    """Application configuration class"""
    
    # Demo Mode Settings
    DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Satellite Imagery APIs
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN')
    
    # Application Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'kyc-geointelligent-demo-key-2024')
    
    # Risk Analysis Thresholds
    HIGH_RISK_THRESHOLD = float(os.getenv('HIGH_RISK_THRESHOLD', '0.7'))
    MEDIUM_RISK_THRESHOLD = float(os.getenv('MEDIUM_RISK_THRESHOLD', '0.4'))
    
    # Cache Settings
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '3600'))
    
    # OpenStreetMap Nominatim Settings
    OSM_USER_AGENT = os.getenv('OSM_USER_AGENT', "KYC-Geointelligent/1.0")
    
    # Satellite Image Analysis Settings
    IMAGE_ANALYSIS_TIMEOUT = int(os.getenv('IMAGE_ANALYSIS_TIMEOUT', '30'))
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '2048'))  # pixels
    
    @staticmethod
    def validate_config():
        """Validate that required configuration is present"""
        if Config.DEMO_MODE:
            # In demo mode, we don't require API keys
            return True
            
        required_keys = ['OPENAI_API_KEY']
        missing_keys = [key for key in required_keys if not getattr(Config, key)]
        
        if missing_keys:
            print(f"⚠️ Missing API keys: {', '.join(missing_keys)}")
            print("🚀 Running in DEMO mode - limited functionality")
            Config.DEMO_MODE = True
            return True
        
        return True
    
    @staticmethod
    def get_status():
        """Get configuration status"""
        return {
            'demo_mode': Config.DEMO_MODE,
            'openai_configured': bool(Config.OPENAI_API_KEY),
            'google_maps_configured': bool(Config.GOOGLE_MAPS_API_KEY),
            'mapbox_configured': bool(Config.MAPBOX_ACCESS_TOKEN)
        }
