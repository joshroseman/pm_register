import pandas as pd
import re
from collections import defaultdict
import os

csv_path = "final_task_register.csv"
df = pd.read_csv(csv_path)


def normalize_text(text):
    if pd.isna(text) or text == "":
        return ""
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


name_groups = defaultdict(list)
for idx, row in df.iterrows():
    task_name = row["TaskName"]
    if pd.isna(task_name) or task_name == "":
        continue

    normalized_name = normalize_text(task_name)
    key = " ".join(normalized_name.split()[:3])

    if key:
        name_groups[key].append((idx, row))

similar_groups = {k: v for k, v in name_groups.items() if len(v) >= 2}
print(f"Found {len(similar_groups)} groups of tasks with potentially similar names")

report_path = "similar_tasks_report.md"
with open(report_path, "w") as f:
    f.write("# Analysis of Similar Tasks\n\n")
    f.write(
        f"Found {len(similar_groups)} groups of tasks with potentially similar names.\n\n"
    )

    sorted_groups = sorted(
        similar_groups.items(), key=lambda x: len(x[1]), reverse=True
    )

    for i, (key, tasks) in enumerate(sorted_groups):
        first_task_name = tasks[0][1]["TaskName"]

        f.write(f"## Group {i+1}: {first_task_name} ({len(tasks)} tasks)\n\n")

        descriptions = [normalize_text(task[1]["TaskDescription"]) for task in tasks]
        identical_descriptions = len(set(descriptions)) == 1

        if identical_descriptions:
            f.write("**All tasks in this group have identical descriptions.**\n\n")
        else:
            f.write("**Tasks in this group have different descriptions.**\n\n")

        f.write(
            "| TaskID | TaskName | TaskDescription | Assignee | Initiative | ParentTaskID |\n"
        )
        f.write(
            "|--------|----------|----------------|----------|------------|-------------|\n"
        )

        for idx, task in tasks:
            task_id = task["TaskID"]
            task_name = task["TaskName"]
            description = str(task["TaskDescription"])
            if len(description) > 50:
                description = description[:47] + "..."
            description = description.replace("|", "\\|").replace("\n", " ")
            task_name = task_name.replace("|", "\\|").replace("\n", " ")

            assignee = task["Assignee"] if pd.notna(task["Assignee"]) else ""
            initiative = task["Initiative"] if pd.notna(task["Initiative"]) else ""
            parent_id = task["ParentTaskID"] if pd.notna(task["ParentTaskID"]) else ""

            f.write(
                f"| {task_id} | {task_name} | {description} | {assignee} | {initiative} | {parent_id} |\n"
            )

        f.write("\n")

review_tasks_key = next(
    (k for k, v in similar_groups.items() if "review and clarify" in k), None
)
if review_tasks_key:
    review_tasks = similar_groups[review_tasks_key]

    with open("review_tasks_analysis.md", "w") as f:
        f.write("# Analysis of 'Review and Clarify Task Requirements' Tasks\n\n")
        f.write(f"Found {len(review_tasks)} tasks with this name.\n\n")

        descriptions = [
            normalize_text(task[1]["TaskDescription"]) for task in review_tasks
        ]
        unique_descriptions = set(descriptions)

        f.write(f"Number of unique descriptions: {len(unique_descriptions)}\n\n")

        if len(unique_descriptions) == 1:
            f.write("**All tasks have identical descriptions.**\n\n")
            f.write(f"Description: {next(iter(unique_descriptions))}\n\n")
        else:
            f.write("**Tasks have different descriptions.**\n\n")
            f.write("### Sample of unique descriptions:\n\n")
            for i, desc in enumerate(list(unique_descriptions)[:5]):
                f.write(f"{i+1}. {desc}\n\n")

        parent_groups = defaultdict(list)
        for idx, task in review_tasks:
            parent_id = (
                task["ParentTaskID"] if pd.notna(task["ParentTaskID"]) else "None"
            )
            parent_groups[parent_id].append((idx, task))

        f.write(f"Tasks grouped by parent: {len(parent_groups)} different parents\n\n")

        initiative_groups = defaultdict(list)
        for idx, task in review_tasks:
            initiative = task["Initiative"] if pd.notna(task["Initiative"]) else "None"
            initiative_groups[initiative].append((idx, task))

        f.write("### Distribution by Initiative:\n\n")
        for initiative, tasks in sorted(
            initiative_groups.items(), key=lambda x: len(x[1]), reverse=True
        ):
            f.write(f"- {initiative}: {len(tasks)} tasks\n")

        f.write("\n### Recommendation:\n\n")
        if len(unique_descriptions) == 1:
            f.write(
                "Since all these tasks have identical names and descriptions, they can be consolidated. "
            )
            f.write(
                "Consider keeping one task per initiative and deleting the rest, or appending a [review/clarify] tag to parent tasks.\n\n"
            )
        else:
            f.write("These tasks have identical names but different descriptions. ")
            f.write(
                "Consider reviewing each description to determine if tasks can be consolidated by initiative or parent task.\n\n"
            )

print(f"Generated report at {report_path}")
print(
    f"Generated special analysis for 'review and clarify' tasks at review_tasks_analysis.md"
)
