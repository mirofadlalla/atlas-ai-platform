import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from huggingface_hub import InferenceClient

# Local Imports
from app.rag.retrivel_data_pipline import get_retriever
from app.rag.evaluation.relevance_evaluation import relevance_evaluation_
from app.rag.evaluation.retrieval_stability import retrieval_stability_ as RetrievalStability

class EvalPipeline:
    def __init__(self, path: Path, tenant_id: str): 
        self.tenant_id = tenant_id
        self.data = self._get_json_file(path)
        

        # 1. Setup Retriever
        self.retriever = get_retriever(tenant_id=self.tenant_id)
        if hasattr(self.retriever, 'search_kwargs'):
            self.retriever.search_kwargs["k"] = 2  # Limit to top-2 for evaluation consistency

        # 2. Setup LLM (Qwen via Featherless AI on HuggingFace)
        self.llm = InferenceClient(
            provider="featherless-ai",
            api_key=os.environ["HF_TOKEN"],
        )
        self.model_id = "Qwen/Qwen2.5-1.5B-Instruct"

    def _get_json_file(self, path: Path) -> List[Dict]:
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"[Error] Failed to read JSON: {e}")
            return []

    def _answer_question(self, question: str, docs) -> str:
        """Call the LLM directly with retrieved context."""
        context = "\n\n".join(d.page_content for d in docs)
        prompt = (
        "You are a precise QA assistant. Answer the question using ONLY the provided context.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER FORMAT GUIDELINES:\n"
        "• Be concise - answer in as few words as possible while being complete\n"
        "• Use the same keywords and terminology found in the context\n"
        "• For factual questions (names, dates, numbers), provide just the fact\n"
        "• For explanatory questions, provide a brief 1-2 sentence explanation\n"
        "• Match the language style of the context\n\n"
        "QUALITY REQUIREMENTS:\n"
        "✓ Extract answers verbatim when possible\n"
        "✓ Prioritize precision over completeness\n"
        "✓ If multiple pieces of information exist, include the most relevant\n"
        "✓ Never invent or hallucinate information\n"
        "✓ If unsure or answer not in context, say exactly 'I don't know'\n\n"
        "Answer (use context keywords):"
    )
        completion = self.llm.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.1,
        )
        return completion.choices[0].message.content.strip()

    @staticmethod
    def _keyword_overlap_score(prediction: str, reference: str) -> float:
        """Simple token F1 between prediction and reference (no external deps)."""
        pred_tokens  = set(prediction.lower().split())
        ref_tokens   = set(reference.lower().split())
        if not ref_tokens:
            return 0.0
        common = pred_tokens & ref_tokens
        precision = len(common) / len(pred_tokens) if pred_tokens else 0.0
        recall    = len(common) / len(ref_tokens)
        if precision + recall == 0:
            return 0.0
        return round(2 * precision * recall / (precision + recall), 4)

    def evaluate(self, runs: int = 2):
        results = []

        for sample in self.data:
            question = sample["question"]
            relevant_docs = [str(i) for i in sample.get("relevant_ids", sample.get("relevant_docs", []))]
            reference_answer = sample.get("answer", "")

            # --- 1. Retriever Evaluation (Relevance) ---
            retrieved_documents = self.retriever.invoke(question)

            retrieved_ids = [
                str(doc.metadata.get("_id") or doc.metadata.get("id") or "")
                for doc in retrieved_documents
            ]

            rel_eval = relevance_evaluation_(retrieved_ids, relevant_docs)

            # --- 2. Stability Evaluation ---
            stability_scores = RetrievalStability.retrieval_stability_test(
                retriever=self.retriever,
                question=question,
                runs=runs
            )

            paraphrases = sample.get("paraphrases", [])
            rephrase_score = None
            if paraphrases:
                rephrase_score = RetrievalStability.rephrase_stability_test(
                    retriever=self.retriever,
                    question=question,
                    paraphrases=paraphrases
                )

            # --- 3. Generator (LLM) Evaluation ---
            prediction = self._answer_question(question, retrieved_documents)
            token_f1   = self._keyword_overlap_score(prediction, reference_answer)

            results.append({
                "question": question,
                "retrieval_metrics": {
                    "precision":  rel_eval.precision(),
                    "recall":     rel_eval.recall(),
                    "f1":         rel_eval.f1_score(),
                    "mrr":        rel_eval.mrr()
                },
                "stability_metrics": {
                    "avg_jaccard":   stability_scores.get("avg_jaccard"),
                    "rephrase_score": rephrase_score
                },
                "generation_metrics": {"token_f1": token_f1},
                "prediction":  prediction,
                "reference":   reference_answer
            })

        return results

# if __name__ == "__main__":
#     test = EvalPipeline(path=Path("app/rag/evaluation/evaluation_dataset.json"), tenant_id="1234")
#     eval_results = test.evaluate(runs=3)
#     print(json.dumps(eval_results, indent=2))