from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

sequence_to_classify = """
La Ley de promoción de beneficios sociales y económicos en Galicia tiene como objetivo principal regular el uso sostenible de los recursos naturales en la región. Esta normativa integra la valoración de los impactos sociales y económicos en proyectos relacionados con la energía renovable, la minería y la gestión de residuos. Además, se establecen medidas específicas para fomentar la participación de la comunidad local en la toma de decisiones y se promueve la sostenibilidad ambiental, asegurando que el desarrollo económico no comprometa el bienestar social ni el equilibrio ecológico.
"""
candidate_labels = [
    "Agricultura, ganadería, silvicultura y pesca",
    "Actividades extractivas",
    "Industria manufacturera",
    "Suministro de electricidad, gas, vapor y aire acondicionado",
    "Suministro de agua; actividades de saneamiento, gestión de residuos y descontaminación",
    "Construcción",
    "Comercio al por mayor y al por menor; reparación de vehículos de motor y motocicletas",
    "Transporte y almacenamiento",
    "Hostelería",
    "Información y comunicaciones",
    "Actividades financieras y de seguros",
    "Actividades inmobiliarias",
    "Actividades profesionales, científicas y técnicas",
    "Actividades administrativas y servicios auxiliares",
    "Administración pública y defensa; seguridad social obligatoria",
    "Educación",
    "Actividades sanitarias y de servicios sociales",
    "Actividades artísticas, de entretenimiento y recreativas",
    "Otras actividades de servicios",
    "Actividades de los hogares como empleadores de personal doméstico; producción de bienes y servicios para uso propio",
    "Actividades de organizaciones y organismos extraterritoriales"
]
print(classifier(sequence_to_classify, candidate_labels, multi_label=True))
