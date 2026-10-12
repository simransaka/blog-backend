from src.graph.graph import blog

if __name__ == "__main__":
    out = blog.invoke({
        "topic": "Write a blog on new discoveries in science in September 2026",
        "sections": [],
    })
    print(out.get("final", ""))