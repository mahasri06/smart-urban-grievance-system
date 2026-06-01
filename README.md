# Smart Urban Grievance Redressal and Infrastructure Monitoring System

A data-driven urban intelligence platform that collects citizen complaints, scrapes social media and news sources, classifies issues using NLP and Machine Learning, extracts exact locations using LLMs, mines patterns, and visualizes insights for municipal authorities.

---

## Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
  - [High-Level Design](#high-level-design)
  - [Low-Level Design](#low-level-design)
- [Classification Pipeline](#classification-pipeline)
  - [How It Works](#how-it-works)
  - [Strategy Chain](#strategy-chain)
  - [NLI Zero-Shot Classifier](#nli-zero-shot-classifier)
- [Module Breakdown](#module-breakdown)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Dashboard](#dashboard)
- [Data Mining Techniques Used](#data-mining-techniques-used)

---

## Project Overview

Traditional grievance systems are reactive and manual. This system transforms complaint handling into a **proactive, data-driven pipeline** by:

1. Accepting citizen complaints via a REST API
2. Scraping urban issue discussions from Reddit and local news sites
3. Extracting exact street names and geographic coordinates from unstructured text using an **LLM Parser**
4. Classifying complaints by **category** and **urgency** using a zero-shot NLI model (no training data required)
5. Performing **sentiment analysis** on complaint text
6. Mining **association rules** (Apriori) to find co-occurring issue types
7. Mining **sequential patterns** (PrefixSpan) to detect escalation chains
8. Visualizing everything on a **Streamlit dashboard** with charts, heatmaps, alerts, and pattern insights

---

## System Architecture

### High-Level Design

```
+---------------------------------------------------------------------+
|                        DATA SOURCES                                 |
|                                                                     |
|   +------------------+         +-----------------------------+      |
|   |  Citizen API     |         |  Scrapers (News + Reddit)   |      |
|   |  (FastAPI POST)  |         |  r/india, local news sites  |      |
|   +--------+---------+         +-------------+---------------+      |
+------------|---------------------------------|---------------------+
             |                                 |
             v                                 v
+---------------------------------------------------------------------+
|                      INGESTION LAYER                                |
|         Complaint DTO (Pydantic)  <-->  Scraped Post Mapper         |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                      NLP & LLM PROCESSING LAYER                     |
|                                                                     |
|   +------------------+  +---------------------------+  +---------+ |
|   | LLM Location     |  | NLI Zero-Shot Classifier  |  |Sentiment| |
|   | Parser (Groq API)|  | (DeBERTa-v3, no training) |  |Analyzer | |
|   +------------------+  +---------------------------+  +---------+ |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                    CLASSIFICATION LAYER                             |
|                                                                     |
|   +---------------------------+   +------------------------------+  |
|   | Category Classifier       |   | Urgency Classifier           |  |
|   | (Roads, Water, Power, ...) |   | (HIGH / MEDIUM / LOW)        |  |
|   | Strategy: NLI → TF-IDF   |   | Strategy: NLI → TF-IDF       |  |
|   |           → Keywords      |   |           → Keywords          |  |
|   +---------------------------+   +------------------------------+  |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                    DATA MINING LAYER                                |
|                                                                     |
|  +------------------+  +-------------------+                       |
|  | Association Rule |  | Sequential Pattern|                       |
|  | Mining (Apriori) |  | Mining (PrefixSpan|                       |
|  | mlxtend          |  | custom impl.)     |                       |
|  +------------------+  +-------------------+                       |
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
|              Streamlit Dashboard (4 pages)                          |
|   Overview | Heatmap | Category & Sentiment | Pattern Alerts        |
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
        |-- process_text(description)               -> cleaned text
        |-- classify_text(cleaned_text)             -> (category, urgency, sentiment)
        |-- Complaint entity built
        v
  ComplaintRepository.create_complaint()            -> saved to DB

POST /scraper/run
        |
        v
  Background: scrape_and_store()
        |-- Execute Reddit & News collectors
        |-- LLMParser.extract_location(text)
        |-- process_text() + classify_text() per post
        |-- ScrapedPostRepository.upsert_bulk()     (deduplicates)
```

#### 2. NLP & Classification Pipeline

```
Raw complaint text
        |
        v
  nlp_service.process_text()
        |-- Lowercase
        |-- Remove punctuation / special characters
        |-- Tokenize (NLTK)
        |-- Remove stopwords
        v
  Cleaned text
        |
        v
  classifier.classify_text()
        |
        |-- Strategy 1: NLI zero-shot (cross-encoder/nli-deberta-v3-small)
        |       |-- Scores text against descriptive category hypotheses
        |       |-- Scores text against urgency level hypotheses
        |       └-- Returns (category, urgency) with confidence scores
        |
        |-- Strategy 2: TF-IDF + Logistic Regression pkl (if NLI unavailable)
        |       └-- Loads pre-trained models from src/models/
        |
        └-- Strategy 3: Keyword matching (always available, no dependencies)
        |
        v
  (category, urgency, sentiment)
```

---

## Classification Pipeline

### How It Works

Every complaint — whether submitted by a citizen via the API or collected by the scraper — passes through `classify_text()` in `src/nlp/classifier.py`. This function returns a `(category, urgency, sentiment)` tuple. The rest of the system (services, scraper, dashboard) never needs to know which strategy produced the result.

### Strategy Chain

The classifier tries three strategies in order. The first one that succeeds wins:

| Priority | Strategy | When active | Accuracy |
|---|---|---|---|
| 1 | **NLI zero-shot** (`nli_classifier.py`) | `transformers` + `torch` installed | Best — generalizes to unseen phrasing |
| 2 | **TF-IDF + Logistic Regression** (`src/models/*.pkl`) | pkl files present | Good on template-like text |
| 3 | **Keyword matching** (built-in) | Always | Deterministic fallback |

If Strategy 1 fails (e.g. model not downloaded yet), it silently falls through to Strategy 2. If Strategy 2 is also unavailable, Strategy 3 always works. The API never goes down due to a missing model.

### NLI Zero-Shot Classifier

**Model:** `cross-encoder/nli-deberta-v3-small` (~180 MB)  
**File:** `src/nlp/nli_classifier.py`

Instead of training on labeled examples, this model uses **Natural Language Inference** to score how well each candidate label description *entails* the input text. No training data is required.

The key insight is using **descriptive hypothesis strings** rather than bare label names:

```python
# Instead of just "Roads & Traffic" as a label...
CATEGORY_LABELS = {
    "Roads & Traffic":       "complaint about road damage, pothole, traffic jam, or street obstruction",
    "Water & Sanitation":    "complaint about water supply, pipe leak, sewage overflow, or sanitation",
    "Electricity":           "complaint about power outage, voltage fluctuation, sparking wire, or streetlight",
    "Flooding":              "complaint about flooding, waterlogging, or stagnant water after rain",
    "Garbage & Waste":       "complaint about garbage collection, trash overflow, or illegal dumping",
    "Noise & Pollution":     "complaint about noise, air pollution, smoke, or chemical smell",
    "Public Infrastructure": "complaint about broken park equipment, bridge, public toilet, or shelter",
}

URGENCY_LABELS = {
    "HIGH":   "this is an urgent emergency requiring immediate attention, involving danger or injury",
    "MEDIUM": "this issue is moderately serious and needs attention soon but is not an emergency",
    "LOW":    "this is a minor inconvenience or low-priority complaint",
}
```

This approach generalizes to real-world noisy text (slang, typos, mixed phrasing) without any fine-tuning.

**Activating the NLI classifier:**

```bash
pip install transformers torch
```

The model downloads automatically from HuggingFace on the first classification call and caches locally at `~/.cache/huggingface/`. No scripts to run, no training required.

**Why this replaces the old TF-IDF approach:**

The previous Logistic Regression models were trained on ~60 synthetic sentence templates with minor variations (filler words, typos, synonym swaps). This caused the train/test split to contain near-duplicate sentences, producing artificially perfect F1 scores of 1.0. The models were effectively memorizing templates, not learning to generalize. The NLI model has no such limitation — it understands the semantic meaning of complaint text regardless of phrasing.

---

## Module Breakdown

| Module | Path | Responsibility |
|---|---|---|
| API Controller | `src/api/complaint_controller.py` | FastAPI routes for complaints and analytics |
| Complaint Service | `src/services/complaint_service.py` | Business logic, NLP orchestration |
| NLI Classifier | `src/nlp/nli_classifier.py` | Zero-shot classification via DeBERTa NLI |
| Classifier | `src/nlp/classifier.py` | Strategy chain: NLI → TF-IDF → keywords |
| NLP Service | `src/nlp/nlp_service.py` | Text preprocessing (tokenize, stopwords) |
| Text Preprocessor | `src/nlp/text_preprocessor.py` | Unicode normalization, stemming |
| Scraper | `src/scraper/main.py` | Reddit + News collection orchestrator |
| Filter | `src/scraper/processors/filter.py` | Relevance filtering via stemmed keywords |
| Scoring | `src/scraper/processors/scoring.py` | Severity score calculation |
| Location Parser | `src/location/llm_parser.py` | Groq LLM location extraction |
| Location Processor | `src/location/location_processor.py` | Fuzzy geocoding and normalization |
| Association Miner | `src/patterns/association_miner.py` | Apriori rule mining on complaint data |
| Sequential Miner | `src/patterns/sequential_miner.py` | PrefixSpan pattern mining |
| Dashboard | `src/dashboard/app.py` | Streamlit visualization |
| Training Script | `src/classification/train.py` | TF-IDF model training (optional) |
| Synthetic Data | `src/classification/synthetic_data.py` | Template-based data generation |

---

## Tech Stack

- **Backend Framework:** FastAPI (Python 3.10+)
- **Web Server:** Uvicorn
- **Dashboard:** Streamlit, Plotly
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **NLP / ML:** `transformers` (DeBERTa NLI), `scikit-learn` (TF-IDF fallback), `nltk`, `torch`
- **LLM Integration:** Groq API
- **Scraping:** `praw` (Reddit API), `beautifulsoup4`, `newspaper3k`
- **Data Mining:** `mlxtend` (Apriori), custom PrefixSpan implementation

---

## Project Structure

```
.
├── requirements.txt
├── .env.example
├── README.md
├── SYSTEM_DESIGN.md
├── ML_COMPARISON_REPORT.md
├── frontend/
│   └── src/
│       ├── api/
│       ├── hooks/
│       └── pages/map-view/
└── src/
    ├── main.py                         # FastAPI app entry point
    ├── api/
    │   └── complaint_controller.py
    ├── services/
    │   └── complaint_service.py
    ├── nlp/
    │   ├── classifier.py               # Strategy chain (NLI → TF-IDF → keywords)
    │   ├── nli_classifier.py           # NLI zero-shot classifier (NEW)
    │   ├── nlp_service.py              # Text preprocessing
    │   └── text_preprocessor.py
    ├── classification/
    │   ├── train.py                    # Optional TF-IDF training script
    │   ├── data_utils.py
    │   └── synthetic_data.py
    ├── models/
    │   ├── category_classifier.pkl     # TF-IDF fallback model
    │   └── urgency_classifier.pkl      # TF-IDF fallback model
    ├── scraper/
    │   ├── main.py
    │   ├── collectors/
    │   ├── normalizers/
    │   └── processors/
    ├── patterns/
    │   ├── association_miner.py
    │   └── sequential_miner.py
    ├── location/
    │   ├── llm_parser.py
    │   └── location_processor.py
    ├── dashboard/
    │   └── app.py
    ├── database/
    ├── entities/
    ├── repositories/
    ├── dto/
    └── data/
        └── real_complaints.csv
```

---

## Setup and Installation

### 1. Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- Groq API Key
- Reddit API Credentials (Client ID, Secret, User Agent)

### 2. Clone and Install

```bash
git clone https://github.com/mahasri06/smart-urban-grievance-system.git
cd smart-urban-grievance-system
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory (see `.env.example`):

```ini
DATABASE_URL=postgresql://user:password@localhost:5432/grievance_db
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=your_agent
GROQ_API_KEY=your_groq_key
```

### 4. NLI Model (recommended — no training required)

The NLI classifier activates automatically once `transformers` and `torch` are installed (both are in `requirements.txt`). The model downloads on the first classification call:

```bash
# Already included in requirements.txt — no extra step needed.
# Model (~180 MB) downloads automatically on first use.
pip install transformers torch
```

To verify the model loads correctly:

```bash
cd src
python -c "from nlp.nli_classifier import is_available; print('NLI ready:', is_available())"
```

### 5. TF-IDF Fallback Models (optional)

The old Logistic Regression models are kept as a fallback. To regenerate them:

```bash
cd src
python classification/train.py
```

This is optional — if the NLI model is available, the TF-IDF models are never used.

---

## Running the Project

### 1. Start the API Server

```bash
cd src
uvicorn main:app --reload
```

API runs at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 2. Start the Streamlit Dashboard

```bash
cd src
streamlit run dashboard/app.py
```

Dashboard runs at `http://localhost:8501`.

### 3. Run the Scraper

Trigger via the API endpoint:

```bash
curl -X POST http://localhost:8000/scraper/run
```

Or run directly:

```bash
cd src
python scraper/main.py
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/complaints` | Submit a single complaint |
| `POST` | `/complaints/bulk` | Submit complaints in bulk (async NLP) |
| `GET` | `/complaints` | List complaints with pagination |
| `GET` | `/complaints/{id}` | Get a single complaint |
| `GET` | `/analytics/complaints/by-location` | Complaint counts grouped by location |
| `GET` | `/analytics/complaints/top-locations` | Top complaint hotspots |
| `GET` | `/analytics/patterns/association` | Run Apriori association rule mining |
| `GET` | `/analytics/patterns/sequential` | Run PrefixSpan sequential mining |
| `POST` | `/analytics/credibility/score` | Trigger PageRank credibility scoring |
| `GET` | `/analytics/scraped-posts` | Fetch scraped posts with optional credibility filter |
| `POST` | `/scraper/run` | Trigger Reddit + News scraper |

Full interactive docs available at `http://localhost:8000/docs` when the server is running.

---

## Dashboard

The Streamlit dashboard has five pages:

| Page | What it shows |
|---|---|
| **Overview** | Total complaints, urgency breakdown, processing status, recent entries |
| **Location Heatmap** | Complaint volume and category distribution per location |
| **Category & Sentiment** | Issue type distribution, sentiment breakdown, urgency per category |
| **Pattern Mining** | Association rules (Apriori) and sequential patterns (PrefixSpan) with interactive controls |
| **Scraped Data** | Reddit/news posts with credibility scores and high-credibility alerts |

---

## Data Mining Techniques Used

### 1. Zero-Shot NLI Classification
Uses Natural Language Inference to classify complaint text without any labeled training data. The model (`cross-encoder/nli-deberta-v3-small`) scores entailment between the input text and descriptive label hypotheses, selecting the highest-scoring category and urgency level.

### 2. TF-IDF Information Retrieval (fallback)
Identifies the most statistically significant terms in complaint text. Used as a fallback classifier when the NLI model is unavailable.

### 3. Credibility Analysis (PageRank)
Borrows from Google's PageRank algorithm to score scraped posts by corroboration. Posts that are independently reported from multiple sources receive higher credibility scores and surface as priority alerts.

### 4. Association Rule Mining (Apriori)
Discovers co-occurring complaint categories at the same location. Example: "When Flooding complaints appear in a location, Water & Sanitation complaints follow 78% of the time." Helps authorities anticipate cascading infrastructure failures.

### 5. Sequential Pattern Mining (PrefixSpan)
Discovers temporal sequences of complaint categories per location. Example: `Flooding → Water & Sanitation → Electricity` as a recurring cascade. Implemented from scratch without external dependencies.
