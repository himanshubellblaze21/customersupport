# import os
# from flask import Flask, render_template, request, jsonify
# import requests
# print(">>> API_GATEWAY_URL =", repr(os.getenv("API_GATEWAY_URL")))
 
# app = Flask(__name__)

 
# API_GATEWAY = os.getenv("API_GATEWAY_URL")
 
# @app.route('/')
# def index():
#     return render_template('index.html')
 
# @app.route('/chat', methods=['POST'])
# def chat():
#     data = request.get_json() or {}
#     user_msg = data.get("query", "")
 
#       # send "query" instead of "message"
#     gw_resp = requests.post(
#       API_GATEWAY,
#      json={"query": user_msg},
#        headers={"Content-Type": "application/json"}
#     )
    

#     gw_resp.raise_for_status()
#     reply = gw_resp.json().get("answer", "")
 
#     return jsonify({"answer": reply})
 
# if __name__ == '__main__':
#     app.run(debug=True)







import os
import json
import boto3
import psycopg2
import logging
from flask import Flask, render_template, request, jsonify

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# ── Import your backend‐response‐logic functions ────────────────────────────────
# Assume you’ve placed the following functions (get_titan_embedding,
# fetch_semantic_context_from_pgvector, get_response_llm, etc.) into a file
# named backend_logic.py in the same directory. Adjust the import path
# if you placed them elsewhere.
from response_logic import get_titan_text_llm, fetch_semantic_context_from_pgvector, get_response_llm

app = Flask(__name__)

# If you still need to construct a Titan‐LLM wrapper, do it once here:
llm = get_titan_text_llm()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_msg = data.get("query", "").strip()

    if not user_msg:
        return jsonify({"answer": "Error: Empty query received."}), 400

    try:
        # 1) Call your “get_response_llm” logic, passing in the llm and user query
        response_dict = get_response_llm(llm, user_msg)

        # 2) Ensure we always return a JSON with an "answer" field
        #    If fetch_semantic_context_from_pgvector found context, it returns {"document_context": ...}
        #    We need to normalize it to {"answer": ...} so chat.js can unwrap data.answer.
        if "document_context" in response_dict:
            reply_text = response_dict["document_context"]
        else:
            reply_text = response_dict.get("answer", "Sorry, something went wrong.")

        return jsonify({"answer": reply_text})
    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        return jsonify({"answer": "Error: Could not process your request."}), 500

if __name__ == '__main__':
    app.run(debug=True)
