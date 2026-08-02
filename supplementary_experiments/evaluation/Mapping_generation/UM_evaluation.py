import pandas as pd

# Merge the logic of the two scripts into one
# Load the original CSVfile
df = pd.read_csv("disagreement_report_new1111test1.csv")

# Convert non- "non"  content to  "non-None"
columns_to_process = ['GT', 'TFIDF', 'LLMProb', 'LLMAssign', "LLMAssign-IPRAG"]
for col in columns_to_process:
    df[col] = df[col].apply(lambda x: 'non-None' if x != 'non' else x)

# Save the intermediate processing result (optional)
df.to_csv("disagreement_report_process1.csv", index=False)

# Get all unique project names
projects = df['Project'].unique()

methods = ['TFIDF', 'LLMProb', 'LLMAssign', 'LLMAssign-IPRAG']

# 4) Compute by project Precision/Recall/F1
projects = df['Project'].unique()
results = []

for project in projects:
    subset = df[df['Project'] == project]
    metrics = {'Project': project}

    for m in methods:
        pred_none = subset[m] == 'non'
        gt_none = subset['GT'] == 'non'

        tp = (pred_none & gt_none).sum()
        fp = (pred_none & ~gt_none).sum()
        fn = (~pred_none & gt_none).sum()

        precision = tp / (tp + fp) if (tp + fp) != 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) != 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) != 0 else 0.0

        metrics[f'precision_{m}'] = round(precision, 4)
        metrics[f'recall_{m}'] = round(recall, 4)
        metrics[f'f1_{m}'] = round(f1, 4)

    results.append(metrics)

# Generate the result DataFrame and print the output
result_df = pd.DataFrame(results)
print(result_df)

# 5) Strictly set the exported column order: all  precision,then all  recall,then all  f1
precision_cols = [f'precision_{m}' for m in methods]
recall_cols    = [f'recall_{m}'    for m in methods]
f1_cols        = [f'f1_{m}'        for m in methods]

ordered_cols = ['Project'] + precision_cols + recall_cols + f1_cols
result_df = result_df[ordered_cols]

# 6) Export result CSV
result_df.to_csv('UM_mapping_accuracy1.csv', index=False)

# 7) Compute and print the macro average for each method (average across projects)
mean_precision = result_df[precision_cols].mean()
mean_recall    = result_df[recall_cols].mean()
mean_f1        = result_df[f1_cols].mean()

for m in methods:
    print(f"\nMethod: {m}")
    print(f"Average Precision: {mean_precision[f'precision_{m}']:.4f}")
    print(f"Average Recall:    {mean_recall[f'recall_{m}']:.4f}")
    print(f"Average F1 Score:  {mean_f1[f'f1_{m}']:.4f}")