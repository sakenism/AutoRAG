from autorag.validator import Validator

validator = Validator(qa_data_path='qa_test.parquet', corpus_data_path='corpus.parquet')
validator.validate('config.yaml')

