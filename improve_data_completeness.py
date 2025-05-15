import pandas as pd

csv_path = 'final_task_register.csv'
df = pd.read_csv(csv_path)

key_fields = [
    'TaskName', 
    'TaskDescription', 
    'Assignee', 
    'Status', 
    'ClassificationCategory', 
    'IsInformationalContext', 
    'TranscriptionMatchNotes'
]

before_counts = {}
for field in key_fields:
    if field in df.columns:
        missing = (df[field].isna() | (df[field] == '')).sum()
        before_counts[field] = missing
        print(f"Before: {field} has {missing} missing values")

changes = 0

for field in key_fields:
    if field not in df.columns:
        continue
    
    if field == 'TaskName':
        mask = df['TaskName'].isna() | (df['TaskName'] == '')
        df.loc[mask, 'TaskName'] = df.loc[mask, 'TaskID'].apply(lambda x: f"Task {x}")
        changes += mask.sum()
        
    elif field == 'TaskDescription':
        mask = df['TaskDescription'].isna() | (df['TaskDescription'] == '')
        df.loc[mask, 'TaskDescription'] = df.loc[mask, 'TaskName'].apply(lambda x: f"This task involves {x.lower()}.")
        changes += mask.sum()
        
    elif field == 'Assignee':
        mask = df['Assignee'].isna() | (df['Assignee'] == '')
        df.loc[mask, 'Assignee'] = 'Unassigned'
        changes += mask.sum()
        
    elif field == 'Status':
        mask = df['Status'].isna() | (df['Status'] == '')
        df.loc[mask, 'Status'] = 'Not Started'
        changes += mask.sum()
        
    elif field == 'ClassificationCategory':
        mask = df['ClassificationCategory'].isna() | (df['ClassificationCategory'] == '')
        df.loc[mask, 'ClassificationCategory'] = 'unclassified'
        changes += mask.sum()
        
    elif field == 'IsInformationalContext':
        mask = df['IsInformationalContext'].isna() | (df['IsInformationalContext'] == '')
        df.loc[mask, 'IsInformationalContext'] = 'False'
        changes += mask.sum()
        
    elif field == 'TranscriptionMatchNotes':
        mask = df['TranscriptionMatchNotes'].isna() | (df['TranscriptionMatchNotes'] == '')
        df.loc[mask, 'TranscriptionMatchNotes'] = 'No transcription match information available'
        changes += mask.sum()

after_counts = {}
for field in key_fields:
    if field in df.columns:
        missing = (df[field].isna() | (df[field] == '')).sum()
        after_counts[field] = missing
        print(f"After: {field} has {missing} missing values")

df.to_csv(csv_path, index=False)
print(f"Made {changes} changes to improve data completeness")
