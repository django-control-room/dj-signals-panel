# Development

Contributing to Dj Signals Panel or setting up for local development.

## Prerequisites

- Python 3.9+
- Git
- Docker (recommended)

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/yassi/dj-signals-panel.git
cd dj-signals-panel
```

### 2. Choose Development Environment

#### Option A: Docker (Recommended)

```bash
make docker_up       # Start all services
make docker_shell    # Open shell in container
```

#### Option B: Local Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install package and dependencies
make install
# or
pip install -e .
pip install -r requirements.txt
```

### 3. Set Up Example Project

```bash
cd example_project
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/admin/`

## Testing

### Run All Tests

```bash
# Docker
make test_docker

# Local
make test_local
```

### Run Specific Tests

```bash
pytest tests/test_admin.py -v
pytest tests/test_search_views.py -v
pytest tests/test_detail_view.py -v
```

### With Coverage

```bash
pytest --cov=dj_signals_panel tests/
```

## Project Structure

```
dj-signals-panel/
├── dj_signals_panel/          # Main package
│   ├── admin.py              # Admin integration (registers the panel)
│   ├── apps.py               # AppConfig
│   ├── conf.py               # Settings and defaults
│   ├── data.py               # Data-fetching logic
│   ├── interfaces.py         # Typed data structures
│   ├── models.py             # Placeholder model (no migrations)
│   ├── panel.py              # Admin panel class
│   ├── urls.py               # URL patterns
│   ├── utils.py              # Utility helpers
│   ├── views.py              # Django views
│   ├── static/               # CSS and vendor assets
│   ├── templates/            # HTML templates
│   └── templatetags/         # Custom template tags
├── tests/                    # Test suite
│   ├── base.py               # Test base class
│   ├── conftest.py           # Pytest configuration
│   ├── test_admin.py         # Admin integration tests
│   ├── test_search_views.py  # Signal list/search view tests
│   └── test_detail_view.py   # Signal detail view tests
├── example_project/          # Example Django project
├── docs/                     # Documentation
└── Makefile                  # Development commands
```

## Code Style

- Follow PEP 8
- Use type hints where helpful
- Write docstrings for public methods
- Keep functions focused and small

## Makefile Commands

```bash
make install        # Install dependencies
make test_local     # Run tests locally
make test_docker    # Run tests in Docker
make docker_up      # Start Docker services
make docker_down    # Stop Docker services
make docker_shell   # Open shell in container
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run test suite
6. Submit pull request
