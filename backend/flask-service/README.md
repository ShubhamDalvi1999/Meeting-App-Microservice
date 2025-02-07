# Flask Service

## Overview
The Flask service is a core component of the meeting management system, responsible for handling meeting creation, management, and user profile operations. It integrates with the Auth service for authentication and authorization.

## Features
- Meeting management (create, read, update, delete)
- User profile management
- Integration with Auth service
- Rate limiting and caching
- Prometheus metrics
- Standardized error handling

## Tech Stack
- Python 3.11+
- Flask 2.x
- SQLAlchemy (ORM)
- PostgreSQL
- Redis
- Prometheus

## Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL
- Redis
- Docker (optional)

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Update `.env` with your configuration:
```env
FLASK_ENV=development
FLASK_APP=app.py
DATABASE_URL=postgresql://user:password@localhost:5432/db_name
REDIS_URL=redis://localhost:6379/0
AUTH_SERVICE_URL=http://localhost:3000
AUTH_SERVICE_KEY=your-service-key
```

### Running the Service

#### Development
```bash
flask run
```

#### Production
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Docker
```bash
docker build -t flask-service .
docker run -p 5000:5000 flask-service
```

## Documentation
- [API Documentation](docs/api.md)
- [Integration Guide](docs/integration.md)

## Development

### Code Structure
```
flask-service/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   └── services/
├── docs/
│   ├── api.md
│   └── integration.md
├── tests/
├── .env.example
├── app.py
├── config.py
└── requirements.txt
```

### Running Tests
```bash
pytest
```

### Code Style
The project follows PEP 8 guidelines. Run linting:
```bash
flake8
```

## Monitoring
- Prometheus metrics available at `/metrics`
- Health check endpoint at `/health`

## Contributing
1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License
MIT 