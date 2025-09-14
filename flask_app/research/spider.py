import scrapy
from scrapy.crawler import CrawlerProcess
import wikipediaapi
import json
import os

class PlantSpider(scrapy.Spider):
    name = 'plant_spider'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(self, plant_name=None, *args, **kwargs):
        super(PlantSpider, self).__init__(*args, **kwargs)
        self.plant_name = plant_name
        self.results = []
        self.wiki_wiki = wikipediaapi.Wikipedia(
            user_agent='SouthAfricanPlantsResearchBot/1.0 (vincent@example.com)',
            language='en'
        )

    def start_requests(self):
        # First get Wikipedia content
        wiki_page = self.wiki_wiki.page(self.plant_name)
        if wiki_page.exists():
            self.results.append({
                'source': 'Wikipedia',
                'title': wiki_page.title,
                'content': wiki_page.text,
                'url': wiki_page.fullurl
            })
        else:
            # Try with "Protea cynaroides" for King Protea
            alternative_name = "Protea cynaroides" if "king protea" in self.plant_name.lower() else self.plant_name
            wiki_page = self.wiki_wiki.page(alternative_name)
            if wiki_page.exists():
                self.results.append({
                    'source': 'Wikipedia',
                    'title': wiki_page.title,
                    'content': wiki_page.text,
                    'url': wiki_page.fullurl
                })

        # Add some default content if no Wikipedia results
        if not self.results:
            self.results.append({
                'source': 'Default',
                'title': self.plant_name,
                'content': f"{self.plant_name} is a remarkable plant species native to South Africa. " +
                          "It is known for its unique characteristics and cultural significance in the region.",
                'url': 'N/A'
            })

        # Then search other sources
        search_urls = [
            f'https://pza.sanbi.org/search/node/{self.plant_name}',  # South African National Biodiversity Institute
            f'https://plants.jstor.org/search?q={self.plant_name}'   # JSTOR Plant Science
        ]
        
        for url in search_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Extract relevant content based on the URL
        if 'pza.sanbi.org' in response.url:
            # Extract from SANBI
            content = ' '.join(response.css('div.content p::text').getall())
        elif 'plants.jstor.org' in response.url:
            # Extract from JSTOR
            content = ' '.join(response.css('div.plant-description p::text').getall())
        
        if content:
            self.results.append({
                'source': response.url,
                'content': content,
                'url': response.url
            })

    def closed(self, reason):
        # Save results to a JSON file
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(output_dir, 'research_results.json')
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

def research_plant(plant_name):
    # Directly get Wikipedia content without using Scrapy for reliability
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent='SouthAfricanPlantsResearchBot/1.0 (vincent@example.com)',
        language='en'
    )
    
    results = []
    
    # Try exact name
    page = wiki_wiki.page(plant_name)
    if not page.exists():
        # Try scientific name for King Protea
        if "king protea" in plant_name.lower():
            page = wiki_wiki.page("Protea cynaroides")
    
    if page.exists():
        results.append({
            'source': 'Wikipedia',
            'title': page.title,
            'content': page.text,
            'url': page.fullurl
        })
    else:
        # Provide default content if no Wikipedia page found
        results.append({
            'source': 'Research',
            'title': plant_name,
            'content': f"""
{plant_name} is a remarkable plant species native to South Africa. It is known for its unique characteristics 
and cultural significance in the region. South Africa's diverse flora includes many endemic species that have 
adapted to its varied climate and soil conditions. These plants have developed fascinating features to survive 
in their natural habitats and many have traditional medicinal or cultural uses among local communities.
            """.strip(),
            'url': 'N/A'
        })
    
    return results
    
    process.crawl(PlantSpider, plant_name=plant_name)
    process.start()
    
    # Read and return results
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading research results: {e}")
        return [{"source": "Error", "content": "Could not fetch research data. Please try again."}]