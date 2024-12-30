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


def max_tokens_per_chunk(max_tokens_response_summary, config):
    logger = lg.getLogger(max_tokens_per_chunk.__name__)

    tokens_prompt_resumen = num_tokens_from_string(
        config["prompt_resumen"], config["model"]
    )
    tokens_prompt_cnae = num_tokens_from_string(config["prompt_cnae"], config["model"])
    max_prompt_tokens = max(tokens_prompt_resumen, tokens_prompt_cnae)

    max_tokens_per_prompt = (
        int(config["tokens_context_window"])
        - max_tokens_response_summary
        - max_prompt_tokens
        - int(config["tokens_safeguard"])
    ) / 1.5  # por condición de tokenizer, para no cortar a mitad de frase

    return int(max_tokens_per_prompt)


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
    tokens = tokenizer.encode(text)  # Encode the entire text into tokens
    i = 0
    while i < len(tokens):
        # Attempt to form a chunk up to 1.2 * n tokens
        end = min(i + int(n * 1.2), len(tokens))
        best_end = end  # Default to the maximum size allowed

        # Decode the largest candidate chunk once
        chunk = tokenizer.decode(tokens[i:end])

        # Find the last sentence boundary (greedy search, moving backward)
        for j in range(len(chunk) - 1, -1, -1):
            if chunk[j] in {".", "!", "?", "\n"}:  # Sentence boundary
                best_end = (
                    i + tokenizer.encode(chunk[: j + 1]).__len__()
                )  # Adjust token size
                break

        # If no boundary is found, fallback to n tokens
        if best_end == end and end - i > n:
            best_end = i + n

        # Yield the chunk and move to the next position
        yield tokenizer.decode(tokens[i:best_end])
        i = best_end


# Hacer los prompts por cada chunk
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
