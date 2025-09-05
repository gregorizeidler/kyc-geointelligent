#!/usr/bin/env python3
"""
KYC Geointelligent - Example Usage Script
Demonstrates how to use the KYC system programmatically
"""

import json
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.address_validator import AddressValidator
    from app.satellite_analyzer import SatelliteAnalyzer
    from app.risk_analyzer import RiskAnalyzer
    from config import Config
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have installed all dependencies with: pip install -r requirements.txt")
    sys.exit(1)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_result(result: dict, title: str = "Result"):
    """Pretty print analysis results"""
    print(f"\n{title}:")
    print("-" * 40)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_address_validation():
    """Example: Address validation only"""
    print_header("EXAMPLE 1: ADDRESS VALIDATION")
    
    validator = AddressValidator()
    
    # Test addresses
    addresses = [
        "Avenida Paulista, 1578, São Paulo, SP",
        "Rodovia dos Bandeirantes, km 25, Jundiaí, SP", 
        "Rua das Palmeiras, 123, house, Cotia, SP"
    ]
    
    for i, address in enumerate(addresses, 1):
        print(f"\n{i}. Validating: {address}")
        result = validator.validate_address(address)
        
        if result['is_valid']:
            print(f"✅ Valid: {result['formatted_address']}")
            print(f"📍 Coordinates: {result['coordinates']}")
            print(f"🏢 Type: {result['location_type']}")
        else:
            print(f"❌ Invalid: {result['error']}")


def example_satellite_analysis():
    """Example: Satellite image analysis"""
    print_header("EXAMPLE 2: SATELLITE IMAGE ANALYSIS")
    
    # Check if required API keys are configured
    if not Config.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not configured. Skipping satellite analysis.")
        return
    
    analyzer = SatelliteAnalyzer()
    
    # São Paulo coordinates (Avenida Paulista)
    lat, lon = -23.5613, -46.6565
    business_type = "Technology"
    
    print(f"🛰️ Analyzing location: {lat}, {lon}")
    print(f"📊 Business type: {business_type}")
    
    result = analyzer.analyze_location(lat, lon, business_type)
    
    if result['analysis_completed']:
        print("✅ Analysis completed!")
        print(f"🏢 Buildings detected: {result['visual_features'].get('building_detection', {}).get('building_count', 0)}")
        print(f"🚗 Vehicles detected: {result['visual_features'].get('vehicle_detection', {}).get('vehicle_count', 0)}")
        print(f"🤖 AI confidence: {result.get('confidence_score', 0):.2f}")
    else:
        print(f"❌ Analysis error: {result.get('error', 'Unknown')}")


def example_complete_kyc_analysis():
    """Example: Complete KYC analysis"""
    print_header("EXAMPLE 3: COMPLETE KYC ANALYSIS")
    
    # Sample companies for testing
    companies = [
        {
            'cnpj': '12345678000190',
            'address': 'Rodovia dos Bandeirantes, km 25, Jundiaí, SP',
            'business_type': 'Logistics',
            'declared_activity': 'Road freight transport',
            'expected': 'LOW risk (appropriate infrastructure)'
        },
        {
            'cnpj': '98765432000110', 
            'address': 'Rua das Palmeiras, 45, house, Cotia, SP',
            'business_type': 'Technology',
            'declared_activity': 'Software development',
            'expected': 'HIGH risk (residential address for tech company)'
        }
    ]
    
    # Initialize components
    address_validator = AddressValidator()
    risk_analyzer = RiskAnalyzer()
    
    # Only use satellite analyzer if OpenAI key is available
    if Config.OPENAI_API_KEY:
        satellite_analyzer = SatelliteAnalyzer()
    else:
        print("⚠️ OPENAI_API_KEY not configured. Satellite analysis will be simulated.")
        satellite_analyzer = None
    
    for i, company in enumerate(companies, 1):
        print(f"\n{'='*20} COMPANY {i} {'='*20}")
        print(f"CNPJ: {company['cnpj']}")
        print(f"Address: {company['address']}")
        print(f"Type: {company['business_type']}")
        print(f"Activity: {company['declared_activity']}")
        print(f"Expected: {company['expected']}")
        print("-" * 60)
        
        try:
            # Step 1: Address validation
            print("1️⃣ Validating address...")
            address_data = address_validator.validate_address(company['address'], company['cnpj'])
            
            if address_data['is_valid']:
                print(f"✅ Valid address: {address_data['location_type']}")
                
                # Step 2: Satellite analysis
                print("2️⃣ Analyzing satellite image...")
                if satellite_analyzer:
                    coordinates = address_data['coordinates']
                    satellite_data = satellite_analyzer.analyze_location(
                        coordinates[0], coordinates[1], company['business_type']
                    )
                else:
                    # Simulate satellite data for demo
                    satellite_data = {
                        'analysis_completed': True,
                        'visual_features': {
                            'building_detection': {'building_count': 2, 'total_building_area': 3000},
                            'vehicle_detection': {'vehicle_count': 5}
                        },
                        'infrastructure_assessment': {'positive_indicators': ['warehouse', 'loading dock']},
                        'risk_indicators': [],
                        'confidence_score': 0.8
                    }
                
                # Step 3: Risk analysis
                print("3️⃣ Calculating risk...")
                risk_result = risk_analyzer.analyze_comprehensive_risk(
                    company['cnpj'],
                    address_data,
                    satellite_data, 
                    company['business_type'],
                    company['declared_activity']
                )
                
                # Display results
                print("\n📋 ANALYSIS RESULT:")
                print(f"🎯 Risk Level: {risk_result['risk_level']}")
                print(f"📊 Score: {risk_result['overall_risk_score']:.3f}")
                print(f"🤖 Confidence: {risk_result['confidence_level']:.2f}")
                print(f"💡 Recommendation: {risk_result['recommendation']}")
                print(f"📝 Assessment: {risk_result['recommendation_text']}")
                
                if risk_result['risk_factors']:
                    print("\n⚠️ RISK FACTORS:")
                    for factor in risk_result['risk_factors'][:3]:
                        print(f"  • {factor}")
                
                if risk_result['positive_factors']:
                    print("\n✅ POSITIVE FACTORS:")
                    for factor in risk_result['positive_factors'][:3]:
                        print(f"  • {factor}")
            
            else:
                print(f"❌ Invalid address: {address_data['error']}")
                print("🚨 RESULT: HIGH RISK - Address not found")
        
        except Exception as e:
            print(f"❌ Analysis error: {str(e)}")


