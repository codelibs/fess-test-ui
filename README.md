# Fess UI Test

Automated UI testing suite for [Fess](https://fess.codelibs.org/) (Enterprise Search Server) using Playwright with Python. This repository provides comprehensive end-to-end testing for Fess admin interface functionality across multiple versions and search engine configurations.

## Key Features

- **Multi-Version Testing**: Supports Fess 15.x and snapshot builds across different OS distributions (Debian, AL2023, Noble)
- **Multi-Engine Support**: Tests against OpenSearch 2.x and 3.x configurations
- **Comprehensive Admin UI Coverage**: Tests all major admin functionality including search configurations, dictionaries, user management, and content management
- **Docker-Based**: Fully containerized test environment with dynamic compose file selection
- **Japanese UI Support**: Native testing of Japanese Fess interface elements

## Tech Stack

- **Testing Framework**: [Playwright](https://playwright.dev/) 1.17.1 with Python
- **Containerization**: Docker & Docker Compose
- **Search Engines**: OpenSearch 2.19.1, OpenSearch 3.3.0
- **Fess Versions**: 15.2.0 (stable), snapshot builds
- **Base Images**: Microsoft Playwright (Ubuntu Jammy), CodeLibs Fess & OpenSearch

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

| Variable | Default | Description |
|----------|---------|-------------|
| `FESS_URL` | `http://localhost:8080` | Fess instance URL |
| `FESS_USERNAME` | `admin` | Admin username |
| `FESS_PASSWORD` | `admin` | Admin password |
| `BROWSER_LOCALE` | `ja-JP` | Browser locale for Playwright |
| `HEADLESS` | `false` (CI: `true`) | Run browser in headless mode |
| `TEST_LABEL` | (auto-generated) | Override test label generation |
| `FESS_DICTIONARY_PATH` | (engine-specific) | Dictionary path for Fess |

### Custom Configuration

Create a `.env.local` file to override defaults:
```bash
FESS_URL=http://my-fess-instance:8080
FESS_USERNAME=testuser
FESS_PASSWORD=testpass
HEADLESS=true
```

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
├── src/                          # Test source code
│   ├── main.py                   # Test execution entry point
│   ├── run.sh                    # Container startup script
│   └── fess/
│       └── test/
│           ├── __init__.py       # Test utilities and assertions
│           └── ui/
│               ├── context.py    # FessContext class for browser management
│               └── admin/        # Admin UI test modules
│                   ├── badword/  # Bad word management tests
│                   ├── user/     # User management tests
│                   ├── dict/     # Dictionary management tests
│                   └── ...       # Other admin feature tests
├── compose.yaml                  # Base test container configuration
├── compose-fess15.yaml          # Fess 15 configuration
├── compose-fessx.yaml           # Fess snapshot configuration
├── compose-opensearch2.yaml     # OpenSearch 2 configuration
├── compose-opensearch3.yaml     # OpenSearch 3 configuration
├── run_test.sh                  # Test execution script
├── Dockerfile                   # Test container image
└── requirements.txt             # Python dependencies
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
