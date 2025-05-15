import pandas as pd

csv_path = "final_task_register.csv"
df = pd.read_csv(csv_path)

new_columns = [
    "ConversationFlowID",  # For hierarchical structure derived from transcription line numbers
    "HierarchyMethod",  # Method used to establish task hierarchy
    "LineRefQuality",  # Quality assessment of line references
    "ProcessingStageNotes",  # Notes from various processing stages
    "DecompositionMethod",  # Method used for task decomposition
    "RefinementStageFlag",  # Flag indicating refinement stage
    "ContextualReferenceMap",  # Mapping of contextual references
    "MetadataCompleteness",  # Assessment of metadata completeness
]

for column in new_columns:
    if column not in df.columns:
        df[column] = ""
        print(f"Added column: {column}")

df.to_csv(csv_path, index=False)
print(f"CSV updated with {len(new_columns)} new metadata columns")
