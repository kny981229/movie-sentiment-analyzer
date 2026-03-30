from pydantic import BaseModel
from typing import List, Optional
import datetime

class ReviewBase(BaseModel):
    author: str
    content: str

class ReviewCreate(ReviewBase):
    movie_id: int

class Review(ReviewBase):
    id: int
    movie_id: int
    sentiment_result: str
    sentiment_score: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class MovieBase(BaseModel):
    title: str
    release_date: str
    director: str
    genre: str
    poster_url: str

class MovieCreate(MovieBase):
    pass

class Movie(MovieBase):
    id: int
    reviews: List[Review] = []

    class Config:
        from_attributes = True
