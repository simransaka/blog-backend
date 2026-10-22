import argparse

from src.config import setup_logging
from src.graph.graph import blog


def main() -> None:
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Generate a blog post on a given topic"
    )
    parser.add_argument(
        "topic",
        help="Topic to write the blog content"
    )

    args = parser.parse_args()

    out = blog.invoke({
        "topic": args.topic,
        "sections": [],
        "web_search_count": 0,
        "research_steps": 0,
        "fetch_count": 0,
        "evidence": [],
    })

    print(out.get("final", ""))

if __name__ == "__main__":
    main()