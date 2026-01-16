"""
Quick script to check what's in Redis and debug the WebSocket client.
"""
import redis
import json

# Connect to Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

print("=== Redis Debug Info ===\n")

# Check all keys
all_keys = client.keys("*")
print(f"Total keys in Redis: {len(all_keys)}")
print(f"Keys: {all_keys[:20]}\n")  # Show first 20 keys

# Check for price keys
price_keys = client.keys("price:*")
print(f"\nPrice keys ({len(price_keys)}):")
for key in price_keys:
    data = client.get(key)
    print(f"  {key}: {data}")

# Check for history keys
history_keys = client.keys("history:*")
print(f"\nHistory keys ({len(history_keys)}):")
for key in history_keys[:5]:  # Show first 5
    count = client.llen(key)
    print(f"  {key}: {count} entries")
    if count > 0:
        latest = client.lindex(key, 0)
        print(f"    Latest: {latest}")

# Check logs
log_count = client.llen("logs:agent")
print(f"\nAgent logs: {log_count} entries")
if log_count > 0:
    latest_log = client.lindex("logs:agent", 0)
    print(f"  Latest: {latest_log}")