def example_api_simulation():
    """Example: Simulated API calls"""
    print_header("EXAMPLE 4: API CALLS SIMULATION")
    
    api_examples = [
        {
            'method': 'POST',
            'endpoint': '/api/kyc/analyze',
            'payload': {
                'cnpj': '12.345.678/0001-90',
                'address': 'Avenida Paulista, 1578, São Paulo, SP',
                'business_type': 'Technology',
                'declared_activity': 'Software development'
            }
        },
        {
            'method': 'POST', 
            'endpoint': '/api/kyc/batch',
            'payload': {
                'companies': [
                    {
                        'cnpj': '11.222.333/0001-44',
                        'address': 'Industrial District, Av. das Indústrias, 1000',
                        'business_type': 'Manufacturing',
                        'declared_activity': 'Metal parts manufacturing'
                    }
                ]
            }
        }
    ]
    
    for i, example in enumerate(api_examples, 1):
        print(f"\n📡 EXAMPLE {i}: {example['method']} {example['endpoint']}")
        print("\n🔹 Payload (JSON):")
        print(json.dumps(example['payload'], indent=2, ensure_ascii=False))
        
        print("\n🔹 cURL Command:")
        payload_str = json.dumps(example['payload'], ensure_ascii=False)
        print(f"""curl -X {example['method']} http://localhost:5000{example['endpoint']} \\
  -H "Content-Type: application/json" \\
  -d '{payload_str}'""")


def main():
    """Main function to run all examples"""
    print("🛰️ KYC GEOINTELLIGENT - USAGE EXAMPLES")
    print("=====================================")
    print("This script demonstrates the KYC Geointelligent system functionalities.")
    print("Make sure you have configured the necessary environment variables.")
    
    # Check configuration
    print(f"\n🔧 CONFIGURATION:")
    print(f"  ✅ OpenAI API Key: {'Configured' if Config.OPENAI_API_KEY else '❌ NOT CONFIGURED'}")
    print(f"  📡 Google Maps Key: {'Configured' if Config.GOOGLE_MAPS_API_KEY else 'Not configured (optional)'}")
    print(f"  🗺️ Mapbox Token: {'Configured' if Config.MAPBOX_ACCESS_TOKEN else 'Not configured (optional)'}")
    
    try:
        # Run examples
        example_address_validation()
        example_satellite_analysis() 
        example_complete_kyc_analysis()
        example_api_simulation()
        
        print_header("CONCLUSION")
        print("✅ Examples executed successfully!")
        print("📖 See README.md for more information")
        print("🔧 For production use, configure all API keys in the .env file")
        print("🌐 Run 'python app/web_app.py' to use the web interface")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Execution interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during execution: {str(e)}")
        print("🔍 Check if all dependencies are installed:")
        print("   pip install -r requirements.txt")


if __name__ == "__main__":
    main()