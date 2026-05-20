# Smart Urban Grievance & Infrastructure Monitoring System

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Framework](https://img.shields.io/badge/FastAPI-0.100%2B-009688)
![Database](https://img.shields.io/badge/PostgreSQL-15.0-336791)
![Architecture](https://img.shields.io/badge/Architecture-Layered-brightgreen)

## 📖 Abstract

Rapid urbanization and increasing population density have created major challenges in urban infrastructure management, including traffic congestion, flooding, water scarcity, power outages, and public grievance handling. Traditional grievance redressal systems are mostly reactive, manual, and inefficient. 

This project proposes a **Proactive, Data-Driven Urban Intelligence Platform** using Web Data Mining techniques. The system collects and analyzes data from multiple sources (social media platforms, news websites, open government datasets) to identify, classify, and prioritize civic issues in real time.

By leveraging advanced **Natural Language Processing (NLP)** and **Machine Learning** algorithms, we aim to transform traditional complaint-based governance into a smart monitoring system that improves response efficiency, resource allocation, and public trust.

---

## ✨ Key Features & Capabilities

- **Real-Time Data Ingestion:** Automated data pipelines ingesting batch payloads of unstructured grievances from social media and web platforms.
- **NLP Preprocessing Pipeline:** Intelligent text cleaning and normalization to handle noisy social media data.
- **Sentiment & Urgency Classification:** Utilizing Naive Bayes and machine learning classifiers to determine the severity of a complaint (e.g., immediate infrastructural hazard vs. general feedback).
- **Advanced Data Mining:**
  - *TF-IDF Information Retrieval*: Extracting key infrastructural entities.
  - *Association Rule Mining*: Detecting hidden relationships between different municipal issues.
  - *PageRank-based Credibility Analysis*: Filtering misinformation and spam.
  - *Sequential Pattern Mining*: Predicting cascading infrastructure failures.
- **Interactive Analytics Dashboard:** Heatmaps, alerts, and trend analysis endpoints designed to be consumed by municipal authorities.

---

## 🏗️ Technical Architecture

This project strictly adheres to a **Layered Architecture** pattern, ensuring separation of concerns, high maintainability, and testability.

```
src/
├── api/            # Controllers handling HTTP routing and request validation
├── services/       # Business logic orchestration and NLP integration
├── repositories/   # Database access layer (SQLAlchemy)
├── entities/       # Database models representing relational tables
├── dto/            # Data Transfer Objects (Pydantic) for I/O validation
├── nlp/            # NLP cleaning, classification, and scoring models
└── patterns/       # Advanced mining algorithms (TF-IDF, PageRank, etc.)
```

### Tech Stack
- **Backend Framework:** FastAPI (Asynchronous, High Performance)
- **Database:** PostgreSQL (Relational Data Storage)
- **ORM:** SQLAlchemy (with Database Migrations)
- **Data Validation:** Pydantic
- **Data Mining & NLP:** Custom Python Pipelines (Integration with scikit-learn/NLTK planned)

---

## 🚀 Upcoming Roadmap (What We Are Doing Next)

As we evolve from manual entry to full automation, our immediate engineering goals are:

1. **[COMPLETED] Batch Ingestion Pipeline:** Implement `/complaints/bulk` endpoints with bulk SQLAlchemy insertions to handle high-volume data streams from the scraper pipeline.
2. **[IN PROGRESS] Asynchronous Processing:** Offload the heavy NLP and Data Mining tasks (TF-IDF, PageRank) to background workers (e.g., Celery or FastAPI BackgroundTasks) to keep ingestion APIs responsive.
3. **[PLANNED] Predictive Analytics Integration:** Connect the sequential pattern mining algorithms to our historical database to generate predictive alerts for cascading failures.
4. **[PLANNED] Advanced Filtering & Geolocation:** Enhance our geospatial queries using PostGIS to deliver precise heatmaps for the municipal dashboard.

---

## 💻 Getting Started (Development)

### Prerequisites
- Python 3.9+
- PostgreSQL Server running locally or via Docker

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/smart-urban-grievance.git
   cd smart-urban-grievance
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Database:**
   Ensure PostgreSQL is running and update your database URL in the configuration files (or `database/database.py`).

4. **Run the FastAPI Server:**
   ```bash
   uvicorn src.main:app --reload
   ```
   The API will be accessible at `http://127.0.0.1:8000`. You can view the automated interactive API documentation at `http://127.0.0.1:8000/docs`.
