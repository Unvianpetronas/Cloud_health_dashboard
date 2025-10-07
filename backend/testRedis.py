# check_redis.py
import redis

# --- Configuration ---
# Change this if your Redis server is not on localhost or uses a different port
REDIS_HOST = "localhost"
REDIS_PORT = 6379

def check_redis_connection():
    """
    Connects to Redis, checks the connection, and verifies it can
    set and get a value.
    """
    print(f"🐍 Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT}...")

    try:
        # 1. Establish a connection
        # decode_responses=True makes the output a normal string instead of bytes
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

        # 2. Check the connection with PING
        response = r.ping()
        if response:
            print("✅ Connection Successful! Server responded to PING.")
        else:
            print("❌ Connection failed. Server did not respond to PING.")
            return

        # 3. Check if it's working (SET and GET)
        print("\nChecking functionality (SET/GET)...")
        r.set("python_test_key", "hello from python")
        value = r.get("python_test_key")

        if value == "hello from python":
            print(f"✅ Functionality Confirmed! Successfully SET and GET a key.")
            print(f"   - Retrieved value: '{value}'")
        else:
            print(f"❌ Functionality Failed! Could not retrieve the correct value.")
            print(f"   - Expected: 'hello from python', Got: '{value}'")

        # Clean up the key we created
        r.delete("python_test_key")

    except redis.exceptions.ConnectionError as e:
        print("\n---------------------------------------------------------")
        print(f"❌ CONNECTION FAILED: Could not connect to Redis.")
        print(f"   Error: {e}")
        print("\nTroubleshooting Tips:")
        print("   1. Is the Redis server running?")
        print("   2. Is the REDIS_HOST and REDIS_PORT correct in this script?")
        print("   3. Is a firewall blocking the connection?")
        print("---------------------------------------------------------")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    check_redis_connection()