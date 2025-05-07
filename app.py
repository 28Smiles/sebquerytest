from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from typing import Optional
from datetime import datetime, timezone
import tempfile
import os
from urllib.parse import urlparse

app = FastAPI()


def is_using_seb(request: Request) -> bool:
    user_agent = request.headers.get("user-agent")
    if user_agent:
        return "SEB" in user_agent
    return False

def create_file_content(wwroot: str, id: Optional[int]) -> str:
    if id is None:
        return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>startURL</key>
    <string>http://{wwroot}</string>
    <key>examSessionReconfigureAllow</key>
    <true />
    <key>allowQuit</key>
    <true />
</dict>
</plist>'''

    with open("config.seb.template") as f:
        content = f.read()
        content = content.replace("host:8000", wwroot)
        content = content.replace("?id=1", f"?id={id}")
        return content

def generate_temp_file(content: str) -> str:
    fd, path = tempfile.mkstemp(text=True)
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(content)
    return path


def get_headers():
    return {
        "Cache-Control": "private, max-age=1, no-transform",
        "Expires": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "Pragma": "no-cache",
        "Content-Disposition": "attachment; filename=config.seb",
        "Content-Type": "application/seb"
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    wwwroot = urlparse(str(request.base_url)).netloc
    if not is_using_seb(request):
        return f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Welcome</h1>
        <a href="seb://{wwwroot}/start">Start</a>
    </body>
    </html>
    """

    content = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Welcome</h1>
        <h2>Query Parameters Not Picked Up</h2>
        <a href="seb://{wwwroot}/start?id=1?aid=1">Start 1 1</a>
        <a href="seb://{wwwroot}/start?id=1?aid=2">Start 1 2</a>
        <a href="seb://{wwwroot}/start?id=2?aid=1">Start 2 1</a>
        <a href="seb://{wwwroot}/start?id=2?aid=2">Start 2 2</a>
        <h2>Query Parameters More Params</h2>
        <a href="seb://{wwwroot}/start?id=1&bid=1?aid=1&cid=1">Start 1 1</a>
        <a href="seb://{wwwroot}/start?id=1&bid=1?aid=2&cid=2">Start 1 2</a>
        <a href="seb://{wwwroot}/start?id=2&bid=2?aid=1&cid=1">Start 2 1</a>
        <a href="seb://{wwwroot}/start?id=2&bid=2?aid=2&cid=2">Start 2 2</a>
    </body>
    </html>
    """
    return content


@app.get("/start")
async def start(request: Request):
    wwwroot = urlparse(str(request.base_url)).netloc
    # The following is crude but fastapi does not ignore the second ?.
    queryparams = request.url.__str__().split("?")[1] if "?" in request.url.__str__() else ""
    id = None
    if queryparams.startswith("id="):
        id = int(queryparams[3:4])

    file_content = create_file_content(wwwroot, id)
    temp_file = generate_temp_file(file_content)

    return FileResponse(
        temp_file,
        headers=get_headers(),
        filename=f"config.seb",
        background=None
    )


@app.get("/home", response_class=HTMLResponse)
async def application(request: Request):
    # The following is crude but fastapi does not ignore the second ?.
    queryparams = request.url.__str__().split("?")[1] if "?" in request.url.__str__() else ""
    id = None
    if queryparams.startswith("id="):
        id = int(queryparams[3:4])

    content = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Application Page</h1>
        <p>URL: {request.url}</p>
        <a href="/stop?id={id}">Stop</a>
    </body>
    </html>
    """
    return content


@app.get("/stop")
async def stop():
    return RedirectResponse(url="/")
