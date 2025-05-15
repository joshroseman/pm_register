import pandas as pd
import re
import os
import sys
from collections import defaultdict
from difflib import SequenceMatcher

dry_run = True  # Default to dry run mode
if len(sys.argv) > 1 and sys.argv[1] == "--apply":
    dry_run = False

csv_path = "final_task_register.csv"
if not dry_run:
    backup_path = f"{csv_path}.consolidation.bak"
    os.system(f"cp {csv_path} {backup_path}")
    print(f"Created backup at {backup_path}")

df = pd.read_csv(csv_path)
original_df = df.copy()


def normalize_text(text):
    if pd.isna(text) or text == "":
        return ""
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def similarity_ratio(text1, text2):
    if pd.isna(text1) or pd.isna(text2) or text1 == "" or text2 == "":
        return 0
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()


def evaluate_description(desc):
    if pd.isna(desc) or desc == "":
        return "empty", 0

    normalized = normalize_text(desc)

    non_informative_markers = [
        "insufficient automated qc",
        "unassigned",
        "insufficient",
    ]

    for marker in non_informative_markers:
        if marker in normalized:
            return "non_informative", 1

    if len(normalized.split()) < 5:
        return "minimal", 2

    context_markers = [
        "this",
        "specific",
        "should",
        "need",
        "must",
        "ensure",
        "verify",
        "implement",
        "develop",
        "create",
        "update",
        "modify",
        "review",
    ]

    context_score = sum(
        [1 for marker in context_markers if marker in normalized.split()]
    )

    if context_score >= 2:
        return "contextual", 4

    if len(normalized.split()) > 15:
        return "detailed", 3

    return "basic", 2


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

