"""
Module for gathering research from multiple sources about South African plants.
Enhanced with fuzzy matching and comprehensive multi-source research.
"""
import requests
import json
import os
import time
import urllib.parse
from urllib.parse import urlparse
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import urllib3
from bs4 import BeautifulSoup
import re

# Disable SSL warnings since we're accessing some sites with self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class PlantResearchData:
    """Structured data container for plant research"""
    plant_name: Optional[str] = None
    scientific_name: Optional[str] = None
    title: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None  # 'government', 'academic', 'wikipedia', 'encyclopedia'
    source_name: Optional[str] = None
    abstract: Optional[str] = None
    full_text: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_date: Optional[str] = None
    traditional_uses: Optional[List[str]] = None
    scraped_date: Optional[str] = None
    confidence_score: Optional[float] = None

    def to_dict(self):
        return asdict(self)

class PlantNameMatcher:
    """Enhanced plant name matching with fuzzy search capabilities"""
    
    # Comprehensive South African plant database
    SA_PLANTS = {
        # Protea family
        'protea': {
            'names': ['protea', 'king protea', 'protea cynaroides', 'sugar bush', 'sugarbush'],
            'scientific': 'Protea cynaroides',
            'family': 'Proteaceae',
            'common_names': ['king protea', 'giant protea', 'honeypot']
        },
        'pincushion': {
            'names': ['pincushion', 'leucospermum', 'pincushion protea'],
            'scientific': 'Leucospermum',
            'family': 'Proteaceae',
            'common_names': ['pincushion flower', 'needle cushion']
        },
        
        # Well-known medicinal plants
        'rooibos': {
            'names': ['rooibos', 'red bush', 'redbush', 'red bush tea', 'aspalathus linearis', 'bush tea'],
            'scientific': 'Aspalathus linearis',
            'family': 'Fabaceae',
            'common_names': ['red bush tea', 'bush tea', 'rooibos tea']
        },
        'buchu': {
            'names': ['buchu', 'agathosma', 'round leaf buchu', 'agathosma betulina', 'barosma'],
            'scientific': 'Agathosma betulina',
            'family': 'Rutaceae',
            'common_names': ['bookoo', 'diosma', 'short buchu']
        },
        'african_wormwood': {
            'names': ['african wormwood', 'artemisia afra', 'wilde als', 'umhlonyane', 'wormwood'],
            'scientific': 'Artemisia afra',
            'family': 'Asteraceae',
            'common_names': ['wilde als', 'umhlonyane', 'African sage']
        },
        'sutherlandia': {
            'names': ['sutherlandia', 'cancer bush', 'kankerbos', 'lessertia frutescens', 'balloon pea'],
            'scientific': 'Lessertia frutescens',
            'family': 'Fabaceae',
            'common_names': ['cancer bush', 'kankerbos', 'balloon pea', 'swan plant']
        },
        'wild_garlic': {
            'names': ['wild garlic', 'tulbaghia', 'society garlic', 'tulbaghia violacea', 'pink agapanthus'],
            'scientific': 'Tulbaghia violacea',
            'family': 'Amaryllidaceae',
            'common_names': ['society garlic', 'sweet garlic', 'pink agapanthus']
        },
        'kanna': {
            'names': ['kanna', 'sceletium', 'kougoed', 'sceletium tortuosum', 'channa'],
            'scientific': 'Sceletium tortuosum',
            'family': 'Aizoaceae',
            'common_names': ['kougoed', 'channa', 'tortuose fig-marigold']
        },
        'honeybush': {
            'names': ['honeybush', 'heuningbos', 'cyclopia', 'honey bush tea', 'mountain tea'],
            'scientific': 'Cyclopia intermedia',
            'family': 'Fabaceae',
            'common_names': ['heuningbos', 'bergtee', 'mountain tea']
        },
        'african_potato': {
            'names': ['african potato', 'hypoxis', 'yellow stars', 'hypoxis hemerocallidea', 'star lily'],
            'scientific': 'Hypoxis hemerocallidea',
            'family': 'Hypoxidaceae',
            'common_names': ['yellow stars', 'star lily', 'African star grass']
        },
        'wild_dagga': {
            'names': ['wild dagga', 'leonotis', 'lions tail', 'leonotis leonurus', 'minaret flower'],
            'scientific': 'Leonotis leonurus',
            'family': 'Lamiaceae',
            'common_names': ['lions tail', 'minaret flower', 'lion\'s ear']
        },
        'cape_aloe': {
            'names': ['cape aloe', 'aloe ferox', 'bitter aloe', 'red aloe', 'tap aloe'],
            'scientific': 'Aloe ferox',
            'family': 'Asphodelaceae',
            'common_names': ['bitter aloe', 'red aloe', 'tap aloe']
        },
        'bird_of_paradise': {
            'names': ['bird of paradise', 'strelitzia', 'strelitzia reginae', 'crane flower'],
            'scientific': 'Strelitzia reginae',
            'family': 'Strelitziaceae',
            'common_names': ['crane flower', 'orange bird of paradise']
        }
    }
    
    @classmethod
    def fuzzy_match(cls, search_term: str, threshold: float = 0.6) -> List[Dict]:
        """Find plants using fuzzy string matching"""
        search_term = search_term.lower().strip()
        matches = []
        
        for plant_key, plant_data in cls.SA_PLANTS.items():
            # Check all possible names for this plant
            for name in plant_data['names']:
                similarity = SequenceMatcher(None, search_term, name.lower()).ratio()
                
                # Also check if search term is contained in any name
                contains_match = search_term in name.lower() or name.lower() in search_term
                
                if similarity >= threshold or contains_match:
                    match = {
                        'plant_key': plant_key,
                        'matched_name': name,
                        'similarity': similarity,
                        'scientific_name': plant_data['scientific'],
                        'common_names': plant_data['common_names'],
                        'family': plant_data['family']
                    }
                    matches.append(match)
                    break  # Only add each plant once
        
        # Sort by similarity score
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches
    
    @classmethod
    def get_search_variations(cls, plant_name: str) -> List[str]:
        """Generate search term variations for better results"""
        variations = [plant_name]
        
        # Find fuzzy matches first
        matches = cls.fuzzy_match(plant_name, threshold=0.3)
        
        for match in matches[:3]:  # Top 3 matches
            plant_key = match['plant_key']
            plant_data = cls.SA_PLANTS[plant_key]
            
            # Add scientific name
            variations.append(plant_data['scientific'])
            
            # Add primary common names
            variations.extend(plant_data['common_names'][:2])
            
            # Add the matched name itself
            variations.append(match['matched_name'])
        
        # Remove duplicates and normalize
        unique_variations = []
        for var in variations:
            normalized = var.lower().strip()
            if normalized not in [v.lower() for v in unique_variations]:
                unique_variations.append(var)
        
        return unique_variations[:5]  # Limit to 5 variations

