"""
@author: mkturkcan
@changed by: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

# simulation\utils\config.py

# Copy and paste your OpenAI API Key
openai_api_key = "<your_api_key>"
openai_base_url = "http://192.168.1.110:3001/v1"
# Put your name
key_owner = "Huang Miaosen"

class DefaultModel:
    # Set a model name for embedding
    embedding = "BAAI/bge-m3"
    # Set a model name for completion
    completion = "gpt-4o-mini"
