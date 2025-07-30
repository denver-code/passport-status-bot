# MFA Passport Dashboard Bot

<p align="center">
   <a href="https://t.me/passport_mfa_gov_ua_check_bot"><img src="https://telegram.org/img/t_logo.png?1"></a> <br>
   🤖 Advanced Telegram bot for tracking MFA passport application status<br>
   <strong>Production-ready with enterprise-grade architecture</strong>
</p>

<p align="center">
   <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python Version">
   <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
   <img src="https://img.shields.io/badge/Code%20Style-Black-black.svg" alt="Code Style">
   <img src="https://img.shields.io/badge/Type%20Checker-MyPy-blue.svg" alt="Type Checker">
</p>

## 📋 Overview

This Telegram bot provides automated tracking and notifications for MFA passport application status from
_passport.mfa.gov.ua_. Built with modern Python best practices, it offers enterprise-grade reliability, performance
monitoring, and comprehensive testing.

### ✨ Key Features

- **🔍 Status Checking**: Instant status lookup by application ID
- **👤 Personal Cabinet**: User profile management with linked applications
- **🔔 Smart Subscriptions**: Automated status change notifications (up to 5 per user)
- **📱 Push Notifications**: Real-time alerts via NTFY.sh integration
- **📊 QR Code Scanner**: Extract application IDs from QR codes
- **🛡️ Anti-Spam Protection**: Rate limiting and user behavior monitoring
- **📈 Performance Monitoring**: Health checks and system metrics
- **🔐 Security**: Input validation, secure configuration, vulnerability scanning

<details>
<summary>📸 Screenshots</summary>

| Feature            | Screenshot                                                        |
|--------------------|-------------------------------------------------------------------|
| Status Check       | <img src="assets/pic1.png" alt="Status Check" width="200"/>       |
| Personal Cabinet   | <img src="assets/pic2.png" alt="Cabinet" width="200"/>            |
| Subscriptions      | <img src="assets/pic3.png" alt="Subscriptions" width="200"/>      |
| Push Notifications | <img src="assets/pic4.png" alt="Push Notifications" width="200"/> |
| Commands           | <img src="assets/pic5.png" alt="Commands" width="200"/>           |

</details>

## 🏗️ Architecture

The bot follows modern software engineering principles:

- **Service Layer Pattern**: Separated business logic from presentation
- **Command Pattern**: Organized command handling with proper separation of concerns
- **Dependency Injection**: Loose coupling and testable components
- **Event-Driven Architecture**: Async processing with proper error handling
- **Monitoring & Observability**: Structured logging and health checks

```
bot/
├── commands/           # Command handlers by category
├── core/              # Core utilities and models
├── middlewares/       # Request processing middleware
├── services/          # Business logic layer
└── main.py           # Application entry point
```

## 🚀 Production Deployment

### Prerequisites

- **Python 3.12+**
- **MongoDB 4.4+**
- **Docker & Docker Compose** (recommended)
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

### Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/mrAlexZT/passport-status-bot
cd passport-status-bot

# Configure environment
cp sample.env .env
nano .env  # Add your bot token and admin ID

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f mfa_passport_bot
```

### Manual Production Setup

```bash
# Install dependencies
poetry install --only main

# Validate configuration
poetry run python -c "from bot.core.config import validate_configuration; validate_configuration()"

# Run database migrations (if any)
poetry run python -m bot.core.database

# Start bot
poetry run python -m bot
```

### Environment Variables

| Variable                     | Description            | Required | Default                     |
|------------------------------|------------------------|----------|-----------------------------|
| `TOKEN`                      | Telegram Bot API token | ✅        | -                           |
| `ADMIN_ID`                   | Telegram Admin User ID | ✅        | -                           |
| `DATABASE_URL`               | MongoDB connection URL | ❌        | `mongodb://localhost:27003` |
| `DATABASE_NAME`              | Database name          | ❌        | `mfa_passport_bot`          |
| `DEBUG`                      | Debug mode             | ❌        | `false`                     |
| `LOG_LEVEL`                  | Logging level          | ❌        | `INFO`                      |
| `MAX_SUBSCRIPTIONS_PER_USER` | Subscription limit     | ❌        | `5`                         |

### Production Monitoring

The bot includes comprehensive monitoring:

```bash
# Health check endpoint (if running with web server)
curl http://localhost:8080/health

# View performance metrics
poetry run python -c "
from bot.core.monitoring import health_checker
import asyncio
metrics = asyncio.run(health_checker.perform_health_check())
print(f'Status: {metrics.database_status}')
print(f'Response Time: {metrics.database_response_time:.3f}s')
"
```

## 🛠️ Development

### Quick Setup

```bash
# One-command setup
./scripts/run.sh setup
```

Or manually:

```bash
# Install all dependencies including dev tools
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Install browser for testing
poetry run playwright install chromium
```

### Development Commands

```bash
# Start development server with auto-reload
./scripts/run.sh dev

# Run all quality checks
./scripts/run.sh check

# Run specific checks
./scripts/run.sh lint      # Code formatting and linting
./scripts/run.sh typecheck # Static type checking
./scripts/run.sh security  # Security vulnerability scan
./scripts/run.sh test      # Run tests with coverage
```

