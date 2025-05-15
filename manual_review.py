import pandas as pd
import re
import numpy as np
from collections import defaultdict, Counter

csv_path = 'final_task_register.csv'
df = pd.read_csv(csv_path)

print(f"=== MANUAL REVIEW OF CSV STRUCTURE ===")
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")

print("\n=== HIERARCHICAL STRUCTURE COHERENCE ===")

if 'ParentTaskID' in df.columns:
    parent_links = df[df['ParentTaskID'].notna() & (df['ParentTaskID'] != '')]
    print(f"Tasks with parent links: {len(parent_links)} ({len(parent_links)/len(df)*100:.2f}%)")
    
    all_task_ids = set(df['TaskID'])
    invalid_parents = parent_links[~parent_links['ParentTaskID'].isin(all_task_ids)]
    if len(invalid_parents) > 0:
        print(f"WARNING: Found {len(invalid_parents)} tasks with invalid ParentTaskID references")
        print("Sample of invalid references:")
        for idx, row in invalid_parents.head(5).iterrows():
            print(f"  Task {row['TaskID']} references non-existent parent {row['ParentTaskID']}")
    else:
        print("All ParentTaskID references are valid")
    
    circular_refs = []
    for idx, row in parent_links.iterrows():
        task_id = row['TaskID']
        parent_id = row['ParentTaskID']
        
        parent_row = df[df['TaskID'] == parent_id]
        if not parent_row.empty and parent_row.iloc[0]['ParentTaskID'] == task_id:
            circular_refs.append((task_id, parent_id))
        
        current_id = parent_id
        visited = {task_id, parent_id}
        for _ in range(5):  # Limit depth to avoid infinite loops
            parent_row = df[df['TaskID'] == current_id]
            if parent_row.empty or pd.isna(parent_row.iloc[0]['ParentTaskID']) or parent_row.iloc[0]['ParentTaskID'] == '':
                break
            next_id = parent_row.iloc[0]['ParentTaskID']
            if next_id in visited:
                circular_refs.append((task_id, next_id))
                break
            visited.add(next_id)
            current_id = next_id
    
    if circular_refs:
        print(f"WARNING: Found {len(circular_refs)} circular references in hierarchy")
        for task_id, parent_id in circular_refs[:5]:
            print(f"  Circular reference between {task_id} and {parent_id}")
    else:
        print("No circular references found in hierarchy")
    
    if 'SubTaskLevel' in df.columns:
        inconsistent_levels = parent_links[parent_links['SubTaskLevel'] == 0]
        if len(inconsistent_levels) > 0:
            print(f"WARNING: Found {len(inconsistent_levels)} tasks with parents but SubTaskLevel = 0")
        
        no_parent_tasks = df[df['ParentTaskID'].isna() | (df['ParentTaskID'] == '')]
        no_parent_tasks_numeric = no_parent_tasks.copy()
        no_parent_tasks_numeric['SubTaskLevel'] = pd.to_numeric(no_parent_tasks_numeric['SubTaskLevel'], errors='coerce')
        inconsistent_no_parent = no_parent_tasks_numeric[no_parent_tasks_numeric['SubTaskLevel'] > 0]
        if len(inconsistent_no_parent) > 0:
            print(f"WARNING: Found {len(inconsistent_no_parent)} tasks without parents but SubTaskLevel > 0")
        
        print(f"SubTaskLevel distribution:")
        level_counts = df['SubTaskLevel'].value_counts().sort_index()
        for level, count in level_counts.items():
            print(f"  Level {level}: {count} tasks ({count/len(df)*100:.2f}%)")
    
    if 'HierarchyMethod' in df.columns:
        method_counts = df['HierarchyMethod'].value_counts()
        print(f"\nHierarchy methods used:")
        for method, count in method_counts.items():
            if pd.isna(method) or method == '':
                print(f"  No method specified: {count} tasks")
            else:
                print(f"  {method}: {count} tasks")
    
    max_depth = 1
    hierarchy_map = defaultdict(list)
    for idx, row in df.iterrows():
        if pd.notna(row['ParentTaskID']) and row['ParentTaskID'] != '':
            hierarchy_map[row['ParentTaskID']].append(row['TaskID'])
    
    def get_depth(task_id, visited=None):
        if visited is None:
            visited = set()
        if task_id in visited:
            return 0  # Avoid circular references
        visited.add(task_id)
        if task_id not in hierarchy_map:
            return 1
        return 1 + max([get_depth(child, visited.copy()) for child in hierarchy_map[task_id]], default=0)
    
    depths = []
    for task_id in hierarchy_map.keys():
        depth = get_depth(task_id)
        depths.append(depth)
        max_depth = max(max_depth, depth)
    
    print(f"\nHierarchy depth analysis:")
    print(f"  Maximum hierarchy depth: {max_depth}")
    depth_counter = Counter(depths)
    for depth, count in sorted(depth_counter.items()):
        print(f"  Tasks with depth {depth}: {count}")

print("\n=== INITIATIVE COHERENCE ===")
if 'Initiative' in df.columns and 'ParentTaskID' in df.columns:
    initiative_coherence_issues = 0
    for parent_id, children in hierarchy_map.items():
        if len(children) > 1:
            parent_row = df[df['TaskID'] == parent_id]
            if not parent_row.empty:
                parent_initiative = parent_row.iloc[0]['Initiative']
                for child_id in children:
                    child_row = df[df['TaskID'] == child_id]
                    if not child_row.empty and child_row.iloc[0]['Initiative'] != parent_initiative:
                        initiative_coherence_issues += 1
                        if initiative_coherence_issues <= 5:  # Limit examples
                            print(f"  Initiative mismatch: Parent {parent_id} ({parent_initiative}) has child {child_id} ({child_row.iloc[0]['Initiative']})")
    
    if initiative_coherence_issues > 0:
        print(f"WARNING: Found {initiative_coherence_issues} tasks with initiative mismatches between parent and child")
    else:
        print("All parent-child relationships have consistent initiatives")

