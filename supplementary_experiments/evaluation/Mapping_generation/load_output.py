import csv
# def make_metric_header(thresholds):
#     """
#     Generate a header like: ["Project", "Metric", "@10", "@20", ..., "@90"] header
#     """
#     return ["Project", "Metric"] + [f"@{thr}" for thr in thresholds]

def write_pr_curve_stacked(filename, rows, thresholds):
    """
    Convert the original  rows(in the form:[Project, Prec@10, Reca@10, F1@10, Prec@20, Reca@20, F1@20, ...])
    Output as:
        [All projects Precision section...]
        [All projects Recall section...]
        [All projects F1 section...]
    """
    header = ["Project"] + [f"{thr}" for thr in thresholds]
    out_rows = []

    # Separate the three metric types
    prec_rows, reca_rows, f1_rows = [], [], []
    for row in rows:
        project = row[0]
        values = row[1:]
        expect_len = len(thresholds) * 3
        if len(values) != expect_len:
            if len(values) < expect_len:
                values = values + [""] * (expect_len - len(values))
            else:
                values = values[:expect_len]

        precisions, recalls, f1s = [], [], []
        for i in range(len(thresholds)):
            base = i * 3
            precisions.append(values[base + 0])
            recalls.append(values[base + 1])
            f1s.append(values[base + 2])

        prec_rows.append([project] + precisions)
        reca_rows.append([project] + recalls)
        f1_rows.append([project] + f1s)

    # Merge into Precision→Recall→F1"order
    out_rows.append(["Precision"])
    out_rows.append(header)
    out_rows.extend(prec_rows)

    out_rows.append([])
    out_rows.append(["Recall"])
    out_rows.append(header)
    out_rows.extend(reca_rows)

    out_rows.append([])
    out_rows.append(["F1"])
    out_rows.append(header)
    out_rows.extend(f1_rows)

    with open(filename, "w", newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(out_rows)

