import hashlib, json, os, subprocess, time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Coomer Resolver API")

# ----------------- CORS -----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------------

CACHE_DIR = "cache"
CACHE_TTL = 6 * 60 * 60   # 6 hours
os.makedirs(CACHE_DIR, exist_ok=True)


def cache_path(key):
    return f"{CACHE_DIR}/{key}.json"


def h(s):
    return hashlib.sha1(s.encode()).hexdigest()[:12]


# ----------------- Resolver -----------------
def resolve_gallery(url: str):
    gid = hashlib.md5(url.encode()).hexdigest()[:16]
    cpath = cache_path(gid)

    # Use cache if still fresh
    if os.path.exists(cpath):
        if time.time() - os.path.getmtime(cpath) < CACHE_TTL:
            return json.load(open(cpath))

    # gallery-dl in link-only mode
    p = subprocess.run(
        ["gallery-dl", "-g", url],
        capture_output=True,
        text=True,
        timeout=120
    )

    urls = [x.strip() for x in p.stdout.splitlines() if x.strip()]
    items = [{"url": u, "h": h(u)} for u in urls]

    if not items:
        raise HTTPException(400, "No media found")

    data = {
        "gid": gid,
        "count": len(items),
        "items": items
    }

    json.dump(data, open(cpath, "w"))
    return data


# ----------------- API Endpoint -----------------
@app.get("/resolve")
def resolve(url: str = Query(..., min_length=8, max_length=2048)):
    return resolve_gallery(url)
