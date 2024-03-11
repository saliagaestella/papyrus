import json
import os
import tiktoken
from src.initialize import Initializer
from src.docs_processor.utils import (
    create_chunks,
    extract_chunk,
    max_tokens_per_chunk,
)


class DocumentProcessor:
    def __init__(self, initializer: Initializer):
        self.initializer = initializer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.config = initializer.config
        self.results = None

    def process_document(self, text: str):
        clean_text = text.replace("  ", " ").replace("\n", "; ").replace(";", " ")
        max_tokens_response_summary = (
            int(self.config["max_words_response_summary"]) * 4 / 3
        )
        chunk_tokens = max_tokens_per_chunk(
            self.config["prompt"],
            max_tokens_response_summary,
            clean_text,
            self.config,
        )
        print(chunk_tokens)

        chunks = create_chunks(clean_text, chunk_tokens, self.tokenizer)
        text_chunks = [self.tokenizer.decode(chunk) for chunk in chunks]
        print(f"Number of API calls/document divisions: {len(text_chunks)}")

        self.results = [self._process_chunk(chunk) for chunk in text_chunks]
        self._postprocess_results()
        self._clean_aggregated_results()
        self._unify_legal_category()
        self._unify_summary()
        self._generate_final_summary()

        return self.results

    def _process_chunk(self, chunk: str):
        result, input_token, output_token = extract_chunk(
            chunk, self.config, self.initializer.openai_client
        )
        print(f"Result /n {result}")
        print(f"Number of input tokens: {input_token}")
        print(f"Number of output tokens: {output_token}")
        return result

    def _postprocess_results(self):
        aggregated = {
            "summaries": [],
            "labels": set(),
            "legal_categories": [],
            "impacts": set(),
            "stakeholders": set(),
        }

        for result in self.results:
            data = json.loads(result)
            aggregated["summaries"].append(data["resumen"])
            aggregated["legal_categories"].append(data["categoria_legal"])
            aggregated["impacts"].add(data["impacto"])
            self._aggregate_data(aggregated, "stakeholders", data["stakeholders"])
            self._aggregate_data(aggregated, "labels", data["etiquetas"])

        for key in aggregated.keys():
            if isinstance(aggregated[key], set):
                aggregated[key] = list(aggregated[key])
        self.results = aggregated

    def _aggregate_data(self, aggregated, key, data):
        if isinstance(data, list):
            for item in data:
                aggregated[key].add(item)
        else:
            aggregated[key].add(data)

    def _clean_aggregated_results(self):
        results = self.results
        for key in results:
            if isinstance(results[key], list):
                results[key] = [
                    element for element in results[key] if element != "No identificado"
                ]
        self.results = results

    def _unify_legal_category(self):
        aggregated = self.results
        category_weights = self._weighted_counts(aggregated["legal_categories"])
        aggregated["legal_categories"] = max(category_weights, key=category_weights.get)
        self.results = aggregated

    def _weighted_counts(self, items):
        weighting = {}
        additional_weight = len(items) / 2
        for i, item in enumerate(items):
            if item == "No identificado":
                continue
            weighting[item] = weighting.get(item, 0) + (
                1 + additional_weight if i == 0 else 1
            )
        return weighting

    def _unify_summary(self):
        aggregated = self.results
        unified_summary = " ".join(aggregated["summaries"])
        aggregated["summaries"] = unified_summary
        self.results = aggregated

    def _generate_final_summary(self):
        summary = self.results["summaries"]
        messages = [
            {
                "role": "system",
                "content": "Tu trabajo es integrar los disintos resumenes de diferentes apartados de un texto legal con el objetivo de proporcionar el resumen final más fidedigno, profesional, coherente y completo posible",
            },
            {"role": "user", "content": summary},
        ]

        client = self.initializer.openai_client
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        final_summary = response.choices[0].message.content
        self.results["summaries"] = final_summary
        return (
            final_summary,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )
