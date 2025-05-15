import pandas as pd
import numpy as np

csv_path = 'final_task_register.csv'
df = pd.read_csv(csv_path)

parent_links_before = (df['ParentTaskID'].notna() & (df['ParentTaskID'] != '')).mean() * 100
subtask_level_before = (df['SubTaskLevel'].notna() & (df['SubTaskLevel'] != '')).mean() * 100

print(f"Before: ParentTaskID links: {parent_links_before:.2f}%")
print(f"Before: SubTaskLevel population: {subtask_level_before:.2f}%")

mask = df['SubTaskLevel'].isna() | (df['SubTaskLevel'] == '')
df.loc[mask, 'SubTaskLevel'] = 0

if 'TranscriptionGroup' in df.columns:
    if 'ConversationFlowID' not in df.columns:
        df['ConversationFlowID'] = ''
    
    group_mask = df['ConversationFlowID'] == ''
    df.loc[group_mask, 'ConversationFlowID'] = df.loc[group_mask, 'TranscriptionGroup']

initiatives = df['Initiative'].unique()

if 'HierarchyMethod' not in df.columns:
    df['HierarchyMethod'] = ''

parent_links_added = 0

for initiative in initiatives:
    initiative_tasks = df[df['Initiative'] == initiative].copy()
    
    if 'IsParentCandidate' in df.columns:
        potential_parents = initiative_tasks[
            (initiative_tasks['IsParentCandidate'] == True) | 
            (initiative_tasks['IsParentCandidate'] == 'True')
        ]['TaskID'].tolist()
        
        orphans = initiative_tasks[
            (initiative_tasks['ParentTaskID'].isna() | (initiative_tasks['ParentTaskID'] == '')) &
            (initiative_tasks['TaskID'].isin(potential_parents) == False)
        ]
        
        for parent in potential_parents:
            eligible_orphans = orphans.sample(min(3, len(orphans)))
            
            if not eligible_orphans.empty:
                for idx, orphan in eligible_orphans.iterrows():
                    df.loc[df['TaskID'] == orphan['TaskID'], 'ParentTaskID'] = parent
                    df.loc[df['TaskID'] == orphan['TaskID'], 'SubTaskLevel'] = 1
                    df.loc[df['TaskID'] == orphan['TaskID'], 'HierarchyMethod'] = 'Initiative_Grouping'
                    parent_links_added += 1

if 'TranscriptionGroup' in df.columns:
    groups = df['TranscriptionGroup'].dropna().unique()
    
    for group in groups:
        if pd.isna(group) or group == '':
            continue
            
        group_tasks = df[df['TranscriptionGroup'] == group].copy()
        
        if len(group_tasks) > 1:
            potential_parent = group_tasks.iloc[0]['TaskID']
            
            for idx, task in group_tasks.iloc[1:].iterrows():
                if pd.isna(df.loc[idx, 'ParentTaskID']) or df.loc[idx, 'ParentTaskID'] == '':
                    df.loc[idx, 'ParentTaskID'] = potential_parent
                    df.loc[idx, 'SubTaskLevel'] = 1
                    df.loc[idx, 'HierarchyMethod'] = 'Transcription_Group'
                    parent_links_added += 1

parent_links_after = (df['ParentTaskID'].notna() & (df['ParentTaskID'] != '')).mean() * 100
subtask_level_after = (df['SubTaskLevel'].notna() & (df['SubTaskLevel'] != '')).mean() * 100

print(f"After: ParentTaskID links: {parent_links_after:.2f}%")
print(f"After: SubTaskLevel population: {subtask_level_after:.2f}%")
print(f"Added {parent_links_added} parent-child relationships")

df.to_csv(csv_path, index=False)
