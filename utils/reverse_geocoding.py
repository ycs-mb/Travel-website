"""
Reverse Geocoding Utility

Converts GPS coordinates (latitude, longitude) to human-readable location names.
Uses geopy with Nominatim (OpenStreetMap) for free geocoding.
Includes caching to minimize API calls and respect rate limits.
"""

from typing import Dict, Optional, Tuple
import logging
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from utils.logger import log_info, log_error


class ReverseGeocoder:
    """
    Reverse geocoding service with caching.
    
    Converts GPS coordinates to location names using OpenStreetMap's Nominatim service.
    """
    
    def __init__(self, config: Dict, logger: logging.Logger):
        """
        Initialize reverse geocoder.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.logger = logger
        self.config = config.get('reverse_geocoding', {})
        
        # Configuration
        self.enabled = self.config.get('enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_ttl_hours = self.config.get('cache_ttl_hours', 24)
        self.timeout = self.config.get('timeout_seconds', 5)
        self.user_agent = self.config.get('user_agent', 'TravelPhotoAnalysis/1.0')
        
        # Initialize geocoder
        if self.enabled:
            self.geolocator = Nominatim(user_agent=self.user_agent, timeout=self.timeout)
        else:
            self.geolocator = None
        
        # Cache setup
        self.cache_file = Path(__file__).parent.parent / 'cache' / 'geocoding_cache.json'
        self.cache = self._load_cache() if self.cache_enabled else {}
        
        # Rate limiting (Nominatim requires max 1 request per second)
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
        
        log_info(self.logger, f"Reverse geocoding initialized (enabled: {self.enabled}, cache: {self.cache_enabled})", "ReverseGeocoding")
    
    def _load_cache(self) -> Dict:
        """Load geocoding cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    log_info(self.logger, f"Loaded {len(cache)} cached locations", "ReverseGeocoding")
                    return cache
            except Exception as e:
                log_error(self.logger, "ReverseGeocoding", "CacheLoadError", f"Failed to load cache: {e}", "warning")
        
        # Create cache directory if it doesn't exist
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        return {}
    
    def _save_cache(self):
        """Save geocoding cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            log_error(self.logger, "ReverseGeocoding", "CacheSaveError", f"Failed to save cache: {e}", "warning")
    
    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key from coordinates (rounded to 4 decimal places)."""
        return f"{lat:.4f},{lon:.4f}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        if 'timestamp' not in cache_entry:
            return False
        
        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        expiry_time = cached_time + timedelta(hours=self.cache_ttl_hours)
        return datetime.now() < expiry_time
    
    def _rate_limit(self):
        """Enforce rate limiting (1 request per second for Nominatim)."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """
        Convert GPS coordinates to location information.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dictionary with location information or None if geocoding fails
            {
                'city': 'City name',
                'state': 'State/Region',
                'country': 'Country',
                'formatted': 'City, State, Country'
            }
        """
        if not self.enabled or self.geolocator is None:
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(lat, lon)
        if self.cache_enabled and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry):
                log_info(self.logger, f"Cache hit for {cache_key}", "ReverseGeocoding")
                return cache_entry.get('location')
        
        # Rate limiting
        self._rate_limit()
        
        # Perform reverse geocoding
        try:
            log_info(self.logger, f"Reverse geocoding ({lat:.4f}, {lon:.4f})", "ReverseGeocoding")
            location = self.geolocator.reverse((lat, lon), language='en')
            
            if location and location.raw:
                address = location.raw.get('address', {})
                
                # Extract location components
                city = (
                    address.get('city') or 
                    address.get('town') or 
                    address.get('village') or 
                    address.get('municipality') or
                    address.get('county')
                )
                
                state = (
                    address.get('state') or 
                    address.get('region') or
                    address.get('province')
                )
                
                country = address.get('country')
                
                # Build formatted location
                location_parts = []
                if city:
                    location_parts.append(city)
                if state and state != city:
                    location_parts.append(state)
                if country:
                    location_parts.append(country)
                
                location_data = {
                    'city': city,
                    'state': state,
                    'country': country,
                    'formatted': ', '.join(location_parts) if location_parts else None
                }
                
                # Cache the result
                if self.cache_enabled:
                    self.cache[cache_key] = {
                        'location': location_data,
                        'timestamp': datetime.now().isoformat()
                    }
                    self._save_cache()
                
                log_info(self.logger, f"Geocoded to: {location_data.get('formatted')}", "ReverseGeocoding")
                return location_data
            
            return None
            
        except GeocoderTimedOut:
            log_error(self.logger, "ReverseGeocoding", "Timeout", f"Geocoding timed out for ({lat}, {lon})", "warning")
            return None
        except GeocoderServiceError as e:
            log_error(self.logger, "ReverseGeocoding", "ServiceError", f"Geocoding service error: {e}", "warning")
            return None
        except Exception as e:
            log_error(self.logger, "ReverseGeocoding", "Error", f"Geocoding failed: {e}", "warning")
            return None
    
    def format_location(self, lat: float, lon: float, location_data: Optional[Dict[str, str]] = None) -> str:
        """
        Format location for display.
        
        Args:
            lat: Latitude
            lon: Longitude
            location_data: Optional pre-fetched location data
        
        Returns:
            Formatted location string
        """
        if location_data is None:
            location_data = self.reverse_geocode(lat, lon)
        
        if location_data and location_data.get('formatted'):
            return f"{location_data['formatted']} ({lat:.4f}, {lon:.4f})"
        else:
            return f"({lat:.4f}, {lon:.4f})"


# Convenience function for simple usage
def get_location_name(lat: float, lon: float, config: Dict, logger: logging.Logger) -> Optional[str]:
    """
    Simple function to get location name from coordinates.
    
    Args:
        lat: Latitude
        lon: Longitude
        config: Configuration dictionary
        logger: Logger instance
    
    Returns:
        Formatted location string or None
    """
    geocoder = ReverseGeocoder(config, logger)
    location_data = geocoder.reverse_geocode(lat, lon)
    
    if location_data:
        return location_data.get('formatted')
    
    return None
