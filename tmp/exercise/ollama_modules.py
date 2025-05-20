from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

def get_ollama_embedding(model_name="nomic-embed-text"):
    """
    Create an Ollama embedding model
    
    Args:
        model_name: Name of the Ollama embedding model to use
        
    Returns:
        OllamaEmbedding: Configured embedding model
    """
    print(f"Creating Ollama embedding model: {model_name}")
    return OllamaEmbedding(
        model_name=model_name,
        base_url="http://localhost:11434"
    )

def get_ollama_llm(model_name="llama3"):
    """
    Create an Ollama LLM
    
    Args:
        model_name: Name of the Ollama LLM to use
        
    Returns:
        Ollama: Configured LLM
    """
    print(f"Creating Ollama LLM: {model_name}")
    return Ollama(
        model_name=model_name,
        base_url="http://localhost:11434",
        request_timeout=120.0
    )