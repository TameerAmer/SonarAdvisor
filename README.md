# SonarQube AI Advisor

A FastAPI microservice that integrates with SonarQube and provides AI-powered code analysis insights.

## Features

- **SonarQube Integration**: Fetches issues, bugs, vulnerabilities, and code smells from SonarQube projects
- **AI-Powered Analysis**: Analyzes SonarQube data to provide:
  - Top recurring problems identification
  - Prioritized critical issues list
  - Actionable improvement suggestions
  - Comprehensive analysis summaries
- **User Authentication**: JWT-based authentication with user registration/login
- **SQLite Database**: Stores users, analysis requests, and AI reports using SQLAlchemy
- **RESTful API**: Well-documented FastAPI endpoints with automatic OpenAPI documentation
- **Background Processing**: Asynchronous analysis processing for better user experience

## Project Structure

```
sonar_advisor/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
├── sonar_advisor/
│   ├── __init__.py
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Application configuration
│   │   ├── database.py        # SQLAlchemy database setup
│   │   └── auth.py            # JWT authentication utilities
│   ├── models/                # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   ├── analysis_request.py # Analysis request model
│   │   └── ai_report.py       # AI report model
│   ├── schemas/               # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py            # User schemas
│   │   └── analysis.py        # Analysis schemas
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── sonarqube.py       # SonarQube API integration
│   │   └── ai_analysis.py     # AI analysis engine
│   └── routers/               # FastAPI route handlers
│       ├── __init__.py
│       ├── auth.py            # Authentication endpoints
│       └── analysis.py        # Analysis endpoints
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- SonarQube server running (local or remote)
- SonarQube authentication token or username/password

### 2. Installation

```bash
# Clone or download the project
cd sonar_advisor

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy the environment template and configure your settings:

```bash
copy .env.example .env
```

Edit `.env` file with your settings:

```env
# SonarQube settings
SONARQUBE_URL=http://localhost:9000
SONARQUBE_TOKEN=your_sonarqube_token_here

# JWT settings
SECRET_KEY=your-super-secret-key-change-this-in-production

# Optional: AI model configuration
AI_MODEL_TYPE=rule_based
```

### 4. Run the Application

```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Usage

### Authentication

1. **Register a new user**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

2. **Login to get access token**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpassword123"
```

### Analysis Workflow

1. **List available SonarQube projects**:
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/sonarqube/projects" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Start project analysis**:
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_key": "your-project-key"}'
```

3. **Check analysis status**:
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/status/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. **Get analysis results**:
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/requests/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Schema

The application uses SQLite with SQLAlchemy ORM and includes three main tables:

- **users**: Store user accounts with JWT authentication
- **analysis_requests**: Track analysis requests with project keys and status
- **ai_reports**: Store AI-generated analysis results linked to requests

Database tables are automatically created when the application starts.

## AI Analysis Features

The AI analysis engine currently implements rule-based analysis and provides:

### Top Recurring Problems
- Identifies the most frequent rule violations
- Groups issues by SonarQube rule keys
- Provides occurrence counts and severity levels

### Suggested Improvements
- Security improvements for vulnerabilities
- Reliability improvements for bugs
- Maintainability improvements for code smells
- Priority-based recommendations

### Prioritized Issues
- Weighted scoring based on severity and issue type
- Detailed reasoning for prioritization
- Focus on critical and high-impact issues

### Analysis Summary
- Overall project health assessment
- Key metrics and statistics
- Actionable recommendations

## Configuration Options

### SonarQube Connection
- **Token-based**: Recommended for production
- **Username/Password**: Alternative authentication method

### AI Model Types
- **rule_based**: Built-in analysis engine (default)
- **openai**: Integration ready for OpenAI GPT models
- **local_llm**: Extensible for local LLM integration

### Security Settings
- JWT secret key configuration
- Token expiration settings
- CORS configuration for web frontends

## Development

### Adding New Features

1. **Database Changes**: Modify models in `sonar_advisor/models/`
2. **API Endpoints**: Add routes in `sonar_advisor/routers/`
3. **Business Logic**: Implement services in `sonar_advisor/services/`
4. **Request/Response**: Define schemas in `sonar_advisor/schemas/`

### Testing

The application includes basic health checks and error handling. For comprehensive testing:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (when test files are added)
pytest
```

## Production Deployment

### Environment Variables
- Set strong `SECRET_KEY`
- Configure proper `SONARQUBE_URL` and authentication
- Set `DEBUG=false`

### Database
- Consider PostgreSQL for production instead of SQLite
- Update `DATABASE_URL` in configuration

### Security
- Configure CORS properly for your frontend domains
- Use HTTPS in production
- Implement proper logging and monitoring

## Troubleshooting

### Common Issues

1. **SonarQube Connection Failed**
   - Verify SonarQube URL is accessible
   - Check authentication token/credentials
   - Ensure SonarQube server is running

2. **Database Errors**
   - Check write permissions for SQLite file
   - Verify database connection string

3. **Authentication Issues**
   - Ensure SECRET_KEY is set
   - Check token expiration settings
   - Verify user credentials

### Health Check
Visit `http://localhost:8000/health` to verify:
- Application status
- Database connectivity
- SonarQube configuration

## License

This project is provided as-is for educational and development purposes.