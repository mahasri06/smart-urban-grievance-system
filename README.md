# Smart Urban Grievance Redressal and Infrastructure Monitoring System

A data-driven urban intelligence platform that collects citizen complaints, scrapes social media and news sources, classifies issues using Machine Learning (Logistic Regression), extracts exact locations using LLMs, mines patterns, and visualizes insights for municipal authorities — built as an advanced college-level Web Data Mining project.

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

---

## Project Overview

Traditional grievance systems are reactive and manual. This system transforms complaint handling into a **proactive, data-driven pipeline** by:

1. Accepting citizen complaints via a REST API
2. Scraping urban issue discussions from Reddit and Local News sites
3. Extracting exact street names and geographic coordinates from unstructured text using an **LLM Parser**
4. Classifying complaints by **category** and **urgency** using TF-IDF + Logistic Regression
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
|   +------------------+  +------------------+  +-----------------+  |
|   | LLM Location     |  | TF-IDF Vectorizer|  | Sentiment       |  |
|   | Parser (Groq API)|  | (scikit-learn)   |  | Analyzer        |  |
|   +------------------+  +------------------+  +-----------------+  |
+------------------------------+--------------------------------------+
                               |
                               v
+---------------------------------------------------------------------+
|                    CLASSIFICATION LAYER                             |
|                                                                     |
|   +---------------------------+   +------------------------------+  |
|   | Logistic Regression       |   | Logistic Regression          |  |
|   | Category Classifier       |   | Urgency Classifier           |  |
|   | (Roads, Water, Power, ...) |   | (HIGH / MEDIUM / LOW)        |  |
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
        |-- LLMParser.extract_location(description) -> coordinates
        |-- classify_text(cleaned_text)             -> (category, urgency, sentiment)
        |-- Complaint entity built
        v
  ComplaintRepository.create_complaint()            -> saved to DB

POST /scraper/run
        |
        v
  Background: scrape_and_store()
        |-- Execute Reddit & News collectors based on dynamic stems
        |-- LLMParser.extract_location(text)
        |-- process_text() + classify_text() per post
        |-- ScrapedPostRepository.upsert_bulk()  (deduplicates)
```

#### 2. NLP & ML Pipeline

1. **Preprocessing (`text_preprocessor.py`)**: 
   - Converts to lowercase.
   - Removes URLs, special characters, and digits using Regex.
   - Tokenizes and removes NLTK stopwords.
   - Applies Porter Stemmer (NLTK).
2. **TF-IDF Vectorization (`train.py`)**:
   - Uses `scikit-learn` `TfidfVectorizer` with `ngram_range=(1,2)` (unigrams and bigrams).
   - Applies sublinear TF scaling (`1 + log(tf)`).
3. **Classification**:
   - We rigorously evaluated Naive Bayes, Logistic Regression, LinearSVC, and Random Forest.
   - **Logistic Regression** achieved a perfect Macro F1-Score of 1.0000 across both Category and Urgency tasks and is the exclusive model used in production.
4. **Location Parsing**:
   - Uses the `Groq` LLM API to parse unstructured text, identifying exact localities and returning formatted JSON with latitude/longitude coordinates.

---

## Tech Stack

*   **Backend Framework:** FastAPI (Python 3.10+)
*   **Web Server:** Uvicorn
*   **Frontend / Dashboard:** Streamlit, Plotly, Folium
*   **Database:** PostgreSQL
*   **ORM:** SQLAlchemy (async ready setup)
*   **Data Science / ML:** `scikit-learn` (Logistic Regression, TF-IDF), `pandas`, `numpy`
*   **NLP:** `nltk`, TextBlob
*   **LLM Integration:** `groq` API
*   **Scraping:** `praw` (Reddit API), `beautifulsoup4` (News Scraping)
*   **Data Mining Algorithms:** `mlxtend` (Apriori for Association Rules), Custom PrefixSpan (Sequential Pattern Mining)

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
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/grievance_db
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=your_agent
GROQ_API_KEY=your_groq_key
```

### 4. Train Models & Init Database
```bash
cd src
python classification/train.py
```

## Running the Project

**1. Start the API Server:**
```bash
cd src
uvicorn main:app --reload
```
API runs at `http://localhost:8000`. Swagger docs at `/docs`.

**2. Start the Streamlit Dashboard:**
```bash
cd src
streamlit run dashboard/app.py
```
Dashboard runs at `http://localhost:8501`.

**3. Run the Data Scraper:**
You can trigger the scraper via the `/scraper/run` API endpoint, or run it manually:
```bash
cd src
python scraper/main.py
```
