"""
Enhanced article generation module using AI to summarize research data.
Updated to output HTML format with proper Jekyll front matter and improved functionality.
"""
from transformers import pipeline
import re
import random
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleGenerator:
    """Main class for generating botanical articles using AI."""
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """Initialize the article generator with specified model."""
        self.model_name = model_name
        self.summarizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the AI summarization model."""
        try:
            logger.info(f"🤖 Loading AI model: {self.model_name}")
            self.summarizer = pipeline("summarization", model=self.model_name)
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {str(e)}")
            raise

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and format text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Fix common punctuation issues
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        return text

    def extract_section_content(self, research_data: List[Dict], section_type: str) -> str:
        """Extract content for a specific section type from research data."""
        relevant_content = []
        
        for item in research_data:
            if not isinstance(item, dict):
                continue
                
            item_type = item.get('type', '').lower()
            content = item.get('content', '')
            
            if section_type == 'all' or item_type == section_type.lower():
                if content and len(content.strip()) > 10:
                    relevant_content.append(self.clean_text(content))
        
        return ' '.join(relevant_content)

    def generate_section(self, content: str, prompt: str, max_length: int = 80, min_length: int = 50) -> str:
        """Generate a section using the summarizer with a specific prompt."""
        if not content or not content.strip():
            return ""

        try:
            # Split content into smaller chunks if it's too long
            max_chunk = 1000
            content_chunks = [content[i:i + max_chunk] for i in range(0, len(content), max_chunk)]
            summaries = []

            for chunk in content_chunks:
                chunk = chunk.strip()
                if len(chunk) < 50:  # Skip very small chunks
                    continue
                
                # Prepare input with proper formatting
                input_text = f"{prompt}: {chunk}"
                
                # Generate summary
                summary = self.summarizer(
                    input_text,
                    max_length=min(max_length, len(chunk) // 2),
                    min_length=min(min_length, len(chunk) // 4),
                    do_sample=False,
                    truncation=True
                )
                
                if summary and len(summary) > 0:
                    summary_text = self.clean_text(summary[0]['summary_text'])
                    if summary_text and len(summary_text) > 20:
                        summaries.append(summary_text)

            return ' '.join(summaries) if summaries else ""
            
        except Exception as e:
            logger.warning(f"⚠️ Error generating section: {str(e)}")
            return ""

    def create_html_paragraphs(self, text: str, section_class: str = "") -> List[str]:
        """Convert text into properly formatted HTML paragraphs."""
        if not text:
            return []
        
        # Split into sentences and group into paragraphs
        sentences = re.split(r'(?<=[.!?])\s+', text)
        paragraphs = []
        current_para = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Ensure sentence ends with punctuation
            if not re.search(r'[.!?]$', sentence):
                sentence += '.'
            
            current_para.append(sentence)
            
            # Create new paragraph every 2-3 sentences
            if len(current_para) >= random.randint(2, 3):
                para_text = ' '.join(current_para)
                class_attr = f' class="{section_class}"' if section_class else ''
                paragraphs.append(f'<p{class_attr}>{para_text}</p>')
                current_para = []
        
        # Add remaining sentences as final paragraph
        if current_para:
            para_text = ' '.join(current_para)
            class_attr = f' class="{section_class}"' if section_class else ''
            paragraphs.append(f'<p{class_attr}>{para_text}</p>')
        
        return paragraphs

    def generate_jekyll_front_matter(self, plant_name: str, title: str) -> str:
        """Generate Jekyll front matter for the article."""
        slug = re.sub(r'[^a-z0-9]+', '-', plant_name.lower()).strip('-')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        front_matter = f"""---
layout: post
title: "{title}"
date: {current_date}
categories: [south-african-plants, botanical-guide]
tags: [flora, indigenous, conservation, ecology]
plant_name: "{plant_name}"
slug: "{slug}"
featured_image: "/assets/images/plants/{slug}.jpg"
description: "Discover the remarkable {plant_name}, a unique South African plant species with fascinating adaptations and cultural significance."
author: "Botanical AI Assistant"
---