### Code Quality Tools

The project uses modern Python tooling:

- **🔧 Ruff**: Fast linting and formatting
- **⚫ Black**: Code formatting
- **🏷️ MyPy**: Static type checking
- **🔒 Bandit**: Security scanning
- **🧪 Pytest**: Testing with async support
- **📊 Coverage**: Code coverage reporting
- **🪝 Pre-commit**: Automated quality checks

### Development Workflow

1. **Make changes** to the codebase
2. **Run checks** with `./scripts/run.sh check`
3. **Fix any issues** reported by the tools
4. **Commit changes** (pre-commit hooks run automatically)
5. **Push to repository**

### Project Structure

```
bot/
├── commands/              # Command handlers
│   ├── system.py         # System commands (ping, help, etc.)
│   ├── user.py           # User management commands
│   ├── subscription.py   # Subscription management
│   └── admin.py          # Admin-only commands
├── core/                 # Core functionality
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exception classes
│   ├── logger.py         # Structured logging
│   ├── monitoring.py     # Health checks and metrics
│   └── models/           # Database models
├── middlewares/          # Request processing
│   ├── antiflood.py      # Rate limiting and anti-spam
│   └── error_handler.py  # Error handling middleware
├── services/             # Business logic
│   └── user_service.py   # User management services
└── main.py              # Application entry point
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage
./scripts/run.sh test

# Run specific test file
poetry run pytest tests/test_models.py -v

# Run tests with HTML coverage report
poetry run pytest --cov=bot --cov-report=html
```

### Test Coverage

The project maintains high test coverage with:

- **Unit tests** for models and business logic
- **Integration tests** for service layer
- **Mock objects** for external dependencies
- **Async test support** for aiogram handlers
- **Database fixtures** for isolated testing

### Writing Tests

```python
import pytest
from tests.conftest import MockTelegramMessage, TestDataFactory

async def test_user_creation():
    """Example test demonstrating best practices."""
    # Arrange
    user_data = TestDataFactory.create_user_data()
    mock_message = MockTelegramMessage()

    # Act
    result = await create_user(user_data)

    # Assert
    assert result.telegram_id == user_data["telegram_id"]
```

### Continuous Integration

GitHub Actions automatically run:

- ✅ **All tests** with coverage reporting
- ✅ **Code quality checks** (linting, formatting)
- ✅ **Type checking** with MyPy
- ✅ **Security scanning** with Bandit
- ✅ **Dependency vulnerability** checks

## 📊 Features Status

| Feature                  | Status   | Description                    |
|--------------------------|----------|--------------------------------|
| ✅ Status Checking        | Complete | Check application status by ID |
| ✅ Personal Cabinet       | Complete | User profile management        |
| ✅ Subscriptions          | Complete | Automated status monitoring    |
| ✅ Push Notifications     | Complete | NTFY.sh integration            |
| ✅ QR Scanner             | Complete | Extract IDs from QR codes      |
| ✅ Anti-Spam              | Complete | Rate limiting and protection   |
| ✅ Admin Panel            | Complete | Administrative commands        |
| ✅ Performance Monitoring | Complete | Health checks and metrics      |
| ⏳ Analytics Dashboard    | Planned  | Usage analytics and insights   |
| ⏳ Inline Keyboards       | Planned  | Interactive button interfaces  |

## 🔧 Configuration

### Database Configuration

```bash
# MongoDB connection examples
DATABASE_URL="mongodb://localhost:27017"           # Local
DATABASE_URL="mongodb://user:pass@host:27017"      # Authentication
DATABASE_URL="mongodb+srv://cluster.mongodb.net"   # MongoDB Atlas
```

### Logging Configuration

```python
# Structured JSON logging for production
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log files generated:
logs/
├── bot_YYYYMMDD.log        # General logs
├── errors_YYYYMMDD.log     # Error logs only
└── structured_YYYYMMDD.log # JSON structured logs
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Run quality checks** (`./scripts/run.sh check`)
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Development Guidelines

- Follow **PEP 8** style guide (enforced by Black)
- Add **type hints** for all function parameters and returns
- Write **comprehensive tests** for new features
- Update **documentation** for user-facing changes
- Ensure **100% test coverage** for critical paths

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 👥 Authors

- **Ihor Savenko** - *Idea and Development* - [@denver-code](https://github.com/denver-code)
- **Oleksandr Shevchenko** - *Development* - [@mrAlexZT](https://github.com/mrAlexZT)

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/mrAlexZT/passport-status-bot/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/mrAlexZT/passport-status-bot/discussions)
- 📧 **Email**: Contact authors directly

## 🙏 Acknowledgments

- Thanks to the Ukrainian community for feedback and testing
- aiogram library for excellent Telegram Bot API wrapper
- MongoDB team for robust database solution

---

<p align="center">
   Made with ❤️ for the Ukrainian community<br>
   <strong>Слава Україні! 🇺🇦</strong>
</p>
