from typing import List , Dict

from ..retrivel_data_pipline import RetrievalPipeline

class retrieval_stability_:
    @staticmethod
    def jaccard_similarity(a: List[str], b: List[str]):
        a_set, b_set = set(a), set(b)
        if not a_set and not b_set:
            return 1.0
        if not (a_set | b_set): # if both sets are empty, avoid division by zero
            return 0.0
        return len(a_set & b_set) / len(a_set | b_set)

    @staticmethod
    def retrieval_stability_test(retriever, question: str, runs: int = 3):
        all_runs = []
        for _ in range(runs):
            # make sure to handle cases where retriever might return None or empty list
            retrieved_ = retriever.invoke(question) 
            retrived_ids = [doc.metadata.get('id') or doc.metadata.get('_id') for doc in retrieved_]
            all_runs.append(retrived_ids)
        
        if not all_runs: return {"avg_jaccard": 0, "runs": []}
        
        base = all_runs[0]
        scores = [retrieval_stability_.jaccard_similarity(base, run) for run in all_runs]
        return {"avg_jaccard": sum(scores)/len(scores), "runs": all_runs}

    @staticmethod
    def rephrase_stability_test(retriever, question: str, paraphrases: List[str]):
        # Get base retrieval for the original question
        base_docs = retriever.invoke(question)
        base_ids = [doc.metadata.get("id") or doc.metadata.get("_id") for doc in base_docs]
        
        if not paraphrases: return 1.0
        
        scores = []
        for p in paraphrases:
            p_docs = retriever.invoke(p)
            p_ids = [doc.metadata.get("id") or doc.metadata.get("_id") for doc in p_docs]
            scores.append(retrieval_stability_.jaccard_similarity(base_ids, p_ids))

        return sum(scores) / len(scores)