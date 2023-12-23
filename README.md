# Fess UI Test

## Status

| Status | Fess | SearchEngine |
| ------ | ---- | ------------ |
| [![run-fess14-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch7.yml) | Fess 14 | Elasticsearch 7 |
| [![run-fess14-elasticsearch8](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch8.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-elasticsearch8.yml) | Fess 14 | Elasticsearch 8 |
| [![run-fess14-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch1.yml) | Fess 14 | OpenSearch 1 |
| [![run-fess14-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess14-opensearch2.yml) | Fess 14 | OpenSearch 2 |
| [![run-fessx-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch7.yml) | Fess (snapshot-deb) | Elasticsearch 7 |
| [![run-fessx-centos7-elasticsearch7](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-elasticsearch7.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-elasticsearch7.yml) | Fess (snapshot-rpm) | Elasticsearch 7 |
| [![run-fessx-elasticsearch8](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch8.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-elasticsearch8.yml) | Fess (snapshot-deb) | Elasticsearch 8 |
| [![run-fessx-centos7-elasticsearch8](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-elasticsearch8.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-elasticsearch8.yml) | Fess (snapshot-rpm) | Elasticsearch 8 |
| [![run-fessx-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch1.yml) | Fess (snapshot-deb) | OpenSearch 1 |
| [![run-fessx-centos7-opensearch1](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-opensearch1.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-opensearch1.yml) | Fess (snapshot-rpm) | OpenSearch 1 |
| [![run-fessx-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml) | Fess (snapshot-deb) | OpenSearch 2 |
| [![run-fessx-centos7-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-centos7-opensearch2.yml) | Fess (snapshot-rpm) | OpenSearch 2 |
| [![run-fess15-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-opensearch2.yml) | Fess (snapshot-deb) | OpenSearch 2 |
| [![run-fess15-al2023-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-al2023-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-al2023-opensearch2.yml) | Fess (snapshot-rpm) | OpenSearch 2 |

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
