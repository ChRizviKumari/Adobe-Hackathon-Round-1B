import json
from datetime import datetime
import PyPDF2
import re
import os
import string
from typing import List, Dict, Any
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

class DocumentProcessor:
    def __init__(self):
        self.stop_words = set(stopwords.words("english"))
        self.punct_table = str.maketrans("", "", string.punctuation)

    def process_documents(self, config: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "metadata": self._create_metadata(config),
            "extracted_sections": [],
            "subsection_analysis": []
        }

        all_sections = []
        for doc in config['documents']:
            doc_path = self._get_document_path(doc['filename'])
            if not os.path.exists(doc_path):
                print(f"Warning: Document not found - {doc_path}")
                continue

            try:
                sections = self._extract_document_sections(doc_path, doc['filename'], doc['title'])
                all_sections.extend(sections)
            except Exception as e:
                print(f"Error processing {doc['filename']}: {str(e)}")

        scored_sections = self._score_sections(all_sections, config)
        top_sections = self._select_top_sections(scored_sections)

        result['extracted_sections'] = [
            {
                "document": s["document"],
                "section_title": s["title"],
                "importance_rank": i + 1,
                "page_number": s["page_num"]
            } for i, s in enumerate(top_sections)
        ]

        result['subsection_analysis'] = self._generate_subsection_analysis(top_sections)
        return result

    def _create_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "input_documents": [doc['filename'] for doc in config['documents']],
            "persona": config['persona']['role'],
            "job_to_be_done": config['job_to_be_done']['task'],
            "processing_timestamp": datetime.now().isoformat()
        }

    def _get_document_path(self, filename: str) -> str:
        for base_path in ['/app/input', 'input']:
            doc_path = os.path.join(base_path, filename)
            if os.path.exists(doc_path):
                return doc_path
        return filename

    def _extract_document_sections(self, doc_path: str, doc_name: str, doc_title: str) -> List[Dict[str, Any]]:
        sections = []
        with open(doc_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                page_sections = re.split(r'\n(?=\s*[A-Z][A-Za-z0-9 \-]+[.:]\s*\n)', text)
                for section in page_sections:
                    lines = [line.strip() for line in section.split('\n') if line.strip()]
                    if not lines:
                        continue
                    title = lines[0]
                    content = ' '.join(lines[1:]) if len(lines) > 1 else ""
                    if len(content.split()) > 30:
                        sections.append({
                            'document': doc_name,
                            'doc_title': doc_title,
                            'title': title,
                            'content': content,
                            'page_num': page_num
                        })
        return sections

    def _score_sections(self, sections: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        persona_words = set(word_tokenize(config['persona']['role'].lower()))
        job_words = set(word_tokenize(config['job_to_be_done']['task'].lower()))

        for section in sections:
            content = section['content'].lower()
            title = section['title'].lower()
            doc_title = section['doc_title'].lower()

            content_words = [w for w in word_tokenize(content.translate(self.punct_table)) if w not in self.stop_words]
            word_freq = Counter(content_words)
            common_words = set(word for word, _ in word_freq.most_common(10))

            score = 0
            score += len(set(word_tokenize(title)) & job_words) * 2
            score += len(set(content_words) & (persona_words | job_words)) * 2
            score += len(set(content_words) & common_words)
            score += len(set(word_tokenize(doc_title)) & set(content_words))  # match with doc title

            if any(term in title for term in ['abstract', 'introduction', 'conclusion', 'summary']):
                score += 3
            elif any(term in title for term in ['method', 'results', 'analysis', 'discussion']):
                score += 2

            score += int(len(content.split()) > 100)
            score += int(any(c.isdigit() for c in content))

            section['importance_rank'] = score

        return sorted(sections, key=lambda x: x['importance_rank'], reverse=True)

    def _select_top_sections(self, sections: List[Dict[str, Any]], max_sections: int = 5) -> List[Dict[str, Any]]:
        return sections[:max_sections]

    def _generate_subsection_analysis(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        analysis = []
        for section in sections:
            sentences = sent_tokenize(section['content'])
            title_keywords = set(word_tokenize(section['title'].lower())) - self.stop_words

            scored_sentences = []
            for sentence in sentences:
                if 10 <= len(word_tokenize(sentence)) <= 40:
                    lower = sentence.lower()
                    score = sum(1 for word in title_keywords if word in lower)
                    if score > 0:
                        scored_sentences.append((score, sentence))

            scored_sentences.sort(reverse=True)
            refined = " ".join([s[1] for s in scored_sentences[:3]])

            if not refined:
                refined = "This section contains meaningful content relevant to the task."

            analysis.append({
                "document": section['document'],
                "refined_text": f"Key insights: {refined.strip()}",
                "page_number": section['page_num']
            })
        return analysis

def load_config() -> Dict[str, Any]:
    config_path = '/app/challenge1b_input.json' if os.path.exists('/app/challenge1b_input.json') else 'challenge1b_input.json'
    with open(config_path) as f:
        config = json.load(f)
    required_keys = ['documents', 'persona', 'job_to_be_done']
    if not all(key in config for key in required_keys):
        raise ValueError("Invalid input JSON structure")
    return config

def save_output(result: Dict[str, Any]) -> None:
    output_dir = '/app/output' if os.path.exists('/app/output') else 'output'
    os.makedirs(output_dir, exist_ok=True)
    cleaned_sections = [
        {
            "document": s["document"],
            "section_title": s["section_title"],
            "importance_rank": s["importance_rank"],
            "page_number": s["page_number"]
        } for s in result["extracted_sections"]
    ]
    final_output = {
        "metadata": result["metadata"],
        "extracted_sections": cleaned_sections,
        "subsection_analysis": result["subsection_analysis"]
    }
    output_path = os.path.join(output_dir, 'output.json')
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=4)

def main():
    config = load_config()
    processor = DocumentProcessor()
    result = processor.process_documents(config)
    save_output(result)
    print("Processing completed successfully")

if __name__ == "__main__":
    main()
