import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()
class RedisCache:
    def __init__(self):
        """
        Initializes Redis connection.
        """
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )

    def set_cache(self, key, value, expiry_time=None):
        """
        Stores a value in Redis with an optional expiry time.
        """
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value)  # Convert to JSON if necessary

        self.redis_client.set(key, value, ex=expiry_time)

    def get_cache(self, key):
        """
        Retrieves a value from Redis.
        """
        value = self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)  # Convert JSON back to Python object
            except json.JSONDecodeError:
                return value  # Return as-is if not JSON
        return None

    def delete_cache(self, key):
        """
        Deletes a key from Redis.
        """
        self.redis_client.delete(key)

    def flush_cache(self):
        """
        Clears all keys in the Redis database.
        """
        self.redis_client.flushdb()

    def key_exists(self, key):
        """
        Checks if a key exists in Redis.
        """
        return self.redis_client.exists(key)

# # Example Usage
# def main():
#     # print(os.getenv("REDIS_HOST"))
#     # print(os.getenv("REDIS_PORT"))
#     # print(os.getenv("REDIS_PASSWORD"))
#     # exit()
#     redis_cache = RedisCache()

#     # Set the key "bar" to the value "foo"
#     redis_cache.set_cache("bar", "foo")
#     print("Set 'bar' to 'foo'")

#     # Retrieve the value of the key "bar"
#     value = redis_cache.get_cache("bar")
#     print(f"Value of 'bar': {value}")

# if __name__ == "__main__":
#     main()
