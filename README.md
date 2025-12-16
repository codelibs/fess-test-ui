# Fess UI Test

Automated UI testing suite for [Fess](https://fess.codelibs.org/) (Enterprise Search Server) using Playwright with Python. This repository provides comprehensive end-to-end testing for Fess admin interface functionality across multiple versions and search engine configurations.

## Key Features

- **Multi-Version Testing**: Supports Fess 15.x and snapshot builds across different OS distributions (Debian, AL2023, Noble)
- **Multi-Engine Support**: Tests against OpenSearch 2.x and 3.x configurations
- **Comprehensive Admin UI Coverage**: Tests all major admin functionality including search configurations, dictionaries, user management, and content management
- **Coverage Analysis**: HTML capture and DOM analysis to identify untested UI elements with automatic test stub generation
- **Docker-Based**: Fully containerized test environment with dynamic compose file selection
- **Japanese UI Support**: Native testing of Japanese Fess interface elements
- **Enhanced Logging**: Comprehensive logging with configurable levels and browser interaction tracking

## Tech Stack

- **Testing Framework**: [Playwright](https://playwright.dev/) 1.56.0 with Python
- **HTML Analysis**: [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) for DOM parsing
- **Containerization**: Docker & Docker Compose
- **Search Engines**: OpenSearch 2.19.1, OpenSearch 3.3.0
- **Fess Versions**: 15.3.2 (stable), snapshot builds
- **Base Images**: Microsoft Playwright (Ubuntu Noble), CodeLibs Fess & OpenSearch

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

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Linux/macOS/Windows with Docker support

### Basic Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/codelibs/fess-test-ui.git
   cd fess-test-ui
   ```

2. **Build the test container**
   ```bash
   docker compose build
   ```

3. **Run tests** (specify both Fess version and search engine)
   ```bash
   # Fess 15.x with OpenSearch
   ./run_test.sh fess15 opensearch2
   ./run_test.sh fess15-al2023 opensearch2
   ./run_test.sh fess15-al2023 opensearch3
   ./run_test.sh fess15-noble opensearch2
   ./run_test.sh fess15-noble opensearch3

   # Fess snapshot builds with OpenSearch
   ./run_test.sh fessx opensearch2
   ./run_test.sh fessx opensearch3
   ./run_test.sh fessx-al2023 opensearch2
   ./run_test.sh fessx-al2023 opensearch3
   ./run_test.sh fessx-noble opensearch2
   ./run_test.sh fessx-noble opensearch3
   ```

## Available Configurations

### Fess Versions
- `fess15` - Fess 15.2.0 (Debian-based)
- `fess15-al2023` - Fess 15.2.0 (Amazon Linux 2023)
- `fess15-noble` - Fess 15.2.0 (Ubuntu Noble)
- `fessx` - Latest snapshot (Debian-based)
- `fessx-al2023` - Latest snapshot (Amazon Linux 2023)
- `fessx-noble` - Latest snapshot (Ubuntu Noble)

### Search Engines
- `opensearch2` - OpenSearch 2.19.1
- `opensearch3` - OpenSearch 3.3.0

## Configuration

### Environment Variables

#### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FESS_URL` | `http://localhost:8080` | Fess instance URL |
| `FESS_USERNAME` | `admin` | Admin username |
| `FESS_PASSWORD` | `admin` | Admin password |
| `BROWSER_LOCALE` | `ja-JP` | Browser locale for Playwright |
| `HEADLESS` | `false` (CI: `true`) | Run browser in headless mode |
| `TEST_LABEL` | (auto-generated) | Override test label generation |
| `TEST_MODULES` | `all` | Comma-separated list of modules to run |
| `FESS_DICTIONARY_PATH` | (engine-specific) | Dictionary path for Fess |

#### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | `false` | Enable file logging |
| `LOG_DIR` | `logs` | Directory for log files |

#### Tracing Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TRACE_ON_FAILURE` | `false` | Save Playwright traces for failed tests |
| `TRACE_ALL` | `false` | Save traces for all tests |
| `TRACE_DIR` | `traces` | Directory for trace files |

#### HTML Capture & Coverage Analysis

| Variable | Default | Description |
|----------|---------|-------------|
| `HTML_CAPTURE` | `false` | Enable HTML capture (`true`, `false`, `on_failure`) |
| `HTML_CAPTURE_DIR` | `html_snapshots` | Directory for HTML snapshots |
| `COVERAGE_ANALYSIS` | `false` | Run coverage analysis after tests |
| `COVERAGE_REPORT_FORMAT` | `json` | Report format (`json`, `html`, `md`, `all`) |
| `COVERAGE_REPORT_DIR` | `coverage_reports` | Directory for coverage reports |
| `COVERAGE_GENERATE_STUBS` | `false` | Generate test stubs for untested elements |
| `COVERAGE_STUB_DIR` | `generated_tests` | Directory for generated test stubs |

### Custom Configuration

Create a `.env.local` file to override defaults:
```bash
FESS_URL=http://my-fess-instance:8080
FESS_USERNAME=testuser
FESS_PASSWORD=testpass
HEADLESS=true
```

### Running with Coverage Analysis

To capture HTML and analyze test coverage:
```bash
HTML_CAPTURE=true \
COVERAGE_ANALYSIS=true \
COVERAGE_REPORT_FORMAT=all \
COVERAGE_GENERATE_STUBS=true \
./run_test.sh fess15 opensearch2
```

This generates:
- `html_snapshots/` - Captured HTML files with metadata
- `coverage_reports/` - Coverage reports in JSON, HTML, and Markdown formats
- `generated_tests/` - Auto-generated test stubs for untested elements

## Testing Features

The test suite covers the following Fess admin functionality:

### Core Admin Features
- **Access Tokens**: Create, update, delete access tokens
- **Bad Words**: Suggestion exclusion word management
- **Boost Documents**: Document ranking boost configuration
- **Users & Groups**: User account and group management
- **Roles**: Role-based access control
- **Labels**: Search result labeling
- **Virtual Hosts**: Virtual host configuration

### Search Configuration
- **Web Crawl Config**: Web crawling configuration management
- **File Crawl Config**: File system crawling setup
- **Duplicate Hosts**: Duplicate content handling
- **Key Match**: Keyword matching rules
- **Elevate Words**: Search result elevation
- **Related Content**: Related content suggestions
- **Related Queries**: Related query suggestions

### Dictionary Management
- **Kuromoji**: Japanese morphological analysis dictionary
- **Synonyms**: Synonym dictionary management
- **Mapping**: Field mapping configurations
- **Protected Words**: Word protection rules
- **Stemmer Override**: Stemming override rules
- **Stop Words**: Stop word management

## Project Structure

```
fess-test-ui/
├── src/                              # Test source code
│   ├── main.py                       # Test execution entry point
│   ├── run.sh                        # Container startup script
│   └── fess/
│       └── test/
│           ├── __init__.py           # Test utilities and assertions
│           ├── logging_config.py     # Logging configuration
│           ├── result.py             # Test result collection
│           ├── metrics.py            # Performance metrics tracking
│           ├── capture/              # HTML capture module
│           │   ├── __init__.py
│           │   └── html_capture.py   # HTML snapshot capture
│           ├── coverage/             # Coverage analysis module
│           │   ├── __init__.py
│           │   ├── models.py         # Data models (DOMElement, PageInventory, etc.)
│           │   ├── analyzer.py       # DOM analysis engine
│           │   ├── inventory.py      # Element inventory management
│           │   ├── reporter.py       # Coverage report generation
│           │   └── generator.py      # Test stub generation
│           └── ui/
│               ├── context.py        # FessContext class for browser management
│               ├── testdata.py       # Test data builders and patterns
│               └── admin/            # Admin UI test modules
│                   ├── badword/      # Bad word management tests
│                   ├── user/         # User management tests
│                   ├── dict/         # Dictionary management tests
│                   └── ...           # Other admin feature tests
├── compose.yaml                      # Base test container configuration
├── compose-fess15.yaml               # Fess 15 configuration
├── compose-fessx.yaml                # Fess snapshot configuration
├── compose-opensearch2.yaml          # OpenSearch 2 configuration
├── compose-opensearch3.yaml          # OpenSearch 3 configuration
├── run_test.sh                       # Test execution script
├── Dockerfile                        # Test container image
└── requirements.txt                  # Python dependencies
```

## Test Development

### Running Individual Tests

```bash
# Run specific test module
cd src
python -m fess.test.ui.admin.badword.add

# Run with custom Playwright instance
python fess/test/ui/admin/user/add.py
```

### Test Pattern

Each test module follows a consistent pattern:

```python
def setup(playwright: Playwright) -> FessContext:
    """Create and configure test context"""

def run(context: FessContext) -> None:
    """Execute test steps"""

def destroy(context: FessContext) -> None:
    """Clean up test context"""
```

### Adding New Tests

1. Create test module in appropriate `src/fess/test/ui/admin/` subdirectory
2. Implement `run(context)` function with Playwright interactions
3. Use Japanese UI selectors (e.g., `text=新規作成`, `text=作成`)
4. Add assertions using `assert_equal` and `assert_not_equal`
5. Update module `__init__.py` to include new test

### Using Coverage Analysis to Improve Tests

The coverage analysis feature helps identify untested UI elements:

1. **Run tests with HTML capture**:
   ```bash
   HTML_CAPTURE=true ./run_test.sh fess15 opensearch2
   ```

2. **Analyze coverage**:
   ```bash
   COVERAGE_ANALYSIS=true COVERAGE_REPORT_FORMAT=html ./run_test.sh fess15 opensearch2
   ```

3. **Generate test stubs for untested elements**:
   ```bash
   COVERAGE_GENERATE_STUBS=true ./run_test.sh fess15 opensearch2
   ```

4. **Review generated files**:
   - `coverage_reports/coverage_report.html` - Interactive coverage report
   - `generated_tests/test_coverage_gaps.py` - Test stubs for untested elements

### Test Output Directories

| Directory | Description |
|-----------|-------------|
| `test_results.json` | Test execution results |
| `test_metrics_history.json` | Historical performance metrics |
| `screenshots/` | Failure screenshots |
| `traces/` | Playwright trace files |
| `logs/` | Test execution logs |
| `html_snapshots/` | Captured HTML pages |
| `coverage_reports/` | Coverage analysis reports |
| `coverage_data/` | Element inventory data |
| `generated_tests/` | Auto-generated test stubs |

## Troubleshooting

### Common Issues

**Tests fail with timeout errors**
- Increase wait time or check if Fess is properly started
- Verify container networking connectivity

**Browser launch failures**
- Ensure Docker container has sufficient resources
- Check Playwright installation in container

**Assertion failures**
- Verify Japanese text selectors match current Fess UI
- Check if test data cleanup completed properly

### Debug Mode

Run tests with visible browser:
```bash
export HEADLESS=false
./run_test.sh fess15 opensearch2
```

### Log Analysis

Container logs provide detailed execution information:
```bash
docker compose logs test01
```

## Cleanup

### Remove Test Containers and Volumes

```bash
docker system prune -f
docker volume prune -f
```

### Reset Test Environment

```bash
docker compose down -v
docker compose build --no-cache
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-test`)
3. Add tests following existing patterns
4. Ensure all tests pass: `./run_test.sh fess15 opensearch2`
5. Submit pull request

### Code Style

- Follow existing Python patterns and naming conventions
- Use descriptive test method and variable names
- Include appropriate assertions and error handling
- Document complex test scenarios

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
