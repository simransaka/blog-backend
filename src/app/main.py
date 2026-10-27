import argparse

from langgraph.types import Command

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

    config = {
        "configurable": {
            "thread_id": "blog-1"
        }
    }

    out = blog.invoke(
        {
            "topic": args.topic,
            "sections": [],
            "web_search_count": 0,
            "research_steps": 0,
            "fetch_count": 0,
            "evidence": [],
        },
        config=config
    )

    while "__interrupt__" in out:
        print("\n---HUMAN REVIEW REQUIRED---")
        print(out["__interrupt__"][0].value)

        decision = input(
            "\nChoose approve, reject, or edit - "
        ).strip().lower()

        if decision not in {"approve", "reject", "edit"}:
            print("Invalid choice . Please try again.")

        out = blog.invoke(
            Command(resume={"review": decision}),
            config=config
        )

    print("\n--- GENERATED BLOG ---")
    print(out.get("final", ""))

if __name__ == "__main__":
    main()