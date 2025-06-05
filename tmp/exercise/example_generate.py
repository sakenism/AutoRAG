import pandas as pd
from autorag.evaluator import Evaluator

# Step 1: Prepare your QA data with required columns
evaluator = Evaluator(
    qa_data_path='qa_test_test.parquet',
    corpus_data_path='corpus_test.parquet',  # Still required by AutoRAG
    project_dir='dir'
)

evaluator.start_trial('config_generation.yaml')
