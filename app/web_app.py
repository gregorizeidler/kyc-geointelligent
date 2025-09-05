"""
Web Interface for KYC Geointelligent System
Flask application providing a web interface for the KYC system
"""

from flask import Flask, render_template, request, jsonify
import logging
from datetime import datetime
import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kyc_api import kyc_api, app as api_app
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use the same Flask app instance from kyc_api
app = api_app


@app.route('/')
def index():
    """Main web interface page"""
    return render_template('index.html')


@app.route('/demo')
def demo():
    """Demo page with sample data"""
    sample_companies = [
        {
            'name': 'TransLog Transportes Ltd',
            'cnpj': '12.345.678/0001-90',
            'address': 'Rodovia dos Bandeirantes, km 25, Jundiaí, SP',
            'business_type': 'Logistics',
            'declared_activity': 'Road freight transport',
            'expected_risk': 'LOW'
        },
        {
            'name': 'TechSoft Solutions',
            'cnpj': '98.765.432/0001-10', 
            'address': 'Rua das Palmeiras, 45, house, Cotia, SP',
            'business_type': 'Technology',
            'declared_activity': 'Software development',
            'expected_risk': 'HIGH'
        },
        {
            'name': 'ABC Metallurgical Industry',
            'cnpj': '11.222.333/0001-44',
            'address': 'Industrial District, Av. das Indústrias, 1000, Santo André, SP', 
            'business_type': 'Manufacturing',
            'declared_activity': 'Metal parts manufacturing',
            'expected_risk': 'LOW'
        }
    ]
    
    return render_template('demo.html', companies=sample_companies)


@app.route('/about')
def about():
    """About page with system information"""
    system_info = {
        'version': '1.0.0',
        'description': 'AI system for KYC risk analysis using geospatial analysis',
        'features': [
            'Automatic address validation with OpenStreetMap',
            'Satellite image analysis with computer vision',
            'Contextual analysis with GPT-4 Vision',
            'Automated risk scoring',
            'REST API for integration'
        ],
        'technology_stack': [
            'Python Flask for web API',
            'OpenCV for image analysis',
            'OpenAI GPT-4 Vision for contextual analysis', 
            'GeoPy for geocoding',
            'Bootstrap for web interface'
        ]
    }
    
    return render_template('about.html', info=system_info)


@app.route('/api-docs')
def api_documentation():
    """API documentation page"""
    return render_template('api_docs.html')


@app.errorhandler(404)
def not_found_error(error):
    """404 error handler"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error"), 500


if __name__ == '__main__':
    logger.info("Starting KYC Geointelligent Web Application...")
    
    # Ensure templates directory exists
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(template_dir):
        logger.warning(f"Templates directory not found: {template_dir}")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.FLASK_DEBUG
    )
