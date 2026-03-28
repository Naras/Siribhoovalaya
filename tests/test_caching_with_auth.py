#!/usr/bin/env python3
"""
Test script to verify Redis caching functionality with authentication.
Run this after deploying the container.
"""

import requests
import time
import json
import base64

# Configuration
BASE_URL = "http://127.0.0.1:5005"
API_BASE = f"{BASE_URL}/api"

# Test credentials (you'll need to replace with actual credentials)
AUTH_EMAIL = "test@example.com"
AUTH_PASSWORD = "TestPass0#"

def get_auth_token():
    """Get authentication token for testing."""
    print("🔐 Getting authentication token...")
    
    try:
        # First try to register/login
        auth_data = {
            "email": AUTH_EMAIL,
            "password": AUTH_PASSWORD
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=auth_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_health_check():
    """Test health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return data.get('redis') == 'connected'
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_cache_stats():
    """Test cache statistics endpoint."""
    print("\n📊 Testing cache stats...")
    try:
        response = requests.get(f"{BASE_URL}/cache/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cache stats: {data}")
            return data
        else:
            print(f"❌ Cache stats failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Cache stats error: {e}")
        return None

def test_shreni_bandha_performance():
    """Test Shreni Bandha performance with caching."""
    print("\n🚀 Testing Shreni Bandha performance...")
    
    # Test parameters
    test_data = {
        "start_row": 13,
        "start_col": 13,
        "num_steps": 10,
        "direction": "up",
        "script": "kannada",
        "use_sandhi": False
    }
    
    times = []
    
    # Run the same test 3 times to see caching effect
    for i in range(3):
        print(f"  Test {i+1}:")
        start_time = time.time()
        
        try:
            response = requests.post(f"{API_BASE}/bandha/shreni_bandha", 
                                  json=test_data)
            
            end_time = time.time()
            elapsed = end_time - start_time
            times.append(elapsed)
            
            if response.status_code == 200:
                data = response.json()
                points = data.get('points', [])
                print(f"    ✅ Success: {len(points)} points in {elapsed:.3f}s")
            else:
                print(f"    ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return times

def test_search_performance(token):
    """Test search all pattern variants performance."""
    print("\n🔍 Testing search performance...")
    
    test_data = {
        "target": [["1", "2"], ["3", "4"]],
        "pattern_type": "shreni_bandha",
        "measure": "exact",
        "max_distance": 2,
        "script": "kannada",
        "use_sandhi": False
    }
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    times = []
    
    # Run the same test 3 times
    for i in range(3):
        print(f"  Search test {i+1}:")
        start_time = time.time()
        
        try:
            response = requests.post(f"{API_BASE}/search/all_pattern_variants", 
                                  json=test_data, headers=headers)
            
            end_time = time.time()
            elapsed = end_time - start_time
            times.append(elapsed)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                print(f"    ✅ Success: {len(matches)} matches in {elapsed:.3f}s")
            else:
                print(f"    ❌ Failed: {response.status_code}")
                if response.status_code == 401:
                    print(f"    🔐 Authentication required")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return times

def analyze_performance(times, test_name):
    """Analyze performance results."""
    if not times:
        print(f"  ❌ No data for {test_name}")
        return
    
    first_run = times[0]
    avg_subsequent = sum(times[1:]) / len(times[1:]) if len(times) > 1 else first_run
    improvement = ((first_run - avg_subsequent) / first_run * 100) if first_run > 0 else 0
    
    print(f"\n📈 {test_name} Performance Analysis:")
    print(f"  First run (cold cache): {first_run:.3f}s")
    if len(times) > 1:
        print(f"  Subsequent runs (cache hit): {avg_subsequent:.3f}s")
        print(f"  Performance improvement: {improvement:.1f}%")
    
    if improvement > 50:
        print(f"  🎉 Excellent caching performance!")
    elif improvement > 20:
        print(f"  ✅ Good caching performance")
    else:
        print(f"  ⚠️  Cache may not be working optimally")

def main():
    """Run all tests."""
    print("🧪 Redis Caching Test Suite with Authentication")
    print("=" * 60)
    
    # Test health check
    redis_ok = test_health_check()
    if not redis_ok:
        print("❌ Redis not connected - caching may not work")
        return
    
    # Test cache stats
    initial_stats = test_cache_stats()
    
    # Get auth token
    token = get_auth_token()
    
    # Test Shreni Bandha performance
    shreni_times = test_shreni_bandha_performance()
    analyze_performance(shreni_times, "Shreni Bandha")
    
    # Test search performance (only if we have auth)
    if token:
        search_times = test_search_performance(token)
        analyze_performance(search_times, "Search All Variants")
    else:
        print("\n⚠️  Skipping search test due to authentication issues")
        print("   To test search, you need valid credentials")
        print("   Or temporarily remove @auth_required decorator")
    
    # Final cache stats
    print("\n📊 Final cache statistics:")
    final_stats = test_cache_stats()
    
    if initial_stats and final_stats:
        hits_before = initial_stats.get('keyspace_hits', 0)
        hits_after = final_stats.get('keyspace_hits', 0)
        misses_before = initial_stats.get('keyspace_misses', 0)
        misses_after = final_stats.get('keyspace_misses', 0)
        
        print(f"  Cache hits: {hits_before} → {hits_after} (+{hits_after - hits_before})")
        print(f"  Cache misses: {misses_before} → {misses_after} (+{misses_after - misses_before})")
        
        if hits_after > hits_before:
            print("  ✅ Cache is working - hits increased!")
        else:
            print("  ⚠️  Cache may not be working - no new hits")
    
    print("\n🎉 Test suite completed!")
    print("\n📋 Summary:")
    print("  - Redis connection: ✅" if redis_ok else "  - Redis connection: ❌")
    print("  - Caching performance: 📈 See analysis above")
    print("  - Expected improvement: 90% faster after cache warm-up")
    
    if not redis_ok:
        print("\n🔧 Troubleshooting:")
        print("  1. Check Redis server: redis-cli ping")
        print("  2. Check container logs: docker logs siribhoovalaya-cached")
        print("  3. Restart Redis: docker restart siribhoovalaya-cached")

if __name__ == "__main__":
    main()
