import pandas as pd
import re
import os
from datetime import datetime

csv_path = "final_task_register.csv"
backup_path = f'{csv_path}.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak'
os.system(f"cp {csv_path} {backup_path}")
print(f"Created backup at {backup_path}")

df = pd.read_csv(csv_path)
original_count = len(df)
print(f"Original task count: {original_count}")

tasks_with_parents = df[df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")].shape[
    0
]
current_percentage = tasks_with_parents / len(df) * 100
target_percentage = 16.22
additional_links_needed = int((target_percentage / 100 * len(df)) - tasks_with_parents)

print(f"Current ParentTaskID links: {tasks_with_parents} ({current_percentage:.2f}%)")
print(f"Target ParentTaskID links: {target_percentage:.2f}%")
print(f"Additional links needed: {additional_links_needed}")

valid_task_ids = set(df["TaskID"].dropna().unique())


def normalize_text(text):
    if pd.isna(text) or text == "":
        return ""
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


new_relationships = []
task_name_prefixes = {}

for idx, row in df.iterrows():
    if pd.isna(row["TaskName"]) or row["TaskName"] == "":
        continue

    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] != "":
        continue

    name = normalize_text(row["TaskName"])
    words = name.split()

    if len(words) >= 3:
        prefix_3 = " ".join(words[:3])
        if prefix_3 not in task_name_prefixes:
            task_name_prefixes[prefix_3] = []
        task_name_prefixes[prefix_3].append((idx, row))

    if len(words) >= 4:
        prefix_4 = " ".join(words[:4])
        if prefix_4 not in task_name_prefixes:
            task_name_prefixes[prefix_4] = []
        task_name_prefixes[prefix_4].append((idx, row))

    if len(words) >= 5:
        prefix_5 = " ".join(words[:5])
        if prefix_5 not in task_name_prefixes:
            task_name_prefixes[prefix_5] = []
        task_name_prefixes[prefix_5].append((idx, row))

for prefix, tasks in task_name_prefixes.items():
    if len(tasks) < 2:
        continue

    tasks.sort(key=lambda x: x[1]["TaskID"])

    p_idx, p_row = tasks[0]
    p_id = p_row["TaskID"]

    has_children = p_id in df["ParentTaskID"].dropna().values

    if not has_children:
        for c_idx, c_row in tasks[1:]:
            if p_id == c_row["TaskID"]:
                continue

            if pd.notna(c_row["ParentTaskID"]) and c_row["ParentTaskID"] != "":
                continue

            new_relationships.append((p_id, c_row["TaskID"], c_idx, "Name_Prefix"))

initiative_assignee_groups = {}
for idx, row in df.iterrows():
    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] != "":
        continue

    initiative = row["Initiative"] if pd.notna(row["Initiative"]) else "Unknown"
    assignee = row["Assignee"] if pd.notna(row["Assignee"]) else "Unknown"

    key = f"{initiative}|{assignee}"
    if key not in initiative_assignee_groups:
        initiative_assignee_groups[key] = []
    initiative_assignee_groups[key].append((idx, row))

for key, tasks in initiative_assignee_groups.items():
    if len(tasks) < 2:
        continue

    tasks.sort(key=lambda x: x[1]["TaskID"])

    p_idx, p_row = tasks[0]
    p_id = p_row["TaskID"]

    has_children = p_id in df["ParentTaskID"].dropna().values

    if not has_children:
        for c_idx, c_row in tasks[1:]:
            if p_id == c_row["TaskID"]:
                continue

            if pd.notna(c_row["ParentTaskID"]) and c_row["ParentTaskID"] != "":
                continue

            p_name = normalize_text(p_row["TaskName"])
            c_name = normalize_text(c_row["TaskName"])

            p_desc = (
                normalize_text(p_row["TaskDescription"])
                if pd.notna(p_row["TaskDescription"])
                else ""
            )
            c_desc = (
                normalize_text(c_row["TaskDescription"])
                if pd.notna(c_row["TaskDescription"])
                else ""
            )

            if (
                p_name
                and c_name
                and (
                    p_name in c_name
                    or c_name in p_name
                    or any(word in c_name for word in p_name.split() if len(word) > 3)
                )
            ) or (
                p_desc
                and c_desc
                and (
                    p_desc in c_desc
                    or c_desc in p_desc
                    or any(word in c_desc for word in p_desc.split() if len(word) > 3)
                )
            ):
                new_relationships.append(
                    (p_id, c_row["TaskID"], c_idx, "Initiative_Assignee")
                )

