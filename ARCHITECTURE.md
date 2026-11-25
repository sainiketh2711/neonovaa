# LoreForge architecture

## Classical AI pipeline

1. **Ingestion:** Flask accepts TXT, selectable-text PDF, DOCX and PPTX uploads.
2. **Extraction:** format-specific readers extract text while retaining source file and page/slide metadata.
3. **Knowledge representation:** text is split into sentence/line knowledge units with source provenance and deterministic tokens.
4. **Question processing:** fixed regular-expression tokenization, stop-word removal, explicit alias rules and simple intent classification.
5. **Retrieval:** transparent weighted lexical scoring uses query coverage, term rarity, density, phrase matching and source diversity. Overview queries use document-wide term recurrence to select representative statements.
6. **Reasoning and synthesis:** intent-specific deterministic templates organise source statements. A small, explicit phrase glossary provides limited plain-language rewording. Simple follow-ups combine the previous question with pronoun-based follow-up text.
7. **Evidence:** answers expose source passages, page/slide locations, matched terms, heuristic evidence strength and a reasoning trace.
8. **Evaluation:** automated deterministic unit tests plus a lexical expected-term evaluation endpoint.

## Deliberate exclusions

No LLM, paid inference API, embeddings, vector database, RAG, OCR or learned NLP pipeline is included. The system is therefore explainable and reproducible, but it does not have open-ended semantic understanding or unrestricted natural-language generation. The phrase glossary is intentionally small and inspectable.

## Runtime architecture

- Flask web application and JSON API.
- Vanilla HTML/CSS/JavaScript client.
- In-memory, per-session workspace for local/single-process demonstrations.
- Export generation for PDF, DOCX, TXT and CSV.
- Gunicorn-compatible Flask entry point (`app:app`).

A production deployment requires persistent storage and a multi-worker-safe session/data layer.
