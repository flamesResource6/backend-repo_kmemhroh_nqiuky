import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Module, Progress, Note, Resource, Timestamp

app = FastAPI(title="Teacher Training API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IdModel(BaseModel):
    id: str


def to_str_id(doc: dict):
    if not doc:
        return doc
    d = dict(doc)
    _id = d.get("_id")
    if _id is not None:
        d["id"] = str(_id)
        del d["_id"]
    return d


@app.get("/")
def read_root():
    return {"message": "Teacher Training API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# Seed sample modules for demo
@app.post("/api/seed")
def seed_modules():
    try:
        existing = db["module"].count_documents({}) if db else 0
        if existing > 0:
            return {"status": "ok", "message": "Modules already exist", "count": existing}
        samples: List[Module] = [
            Module(
                title="Classroom Management: Routines that Work",
                description="Establishing smooth routines to reduce disruptions.",
                video_url="https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=1200&q=80&auto=format&fit=crop",
                category="Classroom",
                timestamps=[
                    Timestamp(label="Overview", time=5),
                    Timestamp(label="Entry Routine", time=20),
                    Timestamp(label="Transitions", time=40),
                ],
                resources=[
                    Resource(label="Routine Checklist (PDF)", url="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", type="pdf"),
                ],
            ),
            Module(
                title="Differentiation: Tiered Tasks",
                description="Design assignments that meet students where they are.",
                video_url="https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1509062522246-3755977927d7?w=1200&q=80&auto=format&fit=crop",
                category="Instruction",
                timestamps=[Timestamp(label="Why Tiering", time=6), Timestamp(label="Examples", time=18)],
                resources=[Resource(label="Tiered Task Templates", url="https://www.africau.edu/images/default/sample.pdf", type="pdf")],
            ),
            Module(
                title="Assessment: Quick Formative Checks",
                description="Gather real-time data to adjust instruction.",
                video_url="https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
                thumbnail_url="https://images.unsplash.com/photo-1523580846011-d3a5bc25702b?w=1200&q=80&auto=format&fit=crop",
                category="Assessment",
                timestamps=[Timestamp(label="Entry Tickets", time=8), Timestamp(label="Exit Tickets", time=16)],
                resources=[Resource(label="Formative Check Bank", url="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", type="pdf")],
            ),
        ]
        for m in samples:
            create_document("module", m)
        return {"status": "ok", "inserted": len(samples)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Modules endpoints
@app.post("/api/modules", response_model=dict)
def create_module(module: Module):
    try:
        inserted_id = create_document("module", module)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/modules", response_model=List[dict])
def list_modules(limit: Optional[int] = 50):
    try:
        docs = get_documents("module", {}, limit)
        return [to_str_id(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/modules/{module_id}", response_model=dict)
def get_module(module_id: str):
    try:
        doc = db["module"].find_one({"_id": ObjectId(module_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Module not found")
        return to_str_id(doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Progress endpoints
@app.post("/api/progress", response_model=dict)
def save_progress(progress: Progress):
    try:
        db["progress"].update_one(
            {"user_id": progress.user_id, "module_id": progress.module_id},
            {"$set": progress.model_dump()},
            upsert=True,
        )
        doc = db["progress"].find_one({"user_id": progress.user_id, "module_id": progress.module_id})
        return to_str_id(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress", response_model=dict)
def get_progress(user_id: str, module_id: str):
    try:
        doc = db["progress"].find_one({"user_id": user_id, "module_id": module_id})
        if not doc:
            return {"user_id": user_id, "module_id": module_id, "last_position": 0, "completed": False}
        return to_str_id(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Notes endpoints
@app.post("/api/notes", response_model=dict)
def save_note(note: Note):
    try:
        db["note"].update_one(
            {"user_id": note.user_id, "module_id": note.module_id},
            {"$set": note.model_dump()},
            upsert=True,
        )
        doc = db["note"].find_one({"user_id": note.user_id, "module_id": note.module_id})
        return to_str_id(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/notes", response_model=dict)
def get_note(user_id: str, module_id: str):
    try:
        doc = db["note"].find_one({"user_id": user_id, "module_id": module_id})
        if not doc:
            return {"user_id": user_id, "module_id": module_id, "content": ""}
        return to_str_id(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
