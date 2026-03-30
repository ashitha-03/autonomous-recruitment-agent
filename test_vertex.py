import os
import vertexai
from vertexai.generative_models import GenerativeModel

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/credentials.json"

vertexai.init(
    project="interns2026",
    location="us-central1"
)

model = GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Explain artificial intelligence in one sentence.")

print(response.text)