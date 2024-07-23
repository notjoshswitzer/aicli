# OpenAI config
OAI_KEY = 'sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' # https://platform.openai.com/api-keys
OAI_LLM = 'gpt-4o-mini'                                              # https://platform.openai.com/docs/models

# Ollama config
OLLAMA_URL = 'http://localhost:11434/'                               # Ollama API endpoint (Ensure your Ollama service is public)
OLLAMA_LLM = 'llama3.1:8b'                                           # https://ollama.com/library

# Default LLM
DEFAULT_LLM = 'ollama'                                               # ollama or oai (-G and -O flag overide this default)
