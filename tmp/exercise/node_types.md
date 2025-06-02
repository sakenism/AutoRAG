# AutoRAG Node Types - Detailed Examples

## 1. Query Expansion Node

### What it does:
Transforms the original user query into multiple variations or more detailed queries to improve retrieval performance. Instead of searching with just "What is Python?", it might generate "What is Python programming language?", "Python syntax basics", "Python features and benefits".

### When to use:
- When users ask short or ambiguous questions
- When you want to capture different aspects of a query
- When your retrieval system misses relevant documents with the original query

### How it works:
1. Takes the user's original query
2. Uses an LLM to generate expanded/alternative queries
3. These expanded queries are then used for retrieval
4. **Evaluation**: Since expansion affects retrieval, it's evaluated by running retrieval with the expanded queries

### Example Configuration:

```yaml
- node_type: query_expansion
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
    speed_threshold: 10
    top_k: 10
    # REQUIRED: Specify which retrieval modules to use for evaluation
    retrieval_modules:
      - module_type: bm25
      - module_type: vectordb
        vectordb: default
  modules:
    # Baseline: No expansion (sometimes this is best!)
    - module_type: pass_query_expansion
    
    # Decompose complex questions into simpler ones
    - module_type: query_decompose
      llm: openai
      model: gpt-3.5-turbo
      temperature: [0.2, 0.7]
    
    # Generate hypothetical answer passages
    - module_type: hyde
      llm: openai
      model: gpt-3.5-turbo
      max_token: 128
      prompt: "Write a detailed answer to this question: {query}"
    
    # Generate multiple query variations
    - module_type: multi_query_expansion
      llm: openai
      model: gpt-3.5-turbo
      query_count: [3, 5]
```

### Real Example:
```
Original: "Python speed"
Decomposed: ["What affects Python performance?", "How fast is Python compared to other languages?", "Python optimization techniques"]
HyDE: Generates a fake answer about Python speed, then searches for documents similar to that answer
Multi-query: ["Python execution speed", "Python performance benchmarks", "Python vs C++ speed comparison"]
```

---

## 2. Retrieval Node

### What it does:
Finds and retrieves the most relevant documents/passages from your knowledge base that could help answer the user's query. This is the core information gathering step.