"""
        return front_matter

    def generate_title_variations(self, plant_name: str) -> List[str]:
        """Generate multiple title options for the plant article."""
        return [
            f"Discovering {plant_name}: A South African Botanical Treasure",
            f"The Remarkable {plant_name}: Indigenous Beauty of South Africa", 
            f"{plant_name}: A Journey into South African Flora",
            f"Exploring {plant_name}: Nature's Masterpiece from South Africa",
            f"{plant_name}: Where Beauty Meets Botanical Wonder",
            f"The Story of {plant_name}: A South African Native",
            f"Unveiling {plant_name}: Botanical Heritage of South Africa",
            f"{plant_name} and the Rich Tapestry of South African Flora"
        ]

    def generate_article(self, research_data: List[Dict], plant_name: str, 
                        include_front_matter: bool = True) -> str:
        """Generate a complete HTML article from research data."""
        
        if not research_data or not plant_name:
            raise ValueError("Research data and plant name are required")
        
        logger.info(f"✍️ Generating article for {plant_name}")
        
        # Extract content for different sections
        all_content = self.extract_section_content(research_data, 'all')
        
        if not all_content:
            logger.warning("No content found in research data, using fallback")
            return self._generate_fallback_article(plant_name, include_front_matter)

        # Generate sections using AI
        sections_data = {
            'introduction': {
                'content': self.generate_section(
                    all_content,
                    f"Write an engaging introduction about {plant_name}, highlighting its significance as a South African plant species"
                ),
                'fallback': f"{plant_name} stands as one of South Africa's most remarkable botanical treasures, representing the incredible diversity and resilience of the region's indigenous flora."
            },
            'characteristics': {
                'title': 'Distinctive Features',
                'content': self.generate_section(
                    all_content,
                    f"Describe the distinctive physical characteristics, unique adaptations, and identifying features of {plant_name}"
                ),
                'fallback': f"This exceptional species displays remarkable adaptations that allow it to thrive in South Africa's diverse landscapes and challenging environmental conditions."
            },
            'habitat': {
                'title': 'Natural Habitat & Ecology',
                'content': self.generate_section(
                    all_content,
                    f"Explain the natural habitat, ecological niche, and environmental requirements of {plant_name}"
                ),
                'fallback': f"{plant_name} has evolved to occupy a specific ecological niche within South Africa's complex ecosystem, playing an important role in its native environment."
            },
            'cultural': {
                'title': 'Cultural Heritage & Traditional Uses',
                'content': self.generate_section(
                    all_content,
                    f"Discuss the cultural significance, traditional uses, and historical importance of {plant_name} in South African communities"
                ),
                'fallback': f"Like many South African plants, {plant_name} holds deep cultural significance and has been valued by indigenous communities for generations."
            },
            'conservation': {
                'title': 'Conservation & Future Prospects',
                'content': self.generate_section(
                    all_content,
                    f"Address the conservation status, threats, and cultivation potential of {plant_name}"
                ),
                'fallback': f"Conservation efforts for {plant_name} are essential to preserve this valuable component of South Africa's botanical heritage for future generations."
            }
        }

        # Build HTML content
        html_sections = []
        
        # Add introduction paragraphs
        intro_content = sections_data['introduction']['content'] or sections_data['introduction']['fallback']
        html_sections.extend(self.create_html_paragraphs(intro_content, "intro"))
        
        # Add other sections with headings
        for section_key, section_info in list(sections_data.items())[1:]:  # Skip introduction
            if 'title' in section_info:
                html_sections.append(f'<h2 class="section-heading">{section_info["title"]}</h2>')
                
                section_content = section_info['content'] or section_info['fallback']
                html_sections.extend(self.create_html_paragraphs(section_content, f"section-{section_key}"))

        # Generate title and front matter
        title_options = self.generate_title_variations(plant_name)
        selected_title = random.choice(title_options)
        
        # Compile final article
        article_parts = []
        
        if include_front_matter:
            article_parts.append(self.generate_jekyll_front_matter(plant_name, selected_title))
        
        article_parts.append('\n\n'.join(html_sections))
        
        logger.info(f"✅ Article generated successfully for {plant_name}")
        return '\n'.join(article_parts)

    def _generate_fallback_article(self, plant_name: str, include_front_matter: bool = True) -> str:
        """Generate a basic fallback article when no research data is available."""
        logger.info(f"📝 Generating fallback article for {plant_name}")
        
        html_sections = [
            f'<p class="intro">{plant_name} represents one of the many remarkable plant species that contribute to South Africa\'s incredible botanical diversity.</p>',
            f'<p class="intro">As an indigenous species, {plant_name} has evolved unique adaptations that allow it to thrive in the diverse landscapes and climates found across South Africa.</p>',
            '<h2 class="section-heading">A Living Heritage</h2>',
            f'<p class="section-heritage">South Africa\'s rich botanical heritage includes thousands of species like {plant_name} that have developed fascinating strategies for survival in challenging environments.</p>',
            f'<p class="section-heritage">Each species tells a story of evolutionary adaptation, ecological relationships, and often deep cultural connections with the people who have shared this landscape for millennia.</p>',
            '<h2 class="section-heading">Conservation Importance</h2>',
            f'<p class="section-conservation">Understanding and preserving native species like {plant_name} is crucial for maintaining South Africa\'s position as one of the world\'s most biodiverse countries.</p>',
            f'<p class="section-conservation">These plants not only contribute to ecosystem health but also represent potential resources for medicine, horticulture, and sustainable development.</p>'
        ]

        title_options = self.generate_title_variations(plant_name)
        selected_title = random.choice(title_options)
        
        article_parts = []
        
        if include_front_matter:
            article_parts.append(self.generate_jekyll_front_matter(plant_name, selected_title))
        
        article_parts.append('\n\n'.join(html_sections))
        
        return '\n'.join(article_parts)

# Convenience functions for backward compatibility
def generate_article(research_data: List[Dict], plant_name: str) -> str:
    """Generate article using default settings (backward compatibility)."""
    generator = ArticleGenerator()
    return generator.generate_article(research_data, plant_name, include_front_matter=False)

def generate_plant_title(plant_name: str) -> str:
    """Generate an engaging title for the plant article (backward compatibility)."""
    generator = ArticleGenerator()
    titles = generator.generate_title_variations(plant_name)
    return random.choice(titles)