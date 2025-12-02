from flask import Flask, request, jsonify
import joblib
from flask_cors import CORS
import os
import requests
from rapidfuzz import fuzz, process



# TMDB SETTINGS

TMDB_API_KEY = "b63417410a09e10708c29af76427c744"
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_TRENDING_URL = "https://api.themoviedb.org/3/trending/movie/week"
TMDB_GENRES_URL = "https://api.themoviedb.org/3/genre/movie/list"
TMDB_DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_MOVIE_DETAILS = "https://api.themoviedb.org/3/movie"
TMDB_CREDITS_URL = "https://api.themoviedb.org/3/movie/{id}/credits"
TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/w500"



# FLASK INIT

app = Flask(__name__)
CORS(app)


# LOAD LOCAL DATA
if not os.path.exists("netflix_data.pkl"):
    raise FileNotFoundError("❗ netflix_data.pkl missing")

netflix_data = joblib.load("netflix_data.pkl")

try:
    cosine_sim = joblib.load("cosine_sim.pkl")
except:
    cosine_sim = None
    print("⚠ cosine_sim.pkl missing")


# CACHES
tmdb_search_cache = {}
tmdb_details_cache = {}
poster_cache = {}
genres_cache = {"fetched": False, "genres": []}



# Fuzzy TMDB Search Function (Fix 2)
def tmdb_search_movie(title):
    key = title.lower()
    if key in tmdb_search_cache:
        return tmdb_search_cache[key]

    try:
        # 1. Direct search
        params = {"api_key": TMDB_API_KEY, "query": title}
        res = requests.get(TMDB_SEARCH_URL, params=params, timeout=6).json()
        results = res.get("results") or []

        if results:
            item = results[0]
            out = {
                "id": item.get("id"),
                "title": item.get("title"),
                "poster_path": item.get("poster_path"),
                "overview": item.get("overview"),
                "vote_average": item.get("vote_average"),
                "release_date": item.get("release_date")
            }
            tmdb_search_cache[key] = out
            return out

        # 2. Fuzzy match fallback
        discover = requests.get(
            TMDB_DISCOVER_URL,
            params={"api_key": TMDB_API_KEY, "sort_by": "popularity.desc", "page": 1},
            timeout=6
        ).json()

        movies = discover.get("results", [])
        if not movies:
            tmdb_search_cache[key] = None
            return None

        titles = [m.get("title", "") for m in movies]

        match, score, idx = process.extractOne(title, titles, scorer=fuzz.WRatio)

        if score >= 70:
            m = movies[idx]
            out = {
                "id": m.get("id"),
                "title": m.get("title"),
                "poster_path": m.get("poster_path"),
                "overview": m.get("overview"),
                "vote_average": m.get("vote_average"),
                "release_date": m.get("release_date")
            }
            tmdb_search_cache[key] = out
            return out

    except Exception as e:
        print("Fuzzy TMDB search error:", e)

    tmdb_search_cache[key] = None
    return None



# MOVIE DETAILS
def tmdb_get_details_by_id(tmdb_id):
    if tmdb_id in tmdb_details_cache:
        return tmdb_details_cache[tmdb_id]

    try:
        url = f"{TMDB_MOVIE_DETAILS}/{tmdb_id}"
        res = requests.get(url, params={"api_key": TMDB_API_KEY}).json()

        info = {
            "id": res.get("id"),
            "title": res.get("title"),
            "poster_path": res.get("poster_path"),
            "overview": res.get("overview"),
            "vote_average": res.get("vote_average"),
            "release_date": res.get("release_date"),
            "runtime": res.get("runtime"),
            "genres": [g["name"] for g in res.get("genres", [])]
        }

        tmdb_details_cache[tmdb_id] = info
        return info

    except Exception as e:
        print("TMDB details error:", e)
        return None


# CAST FUNCTION (Actors List)
def tmdb_get_cast(tmdb_id, limit=10):
    try:
        url = TMDB_CREDITS_URL.format(id=tmdb_id)
        res = requests.get(url, params={"api_key": TMDB_API_KEY}).json()
        cast = res.get("cast", [])
        return [c.get("name") for c in cast[:limit]]
    except:
        return []



# HELPERS
def poster_url_from_path(path, fallback="Movie"):
    if not path:
        return f"https://via.placeholder.com/300x450?text={fallback.replace(' ', '+')}"
    return TMDB_POSTER_BASE + path




