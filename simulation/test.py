import unittest
from utils.text_generation import GPT_request

class TestGPTRequest(unittest.TestCase):
    def test_gpt_request_success(self):
        prompt = "Tell me a joke."
        response = GPT_request(prompt)
        self.assertIsInstance(response, str)
        self.assertNotEqual(response, "")
    
    def test_gpt_request_error(self):
        prompt = ""
        response = GPT_request(prompt)
        self.assertTrue("ERROR" in response)

if __name__ == "__main__":
    unittest.main()