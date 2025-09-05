"""
Address Validation Module
Validates and geocodes Brazilian business addresses using OpenStreetMap
"""

import requests
import time
from typing import Dict, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

logger = logging.getLogger(__name__)


class AddressValidator:
    """Validates and enriches address information using OpenStreetMap"""
    
    def __init__(self, user_agent: str = "KYC-Geointelligent/1.0"):
        self.geocoder = Nominatim(user_agent=user_agent)
        self.overpass_url = "https://overpass-api.de/api/interpreter"
    
    def validate_address(self, address: str, cnpj: str = None) -> Dict:
        """
        Validates a Brazilian business address and returns enriched data
        
        Args:
            address: Business address string
            cnpj: Optional CNPJ for additional validation
            
        Returns:
            Dict containing validation results and geocoded information
        """
        result = {
            'address_input': address,
            'cnpj': cnpj,
            'is_valid': False,
            'coordinates': None,
            'formatted_address': None,
            'location_type': None,
            'neighborhood_context': None,
            'error': None
        }
        
        try:
            # Geocode the address
            location = self._geocode_address(address)
            if not location:
                result['error'] = "Address not found in OpenStreetMap"
                return result
            
            result['coordinates'] = (location.latitude, location.longitude)
            result['formatted_address'] = location.address
            result['is_valid'] = True
            
            # Analyze location context
            context = self._analyze_location_context(
                location.latitude, 
                location.longitude
            )
            
            result.update(context)
            
            logger.info(f"Successfully validated address: {address}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating address {address}: {str(e)}")
            result['error'] = f"Validation error: {str(e)}"
            return result
    
    def _geocode_address(self, address: str) -> Optional[object]:
        """Geocodes an address using Nominatim"""
        try:
            # Add Brazil context to improve accuracy
            search_query = f"{address}, Brazil"
            location = self.geocoder.geocode(
                search_query, 
                timeout=10,
                language='pt-BR',
                country_codes='br'
            )
            return location
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding service error: {str(e)}")
            return None
    
    def _analyze_location_context(self, lat: float, lon: float) -> Dict:
        """
        Analyzes the context around a location using Overpass API
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with location context information
        """
        context = {
            'location_type': 'unknown',
            'neighborhood_context': 'unknown',
            'nearby_amenities': [],
            'land_use': 'unknown'
        }
        
        try:
            # Query for nearby amenities and land use
            overpass_query = self._build_overpass_query(lat, lon)
            response = requests.post(
                self.overpass_url,
                data={'data': overpass_query},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                context = self._parse_overpass_response(data)
            
        except Exception as e:
            logger.warning(f"Error analyzing location context: {str(e)}")
        
        return context
    
    def _build_overpass_query(self, lat: float, lon: float, radius: int = 500) -> str:
        """Builds Overpass API query for location analysis"""
        query = f"""
        [out:json][timeout:15];
        (
          way(around:{radius},{lat},{lon})["landuse"];
          way(around:{radius},{lat},{lon})["amenity"];
          way(around:{radius},{lat},{lon})["building"];
          way(around:{radius},{lat},{lon})["industrial"];
          relation(around:{radius},{lat},{lon})["landuse"];
        );
        out geom;
        """
        return query
    
    def _parse_overpass_response(self, data: Dict) -> Dict:
        """Parses Overpass API response to extract context information"""
        context = {
            'location_type': 'mixed',
            'neighborhood_context': 'urban',
            'nearby_amenities': [],
            'land_use': 'mixed'
        }
        
        land_uses = []
        amenities = []
        building_types = []
        
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            
            # Analyze land use
            if 'landuse' in tags:
                land_uses.append(tags['landuse'])
            
            # Analyze amenities
            if 'amenity' in tags:
                amenities.append(tags['amenity'])
            
            # Analyze building types
            if 'building' in tags:
                building_types.append(tags['building'])
        
        # Determine dominant characteristics
        context['land_use'] = self._get_dominant_characteristic(land_uses)
        context['nearby_amenities'] = list(set(amenities))
        context['location_type'] = self._classify_location_type(
            land_uses, building_types, amenities
        )
        
        return context
    
    def _get_dominant_characteristic(self, characteristics: list) -> str:
        """Gets the most common characteristic from a list"""
        if not characteristics:
            return 'unknown'
        
        # Count occurrences
        char_counts = {}
        for char in characteristics:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Return most common
        return max(char_counts.items(), key=lambda x: x[1])[0]
    
    def _classify_location_type(self, land_uses: list, buildings: list, amenities: list) -> str:
        """Classifies the location type based on surrounding context"""
        
        # Industrial indicators
        industrial_indicators = ['industrial', 'warehouse', 'factory', 'logistics']
        if any(indicator in land_uses + buildings + amenities for indicator in industrial_indicators):
            return 'industrial'
        
        # Commercial indicators
        commercial_indicators = ['commercial', 'retail', 'office', 'shop']
        if any(indicator in land_uses + buildings + amenities for indicator in commercial_indicators):
            return 'commercial'
        
        # Residential indicators
        residential_indicators = ['residential', 'house', 'apartment']
        if any(indicator in land_uses + buildings + amenities for indicator in residential_indicators):
            return 'residential'
        
        return 'mixed'
