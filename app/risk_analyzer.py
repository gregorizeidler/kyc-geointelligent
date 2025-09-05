"""
Risk Analysis Module
Combines address validation and satellite analysis to generate comprehensive risk scores
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime
import json
from config import Config

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Main risk analysis engine that combines all data sources"""
    
    def __init__(self):
        """Initialize risk analyzer with thresholds"""
        self.high_risk_threshold = Config.HIGH_RISK_THRESHOLD
        self.medium_risk_threshold = Config.MEDIUM_RISK_THRESHOLD
        
        # Business type mappings for expected infrastructure
        self.business_infrastructure_mapping = {
            'logistics': ['industrial', 'warehouse', 'loading_dock'],
            'transport': ['industrial', 'warehouse', 'vehicle_maintenance'],
            'manufacturing': ['industrial', 'factory', 'warehouse'],
            'technology': ['office', 'commercial'],
            'consulting': ['office', 'commercial'],
            'retail': ['commercial', 'storefront'],
            'restaurant': ['commercial', 'food_service'],
            'construction': ['industrial', 'warehouse', 'equipment_storage']
        }
    
    def analyze_comprehensive_risk(
        self, 
        cnpj: str,
        address_data: Dict,
        satellite_data: Dict,
        business_type: str,
        declared_activity: str
    ) -> Dict:
        """
        Performs comprehensive risk analysis combining all data sources
        
        Args:
            cnpj: Company CNPJ
            address_data: Results from address validation
            satellite_data: Results from satellite analysis  
            business_type: Primary business category
            declared_activity: Detailed business activity description
            
        Returns:
            Complete risk assessment with score and recommendations
        """
        analysis_result = {
            'cnpj': cnpj,
            'analysis_timestamp': datetime.now().isoformat(),
            'address_validation': address_data,
            'satellite_analysis': satellite_data,
            'business_information': {
                'type': business_type,
                'declared_activity': declared_activity
            },
            'risk_factors': [],
            'positive_factors': [],
            'overall_risk_score': 0.0,
            'risk_level': 'UNKNOWN',
            'recommendation': 'MANUAL_REVIEW',
            'detailed_assessment': {},
            'confidence_level': 0.0
        }
        
        try:
            # 1. Address validation analysis
            address_risk = self._analyze_address_risk(address_data, business_type)
            analysis_result['detailed_assessment']['address_risk'] = address_risk
            
            # 2. Satellite imagery analysis
            satellite_risk = self._analyze_satellite_risk(satellite_data, business_type)
            analysis_result['detailed_assessment']['satellite_risk'] = satellite_risk
            
            # 3. Business compatibility analysis
            compatibility_risk = self._analyze_business_compatibility(
                address_data, satellite_data, business_type, declared_activity
            )
            analysis_result['detailed_assessment']['compatibility_risk'] = compatibility_risk
            
            # 4. Calculate overall risk score
            overall_score = self._calculate_overall_risk_score(
                address_risk, satellite_risk, compatibility_risk
            )
            
            # 5. Generate final assessment
            final_assessment = self._generate_final_assessment(overall_score, analysis_result)
            analysis_result.update(final_assessment)
            
            logger.info(f"Risk analysis completed for CNPJ: {cnpj}, Score: {overall_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error in comprehensive risk analysis: {str(e)}")
            analysis_result['error'] = str(e)
            analysis_result['risk_level'] = 'HIGH'
            analysis_result['recommendation'] = 'MANUAL_REVIEW'
        
        return analysis_result
    
    def _analyze_address_risk(self, address_data: Dict, business_type: str) -> Dict:
        """Analyzes risk factors from address validation data"""
        risk_analysis = {
            'risk_score': 0.0,
            'risk_factors': [],
            'positive_factors': [],
            'address_quality': 'UNKNOWN'
        }
        
        # Check if address validation was successful
        if not address_data.get('is_valid', False):
            risk_analysis['risk_score'] = 0.9
            risk_analysis['risk_factors'].append("Address not found or invalid")
            risk_analysis['address_quality'] = 'INVALID'
            return risk_analysis
        
        # Analyze location type compatibility
        location_type = address_data.get('location_type', 'unknown')
        expected_locations = self._get_expected_locations(business_type)
        
        if location_type == 'residential':
            risk_analysis['risk_score'] += 0.4
            risk_analysis['risk_factors'].append(
                "Business registered at residential address"
            )
        elif location_type in expected_locations:
            risk_analysis['positive_factors'].append(
                f"Address in appropriate {location_type} area"
            )
        elif location_type == 'commercial' and business_type not in ['technology', 'consulting']:
            risk_analysis['risk_score'] += 0.1
            risk_analysis['risk_factors'].append(
                "Business type may not match commercial location"
            )
        
        # Analyze neighborhood context
        neighborhood = address_data.get('neighborhood_context', 'unknown')
        if neighborhood == 'remote' or neighborhood == 'rural':
            if business_type in ['technology', 'consulting']:
                risk_analysis['risk_score'] += 0.3
                risk_analysis['risk_factors'].append(
                    "Tech/consulting business in remote location"
                )
        
        # Check for amenities that support business legitimacy
        amenities = address_data.get('nearby_amenities', [])
        business_supporting_amenities = ['bank', 'office', 'commercial', 'industrial']
        if any(amenity in business_supporting_amenities for amenity in amenities):
            risk_analysis['positive_factors'].append(
                "Business-supporting amenities nearby"
            )
        
        # Set address quality
        if risk_analysis['risk_score'] < 0.2:
            risk_analysis['address_quality'] = 'EXCELLENT'
        elif risk_analysis['risk_score'] < 0.4:
            risk_analysis['address_quality'] = 'GOOD'
        else:
            risk_analysis['address_quality'] = 'POOR'
        
        return risk_analysis
    
    def _analyze_satellite_risk(self, satellite_data: Dict, business_type: str) -> Dict:
        """Analyzes risk factors from satellite imagery analysis"""
        risk_analysis = {
            'risk_score': 0.0,
            'risk_factors': [],
            'positive_factors': [],
            'infrastructure_quality': 'UNKNOWN'
        }
        
        # Check if satellite analysis was successful
        if not satellite_data.get('analysis_completed', False):
            risk_analysis['risk_score'] = 0.3
            risk_analysis['risk_factors'].append("Satellite analysis unavailable")
            return risk_analysis
        
        # Analyze visual features
        visual_features = satellite_data.get('visual_features', {})
        building_detection = visual_features.get('building_detection', {})
        
        # Check building presence and size
        building_count = building_detection.get('building_count', 0)
        largest_building = building_detection.get('largest_building_area', 0)
        
        if building_count == 0:
            risk_analysis['risk_score'] += 0.5
            risk_analysis['risk_factors'].append("No buildings detected at registered address")
        elif building_count > 0 and largest_building > 5000:  # Large building
            risk_analysis['positive_factors'].append("Substantial building infrastructure present")
        
        # Analyze vehicle presence (activity indicator)
        vehicle_detection = visual_features.get('vehicle_detection', {})
        vehicle_count = vehicle_detection.get('vehicle_count', 0)
        
        if vehicle_count > 5:
            risk_analysis['positive_factors'].append("Multiple vehicles present - signs of activity")
        elif vehicle_count == 0 and business_type in ['logistics', 'transport']:
            risk_analysis['risk_score'] += 0.3
            risk_analysis['risk_factors'].append(
                "No vehicles visible for logistics/transport business"
            )
        
        # Analyze AI contextual assessment
        infrastructure_assessment = satellite_data.get('infrastructure_assessment', {})
        positive_indicators = infrastructure_assessment.get('positive_indicators', [])
        
        if len(positive_indicators) >= 3:
            risk_analysis['positive_factors'].append(
                "Strong infrastructure indicators from AI analysis"
            )
        elif len(positive_indicators) == 0:
            risk_analysis['risk_score'] += 0.2
            risk_analysis['risk_factors'].append(
                "Limited infrastructure indicators"
            )
        
        # Check AI-identified risk indicators
        ai_risk_indicators = satellite_data.get('risk_indicators', [])
        if ai_risk_indicators:
            risk_analysis['risk_score'] += min(0.4, len(ai_risk_indicators) * 0.1)
            risk_analysis['risk_factors'].extend(ai_risk_indicators[:3])  # Top 3 risks
        
        # Set infrastructure quality
        if risk_analysis['risk_score'] < 0.2 and len(positive_indicators) >= 2:
            risk_analysis['infrastructure_quality'] = 'EXCELLENT'
        elif risk_analysis['risk_score'] < 0.4:
            risk_analysis['infrastructure_quality'] = 'ADEQUATE'
        else:
            risk_analysis['infrastructure_quality'] = 'POOR'
        
        return risk_analysis
    
    def _analyze_business_compatibility(
        self, 
        address_data: Dict, 
        satellite_data: Dict, 
        business_type: str, 
        declared_activity: str
    ) -> Dict:
        """Analyzes compatibility between declared business and observed infrastructure"""
        
        compatibility_analysis = {
            'risk_score': 0.0,
            'compatibility_rating': 'UNKNOWN',
            'risk_factors': [],
            'positive_factors': []
        }
        
        # Get expected infrastructure for business type
        expected_infrastructure = self.business_infrastructure_mapping.get(
            business_type.lower(), []
        )
        
        # Check location type compatibility
        location_type = address_data.get('location_type', 'unknown')
        
        # High-risk incompatibilities
        if business_type.lower() in ['logistics', 'manufacturing'] and location_type == 'residential':
            compatibility_analysis['risk_score'] += 0.6
            compatibility_analysis['risk_factors'].append(
                f"Industrial {business_type} business at residential location"
            )
        
        # Medium-risk incompatibilities  
        if business_type.lower() in ['technology', 'consulting'] and location_type == 'industrial':
            compatibility_analysis['risk_score'] += 0.2
            compatibility_analysis['risk_factors'].append(
                f"{business_type} business in industrial area (unusual but possible)"
            )
        
        # Analyze infrastructure size vs business type
        visual_features = satellite_data.get('visual_features', {})
        building_detection = visual_features.get('building_detection', {})
        total_building_area = building_detection.get('total_building_area', 0)
        
        # Large infrastructure expectations
        if business_type.lower() in ['logistics', 'manufacturing']:
            if total_building_area < 1000:  # Small infrastructure
                compatibility_analysis['risk_score'] += 0.3
                compatibility_analysis['risk_factors'].append(
                    "Small infrastructure for industrial business type"
                )
            else:
                compatibility_analysis['positive_factors'].append(
                    "Adequate infrastructure size for business type"
                )
        
        # Activity level analysis
        vehicle_count = visual_features.get('vehicle_detection', {}).get('vehicle_count', 0)
        if business_type.lower() in ['logistics', 'transport']:
            if vehicle_count < 2:
                compatibility_analysis['risk_score'] += 0.2
                compatibility_analysis['risk_factors'].append(
                    "Low vehicle activity for transport/logistics business"
                )
        
        # Set compatibility rating
        if compatibility_analysis['risk_score'] < 0.15:
            compatibility_analysis['compatibility_rating'] = 'EXCELLENT'
        elif compatibility_analysis['risk_score'] < 0.35:
            compatibility_analysis['compatibility_rating'] = 'GOOD'
        elif compatibility_analysis['risk_score'] < 0.55:
            compatibility_analysis['compatibility_rating'] = 'QUESTIONABLE'
        else:
            compatibility_analysis['compatibility_rating'] = 'POOR'
        
        return compatibility_analysis
    
    def _calculate_overall_risk_score(
        self, 
        address_risk: Dict, 
        satellite_risk: Dict, 
        compatibility_risk: Dict
    ) -> float:
        """Calculates weighted overall risk score"""
        
        # Weighted components (total = 1.0)
        address_weight = 0.3
        satellite_weight = 0.4
        compatibility_weight = 0.3
        
        # Extract individual scores
        address_score = address_risk.get('risk_score', 0.5)
        satellite_score = satellite_risk.get('risk_score', 0.5)
        compatibility_score = compatibility_risk.get('risk_score', 0.5)
        
        # Calculate weighted average
        overall_score = (
            address_score * address_weight + 
            satellite_score * satellite_weight + 
            compatibility_score * compatibility_weight
        )
        
        # Apply confidence adjustments
        satellite_data_confidence = satellite_risk.get('confidence_score', 0.5)
        if satellite_data_confidence < 0.3:
            overall_score += 0.1  # Increase risk if analysis confidence is low
        
        return min(1.0, overall_score)
    
    def _generate_final_assessment(self, overall_score: float, analysis_result: Dict) -> Dict:
        """Generates final risk assessment and recommendations"""
        
        # Collect all risk and positive factors
        all_risk_factors = []
        all_positive_factors = []
        
        for assessment in analysis_result['detailed_assessment'].values():
            all_risk_factors.extend(assessment.get('risk_factors', []))
            all_positive_factors.extend(assessment.get('positive_factors', []))
        
        # Determine risk level
        if overall_score >= self.high_risk_threshold:
            risk_level = 'HIGH'
            recommendation = 'BLOCK'
        elif overall_score >= self.medium_risk_threshold:
            risk_level = 'MEDIUM'
            recommendation = 'MANUAL_REVIEW'
        else:
            risk_level = 'LOW'
            recommendation = 'AUTO_APPROVE'
        
        # Generate detailed recommendation text
        recommendation_text = self._generate_recommendation_text(
            risk_level, overall_score, all_risk_factors, all_positive_factors
        )
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(analysis_result)
        
        return {
            'overall_risk_score': overall_score,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'recommendation_text': recommendation_text,
            'risk_factors': all_risk_factors[:5],  # Top 5 risk factors
            'positive_factors': all_positive_factors[:5],  # Top 5 positive factors
            'confidence_level': confidence_level
        }
    
    def _generate_recommendation_text(
        self, 
        risk_level: str, 
        score: float, 
        risk_factors: List[str], 
        positive_factors: List[str]
    ) -> str:
        """Generates human-readable recommendation text"""
        
        if risk_level == 'HIGH':
            text = f"🚨 HIGH RISK (Score: {score:.2f}): "
            if "residential" in str(risk_factors).lower():
                text += "ALERT: Registered address is residential. "
            if "no buildings" in str(risk_factors).lower():
                text += "No commercial infrastructure visible. "
            text += "High probability of shell company. Block registration and forward for manual review."
            
        elif risk_level == 'MEDIUM':
            text = f"⚠️ MEDIUM RISK (Score: {score:.2f}): "
            text += "The company may be legitimate, but shows some risk indicators. "
            if positive_factors:
                text += f"Positive points: {', '.join(positive_factors[:2])}. "
            text += "Additional document verification recommended."
            
        else:  # LOW risk
            text = f"✅ LOW RISK (Score: {score:.2f}): "
            text += "Address validated. "
            if positive_factors:
                text += f"Adequate infrastructure identified: {', '.join(positive_factors[:2])}. "
            text += "Automatic approval recommended."
        
        return text
    
    def _calculate_confidence_level(self, analysis_result: Dict) -> float:
        """Calculates overall confidence in the analysis"""
        confidence_factors = []
        
        # Address validation confidence
        if analysis_result['address_validation'].get('is_valid'):
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.3)
        
        # Satellite analysis confidence
        satellite_confidence = analysis_result['satellite_analysis'].get('confidence_score', 0.5)
        confidence_factors.append(satellite_confidence)
        
        # Data completeness
        if analysis_result['satellite_analysis'].get('analysis_completed'):
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.4)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def _get_expected_locations(self, business_type: str) -> List[str]:
        """Returns expected location types for a business type"""
        location_mapping = {
            'logistics': ['industrial', 'commercial'],
            'manufacturing': ['industrial'],
            'technology': ['commercial', 'office'],
            'consulting': ['commercial', 'office'],
            'retail': ['commercial'],
            'restaurant': ['commercial']
        }
        
        return location_mapping.get(business_type.lower(), ['commercial'])
