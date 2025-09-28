import json
import os
import hashlib
import pickle
import logging
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading
from pathlib import Path


class CacheManager:
    def __init__(self, cache_dir: str = "cache", expiry_days: int = 30, max_cache_size_mb: int = 100):
        """
        Initialize the cache manager with improved error handling and performance.
        
        Args:
            cache_dir: Directory to store cache files
            expiry_days: Number of days before cache expires
            max_cache_size_mb: Maximum cache size in MB before cleanup
        """
        self.cache_dir = cache_dir
        self.expiry_days = expiry_days
        self.max_cache_size_mb = max_cache_size_mb
        self._lock = threading.RLock()  # Thread-safe operations
        self._setup_logging()
        self.ensure_cache_dir()
    
    def _setup_logging(self):
        """Setup logging for cache operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_cache_dir(self) -> bool:
        """Ensure the cache directory exists with comprehensive error handling."""
        try:
            cache_path = Path(self.cache_dir)
            if not cache_path.exists():
                cache_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created cache directory: {self.cache_dir}")
            return True
        except PermissionError:
            self.logger.warning(f"Permission denied creating cache directory {self.cache_dir}")
            # Fallback to temp directory
            self.cache_dir = tempfile.mkdtemp(prefix="ate_cache_")
            self.logger.info(f"Using temporary cache directory: {self.cache_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create cache directory: {e}")
            # Final fallback to system temp
            self.cache_dir = tempfile.mkdtemp(prefix="ate_cache_")
            self.logger.info(f"Using system temp directory: {self.cache_dir}")
            return True
    
    def get_cache_key(self, brand: str, model: str, options: str = None) -> str:
        """Generate a unique cache key for brand, model, and options combination."""
        try:
            # Normalize inputs and create consistent cache keys
            brand_norm = brand.strip().lower() if brand else ""
            model_norm = model.strip().lower() if model else ""
            options_norm = options.strip().lower() if options else ""
            
            cache_string = f"{brand_norm}|{model_norm}|{options_norm}"
            return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating cache key: {e}")
            # Fallback to simple hash
            fallback_string = f"{brand or ''}{model or ''}{options or ''}"
            return hashlib.md5(fallback_string.encode('utf-8')).hexdigest()
    
    def get_cache_path(self, cache_key: str) -> str:
        """Get the full path for a cache file."""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")
    
    def is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache file exists and is not expired."""
        try:
            if not os.path.exists(cache_path):
                return False
            
            # Check if cache is older than expiry days
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            expiry_time = cache_time + timedelta(days=self.expiry_days)
            
            is_valid = datetime.now() < expiry_time
            if not is_valid:
                self.logger.info(f"Cache expired for {cache_path}")
            return is_valid
        except Exception as e:
            self.logger.error(f"Error checking cache validity: {e}")
            return False
    
    def load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load cached data if it exists and is valid."""
        with self._lock:
            try:
                cache_path = self.get_cache_path(cache_key)
                
                if not self.is_cache_valid(cache_path):
                    return None
                
                with open(cache_path, "rb") as f:
                    cached_data = pickle.load(f)
                    self.logger.info(f"Loaded cached data for {cache_key}")
                    return cached_data
            except FileNotFoundError:
                self.logger.debug(f"Cache file not found for {cache_key}")
                return None
            except Exception as e:
                self.logger.error(f"Error loading cache for {cache_key}: {e}")
                # Try to remove corrupted cache file
                try:
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
                        self.logger.info(f"Removed corrupted cache file: {cache_path}")
                except:
                    pass
                return None
    
    def save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """Save data to cache with error handling."""
        with self._lock:
            try:
                self.ensure_cache_dir()
                cache_path = self.get_cache_path(cache_key)
                
                # Create temporary file first for atomic write
                temp_path = cache_path + ".tmp"
                with open(temp_path, "wb") as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                
                # Atomic move
                os.replace(temp_path, cache_path)
                self.logger.info(f"Saved data to cache for {cache_key}")
                
                # Check cache size and cleanup if needed
                self._cleanup_if_needed()
                return True
            except Exception as e:
                self.logger.error(f"Error saving to cache for {cache_key}: {e}")
                # Clean up temp file if it exists
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                return False
    
    def _cleanup_if_needed(self):
        """Clean up old cache files if cache size exceeds limit."""
        try:
            cache_stats = self.get_cache_stats()
            if cache_stats["total_size"] > self.max_cache_size_mb * 1024 * 1024:
                self.logger.info("Cache size limit exceeded, cleaning up old files")
                self._cleanup_old_files()
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
    
    def _cleanup_old_files(self):
        """Remove oldest cache files to stay under size limit."""
        try:
            cache_files = []
            for file in os.listdir(self.cache_dir):
                if file.endswith(".pkl"):
                    file_path = os.path.join(self.cache_dir, file)
                    mtime = os.path.getmtime(file_path)
                    size = os.path.getsize(file_path)
                    cache_files.append((file_path, mtime, size))
            
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x[1])
            
            # Remove oldest files until under limit
            current_size = sum(f[2] for f in cache_files)
            target_size = self.max_cache_size_mb * 1024 * 1024 * 0.8  # 80% of limit
            
            for file_path, _, size in cache_files:
                if current_size <= target_size:
                    break
                try:
                    os.remove(file_path)
                    current_size -= size
                    self.logger.info(f"Removed old cache file: {file_path}")
                except Exception as e:
                    self.logger.error(f"Error removing cache file {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error during old file cleanup: {e}")
    
    def clear_cache(self) -> bool:
        """Clear all cache files."""
        with self._lock:
            try:
                if not os.path.exists(self.cache_dir):
                    return True
                
                removed_count = 0
                for file in os.listdir(self.cache_dir):
                    if file.endswith(".pkl"):
                        try:
                            os.remove(os.path.join(self.cache_dir, file))
                            removed_count += 1
                        except Exception as e:
                            self.logger.error(f"Error removing cache file {file}: {e}")
                
                self.logger.info(f"Cleared {removed_count} cache files")
                return True
            except Exception as e:
                self.logger.error(f"Error clearing cache: {e}")
                return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            if not os.path.exists(self.cache_dir):
                return {
                    "total_files": 0, 
                    "total_size": 0, 
                    "cache_dir": self.cache_dir,
                    "expiry_days": self.expiry_days,
                    "max_size_mb": self.max_cache_size_mb
                }
            
            files = [f for f in os.listdir(self.cache_dir) if f.endswith(".pkl")]
            total_size = 0
            valid_files = 0
            expired_files = 0
            
            for file in files:
                file_path = os.path.join(self.cache_dir, file)
                try:
                    size = os.path.getsize(file_path)
                    total_size += size
                    
                    if self.is_cache_valid(file_path):
                        valid_files += 1
                    else:
                        expired_files += 1
                except Exception as e:
                    self.logger.error(f"Error checking file {file}: {e}")
            
            return {
                "total_files": len(files),
                "valid_files": valid_files,
                "expired_files": expired_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_dir": self.cache_dir,
                "expiry_days": self.expiry_days,
                "max_size_mb": self.max_cache_size_mb
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {
                "total_files": 0, 
                "total_size": 0, 
                "cache_dir": self.cache_dir,
                "error": str(e)
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired cache files and return count of removed files."""
        with self._lock:
            try:
                if not os.path.exists(self.cache_dir):
                    return 0
                
                removed_count = 0
                for file in os.listdir(self.cache_dir):
                    if file.endswith(".pkl"):
                        file_path = os.path.join(self.cache_dir, file)
                        if not self.is_cache_valid(file_path):
                            try:
                                os.remove(file_path)
                                removed_count += 1
                                self.logger.info(f"Removed expired cache file: {file}")
                            except Exception as e:
                                self.logger.error(f"Error removing expired file {file}: {e}")
                
                if removed_count > 0:
                    self.logger.info(f"Cleaned up {removed_count} expired cache files")
                return removed_count
            except Exception as e:
                self.logger.error(f"Error cleaning up expired files: {e}")
                return 0


# Create a singleton instance for the application
cache_manager = CacheManager(
    cache_dir=os.getenv("CACHE_DIR", "cache"), 
    expiry_days=int(os.getenv("CACHE_EXPIRY_DAYS", "30")),
    max_cache_size_mb=int(os.getenv("MAX_CACHE_SIZE_MB", "100"))
) 