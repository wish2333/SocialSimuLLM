from utils.text_generation import GPT_request, get_embedding
prompt = "Tell me a joke."
response = GPT_request("", prompt)
print(response)
embedding = get_embedding(response)
print(embedding)