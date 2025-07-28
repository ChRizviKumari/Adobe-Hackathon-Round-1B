# Round 1B – Approach Explanation

## Problem Understanding

The objective of Challenge 1B is to design a generalized, offline, persona-driven document analysis engine. Given a set of PDFs, a user persona, and a task (job-to-be-done), the solution must extract the most relevant sections from each document, rank them by importance, and provide refined textual insights. The solution must be robust enough to handle a variety of document types (research papers, textbooks, financial reports) and diverse user intents, all while adhering to execution constraints.

## Methodology

### 1. Input Parsing
The solution ingests a configuration file (`challenge1b_input.json`) that defines:
- A collection of PDF files
- The persona's role (e.g., "AI researcher")
- The job to be done (e.g., "summarize trends in GNNs for drug discovery")

Each PDF is processed using `PyPDF2` to extract page-level text and segment it into sections based on formatting patterns (e.g., title-case lines, colons, and page breaks). Sections with fewer than 30 words are filtered out to remove noise.

### 2. Section Scoring
Each section is scored based on its semantic and structural alignment with:
- The persona description
- The job-to-be-done description
- The document’s title (if provided)

The scoring algorithm counts overlapping keywords, detects presence of numerals (indicating data), and boosts sections labeled with headings like “Abstract”, “Introduction”, or “Conclusion”. This ensures that even generic documents are ranked meaningfully without needing domain-specific keywords.

### 3. Ranking and Selection
The top-N sections (default: 5) with the highest scores are retained. Each is given a normalized `importance_rank`, ensuring rank 1 is most important.

### 4. Subsection Analysis
The selected sections are analyzed for key sentences using:
- Token length filters (10–40 words)
- Overlap with the section title

This helps extract core ideas from verbose academic or business content, resulting in concise “refined_text” summaries suitable for the defined persona and task.

### 5. Output Format
The results are serialized to an output JSON with three blocks:
- `metadata` (persona, task, timestamp)
- `extracted_sections` (document, section, rank)
- `subsection_analysis` (key insights)

## Design Considerations

- **Generality**: No domain-specific terms are hardcoded. The algorithm dynamically adapts based on the input persona and job.
- **Offline Execution**: All dependencies (e.g., NLTK stopwords, Punkt tokenizer) are pre-downloaded in Docker build.
- **Efficiency**: The processing pipeline completes within 60 seconds for 4–6 PDF documents (~10 pages each), as required.

## Conclusion

This solution builds a reliable and reusable pipeline that transforms static PDFs into actionable insights for any user scenario. It is modular, offline-ready, and robust to domain variations, forming the foundation for further semantic linking and interface integration in later hackathon stages.
