# Fess UI Test

## Status

| Status | Fess | SearchEngine |
| ------ | ---- | ------------ |
| [![run-fessx-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch2.yml) | Fess (snapshot-deb) | OpenSearch 2 |
| [![run-fessx-al2023-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch2.yml) | Fess (snapshot-rpm) | OpenSearch 2 |
| [![run-fessx-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-opensearch3.yml) | Fess (snapshot-deb) | OpenSearch 3 |
| [![run-fessx-al2023-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-al2023-opensearch3.yml) | Fess (snapshot-rpm) | OpenSearch 3 |
| [![run-fessx-noble-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch2.yml) | Fess (snapshot-noble) | OpenSearch 2 |
| [![run-fessx-noble-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fessx-noble-opensearch3.yml) | Fess (snapshot-noble) | OpenSearch 3 |
| [![run-fess15-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-opensearch2.yml) | Fess 15 | OpenSearch 2 |
| [![run-fess15-al2023-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-al2023-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-al2023-opensearch2.yml) | Fess 15 (al2023) | OpenSearch 2 |
| [![run-fess15-al2023-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-al2023-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-al2023-opensearch3.yml) | Fess 15 (al2023) | OpenSearch 3 |
| [![run-fess15-noble-opensearch2](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-noble-opensearch2.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-noble-opensearch2.yml) | Fess 15 (noble) | OpenSearch 2 |
| [![run-fess15-noble-opensearch3](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-noble-opensearch3.yml/badge.svg)](https://github.com/codelibs/fess-test-ui/actions/workflows/run-fess15-noble-opensearch3.yml) | Fess 15 (noble) | OpenSearch 3 |

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
