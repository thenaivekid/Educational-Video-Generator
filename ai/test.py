import openai

# Set your OpenAI API key

# Send a chat request
response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "This is a test!"}
  ]
)

# Extract usage data from the response
usage = response['usage']

# Print out the token usage details
prompt_tokens = usage['prompt_tokens']
completion_tokens = usage['completion_tokens']
total_tokens = usage['total_tokens']

print(f"Prompt Tokens: {prompt_tokens}")
print(f"Completion Tokens: {completion_tokens}")
print(f"Total Tokens: {total_tokens}")
