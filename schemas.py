"""
Database Schemas for Teacher Training Modules

Each Pydantic model below corresponds to a MongoDB collection. The collection
name is the lowercase of the class name.

- Module  -> "module"
- Progress -> "progress"
- Note -> "note"
"""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class Timestamp(BaseModel):
    label: str = Field(..., description="Short description for the timestamp")
    time: int = Field(..., ge=0, description="Seconds from start of video")


class Resource(BaseModel):
    label: str = Field(..., description="Display name for the resource")
    url: HttpUrl = Field(..., description="Public URL to the file (PDF, slides)")
    type: Optional[str] = Field(None, description="pdf | slides | doc | other")


class Module(BaseModel):
    title: str = Field(..., description="Module title")
    description: Optional[str] = Field(None, description="Short summary of the module")
    video_url: HttpUrl = Field(..., description="Video source URL")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail image URL")
    category: Optional[str] = Field(None, description="Tag or category")
    timestamps: List[Timestamp] = Field(default_factory=list, description="Jump points")
    resources: List[Resource] = Field(default_factory=list, description="Downloadable resources")


class Progress(BaseModel):
    user_id: str = Field(..., description="Unique user identifier (e.g., email or UUID)")
    module_id: str = Field(..., description="Associated module id (stringified ObjectId)")
    last_position: int = Field(0, ge=0, description="Last watched position in seconds")
    completed: bool = Field(False, description="Whether the module is completed")


class Note(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    module_id: str = Field(..., description="Associated module id (stringified ObjectId)")
    content: str = Field("", description="Personal notes content")
