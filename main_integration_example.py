import webbrowser
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

# serve the frontend page at http://127.0.0.1:8000/
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    webbrowser.open("http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
