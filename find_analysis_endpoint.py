#!/usr/bin/env python
"""Try to find stream analysis/probe endpoints in Dispatcharr."""

from api.dispatcharr_client import DispatcharrClient
import requests

def main():
    client = DispatcharrClient(
        base_url="http://192.168.10.10:9192",
        username="jose",
        password="rotring1010"
    )
    
    # Try different potential endpoints for stream analysis
    channel_id = 614
    stream_ids = [776, 720, 531]
    
    endpoints_to_try = [
        # Stream-specific endpoints
        f"/api/streams/{stream_ids[0]}/analyze",
        f"/api/streams/{stream_ids[0]}/probe",
        f"/api/streams/{stream_ids[0]}/test",
        f"/api/streams/{stream_ids[0]}/stats",
        f"/api/streams/{stream_ids[0]}/update_stats",
        f"/api/streams/{stream_ids[0]}/refresh",
        # Channel-specific endpoints
        f"/api/channels/channels/{channel_id}/analyze",
        f"/api/channels/channels/{channel_id}/probe",
        f"/api/channels/channels/{channel_id}/test",
        f"/api/channels/channels/{channel_id}/update_stats",
    ]
    
    print("="*80)
    print("TESTING POTENTIAL ANALYSIS ENDPOINTS")
    print("="*80)
    
    for endpoint in endpoints_to_try:
        url = f"{client.base_url}{endpoint}"
        print(f"\n📡 Testing: {endpoint}")
        
        # Try GET
        try:
            response = client.session.get(url)
            if response.status_code == 200:
                print(f"  ✓ GET {response.status_code}: {response.text[:200]}")
            elif response.status_code == 404:
                print(f"  ✗ GET 404 (not found)")
            else:
                print(f"  ? GET {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ✗ GET error: {str(e)[:80]}")
        
        # Try POST
        try:
            response = client.session.post(url, json={})
            if response.status_code in [200, 201]:
                print(f"  ✓ POST {response.status_code}: {response.text[:200]}")
            elif response.status_code == 404:
                print(f"  ✗ POST 404 (not found)")
            elif response.status_code == 405:
                print(f"  ⚠ POST 405 (method not allowed - GET might work)")
            else:
                print(f"  ? POST {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ✗ POST error: {str(e)[:80]}")
    
    print("\n" + "="*80)
    print("CHECKING SWAGGER/OPENAPI ENDPOINTS")
    print("="*80)
    
    swagger_endpoints = [
        "/swagger",
        "/api/swagger",
        "/swagger.json",
        "/api/swagger.json",
        "/openapi.json",
        "/api/openapi.json",
        "/docs",
        "/api/docs",
        "/redoc",
        "/api/redoc",
    ]
    
    for endpoint in swagger_endpoints:
        url = f"{client.base_url}{endpoint}"
        try:
            response = client.session.get(url)
            if response.status_code == 200:
                content = response.text[:300]
                if "swagger" in content.lower() or "openapi" in content.lower() or "{" in content:
                    print(f"\n✓ Found: {endpoint}")
                    print(f"  Preview: {content[:150]}")
        except:
            pass

if __name__ == "__main__":
    main()
