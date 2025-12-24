
import asyncio
import httpx
import time
import os
import io

API_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "your-secret-api-key-here")

# Define a minimal dummy image for testing
try:
    from PIL import Image
    import io
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    dummy_image = img_byte_arr.getvalue()
except ImportError:
    dummy_image = b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xDB\x00\x43\x00\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xC0\x00\x11\x08\x00\x64\x00\x64\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01\xFF\xC4\x00\x1F\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\xFF\xC4\x00\xB5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01\x7D\x01\x02\x03\x00\x04\x11\x05\x12\x21\x31\x41\x06\x13\x51\x61\x07\x22\x71\x14\x32\x81\x91\xA1\x08\x23\x42\xB1\xC1\x15\x52\xD1\xF0\x24\x33\x62\x72\x82\x09\x0A\x16\x17\x18\x19\x1A\x25\x26\x27\x28\x29\x2A\x34\x35\x36\x37\x38\x39\x3A\x43\x44\x45\x46\x47\x48\x49\x4A\x53\x54\x55\x56\x57\x58\x59\x5A\x63\x64\x65\x66\x67\x68\x69\x6A\x73\x74\x75\x76\x77\x78\x79\x7A\x83\x84\x85\x86\x87\x88\x89\x8A\x92\x93\x94\x95\x96\x97\x98\x99\x9A\xA2\xA3\xA4\xA5\xA6\xA7\xA8\xA9\xAA\xB2\xB3\xB4\xB5\xB6\xB7\xB8\xB9\xBA\xC2\xC3\xC4\xC5\xC6\xC7\xC8\xC9\xCA\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDA\xE1\xE2\xE3\xE4\xE5\xE6\xE7\xE8\xE9\xEA\xF1\xF2\xF3\xF4\xF5\xF6\xF7\xF8\xF9\xFA\xFF\xC4\x00\x1F\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\xFF\xC4\x00\xB5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02\x77\x00\x01\x02\x03\x11\x04\x05\x21\x31\x06\x12\x41\x51\x07\x61\x71\x13\x22\x32\x81\x08\x14\x42\x91\xA1\xB1\xC1\x09\x23\x33\x52\xF0\x15\x62\x72\xD1\x0A\x16\x24\x34\xE1\x25\xF1\x17\x18\x19\x1A\x26\x27\x28\x29\x2A\x35\x36\x37\x38\x39\x3A\x43\x44\x45\x46\x47\x48\x49\x4A\x53\x54\x55\x56\x57\x58\x59\x5A\x63\x64\x65\x66\x67\x68\x69\x6A\x73\x74\x75\x76\x77\x78\x79\x7A\x82\x83\x84\x85\x86\x87\x88\x89\x8A\x92\x93\x94\x95\x96\x97\x98\x99\x9A\xA2\xA3\xA4\xA5\xA6\xA7\xA8\xA9\xAA\xB2\xB3\xB4\xB5\xB6\xB7\xB8\xB9\xBA\xC2\xC3\xC4\xC5\xC6\xC7\xC8\xC9\xCA\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDA\xE2\xE3\xE4\xE5\xE6\xE7\xE8\xE9\xEA\xF2\xF3\xF4\xF5\xF6\xF7\xF8\xF9\xFA\xFF\xDA\x00\x0C\x03\x01\x00\x02\x11\x03\x11\x00\x3F\x00\xFA\x63\x1D\x0F\x8B\xDC\x02\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA2\x8A\x28\xA3\xFF\xD9'


async def test_api_concurrency():
    """Verify that multiple requests can be handled concurrently"""
    print("Testing API Concurrency...")
    
    headers = {"X-API-KEY": API_KEY}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check health
        resp = await client.get(f"{API_URL}/health")
        assert resp.status_code == 200, "Health check failed"
        print("✅ Health check 1 passed")
        
        # Start a long running task (simulate by calling metadata only, still takes some time)
        # We'll use the dummy image
        files = {'file': ('test.jpg', dummy_image, 'image/jpeg')}
        
        # We can't easily simulate a 'delay' inside the server without modifying code,
        # but the fact that we can ping /health while this runs is a good sign.
        # Since 'metadata' is fast, we might not catch the race, but let's try.
        
        print("Sending analysis request...")
        task = asyncio.create_task(
            client.post(
                f"{API_URL}/api/v1/analyze/image",
                headers=headers,
                files=files,
                data={"agents": ["metadata"]} # Just basic check
            )
        )
        
        # Immediately try to hit health again
        start = time.time()
        health_resp = await client.get(f"{API_URL}/health")
        duration = time.time() - start
        
        assert health_resp.status_code == 200
        print(f"✅ Health check 2 passed (latency: {duration:.4f}s)")
        
        if duration > 1.0:
            print("⚠️ Warning: Health check took longer than expected, might still be blocking?")
        
        try:
            await task
            print("✅ Analysis request completed")
        except Exception as e:
            print(f"Analysis failed (expected if agents key missing): {e}")

async def test_batch_processing():
    """Verify batch processing submission and status"""
    print("\nTesting Batch Processing...")
    
    headers = {"X-API-KEY": API_KEY}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = [
            ('files', ('img1.jpg', dummy_image, 'image/jpeg')),
            ('files', ('img2.jpg', dummy_image, 'image/jpeg'))
        ]
        
        print("Submitting batch job...")
        resp = await client.post(
            f"{API_URL}/api/v1/analyze/batch",
            headers=headers,
            files=files,
            data={"agents": ["metadata"]}
        )
        
        if resp.status_code != 200:
            print(f"❌ Batch submission failed: {resp.text}")
            return
            
        data = resp.json()
        job_id = data.get("job_id")
        print(f"✅ Job submitted: {job_id}")
        
        # Poll status
        for i in range(10):
            await asyncio.sleep(1)
            status_resp = await client.get(
                f"{API_URL}/api/v1/analyze/status/{job_id}",
                headers=headers
            )
            status_data = status_resp.json()
            status = status_data.get("status")
            progress = status_data.get("progress")
            print(f"Polling... Status: {status}, Progress: {progress}%")
            
            if status in ["completed", "failed"]:
                break
                
        if status == "completed":
            print("✅ Batch processing completed successfully!")
            results = status_data.get("results", [])
            print(f"Received {len(results)} results.")
            if len(results) > 0:
                 print(f"Sample result status: {results[0].get('status')}")
        else:
            print(f"❌ Timed out or failed. Final status: {status}")

if __name__ == "__main__":
    asyncio.run(test_api_concurrency())
    asyncio.run(test_batch_processing())
