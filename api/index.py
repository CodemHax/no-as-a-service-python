import random
from pathlib import Path
from starlette.responses import JSONResponse, FileResponse
from fastapi import FastAPI, Request
import aiofiles
import json
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.staticfiles import StaticFiles


def get_ip(request: Request) -> str:
    return request.headers.get("cf-connecting-ip") or get_remote_address(request)


limiter = Limiter(key_func=get_ip, default_limits=["5/minute"])
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



project_root = Path(__file__).parent.parent
static_dir = project_root / "static"
favicon_path = static_dir / "favicon.ico"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


async def load_data():
    try:
        current_dir = Path(__file__).parent
        reasons_file = current_dir.parent / 'reasons.json'

        async with aiofiles.open(reasons_file, mode='r', encoding='utf-8') as f:
            contents = await f.read()
            return json.loads(contents)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading reasons.json: {e}")
        return []



@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)
@app.get("/no")
@limiter.limit("120/minute")
async def root(request: Request):
    data = await load_data()
    if data:
        choose = random.choice(data)
        return JSONResponse(content={"reason": choose}, status_code=200)
    else:
        return JSONResponse(content={"reason": "No reasons available."}, status_code=500)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
