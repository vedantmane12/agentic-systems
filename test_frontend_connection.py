#!/usr/bin/env python3
"""
Test frontend API connection
"""
import asyncio
import sys
import os

# Add frontend to path
sys.path.append('frontend')
from utils.api_client import APIClient

async def test_frontend_api():
    """Test the frontend API client"""
    
    print("🧪 Testing Frontend API Connection...")
    
    client = APIClient("http://localhost:8000")
    
    # Test 1: Health check
    print("\n1️⃣ Testing health check...")
    try:
        health = await client.health_check()
        print(f"✅ Health check: {health}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
    
    # Test 2: Get all tasks
    print("\n2️⃣ Testing get all tasks...")
    try:
        tasks = await client.get_all_tasks()
        print(f"✅ Tasks retrieved: {tasks.get('count', 0)} tasks")
        
        # Show completed tasks
        if tasks.get('tasks'):
            completed = [t for t in tasks['tasks'] if t.get('status') == 'completed']
            print(f"📋 Completed tasks: {len(completed)}")
            
            if completed:
                latest = completed[-1]  # Get latest completed task
                print(f"🎯 Latest completed task ID: {latest.get('task_id')}")
                print(f"📝 Query: {latest.get('query')}")
                print(f"✅ Has result: {'result' in latest}")
                
                if latest.get('result'):
                    result = latest['result']
                    print(f"📊 Result structure: {list(result.keys())}")
                    if 'report' in result:
                        print(f"📄 Report sections: {list(result['report'].keys())}")
    except Exception as e:
        print(f"❌ Get tasks failed: {str(e)}")
    
    # Test 3: Submit test research (optional)
    print("\n3️⃣ Testing research submission...")
    try:
        response = await client.execute_research("Quick test query")
        print(f"✅ Research submission: {response.get('status')}")
        
        if response.get('task_id'):
            task_id = response['task_id']
            print(f"🎯 Task ID: {task_id}")
            
            # Wait a moment and check status
            await asyncio.sleep(2)
            status = await client.get_task_status(task_id)
            print(f"📊 Initial status: {status.get('status')}")
            
    except Exception as e:
        print(f"❌ Research submission failed: {str(e)}")
    
    print("\n🏁 Frontend API test complete!")

if __name__ == "__main__":
    asyncio.run(test_frontend_api())