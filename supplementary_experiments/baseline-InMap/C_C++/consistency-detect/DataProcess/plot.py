import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
# Read CSV file
csv_path = '/Users/liujingwen/Desktop/consistency/recover/lda_demo/csv_result/teastore_tfidf_inconsistency_results.csv'
data = pd.read_csv(csv_path)

# Assume  CSV file has three columns threshold, delete_count, precision, recall
threshold = data['Threshold'].unique()
delete_count = data['Delete Count'].unique()
# precision = data['precision']
# recall = data['recall']

# Use pivot_table to convert precision and recall into 2D tables, and fill missing values with 0 or another default value
precision_table = data.pivot_table(values='precision', index='Delete Count', columns='Threshold', fill_value=0)
recall_table = data.pivot_table(values='recall', index='Delete Count', columns='Threshold', fill_value=0)

# Ensure the 2D data can be plotted as a surface and take the  precision and recall value matrices
Z_precision = precision_table.values
Z_recall = recall_table.values

# Update threshold and delete_count  grid to ensure every value has a corresponding combination
threshold_grid, delete_count_grid = np.meshgrid(precision_table.columns, precision_table.index)

# Create precision surface plot
precision_surface = go.Surface(z=Z_precision, x=threshold_grid, y=delete_count_grid, colorscale='Viridis', name='Precision')

# Create recall surface plot
recall_surface = go.Surface(z=Z_recall, x=threshold_grid, y=delete_count_grid, colorscale='Plasma', name='Recall')

# Create layout
layout = go.Layout(
    scene=dict(
        xaxis_title='Threshold',
        yaxis_title='Delete Count',
        zaxis_title='Precision / Recall'
    ),
    title='Precision and Recall Surface Plots'
)

# Create chart
fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'surface'}, {'type': 'surface'}]],
                    subplot_titles=['Precision Surface', 'Recall Surface'])

fig.add_trace(precision_surface, row=1, col=1)
fig.add_trace(recall_surface, row=1, col=2)

fig.update_layout(layout)

fig.show()