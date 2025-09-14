"""
Standalone script to test article generation about South African plants.
Updated to output HTML files with proper Jekyll front matter format.
"""
import os
import sys
import random
from research_v2.spider import research_plant
from research_v2.generator import generate_article, generate_plant_title
from datetime import datetime

def generate_plant_article(plant_name):
    print(f"\n🔍 Researching '{plant_name}'...")
    
    # Gather research using web scraping
    try:
        research_data = research_plant(plant_name)
        print("✓ Research data gathered successfully")
        
        # Show sources found
        print(f"\nSources found ({len(research_data)}):")
        for item in research_data:
            if 'source' in item:
                print(f"- {item['source']}: {item.get('url', 'N/A')}")
    
        # Generate article using AI summarization
        print("\n🤖 Processing content with AI...")
        article_html = generate_article(research_data, plant_name)
        
        # Generate title
        title = generate_plant_title(plant_name)
        
        # Create filename
        date = datetime.now()
        filename = f"{date.strftime('%Y-%m-%d')}-{plant_name.lower().replace(' ', '-').replace('(', '').replace(')', '')}.html"
        
        # Create posts directory if it doesn't exist
        posts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '_posts')
        os.makedirs(posts_dir, exist_ok=True)
        filepath = os.path.join(posts_dir, filename)
        
        # Random background image (you can expand this list)
        background_images = [
            '/img/posts/01.jpg',
            '/img/posts/02.jpg',
            '/img/posts/03.jpg',
            '/img/posts/04.jpg',
            '/img/posts/05.jpg',
            '/img/posts/06.jpg'
        ]
        background = random.choice(background_images)
        
        # Jekyll front matter in exact format requested
        front_matter = f"""---
layout: post
title: "{title}"
date: {date.strftime('%Y-%m-%d %H:%M:%S %z')}
background: '{background}'
---

"""
        
        # Combine front matter with HTML article content
        full_article = front_matter + article_html
        
        # Save the HTML post
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_article)
            
        print(f"\n✓ HTML article saved to: {filepath}")
        print(f"📁 File size: {len(full_article)} characters")
        
        # Show preview
        print(f"\n📝 Generated Article Preview:")
        print("=" * 80)
        print("FRONT MATTER:")
        print(front_matter.strip())
        print("\nHTML CONTENT (first 500 chars):")
        print(article_html[:500] + "..." if len(article_html) > 500 else article_html)
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def batch_generate_articles(plant_list):
    """Generate articles for multiple plants"""
    print(f"🌱 Starting batch generation for {len(plant_list)} plants...")
    
    success_count = 0
    for i, plant in enumerate(plant_list, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(plant_list)}: {plant}")
        print('='*60)
        
        if generate_plant_article(plant):
            success_count += 1
        
        # Small delay between requests to be respectful to scraped sites
        if i < len(plant_list):
            print("\n⏳ Waiting 5 seconds before next plant...")
            import time
            time.sleep(5)
    
    print(f"\n🎉 Batch complete! Successfully generated {success_count}/{len(plant_list)} articles")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single plant: python3 test_generator.py 'Plant Name'")
        print("  Multiple plants: python3 test_generator.py 'Plant 1' 'Plant 2' 'Plant 3'")
        print("\nExamples:")
        print("  python3 test_generator.py 'King Protea'")
        print("  python3 test_generator.py 'King Protea' 'Bird of Paradise' 'Aloe Ferox'")
        sys.exit(1)
    
    plant_names = sys.argv[1:]
    
    if len(plant_names) == 1:
        # Single plant
        generate_plant_article(plant_names[0])
    else:
        # Multiple plants
        batch_generate_articles(plant_names)
