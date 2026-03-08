from transformers import pipeline
import torch

# Global variables to store models once loaded
_summarizer = None
_qa_engine = None

def get_models():
    """Only loads models when needed to prevent 'Silent 500' errors"""
    global _summarizer, _qa_engine
    if _summarizer is None:
        print("--- Loading T5 Summarizer (First Run) ---")
        _summarizer = pipeline("summarization", model="t5-small", device=-1)
    if _qa_engine is None:
        print("--- Loading DistilBERT QA (First Run) ---")
        _qa_engine = pipeline("question-answering", model="distilbert-base-cased-distilled-squad", device=-1)
    return _summarizer, _qa_engine

def local_analyze(text):
    """Summarizes research papers for your placement preparation"""
    try:
        summarizer, _ = get_models()
        # Truncate text to 1024 to avoid memory crashes
        summary = summarizer(text[:1024], max_length=150, min_length=40, do_sample=False)[0]['summary_text']
        return {"summary": summary}
    except Exception as e:
        return {"summary": f"Neural Analysis Error: {str(e)}"}

def ask_neural_query(question, context):
    """Answers specific research methodology questions"""
    try:
        _, qa_engine = get_models()
        result = qa_engine(question=question, context=context)
        return result['answer']
    except Exception as e:
        return f"Could not extract answer: {str(e)}"