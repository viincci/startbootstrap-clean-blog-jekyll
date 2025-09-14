"""
Standalone script to test article generation about South African plants.
Updated to work with research_v2 folder structure and output Jekyll HTML files.
"""
import os
import sys
import random
import time
from datetime import datetime

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import from your research_v2 module structure
try:
    from research_v2.spider import research_plant
    print("✓ Successfully imported research_plant from research_v2.spider")
except ImportError as e:
    print(f"❌ Error importing research_plant: {e}")
    print("Make sure research_v2/spider.py exists and contains the research_plant function")
    sys.exit(1)

# Try to import article generator - check multiple possible locations
generator_imported = False
JekyllArticleGenerator = None

# Try different import locations for the generator
try:
    from research_v2.generator import JekyllArticleGenerator
    print("✓ Successfully imported JekyllArticleGenerator from research_v2.generator")
    generator_imported = True
except ImportError:
    try:
        from research_v2.generator import generate_article, generate_plant_title
        print("✓ Successfully imported generate_article functions from research_v2.generator")
        generator_imported = "functions"
    except ImportError:
        try:
            # Try importing from current directory
            from generator import JekyllArticleGenerator
            print("✓ Successfully imported JekyllArticleGenerator from generator.py")
            generator_imported = True
        except ImportError:
            print("❌ Could not find article generator. Creating basic generator...")
            generator_imported = False

# Simple fallback generator if none found
class BasicJekyllGenerator:
    """Basic Jekyll article generator as fallback"""
    
    def generate_article(self, research_data, plant_name, include_front_matter=True):
        """Generate a basic Jekyll article"""
        date = datetime.now()
        
        # Create front matter
        front_matter = f"""---
layout: post
title: "Discovering {plant_name}: A South African Botanical Wonder"
subtitle: "Exploring the unique characteristics and heritage of this remarkable indigenous plant"
date: {date.strftime('%Y-%m-%d %H:%M:%S')}
background: '/img/posts/{random.randint(1, 6):02d}.jpg'
---

"""
        
        # Generate content based on research data
        content_parts = []
        
        # Introduction
        content_parts.append(f"<p>We're excited to share comprehensive information about {plant_name}, one of South Africa's fascinating indigenous plant species! Our research system has gathered detailed information from leading botanical databases to bring you accurate and up-to-date knowledge about this remarkable plant.</p>")
        
        # Research sources section
        content_parts.append("<h2>Botanical Research Sources</h2>")
        content_parts.append(f"<p>Our comprehensive research on {plant_name} draws from authoritative botanical sources including:</p>")
        content_parts.append("<ul>")
        content_parts.append("    <li>South African National Biodiversity Institute (SANBI)</li>")
        content_parts.append("    <li>PlantZAfrica</li>")
        content_parts.append("    <li>Wikipedia</li>")
        content_parts.append("    <li>Academic databases (PubMed, OpenAlex)</li>")
        content_parts.append("    <li>Botanical websites and databases</li>")
        content_parts.append("</ul>")
        
        # Content from research data
        if research_data:
            content_parts.append("<h2>Research Findings</h2>")
            
            # Group content by type
            general_content = []
            characteristics_content = []
            benefits_content = []
            
            for item in research_data:
                content_text = item.get('content', '').strip()
                if len(content_text) > 50:  # Only use substantial content
                    content_type = item.get('type', 'general_info')
                    if content_type == 'characteristics':
                        characteristics_content.append(content_text[:300] + "..." if len(content_text) > 300 else content_text)
                    elif content_type == 'benefits':
                        benefits_content.append(content_text[:300] + "..." if len(content_text) > 300 else content_text)
                    else:
                        general_content.append(content_text[:400] + "..." if len(content_text) > 400 else content_text)
            
            # Add general information
            if general_content:
                for i, content in enumerate(general_content[:2]):  # Limit to 2 items
                    content_parts.append(f"<p>{content}</p>")
            
            # Add characteristics if found
            if characteristics_content:
                content_parts.append("<h2>Plant Characteristics</h2>")
                for content in characteristics_content[:1]:  # Limit to 1 item
                    content_parts.append(f"<p>{content}</p>")
            
            # Add benefits/uses if found
            if benefits_content:
                content_parts.append("<h2>Traditional Uses & Benefits</h2>")
                for content in benefits_content[:1]:  # Limit to 1 item
                    content_parts.append(f"<p>{content}</p>")
        
        # Default content sections
        content_parts.append("<h2>South African Botanical Heritage</h2>")
        content_parts.append(f"<p>{plant_name} represents the extraordinary diversity of South Africa's flora. As an indigenous species, it has evolved unique adaptations to thrive in the region's diverse landscapes and challenging environmental conditions.</p>")
        
        content_parts.append("<h2>Conservation & Future</h2>")
        content_parts.append(f"<p>Understanding and preserving native species like {plant_name} is crucial for maintaining South Africa's position as one of the world's most biodiverse countries. These plants contribute to ecosystem health and may hold keys to future discoveries in medicine and sustainable agriculture.</p>")
        
        # Final paragraph
        content_parts.append("<p>Our ongoing research into South African flora continues to reveal fascinating insights about these remarkable plants. We remain committed to providing accurate, comprehensive information about botanical treasures like this one.</p>")
        
        # Combine all parts
        html_content = '\n\n'.join(content_parts)
        
        if include_front_matter:
            return front_matter + html_content
        else:
            return html_content

