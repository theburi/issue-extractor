from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Dict
import logging
import re
import json

def setup_llm(config: Dict, max_tokens=2000) -> OllamaLLM:
    logging.info(f"Setting up LLM with model: {config['llm']}")
    return OllamaLLM(
        model=config["llm"]["model_name"],
        temperature=config["llm"]["temperature"],
        max_tokens=max_tokens,
        base_url=config["llm"]["base_url"]

    )

def parse_llm_output(output: str) -> List[Dict]:
    """Parse LLM output to extract problems, severity, and impact using regex."""
    problems = []
    parsed_data={}
    try:
        # Use regex to locate the JSON array in the output
        json_pattern = re.compile(r'{.*?}', re.DOTALL)
        match = json_pattern.search(output)
        if not match:
             # Use regex to locate the JSON-like structure in the output
            json_pattern = re.compile(r'"?Problem"?:.*?"?Severity"?:.*?"?Impact"?:.*?(?=\n|\n\n|$)', re.DOTALL)
            matches2 = json_pattern.findall(output)
            if not matches2:
                raise ValueError("No Data array found in the output.")            
            for string_match in matches2:
                # Add braces to ensure valid JSON
                print ("match ",string_match)
                problems.append({
                    "description": re.search(r"(?<=Problem:\s).*?(?=\s*Severity:)", string_match).group().strip() if re.search(r"(?<=Problem:\s).*?(?=\s*Severity:)", string_match) else "No problem description found",
                    "severity": re.search(r"(?<=Severity:\s).*?(?=\s*Impact:)", string_match).group().strip() if re.search(r"(?<=Severity:\s).*?(?=\s*Impact:)", string_match) else "No severity found",
                    "impact": re.search(r"(?<=Impact:\s).*", string_match).group().strip() if re.search(r"(?<=Impact:\s).*", string_match) else "No impact found"
                })
        else:           
            # Extract the JSON block
            json_block = match.group(0)
            parsed_data = json.loads(json_block)

            # Process each problem in the JSON list
            problems.append({
                "description": parsed_data.get("Problem", "").strip(),
                "severity": parsed_data.get("Severity", "").strip(),
                "impact": parsed_data.get("Impact", "").strip()
            })
    except (json.JSONDecodeError, ValueError) as e:       
        logging.error(f"Error parsing LLM output JSON: {output} \n Exception: {str(e)}")
        return problems  # Return an empty list if parsing fails
    
    return problems

def setup_embeddings(config: Dict) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=config["embeddings"]["model_name"]
    )

def invoke_llm(config, prompt, input_variables, max_tokens=2000):

    llm = setup_llm(config, max_tokens)
    # Lets ask LLM if this is a problem related to the original question
    llm_promt = PromptTemplate(
        template=prompt,
        input_variables=input_variables
    )
    chain = llm_promt | llm
    results = chain.invoke(input_variables)
    # if llm model name is deepseek wh need to remove text between <think> and </think> tags
    if "deepseek" in config["llm"]["model_name"]:
        results = re.sub(r'<think>.*?</think>', '', results,  flags=re.DOTALL)
        logging.info(f"Results after removing <think> tags: {results}")

    return results