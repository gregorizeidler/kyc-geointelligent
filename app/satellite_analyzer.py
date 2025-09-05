"""
Satellite Image Analysis Module
Downloads and analyzes satellite imagery to assess business location authenticity
"""

import requests
import cv2
import numpy as np
from PIL import Image
import base64
import io
import logging
from typing import Dict, Optional, Tuple
import openai
from config import Config

logger = logging.getLogger(__name__)


class SatelliteAnalyzer:
    """Analyzes satellite imagery to assess business location characteristics"""
    
    def __init__(self):
        """Initialize the satellite analyzer with API clients"""
        self.google_api_key = Config.GOOGLE_MAPS_API_KEY
        self.mapbox_token = Config.MAPBOX_ACCESS_TOKEN
        openai.api_key = Config.OPENAI_API_KEY
        
        # Image analysis parameters
        self.image_size = Config.MAX_IMAGE_SIZE
        self.zoom_level = 18  # High detail for business analysis
    
    def analyze_location(self, lat: float, lon: float, business_type: str) -> Dict:
        """
        Complete analysis of a business location using satellite imagery
        
        Args:
            lat: Latitude
            lon: Longitude
            business_type: Type of business (e.g., "Logistics", "Technology")
            
        Returns:
            Dict containing analysis results and risk assessment
        """
        result = {
            'coordinates': (lat, lon),
            'business_type': business_type,
            'image_downloaded': False,
            'analysis_completed': False,
            'visual_features': {},
            'infrastructure_assessment': {},
            'activity_indicators': {},
            'risk_indicators': [],
            'confidence_score': 0.0,
            'error': None
        }
        
        try:
            # Download satellite image
            image_data = self._download_satellite_image(lat, lon)
            if not image_data:
                result['error'] = "Failed to download satellite image"
                return result
            
            result['image_downloaded'] = True
            
            # Perform computer vision analysis
            cv_analysis = self._computer_vision_analysis(image_data)
            result['visual_features'] = cv_analysis
            
            # Perform AI-powered contextual analysis
            ai_analysis = self._ai_contextual_analysis(image_data, business_type)
            result.update(ai_analysis)
            
            result['analysis_completed'] = True
            logger.info(f"Successfully analyzed location: {lat}, {lon}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing location {lat}, {lon}: {str(e)}")
            result['error'] = f"Analysis error: {str(e)}"
            return result
    
    def _download_satellite_image(self, lat: float, lon: float) -> Optional[bytes]:
        """
        Downloads satellite image from available providers
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Image data as bytes or None if failed
        """
        # Try Google Maps Static API first
        if self.google_api_key:
            image_data = self._download_from_google(lat, lon)
            if image_data:
                return image_data
        
        # Fallback to Mapbox
        if self.mapbox_token:
            image_data = self._download_from_mapbox(lat, lon)
            if image_data:
                return image_data
        
        logger.warning("No satellite imagery provider available")
        return None
    
    def _download_from_google(self, lat: float, lon: float) -> Optional[bytes]:
        """Downloads satellite image from Google Maps Static API"""
        try:
            url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                'center': f"{lat},{lon}",
                'zoom': self.zoom_level,
                'size': f"{self.image_size}x{self.image_size}",
                'maptype': 'satellite',
                'key': self.google_api_key,
                'format': 'png'
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                return response.content
            
        except Exception as e:
            logger.warning(f"Google Maps API error: {str(e)}")
        
        return None
    
    def _download_from_mapbox(self, lat: float, lon: float) -> Optional[bytes]:
        """Downloads satellite image from Mapbox Static API"""
        try:
            url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},{self.zoom_level}/{self.image_size}x{self.image_size}@2x"
            params = {'access_token': self.mapbox_token}
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.content
                
        except Exception as e:
            logger.warning(f"Mapbox API error: {str(e)}")
        
        return None
    
    def _computer_vision_analysis(self, image_data: bytes) -> Dict:
        """
        Performs computer vision analysis on satellite image
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dict with computer vision analysis results
        """
        analysis = {
            'building_detection': {},
            'vehicle_detection': {},
            'infrastructure_features': {},
            'area_characteristics': {}
        }
        
        try:
            # Convert bytes to OpenCV image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return analysis
            
            # Building detection using edge detection and contour analysis
            buildings = self._detect_buildings(image)
            analysis['building_detection'] = buildings
            
            # Vehicle detection (bright spots that could be vehicles)
            vehicles = self._detect_vehicles(image)
            analysis['vehicle_detection'] = vehicles
            
            # Infrastructure analysis
            infrastructure = self._analyze_infrastructure(image)
            analysis['infrastructure_features'] = infrastructure
            
            # Overall area characteristics
            characteristics = self._analyze_area_characteristics(image)
            analysis['area_characteristics'] = characteristics
            
        except Exception as e:
            logger.error(f"Computer vision analysis error: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _detect_buildings(self, image: np.ndarray) -> Dict:
        """Detects building structures in satellite image"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection for building outlines
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size and shape
        buildings = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Minimum building size
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) >= 4:  # Rectangular-ish shapes
                    buildings.append({
                        'area': area,
                        'vertices': len(approx),
                        'perimeter': cv2.arcLength(contour, True)
                    })
        
        return {
            'building_count': len(buildings),
            'total_building_area': sum(b['area'] for b in buildings),
            'largest_building_area': max([b['area'] for b in buildings], default=0),
            'buildings': buildings[:10]  # Top 10 largest
        }
    
    def _detect_vehicles(self, image: np.ndarray) -> Dict:
        """Detects potential vehicles (bright rectangular objects)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Create a mask for bright objects
        _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Find contours of bright objects
        contours, _ = cv2.findContours(bright_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        vehicles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            # Vehicle-sized objects
            if 50 < area < 500:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                # Rectangular objects with reasonable aspect ratio
                if 0.5 < aspect_ratio < 3.0:
                    vehicles.append({
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'position': (x, y)
                    })
        
        return {
            'vehicle_count': len(vehicles),
            'vehicles': vehicles
        }
    
    def _analyze_infrastructure(self, image: np.ndarray) -> Dict:
        """Analyzes infrastructure features like roads, parking lots"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Road detection (looking for linear features)
        kernel = np.ones((3,3), np.uint8)
        processed = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        
        # Edge detection for linear features
        edges = cv2.Canny(processed, 50, 150, apertureSize=3)
        
        # Hough line detection for roads
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
        
        return {
            'detected_lines': len(lines) if lines is not None else 0,
            'infrastructure_density': np.sum(edges > 0) / edges.size
        }
    
    def _analyze_area_characteristics(self, image: np.ndarray) -> Dict:
        """Analyzes general characteristics of the area"""
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Vegetation detection (green areas)
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        vegetation_mask = cv2.inRange(hsv, lower_green, upper_green)
        vegetation_percentage = np.sum(vegetation_mask > 0) / vegetation_mask.size * 100
        
        # Water detection (blue areas)
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        water_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        water_percentage = np.sum(water_mask > 0) / water_mask.size * 100
        
        # Overall brightness (activity indicator)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        average_brightness = np.mean(gray)
        
        return {
            'vegetation_percentage': vegetation_percentage,
            'water_percentage': water_percentage,
            'average_brightness': average_brightness,
            'developed_area_percentage': max(0, 100 - vegetation_percentage - water_percentage)
        }
    
    def _ai_contextual_analysis(self, image_data: bytes, business_type: str) -> Dict:
        """
        Uses GPT-4 Vision to perform contextual analysis of the satellite image
        
        Args:
            image_data: Raw image bytes
            business_type: Type of business being analyzed
            
        Returns:
            Dict with AI analysis results
        """
        try:
            # Convert image to base64 for OpenAI API
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            prompt = self._build_analysis_prompt(business_type)
            
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content
            return self._parse_ai_response(analysis_text)
            
        except Exception as e:
            logger.error(f"AI contextual analysis error: {str(e)}")
            return {
                'infrastructure_assessment': {'error': str(e)},
                'activity_indicators': {},
                'risk_indicators': [],
                'confidence_score': 0.0
            }
    
    def _build_analysis_prompt(self, business_type: str) -> str:
        """Builds the analysis prompt for GPT-4 Vision"""
        return f"""
        Analyze this satellite image for a business location assessment. The declared business type is: "{business_type}".

        Please provide a detailed analysis covering:

        1. INFRASTRUCTURE ASSESSMENT:
        - What type of buildings/structures are visible?
        - Are there loading docks, warehouses, office buildings?
        - What is the scale and condition of the infrastructure?
        
        2. ACTIVITY INDICATORS:
        - Are there vehicles present?
        - Signs of active business operations?
        - Parking facilities and their usage?
        
        3. LOCATION COMPATIBILITY:
        - Does this location match the declared business type?
        - Is the infrastructure appropriate for the stated activity?
        
        4. RISK INDICATORS:
        - Any signs this might be a facade/shell company?
        - Empty lots, residential areas, or inappropriate locations?
        - Inconsistencies with the business type?
        
        5. CONFIDENCE ASSESSMENT:
        - How confident are you in this analysis (0.0 to 1.0)?
        
        Please format your response as a structured analysis with clear sections.
        """
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parses the AI response into structured data"""
        # This is a simplified parser - in production, you might want more sophisticated parsing
        lines = response_text.lower().split('\n')
        
        risk_keywords = ['empty', 'residential', 'inappropriate', 'facade', 'shell', 'suspicious']
        positive_keywords = ['warehouse', 'office', 'industrial', 'commercial', 'loading', 'vehicles']
        
        risk_indicators = [line.strip() for line in lines if any(keyword in line for keyword in risk_keywords)]
        positive_indicators = [line.strip() for line in lines if any(keyword in line for keyword in positive_keywords)]
        
        # Simple confidence estimation based on analysis content
        confidence = min(1.0, len(positive_indicators) * 0.2 + 0.5)
        if risk_indicators:
            confidence *= 0.7  # Reduce confidence if risk indicators present
        
        return {
            'infrastructure_assessment': {
                'positive_indicators': positive_indicators,
                'infrastructure_quality': 'good' if len(positive_indicators) > 2 else 'limited'
            },
            'activity_indicators': {
                'signs_of_activity': len(positive_indicators) > 1,
                'vehicle_presence': any('vehicle' in indicator for indicator in positive_indicators)
            },
            'risk_indicators': risk_indicators,
            'confidence_score': confidence,
            'full_analysis': response_text
        }
