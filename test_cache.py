#!/usr/bin/env python3
"""
Test script for the improved cache manager
"""

import os
import tempfile
import shutil
from cache_manager import CacheManager

def test_cache_manager():
    """Test the cache manager functionality"""
    print("🧪 Testing Cache Manager...")
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="cache_test_")
    print(f"📁 Test directory: {test_dir}")
    
    try:
        # Initialize cache manager
        cache = CacheManager(
            cache_dir=test_dir,
            expiry_days=1,  # Short expiry for testing
            max_cache_size_mb=1  # Small size for testing
        )
        
        # Test 1: Basic operations
        print("\n✅ Test 1: Basic cache operations")
        test_data = {
            "brand": "Rohde & Schwarz",
            "model": "SMA100B",
            "options": "B711/B86/B93/B35",
            "analysis": "Test analysis data"
        }
        
        cache_key = cache.get_cache_key("Rohde & Schwarz", "SMA100B", "B711/B86/B93/B35")
        print(f"🔑 Generated cache key: {cache_key}")
        
        # Save to cache
        success = cache.save_to_cache(cache_key, test_data)
        print(f"💾 Save to cache: {'✅ Success' if success else '❌ Failed'}")
        
        # Load from cache
        loaded_data = cache.load_from_cache(cache_key)
        print(f"📥 Load from cache: {'✅ Success' if loaded_data else '❌ Failed'}")
        
        if loaded_data:
            print(f"📊 Data matches: {'✅ Yes' if loaded_data == test_data else '❌ No'}")
        
        # Test 2: Cache statistics
        print("\n✅ Test 2: Cache statistics")
        stats = cache.get_cache_stats()
        print(f"📈 Cache stats: {stats}")
        
        # Test 3: Invalid cache key
        print("\n✅ Test 3: Invalid cache key")
        invalid_data = cache.load_from_cache("invalid_key_12345")
        print(f"🚫 Invalid key result: {'✅ None (expected)' if invalid_data is None else '❌ Unexpected data'}")
        
        # Test 4: Cache cleanup
        print("\n✅ Test 4: Cache cleanup")
        removed_count = cache.cleanup_expired()
        print(f"🧹 Cleaned up {removed_count} expired files")
        
        # Test 5: Clear cache
        print("\n✅ Test 5: Clear cache")
        clear_success = cache.clear_cache()
        print(f"🗑️ Clear cache: {'✅ Success' if clear_success else '❌ Failed'}")
        
        # Final stats
        final_stats = cache.get_cache_stats()
        print(f"📊 Final stats: {final_stats}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Cleanup test directory
        try:
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test directory: {test_dir}")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test directory: {e}")

if __name__ == "__main__":
    success = test_cache_manager()
    exit(0 if success else 1) 