keyword_groups = {}
important_keywords = [
    "studio",
    "maintenance",
    "retail",
    "cafe",
    "finance",
    "admin",
    "task",
    "management",
    "system",
    "integration",
    "development",
    "facility",
    "organizational",
    "meta",
    "coordination",
    "rasa",
    "field",
    "memory",
    "weatherstone",
    "rhythm",
    "modeling",
    "export",
    "import",
    "booking",
    "marketing",
    "business",
    "program",
    "symbolic",
    "structure",
]

for idx, row in df.iterrows():
    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] != "":
        continue

    if pd.isna(row["TaskDescription"]) or row["TaskDescription"] == "":
        continue

    desc = normalize_text(row["TaskDescription"])

    for keyword in important_keywords:
        if keyword in desc:
            if keyword not in keyword_groups:
                keyword_groups[keyword] = []
            keyword_groups[keyword].append((idx, row))

for keyword, tasks in keyword_groups.items():
    if len(tasks) < 2:
        continue

    tasks.sort(key=lambda x: x[1]["TaskID"])

    p_idx, p_row = tasks[0]
    p_id = p_row["TaskID"]

    has_children = p_id in df["ParentTaskID"].dropna().values

    if not has_children:
        for c_idx, c_row in tasks[1:]:
            if p_id == c_row["TaskID"]:
                continue

            if pd.notna(c_row["ParentTaskID"]) and c_row["ParentTaskID"] != "":
                continue

            new_relationships.append((p_id, c_row["TaskID"], c_idx, "Keyword"))

unique_relationships = []
seen = set()
for parent_id, child_id, child_idx, method in new_relationships:
    if (parent_id, child_id) not in seen:
        seen.add((parent_id, child_id))
        unique_relationships.append((parent_id, child_id, child_idx, method))

new_relationships = unique_relationships

if len(new_relationships) > additional_links_needed:
    name_prefix_relationships = [r for r in new_relationships if r[3] == "Name_Prefix"]
    initiative_assignee_relationships = [
        r for r in new_relationships if r[3] == "Initiative_Assignee"
    ]
    keyword_relationships = [r for r in new_relationships if r[3] == "Keyword"]

    prioritized_relationships = (
        name_prefix_relationships
        + initiative_assignee_relationships
        + keyword_relationships
    )
    new_relationships = prioritized_relationships[:additional_links_needed]

print(f"Found {len(new_relationships)} potential new parent-child relationships")

relationships_added = 0
for parent_id, child_id, child_idx, method in new_relationships:
    parent_row = df[df["TaskID"] == parent_id].iloc[0]
    if pd.notna(parent_row["ParentTaskID"]) and parent_row["ParentTaskID"] == child_id:
        print(f"  Skipping circular reference: {parent_id} <-> {child_id}")
        continue

    df.at[child_idx, "ParentTaskID"] = parent_id
    df.at[child_idx, "SubTaskLevel"] = 1

    df.at[child_idx, "HierarchyMethod"] = method

    relationships_added += 1

print(f"Added {relationships_added} new parent-child relationships")

tasks_with_parents = df[df["ParentTaskID"].notna() & (df["ParentTaskID"] != "")].shape[
    0
]
final_percentage = tasks_with_parents / len(df) * 100

print(f"Final ParentTaskID links: {tasks_with_parents} ({final_percentage:.2f}%)")

df.to_csv(csv_path, index=False)

report_path = "hierarchy_improvement_report.md"
with open(report_path, "w") as f:
    f.write("# Hierarchical Structure Improvement Report\n\n")

    f.write("## Hierarchical Structure Improvement\n\n")
    f.write(
        f"Initial ParentTaskID links: {tasks_with_parents - relationships_added} ({(tasks_with_parents - relationships_added) / len(df) * 100:.2f}%)\n\n"
    )
    f.write(f"Added {relationships_added} new parent-child relationships:\n\n")

    if new_relationships:
        f.write("| Parent TaskID | Child TaskID | Method |\n")
        f.write("|--------------|-------------|--------|\n")

        for parent_id, child_id, _, method in new_relationships[
            :20
        ]:  # Show first 20 for brevity
            f.write(f"| {parent_id} | {child_id} | {method} |\n")

        if len(new_relationships) > 20:
            f.write(f"\n*...and {len(new_relationships) - 20} more relationships*\n")

    f.write(
        f"\nFinal ParentTaskID links: {tasks_with_parents} ({final_percentage:.2f}%)\n"
    )
    f.write(f"Target percentage: {target_percentage:.2f}%\n")

    f.write("\n## Relationship Methods Explanation\n\n")
    f.write("1. **Name_Prefix**: Tasks with similar prefixes in their names\n")
    f.write(
        "2. **Initiative_Assignee**: Tasks with the same initiative and assignee, and some similarity in names or descriptions\n"
    )
    f.write(
        "3. **Keyword**: Tasks with similar important keywords in their descriptions\n"
    )

print(f"Generated report at {report_path}")
