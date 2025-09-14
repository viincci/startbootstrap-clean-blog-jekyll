"""
Standalone script to test article generation about South African plants.
This script demonstrates the research and article generation without needing the Flask app.
"""
import os
import sys
from research_v2.spider import research_plant
from research_v2.generator import generate_article
from datetime import datetime

def generate_plant_article(plant_name):
    print(f"\n🔍 Researching '{plant_name}'...")
    
    # Gather research
    try:
        research_data = research_plant(plant_name)
        print("✓ Research gathered successfully")
        
        # Show sources found
        print("\nSources found:")
        for item in research_data:
            if 'source' in item:
                print(f"- {item['source']}")
    
        # Generate article
        print("\n✍️ Generating article...")
        article = generate_article(research_data)
        
        # Save article
        date = datetime.now()
        filename = f"{date.strftime('%Y-%m-%d')}-{plant_name.lower().replace(' ', '-')}.html"
        posts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '_posts')
        filepath = os.path.join(posts_dir, filename)
        
        # Jekyll front matter
        front_matter = f"""---
title: "South African Plant Series: {plant_name}"
subtitle: "A Deep Dive into Indigenous Flora"
date: {date.strftime('%Y-%m-%d %H:%M:%S %z')}
background: '/img/posts/01.jpg'
---

"""
        # Save the post
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(front_matter + article)
            
        print(f"\n✓ Article saved to: {filepath}")
        print("\n📝 Generated Article:")
        print("=" * 80)
        print(article)
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_generator.py 'Plant Name'")
        print("Example: python3 test_generator.py 'King Protea'")
        sys.exit(1)
        
    plant_name = sys.argv[1]
    generate_plant_article(plant_name)