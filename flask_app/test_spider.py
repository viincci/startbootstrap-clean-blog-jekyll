"""
Test the research spider functionality
"""
import sys
import os
import json
from pathlib import Path

# Add the parent directory to the Python path so we can import from research_v2
sys.path.append(str(Path(__file__).parent))
from research_v2.spider import research_plant

def test_research():
    """Test researching different plants"""
    test_plants = [
        "King Protea",
        "Bird of Paradise",
        "Aloe Ferox"
    ]
    
    for plant in test_plants:
        print(f"\n{'='*80}\nTesting research for: {plant}\n{'='*80}")
        results = research_plant(plant)
        
        # Print summary of results
        print(f"\nFound {len(results)} sources:")
        for result in results:
            print(f"\n- Source: {result['source']}")
            print(f"  Type: {result['type']}")
            print(f"  URL: {result['url']}")
            print(f"  Content length: {len(result['content'])} characters")
            # Print first 100 characters of content as preview
            preview = result['content'][:100].replace('\n', ' ').strip()
            print(f"  Preview: {preview}...")
        
        print("\nResults saved to research_results.json")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    test_research()