class ResearchCollector:
    """Enhanced research collector with multi-source capabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'SouthAfricanPlantsResearchBot/2.0 (Educational Purpose)'
        }
        self.session.headers.update(self.headers)
        self.delay = 1  # Respectful delay between requests
        
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
            }
        }

    def clean_content(self, text: str) -> str:
        """Clean extracted text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common artifacts from web scraping
        text = re.sub(r'\[[^\]]*\]', '', text)  # Remove [edit] and similar
        text = re.sub(r'\(\s*\)', '', text)     # Remove empty parentheses
        
        return text

    def get_wikipedia_content(self, plant_name):
        """Get content from Wikipedia using enhanced search"""
        # Get search variations
        search_variations = PlantNameMatcher.get_search_variations(plant_name)
        
        for variation in search_variations:
            try:
                # Use Wikipedia API
                search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(variation)
                response = self.session.get(search_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('type') == 'standard':
                        result = {
                            'source': 'Wikipedia',
                            'title': data.get('title', ''),
                            'content': self.clean_content(data.get('extract', '')),
                            'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            'type': 'general_info',
                            'scientific_name': None,
                            'traditional_uses': []
                        }
                        
                        # Try to get more detailed content
                        if result['url']:
                            detailed_data = self._get_wikipedia_details(result['url'])
                            if detailed_data:
                                # Use detailed content if it's significantly longer
                                detailed_text = detailed_data.get('full_text', '')
                                if len(detailed_text) > len(result['content']) * 2:
                                    result['content'] = self.clean_content(detailed_text)
                                result['scientific_name'] = detailed_data.get('scientific_name', '')
                                result['traditional_uses'] = detailed_data.get('traditional_uses', [])
                        
                        return result
                        
            except Exception as e:
                print(f"Wikipedia error for '{variation}': {e}")
                continue
                
        return None

    def _get_wikipedia_details(self, wiki_url: str) -> Dict:
        """Get detailed information from Wikipedia page"""
        try:
            response = self.session.get(wiki_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1', id='firstHeading')
            title = title_elem.get_text() if title_elem else ''
            
            # Extract full text from paragraphs only (avoid navigation, infoboxes, etc.)
            content_div = soup.find('div', {'class': 'mw-parser-output'})
            if content_div:
                paragraphs = content_div.find_all('p', recursive=False)
            else:
                paragraphs = soup.find_all('p')
                
            full_text = ' '.join([p.get_text() for p in paragraphs])
            
            # Look for scientific name in binomial span
            scientific_name = None
            binomial = soup.find('span', class_='binomial')
            if binomial:
                scientific_name = binomial.get_text().strip()
            
            # Look for traditional uses in text
            traditional_uses = []
            keywords = ['traditional', 'medicinal', 'remedy', 'treatment', 'therapeutic', 'healing', 'medicine']
            
            for p in paragraphs:
                text = p.get_text().lower()
                if any(keyword in text for keyword in keywords):
                    use_text = p.get_text().strip()
                    if len(use_text) > 50 and len(use_text) < 300:  # Reasonable length
                        traditional_uses.append(use_text)
            
            return {
                'full_text': full_text,
                'scientific_name': scientific_name,
                'traditional_uses': traditional_uses[:5],  # Limit to 5 uses
                'title': title
            }
            
        except Exception as e:
            print(f"Error getting Wikipedia details: {e}")
            return {}

    def search_pubmed(self, plant_name: str) -> List[Dict]:
        """Search PubMed for medical research"""
        results = []
        search_variations = PlantNameMatcher.get_search_variations(plant_name)
        
        for variation in search_variations[:2]:  # Limit variations for API calls
            try:
                # Search PubMed via eUtils API
                search_term = f'"{variation}" medicinal OR traditional'
                
                search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                params = {
                    'db': 'pubmed',
                    'term': search_term,
                    'retmax': 5,  # Increased slightly
                    'retmode': 'json'
                }
                
                response = self.session.get(search_url, params=params, timeout=10)
                if response.status_code != 200:
                    continue
                    
                search_data = response.json()
                pmids = search_data.get('esearchresult', {}).get('idlist', [])
                
                if pmids:
                    # Get abstracts using efetch
                    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    fetch_params = {
                        'db': 'pubmed',
                        'id': ','.join(pmids[:3]),  # Limit to 3 papers
                        'retmode': 'xml'
                    }
                    
                    fetch_response = self.session.get(fetch_url, params=fetch_params, timeout=15)
                    if fetch_response.status_code == 200:
                        # Parse XML for abstracts
                        fetch_soup = BeautifulSoup(fetch_response.content, 'xml')
                        articles = fetch_soup.find_all('PubmedArticle')
                        
                        for article in articles:
                            title_elem = article.find('ArticleTitle')
                            abstract_elem = article.find('AbstractText')
                            pmid_elem = article.find('PMID')
                            
                            if title_elem and pmid_elem:
                                title = title_elem.get_text()
                                abstract = abstract_elem.get_text() if abstract_elem else ''
                                pmid = pmid_elem.get_text()
                                
                                result = {
                                    'source': 'PubMed',
                                    'title': title,
                                    'content': self.clean_content(abstract),
                                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                    'type': 'benefits',
                                    'authors': [],
                                    'publication_date': ''
                                }
                                results.append(result)
                            
                if results:
                    break  # Found results, no need to try more variations
                    
                time.sleep(self.delay)
                        
            except Exception as e:
                print(f"PubMed error for '{variation}': {e}")
                continue
                
        return results

    def search_openalex(self, plant_name: str) -> List[Dict]:
        """Search OpenAlex for academic papers"""
        results = []
        search_variations = PlantNameMatcher.get_search_variations(plant_name)
        
        for variation in search_variations[:2]:  # Limit variations
            try:
                # More specific search terms
                search_term = f'"{variation}" AND (medicinal OR traditional OR therapeutic)'
                
                api_url = "https://api.openalex.org/works"
                params = {
                    'search': search_term,
                    'per-page': 5,
                    'sort': 'cited_by_count:desc',
                    'filter': 'type:article'
                }
                
                headers = {
                    'User-Agent': 'SA Plant Bot (Educational Purpose)',
                    'mailto': 'research@example.com'  # OpenAlex recommends this
                }
                
                response = self.session.get(api_url, params=params, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                works = data.get('results', [])
                
                for work in works:
                    # Extract authors
                    authors = []
                    for authorship in work.get('authorships', [])[:3]:
                        author_name = authorship.get('author', {}).get('display_name')
                        if author_name:
                            authors.append(author_name)
                    
                    # Get abstract if available
                    abstract = work.get('abstract', '')
                    if not abstract:
                        # Try inverted abstract
                        inverted_abstract = work.get('abstract_inverted_index', {})
                        if inverted_abstract:
                            # Reconstruct abstract from inverted index (simplified)
                            words = [''] * 500  # Max length
                            for word, positions in inverted_abstract.items():
                                for pos in positions:
                                    if pos < len(words):
                                        words[pos] = word
                            abstract = ' '.join([w for w in words if w])
                    
                    result = {
                        'source': 'OpenAlex',
                        'title': work.get('title', ''),
                        'content': self.clean_content(abstract),
                        'url': work.get('id', ''),
                        'type': 'characteristics',
                        'authors': authors,
                        'publication_date': work.get('publication_date', '')
                    }
                    results.append(result)
                    
                if results:
                    break  # Found results
                    
                time.sleep(self.delay)
                    
            except Exception as e:
                print(f"OpenAlex error for '{variation}': {e}")
                continue
                
        return results

    def extract_text_from_url(self, url):
        """Extract main content from a webpage with improved content detection"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=15, verify=False)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'ads', 'iframe', 
                               'aside', 'menu', 'form', 'button']):
                element.decompose()

            # Look for specific content areas (improved selectors)
            content_selectors = [
                ('div', {'class': re.compile(r'content|main|article|post|entry', re.I)}),
                ('article', {}),
                ('main', {}),
                ('section', {'class': re.compile(r'content|main', re.I)}),
                ('div', {'id': re.compile(r'content|main|article', re.I)}),
            ]

            content = None
            for tag, attrs in content_selectors:
                if 'class' in attrs and hasattr(attrs['class'], 'pattern'):
                    elements = soup.find_all(tag, class_=attrs['class'])
                elif 'id' in attrs and hasattr(attrs['id'], 'pattern'):
                    elements = soup.find_all(tag, id=attrs['id'])
                else:
                    elements = soup.find_all(tag, attrs)
                    
                for element in elements:
                    if element and len(element.get_text().strip()) > 200:
                        content = element
                        break
                        
                if content:
                    break

            if not content:
                content = soup

            # Extract text from paragraphs and headings
            text_elements = []
            for elem in content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = elem.get_text().strip()
                if text and len(text) > 20:
                    text_elements.append(text)

            text = ' '.join(text_elements)
            text = self.clean_content(text)

            if len(text) > 200:
                return text
                    
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
        return None

    def search_botanical_sites(self, plant_name):
        """Search specific botanical websites (enhanced with fuzzy matching)"""
        results = []
        search_variations = PlantNameMatcher.get_search_variations(plant_name)
        
        # Generate URLs for each variation
        for variation in search_variations[:2]:  # Limit to prevent too many requests
            names = {
                'scientific': variation.lower().replace(' ', '-'),
                'common': variation.lower().replace(' ', '-')
            }

            urls = []
            for site, config in self.base_urls.items():
                for path in config['paths']:
                    for name_type, name in names.items():
                        url = config['base'] + path.format(name=name)
                        urls.append((url, site))

            for url, site_type in urls:
                try:
                    content = self.extract_text_from_url(url)
                    if content and len(content) > 100:  # Minimum content length
                        content_type = 'characteristics'
                        source = urlparse(url).netloc

                        result = {
                            'source': source,
                            'title': f"{plant_name} - {content_type.replace('_', ' ').title()}",
                            'content': content,
                            'url': url,
                            'type': content_type
                        }
                        results.append(result)
                        
                except Exception as e:
                    continue
                    
                time.sleep(self.delay)

        return results

    def collect_research(self, plant_name):
        """Collect research about a plant from multiple sources (enhanced)"""
        all_content = []
        
        print(f"Researching {plant_name} from multiple sources...")
        
        # Show fuzzy matches
        matches = PlantNameMatcher.fuzzy_match(plant_name)
        if matches:
            print(f"Found {len(matches)} plant matches:")
            for match in matches[:3]:
                print(f"  • {match['matched_name'].title()} ({match['scientific_name']}) - {match['similarity']:.2f} similarity")
        
        # Get Wikipedia content
        wiki_content = self.get_wikipedia_content(plant_name)
        if wiki_content and wiki_content.get('content'):
            all_content.append(wiki_content)
            print(f"✓ Found Wikipedia article: {wiki_content['title']} ({len(wiki_content['content'])} chars)")

        # Search PubMed
        try:
            pubmed_results = self.search_pubmed(plant_name)
            if pubmed_results:
                all_content.extend(pubmed_results)
                print(f"✓ Found {len(pubmed_results)} PubMed articles")
        except Exception as e:
            print(f"PubMed search failed: {e}")

        # Search OpenAlex
        try:
            openalex_results = self.search_openalex(plant_name)
            if openalex_results:
                all_content.extend(openalex_results)
                print(f"✓ Found {len(openalex_results)} OpenAlex articles")
        except Exception as e:
            print(f"OpenAlex search failed: {e}")

        # Search botanical websites
        botanical_content = self.search_botanical_sites(plant_name)
        if botanical_content:
            all_content.extend(botanical_content)
            print(f"✓ Found {len(botanical_content)} botanical website results")

        # Enhanced fallback content if nothing found
        if not all_content:
            fallback_content = self._generate_fallback_content(plant_name)
            all_content.append(fallback_content)
            print("! No external sources found - using enhanced fallback content")
        else:
            print(f"✓ Total sources found: {len(all_content)}")

        return all_content

    def _generate_fallback_content(self, plant_name: str) -> Dict:
        """Generate enhanced fallback content when no sources are found"""
        # Try to get some plant information from fuzzy matching
        matches = PlantNameMatcher.fuzzy_match(plant_name, threshold=0.3)
        
        if matches:
            best_match = matches[0]
            plant_info = PlantNameMatcher.SA_PLANTS[best_match['plant_key']]
            scientific_name = plant_info['scientific']
            family = plant_info['family']
            common_names = ', '.join(plant_info['common_names'][:3])
            
            content = f"""
{plant_name} ({scientific_name}) is a remarkable plant species native to South Africa, belonging to the {family} family. 
It is also known by several common names including {common_names}. This indigenous species represents the incredible 
diversity of South African flora, having evolved unique adaptations to thrive in the region's varied climate zones 
and soil conditions.

South African plants like {plant_name} have developed fascinating survival strategies over millions of years of evolution. 
These adaptations allow them to withstand challenging environmental conditions including drought, extreme temperatures, 
and nutrient-poor soils. Many species have also developed important ecological relationships with local wildlife, 
serving as food sources for birds, insects, and other animals.

The cultural significance of {plant_name} extends beyond its ecological role. Like many South African plants, it has 
likely been known and utilized by indigenous communities for generations, contributing to traditional knowledge systems 
about local flora. This traditional botanical knowledge represents centuries of observation and experimentation, 
providing valuable insights into sustainable plant use and conservation.

Conservation of species like {plant_name} is crucial for maintaining South Africa's status as one of the world's most 
biodiverse countries. These plants not only contribute to ecosystem health and stability but also represent potential 
resources for medicine, horticulture, and sustainable development initiatives.
            """.strip()
        else:
            content = f"""
{plant_name} is a remarkable plant species native to South Africa, representing the extraordinary diversity found 
within the country's flora. South Africa is recognized as one of the world's most biodiverse regions, home to an 
estimated 24,000 plant species, many of which are found nowhere else on Earth.

Indigenous plants like {plant_name} have evolved unique characteristics and adaptations that allow them to thrive 
in South Africa's diverse landscapes. From the Mediterranean climate of the Western Cape to the subtropical regions 
of KwaZulu-Natal, these plants have developed sophisticated strategies for survival in challenging conditions.

The cultural heritage associated with South African plants is deeply intertwined with the history of the region's 
people. Indigenous communities have developed extensive knowledge about local flora over thousands of years, 
understanding their medicinal properties, ecological relationships, and sustainable harvesting practices.

Conservation efforts for plants like {plant_name} are essential for preserving South Africa's botanical heritage. 
These species contribute to ecosystem stability, provide habitat for wildlife, and may hold keys to future medical 
discoveries or sustainable agricultural practices. Understanding and protecting this botanical diversity is crucial 
for maintaining healthy ecosystems and supporting local communities.
            """.strip()
        
        return {
            'source': 'Enhanced Default',
            'title': f"{plant_name} - South African Plant Profile",
            'content': content,
            'url': 'N/A',
            'type': 'general_info',
            'scientific_name': scientific_name if matches else '',
            'traditional_uses': []
        }

def research_plant(plant_name):
    """Main function to research a plant from multiple sources (enhanced)"""
    collector = ResearchCollector()

    print(f"🔍 Researching {plant_name} with enhanced fuzzy matching...")
    
    # Perform fuzzy match
    matches = PlantNameMatcher.fuzzy_match(plant_name, threshold=0.3)
    
    # Get Wikipedia content to check for a reliable plant name
    wiki_content = collector.get_wikipedia_content(plant_name)
    wiki_plant_name = None
    if wiki_content and wiki_content.get('title'):
        wiki_plant_name = wiki_content['title']
        print(f"✓ Found Wikipedia entry: '{wiki_plant_name}'")

    # Determine best plant name to use for research
    research_plant_name = plant_name
    if matches:
        best_match = matches[0]
        
        # Use different strategies based on confidence level
        if best_match['similarity'] >= 0.8:
            # High confidence - use scientific name
            research_plant_name = best_match['scientific_name']
            print(f"💡 High confidence match: '{best_match['matched_name'].title()}' ({research_plant_name})")
        elif best_match['similarity'] >= 0.6:
            # Medium confidence - use matched name
            research_plant_name = best_match['matched_name']
            print(f"💡 Medium confidence match: '{best_match['matched_name'].title()}' ({research_plant_name})")
        elif wiki_plant_name:
            # Low confidence but Wikipedia found - use Wikipedia title
            research_plant_name = wiki_plant_name
            print(f"💡 Low confidence match ({best_match['similarity']:.2f}). Using Wikipedia title: '{research_plant_name}'")
        else:
            # Low confidence and no Wikipedia - show alternatives
            research_plant_name = best_match['matched_name']
            print(f"💡 Low confidence match: '{best_match['matched_name'].title()}' ({best_match['similarity']:.2f})")
            print("Other possible matches:")
            for match in matches[1:3]:
                print(f"   • '{match['matched_name'].title()}' ({match['scientific_name']}) - {match['similarity']:.2f}")
    elif wiki_plant_name:
        # No fuzzy matches but Wikipedia found
        research_plant_name = wiki_plant_name
        print(f"No plant database matches. Using Wikipedia title: '{research_plant_name}'")
    else:
        print(f"No matches found in plant database or Wikipedia. Using original: '{plant_name}'")

    # Collect research data
    results = collector.collect_research(research_plant_name)

    # Save results to JSON file with timestamp
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'research_results_{timestamp}.json')
    os.makedirs(output_dir, exist_ok=True)

    # Convert to the expected format
    formatted_results = []
    for result in results:
        formatted_result = {
            'source': result.get('source', 'Unknown'),
            'title': result.get('title', ''),
            'content': result.get('content', ''),
            'url': result.get('url', ''),
            'type': result.get('type', 'general_info'),
            'scientific_name': result.get('scientific_name', ''),
            'traditional_uses': result.get('traditional_uses', []),
            'authors': result.get('authors', []),
            'publication_date': result.get('publication_date', ''),
            'scraped_date': datetime.now().isoformat(),
            'original_search_term': plant_name,
            'research_term_used': research_plant_name
        }
        formatted_results.append(formatted_result)

    # Save timestamped file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)

    # Also save as latest research_results.json for compatibility
    latest_file = os.path.join(output_dir, 'research_results.json')
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)

    print(f"💾 Results saved to {output_file}")
    print(f"💾 Latest results also saved to {latest_file}")
    return formatted_results

# Helper functions for testing
def suggest_plants(partial_name: str):
    """Suggest plants based on partial name input"""
    matches = PlantNameMatcher.fuzzy_match(partial_name, threshold=0.3)
    
    print(f"🔍 Plant suggestions for '{partial_name}':")
    if matches:
        for i, match in enumerate(matches[:10], 1):  # Show more suggestions
            print(f"{i:2d}. {match['matched_name'].title()}")
            print(f"     Scientific: {match['scientific_name']}")
            print(f"     Family: {match['family']}")
            print(f"     Similarity: {match['similarity']:.2f}")
            if i <= 5:  # Show common names for top 5
                common_names = ', '.join(match['common_names'][:3])
                print(f"     Also known as: {common_names}")
            print()
    else:
        print("❌ No matching plants found")
        print("\nSuggested South African plants to try:")
        popular_plants = [
            'King Protea', 'Rooibos', 'Bird of Paradise', 'Cape Aloe',
            'Buchu', 'African Wormwood', 'Sutherlandia', 'Wild Dagga',
            'Honeybush', 'African Potato', 'Wild Garlic', 'Kanna'
        ]
        for plant in popular_plants:
            print(f"  • {plant}")

def test_fuzzy_search():
    """Test the fuzzy search functionality"""
    test_cases = [
        "king protea",
        "red bush", 
        "wilde als",
        "society garlic",
        "cancer bush",
        "lions tail",
        "bird paradise",
        "aloe ferox",
        "honeybush tea",
        "african potato"
    ]
    
    print("🎯 Testing fuzzy search capabilities:")
    print("=" * 50)
    
    for test_case in test_cases:
        matches = PlantNameMatcher.fuzzy_match(test_case)
        print(f"'{test_case}' -> {len(matches)} matches")
        if matches:
            best = matches[0]
            print(f"   Best: {best['matched_name']} ({best['scientific_name']}) - {best['similarity']:.2f}")
        print()

def list_available_plants():
    """List all plants available in the database"""
    print("🌿 Available South African Plants in Database:")
    print("=" * 60)
    
    for i, (plant_key, plant_data) in enumerate(PlantNameMatcher.SA_PLANTS.items(), 1):
        print(f"{i:2d}. {plant_data['scientific']}")
        print(f"     Family: {plant_data['family']}")
        print(f"     Common names: {', '.join(plant_data['common_names'][:3])}")
        print(f"     Search terms: {', '.join(plant_data['names'][:3])}...")
        print()

if __name__ == "__main__":
    print("🌿 Enhanced SA Plant Research Module v2.1")
    print("=" * 45)
    print("Available functions:")
    print("• research_plant('plant_name') - Main research function")
    print("• suggest_plants('partial_name') - Get plant suggestions") 
    print("• test_fuzzy_search() - Test fuzzy matching")
    print("• list_available_plants() - Show all database plants")
    print("• PlantNameMatcher.SA_PLANTS.keys() - Plant database keys")
    print()
    print("Example usage:")
    print("  research_plant('King Protea')")
    print("  suggest_plants('red')")
    print("  test_fuzzy_search()")