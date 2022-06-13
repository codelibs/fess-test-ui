# Fess UI Test

## Status

| Status | Fess | SearchEngine |
| ------ | ---- | ------------ |
| [![run-fess13-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess13-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess13-elasticsearch7.yml) | Fess 13 | Elasticsearch 7 |
| [![run-fess13-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess13-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess13-opensearch1.yml) | Fess 13 | OpenSearch 1 |
| [![run-fess14-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch7.yml) | Fess 14 | Elasticsearch 7 |
| [![run-fess14-elasticsearch8](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch8.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch8.yml) | Fess 14 | Elasticsearch 8 |
| [![run-fess14-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch1.yml) | Fess 14 | OpenSearch 1 |
| [![run-fess14-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch2.yml) | Fess 14 | OpenSearch 1 |
| [![run-fessx-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch7.yml) | Fess (snapshot) | Elasticsearch 7 |
| [![run-fessx-elasticsearch8](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch8.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch8.yml) | Fess (snapshot) | Elasticsearch 8 |
| [![run-fessx-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch1.yml) | Fess (snapshot) | OpenSearch 1 |
| [![run-fessx-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml) | Fess (snapshot) | OpenSearch 2 |

## Usage

### Build

```
$ docker-compose build
```

### Run

```
$ /bin/bash ./run_test.sh fess13 elasticsearch7
```

### Cleanup

```
$ docker system prune -f
$ docker volume prune -f
```
