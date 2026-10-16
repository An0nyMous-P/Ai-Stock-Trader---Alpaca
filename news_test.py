from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6-luna",
    tools=[
        {"type": "web_search"}
    ],
    input="What is the latest major news about Apple (AAPL)? Give me a short summary and include the dates of the news."
)

print(response.output_text)