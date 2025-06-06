from langchain.prompts import PromptTemplate
import psycopg2
import boto3
import json

DB_CONFIG = {
    "host": "database-dev.c5gamqs0cv9w.ap-south-1.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres123"
}



def get_titan_text_llm():
    bedrock_runtime = boto3.client("bedrock-runtime", region_name="ap-northeast-1")

    def llm(prompt: str) -> str:
        print("Titan Model LLM called")

        payload = {
            "inputText": prompt,                      
            "textGenerationConfig": {
                "maxTokenCount": 512,
                "temperature": 0.3,
                "topP": 0.9
                
            }
        }

        # Print the exact JSON you’re sending to Bedrock 
        print("Bedrock payload:", json.dumps(payload))

        # 1) Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=json.dumps(payload).encode("utf-8"),
            accept="application/json",
            contentType="application/json"
        )

        # 2) Read and decode the raw response bytes
        raw_body = response["body"].read().decode("utf-8")

        # 3) Parse the JSON
        parsed = json.loads(raw_body)

        # ◀︎ INSERT THESE PRINTS to see exactly what Titan returned ▶︎
        print("💬 Bedrock raw JSON response:", raw_body)
        print("🧩 Parsed JSON keys:", parsed.keys())
        # If Titan returns "results": [ { "outputText": "..." }, … ],
        # print out that entire list:
        print("🧩 Parsed[\"results\"]:", parsed.get("results"))

        # 4) Now extract the actual answer text from results[0]["outputText"], if present
        #    (older versions sometimes used “completion”, but current Titan uses “results”→“outputText”)
        answer_text = ""
        if "results" in parsed and isinstance(parsed["results"], list) and parsed["results"]:
            answer_text = parsed["results"][0].get("outputText", "").strip()

        # 5) Print the final extracted answer
        print("💬 Bedrock answer (outputText):", answer_text)

        return answer_text

    return llm



def get_titan_embedding(text: str):
    bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
    body = {"inputText": text}
    response = bedrock_runtime.invoke_model(
        body=json.dumps(body),
        modelId="amazon.titan-embed-text-v1",
        accept="application/json",
        contentType="application/json"
    )
    embedding_response = json.loads(response["body"].read())
    return embedding_response["embedding"]


def fetch_semantic_context_from_pgvector(query: str) -> str | None:
    try:
        embedding = get_titan_embedding(query)
        print("🔑 Query embedding:", embedding[:5], "… (total length:", len(embedding), ")")

        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ PG connected successfully")
        cur = conn.cursor()

        cur.execute("""
            SELECT content
            FROM document_vectors1
            ORDER BY embedding <-> %s::vector
            LIMIT 1;
        """, (embedding,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return "\n---\n".join([row[0] for row in rows]) if rows else None

    except Exception as e:
        print("DB Error (embedding/vector search):", e)
        return None
    

solar_prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful customer‐support assistant for a solar‐energy company. Use the provided context—if it’s relevant—to answer the user’s question. If the context is not relevant, rely on your general solar‐energy knowledge.

<context>
{context}
</context>

Question: {question}

Answer in a clear, concise manner."""
)    


def get_response_llm(llm, query: str) -> dict:
    """
    1) Run semantic search to fetch up to 3 relevant text chunks.
    2) If context is found, format a prompt (context + user question) and send it to Titan Text Express.
    3) Return Titan's generated answer.
    4) If no context found, return a fallback answer.
    """

    print("🔍 Running semantic search for query:", query)
    context = fetch_semantic_context_from_pgvector(query)
    print("🔑 Context from pgvector (if any):", context)

    # 2) If we have any context, build the Titan prompt and call the LLM:
    if context:
        # 2a) Build the prompt using PromptTemplate
        prompt = solar_prompt_template.format(
            context=context,
            question=query
        )
        print("✏️  Prompt sent to Titan Text Express:")
        print(prompt[:200] + "…")  # Print first 200 chars for brevity

        # 2b) Call Titan Text Express LLM with that prompt
        try:
            answer = llm(prompt)
        except Exception as e:
            print("❌ Error when calling Titan Text Express:", e)
            # Fallback: if LLM errors, return raw context for debugging
            return {"document_context": context}

        # 2c) Return Titan’s generated answer
        return {"answer": answer}

    # 3) Otherwise, no context → fallback
    return {
        "answer": "Sorry, I couldn’t find anything related to your query."
    }

























