# Smart Urban Grievance Redressal and Infrastructure Monitoring System

A data-driven urban intelligence platform that collects citizen complaints, scrapes social media, classifies issues using ML, mines patterns, and visualizes insights for municipal authorities — built as a college-level Web Data Mining project.

---

## Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
  - [High-Level Design](#high-level-design)
  - [Low-Level Design](#low-level-design)
- [Module Breakdown](#module-breakdown)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Dashboard](#dashboard)
- [Data Mining Techniques Used](#data-mining-techniques-used)
- [Current Status](#current-status)

---

## Project Overview

Traditional grievance systems are reactive and manual. This system transforms complaint handling into a **proactive, data-driven pipeline** by:

1. Accepting citizen complaints via a REST API
2. Scraping urban issue discussions from Reddit using PRAW
3. Preprocessing text using NLP (tokenization, stopword removal, cleaning)
4. Classifying complaints by **category** and **urgency** using TF-IDF + Naive Bayes
5. Performing **sentiment analysis** on complaint text
6. Mining **association rules** (Apriori) to find co-occurring issue types
7. Mining **sequential patterns** (PrefixSpan) to detect escalation chains
8. Scoring source credibility using a **PageRank-inspired** graph algorithm
9. Visualizing everything on a **Streamlit dashboard** with charts, alerts, and pattern insights

---

## System Architecture

### High-Level Design

```
+---------------------------------------------------------------------+
|                        DATA SOURCES                                 |
|                                                                     |
|   +------------------+         +-----------------------------+      |
|   |  Citizen API     |         |  Reddit Scraper (PRAW)      |      |
|   |  (FastAPI POST)  |         |  r/india, r/bangalore, etc. |      |
|   +--------+---------+         +-------------+---------------+      |
+------------|---------------------------------|---------------------+
             |                                 |
             v                                 v
+---------------------------------------------------------------------+
|                      INGESTION LAYER                                |
|         Complaint DTO (Pydantic)  <-->  Reddit Post Mapper          |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                      NLP PROCESSING LAYER                           |
|                                                                     |
|   +------------------+  +------------------+  +-----------------+  |
|   | Text Preprocessor|  | TF-IDF Vectorizer|  | Sentiment       |  |
|   | (NLTK tokenize,  |  | (scikit-learn)   |  | Analyzer        |  |
|   |  stopwords)      |  |                  |  | (lexicon-based) |  |
|   +------------------+  +------------------+  +-----------------+  |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                    CLASSIFICATION LAYER                             |
|                                                                     |
|   +---------------------------+   +------------------------------+  |
|   | Naive Bayes               |   | Urgency Classifier           |  |
|   | Category Classifier       |   | (HIGH / MEDIUM / LOW)        |  |
|   | (Roads, Water, Power, ...) |   |                              |  |
|   +---------------------------+   +------------------------------+  |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                    DATA MINING LAYER                                |
|                                                                     |
|  +------------------+  +-------------------+  +----------------+   |
|  | Association Rule |  | Sequential Pattern|  | PageRank       |   |
|  | Mining (Apriori) |  | Mining (PrefixSpan|  | Credibility    |   |
|  | mlxtend          |  | custom impl.)     |  | networkx       |   |
|  +------------------+  +-------------------+  +----------------+   |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                      PERSISTENCE LAYER                              |
|              PostgreSQL via SQLAlchemy ORM                          |
|         complaints | scraped_posts | (pattern results via API)      |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                    PRESENTATION LAYER                               |
|              Streamlit Dashboard (5 pages)                          |
|   Overview | Heatmap | Category+Sentiment | Patterns | Scraped Data |
+---------------------------------------------------------------------+
```

---

### Low-Level Design

#### 1. Data Ingestion Flow

```
POST /complaints
  ComplaintCreate (DTO: title, description, location)
        |
        v
  ComplaintService.create_complaint()
        |-- process_text(description)          -> cleaned_description
        |-- classify_text(cleaned_text)        -> (category, urgency, sentiment)
        |-- Complaint entity built
        v
  ComplaintRepository.create_complaint()      -> saved to DB

POST /complaints/bulk
  List[ComplaintCreate]
        |
        v
  ComplaintService.create_complaints_bulk()
        |-- Save all with status=PENDING_ANALYSIS (fast, synchronous)
        |-- Schedule background task with complaint IDs
        v
  Background: _process_nlp_background(ids)
        |-- process_text() + classify_text() per complaint
        |-- Update DB, set status=PROCESSED

POST /scraper/run
        |
        v
  Background: scrape_and_store()
        |-- praw.Reddit.subreddit(name).search(keyword)
        |-- extract_location(text)
        |-- process_text() + classify_text() per post
        |-- ScrapedPostRepository.upsert_bulk()  (deduplicates by source_id)
```

#### 2. NLP Pipeline

```
process_text(raw_text: str) -> cleaned_text: str
  1. lowercase
  2. regex remove punctuation/special chars
  3. nltk.word_tokenize()
  4. remove stopwords (nltk.corpus.stopwords)
  5. rejoin tokens

classify_text(text: str) -> (category, urgency, sentiment)
  category  <- category_classifier.pkl (TF-IDF + MultinomialNB)
               fallback: keyword matching if model not trained
  urgency   <- urgency_classifier.pkl  (TF-IDF + MultinomialNB)
               fallback: keyword matching
  sentiment <- lexicon-based (negative/positive word sets)
               returns NEGATIVE / NEUTRAL / POSITIVE
```

#### 3. Classification Models

```
Training (run once: python classification/train.py)
  Input:  src/data/synthetic_complaints.csv  (text, category, urgency)
  
  Pipeline per model:
    TfidfVectorizer(ngram_range=(1,2), max_features=1000, sublinear_tf=True)
      -> MultinomialNB(alpha=0.5)
  
  Output:
    src/models/category_classifier.pkl
    src/models/urgency_classifier.pkl

Categories: Roads & Traffic | Water & Sanitation | Electricity |
            Garbage & Waste | Flooding | Public Infrastructure |
            Noise & Pollution | General

Urgency:    HIGH | MEDIUM | LOW
```

#### 4. Data Mining

```
Association Rule Mining (src/patterns/association_miner.py)
  Input:  complaints + scraped_posts grouped by location
  Step 1: Build transactions — each location = set of categories reported there
  Step 2: TransactionEncoder -> binary matrix
  Step 3: apriori(min_support) -> frequent itemsets
  Step 4: association_rules(min_confidence) -> rules
  Output: antecedents, consequents, support, confidence, lift
  Example: "Flooding -> Water & Sanitation" (conf=0.78, lift=2.1)

Sequential Pattern Mining (src/patterns/sequential_miner.py)
  Input:  complaints ordered by ID per location
  Step 1: Build sequences — each location = ordered list of categories
  Step 2: PrefixSpan algorithm (custom implementation, no extra dependency)
  Output: frequent subsequences with support count
  Example: ["Flooding", "Water & Sanitation", "Electricity"] support=3

PageRank Credibility (src/credibility/pagerank_scorer.py)
  Input:  all scraped posts
  Step 1: Build graph — nodes=posts, edges between posts sharing category+location
  Step 2: Edge weight = 1 / (1 + |engagement_i - engagement_j|)
  Step 3: Personalisation vector = normalised engagement per post
  Step 4: nx.pagerank(G, alpha=0.85, personalization=...)
  Step 5: Min-max normalise scores to [0, 1]
  Output: credibility_score per post stored in DB
```

#### 5. Database Schema

```
complaints
  id                  INTEGER  PK
  title               VARCHAR
  description         VARCHAR
  cleaned_description VARCHAR
  location            VARCHAR
  category            VARCHAR   (Roads & Traffic | Water & Sanitation | ...)
  urgency             VARCHAR   (HIGH | MEDIUM | LOW)
  sentiment           VARCHAR   (POSITIVE | NEUTRAL | NEGATIVE)
  status              VARCHAR   (PENDING_ANALYSIS | PROCESSED)

scraped_posts
  id                  INTEGER  PK
  source              VARCHAR   (reddit)
  source_id           VARCHAR   UNIQUE  (Reddit post ID, prevents duplicates)
  subreddit           VARCHAR
  title               VARCHAR
  body                TEXT
  url                 VARCHAR
  location            VARCHAR
  upvotes             INTEGER
  num_comments        INTEGER
  author              VARCHAR
  cleaned_text        VARCHAR
  category            VARCHAR
  urgency             VARCHAR
  sentiment           VARCHAR
  credibility_score   FLOAT     (0.0 - 1.0, set by PageRank scorer)
  scraped_at          TIMESTAMP
```

#### 6. Streamlit Dashboard Pages

```
Page 1: Overview
  - KPI metrics: total complaints, high urgency count, locations, categories
  - Urgency breakdown pie chart
  - Processing status bar chart
  - Recent complaints table

Page 2: Location Heatmap
  - Complaints per location (bar chart, colour-scaled)
  - Top 5 hotspot locations
  - Category distribution per location (stacked bar)
  - Urgency by location (grouped bar)

Page 3: Category & Sentiment
  - Category distribution pie chart
  - Sentiment distribution pie chart
  - Sentiment breakdown per category (stacked bar)
  - Urgency breakdown per category (grouped bar)

Page 4: Pattern Mining
  - Association rules: interactive sliders for support/confidence/lift
  - Rules table + top rules bar chart
  - Sequential patterns: support slider + pattern list

Page 5: Scraped Data
  - KPI metrics: posts, subreddits, locations, scored posts
  - Run PageRank scoring button
  - High credibility alerts (score >= 0.6) with expandable details
  - Credibility score histogram
  - Category + subreddit breakdown charts
  - Full posts table
```

---

## Module Breakdown

| Module | Path | Purpose |
|---|---|---|
| API Layer | `src/api/` | FastAPI routes for complaints and analytics |
| Service Layer | `src/services/` | Business logic, orchestrates NLP + DB |
| NLP | `src/nlp/` | Text cleaning, classification, sentiment |
| Classification | `src/classification/` | Model training script (TF-IDF + Naive Bayes) |
| Scraper | `src/scraper/` | Reddit scraper using PRAW |
| Pattern Mining | `src/patterns/` | Association rules + sequential patterns |
| Credibility | `src/credibility/` | PageRank-based post scoring |
| Entities | `src/entities/` | SQLAlchemy ORM models |
| Repositories | `src/repositories/` | DB query layer |
| DTOs | `src/dto/` | Pydantic request/response schemas |
| Database | `src/database/` | DB connection + session management |
| Dashboard | `src/dashboard/` | Streamlit multi-page app |
| Data | `src/data/` | Synthetic training dataset (CSV) |
| Models | `src/models/` | Saved trained model files (generated) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| NLP | NLTK (tokenization, stopwords) |
| ML / Classification | scikit-learn (TF-IDF, Multinomial Naive Bayes) |
| Association Mining | mlxtend (Apriori algorithm) |
| Sequential Mining | Custom PrefixSpan implementation |
| Graph / PageRank | networkx |
| Web Scraping | PRAW (Reddit API) |
| Dashboard | Streamlit + Plotly |
| Config | python-dotenv |

---

## Project Structure

```
smart_grievance_system/
|
+-- .env.example                         # Environment variable template
+-- .env                                 # Your local config (not committed)
+-- requirements.txt
+-- README.md
+-- implementation_plan.md
|
+-- src/
    +-- main.py                          # FastAPI app entry point
    +-- download.py                      # NLTK data downloader
    +-- alter_db.py                      # DB migration utility
    +-- drop_db.py                       # DB reset utility
    |
    +-- api/
    |   +-- complaint_controller.py      # Complaint REST endpoints
    |
    +-- services/
    |   +-- complaint_service.py         # Business logic + background NLP
    |
    +-- nlp/
    |   +-- nlp_service.py               # Text preprocessing
    |   +-- classifier.py                # classify_text() — ML or keyword fallback
    |   +-- text_preprocessor.py         # TextPreprocessor class (legacy)
    |
    +-- classification/
    |   +-- __init__.py
    |   +-- train.py                     # Train Naive Bayes models
    |
    +-- scraper/
    |   +-- __init__.py
    |   +-- reddit.py                    # Reddit PRAW scraper
    |
    +-- patterns/
    |   +-- __init__.py
    |   +-- association_miner.py         # Apriori association rules
    |   +-- sequential_miner.py          # PrefixSpan sequential patterns
    |
    +-- credibility/
    |   +-- __init__.py
    |   +-- pagerank_scorer.py           # PageRank credibility scoring
    |
    +-- entities/
    |   +-- complaint_entity.py          # Complaint ORM model
    |   +-- scraped_post_entity.py       # ScrapedPost ORM model
    |
    +-- repositories/
    |   +-- complaint_repository.py      # Complaint DB queries
    |   +-- scraped_post_repository.py   # ScrapedPost DB queries
    |
    +-- dto/
    |   +-- complaint_dto.py             # Pydantic schemas
    |
    +-- database/
    |   +-- database.py                  # DB engine + session
    |   +-- dependencies.py             # FastAPI DB dependency
    |
    +-- data/
    |   +-- synthetic_complaints.csv     # Training data (115 labeled samples)
    |
    +-- models/                          # Generated after running train.py
    |   +-- category_classifier.pkl
    |   +-- urgency_classifier.pkl
    |
    +-- dashboard/
        +-- __init__.py
        +-- app.py                       # Streamlit dashboard (5 pages)
```

---

## Setup and Installation

### Prerequisites

- Python 3.10+
- PostgreSQL running locally

### 1. Clone the repository

```bash
git clone <repo-url>
cd smart_grievance_system
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download NLTK data

```bash
python src/download.py
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/smart_grievance_db
```

### 6. Create the database

```sql
CREATE DATABASE smart_grievance_db;
```

### 7. Train the Naive Bayes models

```bash
cd src
python classification/train.py
```

This reads `src/data/synthetic_complaints.csv`, trains two models, and saves them to `src/models/`.

---

## Running the Project

### Start the API server

```bash
cd src
uvicorn main:app --reload
```

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### Start the Streamlit dashboard

```bash
cd src
streamlit run dashboard/app.py
```

- Dashboard: `http://localhost:8501`

### Run the Reddit scraper manually

```bash
cd src
python scraper/reddit.py
```

Or trigger it via the API:

```bash
curl -X POST http://localhost:8000/scraper/run
```

---

## API Reference

### Complaints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/complaints` | Submit a single complaint (synchronous NLP) |
| `POST` | `/complaints/bulk` | Submit multiple complaints (background NLP) |
| `GET` | `/complaints` | List complaints (paginated, filterable) |
| `GET` | `/complaints/{id}` | Get a single complaint by ID |

**POST /complaints — Request Body**
```json
{
  "title": "Flooded road near market",
  "description": "The main road near the central market has been flooded for 3 days. Vehicles cannot pass.",
  "location": "Koramangala"
}
```

**Response**
```json
{
  "id": 1,
  "title": "Flooded road near market",
  "description": "The main road near the central market has been flooded for 3 days.",
  "cleaned_description": "flooded road near central market 3 days vehicles cannot pass",
  "location": "Koramangala",
  "category": "Flooding",
  "urgency": "HIGH",
  "sentiment": "NEGATIVE",
  "status": "PROCESSED"
}
```

**GET /complaints query params**

| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `size` | int | 10 | Results per page |
| `sort` | string | latest | `latest` or `oldest` |
| `location` | string | - | Filter by location (partial match) |
| `title` | string | - | Filter by title (partial match) |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/complaints/by-location` | Complaint count grouped by location |
| `GET` | `/analytics/complaints/top-locations?limit=5` | Top N locations by volume |
| `GET` | `/analytics/patterns/association` | Run association rule mining |
| `GET` | `/analytics/patterns/sequential` | Run sequential pattern mining |
| `POST` | `/analytics/credibility/score` | Trigger PageRank scoring (background) |
| `GET` | `/analytics/scraped-posts` | List scraped posts with credibility scores |

### Scraper

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scraper/run` | Trigger Reddit scraper (background task) |

---

## Dashboard

The Streamlit dashboard has 5 pages accessible from the sidebar:

| Page | What it shows |
|---|---|
| **Overview** | Total complaints, urgency pie chart, status breakdown, recent complaints table |
| **Location Heatmap** | Complaints per location bar chart, top hotspots, category + urgency by location |
| **Category & Sentiment** | Category pie, sentiment pie, sentiment per category, urgency per category |
| **Pattern Mining** | Association rules with interactive sliders + chart, sequential patterns list |
| **Scraped Data** | Reddit posts table, PageRank scoring button, high-credibility alerts, score histogram |

---

## Data Mining Techniques Used

| Technique | Implementation | Purpose |
|---|---|---|
| **TF-IDF** | `TfidfVectorizer` (scikit-learn) | Convert complaint text to feature vectors |
| **Naive Bayes** | `MultinomialNB` (scikit-learn) | Classify complaint category and urgency |
| **Sentiment Analysis** | Lexicon-based (custom word sets) | Score complaint sentiment |
| **Association Rule Mining** | Apriori (mlxtend) | Find co-occurring issue types per location |
| **Sequential Pattern Mining** | PrefixSpan (custom implementation) | Detect temporal complaint escalation chains |
| **PageRank Credibility** | `nx.pagerank` (networkx) | Score Reddit post credibility via engagement graph |
| **Web Scraping** | PRAW (Reddit API) | Collect urban issue discussions from subreddits |

---

## Current Status

| Module | Status |
|---|---|
| FastAPI CRUD (single + bulk) | Complete |
| Background NLP processing | Complete |
| Basic NLP preprocessing (NLTK) | Complete |
| TF-IDF vectorization | Complete |
| Naive Bayes classifier (trained) | Complete |
| Keyword fallback classifier | Complete |
| Sentiment analysis (lexicon-based) | Complete |
| Synthetic training dataset (115 samples) | Complete |
| Reddit scraper (PRAW) | Complete |
| ScrapedPost entity + repository | Complete |
| Association rule mining (Apriori) | Complete |
| Sequential pattern mining (PrefixSpan) | Complete |
| PageRank credibility scoring | Complete |
| Streamlit dashboard (5 pages) | Complete |
| Pattern mining API endpoints | Complete |
| Scraper trigger API endpoint | Complete |
| Environment variable config (.env) | Complete |
