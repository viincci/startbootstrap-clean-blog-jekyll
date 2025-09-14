"""
Module for gathering research from multiple sources about South African plants.
"""
import wikipediaapi
import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse
import urllib3

# Disable SSL warnings since we're accessing some sites with self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ResearchCollector:
    def __init__(self):
        self.wiki_wiki = wikipediaapi.Wikipedia(
            user_agent='SouthAfricanPlantsResearchBot/1.0 (mmehgoss@gmail.com)',
            language='en'
        )
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Updated URLs based on current availability
        self.base_urls = {
            'sanbi': {
                'base': 'http://pza.sanbi.org',
                'paths': [
                    '/species-name/{name}',
                    '/{name}',
                    '/plants/{name}'
                ]
            },
            'plantzafrica': {
                'base': 'http://pza.sanbi.org',  # Redirects to SANBI
                'paths': [
                    '/plant/{name}',
                    '/plants/{name}'
                ]
            },
            'jstor': {
                'base': 'https://plants.jstor.org',
                'paths': [
                    '/stable/10.5555/al.ap.flora.flosa{name}'
                ]
            },
            'kew': {
                'base': 'http://www.plantsoftheworldonline.org',
                'paths': [
                    '/taxon/{name}'
                ]
            }
        }

    def get_wikipedia_content(self, plant_name):
        """Get content from Wikipedia."""
        wiki_page = self.wiki_wiki.page(plant_name)
        if not wiki_page.exists():
            # Try alternative names
            alternatives = {
                "king protea": ["Protea cynaroides", "Protea (plant)"],
                "bird of paradise": ["Strelitzia reginae", "Strelitzia"],
                "aloe ferox": ["Aloe ferox", "Cape aloe"],
            }
            
            plant_lower = plant_name.lower()
            for key, names in alternatives.items():
                if key in plant_lower:
                    for alt_name in names:
                        wiki_page = self.wiki_wiki.page(alt_name)
                        if wiki_page.exists():
                            break
        
        if wiki_page.exists():
            return {
                'source': 'Wikipedia',
                'title': wiki_page.title,
                'content': wiki_page.text,
                'url': wiki_page.fullurl,
                'type': 'general_info'
            }
        return None

    def extract_text_from_url(self, url):
        """Extract main content from a webpage."""
        try:
            print(f"      Fetching content from {url}")
            response = requests.get(url, headers=self.headers, timeout=15, verify=False)  # Increased timeout
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'ads', 'iframe']):
                    element.decompose()
                
                # Look for specific content areas based on common website structures
                content_selectors = [
                    ('div', {'class_': ['content', 'main-content', 'article-content', 'main', 'article']}),
                    ('article', {}),
                    ('main', {}),
                    ('div', {'id': ['content', 'main', 'article', 'main-content']}),
                ]
                
                content = None
                for tag, attrs in content_selectors:
                    content = soup.find(tag, **attrs)
                    if content and len(content.get_text().strip()) > 200:  # Ensure we have substantial content
                        break
                
                if not content:
                    content = soup  # Fallback to full page
                
                # Extract text from paragraphs and headings
                text_elements = []
                for elem in content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = elem.get_text().strip()
                    if text and len(text) > 20:  # Skip very short fragments
                        text_elements.append(text)
                
                text = ' '.join(text_elements)
                text = ' '.join(text.split())  # Normalize whitespace
                
                if len(text) > 200:  # Only return if we have substantial content
                    print(f"      ✓ Successfully extracted {len(text)} characters")
                    return text
                else:
                    print("      ✗ No substantial content found in the page")
                    return None
        except Exception as e:
            print(f"      × Error extracting content from {url}: {str(e)}")
        return None

    def generate_urls(self, plant_name):
        """Generate possible URLs for the plant."""
        names = {
            'scientific': plant_name.lower(),
            'common': plant_name.lower()
        }
        
        # Handle common name mappings
        if "king protea" in plant_name.lower():
            names['scientific'] = "protea-cynaroides"
        elif "bird of paradise" in plant_name.lower():
            names['scientific'] = "strelitzia-reginae"
        elif "bitter aloe" in plant_name.lower() or "cape aloe" in plant_name.lower():
            names['scientific'] = "aloe-ferox"
        
        # Format names for URLs
        for key in names:
            names[key] = names[key].replace(' ', '-').lower()
        
        urls = []
        # Generate URLs for each base URL and path pattern
        for site, config in self.base_urls.items():
            for path in config['paths']:
                for name_type, name in names.items():
                    url = config['base'] + path.format(name=name)
                    urls.append((url, site))
        
        return urls

    def search_botanical_sites(self, plant_name):
        """Search specific botanical websites for plant information."""
        results = []
        urls = self.generate_urls(plant_name)
        
        print(f"\n🔍 Checking botanical websites for '{plant_name}'...")
        for url, site_type in urls:
            try:
                print(f"  - Checking: {url}")
                content = self.extract_text_from_url(url)
                if content:
                    # Determine content type based on URL and site
                    content_type = 'general_info'
                    source = urlparse(url).netloc
                    
                    if 'sanbi.org' in url or 'plantzafrica' in url:
                        content_type = 'characteristics'
                    elif 'jstor.org' in url:
                        content_type = 'benefits'
                    elif 'plantsoftheworldonline.org' in url:
                        content_type = 'taxonomy'
                        
                    results.append({
                        'source': source,
                        'title': f"{plant_name} - {content_type.replace('_', ' ').title()}",
                        'content': content,
                        'url': url,
                        'type': content_type
                    })
                    print(f"    ✓ Added content from: {url}")
            except Exception as e:
                print(f"    × Error checking {url}: {str(e)}")
                continue
                
        if not results:
            print("  ! No content found from botanical websites. Falling back to Wikipedia...")
            
        return results

    def collect_research(self, plant_name):
        """Collect research about a plant from multiple sources."""
        all_content = []
        
        # First try Wikipedia
        wiki_content = self.get_wikipedia_content(plant_name)
        if wiki_content:
            all_content.append(wiki_content)
            print(f"✓ Found Wikipedia article: {wiki_content['title']}")
            
        # Then try botanical websites
        botanical_content = self.search_botanical_sites(plant_name)
        all_content.extend(botanical_content)
            
        return all_content

def research_plant(plant_name):
    """Main function to research a plant from multiple sources."""
    collector = ResearchCollector()
    results = []
    
    print(f"🔍 Researching {plant_name} from multiple sources...")
    results = collector.collect_research(plant_name)
    
    # Ensure we have at least some content
    if not results:
        results.append({
            'source': 'Default',
            'title': plant_name,
            'content': f"""
{plant_name} is a remarkable plant species native to South Africa. It is known for its unique characteristics 
and cultural significance in the region. South Africa's diverse flora includes many endemic species that have 
adapted to its varied climate and soil conditions. These plants have developed fascinating features to survive 
in their natural habitats and many have traditional medicinal or cultural uses among local communities.
            """.strip(),
            'url': 'N/A',
            'type': 'general_info'
        })
    else:
        print(f"✓ Found {len(results)} sources")
    
    # Save results to JSON file
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, 'research_results.json')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results