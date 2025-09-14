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
    
    # Generate different sections using the summarizer
    introduction = []
    characteristics = []
    benefits = []
    care_tips = []
    
    for chunk in chunks:
        if len(chunk.strip()) > 100:
            # Generate introduction
            intro_prompt = f"Summarize this as an engaging introduction about the plant: {chunk}"
            intro = summarizer(intro_prompt, max_length=200, min_length=100, do_sample=False)
            introduction.append(intro[0]['summary_text'])
            
            # Generate characteristics
            chars_prompt = f"Extract key characteristics and unique features from: {chunk}"
            chars = summarizer(chars_prompt, max_length=200, min_length=100, do_sample=False)
            characteristics.append(chars[0]['summary_text'])
            
            # Generate benefits and uses
            benefits_prompt = f"List benefits, uses, and cultural significance from: {chunk}"
            uses = summarizer(benefits_prompt, max_length=200, min_length=100, do_sample=False)
            benefits.append(uses[0]['summary_text'])
            
            # Generate care tips
            care_prompt = f"Extract growing conditions and care requirements from: {chunk}"
            care = summarizer(care_prompt, max_length=200, min_length=100, do_sample=False)
            care_tips.append(care[0]['summary_text'])
    
    # Combine all sections into a structured article
    article_sections = [
        "## Introduction",
        " ".join(introduction),
        "\n## Characteristics and Features",
        " ".join(characteristics),
        "\n## Benefits and Cultural Significance",
        " ".join(benefits),
        "\n## Growing Guide and Care Tips",
        " ".join(care_tips),
        "\n### Why You Should Consider This Plant",
        "- Unique aesthetic appeal and conversation starter",
        "- Connection to South African heritage and culture",
        "- Potential for both indoor and outdoor cultivation",
        "- Contribution to biodiversity and native plant preservation",
        "\n### Key Considerations",
        "- Climate requirements and local growing conditions",
        "- Space needs and growth patterns",
        "- Initial setup and ongoing maintenance",
        "- Seasonal care requirements",
    ]
    
    final_article = "\n\n".join(article_sections)
    
    # Add sources
    sources = "\n\n## Sources and Further Reading\n"
    for item in research_data:
        if 'url' in item:
            sources += f"- {item['source']}: {item['url']}\n"
    
    return final_article + sources