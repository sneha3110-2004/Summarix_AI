from transformers import pipeline

# Initialize the model once
summarizer = pipeline("summarization", model="t5-small")

def local_analyze(text):
    # Set chunk size to fit model's token limit (approx 1000 characters)
    chunk_size = 1000 
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    
    full_summary = []
    
    # Process every chunk to cover the entire document
    for chunk in chunks:
        if len(chunk.strip()) > 50:
            try:
                # Generate summary for the current segment
                result = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                full_summary.append(result[0]['summary_text'])
            except Exception:
                continue
                
    # Join all segments back into one comprehensive summary
    combined_text = " ".join(full_summary)
    return {"summary": combined_text}

def ask_neural_query(question, context):
    # Neural chat logic remains targeted at the most relevant text
    qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
    result = qa_pipeline(question=question, context=context)
    return result['answer']