def get_posts_directory():
    """Get the correct path to the _posts directory"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    posts_dir = os.path.join(script_dir, '_posts')
    os.makedirs(posts_dir, exist_ok=True)
    return posts_dir

def generate_plant_article(plant_name):
    print(f"\n🔍 Researching '{plant_name}'...")

    try:
        # Step 1: Gather research data
        print("Step 1: Gathering research data...")
        research_data = research_plant(plant_name)
        
        if not research_data:
            print("⚠️ No research data found, but will generate article with fallback content")
            research_data = []
        else:
            print(f"✓ Research data gathered: {len(research_data)} sources")

        # Show sources found
        if research_data:
            print(f"\nSources found ({len(research_data)}):")
            for item in research_data:
                if 'source' in item:
                    source = item['source']
                    url = item.get('url', 'N/A')
                    content_length = len(item.get('content', ''))
                    print(f"- {source}: {content_length} chars - {url}")

        # Step 2: Generate article using appropriate generator
        print("\n🤖 Processing content with AI...")
        
        if generator_imported is True and JekyllArticleGenerator:
            # Use the class-based generator
            generator = JekyllArticleGenerator()
            full_article = generator.generate_article(research_data, plant_name, include_front_matter=True)
        elif generator_imported == "functions":
            # Use the function-based generator with front matter
            article_content = generate_article(research_data, plant_name)
            title = generate_plant_title(plant_name)
            
            date = datetime.now()
            front_matter = f"""---
layout: post
title: "{title}"
subtitle: "Exploring the remarkable {plant_name} and its unique characteristics"
date: {date.strftime('%Y-%m-%d %H:%M:%S')}
background: '/img/posts/{random.randint(1, 6):02d}.jpg'
---

