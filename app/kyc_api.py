"""
KYC Geointelligent API
Main API interface for the KYC Geointelligent system
"""

from flask import Flask, request, jsonify
import logging
from datetime import datetime
import json
from typing import Dict, Optional

from address_validator import AddressValidator
from satellite_analyzer import SatelliteAnalyzer
from risk_analyzer import RiskAnalyzer
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
address_validator = AddressValidator(Config.OSM_USER_AGENT)
satellite_analyzer = SatelliteAnalyzer()
risk_analyzer = RiskAnalyzer()


class KYCGeointelligentAPI:
    """Main API class for KYC Geointelligent system"""
    
    def __init__(self):
        """Initialize the API with required components"""
        try:
            Config.validate_config()
            self.initialized = True
            logger.info("KYC Geointelligent API initialized successfully")
        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            self.initialized = False
    
    def process_kyc_request(
        self, 
        cnpj: str, 
        address: str, 
        business_type: str, 
        declared_activity: str
    ) -> Dict:
        """
        Main processing function for KYC requests
        
        Args:
            cnpj: Company CNPJ
            address: Business address
            business_type: Type of business (e.g., "Logistics")
            declared_activity: Detailed business activity description
            
        Returns:
            Complete KYC analysis result
        """
        if not self.initialized:
            return {
                'error': 'API not properly initialized. Check configuration.',
                'status': 'error'
            }
        
        start_time = datetime.now()
        logger.info(f"Starting KYC analysis for CNPJ: {cnpj}")
        
        result = {
            'request_id': f"kyc_{cnpj}_{int(start_time.timestamp())}",
            'cnpj': cnpj,
            'address_input': address,
            'business_type': business_type,
            'declared_activity': declared_activity,
            'analysis_timestamp': start_time.isoformat(),
            'processing_time_seconds': 0,
            'status': 'processing'
        }
        
        try:
            # Step 1: Address validation
            logger.info("Step 1: Validating address...")
            address_data = address_validator.validate_address(address, cnpj)
            
            if not address_data['is_valid']:
                result.update({
                    'status': 'completed',
                    'risk_level': 'HIGH',
                    'recommendation': 'BLOCK',
                    'recommendation_text': f"🚨 HIGH RISK: Invalid or not found address: {address_data.get('error', 'Address not located')}",
                    'address_validation': address_data,
                    'processing_time_seconds': (datetime.now() - start_time).total_seconds()
                })
                return result
            
            # Step 2: Satellite analysis
            logger.info("Step 2: Analyzing satellite imagery...")
            coordinates = address_data['coordinates']
            satellite_data = satellite_analyzer.analyze_location(
                coordinates[0], coordinates[1], business_type
            )
            
            # Step 3: Comprehensive risk analysis
            logger.info("Step 3: Performing comprehensive risk analysis...")
            risk_analysis = risk_analyzer.analyze_comprehensive_risk(
                cnpj, address_data, satellite_data, business_type, declared_activity
            )
            
            # Step 4: Compile final result
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result.update({
                'status': 'completed',
                'processing_time_seconds': processing_time,
                'risk_level': risk_analysis.get('risk_level', 'UNKNOWN'),
                'overall_risk_score': risk_analysis.get('overall_risk_score', 0.5),
                'recommendation': risk_analysis.get('recommendation', 'MANUAL_REVIEW'),
                'recommendation_text': risk_analysis.get('recommendation_text', ''),
                'confidence_level': risk_analysis.get('confidence_level', 0.5),
                'risk_factors': risk_analysis.get('risk_factors', []),
                'positive_factors': risk_analysis.get('positive_factors', []),
                'detailed_analysis': {
                    'address_validation': address_data,
                    'satellite_analysis': satellite_data,
                    'risk_assessment': risk_analysis.get('detailed_assessment', {})
                }
            })
            
            logger.info(f"KYC analysis completed for {cnpj} in {processing_time:.2f}s - Risk: {result['risk_level']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing KYC request for {cnpj}: {str(e)}")
            result.update({
                'status': 'error',
                'error': str(e),
                'risk_level': 'HIGH',
                'recommendation': 'MANUAL_REVIEW',
                'recommendation_text': f"🚨 ANALYSIS ERROR: {str(e)}. Forward for manual review.",
                'processing_time_seconds': (datetime.now() - start_time).total_seconds()
            })
            return result


# Initialize API instance
kyc_api = KYCGeointelligentAPI()


