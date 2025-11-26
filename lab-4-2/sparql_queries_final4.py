#!/usr/bin/env python3
# coding: utf-8

from SPARQLWrapper import SPARQLWrapper, JSON, XML
import pandas as pd
from rdflib import Graph, Namespace
from rdflib.plugins.stores import sparqlstore
import sys

ENDPOINT_QUERY = "http://localhost:3030/pizza_ds/sparql"
ENDPOINT_UPDATE = "http://localhost:3030/pizza_ds/update"

def run_query(sparql, query, return_format=JSON):
    sparql.setQuery(query)
    sparql.setReturnFormat(return_format)
    try:
        res = sparql.query().convert()
        return res
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}", file=sys.stderr)
        try:
            if hasattr(e, 'response') and e.response is not None:
                body = e.response.read()
                print(body, file=sys.stderr)
        except Exception:
            pass
        return None

def main():
    sparql = SPARQLWrapper(ENDPOINT_QUERY)
    sparql.setReturnFormat(JSON)

    # Query 1 — все классы (с меткой)
    query1 = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?class ?label WHERE {
      ?class a owl:Class .
      OPTIONAL { ?class rdfs:label ?label }
    }
    ORDER BY ?class
    """
    results1 = run_query(sparql, query1)
    if results1 and "results" in results1:
        print("Классы онтологии:")
        for result in results1["results"]["bindings"]:
            cls = result["class"]["value"]
            label = result.get("label", {}).get("value", "No label")
            print(f"{cls} - {label}")

    # Query 2 — все пиццы как подклассы pizza:Pizza (используем промежуточную ?label)
    query2 = """
    PREFIX pizza: <http://www.co-ode.org/ontologies/pizza/pizza.owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?pizza (SAMPLE(?label) AS ?name) WHERE {
      { ?pizza rdfs:subClassOf+ pizza:Pizza } UNION { ?pizza rdf:type pizza:Pizza }
      OPTIONAL { ?pizza rdfs:label ?label }
    }
    GROUP BY ?pizza
    ORDER BY ?name
    """
    results2 = run_query(sparql, query2)
    if results2 and "results" in results2:
        print("\nВсе пиццы (подклассы или экземпляры pizza:Pizza):")
        for result in results2["results"]["bindings"]:
            name = result.get('name', {}).get('value')
            uri = result['pizza']['value']
            print(f"{name or uri}")

    # -----------------------------
    # Исправлённый Query 3 — пиццы с грибами
    # Учитывает: подклассы pizza:Pizza, экземпляры, Restriction owl:someValuesFrom и прямые тройки.
    # -----------------------------
    query3 = """
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
    PREFIX pizza:<http://www.co-ode.org/ontologies/pizza/pizza.owl#>

    SELECT ?pizza (SAMPLE(COALESCE(?pLabel, STRAFTER(STR(?pizza), "#"))) AS ?name)
                  (SAMPLE(COALESCE(?tLabel, STRAFTER(STR(?tClass), "#"))) AS ?topping)
    WHERE {
      { ?pizza rdfs:subClassOf+ pizza:Pizza } UNION { ?pizza rdf:type pizza:Pizza }
      OPTIONAL { ?pizza rdfs:label ?pLabel }

      # 1) Restriction case: class rdfs:subClassOf _:r . _:r owl:onProperty pizza:hasTopping ; owl:someValuesFrom ?tClass .
      OPTIONAL {
        ?pizza rdfs:subClassOf+ ?rnode .
        ?rnode a owl:Restriction .
        ?rnode owl:onProperty pizza:hasTopping .
        ?rnode owl:someValuesFrom ?tClass .
      }

      # 2) Direct triple case (instance hasTopping someIndividualOfClass)
      OPTIONAL {
        ?pizza pizza:hasTopping ?tInst .
        ?tInst a ?tClass .
      }

      OPTIONAL { ?tClass rdfs:label ?tLabel }

      # Фильтр по грибам — классом или подклассом MushroomTopping
      FILTER (
        BOUND(?tClass) &&
        ( ?tClass = pizza:MushroomTopping || EXISTS { ?tClass rdfs:subClassOf+ pizza:MushroomTopping } )
      )
    }
    GROUP BY ?pizza
    ORDER BY ?name
    """
    results3 = run_query(sparql, query3)
    print("\nПиццы с грибами:")
    if results3 and "results" in results3 and results3["results"]["bindings"]:
        for result in results3["results"]["bindings"]:
            name = result.get('name', {}).get('value')
            topping = result.get('topping', {}).get('value')
            print(f"{name or result['pizza']['value']} - {topping}")
    else:
        print("Нет результатов для пицц с грибами")

    # -----------------------------
    # Исправлённый Query 4 — популярные начинки (топ 10)
    # Считает количество разных пицц (подклассы или экземпляры), где используется каждая начинка-класс.
    # -----------------------------
    query4 = """
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
    PREFIX pizza:<http://www.co-ode.org/ontologies/pizza/pizza.owl#>

    SELECT (SAMPLE(COALESCE(?tLabel, STRAFTER(STR(?tClass), "#"))) AS ?topping)
           (COUNT(DISTINCT ?pizza) AS ?count)
    WHERE {
      # pizza как подкласс или экземпляр
      { ?pizza rdfs:subClassOf+ pizza:Pizza } UNION { ?pizza rdf:type pizza:Pizza }
      OPTIONAL { ?pizza rdfs:label ?pLabel }

      # Получаем класс начинки из Restriction или из прямых тройк
      OPTIONAL {
        ?pizza rdfs:subClassOf+ ?rnode .
        ?rnode a owl:Restriction .
        ?rnode owl:onProperty pizza:hasTopping .
        ?rnode owl:someValuesFrom ?tClass .
      }
      OPTIONAL {
        ?pizza pizza:hasTopping ?tInst .
        ?tInst a ?tClass .
      }

      OPTIONAL { ?tClass rdfs:label ?tLabel }

      # Убедимся что tClass определён
      FILTER( BOUND(?tClass) )
    }
    GROUP BY ?tClass
    ORDER BY DESC(?count)
    LIMIT 10
    """
    results4 = run_query(sparql, query4)
    print("\nПопулярные начинки:")
    if results4 and "results" in results4 and results4["results"]["bindings"]:
        for result in results4["results"]["bindings"]:
            topping = result.get('topping', {}).get('value', 'No label')
            count = result['count']['value']
            print(f"{topping}: {count}")
    else:
        print("Нет данных по популярным начинкам")

    # Query 5 — CONSTRUCT (вернём XML/RDF) — тоже используем путь для начинок
    query5 = """
    PREFIX pizza: <http://www.co-ode.org/ontologies/pizza/pizza.owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ex: <http://example.org/vegetarian#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    CONSTRUCT {
      ?pizza ex:isVegetarian true .
      ?pizza ex:hasTopping ?topping .
    } WHERE {
      { ?pizza rdfs:subClassOf+ pizza:Pizza } UNION { ?pizza rdf:type pizza:Pizza }

      # извлекаем начинку из Restriction или из прямой тройки
      OPTIONAL {
        ?pizza rdfs:subClassOf+ ?rnode .
        ?rnode a owl:Restriction .
        ?rnode owl:onProperty pizza:hasTopping .
        ?rnode owl:someValuesFrom ?topping .
      }
      OPTIONAL {
        ?pizza pizza:hasTopping ?tInst .
        ?tInst a ?topping .
      }

      FILTER NOT EXISTS { ?topping a pizza:MeatTopping . }
    }
    """
    results5 = run_query(sparql, query5, return_format=XML)
    if results5:
        try:
            with open("vegetarian_pizzas.rdf", "w", encoding="utf-8") as f:
                if isinstance(results5, bytes):
                    f.write(results5.decode("utf-8"))
                else:
                    f.write(str(results5))
            print("\nCONSTRUCT запрос выполнен, сохранён vegetarian_pizzas.rdf")
        except Exception as e:
            print(f"Ошибка сохранения CONSTRUCT результата: {e}", file=sys.stderr)

    # RDFLib через SPARQL endpoint (чтение) — пример с подклассами/экземплярами
    store = sparqlstore.SPARQLUpdateStore()
    try:
        store.open((ENDPOINT_QUERY, ENDPOINT_UPDATE))
        g = Graph(store=store)
        PIZZA = Namespace("http://www.co-ode.org/ontologies/pizza/pizza.owl#")
        RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        g.bind("pizza", PIZZA)
        g.bind("rdfs", RDFS)

        query6 = """
        PREFIX pizza: <http://www.co-ode.org/ontologies/pizza/pizza.owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?pizza ?label WHERE {
          ?pizza rdfs:subClassOf+ pizza:Pizza .
          OPTIONAL { ?pizza rdfs:label ?label }
        } LIMIT 50
        """
        results6 = g.query(query6)
        print("\nРезультаты через RDFLib:")
        for row in results6:
            label = getattr(row, "label", None)
            pizza_uri = getattr(row, "pizza", None)
            if label:
                print(f"{pizza_uri} - {label}")
            else:
                print(f"{pizza_uri}")
    except Exception as e:
        print(f"Ошибка при работе через RDFLib/SPARQLUpdateStore: {e}", file=sys.stderr)
    finally:
        try:
            store.close()
        except Exception:
            pass

    # Генерация простого отчёта через SELECT COUNT
    def generate_ontology_report(sparql_wrapper):
        queries = {
            "total_classes": """
              PREFIX owl: <http://www.w3.org/2002/07/owl#>
              SELECT (COUNT(DISTINCT ?class) AS ?count) WHERE { ?class a owl:Class }
            """,
            "total_properties": """
              PREFIX owl: <http://www.w3.org/2002/07/owl#>
              SELECT (COUNT(DISTINCT ?prop) AS ?count) WHERE { ?prop a owl:ObjectProperty }
            """,
            "total_individuals": """
              PREFIX owl: <http://www.w3.org/2002/07/owl#>
              SELECT (COUNT(DISTINCT ?ind) AS ?count) WHERE { ?ind a owl:NamedIndividual }
            """
        }
        report = {}
        for name, q in queries.items():
            res = run_query(sparql_wrapper, q)
            if res and "results" in res and res["results"]["bindings"]:
                report[name] = res["results"]["bindings"][0]["count"]["value"]
            else:
                report[name] = None
        df = pd.DataFrame([report])
        df.to_csv("ontology_report.csv", index=False)
        return report

    ontology_stats = generate_ontology_report(sparql)
    print("\nСтатистика онтологии:")
    for key, value in ontology_stats.items():
        print(f"{key}: {value}")

    # Тест endpoint'ов (короткий тест)
    def test_endpoints():
        endpoints = [
            "http://localhost:3030/pizza_ds/sparql",
            "http://dbpedia.org/sparql",
            "https://query.wikidata.org/sparql"
        ]
        test_query = "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o } LIMIT 1"
        for endpoint in endpoints:
            try:
                sp = SPARQLWrapper(endpoint)
                sp.setQuery(test_query)
                sp.setReturnFormat(JSON)
                r = sp.query().convert()
                count = r["results"]["bindings"][0]["count"]["value"]
                print(f"{endpoint}: Работает ({count} triplets)")
            except Exception:
                print(f"{endpoint}: Не доступен")
    test_endpoints()

if __name__ == "__main__":
    main()
