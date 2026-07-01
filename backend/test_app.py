import asyncio
import httpx
import uuid
import sys
import json

from config.database import AsyncSessionLocal
from models.user import User

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def setup_test_user():
    from config.settings import settings
    print("Database URL:", settings.database_url)
    async with AsyncSessionLocal() as session:
        user = User(email=f"test_{uuid.uuid4()}@example.com", display_name="Test User")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return str(user.id)

async def run_tests():
    print("Testing API Endpoints...")
    
    # 0. Setup dummy user
    try:
        user_id = await setup_test_user()
        print(f"[Setup] Created test user: {user_id}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to setup test user: {e}")
        sys.exit(1)

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
        "user_id": user_id,
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

    # 3. List Saved Searches for the user
    try:
        response = httpx.get(f"{BASE_URL}/searches", params={"user_id": user_id}, timeout=10.0)
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
