"""
Article generation module using AI to summarize research data.
Updated to output HTML format with proper Jekyll front matter.
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

def generate_section(summarizer, content: str, prompt: str, max_length: int = 200) -> str:
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

def generate_article(research_data: List[Dict], plant_name: str) -> str:
    """Generate a well-structured HTML article from research data."""
    # Initialize the summarization pipeline
    print("🤖 Initializing AI summarization model...")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    # Extract all content for AI processing
    all_content = extract_section_content(research_data, 'all')
    
    print("✍️ Generating article sections with AI...")
    
    # Generate different sections using AI summarization
    introduction = generate_section(summarizer, all_content, 
                                 f"Write an engaging introduction about {plant_name}, a South African plant")
    
    characteristics = generate_section(summarizer, all_content,
                                    f"Describe the key physical characteristics and unique features of {plant_name}")
    
    habitat_ecology = generate_section(summarizer, all_content,
                                     f"Explain the natural habitat and ecological role of {plant_name}")
    
    cultural_uses = generate_section(summarizer, all_content,
                                   f"Describe the cultural significance and traditional uses of {plant_name}")
    
    conservation = generate_section(summarizer, all_content,
                                  f"Discuss conservation status and growing information for {plant_name}")
    
    # Build HTML content with proper paragraph tags
    html_sections = []
    
    # Introduction paragraphs
    if introduction:
        intro_sentences = introduction.split('. ')
        for sentence in intro_sentences:
            if sentence.strip() and len(sentence.strip()) > 20:
                sentence = sentence.strip()
                if not sentence.endswith('.'):
                    sentence += '.'
                html_sections.append(f"<p>{sentence}</p>")
    
    # Characteristics section
    if characteristics:
        html_sections.append('<h2 class="section-heading">Distinctive Features</h2>')
        char_sentences = characteristics.split('. ')
        for sentence in char_sentences:
            if sentence.strip() and len(sentence.strip()) > 20:
                sentence = sentence.strip()
                if not sentence.endswith('.'):
                    sentence += '.'
                html_sections.append(f"<p>{sentence}</p>")
    
    # Habitat and Ecology section
    if habitat_ecology:
        html_sections.append('<h2 class="section-heading">Natural Habitat & Ecology</h2>')
        habitat_sentences = habitat_ecology.split('. ')
        for sentence in habitat_sentences:
            if sentence.strip() and len(sentence.strip()) > 20:
                sentence = sentence.strip()
                if not sentence.endswith('.'):
                    sentence += '.'
                html_sections.append(f"<p>{sentence}</p>")
    
    # Cultural significance section
    if cultural_uses:
        html_sections.append('<h2 class="section-heading">Cultural Heritage</h2>')
        cultural_sentences = cultural_uses.split('. ')
        for sentence in cultural_sentences:
            if sentence.strip() and len(sentence.strip()) > 20:
                sentence = sentence.strip()
                if not sentence.endswith('.'):
                    sentence += '.'
                html_sections.append(f"<p>{sentence}</p>")
    
    # Conservation section
    if conservation:
        html_sections.append('<h2 class="section-heading">Conservation & Cultivation</h2>')
        conservation_sentences = conservation.split('. ')
        for sentence in conservation_sentences:
            if sentence.strip() and len(sentence.strip()) > 20:
                sentence = sentence.strip()
                if not sentence.endswith('.'):
                    sentence += '.'
                html_sections.append(f"<p>{sentence}</p>")
    
    # Add fallback content if no AI content was generated
    if not html_sections:
        html_sections = [
            f"<p>{plant_name} is a remarkable plant species native to South Africa, known for its unique adaptations to the diverse South African landscape.</p>",
            f"<p>This indigenous species plays an important role in its natural ecosystem and holds cultural significance for local communities.</p>",
            '<h2 class="section-heading">A Living Heritage</h2>',
            f"<p>South Africa's rich botanical heritage includes many species like {plant_name} that have evolved remarkable strategies for survival in challenging environments.</p>",
            f"<p>Understanding and preserving these native species is crucial for maintaining the country's incredible biodiversity for future generations.</p>"
        ]
    
    return '\n\n'.join(html_sections)

def generate_plant_title(plant_name: str) -> str:
    """Generate an engaging title for the plant article."""
    titles = [
        f"Discovering {plant_name}: A South African Botanical Treasure",
        f"The Remarkable {plant_name}: Indigenous Beauty of South Africa",
        f"{plant_name}: A Journey into South African Flora",
        f"Exploring {plant_name}: Nature's Masterpiece from South Africa",
        f"{plant_name}: Where Beauty Meets Botanical Wonder"
    ]
    # For now, just return the first one, but you could randomize or use AI to pick
    return titles[0]
