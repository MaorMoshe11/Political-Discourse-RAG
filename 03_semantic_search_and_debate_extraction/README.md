## Semantic Search and Debate Extraction

This directory implements the semantic retrieval stage of the project, linking legislative differences to relevant parliamentary committee discussions using a vector-based search framework.

### Semantic Indexing and Vector Database

Each statement in the committee protocols is converted into a sentence-level vector representation using the embedding model:

- **Qwen/Qwen3-Embedding-0.6B**

The resulting vectors are stored in a FAISS index to enable efficient semantic search. For each vector, the following metadata is preserved:
- Protocol index  
- Statement index  
- Speaker name  
- Original text  

This structure supports retrieval at the level of individual statements while allowing reconstruction of the local conversational context within the debate.

### Retrieval-Augmented Generation (RAG) Architecture

For each legislative difference, a semantic query is constructed by combining the section identifier with a textual description of the difference between the bill proposal and the enacted law. The system performs semantic search over the FAISS index to retrieve relevant debate segments.

The architecture is designed to support an additional language-model layer for interactive dialogue with the retrieved protocols and further refinement of results. However, this generation layer was not implemented due to budget constraints.

### Semantic Search Hyperparameters

The semantic retrieval process was tuned iteratively to balance precision and recall. Relevance annotation and calibration were performed by Dr. Noa Kwartz. The final configuration includes:

- Maximum FAISS candidates: 200 statements  
- Similarity score normalization relative to the top match  
- Relevance threshold: normalized score ≥ 0.85  
- Maximum retrieved debate segments per difference: 20  
- Context window: five statements before and after each retrieved statement  

Legislative differences for which no debate segment exceeds the relevance threshold are excluded from the final output. This filtering step was essential to achieve a practical balance between missing relevant discussions and including unrelated content.

### Input and Output Artifacts

The semantic retrieval pipeline operates on the following input files and produces a structured output report:

- **FAISS index**  
  `all_protocols_parsed_by_speaker.faiss`  
  Vector index containing sentence-level embeddings of all parsed protocol statements.

- **Metadata file**  
  `all_protocols_parsed_by_speaker_metadata.parquet`  
  Metadata associated with each vector, including protocol identifiers, speaker names, and original text.

- **Legislative differences file**  
  `cotent_offer_and_final_format_comparison_annotated - cotent_offer_and_final_format_comparison.csv`  
  Annotated differences between the bill proposal and the enacted law, used to construct semantic search queries.

- **Final output**  
  `electricity_law_diff_debates_report.json`  
  A structured report linking each legislative difference to the retrieved parliamentary debate segments.

### Output Structure

The final output dataset is organized hierarchically by:
- Legal section  
- Legislative difference  
- Retrieved debate segments, including metadata and local textual context  

### Files in This Directory

- **`queries_df`**  
  Embedded representation of legislative differences after sentence encoding.

- **`RAG3.ipynb`**  
  Core notebook implementing the semantic indexing and retrieval pipeline.

- **`law_explorer.html`**  
  An exploratory visualization presenting the top five most relevant debate segments per legislative difference, intended to support interpretability and qualitative inspection.

- **`law_explorer2.html`**  
  A labeling-oriented interface presenting up to 20 debate segments per difference, ordered by relevance. Researchers review the debates sequentially and annotate the point at which relevance ceases.

- **`electricity_law_diff_tagging_template.xlsx`**  
  Annotation template used by researchers to provide structured feedback on the retrieval results.
