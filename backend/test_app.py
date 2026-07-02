import asyncio
import httpx
import sys
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def run_tests():
    print("Testing API Endpoints...")

    # 1. Health check
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        print(f"\n[GET /health] Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
        assert response.status_code == 200
        assert response.json()["data"]["database"] == "ok"
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

    # 2. Create a Saved Search
    search_payload = {
        "name": "Software Engineer Remote",
        "job_title": "Software Engineer",
        "field_domain": "Technology",
        "location": "United States",
        "work_mode": "remote",
        "poll_interval_minutes": 60
    }
    
    try:
        response = httpx.post(f"{BASE_URL}/searches", json=search_payload, timeout=10.0)
        print(f"\n[POST /searches] Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
        assert response.status_code == 201
        search_id = response.json()["data"]["id"]
    except Exception as e:
        print(f"Create search failed: {e}")
        sys.exit(1)

    # 3. List Saved Searches
    try:
        response = httpx.get(f"{BASE_URL}/searches", timeout=10.0)
        print(f"\n[GET /searches] Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
    except Exception as e:
        print(f"List searches failed: {e}")
        sys.exit(1)
        
    print("\n✅ All tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