report_path = "contextual_consolidation_report.md"
with open(report_path, "w") as f:
    f.write("# Contextual Task Consolidation Report\n\n")
    f.write(
        f"Analysis of {len(similar_groups)} groups of similar tasks based on description content.\n\n"
    )

    tasks_to_delete = []
    tasks_to_rename = []

    sorted_groups = sorted(
        similar_groups.items(), key=lambda x: len(x[1]), reverse=True
    )

    for group_idx, (key, tasks) in enumerate(sorted_groups):
        first_task_name = tasks[0][1]["TaskName"]

        f.write(f"## Group {group_idx+1}: {first_task_name} ({len(tasks)} tasks)\n\n")

        task_analyses = []
        for idx, row in tasks:
            desc = row["TaskDescription"]
            desc_type, desc_score = evaluate_description(desc)

            parent_id = row["ParentTaskID"] if pd.notna(row["ParentTaskID"]) else "None"
            initiative = row["Initiative"] if pd.notna(row["Initiative"]) else "None"

            task_analyses.append(
                {
                    "idx": idx,
                    "task_id": row["TaskID"],
                    "desc": desc,
                    "desc_type": desc_type,
                    "desc_score": desc_score,
                    "parent_id": parent_id,
                    "initiative": initiative,
                }
            )

        non_informative = [
            t for t in task_analyses if t["desc_type"] in ["empty", "non_informative"]
        ]
        minimal = [t for t in task_analyses if t["desc_type"] == "minimal"]
        basic = [t for t in task_analyses if t["desc_type"] == "basic"]
        good_quality = [
            t for t in task_analyses if t["desc_type"] in ["contextual", "detailed"]
        ]

        f.write("### Analysis by Description Quality\n\n")
        f.write(f"- Non-informative descriptions: {len(non_informative)} tasks\n")
        f.write(f"- Minimal descriptions: {len(minimal)} tasks\n")
        f.write(f"- Basic descriptions: {len(basic)} tasks\n")
        f.write(f"- Good quality descriptions: {len(good_quality)} tasks\n\n")

        f.write("### Recommendations\n\n")

        if non_informative:
            f.write("#### Tasks to Delete (Non-informative descriptions)\n\n")
            f.write("| TaskID | TaskName | TaskDescription | Reason |\n")
            f.write("|--------|----------|----------------|--------|\n")

            for task in non_informative:
                desc_preview = (
                    str(task["desc"])[:50] + "..."
                    if len(str(task["desc"])) > 50
                    else task["desc"]
                )
                desc_preview = desc_preview.replace("|", "\\|").replace("\n", " ")

                f.write(
                    f"| {task['task_id']} | {first_task_name} | {desc_preview} | {task['desc_type']} |\n"
                )
                tasks_to_delete.append(task)

        if minimal and len(minimal) > 1:
            minimal_with_parent = [t for t in minimal if t["parent_id"] != "None"]

            if minimal_with_parent:
                keep = minimal_with_parent[0]
                delete = [t for t in minimal if t != keep]
            else:
                keep = minimal[0]
                delete = minimal[1:]

            if delete:
                f.write("\n#### Additional Tasks to Delete (Minimal descriptions)\n\n")
                f.write("| TaskID | TaskName | TaskDescription | Reason |\n")
                f.write("|--------|----------|----------------|--------|\n")

                for task in delete:
                    desc_preview = (
                        str(task["desc"])[:50] + "..."
                        if len(str(task["desc"])) > 50
                        else task["desc"]
                    )
                    desc_preview = desc_preview.replace("|", "\\|").replace("\n", " ")

                    f.write(
                        f"| {task['task_id']} | {first_task_name} | {desc_preview} | duplicate minimal description |\n"
                    )
                    tasks_to_delete.append(task)

        if good_quality:
            f.write("\n#### Tasks to Rename (Good quality descriptions)\n\n")
            f.write("| TaskID | Current Name | New Name | Description Preview |\n")
            f.write("|--------|--------------|----------|--------------------|\n")

            for task in good_quality:
                desc = str(task["desc"])

                words = normalize_text(desc).split()
                key_words = []

                for word in words[:10]:  # Look at just the first 10 words
                    if len(word) > 3 and word not in [
                        "this",
                        "that",
                        "with",
                        "from",
                        "have",
                        "been",
                    ]:
                        key_words.append(word)
                    if len(key_words) >= 2:
                        break

                key_phrase = " ".join(key_words).title() if key_words else "Specific"
                new_name = f"{first_task_name}: {key_phrase}"

                desc_preview = desc[:50] + "..." if len(desc) > 50 else desc
                desc_preview = desc_preview.replace("|", "\\|").replace("\n", " ")

                f.write(
                    f"| {task['task_id']} | {first_task_name} | {new_name} | {desc_preview} |\n"
                )

                tasks_to_rename.append(
                    {
                        "idx": task["idx"],
                        "task_id": task["task_id"],
                        "old_name": first_task_name,
                        "new_name": new_name,
                    }
                )

        if basic and len(basic) > 1:
            initiative_groups = defaultdict(list)
            for task in basic:
                initiative_groups[task["initiative"]].append(task)

            for initiative, init_tasks in initiative_groups.items():
                if len(init_tasks) > 1:
                    with_parent = [t for t in init_tasks if t["parent_id"] != "None"]

                    if with_parent:
                        keep = with_parent[0]
                        delete = [t for t in init_tasks if t != keep]
                    else:
                        keep = init_tasks[0]
                        delete = init_tasks[1:]

                    new_name = f"{first_task_name}: {initiative}"

                    tasks_to_rename.append(
                        {
                            "idx": keep["idx"],
                            "task_id": keep["task_id"],
                            "old_name": first_task_name,
                            "new_name": new_name,
                        }
                    )

                    if delete:
                        f.write(
                            f"\n#### Tasks to Delete (Redundant in {initiative} initiative)\n\n"
                        )
                        f.write("| TaskID | TaskName | TaskDescription | Reason |\n")
                        f.write("|--------|----------|----------------|--------|\n")

                        for task in delete:
                            desc_preview = (
                                str(task["desc"])[:50] + "..."
                                if len(str(task["desc"])) > 50
                                else task["desc"]
                            )
                            desc_preview = desc_preview.replace("|", "\\|").replace(
                                "\n", " "
                            )

                            f.write(
                                f"| {task['task_id']} | {first_task_name} | {desc_preview} | redundant basic description |\n"
                            )
                            tasks_to_delete.append(task)

        f.write("\n---\n\n")

    f.write("# Consolidation Summary\n\n")
    f.write(f"Total tasks to delete: {len(tasks_to_delete)}\n")
    f.write(f"Total tasks to rename: {len(tasks_to_rename)}\n\n")

    if tasks_to_delete:
        f.write("## All Tasks to Delete\n\n")
        f.write("| TaskID | Reason |\n")
        f.write("|--------|--------|\n")

        for task in tasks_to_delete:
            f.write(f"| {task['task_id']} | {task['desc_type']} description |\n")

    if tasks_to_rename:
        f.write("\n## All Tasks to Rename\n\n")
        f.write("| TaskID | Current Name | New Name |\n")
        f.write("|--------|--------------|----------|\n")

        for task in tasks_to_rename:
            f.write(
                f"| {task['task_id']} | {task['old_name']} | {task['new_name']} |\n"
            )

print(f"Generated consolidation report at {report_path}")

if not dry_run:
    print("\nApplying changes...")

    for task in tasks_to_delete:
        df = df.drop(task["idx"])

    for task in tasks_to_rename:
        df.loc[task["idx"], "TaskName"] = task["new_name"]

    df = df.reset_index(drop=True)

    df.to_csv(csv_path, index=False)

    print(f"Changes applied to {csv_path}")
    print(f"Deleted {len(tasks_to_delete)} tasks")
    print(f"Renamed {len(tasks_to_rename)} tasks")
else:
    print("\nThis was a dry run. To apply changes, run:")
    print("python contextual_consolidation.py --apply")
