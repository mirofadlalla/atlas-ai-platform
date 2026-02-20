from app.design_pattern.embedded_model import EmbeddedModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

class SemanticChunkingFunction:
    @staticmethod
    def process_document(text: str, metadata: dict):
        token_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=50
        )
        initial_docs = token_splitter.create_documents([text], metadatas=[metadata])

        embedding_model = EmbeddedModel()
        semantic_splitter = SemanticChunker(
            embeddings=embedding_model,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=90
        )

        final_docs = semantic_splitter.split_documents(initial_docs)
        return final_docs













# from sklearn.metrics.pairwise import cosine_similarity

# import numpy as np 

# import os
# import re

# def split_into_sentences(text: str):
#     sentences = re.split(r'(?<=[.!?]) +', text)
#     return [s.strip() for s in sentences if s.strip()]


# def semantic_chunk(docs, chunk_size=512, overlap=50, threshold=0.75):

#     sentences = split_into_sentences(docs)

#     if not sentences:
#         return []
    
#     model = EmbeddedModel()
#     embeddings  = model.encode(sentences)

#     chunks = []
#     current_chunk = [sentences[0]]
#     current_embedding = [embeddings[0]]

#     for i in range(1,len(sentences)):

#         centriod = np.mean(current_embedding)
#         sim = cosine_similarity(
#             centriod,
#             embeddings[i]
#         )[0][0]

#     if sim > threshold:
#         current_chunk.append(sentences[i])
#         current_embedding.append(embeddings[i])

#     else :
#         chunks.append(" ".join(current_chunk))
#         current_chunk = [sentences[1]]
#         current_embedding = [embeddings[1]]
    
#     if current_chunk :
#         chunks.append(" ".join(current_chunk))

#     return chunks

# text = """
# Machine learning is a subset of artificial intelligence.
# It allows systems to learn from data.
# Deep learning is a specialized type of machine learning.
# Pizza is one of the most popular foods in the world.
# Neural networks are inspired by the human brain.
# """

# chunks = semantic_chunk(text, threshold=0.7)

# for i, c in enumerate(chunks):
#     print(f"\nChunk {i+1}:\n{c}")


