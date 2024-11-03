from fastapi import FastAPI, HTTPException
import requests
import redis
import os

app = FastAPI()

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

API_KEY = os.getenv("API_KEY")
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))

@app.get("/definition/{word}")
def get_definition(word: str):
    cache_key = f"definition:{word}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return {"source": "redis", "data": cached_result.decode("utf-8")}
    
    response = requests.get(
        f"https://api.api-ninjas.com/v1/dictionary?word={word}",
        headers={'X-Api-Key': API_KEY}
    )
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Word not found")
    
    data = response.json()
    redis_client.setex(cache_key, CACHE_TTL, data["definition"])
    return {"source": "ninjas-api", "data": data["definition"]}

@app.get("/random-word")
def get_random_word():
    response = requests.get(
        f"https://api.api-ninjas.com/v1/randomword",
        headers={'X-Api-Key': API_KEY}
    )
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch random word")
    
    data = response.json()
    word = data["word"]
    
    
    return {"word": word}