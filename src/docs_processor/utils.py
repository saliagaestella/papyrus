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
    logger = lg.getLogger(extract_chunk.__name__)
    input_tokens = 0
    output_tokens = 0

    messages = [
        {
            "role": "system",
            "content": dedent(config["prompt_resumen"]),
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

    output = json.loads(response.choices[0].message.content)
    """if output["resumen"] != "No identificado":
        output["divisiones_cnae"] = generate_divisiones_cnae(
            config,
            client,
            output["resumen"],
        )
    else:
        output["divisiones_cnae"] = []"""

    if output["resumen"] != "No identificado":
        output["divisiones_cnae"] = generate_divisiones_cnae(
            config,
            client,
            dedent(document),
        )
    else:
        output["divisiones_cnae"] = []

    """elif key == "prompt_rama_jca":
        respuesta = json.loads(response.choices[0].message.content)
        output["rama_jca"] = respuesta["rama_jca"]"""

    logger.info(f"AI Result: \n {output}")
    return (output, input_tokens, output_tokens)


def generate_divisiones_cnae(config, client, resumen):
    """
    Generates the cnae tags and checks if all tags in are within possible_tags.
    Keeps prompting up to 5 times until all tags are valid.

    Args:
        tags (list): List of tags to validate.

    Returns:
        list: Validated list of tags or None if validation fails after 5 attempts.
    """
    logger = lg.getLogger(generate_divisiones_cnae.__name__)
    prompt = dedent(config["prompt_cnae"])
    possible_tags = [
        "Agricultura, ganadería, caza y servicios relacionados",
        "Silvicultura y explotación forestal",
        "Pesca y acuicultura",
        "Extracción de antracita, hulla y lignito",
        "Extracción de crudo de petróleo y gas natural",
        "Extracción de minerales metálicos",
        "Otras industrias extractivas",
        "Actividades de apoyo a las industrias extractivas",
        "Industria de la alimentación",
        "Fabricación de bebidas",
        "Industria del tabaco",
        "Industria textil",
        "Confección de prendas de vestir",
        "Industria del cuero y del calzado",
        "Industria de la madera y del corcho",
        "Industria del papel",
        "Artes gráficas y reproducción de soportes grabados",
        "Coquerías y refino de petróleo",
        "Industria química",
        "Fabricación de productos farmacéuticos",
        "Fabricación de productos de caucho y plásticos",
        "Fabricación de otros productos minerales no metálicos",
        "Metalurgia; fabricación de productos de hierro y acero",
        "Fabricación de productos metálicos, excepto maquinaria",
        "Fabricación de productos informáticos, electrónicos y ópticos",
        "Fabricación de material y equipo eléctrico",
        "Fabricación de maquinaria y equipo n.c.o.p",
        "Fabricación de vehículos de motor, remolques y semirremolques",
        "Fabricación de otro material de transporte",
        "Fabricación de muebles",
        "Otras industrias manufactureras",
        "Reparación e instalación de maquinaria y equipo",
        "Suministro de energía eléctrica, gas, vapor y aire acondicionado",
        "Captación, depuración y distribución de agua",
        "Recogida y tratamiento de aguas residuales",
        "Gestión de residuos",
        "Actividades de descontaminación",
        "Construcción de edificios",
        "Ingeniería civil",
        "Actividades de construcción especializada",
        "Venta y reparación de vehículos de motor",
        "Comercio al por mayor",
        "Comercio al por menor",
        "Transporte terrestre y por tubería",
        "Transporte marítimo y por vías navegables interiores",
        "Transporte aéreo",
        "Almacenamiento y actividades anexas al transporte",
        "Actividades postales y de correos",
        "Servicios de alojamiento",
        "Servicios de comidas y bebidas",
        "Edición",
        "Actividades cinematográficas y de vídeo",
        "Actividades de programación y emisión",
        "Telecomunicaciones",
        "Programación, consultoría y otras actividades informáticas",
        "Servicios de información",
        "Servicios financieros, excepto seguros y fondos de pensiones",
        "Seguros, reaseguros y fondos de pensiones",
        "Actividades auxiliares a los servicios financieros y seguros",
        "Actividades inmobiliarias",
        "Actividades jurídicas y de contabilidad",
        "Consultoría de gestión empresarial",
        "Servicios técnicos de arquitectura e ingeniería",
        "Investigación y desarrollo",
        "Publicidad y estudios de mercado",
        "Otras actividades profesionales, científicas y técnicas",
        "Actividades veterinarias",
        "Actividades de alquiler",
        "Actividades relacionadas con el empleo",
        "Agencias de viajes, operadores turísticos",
        "Actividades de seguridad e investigación",
        "Servicios a edificios y actividades de jardinería",
        "Actividades administrativas de oficina",
        "Administración pública y defensa",
        "Educación",
        "Actividades sanitarias",
        "Asistencia en establecimientos residenciales",
        "Actividades de servicios sociales sin alojamiento",
        "Actividades de creación, artísticas y espectáculos",
        "Bibliotecas, archivos, museos y otras actividades culturales",
        "Actividades de juegos de azar y apuestas",
        "Actividades deportivas, recreativas y de entretenimiento",
        "Actividades de organizaciones asociativas",
        "Reparación de ordenadores y artículos personales",
        "Otros servicios personales",
        "Actividades de los hogares como empleadores",
        "Actividades de los hogares como productores",
        "Actividades de organizaciones y organismos extraterritoriales",
    ]
    attempts = 0
    while attempts < 1:
        messages = [
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": resumen},
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

        tags = [
            tag.strip()
            for tag in json.loads(response.choices[0].message.content)[
                "divisiones_cnae"
            ]
        ]

        if any(tag in possible_tags for tag in tags):
            return tags
        else:
            logger.info(
                f"Invalid tags detected ({tags}). Attempt {attempts + 1}/5. Please enter a valid list of tags."
            )
            attempts += 1

    logger.info("Maximum attempts reached. Validation failed.")
    return []


if __name__ == "main":
    INIT_OBJECTS = Initializer()
