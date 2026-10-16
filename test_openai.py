from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6-luna",
    input="Reply with exactly: AI connection works!"
)

print(response.output_text)