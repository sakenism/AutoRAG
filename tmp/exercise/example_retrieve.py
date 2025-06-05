from autorag.evaluator import Evaluator

evaluator = Evaluator(qa_data_path='qa_test_test.parquet', corpus_data_path='corpus_test.parquet',
                      project_dir='dir')
evaluator.start_trial('config_retrieval.yaml')
