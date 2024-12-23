import json
import os
import tiktoken
import logging as lg
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

    def process_document(self, text: str, name: str = None):
        logger = lg.getLogger(self.process_document.__name__)
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

        logger.info(f"Total tokens in the chunk: {chunk_tokens}")

        chunks = create_chunks(clean_text, chunk_tokens, self.tokenizer)
        text_chunks = [self.tokenizer.decode(chunk) for chunk in chunks]
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

        return self.results

    def _process_chunk(self, chunk: str):
        logger = lg.getLogger(self._process_chunk.__name__)
        result, input_token, output_token = extract_chunk(
            chunk, self.config, self.initializer.openai_client
        )
        logger.info(f"Result: \n {result}")
        logger.info(f"Number of input tokens: {input_token}")
        logger.info(f"Number of output tokens: {output_token}")
        return result

    def _postprocess_results(self):
        aggregated = {
            "resumenes": [],
            "etiquetas": set(),
            "impactos": set(),
            "stakeholders": set(),
        }

        for result in self.results:
            data = json.loads(result)
            aggregated["resumenes"].append(data["resumen"])
            aggregated["impactos"].add(data["impacto"])
            self._aggregate_data(aggregated, "stakeholders", data["stakeholders"])
            self._aggregate_data(aggregated, "etiquetas", data["etiquetas"])

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
        etiquetas_posibles = [
            "Administración, defensa y servicios de seguridad social",
            "Maquinaria agrícola",
            "Productos agrícolas, ganaderos, pesqueros, forestales y relacionados",
            "Servicios agrícolas, forestales, hortícolas, acuícolas y apícolas",
            "Servicios de arquitectura, construcción, ingeniería e inspección",
            "Servicios empresariales: derecho, marketing, consultoría, reclutamiento, impresión y seguridad",
            "Productos químicos",
            "Ropa, calzado, artículos de equipaje y accesorios",
            "Agua recogida y purificada",
            "Estructuras de construcción y materiales; productos auxiliares para la construcción (excepto aparatos eléctricos)",
            "Trabajos de construcción",
            "Servicios de educación y formación",
            "Maquinaria eléctrica, aparatos, equipos y consumibles; iluminación",
            "Servicios financieros y de seguros",
            "Alimentos, bebidas, tabaco y productos relacionados",
            "Muebles (incl. mobiliario de oficina), artículos de decoración, electrodomésticos (excl. iluminación) y productos de limpieza",
            "Servicios de salud y trabajo social",
            "Servicios de hotel, restaurante y comercio minorista",
            "Servicios de TI: consultoría, desarrollo de software, Internet y soporte",
            "Maquinaria industrial",
            "Servicios de instalación (excepto software)",
            "Equipos de laboratorio, ópticos y de precisión (excl. gafas)",
            "Tejidos de cuero y textil, materiales plásticos y de caucho",
            "Maquinaria para minería, canteras, equipos de construcción",
            "Equipos médicos, farmacéuticos y productos de cuidado personal",
            "Minería, metales básicos y productos relacionados",
            "Instrumentos musicales, bienes deportivos, juegos, juguetes, artesanías, materiales de arte y accesorios",
            "Maquinaria de oficina y equipos de computación, suministros excepto muebles y paquetes de software",
            "Otros servicios comunitarios, sociales y personales",
            "Productos petrolíferos, combustible, electricidad y otras fuentes de energía",
            "Servicios postales y de telecomunicaciones",
            "Productos impresos y relacionados",
            "Servicios públicos",
            "Radio, televisión, comunicación, telecomunicación y equipos relacionados",
            "Servicios inmobiliarios",
            "Servicios recreativos, culturales y deportivos",
            "Servicios de reparación y mantenimiento",
            "Servicios de investigación y desarrollo y consultoría relacionada",
            "Equipamiento de seguridad, lucha contra incendios, policía y defensa",
            "Servicios relacionados con la industria del petróleo y gas",
            "Servicios de aguas residuales, eliminación de desechos, limpieza y medio ambiente",
            "Paquetes de software y sistemas de información",
            "Servicios de apoyo y auxiliares de transporte; servicios de agencias de viajes",
            "Equipos de transporte y productos auxiliares para el transporte",
            "Servicios de transporte (excl. transporte de residuos)",
        ]
        results = self.results
        for key, value in results.items():
            if isinstance(value, list):
                if any(element != "No identificado" for element in value):
                    output = [
                        element for element in value if element != "No identificado"
                    ]
                """if key == "etiquetas":
                    output = self._etiquetas_similares(
                        etiquetas_posibles, value, 0.5
                    )"""
                results[key] = output

        self.results = results

    """# Función para encontrar categorías de la lista1 que tienen una coincidencia aproximada en lista2
    def _etiquetas_similares(self, lista1, lista2, umbral):
        etiquetas_similares = []
        for etiqueta1 in lista1:
            etiqueta1_encontrada = False
            for etiqueta2 in lista2:
                # Calcular la distancia de Levenshtein y la similitud
                distancia = lev.distance(etiqueta1.lower(), etiqueta2.lower())
                longitud_maxima = max(len(etiqueta1), len(etiqueta2))
                similitud = (longitud_maxima - distancia) / longitud_maxima
                # Si la similitud supera el umbral y la etiqueta aún no se ha agregado, agregarla a la lista de resultados
                if similitud >= umbral and not etiqueta1_encontrada:
                    etiquetas_similares.append(etiqueta1)
                    etiqueta1_encontrada = True
                    break  # No es necesario seguir buscando más coincidencias para esta etiqueta
        return etiquetas_similares"""

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