# Flask routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'initialized': kyc_api.initialized,
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/kyc/analyze', methods=['POST'])
def analyze_kyc():
    """
    Main KYC analysis endpoint
    
    Expected JSON payload:
    {
        "cnpj": "12.345.678/0001-90",
        "address": "Rua das Flores, 123, São Paulo, SP",
        "business_type": "Logistics",
        "declared_activity": "Transporte rodoviário de cargas"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['cnpj', 'address', 'business_type', 'declared_activity']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'status': 'error'
            }), 400
        
        # Clean and validate CNPJ format
        cnpj = data['cnpj'].replace('.', '').replace('/', '').replace('-', '')
        if len(cnpj) != 14 or not cnpj.isdigit():
            return jsonify({
                'error': 'Invalid CNPJ format. Expected format: XX.XXX.XXX/XXXX-XX',
                'status': 'error'
            }), 400
        
        # Process KYC request
        result = kyc_api.process_kyc_request(
            cnpj=cnpj,
            address=data['address'].strip(),
            business_type=data['business_type'].strip(),
            declared_activity=data['declared_activity'].strip()
        )
        
        # Return appropriate HTTP status code
        status_code = 200 if result['status'] == 'completed' else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error in analyze_kyc endpoint: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500


@app.route('/api/kyc/batch', methods=['POST'])
def batch_analyze():
    """
    Batch KYC analysis endpoint for multiple companies
    
    Expected JSON payload:
    {
        "companies": [
            {
                "cnpj": "12.345.678/0001-90",
                "address": "Rua das Flores, 123, São Paulo, SP", 
                "business_type": "Logistics",
                "declared_activity": "Transporte rodoviário de cargas"
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        companies = data.get('companies', [])
        
        if not companies:
            return jsonify({
                'error': 'No companies provided for analysis',
                'status': 'error'
            }), 400
        
        if len(companies) > 10:  # Limit batch size
            return jsonify({
                'error': 'Batch size limited to 10 companies',
                'status': 'error'
            }), 400
        
        results = []
        for i, company in enumerate(companies):
            try:
                # Validate required fields for each company
                required_fields = ['cnpj', 'address', 'business_type', 'declared_activity']
                missing_fields = [field for field in required_fields if not company.get(field)]
                
                if missing_fields:
                    results.append({
                        'company_index': i,
                        'error': f'Missing required fields: {", ".join(missing_fields)}',
                        'status': 'error'
                    })
                    continue
                
                # Process individual company
                result = kyc_api.process_kyc_request(
                    cnpj=company['cnpj'],
                    address=company['address'],
                    business_type=company['business_type'],
                    declared_activity=company['declared_activity']
                )
                result['company_index'] = i
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing company {i}: {str(e)}")
                results.append({
                    'company_index': i,
                    'error': str(e),
                    'status': 'error'
                })
        
        return jsonify({
            'batch_results': results,
            'total_companies': len(companies),
            'successful_analyses': len([r for r in results if r.get('status') == 'completed']),
            'failed_analyses': len([r for r in results if r.get('status') == 'error'])
        })
        
    except Exception as e:
        logger.error(f"Error in batch_analyze endpoint: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500


@app.route('/api/documentation', methods=['GET'])
def get_documentation():
    """Returns API documentation"""
    docs = {
        'title': 'KYC Geointelligent API',
        'version': '1.0.0',
        'description': 'AI-powered geospatial KYC analysis for corporate clients',
        'endpoints': {
            '/health': {
                'method': 'GET',
                'description': 'Health check endpoint',
                'response': 'Status and system information'
            },
            '/api/kyc/analyze': {
                'method': 'POST',
                'description': 'Analyze single company for KYC risk assessment',
                'required_fields': ['cnpj', 'address', 'business_type', 'declared_activity'],
                'response': 'Complete risk analysis with score and recommendations'
            },
            '/api/kyc/batch': {
                'method': 'POST', 
                'description': 'Batch analysis for multiple companies (max 10)',
                'required_fields': ['companies array with individual company objects'],
                'response': 'Array of analysis results for each company'
            }
        },
        'risk_levels': {
            'LOW': 'Score < 0.4 - Auto-approval recommended',
            'MEDIUM': '0.4 <= Score < 0.7 - Manual review recommended', 
            'HIGH': 'Score >= 0.7 - Block registration recommended'
        }
    }
    return jsonify(docs)


if __name__ == '__main__':
    # Development server
    logger.info("Starting KYC Geointelligent API server...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.FLASK_DEBUG
    )
