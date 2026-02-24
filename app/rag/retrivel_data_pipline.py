import os
import sys
from pathlib import Path
import langchain
from langchain_redis import RedisSemanticCache
from langchain_classic.chains import create_retrieval_chain 
from langchain_classic.chains.combine_documents import create_stuff_documents_chain 
from langchain_classic.prompts import ChatPromptTemplate

import time

from app.models.runs import Runs
from app.models.costLog import CostLog

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.rag.steps.retriever import get_retriever
from app.services.llm_runner import CustomLocalLLM
from app.design_pattern.embedded_model import EmbeddedModel # Ensure it's LangChain compatible

class RetrievalPipeline:
    def __init__(self, tenant_id: int):
        self.retriever = get_retriever(tenant_id)
        
        # 1. Define the embedding model (Object)
        # Use the same instance so Redis can use it for similarity comparison
        self.embedding_model = EmbeddedModel() 

        # 2. Setup Redis Semantic Cache (initialized once at load time)
        langchain.llm_cache = RedisSemanticCache(
            redis_url="redis://localhost:6379:0",
            embeddings=self.embedding_model,
            ttl=86400, # one day
            distance_threshold=0.2
        )
        
        # 3. Setup Local LLM and Chain
        self.local_llm = CustomLocalLLM()
        
        prompt = ChatPromptTemplate.from_template(
            "Answer the following question based only on the provided context:\n\n"
            "Context: {context}\n\n"
            "Question: {input}\n\n"
            "Answer:"
        )
        
        self.document_chain = create_stuff_documents_chain(self.local_llm, prompt)
        self.qa_chain = create_retrieval_chain(self.retriever, self.document_chain)

    def retrieve(self, query: str):
        """Direct access to the Retriever without LLM"""
        return self.retriever.invoke(query)
    
    def ask(self, query: str):
        """
        Answer the question using the Cache and the local LLM.
        If the question is similar to a previous one stored in Redis, it will respond immediately.
        """
        # invoke automatically triggers the cache behind the scenes
        response = self.qa_chain.stream({"input": query})
        return response
    
    def ask_stream(self, query: str):
        """
        Stream the answer to a query with logging of run and cost information.
        
        This method:
        1. Streams the answer chunks from the QA chain
        2. Tracks latency and token usage
        3. Logs run and cost information to the database
        """
        start_time = time.time()
        full_answer = ""
        
        # 1. Stream the QA chain response
        for chunk in self.qa_chain.stream({"input": query}):
            if "answer" in chunk:
                full_answer += chunk["answer"]
                yield chunk["answer"]

        # 2. Calculate metrics after streaming completes
        latency = time.time() - start_time
        usage = CustomLocalLLM.last_usage  # Extract token usage from the model
        
        # 3. Save to database (SQLAlchemy)
        try:
            new_run = Runs(
                tenant_id=self.tenant_id,
                query=query,
                answer=full_answer,
                latency=latency,
                cache_hit=False,  # SemanticCache controls this, default to False for now
                retrieved_docs_ids=",".join([doc.metadata.get('_id', '') for doc in self.retriever.invoke(query)])
            )
            
            # Calculate cost (example: Qwen 2.5 1.5B pricing)
            # For local models, cost is 0; for API models, calculate accordingly
            cost = (usage.get("input", 0) * 0.0000001) + (usage.get("output", 0) * 0.0000002) 

            new_cost = CostLog(
                run=new_run,  # Automatic linking via SQLAlchemy relationship
                input_tokens=usage.get("input", 0),
                output_tokens=usage.get("output", 0),
                model_name="Qwen2.5-1.5B",
                cost_usd=cost
            )
            
            # TODO: Uncomment when database session is available
            # session.add(new_run)
            # session.commit()
            print(f"\n[Logged] Run saved with {usage.get('total_tokens')} total tokens.")
            
        except Exception as e:
            print(f"Error logging to DB: {e}")

    @property
    def _llm_type(self) -> str:
        return "custom_huggingface_stream"
    

# retrieval_pipeline = RetrievalPipeline(tenant_id="1234")
# retrieved_docs = retrieval_pipeline.retrieve("What was the effective tax rate for the year ended December 31, 2023, following the IRS rule change regarding foreign tax credits?")
# print(retrieved_docs)

