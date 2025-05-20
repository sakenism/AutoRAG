from autorag.parser import Parser
from autorag.chunker import Chunker
from autorag.validator import Validator
from autorag.evaluator import Evaluator


import os

def main():
    print("Starting parsing...")
    parser = Parser(
        data_path_glob="data/*",
        project_dir='parse_results'
    )
    parser.start_parsing("configs/parse_config.yaml")
    print("Parsing completed!")
    
    # Step 2: Chunk the parsed data
    print("Starting chunking...")

    chunker = Chunker.from_parquet(
        parsed_data_path="parse_results/parsed_result.parquet",
        project_dir='chunk_results'

    )
    chunker.start_chunking("configs/chunk_config.yaml")

    print("Chunking completed!")
    
    print("AutoRAG processing completed successfully!")

if __name__ == "__main__":
    main()