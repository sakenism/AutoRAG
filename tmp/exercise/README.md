# AutoRAG Comprehensive Configuration Guide

## Table of Contents
1. [Basic YAML Structure](#basic-yaml-structure)
2. [All Available Nodes](#all-available-nodes)
3. [Node Configuration Examples](#node-configuration-examples)
4. [Strategy Configuration](#strategy-configuration)
5. [Environment Variables](#environment-variables)
6. [Complete Example Configurations](#complete-example-configurations)

## Basic YAML Structure

```yaml
# Optional: VectorDB Configuration
vectordb:
  - name: your_vectordb_name
    db_type: chroma|milvus|weaviate|pinecone|couchbase|qdrant
    embedding_model: model_name
    # ... other vectordb-specific configs

# Optional: Chunking Configuration  
chunking:
  modules:
    - module_type: llama_index_chunk
      chunk_method: [Token|Sentence|SentenceWindow]
      # ... chunking parameters

# Main Pipeline Configuration
node_lines:
  - node_line_name: your_node_line_name
    nodes:
      - node_type: NODE_TYPE
        strategy:
          metrics: [metric1, metric2]
          speed_threshold: 10
        # Node parameters (apply to all modules in this node)
        top_k: 10
        modules:
          - module_type: MODULE_TYPE
            # Module-specific parameters
```

## All Available Nodes

### 1. Query Expansion Node
**Purpose**: Expand queries to improve retrieval relevance

**Node Type**: `query_expansion`

**Available Modules**:
- `pass_query_expansion` - No expansion (baseline)
- `query_decompose` - Decompose multi-hop into single-hop questions
- `hyde` - Generate hypothetical passages
- `multi_query_expansion` - Generate multiple query variations

**Strategy**: Evaluated using retrieval metrics since expansion affects retrieval
- **Metrics**: `[retrieval_f1, retrieval_recall, retrieval_precision, retrieval_ndcg, retrieval_mrr]`
- **Required**: `retrieval_modules` - specify which retrieval modules to use for evaluation

```yaml
- node_type: query_expansion
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
    speed_threshold: 10
    top_k: 10
    retrieval_modules:
      - module_type: bm25
      - module_type: vectordb
        vectordb: default
  modules:
    - module_type: pass_query_expansion
    - module_type: query_decompose
      llm: openai
      temperature: [0.2, 1.0]
    - module_type: hyde
      llm: openai
      max_token: 64
      prompt: "Custom prompt for HyDE"
    - module_type: multi_query_expansion
      llm: openai
      query_count: [3, 5]
```

### 2. Retrieval Node
**Purpose**: Retrieve relevant documents for queries

**Node Type**: `retrieval`

**Available Modules**:
- `bm25` - BM25 lexical retrieval
- `vectordb` - Semantic vector retrieval  
- `hybrid_rrf` - Reciprocal Rank Fusion of multiple retrievers
- `hybrid_cc` - Convex Combination fusion

**Node Parameters**:
- `top_k`: Number of documents to retrieve

```yaml
- node_type: retrieval
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision, retrieval_ndcg, retrieval_mrr]
    speed_threshold: 60
  top_k: [3, 5, 10]
  modules:
    # BM25 Retrieval
    - module_type: bm25
      bm25_tokenizer: [porter_stemmer, space, ko_kiwi]
    
    # Vector Retrieval
    - module_type: vectordb
      vectordb: your_vectordb_name
      similarity_metric: [cosine, l2, ip]
    
    # Hybrid RRF
    - module_type: hybrid_rrf
      target_modules: ('bm25', 'vectordb')
      rrf_k: [1, 3, 5, 10, 60]
      weight: [0.5, 0.7]
    
    # Hybrid CC (Convex Combination)
    - module_type: hybrid_cc
      target_modules: ('bm25', 'vectordb') 
      cc_weights: [[0.3, 0.7], [0.5, 0.5], [0.7, 0.3]]
      normalize_method: [mm, z, dbsf, tmm]
```

### 3. Passage Augmenter Node
**Purpose**: Add context to retrieved passages

**Node Type**: `passage_augmenter`

**Available Modules**:
- `prev_next_augmenter` - Add previous/next passages

```yaml
- node_type: passage_augmenter
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
  modules:
    - module_type: prev_next_augmenter
      mode: [prev, next, both]
      max_add: [1, 2, 3]
```

### 4. Passage Reranker Node  
**Purpose**: Rerank retrieved passages for better relevance

**Node Type**: `passage_reranker`

**Available Modules**:
- `upr` - Unsupervised Passage Reranker
- `tart` - TART reranker
- `monot5` - MonoT5 model reranker
- `ko_reranker` - Korean reranker
- `cohere_reranker` - Cohere API reranker (requires API key)
- `rankgpt` - RankGPT reranker
- `jina_reranker` - Jina AI reranker (requires API key)
- `colbert_reranker` - ColBERT reranker
- `sentence_transformer_reranker` - SentenceTransformer reranker
- `flag_embedding_reranker` - FlagEmbedding reranker
- `flag_embedding_llm_reranker` - FlagEmbedding LLM reranker
- `time_reranker` - Time-based reranker
- `openvino_reranker` - OpenVINO reranker

**Node Parameters**:
- `top_k`: Number of passages to keep after reranking

```yaml
- node_type: passage_reranker
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
    speed_threshold: 30
  top_k: [3, 5]
  modules:
    - module_type: upr
    
    - module_type: tart
      prompt: "Arrange the following sentences in the correct order."
    
    - module_type: monot5
      model_name: [castorini/monot5-base-msmarco, castorini/monot5-large-msmarco]
    
    - module_type: cohere_reranker
      model: [rerank-english-v2.0, rerank-multilingual-v2.0]
      api_key: ${COHERE_API_KEY}
    
    - module_type: jina_reranker
      model: [jina-reranker-v1-base-en, jina-reranker-v1-turbo-en]
      api_key: ${JINAAI_API_KEY}
```

### 5. Passage Filter Node
**Purpose**: Filter passages based on criteria

**Node Type**: `passage_filter`

**Available Modules**:
- `similarity_threshold_cutoff` - Filter by similarity threshold
- `similarity_percentile_cutoff` - Filter by similarity percentile
- `recency_filter` - Filter by date/time
- `percentile_cutoff` - Filter by length percentile

```yaml
- node_type: passage_filter
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
  modules:
    - module_type: similarity_threshold_cutoff
      threshold: [0.3, 0.5, 0.7]
      reverse: [true, false]
    
    - module_type: recency_filter
      threshold: "2024-01-01"
```

### 6. Passage Compressor Node
**Purpose**: Compress passages to reduce context length

**Node Type**: `passage_compressor`

**Available Modules**:
- `longllmlingua` - LongLLMLingua compression

```yaml
- node_type: passage_compressor
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
  modules:
    - module_type: longllmlingua
      model_name: NousResearch/Llama-2-7b-hf
      target_token: [300, 500, 1000]
      instruction: "Compress the passage while keeping key information"
```

### 7. Prompt Maker Node
**Purpose**: Create prompts from queries and retrieved content

**Node Type**: `prompt_maker`

**Available Modules**:
- `fstring` - F-string template formatting

**Strategy**: Evaluated using generation metrics since prompts affect generation
- **Metrics**: `[bleu, meteor, rouge, sem_score]`
- **Optional**: `generator_modules` - specify which generator modules to use for evaluation

```yaml
- node_type: prompt_maker
  strategy:
    metrics:
      - metric_name: bleu
      - metric_name: meteor  
      - metric_name: rouge
      - metric_name: sem_score
        embedding_model: openai
    speed_threshold: 30
    # Optional: specify generator modules for evaluation
    generator_modules:
      - module_type: llama_index_llm
        llm: openai
        model: gpt-3.5-turbo
  modules:
    - module_type: fstring
      prompt: 
        - "Question: {query}\nContext: {retrieved_contents}\nAnswer:"
        - "Based on the context: {retrieved_contents}\n\nAnswer the question: {query}\n\nAnswer:"
        - "Context: {retrieved_contents}\n\nQ: {query}\nA:"
```

### 8. Generator Node
**Purpose**: Generate final answers using LLMs

**Node Type**: `generator`

**Available Modules**:
- `llama_index_llm` - LlamaIndex LLM wrapper (supports most LLMs)
- `openai_llm` - Direct OpenAI integration
- `vllm` - vLLM for fast local inference

```yaml
- node_type: generator
  strategy:
    metrics:
      - metric_name: bleu
      - metric_name: meteor
      - metric_name: rouge
      - metric_name: sem_score
        embedding_model: openai
    speed_threshold: 120
  modules:
    # OpenAI Models
    - module_type: llama_index_llm
      llm: openai
      model: [gpt-3.5-turbo, gpt-4, gpt-4-turbo]
      temperature: [0.0, 0.3, 0.7]
      max_tokens: [512, 1000, 2000]
      batch: 16
    
    # OpenAI-like API (Ollama, etc.)
    - module_type: llama_index_llm
      llm: openailike
      model: llama3:latest
      api_base: "http://localhost:11434/v1"
      api_key: "not-needed"
      temperature: [0.0, 0.5]
      max_tokens: 1000
      request_timeout: 180
    
    # HuggingFace Models
    - module_type: llama_index_llm
      llm: huggingface
      model: microsoft/DialoGPT-medium
      max_tokens: 1000
      temperature: 0.7
    
    # Direct OpenAI (with more OpenAI-specific features)
    - module_type: openai_llm
      llm: openai
      model: gpt-4
      temperature: 0.0
      max_tokens: 1000
      
    # vLLM for fast local inference
    - module_type: vllm
      model: facebook/opt-125m
      max_tokens: 1000
      temperature: [0.0, 0.7]
```

## Strategy Configuration

### Available Metrics

**Retrieval Metrics**:
- `retrieval_precision` - Precision at k
- `retrieval_recall` - Recall at k  
- `retrieval_f1` - F1 score at k
- `retrieval_ndcg` - Normalized Discounted Cumulative Gain
- `retrieval_mrr` - Mean Reciprocal Rank

**Generation Metrics**:
- `bleu` - BLEU score (lexical similarity)
- `meteor` - METEOR score (lexical + semantic)
- `rouge` - ROUGE score (lexical overlap)
- `sem_score` - Semantic similarity (requires embedding model)

### Strategy Options

```yaml
strategy:
  # Metrics (required)
  metrics: [metric1, metric2]
  # OR for metrics with parameters:
  metrics:
    - metric_name: sem_score
      embedding_model: openai
    - metric_name: bleu
  
  # Speed threshold (optional)
  speed_threshold: 30  # seconds
  
  # Selection strategy (optional)
  strategy_name: [mean, best, normalize_mean, rr]  # default: mean
```

## Environment Variables

```yaml
# Use environment variables for API keys and sensitive data
modules:
  - module_type: vectordb
    embedding_model: openai
    api_key: ${OPENAI_API_KEY}
  
  - module_type: cohere_reranker
    api_key: ${COHERE_API_KEY}
  
  - module_type: jina_reranker  
    api_key: ${JINAAI_API_KEY}
```

## Complete Example Configurations

### Simple RAG Pipeline
```yaml
node_lines:
  - node_line_name: simple_rag
    nodes:
      - node_type: retrieval
        strategy:
          metrics: [retrieval_f1, retrieval_recall]
        top_k: 5
        modules:
          - module_type: vectordb
            vectordb: default
      
      - node_type: prompt_maker
        strategy:
          metrics: [bleu, meteor]
        modules:
          - module_type: fstring
            prompt: "Question: {query}\nContext: {retrieved_contents}\nAnswer:"
      
      - node_type: generator
        strategy:
          metrics: [bleu, meteor, rouge]
        modules:
          - module_type: llama_index_llm
            llm: openai
            model: gpt-3.5-turbo
            temperature: 0.0
```

### Advanced RAG Pipeline
```yaml
vectordb:
  - name: openai_large
    db_type: chroma
    embedding_model: openai_embed_3_large
    
node_lines:
  - node_line_name: advanced_rag
    nodes:
      - node_type: query_expansion
        strategy:
          metrics: [retrieval_f1, retrieval_recall]
          retrieval_modules:
            - module_type: bm25
            - module_type: vectordb
              vectordb: openai_large
        modules:
          - module_type: pass_query_expansion
          - module_type: hyde
            llm: openai
            model: gpt-3.5-turbo
      
      - node_type: retrieval
        strategy:
          metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
        top_k: [5, 10]
        modules:
          - module_type: bm25
          - module_type: vectordb
            vectordb: openai_large
          - module_type: hybrid_rrf
            target_modules: ('bm25', 'vectordb')
            rrf_k: [1, 3, 5]
      
      - node_type: passage_reranker
        strategy:
          metrics: [retrieval_f1, retrieval_precision]
        top_k: 3
        modules:
          - module_type: upr
          - module_type: tart
            prompt: "Rank by relevance"
      
      - node_type: prompt_maker
        strategy:
          metrics: [bleu, meteor, rouge]
        modules:
          - module_type: fstring
            prompt:
              - "Context: {retrieved_contents}\nQuestion: {query}\nAnswer:"
              - "Answer based on context: {retrieved_contents}\nQ: {query}\nA:"
      
      - node_type: generator
        strategy:
          metrics: [bleu, meteor, rouge, sem_score]
        modules:
          - module_type: llama_index_llm
            llm: openai
            model: [gpt-3.5-turbo, gpt-4]
            temperature: [0.0, 0.3, 0.7]
            max_tokens: [512, 1000]
```

### Local Model Pipeline
```yaml
node_lines:
  - node_line_name: local_models
    nodes:
      - node_type: retrieval
        strategy:
          metrics: [retrieval_f1, retrieval_recall]
        top_k: 5
        modules:
          - module_type: bm25
      
      - node_type: prompt_maker
        strategy:
          metrics: [bleu, meteor]
        modules:
          - module_type: fstring
            prompt: "Question: {query}\nAnswer:"
      
      - node_type: generator
        strategy:
          metrics: [bleu, meteor]
        modules:
          # Ollama models
          - module_type: llama_index_llm
            llm: openailike
            model: llama3:latest
            api_base: "http://localhost:11434/v1"
            api_key: "not-needed"
            temperature: [0.0, 0.5]
          
          # vLLM local models
          - module_type: vllm
            model: microsoft/DialoGPT-medium
            max_tokens: 1000
            temperature: [0.0, 0.7]
```

## Key Tips

1. **Tuples vs Lists**: Use tuples `('a', 'b')` for single parameters, lists `[a, b]` for parameter combinations
2. **Environment Variables**: Use `${VAR_NAME}` syntax for secrets
3. **Strategy Evaluation**: Query expansion and prompt maker are evaluated through their impact on subsequent nodes
4. **Parameter Combinations**: Lists create combinations - `[a, b]` × `[1, 2]` = 4 combinations
5. **Speed Threshold**: Set reasonable limits to avoid slow modules
6. **Metrics**: Choose appropriate metrics for your use case (lexical vs semantic)

This guide covers all the major components and configuration options available in AutoRAG. For the most up-to-date information, refer to the official AutoRAG documentation.