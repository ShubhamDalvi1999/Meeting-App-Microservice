"""
Log sampling module for reducing log volume on high-traffic endpoints.
Provides configurable sampling rates for different endpoints and log levels.
"""

import logging
import random
import re
from typing import Dict, List, Optional, Union, Pattern
import threading
import time

logger = logging.getLogger(__name__)

class SamplingConfig:
    """Configuration for log sampling."""
    
    def __init__(self, 
                 default_rate: float = 1.0,
                 path_rates: Optional[Dict[str, float]] = None,
                 method_rates: Optional[Dict[str, float]] = None,
                 level_rates: Optional[Dict[str, float]] = None):
        """
        Initialize sampling configuration.
        
        Args:
            default_rate: Default sampling rate (0.0-1.0) where 1.0 means log everything
            path_rates: Dict mapping path patterns to sampling rates
            method_rates: Dict mapping HTTP methods to sampling rates
            level_rates: Dict mapping log levels to sampling rates
        """
        self.default_rate = max(0.0, min(1.0, default_rate))
        self.path_rates = path_rates or {}
        self.method_rates = method_rates or {}
        self.level_rates = level_rates or {}
        
        # Compile path patterns
        self.path_patterns = {}
        for path, rate in self.path_rates.items():
            try:
                self.path_patterns[re.compile(path)] = max(0.0, min(1.0, rate))
            except re.error:
                logger.warning(f"Invalid path pattern: {path}")
        
        # Normalize method rates
        for method, rate in self.method_rates.items():
            self.method_rates[method.upper()] = max(0.0, min(1.0, rate))
        
        # Normalize level rates
        for level, rate in self.level_rates.items():
            if isinstance(level, str):
                level_num = logging.getLevelName(level.upper())
                if isinstance(level_num, int):
                    self.level_rates[level_num] = max(0.0, min(1.0, rate))
                else:
                    logger.warning(f"Invalid log level: {level}")
            else:
                self.level_rates[level] = max(0.0, min(1.0, rate))
    
    def get_rate_for_path(self, path: str) -> float:
        """
        Get sampling rate for a path.
        
        Args:
            path: Request path
            
        Returns:
            Sampling rate (0.0-1.0)
        """
        for pattern, rate in self.path_patterns.items():
            if pattern.search(path):
                return rate
        return self.default_rate
    
    def get_rate_for_method(self, method: str) -> float:
        """
        Get sampling rate for an HTTP method.
        
        Args:
            method: HTTP method
            
        Returns:
            Sampling rate (0.0-1.0)
        """
        return self.method_rates.get(method.upper(), self.default_rate)
    
    def get_rate_for_level(self, level: Union[int, str]) -> float:
        """
        Get sampling rate for a log level.
        
        Args:
            level: Log level (int or string)
            
        Returns:
            Sampling rate (0.0-1.0)
        """
        if isinstance(level, str):
            level = logging.getLevelName(level.upper())
        
        return self.level_rates.get(level, self.default_rate)


class LogSampler:
    """Log sampler for reducing log volume."""
    
    def __init__(self, config: Optional[SamplingConfig] = None):
        """
        Initialize log sampler.
        
        Args:
            config: Sampling configuration
        """
        self.config = config or SamplingConfig()
        self.request_counts = {}
        self.request_counts_lock = threading.Lock()
        
        # Clean up request counts periodically
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def should_log(self, 
                  path: Optional[str] = None, 
                  method: Optional[str] = None,
                  level: Optional[Union[int, str]] = None) -> bool:
        """
        Determine if a log entry should be included based on sampling rates.
        
        Args:
            path: Request path
            method: HTTP method
            level: Log level
            
        Returns:
            True if the log entry should be included, False otherwise
        """
        # Clean up request counts if needed
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            with self.request_counts_lock:
                self.request_counts = {}
                self.last_cleanup = current_time
        
        # Get sampling rates
        path_rate = self.config.default_rate
        if path:
            path_rate = self.config.get_rate_for_path(path)
        
        method_rate = self.config.default_rate
        if method:
            method_rate = self.config.get_rate_for_method(method)
        
        level_rate = self.config.default_rate
        if level:
            level_rate = self.config.get_rate_for_level(level)
        
        # Use the most restrictive rate
        rate = min(path_rate, method_rate, level_rate)
        
        # Always log if rate is 1.0
        if rate >= 1.0:
            return True
        
        # Never log if rate is 0.0
        if rate <= 0.0:
            return False
        
        # Generate a request key for counting
        request_key = f"{path or ''}:{method or ''}:{level or ''}"
        
        # Increment request count
        with self.request_counts_lock:
            count = self.request_counts.get(request_key, 0) + 1
            self.request_counts[request_key] = count
        
        # Deterministic sampling based on count
        return (count % int(1.0 / rate)) == 0


class SamplingLogFilter(logging.Filter):
    """Log filter that applies sampling to reduce log volume."""
    
    def __init__(self, sampler: Optional[LogSampler] = None):
        """
        Initialize sampling log filter.
        
        Args:
            sampler: Log sampler instance
        """
        super().__init__()
        self.sampler = sampler or LogSampler()
    
    def filter(self, record):
        """
        Filter log records based on sampling configuration.
        
        Args:
            record: Log record
            
        Returns:
            True if the record should be logged, False otherwise
        """
        # Get path and method from record if available
        path = getattr(record, 'path', None)
        method = getattr(record, 'method', None)
        
        # Check if we should log this record
        return self.sampler.should_log(path, method, record.levelno)


# Default sampler instance
_default_sampler = None

def get_default_sampler() -> LogSampler:
    """
    Get the default log sampler instance.
    
    Returns:
        Default log sampler
    """
    global _default_sampler
    if _default_sampler is None:
        _default_sampler = LogSampler()
    return _default_sampler

def configure_sampling(config: SamplingConfig) -> None:
    """
    Configure the default log sampler.
    
    Args:
        config: Sampling configuration
    """
    global _default_sampler
    _default_sampler = LogSampler(config)

def should_log(path: Optional[str] = None, 
              method: Optional[str] = None,
              level: Optional[Union[int, str]] = None) -> bool:
    """
    Determine if a log entry should be included based on sampling rates.
    
    Args:
        path: Request path
        method: HTTP method
        level: Log level
        
    Returns:
        True if the log entry should be included, False otherwise
    """
    return get_default_sampler().should_log(path, method, level) 