# vinlottis-vinmonopolet-to-elastic
Scrape vinmonopolet and add to local elastic instance

## Requirements
- Python 3
- Elasticsearch running and available at localhost:9200.

Install elasticsearch using docker: 
```bash
docker network create elastic
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.12.1
docker run --name es01 --net elastic -p 9200:9200 -p 9300:9300 -e "http.host=0.0.0.0" -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.12.1
```

## Run

Start scraping:
```bash
python3 main.py
```

## Query elasticsearch using curl

GET response by wine id, limit to single document sorted newest ingest timestamp:

```bash
curl http://localhost:9200/wines*/_search -H 'Content-Type: application/json' -d '
{
  "size": 1,
  "query": {
    "match": {
      "wine.code": 1381301
    }
  },
  "_source": {
    "includes": "wine"
  },
  "sort": [
    {
      "@timestamp": "desc"
    }
  ]
}
' | python3 -m json.tool
```

GET response by query, search wine name result sorted by score:
```bash
curl http://localhost:9200/wines*/_search -H 'Content-Type: application/json' -d '
{
  "from": 0,
  "size": 5,
  "query": {
    "multi_match" : {
        "query" : "Fruit",
        "fields": ["wine.name"],
        "fuzziness": 2
    }
  },
  "sort": [
    {
      "_score": {
        "order": "desc"
      }
    }
  ], 
  "_source": {
    "includes": "wine"
  }
}
' | python3 -m json.tool
```

GET total document count for wines index:
```bash
curl http://localhost:9200/wines/_count | python3 -m json.tool
```

GET latest document in wines index:
```bash
curl -X POST http://localhost:9200/wines*/_search -H 'Content-Type: application/json' -d '                              
{
   "size": 1,
   "sort": { "@timestamp": "desc"},
   "query": {
      "match_all": {}
   }
}
' | python3 -m json.tool
```