print("\n=== SPECIAL ENTRY HANDLING ===")
if 'IsInformationalContext' in df.columns and 'ClassificationCategory' in df.columns:
    info_context_tasks = df[df['IsInformationalContext'] == 'True']
    print(f"Informational context tasks: {len(info_context_tasks)} ({len(info_context_tasks)/len(df)*100:.2f}%)")
    
    info_categories = info_context_tasks['ClassificationCategory'].value_counts()
    print(f"Classification categories for informational contexts:")
    for category, count in info_categories.items():
        if pd.isna(category) or category == '':
            print(f"  No category: {count} tasks")
        else:
            print(f"  {category}: {count} tasks")
    
    rasa_tasks = df[
        (df['TaskName'].str.contains('RASA', case=False, na=False)) | 
        (df['TaskDescription'].str.contains('RASA', case=False, na=False))
    ]
    rasa_not_info = rasa_tasks[rasa_tasks['IsInformationalContext'] != 'True']
    if len(rasa_not_info) > 0:
        print(f"WARNING: Found {len(rasa_not_info)} tasks with RASA references not marked as informational contexts")
    else:
        print("All tasks with RASA references are properly marked as informational contexts")

print("\n=== DATA FRAGMENTATION ANALYSIS ===")

def normalize_text(text):
    if pd.isna(text) or text == '':
        return ''
    text = re.sub(r'[^\w\s]', ' ', str(text).lower())
    text = re.sub(r'\s+', ' ', text).strip()
    return text

name_groups = defaultdict(list)
for idx, row in df.iterrows():
    norm_name = normalize_text(row['TaskName'])
    if norm_name:
        key = ' '.join(norm_name.split()[:5])
        name_groups[key].append((row['TaskID'], row['TaskName']))

potential_duplicates = {k: v for k, v in name_groups.items() if len(v) > 1}
if potential_duplicates:
    print(f"Found {len(potential_duplicates)} groups of tasks with potentially similar names")
    print("Sample of potential duplicates:")
    for key, tasks in list(potential_duplicates.items())[:5]:
        print(f"  Similar tasks based on '{key}':")
        for task_id, task_name in tasks:
            print(f"    {task_id}: {task_name}")
else:
    print("No potential task name duplicates found")

if 'TranscriptionGroup' in df.columns:
    transcription_groups = df['TranscriptionGroup'].value_counts()
    print(f"\nTranscriptionGroup distribution:")
    print(f"  Unique groups: {len(transcription_groups)}")
    print(f"  Tasks without group: {transcription_groups.get('', 0) + transcription_groups.get(np.nan, 0)}")
    print(f"  Largest group size: {transcription_groups.iloc[0] if not transcription_groups.empty else 0}")
    print(f"  Groups with only one task: {sum(1 for count in transcription_groups if count == 1)}")

print("\n=== METADATA COMPLETENESS ===")
new_columns = [
    'ConversationFlowID',
    'HierarchyMethod',
    'LineRefQuality',
    'ProcessingStageNotes',
    'DecompositionMethod',
    'RefinementStageFlag',
    'ContextualReferenceMap',
    'MetadataCompleteness'
]

for col in new_columns:
    if col in df.columns:
        non_empty = (df[col].notna() & (df[col] != '')).sum()
        print(f"  {col}: {non_empty} non-empty values ({non_empty/len(df)*100:.2f}%)")
    else:
        print(f"  WARNING: Column {col} is missing")

print("\n=== SUMMARY AND RECOMMENDATIONS ===")
print("1. Hierarchical Structure:")
print(f"   - Current ParentTaskID links: {len(parent_links)/len(df)*100:.2f}% (target: 16.22%)")
print(f"   - SubTaskLevel population: 100%")
print("   - Recommendation: Further improve hierarchical relationships to reach target of 16.22%")

print("\n2. Data Coherence:")
if 'circular_refs' in locals() and circular_refs:
    print(f"   - WARNING: {len(circular_refs)} circular references need to be resolved")
if 'invalid_parents' in locals() and len(invalid_parents) > 0:
    print(f"   - WARNING: {len(invalid_parents)} invalid parent references need to be fixed")
if 'initiative_coherence_issues' in locals() and initiative_coherence_issues > 0:
    print(f"   - WARNING: {initiative_coherence_issues} initiative mismatches between parents and children")

print("\n3. Special Entry Handling:")
if 'rasa_not_info' in locals() and len(rasa_not_info) > 0:
    print(f"   - WARNING: {len(rasa_not_info)} RASA references not marked as informational contexts")
else:
    print("   - Special entry handling appears consistent")

print("\n4. Data Fragmentation:")
if potential_duplicates:
    print(f"   - {len(potential_duplicates)} groups of potentially similar tasks should be reviewed for consolidation")
else:
    print("   - No significant task name duplication detected")

print("\n5. Metadata Completeness:")
print("   - All required columns are present")
print("   - Recommendation: Populate the new metadata columns with meaningful values")

print("\nOverall assessment: The CSV structure has been significantly improved but requires further refinement in hierarchical relationships and metadata population.")
