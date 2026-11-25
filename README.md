# Neonova — Classical AI Document Knowledge Studio

Neonova is a free-to-run, source-grounded document assistant built with Python, Flask, deterministic lexical retrieval, knowledge-unit representation and explicit reasoning rules. The assignment build uses **no paid API, LLM, embeddings, vector database, RAG or prohibited NLP pipeline**.

## What Neonova does

- Upload multiple TXT, text-based PDF, DOCX and PPTX files.
- Extract text and retain PDF page / PPTX slide provenance.
- Build a knowledge library from sentence and line units.
- Ask broad questions such as **“What is this document about?”** and receive a whole-document overview assembled from representative source statements.
- Ask topic questions such as **“Explain PCA”** and receive a structured, plain-language answer layout based on relevant source passages.
- Ask for comparisons, lists, limitations, advantages and other focused details.
- Resolve simple follow-up references using the previous question as context.
- Inspect source passages, locations, matched terms, evidence scores and a transparent reasoning trace.
- Generate per-document briefings, browse extracted knowledge units, batch questions and export answer history to PDF, DOCX, TXT or CSV.
- Use drag-and-drop upload, responsive layouts, animated visual effects, document removal and workspace clearing.

## Assignment alignment and honest limitations

The project follows a classical-AI pipeline: document ingestion → text extraction → sentence/line knowledge-unit construction → deterministic tokenization → fixed lexical equivalence rules → weighted evidence ranking → deterministic answer composition → evidence and reasoning trace.

The overview and explanation modes are **deterministic synthesis**, not free-form language generation. They organise and introduce extracted facts using fixed rules and templates. This makes them transparent and assignment-compatible, but they cannot reliably understand every deep paraphrase, implicit relationship, diagram, scanned page or unstated fact. They are not ChatGPT or NotebookLM equivalents. Evidence-strength percentages are ranking heuristics, not calibrated probabilities or accuracy scores.

The existing domain-specific rule engine is retained for the library-guide scenarios in the assignment. It is applied only when its explicit source patterns are detected.

## Requirements

- Python 3.10+
- Internet is not required at runtime. Google Fonts are an optional visual enhancement; local system fallbacks are included.

## Run locally (Windows PowerShell)

```powershell
cd Neonova
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## Deployment notes

This is a Flask application. Deploy it to a Python web service that supports a persistent Flask/Gunicorn process. Start command:

```bash
gunicorn app:app
```

Set a strong `SECRET_KEY` environment variable. The current workspace is held in process memory for a single-process demonstration. A restart or multi-worker deployment can lose or isolate in-memory sessions. A production deployment needs a database and durable file storage without changing the classical reasoning method.

## Document extraction boundaries

- PDF must contain selectable text. Scanned/image-only PDFs are not OCR processed.
- PPTX must contain readable text in slide text boxes or tables. Text embedded only inside pictures is not extracted.
- DOCX paragraphs and tables are read; embedded images and charts are not interpreted.
- TXT is decoded as UTF-8 with replacement for malformed characters.
- Files are processed in memory and are not permanently saved to disk.

## How the engine works

1. Extract text and retain source file/page/slide provenance.
2. Split content into sentence/line knowledge units.
3. Tokenize with fixed regular expressions and remove a fixed stop-word list.
4. Expand selected terms using an inspectable, fixed synonym dictionary.
5. Rank statements using query coverage, term rarity, overlap density and source diversity.
6. For document overviews, rank representative statements using whole-document term recurrence.
7. Compose answers with intent-specific deterministic templates and extracted evidence.
8. Resolve simple follow-ups by combining the previous question with short pronoun-based follow-up questions.
9. Return evidence, source locations, heuristic evidence strength and a processing trace.

## Project structure

```text
Neonova/
├── app.py
├── src/
├── templates/index.html
├── static/style.css
├── static/script.js
├── tests/
├── documents/
├── screenshots/       # historical screenshots; regenerate for the new interface
├── requirements.txt
└── README.md
```

## Evaluation

Do not report test cases as passed until they have actually been run. Use a manually checked question set for every sample document, including answerable and unanswerable questions. The `/api/evaluate` endpoint measures expected-term lexical coverage only; it is not semantic accuracy.
