import json
from textwrap import dedent
import tiktoken
import logging as lg

from src.initialize import Initializer


def num_tokens_from_string(string: str, model) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def max_tokens_per_chunk(prompt, max_tokens_response_summary, clean_text, config):
    logger = lg.getLogger(max_tokens_per_chunk.__name__)

    tokens_prompt_summary = num_tokens_from_string(prompt, config["model"])
    max_doc_tokens_per_prompt = (
        int(config["tokens_context_window"])
        - max_tokens_response_summary
        - tokens_prompt_summary
        - int(config["tokens_safeguard"])
    ) / 1.5  # por condición de tokenizer, para no cortar a mitad de frase
    total_doc_tokens = num_tokens_from_string(clean_text, config["model"])

    logger.info(f"Total tokens in the document: {total_doc_tokens}")
    return max_doc_tokens_per_prompt


def estimate_cost_before_call(
    tokens_prompt_summary, optimum_tokens_chunk_size, max_tokens_response_summary
):

    total_tokens_input = tokens_prompt_summary + optimum_tokens_chunk_size
    input_call_cost = total_tokens_input * 0.0005 / 1000

    max_tokens_output = max_tokens_response_summary
    estimated_output_call_cost = max_tokens_output * 0.0015 / 1000

    estimated_total_cost = input_call_cost + estimated_output_call_cost
    return estimated_total_cost


# Split a text into smaller chunks of size n, preferably ending at the end of a sentence
def create_chunks(text, n, tokenizer):
    tokens = tokenizer.encode(text)
    """Yield successive n-sized chunks from text."""
    i = 0
    while i < len(tokens):
        # Find the nearest end of sentence within a range of 0.5 * n and 1.5 * n tokens
        j = min(i + int(1.5 * n), len(tokens))
        while j > i + int(0.5 * n):
            # Decode the tokens and check for full stop or newline
            chunk = tokenizer.decode(tokens[i:j])
            if chunk.endswith(".") or chunk.endswith("\n"):
                break
            j -= 1
        # If no end of sentence found, use n tokens as the chunk size
        if j == i + int(0.5 * n):
            j = min(i + n, len(tokens))
        yield tokens[i:j]
        i = j


# Hacer el prompt por cada chunk
def extract_chunk(document, config, client):
    prompts = {
        "prompt_resumen": config["prompt_resumen"],
        "prompt_cnae": config["prompt_cnae"],
    }
    input_tokens = 0
    output_tokens = 0

    for key, value in prompts.items():
        messages = [
            {
                "role": "system",
                "content": dedent(value),
            },
            {"role": "user", "content": dedent(document)},
        ]

        response = client.chat.completions.create(
            model=config["model"],
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0,
            max_tokens=config["max_words_response_summary"],
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        input_tokens += response.usage.prompt_tokens
        output_tokens += response.usage.completion_tokens

        if key == "prompt_resumen":
            output = json.loads(response.choices[0].message.content)
        elif key == "prompt_cnae":
            respuesta = json.loads(response.choices[0].message.content)
            output["divisiones_cnae"] = respuesta["divisiones_cnae"]
        elif key == "prompt_rama_jca":
            respuesta = json.loads(response.choices[0].message.content)
            output["rama_jca"] = respuesta["rama_jca"]


    return (output, input_tokens, output_tokens)


if __name__ == "main":
    INIT_OBJECTS = Initializer()
