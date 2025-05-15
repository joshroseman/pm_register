import pandas as pd
import re
import os
from datetime import datetime

csv_path = 'final_task_register.csv'
backup_path = f'{csv_path}.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak'
os.system(f'cp {csv_path} {backup_path}')
print(f"Created backup at {backup_path}")

df = pd.read_csv(csv_path)
original_count = len(df)
print(f"Original task count: {original_count}")

def normalize_text(text):
    if pd.isna(text) or text == '':
        return ''
    text = re.sub(r'[^\w\s]', ' ', str(text).lower())
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def has_non_informative_description(row):
    if pd.isna(row['TaskDescription']) or row['TaskDescription'] == '':
        return True
        
    desc = str(row['TaskDescription']).lower().strip()
    
    non_informative_patterns = [
        r'^insufficient automated qc\.?$',
        r'^unassigned$',
        r'^this task involves.*$',
        r'^$',
        r'^unknown$',
        r'^none$',
        r'^no description$',
        r'^to be determined$',
        r'^tbd$'
    ]
    
    return any(re.match(pattern, desc) for pattern in non_informative_patterns)

def has_rich_description(row):
    if pd.isna(row['TaskDescription']) or row['TaskDescription'] == '':
        return False
        
    desc = str(row['TaskDescription']).strip()
    
    if len(desc) < 30:
        return False
        
    if '.' in desc or ',' in desc or ':' in desc or ';' in desc:
        return True
        
    detail_keywords = ['specifically', 'detailed', 'process', 'steps', 'requirements', 'implementation']
    if any(keyword in desc.lower() for keyword in detail_keywords):
        return True
        
    return False

def differentiate_task_name(row, base_name):
    if pd.isna(row['TaskDescription']) or row['TaskDescription'] == '':
        if pd.notna(row['Initiative']) and row['Initiative'] != '':
            return f"{base_name}: {row['Initiative']}"
        else:
            return base_name
    
    desc = str(row['TaskDescription'])
    
    words = desc.split()
    if len(words) > 5:
        suffix = ' '.join(words[:5])
        if len(suffix) > 30:
            suffix = suffix[:27] + "..."
    else:
        suffix = desc
        if len(suffix) > 30:
            suffix = suffix[:27] + "..."
    
    if pd.notna(row['Initiative']) and row['Initiative'] != '':
        return f"{base_name}: {suffix} ({row['Initiative']})"
    else:
        return f"{base_name}: {suffix}"

name_groups = {}
for idx, row in df.iterrows():
    if pd.isna(row['TaskName']) or row['TaskName'] == '':
        continue
        
    name = normalize_text(row['TaskName'])
    
    if len(name) < 3:
        continue
        
    if re.match(r'^review and clarify', name):
        key = name
    elif re.match(r'^address task: address:', name):
        key = re.sub(r'^address task: address:', 'address:', name)
    elif re.match(r'^address - part \d+:', name):
        key = re.sub(r'^address - part \d+:', 'address part:', name)
    else:
        words = name.split()
        if len(words) > 5:
            key = ' '.join(words[:5])
        else:
            key = name
    
    if key not in name_groups:
        name_groups[key] = []
    name_groups[key].append((idx, row))

tasks_to_delete = []
tasks_to_rename = []