# TRENDING MOVIES
@app.route("/trending", methods=["GET"])
def trending():
    page = int(request.args.get("page", 1))

    try:
        res = requests.get(
            TMDB_TRENDING_URL,
            params={"api_key": TMDB_API_KEY, "page": page}
        ).json()

        out = []
        for item in res.get("results", []):
            title = item.get("title", "Unknown")
            poster = poster_url_from_path(item.get("poster_path"), title)

            out.append({
                "title": title,
                "poster": poster,
                "tmdb_id": item.get("id"),
                "vote_average": item.get("vote_average"),
                "release_date": item.get("release_date")
            })

        return jsonify({
            "results": out,
            "page": res.get("page", page),
            "total_pages": res.get("total_pages", 1)
        })

    except:
        return jsonify({"results": [], "page": page, "total_pages": 1})



# GENRES
@app.route("/genres", methods=["GET"])
def get_genres():
    if genres_cache["fetched"]:
        return jsonify({"genres": genres_cache["genres"]})

    try:
        res = requests.get(TMDB_GENRES_URL, params={"api_key": TMDB_API_KEY}).json()
        genres_cache["genres"] = res.get("genres", [])
        genres_cache["fetched"] = True
        return jsonify({"genres": res.get("genres", [])})
    except:
        return jsonify({"genres": []})



# MOVIES BY GENRE
@app.route("/genre_movies", methods=["GET"])
def genre_movies():
    gid = request.args.get("genre_id")
    page = int(request.args.get("page", 1))

    if not gid:
        return jsonify({"results": []})

    try:
        res = requests.get(
            TMDB_DISCOVER_URL,
            params={"api_key": TMDB_API_KEY, "with_genres": gid, "page": page}
        ).json()

        items = []
        for m in res.get("results", []):
            title = m.get("title", "Unknown")
            poster = poster_url_from_path(m.get("poster_path"), title)

            items.append({
                "title": title,
                "poster": poster,
                "tmdb_id": m.get("id"),
                "vote_average": m.get("vote_average"),
                "release_date": m.get("release_date")
            })

        return jsonify({
            "results": items,
            "page": res.get("page", 1),
            "total_pages": res.get("total_pages", 1)
        })

    except:
        return jsonify({"results": []})



# MOVIE DETAILS ENDPOINT (with actors)
@app.route("/movie_details", methods=["GET"])
def movie_details():
    tmdb_id = request.args.get("tmdb_id")
    title = request.args.get("title")

    # Prefer ID
    if tmdb_id:
        detail = tmdb_get_details_by_id(tmdb_id)
        if detail:
            cast = tmdb_get_cast(detail["id"])
            out = format_details(detail)
            out["cast"] = cast
            return jsonify(out)

    # fallback by title
    if title:
        info = tmdb_search_movie(title)
        if info and info.get("id"):
            detail = tmdb_get_details_by_id(info["id"])
            if detail:
                cast = tmdb_get_cast(detail["id"])
                out = format_details(detail)
                out["cast"] = cast
                return jsonify(out)

    return jsonify({"error": "Not found"}), 404



def format_details(d):
    return {
        "title": d.get("title"),
        "poster": poster_url_from_path(d.get("poster_path"), d.get("title", "")),
        "overview": d.get("overview"),
        "rating": d.get("vote_average"),
        "release_date": d.get("release_date"),
        "runtime": d.get("runtime"),
        "genres": d.get("genres"),
    }



# AUTOCOMPLETE TITLES
@app.route("/titles", methods=["GET"])
def get_titles():
    return jsonify({"titles": netflix_data["Title"].astype(str).tolist()})


# RECOMMENDATION ENGINE
@app.route("/recommend", methods=["POST"])
def recommend():
    if cosine_sim is None:
        return jsonify({"error": "Missing cosine_sim.pkl"}), 500

    title = request.json.get("title", "").strip()
    if not title:
        return jsonify({"error": "Enter a title"}), 400

    df = netflix_data

    # exact match
    match = df[df["Title"].str.lower() == title.lower()]
    if match.empty:
        match = df[df["Title"].str.lower().str.contains(title.lower())]

    if match.empty:
        return jsonify({"error": "Movie not found"}), 404

    idx = match.index[0]
    sims = list(enumerate(cosine_sim[idx]))
    sims = sorted(sims, key=lambda x: x[1], reverse=True)

    top_idx = [i[0] for i in sims[1:10]]

    recs = []
    for i in top_idx:
        movie_title = df.iloc[i]["Title"]
        info = tmdb_search_movie(movie_title) or {}

        poster = poster_url_from_path(info.get("poster_path"), movie_title)

        recs.append({
            "title": movie_title,
            "poster": poster,
            "tmdb_id": info.get("id")
        })

    return jsonify({"query": title, "recommendations": recs})



# HOME
@app.route("/")
def home():
    return "VDTv API Running ✔ TMDB + Fuzzy Matching Ready 🚀"



# RUN
if __name__ == "__main__":
    app.run(debug=True, port=5001)
