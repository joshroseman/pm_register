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


def is_pm_aggregation_task(row):
    name_patterns = [
        r"aggregate\s+tasks",
        r"task\s+aggregation",
        r"collect\s+tasks",
        r"compile\s+tasks",
        r"gather\s+tasks",
        r"task\s+collection",
        r"task\s+compilation",
        r"task\s+gathering",
        r"task\s+management\s+process",
        r"pm\s+process",
        r"project\s+management\s+process",
        r"meta.?task",
        r"recursive\s+task",
        r"task\s+about\s+tasks",
    ]

    if any(
        re.search(pattern, str(row["TaskName"]).lower()) for pattern in name_patterns
    ):
        return True

    desc_patterns = [
        r"recursive\s+process\s+of\s+project\s+management",
        r"task\s+aggregation",
        r"meta.?task",
        r"task\s+about\s+managing\s+tasks",
        r"not\s+an\s+operational\s+objective",
        r"no\s+operational\s+objective",
        r"task\s+management\s+process\s+only",
        r"only\s+about\s+task\s+management",
        r"self.referential",
        r"self.reference",
        r"recursive\s+reference",
    ]

    if any(
        re.search(pattern, str(row["TaskDescription"]).lower())
        for pattern in desc_patterns
    ):
        return True

    if pd.isna(row["TaskDescription"]) or str(row["TaskDescription"]).strip() == "":
        if pd.isna(row["TaskName"]) or len(str(row["TaskName"]).strip()) < 10:
            return True

    return False


def is_mtap_rasa_params_task(row):
    name_patterns = [
        r"mtap\s+parameter",
        r"rasa\s+parameter",
        r"mtap\s+config",
        r"rasa\s+config",
        r"mtap\s+setting",
        r"rasa\s+setting",
        r"configure\s+mtap",
        r"configure\s+rasa",
        r"mtap\s+configuration",
        r"rasa\s+configuration",
        r"manage\s+mtap",
        r"manage\s+rasa",
        r"mtap\s+management",
        r"rasa\s+management",
    ]

    if any(
        re.search(pattern, str(row["TaskName"]).lower()) for pattern in name_patterns
    ):
        return True

    desc_patterns = [
        r"mtap\s+parameter",
        r"rasa\s+parameter",
        r"mtap\s+config",
        r"rasa\s+config",
        r"mtap\s+setting",
        r"rasa\s+setting",
        r"configure\s+mtap",
        r"configure\s+rasa",
        r"mtap\s+configuration",
        r"rasa\s+configuration",
        r"manage\s+mtap",
        r"manage\s+rasa",
        r"mtap\s+management",
        r"rasa\s+management",
        r"only\s+about\s+mtap",
        r"only\s+about\s+rasa",
        r"mtap\s+only",
        r"rasa\s+only",
    ]

    if any(
        re.search(pattern, str(row["TaskDescription"]).lower())
        for pattern in desc_patterns
    ):
        return True

    if (
        ("RASA" in str(row["TaskName"]) or "RASA" in str(row["TaskDescription"]))
        and (
            "symbolic" in str(row["TaskName"]).lower()
            or "symbolic" in str(row["TaskDescription"]).lower()
        )
        and (
            "parameter" in str(row["TaskName"]).lower()
            or "parameter" in str(row["TaskDescription"]).lower()
        )
    ):
        return True

    return False


report_path = "removed_tasks_report.md"
with open(report_path, "w") as f:
    f.write("# Removed Non-Operational Tasks Report\n\n")

    pm_aggregation_tasks = df[df.apply(is_pm_aggregation_task, axis=1)]
    f.write(f"## Tasks Without Operational Objectives (PM Task Aggregation)\n\n")
    f.write(
        f"Found {len(pm_aggregation_tasks)} tasks that refer to PM task aggregation rather than actual operational objectives.\n\n"
    )

    if not pm_aggregation_tasks.empty:
        f.write("| TaskID | TaskName | TaskDescription |\n")
        f.write("|--------|----------|----------------|\n")

        for idx, row in pm_aggregation_tasks.iterrows():
            task_id = row["TaskID"]
            task_name = str(row["TaskName"]).replace("|", "\\|").replace("\n", " ")
            desc = str(row["TaskDescription"]).replace("|", "\\|").replace("\n", " ")
            if len(desc) > 50:
                desc = desc[:47] + "..."

            f.write(f"| {task_id} | {task_name} | {desc} |\n")

    mtap_rasa_tasks = df[df.apply(is_mtap_rasa_params_task, axis=1)]
    f.write(f"\n\n## Tasks Specifically About Managing MTAP or RASA Parameters\n\n")
    f.write(
        f"Found {len(mtap_rasa_tasks)} tasks that are specifically about managing MTAP or RASA parameters.\n\n"
    )

    if not mtap_rasa_tasks.empty:
        f.write("| TaskID | TaskName | TaskDescription |\n")
        f.write("|--------|----------|----------------|\n")

        for idx, row in mtap_rasa_tasks.iterrows():
            task_id = row["TaskID"]
            task_name = str(row["TaskName"]).replace("|", "\\|").replace("\n", " ")
            desc = str(row["TaskDescription"]).replace("|", "\\|").replace("\n", " ")
            if len(desc) > 50:
                desc = desc[:47] + "..."

            f.write(f"| {task_id} | {task_name} | {desc} |\n")

    tasks_to_remove = pd.concat(
        [pm_aggregation_tasks, mtap_rasa_tasks]
    ).drop_duplicates()
    f.write(f"\n\n## Summary\n\n")
    f.write(f"Total tasks to remove: {len(tasks_to_remove)}\n")
    f.write(f"- PM Task Aggregation: {len(pm_aggregation_tasks)}\n")
    f.write(f"- MTAP/RASA Parameters: {len(mtap_rasa_tasks)}\n")
    f.write(
        f"- Overlap (in both categories): {len(pm_aggregation_tasks) + len(mtap_rasa_tasks) - len(tasks_to_remove)}\n"
    )

tasks_to_remove_ids = set(tasks_to_remove["TaskID"])
df_filtered = df[~df["TaskID"].isin(tasks_to_remove_ids)]

for idx, row in df_filtered.iterrows():
    if pd.notna(row["ParentTaskID"]) and row["ParentTaskID"] in tasks_to_remove_ids:
        df_filtered.at[idx, "ParentTaskID"] = ""

df_filtered.to_csv(csv_path, index=False)
print(f"Removed {len(tasks_to_remove)} tasks from the CSV")
print(f"New task count: {len(df_filtered)}")
print(f"Generated report at {report_path}")
