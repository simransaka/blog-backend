import logging
import json

from src.models import Plan, Task

logger = logging.getLogger(__name__)

def edit_plan(plan: Plan) -> Plan:
    logger.info("Edit blog plan")

    print("\n---EDIT BLOG PLAN---")
    print("Simply press enter to keep the current value else write the updated value and then press enter")

    user_blog_title = input(
        f"Blog title [{plan.blog_title}]: "
    ).strip()

    user_audience = input(
        f"Audience [{plan.audience}]: "
    ).strip()

    user_tone = input(
        f"Tone [{plan.tone}]: "
    ).strip()

    user_blog_kind = input(
        f"Blog kind [{plan.blog_kind}]: "
    ).strip()

    user_constraints = input(
        f"Contraints [{plan.constraints}]: "
    ).strip()

    user_tasks = []

    print("\nCurrent tasks")
    for task in plan.tasks:
        print(
            f"Task ID - {task.id}\n"
        )

        user_title = input(
            f"Title [{task.title}]: "
        ).strip()

        user_goal = input(
           f"Goal [{task.goal}]: "
        ).strip()

        print(f"Bullets [{task.bullets}]:")
        user_bullets = input(
            "Enter new bullets separated by |"
        ).strip()

        user_target_words = input(
            f"Target Words [{task.target_words}]: "
        ).strip()

        user_tags = input(
            f"Tags [{task.tags}]: "
        ).strip()

        edited_task = task.model_dump()
        
        if user_title:
            edited_task["title"] = user_title
    
        if user_goal:
            edited_task["goal"] = user_goal
    
        if user_bullets:
            edited_task["bullets"] = [
                bullet.strip()
                for bullet in user_bullets.split("|")
                if bullet.strip()
            ]
    
        if user_target_words:
            try:
                edited_task["target_words"] = int(user_target_words)
            except ValueError:
                print("Invalid target words. Keeping the original value.")
    
        if user_tags:
            edited_task["tags"] = [
                tag.strip()
                for tag in user_tags.split(",")
                if tag.strip()
            ]

        # Validate the updated plan using the Pydantic schema
        edited_task = Task.model_validate(edited_task)
        user_tasks.append(edited_task)

    # keep the existing values when user presses Enter
    edited_plan = plan.model_dump()

    if user_blog_title:
        edited_plan["blog_title"] = user_blog_title

    if user_audience:
        edited_plan["audience"] = user_audience

    if user_tone:
        edited_plan["tone"] = user_tone

    if user_blog_kind:
        edited_plan["blog_kind"] = user_blog_kind

    if user_constraints:
        edited_plan["constraints"] = user_constraints

    if user_tasks:
        edited_plan["tasks"] = user_tasks

    # Validate the updated plan using the Pydantic schema
    edited_plan = Plan.model_validate(edited_plan)

    logger.info("Plan updated successfully.")

    return edited_plan