from rdflib import Graph, URIRef
import pandas as pd
import os

def guess_format(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.ttl', '.turtle'):
        return 'turtle'
    if ext in ('.rdf', '.xml', '.owl'):
        return 'xml'
    return None

def analyze_ontology(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    g = Graph()
    fmt = guess_format(file_path)
    try:
        if fmt:
            g.parse(file_path, format=fmt)
        else:
            g.parse(file_path)
    except Exception as e:
        raise RuntimeError(f"Ошибка при разборе {file_path}: {e}")

    RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    OWL_CLASS = URIRef("http://www.w3.org/2002/07/owl#Class")
    OWL_OBJECT_PROPERTY = URIRef("http://www.w3.org/2002/07/owl#ObjectProperty")
    OWL_NAMED_INDIVIDUAL = URIRef("http://www.w3.org/2002/07/owl#NamedIndividual")

    classes = sum(1 for _ in g.subjects(predicate=RDF_TYPE, object=OWL_CLASS))
    properties = sum(1 for _ in g.subjects(predicate=RDF_TYPE, object=OWL_OBJECT_PROPERTY))
    individuals = sum(1 for _ in g.subjects(predicate=RDF_TYPE, object=OWL_NAMED_INDIVIDUAL))

    print(f"{os.path.basename(file_path)} — Классы: {classes}, Свойства: {properties}, Индивиды: {individuals}")

    return {"classes": classes, "properties": properties, "individuals": individuals}

if __name__ == "__main__":
    #  пути к файлам
    stats_original = analyze_ontology("/home/dmitriy-dybov/pizza.rdf")
    stats_modified = analyze_ontology("/home/dmitriy-dybov/pizza_russian.rdf")

    report = pd.DataFrame([stats_original, stats_modified], index=["Original", "Modified"])
    report.to_csv("ontology_report.csv")
    print("Отчёт сохранён: ontology_report.csv")
