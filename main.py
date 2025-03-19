import os
import logging
from dotenv import load_dotenv
from src.repurposer import ContentRepurposer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Repurpose content from a URL.')
    parser.add_argument('url', help='URL to fetch content from')
    parser.add_argument('--types', nargs='+', default=['linkedin', 'twitter', 'email', 'thought_leadership'],
                        help='Content types to generate (linkedin, twitter, email, thought_leadership)')
    
    args = parser.parse_args()
    
    repurposer = ContentRepurposer()
    results = repurposer.repurpose(args.url, args.types)
    
    for content_type, content in results.items():
        print(f"\n--- {content_type.upper()} CONTENT ---\n")
        print(content)
        print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    main()