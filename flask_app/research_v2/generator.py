"""
Enhanced article generation module using AI to summarize research data.
Updated to output HTML format with proper Jekyll front matter and NO DUPLICATE content.
"""
from transformers import pipeline
import re
import random
from typing import List, Dict, Optional, Set
from datetime import datetime
import logging
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleGenerator:
    """Main class for generating botanical articles using AI."""

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """Initialize the article generator with specified model."""
        self.model_name = model_name
        self.summarizer = None
        self.used_content_hashes = set()  # Track used content globally
        self._load_model()

    def _load_model(self):
        """Load the AI summarization model."""
        try:
            logger.info(f"Loading AI model: {self.model_name}")
            self.summarizer = pipeline("summarization", model=self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def _hash_content(self, content: str) -> str:
        """Generate a hash for content to detect duplicates."""
        return hashlib.md5(content.encode()).hexdigest()

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

        # Remove very short sentences that don't add value
        sentences = text.split('.')
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return '. '.join(meaningful_sentences)

    def extract_section_content(self, research_data: List[Dict], section_type: str, max_items: int = 2) -> str:
        """Extract content for a specific section type from research data with deduplication."""
        relevant_content = []
        local_used_hashes = set()

        for item in research_data:
            if not isinstance(item, dict):
                continue

            content = item.get('content', '').strip()
            if not content or len(content) < 30:  # Minimum content length
                continue
                
            # Generate content hash for deduplication
            content_hash = self._hash_content(content)
            
            # Skip if we've already used this content globally or locally
            if content_hash in self.used_content_hashes or content_hash in local_used_hashes:
                continue
            
            item_type = item.get('type', '').lower()
            content_lower = content.lower()
            
            # Section-specific content filtering
            if section_type == 'characteristics':
                keywords = ['appearance', 'features', 'characteristics', 'looks', 'size', 'color', 'shape', 'form', 'structure']
                if any(keyword in content_lower for keyword in keywords) or item_type == 'characteristics':
                    relevant_content.append(self.clean_text(content))
                    local_used_hashes.add(content_hash)
                    self.used_content_hashes.add(content_hash)
                    
            elif section_type == 'habitat':
                keywords = ['habitat', 'grows', 'environment', 'climate', 'soil', 'native', 'distribution', 'range']
                if any(keyword in content_lower for keyword in keywords) or item_type == 'habitat':
                    relevant_content.append(self.clean_text(content))
                    local_used_hashes.add(content_hash)
                    self.used_content_hashes.add(content_hash)
                    
            elif section_type == 'cultural':
                keywords = ['traditional', 'cultural', 'uses', 'medicine', 'history', 'indigenous', 'ceremony', 'healing']
                if any(keyword in content_lower for keyword in keywords) or item_type == 'cultural':
                    relevant_content.append(self.clean_text(content))
                    local_used_hashes.add(content_hash)
                    self.used_content_hashes.add(content_hash)
                    
            elif section_type == 'conservation':
                keywords = ['conservation', 'threat', 'endangered', 'protect', 'status', 'vulnerable', 'extinct']
                if any(keyword in content_lower for keyword in keywords) or item_type == 'conservation':
                    relevant_content.append(self.clean_text(content))
                    local_used_hashes.add(content_hash)
                    self.used_content_hashes.add(content_hash)
                    
            elif section_type == 'general' and len(relevant_content) < max_items:
                # Only use if we haven't found enough content yet
                relevant_content.append(self.clean_text(content))
                local_used_hashes.add(content_hash)
                self.used_content_hashes.add(content_hash)

            # Stop once we have enough content for this section
            if len(relevant_content) >= max_items:
                break

        # Return joined content, limited to reasonable length
        combined_content = ' '.join(relevant_content)
        if len(combined_content) > 1500:  # Limit content length
            combined_content = combined_content[:1500] + "..."
        
        return combined_content

    def generate_section(self, content: str, prompt: str, max_length: int = 100, min_length: int = 30) -> str:
        """Generate a section using the summarizer with a specific prompt."""
        if not content or not content.strip() or len(content.strip()) < 20:
            return ""

        try:
            # Clean and prepare content
            content = content.strip()
            
            # Split content into manageable chunks if too long
            max_chunk = 800  # Reduced chunk size for better processing
            if len(content) > max_chunk:
                content = content[:max_chunk]

            # Prepare input with clear context
            input_text = f"{prompt}. Based on this information: {content}"
            
            # Adjust length parameters based on content
            adjusted_max = min(max_length, max(min_length, len(content) // 8))
            adjusted_min = min(min_length, adjusted_max // 2)

            # Generate summary
            summary = self.summarizer(
                input_text,
                max_length=adjusted_max,
                min_length=adjusted_min,
                do_sample=False,
                truncation=True
            )

            if summary and len(summary) > 0:
                summary_text = self.clean_text(summary[0]['summary_text'])
                
                # Ensure the summary is meaningful and not too repetitive
                if summary_text and len(summary_text) > 15:
                    return summary_text

        except Exception as e:
            logger.warning(f"Error generating section: {str(e)}")

        return ""

    def create_html_paragraphs(self, text: str, section_class: str = "") -> List[str]:
        """Convert text into properly formatted HTML paragraphs with deduplication."""
        if not text or not text.strip():
            return []

        # Clean the text first
        text = self.clean_text(text)
        
        # Split into sentences more carefully
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        paragraphs = []
        current_para = []
        used_sentences = set()

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            # Check for duplicate sentences
            sentence_hash = self._hash_content(sentence)
            if sentence_hash in used_sentences:
                continue
            used_sentences.add(sentence_hash)

            # Ensure sentence ends with punctuation
            if not re.search(r'[.!?]$', sentence):
                sentence += '.'

            current_para.append(sentence)

            # Create new paragraph every 2-4 sentences
            if len(current_para) >= random.randint(2, 4):
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
        """Generate a complete HTML article from research data with no duplicates."""

        if not research_data or not plant_name:
            raise ValueError("Research data and plant name are required")

        logger.info(f"Generating article for {plant_name}")

        # Reset used content tracking for this article
        self.used_content_hashes = set()

        # Extract DIFFERENT content for each section to prevent duplication
        sections_data = {}
        
        # Introduction - use general content first
        intro_content = self.extract_section_content(research_data, 'general', max_items=1)
        sections_data['introduction'] = {
            'content': self.generate_section(
                intro_content,
                f"Write a compelling introduction about {plant_name} highlighting its significance as a South African plant species",
                max_length=80, min_length=40
            ),
            'fallback': f"{plant_name} stands as a distinctive representative of South Africa's remarkable botanical heritage, showcasing the unique adaptations that make this region's flora so extraordinary."
        }

        # Characteristics - look for specific characteristic content
        char_content = self.extract_section_content(research_data, 'characteristics', max_items=2)
        sections_data['characteristics'] = {
            'title': 'Distinctive Features',
            'content': self.generate_section(
                char_content,
                f"Describe the unique physical characteristics and distinctive features of {plant_name}",
                max_length=100, min_length=50
            ),
            'fallback': f"This remarkable species displays unique morphological adaptations that distinguish it from other plants in its family, with specialized features that reflect its evolutionary journey in South African landscapes."
        }

        # Habitat - look for habitat-specific content
        habitat_content = self.extract_section_content(research_data, 'habitat', max_items=2)
        sections_data['habitat'] = {
            'title': 'Natural Habitat & Ecology',
            'content': self.generate_section(
                habitat_content,
                f"Explain the natural habitat, growing conditions, and ecological role of {plant_name}",
                max_length=100, min_length=50
            ),
            'fallback': f"The natural distribution of {plant_name} reflects South Africa's diverse ecosystems, where it has evolved to occupy a specific ecological niche that supports both its survival and its role in the broader environmental web."
        }

        # Cultural significance - look for cultural/traditional content
        cultural_content = self.extract_section_content(research_data, 'cultural', max_items=2)
        sections_data['cultural'] = {
            'title': 'Cultural Heritage & Traditional Uses',
            'content': self.generate_section(
                cultural_content,
                f"Discuss the cultural significance and traditional applications of {plant_name} in South African communities",
                max_length=100, min_length=50
            ),
            'fallback': f"Like many indigenous South African plants, {plant_name} carries deep cultural significance, representing the intricate relationship between local communities and their natural environment across generations."
        }

        # Conservation - look for conservation content
        conservation_content = self.extract_section_content(research_data, 'conservation', max_items=2)
        sections_data['conservation'] = {
            'title': 'Conservation & Future Prospects',
            'content': self.generate_section(
                conservation_content,
                f"Address conservation concerns and future prospects for {plant_name}",
                max_length=100, min_length=50
            ),
            'fallback': f"Conservation efforts for {plant_name} are essential to preserve this valuable component of South Africa's botanical diversity, ensuring that future generations can appreciate its unique contributions to the country's natural heritage."
        }

        # Build HTML content with strict deduplication
        html_sections = []
        used_section_content = set()

        # Add introduction
        intro_text = sections_data['introduction']['content'] or sections_data['introduction']['fallback']
        if intro_text:
            intro_hash = self._hash_content(intro_text)
            if intro_hash not in used_section_content:
                html_sections.extend(self.create_html_paragraphs(intro_text, "intro"))
                used_section_content.add(intro_hash)

        # Add other sections with headings
        for section_key in ['characteristics', 'habitat', 'cultural', 'conservation']:
            section_info = sections_data[section_key]
            section_content = section_info['content'] or section_info['fallback']
            
            if section_content:
                content_hash = self._hash_content(section_content)
                # Only add if content is unique
                if content_hash not in used_section_content:
                    html_sections.append(f'<h2 class="section-heading">{section_info["title"]}</h2>')
                    html_sections.extend(self.create_html_paragraphs(section_content, f"section-{section_key}"))
                    used_section_content.add(content_hash)

        # Ensure we have minimum content
        if len(html_sections) < 4:  # At least intro + one section
            logger.warning(f"Limited content generated for {plant_name}, adding fallback")
            html_sections.append('<h2 class="section-heading">About This Species</h2>')
            fallback_content = f"Research into {plant_name} continues to reveal the fascinating complexity of South African flora. This species represents the ongoing discovery of botanical treasures that contribute to our understanding of plant evolution and ecological relationships in this biodiverse region."
            html_sections.extend(self.create_html_paragraphs(fallback_content, "fallback"))

        # Generate title and front matter
        title_options = self.generate_title_variations(plant_name)
        selected_title = random.choice(title_options)

        # Compile final article
        article_parts = []

        if include_front_matter:
            article_parts.append(self.generate_jekyll_front_matter(plant_name, selected_title))

        article_parts.append('\n\n'.join(html_sections))

        logger.info(f"Article generated successfully for {plant_name}")
        final_article = '\n'.join(article_parts)
        
        # Final validation - check for obvious duplicates
        if self._validate_no_duplicates(final_article):
            return final_article
        else:
            logger.warning(f"Duplicate content detected in final article for {plant_name}")
            return self._generate_fallback_article(plant_name, include_front_matter)

    def _validate_no_duplicates(self, article: str) -> bool:
        """Validate that the article doesn't contain obvious duplicate sentences."""
        sentences = re.split(r'[.!?]+', article)
        sentence_hashes = set()
        
        for sentence in sentences:
            clean_sentence = re.sub(r'<[^>]+>', '', sentence).strip()  # Remove HTML tags
            if len(clean_sentence) > 20:  # Only check substantial sentences
                sentence_hash = self._hash_content(clean_sentence.lower())
                if sentence_hash in sentence_hashes:
                    return False
                sentence_hashes.add(sentence_hash)
        
        return True

    def _generate_fallback_article(self, plant_name: str, include_front_matter: bool = True) -> str:
        """Generate a basic fallback article when content generation fails."""
        logger.info(f"Generating fallback article for {plant_name}")

        html_sections = [
            f'<p class="intro">{plant_name} represents one of South Africa\'s many remarkable indigenous plant species, contributing to the country\'s reputation as one of the world\'s most botanically diverse regions.</p>',
            
            '<h2 class="section-heading">South African Flora Heritage</h2>',
            f'<p class="section-heritage">As part of South Africa\'s rich botanical tapestry, {plant_name} has evolved unique characteristics that reflect millions of years of adaptation to the continent\'s diverse climates and landscapes.</p>',
            
            '<h2 class="section-heading">Ecological Significance</h2>',
            f'<p class="section-ecology">The presence of species like {plant_name} highlights the intricate ecological relationships that have developed across South African biomes, from coastal regions to mountainous terrain.</p>',
            
            '<h2 class="section-heading">Conservation Importance</h2>',
            f'<p class="section-conservation">Understanding and preserving native species such as {plant_name} remains crucial for maintaining South Africa\'s extraordinary biodiversity and the ecosystem services these plants provide.</p>'
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