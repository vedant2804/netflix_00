# VDTv — Movie Recommendation System

VDTv is a web-based movie recommendation system inspired by Netflix. It provides personalized movie suggestions using a machine learning model, along with a modern and interactive user interface.

---

## Overview

The application allows users to:

* Browse trending movies
* Explore movies by genre
* Search for specific titles
* Get personalized recommendations
* View detailed movie information (rating, cast, overview)
* Interact with a chat assistant for suggestions

---

## Tech Stack

**Frontend**

* HTML, CSS, JavaScript

**Backend**

* Python (Flask)

**Machine Learning**

* Cosine similarity-based recommendation system

**Data Source**

* TMDB API

---

## Project Structure

```id="3v1g42"
netflix_00/
│
├── app.py                # Backend (Flask API)
├── index.html            # Frontend interface
├── netflix_modeltr.ipynb # Model training notebook
├── cosine_sim.pkl        # Similarity matrix
├── netflix_data.pkl      # Processed data
├── NetflixDataset.csv    # Dataset
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```id="tq3vqa"
git clone https://github.com/vedant2804/netflix_00.git
cd netflix_00
```

### 2. Create and activate virtual environment

```id="c1w2pb"
python -m venv nvenv
source nvenv/bin/activate   # macOS/Linux
nvenv\Scripts\activate      # Windows
```

### 3. Install dependencies

```id="e9vh0i"
pip install -r requirements.txt
```

### 4. Run the backend server

```id="2r1d4o"
python app.py
```

### 5. Launch the frontend

Open `index.html` in your browser.

---

## Configuration

The backend is configured to run locally at:

```id="n4j5sm"
http://127.0.0.1:5001
```

Update this URL in `index.html` when deploying the project.

---

## Future Enhancements

* Deploy the application (frontend + backend)
* Add user authentication
* Improve recommendation model
* Add watchlist functionality
* Optimize performance and UI responsiveness

---

## Author

Vedant
Btech cse Data Science

