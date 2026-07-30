import webbrowser
import subprocess
import sys
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from lost_found.router import router as lost_found_router

app = FastAPI(title="Campus Helpdesk AI Agent")

# allow frontend page to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lost_found_router)

# other teammates add their routers here same way:
# app.include_router(other_feature_router)

app.mount("/cab-assets", StaticFiles(directory="campus_cab"), name="cab-assets")

# serve the website at http://127.0.0.1:8000/
app.mount("/", StaticFiles(directory="static", html=True), name="static")


def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    import uvicorn

    chat_process = None
    if not is_port_open(5000):
        chat_process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd="college_chat",
        )

    webbrowser.open("http://127.0.0.1:8000")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        if chat_process:
            chat_process.terminate()
