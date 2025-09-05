"""
Google Earth Engine Integration Module
Advanced satellite data analysis using Sentinel-2 and Landsat-8 data
"""

import ee
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import folium
import rasterio
from rasterio.transform import from_bounds
import requests
from config import Config

logger = logging.getLogger(__name__)


class EarthEngineAnalyzer:
    """Advanced satellite analysis using Google Earth Engine"""
    
    def __init__(self):
        """Initialize Earth Engine with authentication"""
        self.initialized = False
        self.demo_mode = Config.DEMO_MODE
        
        if not self.demo_mode:
            try:
                # Initialize Earth Engine
                ee.Initialize()
                self.initialized = True
                logger.info("Google Earth Engine initialized successfully")
            except Exception as e:
                logger.warning(f"Earth Engine initialization failed: {str(e)}")
                logger.info("🚀 Running in DEMO mode - using mock satellite data")
                self.demo_mode = True
        else:
            logger.info("🚀 Demo mode enabled - using simulated satellite data")
    
    def get_location_analysis(
        self, 
        lat: float, 
        lon: float, 
        buffer_size: int = 500,
        months_back: int = 6
    ) -> Dict:
        """
        Comprehensive location analysis using multiple satellite sources
        
        Args:
            lat: Latitude
            lon: Longitude
            buffer_size: Analysis buffer in meters
            months_back: How many months of historical data to analyze
            
        Returns:
            Complete satellite analysis with multiple data sources
        """
        if not self.initialized or self.demo_mode:
            logger.info("Using demo satellite analysis with realistic simulated data")
            return self._generate_demo_analysis(lat, lon, buffer_size, months_back)
        
        try:
            # Define area of interest
            point = ee.Geometry.Point([lon, lat])
            aoi = point.buffer(buffer_size)
            
            # Get date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months_back)
            
            # Analyze multiple data sources
            sentinel_analysis = self._analyze_sentinel2(aoi, start_date, end_date)
            landsat_analysis = self._analyze_landsat8(aoi, start_date, end_date)
            infrastructure_analysis = self._analyze_infrastructure(aoi)
            change_detection = self._detect_changes(aoi, start_date, end_date)
            
            # Combine results
            result = {
                'location': {'lat': lat, 'lon': lon},
                'analysis_area_meters': buffer_size,
                'analysis_period_months': months_back,
                'data_sources': {
                    'sentinel2': sentinel_analysis,
                    'landsat8': landsat_analysis
                },
                'infrastructure_assessment': infrastructure_analysis,
                'temporal_analysis': change_detection,
                'composite_score': self._calculate_composite_score(
                    sentinel_analysis, landsat_analysis, infrastructure_analysis
                ),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Earth Engine analysis completed for {lat}, {lon}")
            return result
            
        except Exception as e:
            logger.error(f"Earth Engine analysis failed: {str(e)}")
            return self._fallback_analysis(lat, lon, buffer_size)
    
    def _analyze_sentinel2(self, aoi, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze Sentinel-2 imagery for the area of interest"""
        try:
            # Get Sentinel-2 collection
            sentinel = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(aoi)
                       .filterDate(start_date.strftime('%Y-%m-%d'), 
                                 end_date.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))
            
            if sentinel.size().getInfo() == 0:
                return {'error': 'No Sentinel-2 images available for this period'}
            
            # Get median composite
            median = sentinel.median().clip(aoi)
            
            # Calculate vegetation indices
            ndvi = median.normalizedDifference(['B8', 'B4']).rename('NDVI')
            ndbi = median.normalizedDifference(['B11', 'B8']).rename('NDBI')  # Built-up index
            mndwi = median.normalizedDifference(['B3', 'B11']).rename('MNDWI')  # Water index
            
            # Calculate statistics
            ndvi_stats = self._get_image_statistics(ndvi, aoi)
            ndbi_stats = self._get_image_statistics(ndbi, aoi)
            mndwi_stats = self._get_image_statistics(mndwi, aoi)
            
            # Analyze land cover
            land_cover = self._classify_land_cover(median, aoi)
            
            return {
                'source': 'Sentinel-2',
                'resolution_meters': 10,
                'images_analyzed': sentinel.size().getInfo(),
                'vegetation_index': {
                    'ndvi_mean': ndvi_stats['mean'],
                    'ndvi_std': ndvi_stats['stdDev'],
                    'vegetation_percentage': max(0, (ndvi_stats['mean'] + 1) * 50)  # Normalize to percentage
                },
                'built_up_index': {
                    'ndbi_mean': ndbi_stats['mean'],
                    'ndbi_std': ndbi_stats['stdDev'],
                    'built_up_percentage': max(0, (ndbi_stats['mean'] + 1) * 50)
                },
                'water_index': {
                    'mndwi_mean': mndwi_stats['mean'],
                    'water_percentage': max(0, mndwi_stats['mean'] * 100) if mndwi_stats['mean'] > 0 else 0
                },
                'land_cover_classification': land_cover
            }
            
        except Exception as e:
            logger.error(f"Sentinel-2 analysis failed: {str(e)}")
            return {'error': f'Sentinel-2 analysis failed: {str(e)}'}
    
    def _analyze_landsat8(self, aoi, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze Landsat-8 imagery for the area of interest"""
        try:
            # Get Landsat-8 collection
            landsat = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                      .filterBounds(aoi)
                      .filterDate(start_date.strftime('%Y-%m-%d'), 
                                end_date.strftime('%Y-%m-%d'))
                      .filter(ee.Filter.lt('CLOUD_COVER', 20)))
            
            if landsat.size().getInfo() == 0:
                return {'error': 'No Landsat-8 images available for this period'}
            
            # Get median composite and scale
            median = (landsat.median()
                     .multiply(0.0000275)
                     .add(-0.2)
                     .clip(aoi))
            
            # Calculate thermal analysis
            thermal = median.select('ST_B10').subtract(273.15)  # Convert to Celsius
            thermal_stats = self._get_image_statistics(thermal, aoi)
            
            # Urban heat island analysis
            temperature_threshold = thermal_stats['mean'] + thermal_stats['stdDev']
            hot_spots = thermal.gt(temperature_threshold)
            hot_spot_percentage = self._calculate_percentage(hot_spots, aoi)
            
            return {
                'source': 'Landsat-8',
                'resolution_meters': 30,
                'images_analyzed': landsat.size().getInfo(),
                'thermal_analysis': {
                    'mean_temperature_celsius': thermal_stats['mean'],
                    'temperature_std': thermal_stats['stdDev'],
                    'hot_spot_percentage': hot_spot_percentage,
                    'urban_heat_indicator': 'high' if hot_spot_percentage > 30 else 'moderate' if hot_spot_percentage > 10 else 'low'
                },
                'surface_characteristics': {
                    'temperature_variance': thermal_stats['stdDev'],
                    'heat_distribution': 'uniform' if thermal_stats['stdDev'] < 2 else 'varied'
                }
            }
            
        except Exception as e:
            logger.error(f"Landsat-8 analysis failed: {str(e)}")
            return {'error': f'Landsat-8 analysis failed: {str(e)}'}
    
    def _analyze_infrastructure(self, aoi) -> Dict:
        """Analyze infrastructure and development patterns"""
        try:
            # Use Global Human Settlement Layer
            ghsl = ee.ImageCollection('JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1').mosaic().clip(aoi)
            built_density = ghsl.select('built')
            
            # Calculate built-up statistics
            built_stats = self._get_image_statistics(built_density, aoi)
            total_pixels = ee.Image.constant(1).reduceRegion(
                reducer=ee.Reducer.count(),
                geometry=aoi,
                scale=30,
                maxPixels=1e9
            ).getInfo()['constant']
            
            # Road network analysis using OSM data
            roads = ee.FeatureCollection('projects/sat-io/open-datasets/OSM/OSM_roads')
            roads_in_area = roads.filterBounds(aoi)
            road_density = roads_in_area.size().divide(aoi.area()).multiply(1000000)  # roads per km²
            
            return {
                'built_up_density': {
                    'mean_density': built_stats['mean'],
                    'development_level': 'high' if built_stats['mean'] > 50 else 'medium' if built_stats['mean'] > 20 else 'low'
                },
                'road_network': {
                    'road_count': roads_in_area.size().getInfo(),
                    'road_density_per_km2': road_density.getInfo() if road_density.getInfo() else 0,
                    'connectivity': 'high' if road_density.getInfo() > 5 else 'moderate' if road_density.getInfo() > 2 else 'low'
                },
                'infrastructure_score': min(100, (built_stats['mean'] + road_density.getInfo()) / 2)
            }
            
        except Exception as e:
            logger.warning(f"Infrastructure analysis failed: {str(e)}")
            return {
                'built_up_density': {'mean_density': 0, 'development_level': 'unknown'},
                'road_network': {'road_count': 0, 'road_density_per_km2': 0, 'connectivity': 'unknown'},
                'infrastructure_score': 0,
                'error': str(e)
            }
    
    def _detect_changes(self, aoi, start_date: datetime, end_date: datetime) -> Dict:
        """Detect temporal changes in the area"""
        try:
            # Split time period in half
            mid_date = start_date + (end_date - start_date) / 2
            
            # Get before and after images
            before = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                     .filterBounds(aoi)
                     .filterDate(start_date.strftime('%Y-%m-%d'), 
                               mid_date.strftime('%Y-%m-%d'))
                     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                     .median().clip(aoi))
            
            after = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                    .filterBounds(aoi)
                    .filterDate(mid_date.strftime('%Y-%m-%d'), 
                              end_date.strftime('%Y-%m-%d'))
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                    .median().clip(aoi))
            
            if not before or not after:
                return {'error': 'Insufficient imagery for change detection'}
            
            # Calculate NDVI for both periods
            ndvi_before = before.normalizedDifference(['B8', 'B4'])
            ndvi_after = after.normalizedDifference(['B8', 'B4'])
            
            # Calculate change
            ndvi_change = ndvi_after.subtract(ndvi_before)
            change_stats = self._get_image_statistics(ndvi_change, aoi)
            
            # Classify changes
            significant_change = abs(change_stats['mean']) > 0.1
            change_type = 'development' if change_stats['mean'] < -0.1 else 'greening' if change_stats['mean'] > 0.1 else 'stable'
            
            return {
                'analysis_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'change_detected': significant_change,
                'change_magnitude': abs(change_stats['mean']),
                'change_type': change_type,
                'stability_score': max(0, 1 - abs(change_stats['mean'])) * 100,
                'change_description': self._describe_change(change_type, change_stats['mean'])
            }
            
        except Exception as e:
            logger.warning(f"Change detection failed: {str(e)}")
            return {'error': f'Change detection failed: {str(e)}'}
    
    def _get_image_statistics(self, image, aoi) -> Dict:
        """Get statistics for an image within area of interest"""
        try:
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    reducer2=ee.Reducer.stdDev(),
                    sharedInputs=True
                ),
                geometry=aoi,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            # Extract values from the nested dictionary
            keys = list(stats.keys())
            if len(keys) >= 2:
                return {
                    'mean': stats[keys[0]] or 0,
                    'stdDev': stats[keys[1]] or 0
                }
            else:
                return {'mean': 0, 'stdDev': 0}
        except:
            return {'mean': 0, 'stdDev': 0}
    
    def _classify_land_cover(self, image, aoi) -> Dict:
        """Simple land cover classification"""
        try:
            # Calculate indices
            ndvi = image.normalizedDifference(['B8', 'B4'])
            ndbi = image.normalizedDifference(['B11', 'B8'])
            
            # Simple classification rules
            vegetation = ndvi.gt(0.4)
            built_up = ndbi.gt(0.1)
            bare_soil = ndvi.lt(0.2).And(ndbi.lt(0.1))
            
            # Calculate percentages
            veg_pct = self._calculate_percentage(vegetation, aoi)
            built_pct = self._calculate_percentage(built_up, aoi)
            bare_pct = self._calculate_percentage(bare_soil, aoi)
            
            return {
                'vegetation_percentage': veg_pct,
                'built_up_percentage': built_pct,
                'bare_soil_percentage': bare_pct,
                'dominant_class': max([
                    ('vegetation', veg_pct),
                    ('built_up', built_pct),
                    ('bare_soil', bare_pct)
                ], key=lambda x: x[1])[0]
            }
        except:
            return {
                'vegetation_percentage': 0,
                'built_up_percentage': 0,
                'bare_soil_percentage': 0,
                'dominant_class': 'unknown'
            }
    
    def _calculate_percentage(self, binary_image, aoi) -> float:
        """Calculate percentage of true pixels in binary image"""
        try:
            pixel_area = binary_image.multiply(ee.Image.pixelArea())
            total_true_area = pixel_area.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi,
                scale=30,
                maxPixels=1e9
            )
            
            total_area = aoi.area()
            
            # Extract the actual values
            true_area_value = list(total_true_area.getInfo().values())[0] or 0
            total_area_value = total_area.getInfo()
            
            return (true_area_value / total_area_value) * 100 if total_area_value > 0 else 0
        except:
            return 0
    
    def _calculate_composite_score(
        self, 
        sentinel_data: Dict, 
        landsat_data: Dict, 
        infrastructure_data: Dict
    ) -> Dict:
        """Calculate composite development and activity score"""
        try:
            # Extract key metrics
            built_up_pct = sentinel_data.get('built_up_index', {}).get('built_up_percentage', 0)
            vegetation_pct = sentinel_data.get('vegetation_index', {}).get('vegetation_percentage', 0)
            infrastructure_score = infrastructure_data.get('infrastructure_score', 0)
            
            # Calculate composite scores
            development_score = (built_up_pct + infrastructure_score) / 2
            activity_score = min(100, development_score + (100 - vegetation_pct))
            
            # Classify development level
            if development_score > 70:
                development_level = 'high'
            elif development_score > 40:
                development_level = 'medium'
            else:
                development_level = 'low'
            
            return {
                'development_score': development_score,
                'activity_score': activity_score,
                'development_level': development_level,
                'suitability_for_business': {
                    'industrial': development_score if development_score > 30 else 0,
                    'commercial': min(100, development_score * 1.2),
                    'office': min(100, (development_score + infrastructure_score) / 2)
                }
            }
        except:
            return {
                'development_score': 0,
                'activity_score': 0,
                'development_level': 'unknown',
                'suitability_for_business': {'industrial': 0, 'commercial': 0, 'office': 0}
            }
    
    def _describe_change(self, change_type: str, magnitude: float) -> str:
        """Provide human-readable description of detected changes"""
        if change_type == 'development':
            if magnitude < -0.3:
                return "Significant development/construction activity detected"
            else:
                return "Moderate development activity detected"
        elif change_type == 'greening':
            return "Increase in vegetation cover detected"
        else:
            return "Area appears stable with no significant changes"
    
    def _generate_demo_analysis(self, lat: float, lon: float, buffer_size: int, months_back: int) -> Dict:
        """Generate realistic demo analysis data"""
        import random
        import numpy as np
        
        # Generate realistic values based on location (rough heuristics)
        # São Paulo area tends to be more developed
        is_urban = abs(lat + 23.5505) < 2 and abs(lon + 46.6333) < 2
        
        # Base development score
        if is_urban:
            dev_base = random.uniform(60, 85)
            built_up_pct = random.uniform(45, 75)
            vegetation_pct = random.uniform(10, 35)
        else:
            dev_base = random.uniform(20, 55)
            built_up_pct = random.uniform(15, 40)
            vegetation_pct = random.uniform(40, 80)
        
        # Generate realistic satellite data
        result = {
            'location': {'lat': lat, 'lon': lon},
            'analysis_area_meters': buffer_size,
            'analysis_period_months': months_back,
            'data_sources': {
                'sentinel2': {
                    'source': 'Sentinel-2 (Demo)',
                    'resolution_meters': 10,
                    'images_analyzed': random.randint(5, 15),
                    'vegetation_index': {
                        'ndvi_mean': random.uniform(0.2, 0.8),
                        'ndvi_std': random.uniform(0.1, 0.3),
                        'vegetation_percentage': vegetation_pct
                    },
                    'built_up_index': {
                        'ndbi_mean': random.uniform(-0.2, 0.4),
                        'ndbi_std': random.uniform(0.1, 0.25),
                        'built_up_percentage': built_up_pct
                    },
                    'water_index': {
                        'mndwi_mean': random.uniform(-0.1, 0.2),
                        'water_percentage': random.uniform(0, 5)
                    },
                    'land_cover_classification': {
                        'vegetation_percentage': vegetation_pct,
                        'built_up_percentage': built_up_pct,
                        'bare_soil_percentage': max(0, 100 - vegetation_pct - built_up_pct),
                        'dominant_class': 'built_up' if built_up_pct > vegetation_pct else 'vegetation'
                    }
                },
                'landsat8': {
                    'source': 'Landsat-8 (Demo)',
                    'resolution_meters': 30,
                    'images_analyzed': random.randint(3, 8),
                    'thermal_analysis': {
                        'mean_temperature_celsius': random.uniform(18, 35),
                        'temperature_std': random.uniform(2, 6),
                        'hot_spot_percentage': random.uniform(5, 25),
                        'urban_heat_indicator': 'high' if is_urban else 'moderate'
                    }
                }
            },
            'infrastructure_assessment': {
                'built_up_density': {
                    'mean_density': dev_base,
                    'development_level': 'high' if dev_base > 70 else 'medium' if dev_base > 40 else 'low'
                },
                'road_network': {
                    'road_count': random.randint(5, 25),
                    'road_density_per_km2': random.uniform(2, 15),
                    'connectivity': 'high' if is_urban else 'moderate'
                },
                'infrastructure_score': min(100, dev_base + random.uniform(-10, 10))
            },
            'temporal_analysis': {
                'analysis_period': f"{datetime.now() - timedelta(days=30*months_back)} to {datetime.now()}",
                'change_detected': random.choice([True, False]),
                'change_magnitude': random.uniform(0.02, 0.15),
                'change_type': random.choice(['stable', 'development', 'greening']),
                'stability_score': random.uniform(70, 95),
                'change_description': 'Simulated temporal analysis for demonstration'
            },
            'composite_score': {
                'development_score': dev_base,
                'activity_score': min(100, dev_base + random.uniform(-5, 15)),
                'development_level': 'high' if dev_base > 70 else 'medium' if dev_base > 40 else 'low',
                'suitability_for_business': {
                    'industrial': max(0, dev_base - 20),
                    'commercial': min(100, dev_base * 1.1),
                    'office': min(100, dev_base + 10)
                }
            },
            'analysis_timestamp': datetime.now().isoformat(),
            'demo_mode': True,
            'note': '🚀 This is simulated data for demonstration purposes'
        }
        
        return result
    
    def _fallback_analysis(self, lat: float, lon: float, buffer_size: int) -> Dict:
        """Fallback analysis when Earth Engine is not available"""
        return self._generate_demo_analysis(lat, lon, buffer_size, 6)
    
    def create_analysis_map(self, analysis_result: Dict) -> folium.Map:
        """Create an interactive map showing the analysis results"""
        lat = analysis_result['location']['lat']
        lon = analysis_result['location']['lon']
        
        # Create base map
        m = folium.Map(
            location=[lat, lon],
            zoom_start=16,
            tiles='Satellite'
        )
        
        # Add analysis area
        buffer_size = analysis_result.get('analysis_area_meters', 500)
        circle = folium.Circle(
            location=[lat, lon],
            radius=buffer_size,
            popup=f"Analysis Area ({buffer_size}m radius)",
            color='red',
            fill=True,
            fillOpacity=0.2
        )
        circle.add_to(m)
        
        # Add marker with analysis results
        composite = analysis_result.get('composite_score', {})
        development_level = composite.get('development_level', 'unknown')
        development_score = composite.get('development_score', 0)
        
        popup_html = f"""
        <div style="width: 300px;">
            <h4>Satellite Analysis Results</h4>
            <p><strong>Development Level:</strong> {development_level.title()}</p>
            <p><strong>Development Score:</strong> {development_score:.1f}/100</p>
            <p><strong>Activity Score:</strong> {composite.get('activity_score', 0):.1f}/100</p>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip="Click for detailed analysis",
            icon=folium.Icon(color='green' if development_level == 'high' else 'orange' if development_level == 'medium' else 'red')
        ).add_to(m)
        
        return m