### When to use:
- Always needed in RAG systems (unless you're doing pure generation)
- When you have a corpus of documents to search through
- When you need external knowledge to answer questions

### How it works:
1. Takes the query (original or expanded)
2. Searches through your document corpus
3. Returns top-k most relevant passages with relevance scores
4. **Evaluation**: Compares retrieved passages with ground truth relevant documents

### Example Configuration:

```yaml
- node_type: retrieval
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision, retrieval_ndcg]
    speed_threshold: 60
  top_k: [3, 5, 10]  # Try different numbers of retrieved documents
  modules:
    # Lexical search (keyword matching)
    - module_type: bm25
      bm25_tokenizer: [porter_stemmer, space]  # Different tokenization methods
    
    # Semantic search (meaning-based)
    - module_type: vectordb
      vectordb: openai_embeddings
      similarity_metric: [cosine, l2]
    
    # Combine both approaches with Reciprocal Rank Fusion
    - module_type: hybrid_rrf
      target_modules: ('bm25', 'vectordb')  # Tuple: these modules must exist
      rrf_k: [1, 3, 5]  # RRF parameter
      weight: [0.5, 0.7]  # Weight towards semantic vs lexical
    
    # Combine with weighted average
    - module_type: hybrid_cc
      target_modules: ('bm25', 'vectordb')
      cc_weights: [[0.3, 0.7], [0.5, 0.5], [0.7, 0.3]]  # [lexical_weight, semantic_weight]
      normalize_method: [mm, z]  # Min-max or z-score normalization
```

### Real Example:
```
Query: "How to optimize Python performance?"

BM25 finds: Documents with keywords "optimize", "Python", "performance"
VectorDB finds: Documents about "speeding up code", "efficiency", "bottlenecks"
Hybrid combines both: Gets documents that are both keyword-relevant AND semantically similar
```

---

## 3. Passage Augmenter Node

### What it does:
Adds additional context to retrieved passages by including neighboring content (like the paragraph before/after). This helps provide more complete context for better answer generation.

### When to use:
- When your chunks are small and might miss important context
- When answers require information spanning multiple consecutive passages
- When you want to provide more comprehensive context to the LLM

### How it works:
1. Takes the retrieved passages
2. Looks up neighboring passages (previous/next in the original document)
3. Adds them to provide fuller context
4. **Evaluation**: Evaluated as a retrieval task since it affects what content the LLM sees

### Example Configuration:

```yaml
- node_type: passage_augmenter
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
    speed_threshold: 30
  modules:
    - module_type: prev_next_augmenter
      mode: [prev, next, both]  # Add previous, next, or both surrounding passages
      max_add: [1, 2, 3]        # How many neighboring passages to add
```

### Real Example:
```
Original passage: "The function returns a list of integers."
With prev augmentation: "Here's how to use the sort() method: The function returns a list of integers."
With next augmentation: "The function returns a list of integers. You can then iterate through this list using a for loop."
With both: "Here's how to use the sort() method: The function returns a list of integers. You can then iterate through this list using a for loop."
```

---

## 4. Passage Reranker Node

### What it does:
Re-orders the retrieved passages to put the most relevant ones first. Initial retrieval might get the right documents but in the wrong order - reranking fixes this using more sophisticated relevance models.

### When to use:
- When initial retrieval gets relevant documents but poor ranking
- When you want to use advanced models for better relevance scoring
- When you need to reduce the number of passages while keeping the best ones

### How it works:
1. Takes retrieved passages and their initial scores
2. Uses advanced models to re-score each passage for relevance
3. Re-orders passages by new scores
4. **Evaluation**: Compared against ground truth rankings

### Example Configuration:

```yaml
- node_type: passage_reranker
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
    speed_threshold: 30
  top_k: [3, 5]  # Keep top 3 or 5 after reranking (often fewer than retrieval)
  modules:
    # Neural reranker (no external dependencies)
    - module_type: upr
    
    # Text-to-text reranker with custom prompts
    - module_type: tart
      prompt: "Rank these passages by relevance to the question"
    
    # MonoT5 model (requires GPU for good performance)
    - module_type: monot5
      model_name: [castorini/monot5-base-msmarco, castorini/monot5-large-msmarco]
      batch: 32
    
    # API-based rerankers (require API keys)
    - module_type: cohere_reranker
      model: [rerank-english-v2.0, rerank-multilingual-v2.0]
      api_key: ${COHERE_API_KEY}
    
    - module_type: jina_reranker
      model: jina-reranker-v1-base-en
      api_key: ${JINAAI_API_KEY}
      
    # Embedding-based reranker
    - module_type: flag_embedding_reranker
      model_name: BAAI/bge-reranker-large
```

### Real Example:
```
Initial retrieval order:
1. "Python is a programming language" (score: 0.8)
2. "Machine learning with Python libraries" (score: 0.75)  
3. "Python performance optimization techniques" (score: 0.7)

After reranking for query "How to make Python faster?":
1. "Python performance optimization techniques" (new score: 0.95)
2. "Machine learning with Python libraries" (new score: 0.6)
3. "Python is a programming language" (new score: 0.3)
```

---

## 5. Passage Filter Node

### What it does:
Removes passages that don't meet certain criteria (too old, too irrelevant, too short, etc.). This helps ensure only high-quality, relevant passages make it to the generation stage.

### When to use:
- When you want to filter out low-quality or irrelevant passages
- When you need time-sensitive information (remove old content)
- When similarity scores are too low to be useful

### How it works:
1. Takes reranked passages
2. Applies filtering criteria (thresholds, dates, etc.)
3. Removes passages that don't meet criteria
4. **Evaluation**: Measured by retrieval quality of remaining passages

### Example Configuration:

```yaml
- node_type: passage_filter
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
    speed_threshold: 10
  modules:
    # Remove passages below similarity threshold
    - module_type: similarity_threshold_cutoff
      threshold: [0.3, 0.5, 0.7]  # Different minimum similarity scores
      reverse: false  # false = higher scores are better
    
    # Remove bottom percentage of passages
    - module_type: similarity_percentile_cutoff
      percentile: [0.3, 0.5]  # Keep top 70% or 50%
      reverse: false
    
    # Remove old content (requires last_modified_datetime in metadata)
    - module_type: recency_filter
      threshold: "2024-01-01"  # Remove content older than this date
    
    # Remove passages that are too short/long
    - module_type: percentile_cutoff
      percentile: [0.2, 0.3]  # Remove bottom 20% or 30% by length
      reverse: false
```

### Real Example:
```
Before filtering (5 passages):
1. "Python optimization" (similarity: 0.8, date: 2024-06-01)
2. "Python basics" (similarity: 0.6, date: 2024-05-01)  
3. "Java programming" (similarity: 0.3, date: 2024-04-01)
4. "Python history" (similarity: 0.4, date: 2020-01-01)
5. "C++ performance" (similarity: 0.2, date: 2024-03-01)

After similarity_threshold_cutoff (0.5) and recency_filter (2024-01-01):
1. "Python optimization" (similarity: 0.8, date: 2024-06-01)
2. "Python basics" (similarity: 0.6, date: 2024-05-01)
```

---

## 6. Passage Compressor Node

### What it does:
Compresses long passages to fit within LLM context limits while preserving the most important information. Uses intelligent compression rather than simple truncation.

### When to use:
- When your passages are too long for the LLM context window
- When you want to reduce token costs for API-based LLMs
- When you need to fit more passages in the same context length

### How it works:
1. Takes filtered passages
2. Uses advanced compression models to identify key information
3. Compresses each passage while preserving relevance
4. **Evaluation**: Measured by downstream generation quality

### Example Configuration:

```yaml
- node_type: passage_compressor
  strategy:
    metrics: [retrieval_f1, retrieval_recall, retrieval_precision]
    speed_threshold: 60
  modules:
    - module_type: longllmlingua
      model_name: [NousResearch/Llama-2-7b-hf, microsoft/llmlingua-2-bert-base-multilingual-cased]
      target_token: [200, 300, 500]  # Target compressed length
      instruction: "Compress while keeping technical details"
      chunk_end_tokens: ["."]  # Split on sentences
      dynamic_context_compression_ratio: 0.3
      condition_compare: true
      condition_in_question: "after"
      rank_method: "longllmlingua"
```

### Real Example:
```
Original passage (150 tokens):
"Python is a high-level, interpreted programming language with dynamic semantics. Its high-level built-in data structures, combined with dynamic typing and dynamic binding, make it very attractive for Rapid Application Development, as well as for use as a scripting or glue language to connect existing components together. Python's simple, easy to learn syntax emphasizes readability and therefore reduces the cost of program maintenance."

Compressed (50 tokens):
"Python: high-level, interpreted language with dynamic semantics. Built-in data structures, dynamic typing enable Rapid Application Development, scripting. Simple syntax emphasizes readability, reduces maintenance cost."
```

---

## 7. Prompt Maker Node

### What it does:
Combines the user's query with retrieved passages to create the final prompt that will be sent to the LLM. This is where you control how information is presented to the model.

### When to use:
- Always needed when using generation (unless passing raw data)
- When you want to test different prompt formats
- When you need to control how context is presented to the LLM

### How it works:
1. Takes the query and compressed/filtered passages
2. Formats them according to your template
3. Creates the final prompt for the LLM
4. **Evaluation**: Measured by the quality of LLM responses to these prompts

### Example Configuration:

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
    # Optional: specify which generator to use for evaluation
    generator_modules:
      - module_type: llama_index_llm
        llm: openai
        model: gpt-3.5-turbo
  modules:
    - module_type: fstring
      prompt:
        # Simple format
        - "Question: {query}\nContext: {retrieved_contents}\nAnswer:"
        
        # More detailed format
        - "Based on the following context, please answer the question.\n\nContext:\n{retrieved_contents}\n\nQuestion: {query}\n\nAnswer:"
        
        # Chain of thought format
        - "Context: {retrieved_contents}\n\nQuestion: {query}\n\nLet me think step by step and answer based on the context:\n"
        
        # Instructional format
        - "You are a helpful assistant. Use only the provided context to answer the question. If the answer is not in the context, say 'I don't have enough information.'\n\nContext: {retrieved_contents}\n\nQuestion: {query}\nAnswer:"
        
        # Structured format
        - |
          ## Context
          {retrieved_contents}
          
          ## Question
          {query}
          
          ## Instructions
          Please provide a comprehensive answer based on the context above.
          
          ## Answer
```

### Real Example:
```
Query: "How do I optimize Python performance?"
Retrieved content: "Use list comprehensions instead of loops. Avoid global variables. Use built-in functions when possible."

Generated prompt:
"Based on the following context, please answer the question.

Context:
Use list comprehensions instead of loops. Avoid global variables. Use built-in functions when possible.

Question: How do I optimize Python performance?

Answer:"
```

---

## 8. Generator Node

### What it does:
The final step that uses an LLM to generate the actual answer based on the formatted prompt. This is where the magic happens - turning retrieved information into a coherent, helpful response.

### When to use:
- Always needed for generating final answers
- When you want to compare different LLM models
- When you need to tune generation parameters (temperature, length, etc.)

### How it works:
1. Takes the formatted prompt from prompt_maker
2. Sends it to the specified LLM
3. Generates the final answer
4. **Evaluation**: Compared against ground truth answers using various metrics

### Example Configuration:

```yaml
- node_type: generator
  strategy:
    metrics:
      - metric_name: bleu        # Lexical similarity
      - metric_name: meteor      # Lexical + some semantic
      - metric_name: rouge       # Overlap-based
      - metric_name: sem_score   # Semantic similarity
        embedding_model: openai
    speed_threshold: 120
  modules:
    # OpenAI Models
    - module_type: llama_index_llm
      llm: openai
      model: [gpt-3.5-turbo, gpt-4, gpt-4-turbo]
      temperature: [0.0, 0.3, 0.7]  # 0.0=deterministic, 0.7=creative
      max_tokens: [512, 1000, 2000]
      batch: 16
      system_prompt: "You are a helpful programming assistant."
    
    # Local models via Ollama
    - module_type: llama_index_llm
      llm: openailike
      model: [llama3:latest, mistral:latest, codellama:latest]
      api_base: "http://localhost:11434/v1"
      api_key: "not-needed"
      temperature: [0.0, 0.5]
      max_tokens: 1000
      request_timeout: 180
    
    # HuggingFace models
    - module_type: llama_index_llm
      llm: huggingface
      model: microsoft/DialoGPT-medium
      max_tokens: 1000
      temperature: 0.7
      device_map: "auto"
    
    # Fast local inference with vLLM
    - module_type: vllm
      model: [facebook/opt-125m, microsoft/DialoGPT-medium]
      max_tokens: 1000
      temperature: [0.0, 0.5, 0.7]
      tensor_parallel_size: 1
    
    # Direct OpenAI integration (more OpenAI features)
    - module_type: openai_llm
      llm: openai
      model: gpt-4
      temperature: 0.0
      max_tokens: 1000
      response_format: {"type": "json_object"}  # For structured output
```

### Real Example:
```
Input prompt: "Based on the context about Python optimization, answer: How do I make Python faster?"

GPT-4 (temp=0.0): "Based on the context, here are three key ways to optimize Python performance: 1) Use list comprehensions instead of traditional loops as they are implemented in C and run faster..."

Llama3 (temp=0.7): "Great question! Python performance can definitely be improved. From what I see in the context, you'll want to focus on..."

CodeLlama: "Here's how to optimize Python code based on the provided information: ```python # Instead of this: result = [] for item in items: result.append(process(item))..."
```

---

## Complete Pipeline Example

Here's how all nodes work together:

```yaml
node_lines:
  - node_line_name: full_pipeline
    nodes:
      # 1. Expand the query
      - node_type: query_expansion
        modules:
          - module_type: hyde
            llm: openai
      
      # 2. Retrieve relevant documents  
      - node_type: retrieval
        top_k: 10
        modules:
          - module_type: hybrid_rrf
            target_modules: ('bm25', 'vectordb')
      
      # 3. Add context around passages
      - node_type: passage_augmenter
        modules:
          - module_type: prev_next_augmenter
            mode: both
            max_add: 1
      
      # 4. Rerank for better relevance
      - node_type: passage_reranker
        top_k: 5
        modules:
          - module_type: upr
      
      # 5. Filter out low-quality passages
      - node_type: passage_filter
        modules:
          - module_type: similarity_threshold_cutoff
            threshold: 0.5
      
      # 6. Compress to fit context limits
      - node_type: passage_compressor
        modules:
          - module_type: longllmlingua
            target_token: 500
      
      # 7. Format the prompt
      - node_type: prompt_maker
        modules:
          - module_type: fstring
            prompt: "Context: {retrieved_contents}\nQ: {query}\nA:"
      
      # 8. Generate the final answer
      - node_type: generator
        modules:
          - module_type: llama_index_llm
            llm: openai
            model: gpt-4
```

This creates a sophisticated RAG pipeline that processes queries through multiple enhancement stages before generating the final answer!