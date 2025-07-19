# Fess UI Test

## Status

| Status | Fess | SearchEngine |
| ------ | ---- | ------------ |
| [![run-fess14-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch7.yml) | Fess 14 | Elasticsearch 7 |
| [![run-fess14-elasticsearch8](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch8.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch8.yml) | Fess 14 | Elasticsearch 8 |
| [![run-fess14-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch1.yml) | Fess 14 | OpenSearch 1 |
| [![run-fess14-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch2.yml) | Fess 14 | OpenSearch 2 |
| [![run-fess14x-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-elasticsearch7.yml) | Fess 14.x | Elasticsearch 7 |
| [![run-fess14x-elasticsearch8](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-elasticsearch8.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-elasticsearch8.yml) | Fess 14.x | Elasticsearch 8 |
| [![run-fess14x-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-opensearch1.yml) | Fess 14.x | OpenSearch 1 |
| [![run-fess14x-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14x-opensearch2.yml) | Fess 14.x | OpenSearch 2 |
| [![run-fessx-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml) | Fess (snapshot-deb) | OpenSearch 2 |
| [![run-fessx-al2023-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch2.yml) | Fess (snapshot-rpm) | OpenSearch 2 |
| [![run-fessx-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch3.yml) | Fess (snapshot-deb) | OpenSearch 3 |
| [![run-fessx-al2023-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch3.yml) | Fess (snapshot-rpm) | OpenSearch 3 |
| [![run-fessx-noble-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch2.yml) | Fess (snapshot-noble) | OpenSearch 2 |
| [![run-fessx-noble-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch3.yml) | Fess (snapshot-noble) | OpenSearch 3 |

## Usage

### Build

```
$ docker compose build
```

### Run

```
$ /bin/bash ./run_test.sh fess14 opensearch2
```

### Cleanup

```
$ docker system prune -f
$ docker volume prune -f
```
