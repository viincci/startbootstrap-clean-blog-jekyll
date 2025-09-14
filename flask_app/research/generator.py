from transformers import pipeline
import re

def clean_text(text):
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def generate_article(research_data):
    # Initialize the summarization pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    # Combine all research content
    all_content = ""
    for item in research_data:
        if 'content' in item and item['content']:
            all_content += f"\n\n{item['content']}"
    
    # Clean the text
    all_content = clean_text(all_content)
    
    # Split content into chunks (BART has a max input length)
    max_chunk_length = 1024
    chunks = [all_content[i:i+max_chunk_length] for i in range(0, len(all_content), max_chunk_length)]
    
    # Summarize each chunk
    summaries = []
    for chunk in chunks:
        if len(chunk.strip()) > 100:  # Only summarize substantial chunks
            summary = summarizer(chunk, max_length=300, min_length=100, do_sample=False)
            summaries.append(summary[0]['summary_text'])
    
    # Combine summaries into final article
    final_article = " ".join(summaries)
    
    # Add sources
    sources = "\n\nSources:\n"
    for item in research_data:
        if 'url' in item:
            sources += f"- {item['source']}: {item['url']}\n"
    
    return final_article + sources