import os
from dotenv import load_dotenv
from autorag.evaluator import Evaluator
from autorag.chunker import Chunker
from typing import Callable, List
import autorag
from autorag import LazyInit
from autorag.data import sentence_splitter_modules


# Load environment variables
load_dotenv()


def register_custom_chunking():
    """Register a custom sentence splitter for chunking"""
    # Define custom sentence splitter function
    def split_by_custom_method() -> Callable[[str], List[str]]:
        def split(text: str) -> List[str]:
            # Simple custom logic - modify as needed for your specific use case
            # This example splits by periods and filters out empty strings
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            return sentences
        return split
    
    # Register the custom sentence splitter
    sentence_splitter_modules["custom_splitter"] = LazyInit(split_by_custom_method)
    print("✅ Custom sentence splitter 'custom_splitter' registered successfully")


def register_custom_embeddings():
    """Register custom embedding models including FlagEmbedding"""
    try:
        # Import necessary dependencies
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        
        # Register FlagEmbedding (BAAI/bge-large-en-v1.5)
        autorag.embedding_models['flagembed_large'] = LazyInit(
            HuggingFaceEmbedding, 
            model_name="BAAI/bge-large-en-v1.5"
        )
        
        # Register FlagEmbedding (smaller version)
        autorag.embedding_models['flagembed_small'] = LazyInit(
            HuggingFaceEmbedding, 
            model_name="BAAI/bge-small-en-v1.5"
        )
        
        # Register FlagEmbedding multilingual version
        autorag.embedding_models['flagembed_m3'] = LazyInit(
            HuggingFaceEmbedding, 
            model_name="BAAI/bge-m3"
        )
        
        print("✅ Custom FlagEmbedding models registered successfully")
    except Exception as e:
        print(f"⚠️ Failed to register FlagEmbedding models: {e}")
        print("   Make sure you have installed the required packages with: pip install sentence-transformers")


def main():
    # Check if Ollama server is accessible
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("✅ Connected to Ollama server successfully")
            models = response.json().get("models", [])
            if models:
                print(f"Available models: {', '.join([m['name'] for m in models])}")
        else:
            print(f"⚠️ Connected to Ollama server but received status code: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to connect to Ollama server: {e}")
        print("   Make sure Ollama is running with: ollama serve")
        print("   And you have the required models: ollama pull nomic-embed-text mxbai-embed-large llama3")
        return

    # Register custom sentence splitter for chunking
    register_custom_chunking()
    
    # Register custom embedding models
    # register_custom_embeddings()
    
    # Initialize evaluator    
    print("\nInitializing AutoRAG evaluator...")
    evaluator = Evaluator(
        qa_data_path='qa_test.parquet', 
        corpus_data_path='corpus.parquet',
        project_dir='dir'
    )
    
    # Start evaluation
    print("Starting AutoRAG evaluation with Ollama models...")
    evaluator.start_trial('config.yaml')
    print("Evaluation completed!")


if __name__ == "__main__":
    main()