# # [Document(metadata={'tenant_id': 123, 'source': 'google.pdf', 'author': 'Omar', '_id': '126f69ef-db44-452c-82c8-842815f504a9', '_collection_name': 'atlas_documents1'}, page_content='Investments Measured at Fair Value on a Nonrecurring Basis\nOur non-marketable equity securities are investments in privately held companies without readily determinable \nmarket values. The carrying value of our non-marketable equity securities is adjusted to fair value upon observable \ntransactions for identical or similar investments of the same issuer or impairment. Non-marketable equity securities \nthat have been remeasured during the period based on observable transactions are classified within Level 2 or Level 3'), Document(metadata={'tenant_id': 123, 'source': 'google.pdf', 'author': 'Omar', '_id': '0a081284-de05-4e2c-b09a-5af2c6d93629', '_collection_name': 'atlas_documents1'}, page_content='measurement alternative") and are measured at cost, less impairment, subject to upward and downward adjustments \nresulting from observable price changes for identical or similar investments of the same issuer. These adjustments \nrequire quantitative assessments of the fair value of our securities, which may require the use of unobservable inputs. Adjustments are determined primarily based on a market approach as of the transaction date and involve the use of \nestimates using the best information available, which may include cash flow projections or other available market data. Non-marketable equity securities are also evaluated for impairment, based on qualitative factors including the \ncompanies\' financial and liquidity position and access to capital resources, among others. When indicators of \nimpairment exist, we prepare quantitative measurements of the fair value of our equity investments using a market \napproach or an income approach, which requires judgment and the use of unobservable inputs, including discount \nrates, investee revenues and costs, and comparable market data of private and public companies, among others. Table of Contents Alphabet Inc.'), Document(metadata={'tenant_id': 123, 'source': 'google.pdf', 'author': 'Omar', '_id': 'c16bfdd1-bdeb-4f4e-812f-f8f997a63186', '_collection_name': 'atlas_documents1'}, page_content='marketable equity securities by $597 million. From time to time, we may enter into derivatives to hedge the market \nprice risk on certain of our marketable equity securities. Our non-marketable equity securities not accounted for under the equity method are adjusted to fair value for \nobservable transactions for identical or similar investments of the same issuer or impairment (referred to as the \nmeasurement alternative). The fair value measured at the time of the observable transaction is not necessarily an \nindication of the current fair value as of the balance sheet date. These investments, especially those that are in the \nearly stages, are inherently risky because the technologies or products these companies have under development are \ntypically in the early phases and may never materialize, and they may experience a decline in financial condition, \nwhich could result in a loss of a substantial part of our investment in these companies. Valuations of our equity \ninvestments in private companies are inherently more complex due to the lack of readily available market data and \nobservable transactions at lower valuations could result in significant losses. In addition, global economic conditions \ncould result in additional volatility. The success of our investment in any private company is also typically dependent on \nthe likelihood of our ability to realize appreciation in the value of investments through liquidity events such as public \nofferings, acquisitions, private sales or other market events.'), Document(metadata={'tenant_id': 123, 'source': 'google.pdf', 'author': 'Omar', '_id': 'c10ea4d4-23fa-42a9-b526-b4c1cbbf0375', '_collection_name': 'atlas_documents1'}, page_content='Equity Investment Risk\nOur marketable and non-marketable equity securities are subject to a wide variety of market-related risks that \ncould substantially reduce or increase the fair value of our holdings. Our marketable equity securities are publicly traded stocks or funds and our non-marketable equity securities are \ninvestments in privately held companies, some of which are in the startup or development stages. We record marketable equity securities not accounted for under the equity method at fair value based on readily \ndeterminable market values, of which publicly traded stocks and mutual funds are subject to market price volatility, and \nrepresent $5.2 billion  and $6.0 billion  of our investments as of December 31, 2022  and 2023, respectively. A \nhypothetical adverse price change of 10% on our December 31, 2023  balance would decrease the fair value of'), Document(metadata={'tenant_id': 123, 'source': 'google.pdf', 'author': 'Omar', '_id': 'f9e9f49c-2d41-42fc-9b01-b971c4280e77', '_collection_name': 'atlas_documents1'}, page_content='See Note 7 for further details on OI&E. The carrying values for marketable and non-marketable equity securities are summarized below (in millions):\nAs of December 31, 2022 As of December 31, 2023\nMarketable \nEquity \nSecurities\nNon-Marketable \nEquity \nSecurities Total\nMarketable \nEquity \nSecurities\nNon-Marketable \nEquity \nSecurities Total\nTotal initial cost $ 5,764 $ 16,157 $ 21,921 $ 5,418 $ 17,616 $ 23,034 \nCumulative net \ngain (loss)(1)  (608)  12,372  11,764  555  11,150  11,705 \nCarrying value $ 5,156 $ 28,529 $ 33,685 $ 5,973 $ 28,766 $ 34,739 \n(1) Non-marketable equity securities cumulative net gain (loss) is comprised of $16.8 billion  gains and $4.5 billion  losses \n(including impairments) as of December 31, 2022 and $18.1 billion gains and $6.9 billion losses (including impairments) as of \nDecember 31, 2023. Gains and Losses on Marketable and Non-marketable Equity Securities\nGains and losses (including impairments), net, for marketable and non-marketable equity securities included in \nOI&E are summarized below (in millions):\nYear Ended December 31,\n 2021 2022 2023\nRealized net gain (loss) on equity securities sold during the \nperiod $ 1,196 $ (442) $ 690 \nUnrealized net gain (loss) on marketable equity securities  1,335  (3,242)  790 \nUnrealized net gain (loss) on non-marketable equity securities(1)  9,849  229  (1,088) \nTotal gain (loss) on equity securities in other income \n(expense), net $ 12,380 $ (3,455) $ 392 \n(1) Unrealized gain (loss) on non-marketable equity securities accounted for under the measurement alternative is comprised of \n$10.0 billion, $3.3 billion, and $1.8 billion of upward adjustments as of December 31, 2021, 2022, and 2023, respectively, and')]

# for doc in retrieved_docs:
#     print(doc.metadata['_id'])  # Print the first 200 characters of each retrieved document



# if __name__ == "__main__":
#     pipeline = RetrievalPipeline(tenant_id="1234")
    
#     query = "What level in the fair value hierarchy do debt securities get classified in?"
    
#     # connect to Redis : First call will compute the answer and store it in Redis it will take 
#     # result1 = pipeline.ask(query)
#     # print(result1, end="", flush=True)

#     for chunk in pipeline.ask_stream(query):
#         print(chunk , end="" , flush=True)
    
#     print("--- Second Call (Cached from Redis) ---")
#     for chunk in pipeline.ask_stream(query):
#         print(chunk, end="", flush=True)
#     print("\n")