from langchain_ollama.llms import OllamaLLM
from typing import List, Dict


def setup_llm(config: Dict) -> OllamaLLM:
    return OllamaLLM(
        model=config["llm"]["model_name"],
        temperature=config["llm"]["temperature"]
    )
