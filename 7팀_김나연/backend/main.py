from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import SessionLocal, engine
from transformers import pipeline

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Review API", description="API for movie and review management with sentiment analysis")

print("Loading sentiment model...")
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 경량화를 위한 동적 양자화(Dynamic Quantization) 적용
print("Applying dynamic quantization to the model...")
quantized_model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)

sentiment_analyzer = pipeline("sentiment-analysis", model=quantized_model, tokenizer=tokenizer)
print("Quantized model loaded.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/movies/", response_model=schemas.Movie)
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    db_movie = models.Movie(**movie.model_dump())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@app.get("/movies/", response_model=List[schemas.Movie])
def read_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = db.query(models.Movie).offset(skip).limit(limit).all()
    return movies

@app.get("/movies/{movie_id}", response_model=schemas.Movie)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie

@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(db_movie)
    db.commit()
    return {"message": "Movie deleted successfully"}

@app.post("/reviews/", response_model=schemas.Review)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    db_movie = db.query(models.Movie).filter(models.Movie.id == review.movie_id).first()
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    try:
        result = sentiment_analyzer(review.content)[0]
        # label format: "1 star" ... "5 stars"
        stars = int(result['label'].split()[0])
        sentiment_score = float(stars)
        if stars >= 4:
            sentiment = "Positive"
        elif stars == 3:
            sentiment = "Neutral"
        else:
            sentiment = "Negative"
    except Exception as e:
        sentiment = "Unknown"
        sentiment_score = 0.0

    db_review = models.Review(
        movie_id=review.movie_id,
        author=review.author,
        content=review.content,
        sentiment_result=sentiment,
        sentiment_score=sentiment_score
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@app.get("/reviews/", response_model=List[schemas.Review])
def read_reviews(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews

@app.get("/movies/{movie_id}/reviews", response_model=List[schemas.Review])
def read_movie_reviews(movie_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(models.Review.movie_id == movie_id).all()
    return reviews

@app.get("/movies/{movie_id}/rating")
def get_movie_rating(movie_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(models.Review.movie_id == movie_id).all()
    if not reviews:
        return {"movie_id": movie_id, "rating": 0.0, "review_count": 0}
    avg_score = sum(r.sentiment_score for r in reviews) / len(reviews)
    return {"movie_id": movie_id, "rating": round(avg_score, 2), "review_count": len(reviews)}

@app.delete("/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(db_review)
    db.commit()
    return {"message": "Review deleted successfully"}
