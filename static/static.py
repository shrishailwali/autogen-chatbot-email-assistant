import os
from fastapi.staticfiles import StaticFiles
from chatboot.agent import app

static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
