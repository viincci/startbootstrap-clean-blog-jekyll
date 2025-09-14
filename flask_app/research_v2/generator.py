"""
Article generation module using AI to summarize research data.
"""
from transformers import pipeline
import re
from typing import List, Dict

def clean_text(text: str) -> str:
    """Clean and format text content."""
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def extract_section_content(research_data: List[Dict], section_type: str) -> str:
    """Extract content for a specific section type from research data."""
    relevant_content = []
    for item in research_data:
        if item.get('type') == section_type or section_type == 'all':
            relevant_content.append(item['content'])
    return ' '.join(relevant_content)

def generate_section(summarizer, content: str, prompt: str, max_length: int = 250) -> str:
    """Generate a section using the summarizer with a specific prompt."""
    if not content:
        return ""
    
    try:
        # Split content into smaller chunks if it's too long
        max_chunk = 1000
        content_chunks = [content[i:i + max_chunk] for i in range(0, len(content), max_chunk)]
        summaries = []
        
        for chunk in content_chunks:
            if len(chunk.strip()) > 100:  # Only process substantial chunks
                summary = summarizer(f"{prompt}: {chunk}", 
                                   max_length=max_length,
                                   min_length=50,
                                   do_sample=False)
                if summary and len(summary) > 0:
                    summaries.append(summary[0]['summary_text'])
        
        return ' '.join(summaries) if summaries else ""
    except Exception as e:
        print(f"Error generating section: {str(e)}")
        return ""

def generate_article(research_data: List[Dict]) -> str:
    """Generate a well-structured article from research data."""
    # Initialize the summarization pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    # Generate different sections
    intro_content = extract_section_content(research_data, 'general_info')
    characteristics_content = extract_section_content(research_data, 'characteristics')
    benefits_content = extract_section_content(research_data, 'benefits')
    cultural_content = extract_section_content(research_data, 'cultural')
    care_content = extract_section_content(research_data, 'care_guide')
    
    # If specific sections are empty, use all content
    all_content = extract_section_content(research_data, 'all')
    if not characteristics_content:
        characteristics_content = all_content
    if not benefits_content:
        benefits_content = all_content
    if not care_content:
        care_content = all_content
    
    # Generate sections using AI
    introduction = generate_section(summarizer, intro_content, 
                                 "Write an engaging introduction about this South African plant")
    
    characteristics = generate_section(summarizer, characteristics_content,
                                    "Describe the key characteristics and unique features")
    
    benefits = generate_section(summarizer, benefits_content,
                              "Explain the benefits, uses, and cultural significance")
    
    care_guide = generate_section(summarizer, care_content,
                                "Provide growing conditions and care requirements")
    
    # Combine all sections into a structured article
    article_sections = [
        "## Introduction",
        introduction or "Information about introduction will be added soon.",
        "\n## Characteristics and Features",
        characteristics or "Information about characteristics will be added soon.",
        "\n## Benefits and Cultural Significance",
        benefits or "Information about benefits will be added soon.",
        "\n## Growing Guide and Care Tips",
        care_guide or "Information about care guidelines will be added soon.",
        "\n### Why You Should Consider This Plant",
        "- Unique aesthetic appeal and conversation starter",
        "- Connection to South African heritage and culture",
        "- Potential for both indoor and outdoor cultivation",
        "- Contribution to biodiversity and native plant preservation",
        "\n### Key Considerations",
        "- Climate requirements and local growing conditions",
        "- Space needs and growth patterns",
        "- Initial setup and ongoing maintenance",
        "- Seasonal care requirements"
    ]
    
    final_article = "\n\n".join(article_sections)
    
    # Add sources
    sources = "\n\n## Sources and Further Reading"
    for item in research_data:
        if 'url' in item and item['url'] != 'N/A':
            sources += f"\n- {item['source']}: {item['url']}"
    
    return final_article + sources