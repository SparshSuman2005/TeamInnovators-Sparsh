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

@app.get("/api/stats")
def get_stats():
    from lost_found.database import SessionLocal
    from lost_found.models import Item
    db = SessionLocal()
    try:
        lost_count = db.query(Item).filter(Item.type == "lost", Item.status == "open").count()
        found_count = db.query(Item).filter(Item.type == "found", Item.status == "open").count()
        resolved_count = db.query(Item).filter(Item.status == "resolved").count()
    except Exception:
        lost_count, found_count, resolved_count = 0, 0, 0
    finally:
        db.close()

    chat_online = is_port_open(5000)
    return {
        "lost_open": lost_count,
        "found_open": found_count,
        "resolved_total": resolved_count,
        "cabs_available": 8,
        "chat_online": chat_online
    }

app.mount("/cab-assets", StaticFiles(directory="campus_cab"), name="cab-assets")
app.mount("/map-assets", StaticFiles(directory="campus_map"), name="map-assets")

from pydantic import BaseModel
class ChatQuery(BaseModel):
    question: str

@app.post("/api/chat")
def chat_ai(query: ChatQuery):
    q = query.question.strip().lower()
    if not q:
        return {"answer": "Please ask a question.", "department": "General", "sources": []}
    
    try:
        from chatbot import initialize_chatbot
        rag, config, vector_db = initialize_chatbot()
        res = rag.query(query.question)
        return {
            "answer": res.get("answer", "No answer found."),
            "department": res.get("predicted_department", "General"),
            "sources": res.get("sources", []),
            "departments": res.get("departments", [])
        }
    except Exception:
        answer = "I am the VIT Bhopal AI Campus Assistant. "
        dept = "Campus Info"
        sources = ["VIT Bhopal Campus Guide 2026"]
        
        if "hostel" in q or "room" in q or "mess" in q:
            answer = "Hostel blocks include Boys Hostels 1-6 (Mayuri, Kshipra, Narmada, Tapti, Kaveri, Godavari) and Girls Hostels (Sarojini & Kalpana). Mess serves 4 meals daily. Night canteens are available till 11 PM."
            dept = "Hostel Administration"
        elif "cab" in q or "auto" in q or "ride" in q or "travel" in q:
            answer = "Campus cabs & autos operate 24/7. Vehicles like Creta, Ertiga, Fronx, Exter, and Brezza are available. Book directly via WhatsApp through the Car Service section."
            dept = "Transport Desk"
        elif "ab1" in q or "ab2" in q or "building" in q or "class" in q or "lab" in q or "library" in q:
            answer = "Academic Block 1 (AB1) houses CS labs and 600-seat Auditorium. AB2 houses ECE & Mechanical labs. Central Library is open 8 AM to 10 PM. Check the Campus Map section for pathfinding."
            dept = "Academic Affairs"
        elif "lost" in q or "found" in q or "item" in q:
            answer = "You can report lost or found items in the Lost & Found section. Our AI TF-IDF matcher will suggest instant matches and link you with the owner/finder."
            dept = "Help Desk"
        elif "food" in q or "mayuri" in q or "bistro" in q or "canteen" in q:
            answer = "Food spots include Central Food Court, Mayuri Canteen (AB1 & AB2 sides), Under the Tree (UB), AB Dakshin, and The Bistro. Operating hours are listed on the Campus Map."
            dept = "Canteen Services"
        else:
            answer = f"Thanks for asking about '{query.question}'. For specific queries regarding admissions, exams, or fee payments, please contact the campus helpdesk at +91 96307 41753."
            
        return {"answer": answer, "department": dept, "sources": sources}

import os
import json
from datetime import datetime

class CommunityMsg(BaseModel):
    user_name: str
    text: str

@app.get("/api/community-chat")
def get_community_chat():
    path = "college_chat/chat_data.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": [], "messages": []}

@app.post("/api/community-chat")
def post_community_chat(msg: CommunityMsg):
    path = "college_chat/chat_data.json"
    data = {"users": [], "messages": []}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    
    new_msg = {
        "user_name": msg.user_name.strip() or "Student",
        "text": msg.text.strip(),
        "created_at": datetime.now().strftime("%I:%M %p")
    }
    data["messages"].append(new_msg)
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
    return {"status": "ok", "message": new_msg}

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
