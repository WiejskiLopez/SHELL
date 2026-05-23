def build_frontmatter(content: str, source: str, target: str, timestamp: str, task_id: str) -> str:
    """Prepend YAML frontmatter block to content."""
    frontmatter = (
        f"---\n"
        f"source: {source}\n"
        f"target: {target}\n"
        f"timestamp: {timestamp}\n"
        f"task_id: {task_id}\n"
        f"---\n\n"
    )
    return frontmatter + content
