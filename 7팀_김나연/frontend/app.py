import streamlit as st
import requests
import pandas as pd

import os
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Movie Reviews & Sentiment", layout="wide")
st.title("🎬 영화 리뷰 및 감성 분석 서비스")
st.markdown("스트림릿과 FastAPI를 활용한 영화 평점 및 리뷰 감성 분석 웹서비스입니다.")

menu = ["영화 목록", "영화 추가", "리뷰 작성", "최근 리뷰 보기"]
choice = st.sidebar.selectbox("메뉴", menu)

if choice == "영화 목록":
    st.subheader("영화 목록")
    try:
        response = requests.get(f"{API_URL}/movies/")
        if response.status_code == 200:
            movies = response.json()
            if not movies:
                st.info("등록된 영화가 없습니다.")
            else:
                for m in movies:
                    rating_resp = requests.get(f"{API_URL}/movies/{m['id']}/rating").json()
                    avg_rating = rating_resp.get("rating", 0.0)
                    count = rating_resp.get("review_count", 0)
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        try:
                            if m['poster_url']:
                                st.image(m['poster_url'], use_container_width=True)
                        except Exception:
                            st.markdown("이미지를 불러올 수 없습니다.")
                    with col2:
                        st.write(f"### {m['title']}")
                        st.write(f"⭐ **평점:** {avg_rating:.1f}/5.0 (리뷰 {count}개)")
                        st.write(f"📅 **개봉일:** {m['release_date']}")
                        st.write(f"🎬 **감독:** {m['director']}")
                        st.write(f"🎭 **장르:** {m['genre']}")
                    st.markdown("---")
        else:
            st.error("영화 목록을 불러오는 데 실패했습니다 (API 오류).")
    except Exception as e:
        st.error(f"백엔드 서버({API_URL})에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")

elif choice == "영화 추가":
    st.subheader("새 영화 추가하기")
    title = st.text_input("제목")
    release_date = st.text_input("개봉일 (예: 2024-01-01)")
    director = st.text_input("감독")
    genre = st.text_input("장르")
    poster_url = st.text_input("포스터 이미지 URL")
    
    if st.button("추가하기"):
        if title:
            payload = {
                "title": title,
                "release_date": release_date,
                "director": director,
                "genre": genre,
                "poster_url": poster_url
            }
            try:
                res = requests.post(f"{API_URL}/movies/", json=payload)
                if res.status_code == 200:
                    st.success("영화가 성공적으로 추가되었습니다!")
                else:
                    st.error("영화 추가 중 오류가 발생했습니다.")
            except:
                st.error(f"백엔드 서버({API_URL})에 연결할 수 없습니다.")
        else:
            st.warning("제목을 입력해주세요.")

elif choice == "리뷰 작성":
    st.subheader("리뷰 작성하기 (자동 감성 분석)")
    try:
        movies_res = requests.get(f"{API_URL}/movies/")
        if movies_res.status_code == 200:
            movies = movies_res.json()
            if not movies:
                st.warning("먼저 영화를 추가해주세요!")
            else:
                movie_options = {m['title']: m['id'] for m in movies}
                selected_movie_title = st.selectbox("영화 선택", list(movie_options.keys()))
                author = st.text_input("작성자 이름")
                content = st.text_area("리뷰 내용", help="리뷰를 작성하시면 AI가 감성을 분석하여 Positive/Neutral/Negative 로 분류합니다.")
                
                if st.button("리뷰 등록 및 감성 분석"):
                    if author and content:
                        payload = {
                            "movie_id": movie_options[selected_movie_title],
                            "author": author,
                            "content": content
                        }
                        with st.spinner("감성 분석 진행 중..."):
                            res = requests.post(f"{API_URL}/reviews/", json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            sentiment = data['sentiment_result']
                            score = data['sentiment_score']
                            emoji = "😊" if sentiment == "Positive" else "😐" if sentiment == "Neutral" else "😠"
                            st.success(f"리뷰가 등록되었습니다!")
                            st.info(f"🤖 AI 분석 결과: **{sentiment}** {emoji} (점수: {score}/5.0)")
                        else:
                            st.error("리뷰 등록 실패")
                    else:
                        st.warning("작성자와 내용을 모두 입력해주세요.")
    except:
        st.error(f"백엔드 서버({API_URL})에 연결할 수 없습니다.")

elif choice == "최근 리뷰 보기":
    st.subheader("최근 등록된 리뷰 목록 (30개)")
    try:
        response = requests.get(f"{API_URL}/reviews/?limit=30")
        if response.status_code == 200:
            reviews = response.json()
            if not reviews:
                st.info("작성된 리뷰가 없습니다.")
            else:
                movies_dict = {}
                m_res = requests.get(f"{API_URL}/movies/")
                if m_res.status_code == 200:
                    movies_dict = {m['id']: m['title'] for m in m_res.json()}

                df_data = []
                for r in reviews:
                    df_data.append({
                        "영화": movies_dict.get(r['movie_id'], str(r['movie_id'])),
                        "작성자": r['author'],
                        "리뷰 내용": r['content'],
                        "감성": r['sentiment_result'],
                        "AI 점수": r['sentiment_score'],
                        "등록일": r['created_at'].split("T")[0]
                    })
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
    except:
        st.error(f"백엔드 서버({API_URL})에 연결할 수 없습니다.")