for key, tasks in name_groups.items():
    if len(tasks) < 2:
        continue
        
    print(f"Processing group: {key} ({len(tasks)} tasks)")
    
    descriptions = [normalize_text(row['TaskDescription']) for _, row in tasks]
    all_identical = len(set(descriptions)) == 1
    
    if all_identical:
        tasks.sort(key=lambda x: x[1]['TaskID'])
        
        keep_idx, keep_row = tasks[0]
        
        for idx, row in tasks[1:]:
            children = df[df['ParentTaskID'] == row['TaskID']]
            for child_idx, child_row in children.iterrows():
                df.at[child_idx, 'ParentTaskID'] = keep_row['TaskID']
                
            tasks_to_delete.append((idx, row['TaskID'], key))
    else:
        
        non_informative = [(idx, row) for idx, row in tasks if has_non_informative_description(row)]
        
        rich_desc = [(idx, row) for idx, row in tasks if has_rich_description(row)]
        
        basic_desc = [(idx, row) for idx, row in tasks 
                     if not has_non_informative_description(row) and not has_rich_description(row)]
        
        for idx, row in non_informative:
            children = df[df['ParentTaskID'] == row['TaskID']]
            if not children.empty:
                if rich_desc:
                    new_parent_id = rich_desc[0][1]['TaskID']
                    for child_idx, child_row in children.iterrows():
                        df.at[child_idx, 'ParentTaskID'] = new_parent_id
                elif basic_desc:
                    new_parent_id = basic_desc[0][1]['TaskID']
                    for child_idx, child_row in children.iterrows():
                        df.at[child_idx, 'ParentTaskID'] = new_parent_id
            
            tasks_to_delete.append((idx, row['TaskID'], key))
        
        base_name = tasks[0][1]['TaskName']
        for idx, row in rich_desc:
            new_name = differentiate_task_name(row, base_name)
            tasks_to_rename.append((idx, row['TaskID'], row['TaskName'], new_name))
            df.at[idx, 'TaskName'] = new_name
        
        initiative_groups = {}
        for idx, row in basic_desc:
            initiative = row['Initiative'] if pd.notna(row['Initiative']) else 'Unknown'
            if initiative not in initiative_groups:
                initiative_groups[initiative] = []
            initiative_groups[initiative].append((idx, row))
        
        for initiative, init_tasks in initiative_groups.items():
            if len(init_tasks) == 1:
                idx, row = init_tasks[0]
                new_name = differentiate_task_name(row, base_name)
                tasks_to_rename.append((idx, row['TaskID'], row['TaskName'], new_name))
                df.at[idx, 'TaskName'] = new_name
            else:
                init_tasks.sort(key=lambda x: x[1]['TaskID'])
                keep_idx, keep_row = init_tasks[0]
                
                new_name = differentiate_task_name(keep_row, base_name)
                tasks_to_rename.append((keep_idx, keep_row['TaskID'], keep_row['TaskName'], new_name))
                df.at[keep_idx, 'TaskName'] = new_name
                
                for idx, row in init_tasks[1:]:
                    children = df[df['ParentTaskID'] == row['TaskID']]
                    for child_idx, child_row in children.iterrows():
                        df.at[child_idx, 'ParentTaskID'] = keep_row['TaskID']
                        
                    tasks_to_delete.append((idx, row['TaskID'], key))

rows_to_drop = [idx for idx, _, _ in tasks_to_delete]
df_filtered = df.drop(rows_to_drop)

df_filtered.to_csv(csv_path, index=False)
new_count = len(df_filtered)
print(f"Deleted {len(tasks_to_delete)} tasks")
print(f"Renamed {len(tasks_to_rename)} tasks")
print(f"New task count: {new_count}")

report_path = 'task_consolidation_report.md'
with open(report_path, 'w') as f:
    f.write("# Task Consolidation Report\n\n")
    
    f.write("## Summary\n\n")
    f.write(f"Original task count: {original_count}\n")
    f.write(f"Tasks deleted: {len(tasks_to_delete)}\n")
    f.write(f"Tasks renamed: {len(tasks_to_rename)}\n")
    f.write(f"New task count: {new_count}\n\n")
    
    f.write("## Deleted Tasks\n\n")
    if tasks_to_delete:
        f.write("| TaskID | Original Name | Group |\n")
        f.write("|--------|--------------|-------|\n")
        
        for _, task_id, group in tasks_to_delete[:20]:  # Show first 20 for brevity
            task_row = df.loc[df['TaskID'] == task_id].iloc[0]
            task_name = str(task_row['TaskName']).replace('|', '\\|')
            if len(task_name) > 50:
                task_name = task_name[:47] + "..."
            
            f.write(f"| {task_id} | {task_name} | {group} |\n")
        
        if len(tasks_to_delete) > 20:
            f.write(f"\n*...and {len(tasks_to_delete) - 20} more tasks*\n")
    
    f.write("\n## Renamed Tasks\n\n")
    if tasks_to_rename:
        f.write("| TaskID | Original Name | New Name |\n")
        f.write("|--------|--------------|----------|\n")
        
        for _, task_id, old_name, new_name in tasks_to_rename[:20]:  # Show first 20 for brevity
            old_name = str(old_name).replace('|', '\\|')
            new_name = str(new_name).replace('|', '\\|')
            
            if len(old_name) > 30:
                old_name = old_name[:27] + "..."
            if len(new_name) > 30:
                new_name = new_name[:27] + "..."
            
            f.write(f"| {task_id} | {old_name} | {new_name} |\n")
        
        if len(tasks_to_rename) > 20:
            f.write(f"\n*...and {len(tasks_to_rename) - 20} more tasks*\n")
    
    f.write("\n## Consolidation Approach\n\n")
    f.write("1. **Tasks with Identical Descriptions**: Kept one task and deleted the rest\n")
    f.write("2. **Tasks with Non-Informative Descriptions**: Deleted these tasks\n")
    f.write("3. **Tasks with Rich Descriptions**: Renamed to differentiate based on content\n")
    f.write("4. **Tasks with Basic Descriptions**: Consolidated by initiative, keeping one task per initiative\n")
    f.write("5. **Parent-Child Relationships**: Preserved by updating ParentTaskID references\n")

print(f"Generated report at {report_path}")
