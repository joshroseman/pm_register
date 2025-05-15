import pandas as pd

csv_path = "final_task_register.csv"
df = pd.read_csv(csv_path)

info_context_before = (
    df["IsInformationalContext"].notna() & (df["IsInformationalContext"] != "")
).mean() * 100
print(f"Before: IsInformationalContext completeness: {info_context_before:.2f}%")

informational_categories = [
    "info_only",
    "informational",
    "context_only",
    "INFORMATIONAL",
    "INFO-RASA",
]

mask = df["ClassificationCategory"].isin(informational_categories) & (
    df["IsInformationalContext"].isna() | (df["IsInformationalContext"] == "")
)
df.loc[mask, "IsInformationalContext"] = "True"

rasa_mask = (
    df["TaskName"].str.contains("RASA", case=False, na=False)
    | df["TaskDescription"].str.contains("RASA", case=False, na=False)
) & (df["IsInformationalContext"].isna() | (df["IsInformationalContext"] == ""))
df.loc[rasa_mask, "IsInformationalContext"] = "True"
df.loc[rasa_mask, "ContextProcessedNotes"] = (
    "INFO_CTX: RASA-related entry identified and flagged."
)

not_info_mask = df["IsInformationalContext"].isna() | (
    df["IsInformationalContext"] == ""
)
df.loc[not_info_mask, "IsInformationalContext"] = "False"

info_context_after = (
    df["IsInformationalContext"].notna() & (df["IsInformationalContext"] != "")
).mean() * 100
print(f"After: IsInformationalContext completeness: {info_context_after:.2f}%")

df.to_csv(csv_path, index=False)
