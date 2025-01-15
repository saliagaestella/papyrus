import json
import os
import tiktoken
import logging as lg
from src.initialize import Initializer
from src.docs_processor.utils import (
    create_chunks,
    extract_chunk,
    max_tokens_per_chunk,
    num_tokens_from_string,
)


class DocumentProcessor:
    def __init__(self, initializer: Initializer):
        self.initializer = initializer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.config = initializer.config
        self.results = None

    def process_document(self, text: str, name: str = None):
        logger = lg.getLogger(self.process_document.__name__)
        clean_text = text.replace("  ", " ").replace("\n", "; ").replace(";", " ")
        total_doc_tokens = num_tokens_from_string(clean_text, self.config["model"])
        logger.info(f"Total tokens in the document: {total_doc_tokens}")

        max_tokens_response_summary = (
            int(self.config["max_words_response_summary"]) * 4 / 3
        )
        max_chunk_tokens = max_tokens_per_chunk(
            max_tokens_response_summary,
            self.config,
        )
        logger.info(f"Max tokens per chunk: {max_chunk_tokens}")

        text_chunks = list(create_chunks(clean_text, max_chunk_tokens, self.tokenizer))

        logger.info(f"Number of API calls/chunks: {len(text_chunks)}")

        self.results = [self._process_chunk(chunk) for chunk in text_chunks]
        self._postprocess_results()
        self._clean_aggregated_results()
        self._unify_summary()
        self._generate_final_summary()
        if name:
            self._shorten_name(name)
        else:
            self.results["short_name"] = None

        logger.info(f"Final document: {self.results}")
        logger.info(f"Final CNAE classification: {self.results['divisiones_cnae']}")

        return self.results

    def _process_chunk(self, chunk: str):
        logger = lg.getLogger(self._process_chunk.__name__)
        result, input_token, output_token = extract_chunk(
            chunk, self.config, self.initializer.openai_client
        )
        logger.info(f"Number of input tokens: {input_token}")
        logger.info(f"Number of output tokens: {output_token}")
        return result

    def _postprocess_results(self):
        aggregated = {
            "resumenes": [],
            "etiquetas": set(),
            "impactos": set(),
            "stakeholders": set(),
            "divisiones_cnae": set(),
            "ramas_juridicas": {},
        }

        for data in self.results:
            # Aggregate the data in the appropriate keys
            aggregated["resumenes"].append(data["resumen"])
            aggregated["impactos"].add(data["impacto"])
            self._aggregate_data(aggregated, "stakeholders", data["stakeholders"])
            self._aggregate_data(aggregated, "etiquetas", data["etiquetas"])
            self._aggregate_data(aggregated, "divisiones_cnae", data["divisiones_cnae"])

            if data["ramas_juridicas"]:
                for rama, subramas in data["ramas_juridicas"].items():
                    if rama not in aggregated["ramas_juridicas"]:
                        aggregated["ramas_juridicas"][rama] = set()
                    # Merge subramas with unique values
                    aggregated["ramas_juridicas"][rama].update(subramas)

        # Convert sets to lists for final output
        for key, value in aggregated.items():
            if isinstance(value, set):
                aggregated[key] = list(value)
            elif isinstance(value, dict):
                for key2, value2 in value.items():
                    if isinstance(value2, set):
                        aggregated[key][key2] = list(value2)


        self.results = aggregated

    def _aggregate_data(self, dictionary, key, data):
        if isinstance(data, list):
            # If data is a list, add each item to the set
            for item in data:
                dictionary[key].add(item)
        else:
            # If data is a single value, add it to the set
            dictionary[key].add(data)

    def _clean_aggregated_results(self):
        results = self.results
        for key, value in results.items():
            if isinstance(value, list):
                if any(element != "No identificado" for element in value):
                    output = [
                        element for element in value if element != "No identificado"
                    ]
                    results[key] = output
            elif isinstance(value, dict):
                for key2, value2 in value.items():
                    if isinstance(value2, list):
                        if any(element != "No identificado" for element in value2):
                            output = [
                                element
                                for element in value2
                                if element != "No identificado"
                            ]
                            results[key][key2] = output

        self.results = results

    def _unify_summary(self):
        aggregated = self.results
        unified_summary = " ".join(aggregated["resumenes"])
        aggregated["resumenes"] = unified_summary
        self.results = aggregated

    def _generate_final_summary(self):
        summary = self.results["resumenes"]
        messages = [
            {
                "role": "system",
                "content": "Tu trabajo es integrar los disintos resumenes de diferentes apartados de un texto legal con el objetivo de proporcionar el resumen final más fidedigno, profesional, coherente y completo posible",
            },
            {"role": "user", "content": summary},
        ]

        client = self.initializer.openai_client
        response = client.chat.completions.create(
            model=self.config["model"],
            messages=messages,
            temperature=0,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        final_summary = response.choices[0].message.content
        self.results["resumenes"] = final_summary
        return (
            final_summary,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

    def _shorten_name(self, name: str):
        messages = [
            {
                "role": "system",
                "content": "Tu trabajo es acortar el nombre del documento a un nombre más corto, manteniendo la profesionalidad",
            },
            {"role": "user", "content": name},
        ]

        client = self.initializer.openai_client
        response = client.chat.completions.create(
            model=self.config["model"],
            messages=messages,
            temperature=0,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        short_name = response.choices[0].message.content

        self.results["short_name"] = short_name
