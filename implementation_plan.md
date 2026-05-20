# Simplify Backend Architecture for MVP

This plan refactors the project to align with a simple, reliable, UG-level MVP. We will remove the faux background worker and complex class-based NLP pipeline, replacing them with a straightforward synchronous approach using NLTK. We will also create a `requirements.txt` to properly track dependencies.

## User Review Required

> [!IMPORTANT]
> The heavy NLP background task will be removed. NLP processing (text cleaning, tokenization, stopwords) will run **synchronously** when a complaint is created. For an MVP, this is perfectly fine and much easier to explain. Please confirm you are okay with removing the background worker logic.

## Proposed Changes

---

### Dependencies

#### [NEW] [requirements.txt](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/requirements.txt)
Create a standard Python requirements file containing:
- fastapi
- uvicorn
- sqlalchemy
- psycopg2-binary
- pydantic
- nltk

#### [MODIFY] [download.py](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/src/download.py)
Add `nltk.download('stopwords')` to ensure all needed NLTK data is fetched.

---

### API Layer

#### [MODIFY] [complaint_controller.py](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/src/api/complaint_controller.py)
- Remove `BackgroundTasks` injection.
- Remove the call to `process_complaint_nlp`. The controller will now just call the service and return the result.

---

### Service Layer

#### [MODIFY] [complaint_service.py](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/src/services/complaint_service.py)
- Import the new simple NLP service.
- When `create_complaint` is called, process the description text *before* saving the entity, and set the `cleaned_description` immediately.
- The complaint status will start as `PROCESSED` (or just `PENDING` if you prefer to decouple the status logic, but since it's synchronous, we can just save the cleaned text immediately).

#### [DELETE] [nlp_worker.py](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/src/services/nlp_worker.py)
- Remove this file entirely. We don't need to fake a background worker.

---

### NLP Layer

#### [NEW] [nlp_service.py](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/src/nlp/nlp_service.py)
Create a simple utility file containing basic functions:
- Text lowercasing & punctuation removal.
- Tokenization using `nltk.word_tokenize`.
- Stopword removal using `nltk.corpus.stopwords`.

#### [DELETE] [pipeline.py](file:///c:/Users/admin/OneDrive/Desktop/smart_grievance_system/src/preprocessing/pipeline.py)
- Remove the complex Object-Oriented pipeline abstraction. It's over-engineered for our MVP.

---

## Verification Plan

### Automated Tests
- N/A for this step, though we will ensure the code compiles and runs.

### Manual Verification
- Install dependencies using `pip install -r requirements.txt`.
- Run the API server `uvicorn src.main:app --reload`.
- Use Swagger UI (`http://localhost:8000/docs`) to submit a POST request to `/complaints`.
- Verify that the API responds successfully and the returned JSON contains the `cleaned_description` with stopwords removed and text tokenized.
