import os
import motor.motor_asyncio
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import socketio
from datetime import datetime, timedelta

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_python_key")
COLLEGE_DOMAIN = os.getenv("COLLEGE_DOMAIN", "@college.edu")

# --- Database Setup ---
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.college_chat

# --- Security Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# --- Pydantic Models ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class MessageCreate(BaseModel):
    room: str
    content: str

# --- FastAPI App ---
app = FastAPI(title="College Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Helper Functions ---
def create_jwt(user_id: str, role: str):
    payload = {
        "id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"_id": payload["id"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- REST API Routes ---

@app.post("/api/auth/register")
async def register(user: UserCreate):
    if not user.email.endswith(COLLEGE_DOMAIN):
        raise HTTPException(status_code=400, detail=f"Must use a {COLLEGE_DOMAIN} email")
    
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    user_doc = {
        "_id": user.email, # Using email as primary key for simplicity
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
        "role": "student",
        "is_approved": False
    }
    await db.users.insert_one(user_doc)
    return {"msg": "Registered successfully. Waiting for admin approval."}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not db_user["is_approved"]:
        raise HTTPException(status_code=403, detail="Account not approved by admin.")

    token = create_jwt(db_user["_id"], db_user["role"])
    return {
        "token": token,
        "user": {
            "id": db_user["_id"],
            "name": db_user["name"],
            "role": db_user["role"]
        }
    }

@app.get("/api/admin/pending")
async def get_pending_users(admin: dict = Depends(get_current_user)):
    if admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pending = await db.users.find({"is_approved": False}, {"password": 0}).to_list(100)
    return pending

@app.put("/api/admin/approve/{user_id}")
async def approve_user(user_id: str, admin: dict = Depends(get_current_user)):
    if admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    result = await db.users.update_one({"_id": user_id}, {"$set": {"is_approved": True}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"msg": "User approved"}

# --- Socket.io Server ---
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ, auth):
    token = auth.get("token") if auth else None
    if not token:
        raise ConnectionRefusedError("Authentication failed")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"_id": payload["id"]})
        if not user or not user["is_approved"]:
            raise ConnectionRefusedError("Not authorized")
        
        await sio.save_session(sid, {"user_id": user["_id"], "name": user["name"]})
        print(f"User {user['name']} connected")
    except Exception:
        raise ConnectionRefusedError("Invalid token")

@sio.event
async def join_room(sid, room):
    await sio.enter_room(sid, room)

@sio.event
async def send_message(sid, data):
    session = await sio.get_session(sid)
    message_doc = {
        "room": data["room"],
        "sender": session["user_id"],
        "name": session["name"],
        "content": data["content"],
        "timestamp": datetime.utcnow()
    }
    await db.messages.insert_one(message_doc)
    # Convert datetime to string for JSON serialization in socket emit
    message_doc["timestamp"] = message_doc["timestamp"].isoformat()
    await sio.emit("receive_message", message_doc, room=data["room"])

# Mount Socket.io to FastAPI
app.mount("/", socket_app)