import hashlib, json, os, subprocess, time
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Gallery Resolver API")

CACHE_DIR = "cache"
CACHE_TTL = 6 * 60 * 60  # 6 hours
os.makedirs(CACHE_DIR, exist_ok=True)


def cache_path(key):
    return f"{CACHE_DIR}/{key}.json"


def resolve_gallery(url: str):
    gid = hashlib.md5(url.encode()).hexdigest()[:16]
    cpath = cache_path(gid)

    # Return cached if fresh
    if os.path.exists(cpath):
        if time.time() - os.path.getmtime(cpath) < CACHE_TTL:
            return json.load(open(cpath))

    # Resolve with gallery-dl -g
    p = subprocess.run(["gallery-dl", "-g", url], capture_output=True, text=True, timeout=120)
    if p.returncode != 0 or not p.stdout.strip():
        raise HTTPException(400, "gallery-dl failed")

    files = [x.strip() for x in p.stdout.splitlines() if x.strip()]
    data = {"gid": gid, "count": len(files), "images": files}

    json.dump(data, open(cpath, "w"))
    return data


@app.get("/resolve")
def resolve(url: str = Query(..., min_length=8, max_length=2048)):
    return resolve_gallery(url)
