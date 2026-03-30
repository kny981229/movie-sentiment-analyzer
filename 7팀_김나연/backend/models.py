from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    release_date = Column(String)
    director = Column(String)
    genre = Column(String)
    poster_url = Column(String)

    reviews = relationship("Review", back_populates="movie", cascade="all, delete")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    author = Column(String)
    content = Column(String)
    sentiment_result = Column(String)
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    movie = relationship("Movie", back_populates="reviews")
