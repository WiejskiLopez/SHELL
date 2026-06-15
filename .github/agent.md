OpenCode

Konfiguracja:

export OPENAI_API_KEY=nvapi-xxxx
export OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1

lub w konfiguracji:

{
"provider": "openai",
"baseURL": "https://integrate.api.nvidia.com/v1",
"apiKey": "nvapi-xxxx",
"model": "nvidia/nemotron-3-ultra-550b-a55b"
}
Aider
pip install aider-chat

Uruchomienie:

aider \
--model openai/nvidia/nemotron-3-ultra-550b-a55b \
--openai-api-base https://integrate.api.nvidia.com/v1 \
--openai-api-key $NVIDIA_API_KEY


https://github.com/anomalyco/opencode/tree/dev