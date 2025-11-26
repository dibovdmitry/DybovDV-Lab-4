# МИНИCTEPCTBO НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ
## Федеральное государственное автономное образовательное учреждение высшего образования «Северо-Кавказский федеральный университет» 
### Институт перспективной инженерии
### Отчет по лабораторной работе 4
### Знакомство с онтологиями в Protégé. Работа с SPARQL запросами. Извлечение данных с помощью LLM
Дата: 2025-11-25 \
Семестр: [2 курс 1 полугодие - 3 семестр] \
Группа: ПИН-м-о-24-1 \
Дисциплина: Технологии программирования \
Студент: Дыбов Д.В.

#### Цель работы
Освоение базовых принципов работы с онтологиями и семантическими технологиями через инструмент Protégé; изучение языка запросов SPARQL; исследование возможностей использования языковых моделей LLM для генерации SPARQL запросов по текстовым описаниям на естественном языке.

#### Теоретическая часть
- Краткие изученные концепции:
- Онтологии: классы, подклассы, свойства object properties и data properties, индивиды, аннотации.
- Protégé: загрузка, редактирование, сохранение в форматах TTL и RDF, использование reasoner для логического вывода.
- SPARQL: типы запросов SELECT, ASK, CONSTRUCT, UPDATE; PREFIX, фильтры, агрегаты.
- Apache Jena Fuseki: развертывание SPARQL endpoint, загрузка датасетов, выполнение запросов через HTTP.
- LLM: генерация SPARQL по естественному языку, необходимость валидации и пост обработки.

#### Практическая часть
##### Выполненные задачи
- [x] Установка Java для запуска Protégé.
- [x] Скачивание и запуск Protégé; загрузка образовательной онтологии; изучение классов, свойств и индивидов.
- [x] Добавление субкласса RussianPizza, аннотаций и ограничений hasTopping some RedOnion и hasTopping some Sausage.
- [x] Создание нового объектного свойства с доменом Pizza и диапазоном PizzaTopping.
- [x] Запуск reasoner и проверка автоматической классификации.
- [x] Выполнение DL Query Pizza and hasTopping value MushroomTopping.
- [x] Экспорт онтологии в ttl и rdf.
- [x] Получение отчёта об онтологии с помощью report_ontology.py.
- [x] Установка и запуск Apache Jena Fuseki; создание датасета и загрузка данных.
- [x] Написание и выполнение SPARQL запросов в sparql_queries.py.
- [x] Установка transformers, SPARQLWrapper, rdflib, openai; написание скрипта интеграции LLM для генерации SPARQL.

##### Ключевые фрагменты кода
- Скрипт report_ontology.py
```
python
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
```
- Скрипт sparql_queries.py
```
python
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

    # Все классы
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

    # Все пиццы как подклассы pizza:Pizza
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

    # Пиццы с грибами
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

    # Популярные начинки (топ 10)
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

      # Класс начинки из Restriction или из прямых тройк
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

    # CONSTRUCT
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

      # Извлечение начинки из Restriction или из прямой тройки
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

    # RDFLib через SPARQL endpoint
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

    # Тест endpoint'ов
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
```
- Скрипт llm_sparql_generation.py
```
python

```
##### Результаты выполнения

1. Java установлена;
2. Protégé скачан, распакован и запущен;
3. Онтология загружена и изучена.
![скриншот](report/Screenshot1.png "Установка Java и запуск Protégé") 
Рисунок 1 — Установка Java и запуск Protégé


4. Просмотрены классы, индивиды, аннотации;

Рисунок 2 
5. Добавлен RussianPizza с аннотацией и ограничениями.

![скриншот](report/Screenshot2.png "Классы и индивиды") Рисунок 2 — Классы и индивиды; добавление субкласса

Reasoner и DL Query

Выполнен логический вывод; проверена автоматическая классификация; DL Query: Pizza and hasTopping value MushroomTopping.

![скриншот](report/Screenshot3.png "Результат reasoner") Рисунок 3 — Результат работы reasoner и DL Query

Экспорт онтологии и отчёт

Онтология экспортирована в ttl и rdf; отчёт сформирован скриптом report_ontology.py.

![скриншот](report/Screenshot4.png "Экспорт онтологии") Рисунок 4 — Экспорт и отчёт

Fuseki и загрузка данных

Apache Jena Fuseki установлен и запущен; создан датасет, загружены RDF данные; выполнены SPARQL запросы.

![скриншот](report/Screenshot5.png "Fuseki загрузка") Рисунок 5 — Fuseki: создание датасета и загрузка данных

SPARQL запросы и результаты

Написаны и выполнены запросы в sparql_queries.py; получены табличные результаты и подсчёты триплетов.

![скриншот](report/Screenshot6.png "Результаты SPARQL") Рисунок 6 — Примеры результатов SPARQL

Интеграция с LLM

Установлены transformers, SPARQLWrapper, rdflib, openai; написан скрипт генерации SPARQL из текста.

При использовании тяжёлых моделей возникали ошибки скачивания и OOM; применена distilgpt2 и режимы с ограничением памяти.

![скриншот](report/Screenshot7.png "LLM генерация") Рисунок 7 — Генерация SPARQL с помощью LLM

Тестирование
[x] Модульные тесты — не применялись (фокус на изучении инструментов).
[x] Интеграционные тесты — проверены: Protégé ↔ экспорт RDF ↔ Fuseki ↔ SPARQLWrapper ↔ LLM.
[x] Производительность — выявлены ограничения по памяти при использовании больших LLM; рекомендовано тестировать на выделенных ресурсах.

Таблица ключевых артефактов
Артефакт	Описание
ontology.ttl	Экспорт онтологии в Turtle
ontology.rdf	Экспорт онтологии в RDF XML
report_ontology.py	Скрипт для извлечения сведений об онтологии
sparql_queries.py	Примеры SPARQL запросов и получение результатов
llm_to_sparql.py	Схема генерации SPARQL с помощью LLM
Sources: локальные результаты экспериментов и скрипты проекта

Важные замечания и рекомендации
Валидация LLM: сгенерированные LLM запросы требуют проверки; добавляйте PREFIX и проверяйте синтаксис перед выполнением.

Ресурсы: для больших моделей требуется много RAM; используйте облегчённые модели или выделенные серверы.

Резервирование данных: храните версии онтологий и делайте бэкапы Fuseki датасетов.

Воспроизводимость: фиксируйте версии библиотек в requirements.txt и сохраняйте конфигурации в config.yaml.

Выводы
Освоены базовые операции в Protégé: загрузка, редактирование онтологий, добавление классов, свойств и аннотаций, использование reasoner.

Получены практические навыки работы с SPARQL: формирование запросов, выполнение через Fuseki и программно, анализ результатов.

Исследована интеграция LLM для генерации SPARQL: подход работоспособен, но требует валидации и учёта ограничений по ресурсам; облегчённые модели и ручная пост обработка повышают надёжность.

Рекомендации: хранить версии онтологий, использовать CI для проверки целостности RDF, применять удалённые хранилища и выделенные вычислительные ресурсы для LLM задач.

Приложения
- Скрипты: report_ontology.py, sparql_queries.py, llm_to_sparql.py.
- Экспорт онтологии: ontology.ttl, ontology.rdf.
- Инструкции по запуску Fuseki и загрузке датасета (см. раздел Ключевые фрагменты кода).
- Скриншоты результатов: изображения помещены в папку report.
