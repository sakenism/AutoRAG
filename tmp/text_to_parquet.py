import pandas as pd

# Step 1: Read the text file line by line
lines = []
with open('data/text.txt', 'r') as file:
    for i, line in enumerate(file):
        if line.strip():  # Skip empty lines
            lines.append({
                'doc_id': f'line_{i}',
                'content': line.strip(),
                'line_number': i
            })

# Step 2: Create a pandas DataFrame
df = pd.DataFrame(lines)

# Step 3: Save as Parquet
df.to_parquet('data/output_lines.parquet')