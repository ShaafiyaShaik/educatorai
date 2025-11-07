# Educator AI Administrative Assistant

An AI-powered administrative assistant designed to reduce the burden of non-teaching tasks for educators. This system uses LangChain for intelligent automation and FastAPI for integration with university administrative systems.

## Features

### 🤖 AI-Powered Automation
- **Automated Communications**: AI agents handle routine emails, notifications, and announcements
- **Smart Scheduling**: Intelligent calendar management and meeting coordination
- **Administrative Task Automation**: Streamline repetitive administrative workflows

### 📊 Administrative Management
- **Record Keeping**: Automated data entry and organization for educational records
- **Compliance Reporting**: Generate and submit compliance reports automatically
- **Schedule Management**: Comprehensive calendar and event management system

### 🔐 Security & Integration
- **Secure Authentication**: JWT-based authentication with role-based access control
- **University System Integration**: APIs for seamless integration with existing university systems
- **Data Privacy**: Secure handling of sensitive educational data

## Technology Stack

- **Backend**: FastAPI (Python)
- **AI Framework**: LangChain with OpenAI integration
- **Database**: SQLAlchemy with SQLite/PostgreSQL support
- **Authentication**: JWT with bcrypt password hashing
- **Email**: SMTP integration for automated communications
- **Containerization**: Docker and Docker Compose

## Quick Start

### Prerequisites
- Python 3.11+
- Git
- OpenAI API key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd educator-ai-assistant
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your configuration:
   - Set `OPENAI_API_KEY` for AI features
   - Configure email settings for automated communications
   - Update database URL if using PostgreSQL

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Using Docker

1. **Build and run with Docker Compose**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   docker-compose up --build
   ```

## API Documentation

Once the application is running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Core API Endpoints

### Authentication
- `POST /api/v1/educators/register` - Register new educator
- `POST /api/v1/educators/login` - Login and get access token
- `GET /api/v1/educators/me` - Get current user profile

### Scheduling
- `GET /api/v1/scheduling/` - List schedule events
- `POST /api/v1/scheduling/` - Create new event
- `PUT /api/v1/scheduling/{id}` - Update event
- `GET /api/v1/scheduling/today/events` - Get today's events

### Communications
- `POST /api/v1/communications/send-email` - Send automated email
- `POST /api/v1/communications/bulk-notification` - Send bulk notifications
- `POST /api/v1/communications/generate-template` - Generate email templates

### Compliance
- `GET /api/v1/compliance/` - List compliance reports
- `POST /api/v1/compliance/generate` - Generate compliance reports

## AI Agents

### Communication Agent
Handles automated email communications and notifications:
- Professional email composition
- Bulk notification management
- Template generation
- Schedule-based reminders

### Administrative Agent
Manages routine administrative tasks:
- Record keeping automation
- Compliance report generation
- Task workflow optimization
- Data management

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |
| `SECRET_KEY` | JWT secret key | Yes |
| `EMAIL_USERNAME` | SMTP email username | No |
| `EMAIL_PASSWORD` | SMTP email password | No |

### Database

The application supports multiple database backends:
- **SQLite** (default): File-based database for development
- **PostgreSQL**: Recommended for production
- **MySQL**: Alternative production database

## Development

### Project Structure
```
educator-ai-assistant/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/                # Core configuration and utilities
│   ├── api/                 # API endpoints
│   ├── agents/              # LangChain AI agents
│   ├── models/              # Database models
│   └── services/            # Business logic services
├── frontend/                # Frontend application (future)
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker configuration
└── README.md               # This file
```

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Production Deployment

1. **Update environment configuration**
   - Set `DEBUG=false`
   - Use strong `SECRET_KEY`
   - Configure production database
   - Set up email credentials

2. **Deploy with Docker**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Security Considerations

- Change default secret keys
- Use HTTPS in production
- Configure CORS properly
- Implement rate limiting
- Regular security updates

## Integration

### University Systems
The application provides APIs for integration with:
- Student Information Systems (SIS)
- Learning Management Systems (LMS)
- HR Management Systems
- Calendar Systems

### Email Integration
Supports automated email sending through:
- SMTP servers
- Third-party email services
- Bulk email platforms

## Support

### Common Issues

1. **AI features not working**
   - Ensure `OPENAI_API_KEY` is set correctly
   - Check OpenAI API quota and billing

2. **Email sending fails**
   - Verify SMTP credentials
   - Check firewall settings
   - Use app passwords for Gmail

3. **Database connection issues**
   - Verify DATABASE_URL format
   - Ensure database server is running
   - Check connection permissions

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Advanced scheduling algorithms
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with popular LMS platforms
- [ ] Voice assistant integration