"""
            full_article = front_matter + article_content
        else:
            # Use fallback generator
            generator = BasicJekyllGenerator()
            full_article = generator.generate_article(research_data, plant_name, include_front_matter=True)

        print(f"✓ Article generated successfully: {len(full_article)} characters")

        # Step 3: Create filename and save
        date = datetime.now()
        clean_name = plant_name.lower().replace(' ', '-').replace('(', '').replace(')', '')
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in '-_')
        filename = f"{date.strftime('%Y-%m-%d')}-{clean_name}.html"

        posts_dir = get_posts_directory()
        filepath = os.path.join(posts_dir, filename)

        print(f"Step 3: Saving article to {filename}...")
        print(f"📁 Posts directory: {posts_dir}")

        # Save the HTML post
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_article)

        print(f"✓ Article saved successfully!")
        print(f"📄 Full path: {filepath}")
        print(f"📊 File size: {len(full_article):,} characters")

        # Show preview
        show_article_preview(full_article, plant_name)

        return True

    except Exception as e:
        print(f"\n❌ Error generating article: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_article_preview(full_article, plant_name):
    """Show a preview of the generated article"""
    print(f"\n📝 Article Preview for '{plant_name}':")
    print("=" * 80)
    
    # Split front matter and content for better preview
    if full_article.startswith('---'):
        parts = full_article.split('---', 2)
        if len(parts) >= 3:
            front_matter = f"---{parts[1]}---"
            content = parts[2].strip()
            
            print("FRONT MATTER:")
            print(front_matter)
            print(f"\nCONTENT PREVIEW (first 400 chars):")
            preview = content[:400]
            if len(content) > 400:
                preview += "..."
            print(preview)
        else:
            print("FULL PREVIEW (first 500 chars):")
            print(full_article[:500] + "..." if len(full_article) > 500 else full_article)
    else:
        print("FULL PREVIEW (first 500 chars):")
        print(full_article[:500] + "..." if len(full_article) > 500 else full_article)
    
    print("=" * 80)

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
        else:
            print(f"❌ Failed to generate article for {plant}")

        # Small delay between requests to be respectful to scraped sites
        if i < len(plant_list):
            print(f"\n⏳ Waiting 3 seconds before next plant...")
            time.sleep(3)

    print(f"\n🎉 Batch complete! Successfully generated {success_count}/{len(plant_list)} articles")
    
    # Show summary of generated files
    posts_dir = get_posts_directory()
    if os.path.exists(posts_dir):
        files = [f for f in os.listdir(posts_dir) if f.endswith('.html')]
        if files:
            print(f"\n📋 Generated files in {posts_dir}:")
            for filename in sorted(files):
                filepath = os.path.join(posts_dir, filename)
                size = os.path.getsize(filepath)
                print(f"  • {filename} ({size:,} bytes)")

def show_usage():
    """Display usage instructions and plant suggestions"""
    print("🌿 South African Plant Article Generator")
    print("=" * 50)
    
    # Show current configuration
    posts_dir = get_posts_directory()
    print(f"📁 Posts will be saved to: {posts_dir}")
    
    if generator_imported is True:
        print(f"🤖 Using class-based JekyllArticleGenerator")
    elif generator_imported == "functions":
        print(f"🤖 Using function-based generator")
    else:
        print(f"🤖 Using basic fallback generator")
    
    print("\nUsage:")
    print("  Single plant:    python test_generator.py 'Plant Name'")
    print("  Multiple plants: python test_generator.py 'Plant 1' 'Plant 2' 'Plant 3'")
    print("  Test setup:      python test_generator.py --test")
    print("  Help:           python test_generator.py --help")
    
    print("\nExamples:")
    print("  python test_generator.py 'King Protea'")
    print("  python test_generator.py 'King Protea' 'Bird of Paradise' 'Cape Aloe'")
    
    # Suggest some South African plants
    suggested_plants = [
        'King Protea', 'Rooibos', 'Bird of Paradise', 'Cape Aloe', 
        'Buchu', 'African Wormwood', 'Sutherlandia', 'Wild Dagga',
        'Honeybush', 'African Potato', 'Wild Garlic', 'Kanna'
    ]
    
    print(f"\nSuggested South African plants to try:")
    for i, plant in enumerate(suggested_plants, 1):
        print(f"  {i:2d}. {plant}")

def test_setup():
    """Test the setup and show configuration"""
    print("🧪 Testing setup...")
    
    # Test posts directory
    posts_dir = get_posts_directory()
    print(f"✓ Posts directory: {posts_dir}")
    print(f"✓ Directory exists: {os.path.exists(posts_dir)}")
    
    # Test imports
    print(f"✓ Research module: research_v2.spider.research_plant")
    
    if generator_imported is True:
        print(f"✓ Generator: JekyllArticleGenerator (class-based)")
    elif generator_imported == "functions":
        print(f"✓ Generator: generate_article functions")
    else:
        print(f"✓ Generator: BasicJekyllGenerator (fallback)")
    
    # Show file structure
    print(f"\nFile structure check:")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
    
    if os.path.exists('research_v2'):
        print("✓ research_v2 directory found")
        research_files = [f for f in os.listdir('research_v2') if f.endswith('.py')]
        print(f"  Python files: {research_files}")
        
        # Check specific files
        spider_exists = os.path.exists('research_v2/spider.py')
        generator_exists = os.path.exists('research_v2/generator.py')
        print(f"  spider.py exists: {spider_exists}")
        print(f"  generator.py exists: {generator_exists}")
    else:
        print("❌ research_v2 directory not found")
        print("Make sure you're running this script from the correct directory")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h', 'help']:
        show_usage()
        sys.exit(1)
    
    if sys.argv[1] == '--test':
        test_setup()
        sys.exit(0)

    plant_names = sys.argv[1:]

    if len(plant_names) == 1:
        # Single plant
        success = generate_plant_article(plant_names[0])
        if success:
            print(f"\n✅ Successfully generated article for '{plant_names[0]}'")
            print(f"📂 Check the _posts directory for your new Jekyll article!")
        else:
            print(f"\n❌ Failed to generate article for '{plant_names[0]}'")
    else:
        # Multiple plants
        batch_generate_articles(plant_names)