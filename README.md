# SasaBot - WhatsApp Salon Booking Assistant 💅

A production-ready WhatsApp chatbot for Glow Haven Beauty Lounge, enabling customers to ask questions, book appointments, and pay deposits seamlessly through conversational AI.

## Features ✅

- ✅ **General Q&A** - Natural language queries about services, hours, location, and promotions using Claude AI
- ✅ **Appointment Booking** - Multi-step booking flow with service selection, date/time picker
- ✅ **M-Pesa Payments** - Integrated Daraja STK Push for deposit payments
- ✅ **PDF Receipts** - Auto-generated professional receipts sent via WhatsApp
- ✅ **Context Management** - Maintains conversation state across multiple interactions

## Tech Stack 🛠️

| Component           | Technology            | Rationale                                    |
|---------------------|-----------------------|----------------------------------------------|
| **Framework**       | FastAPI               | Modern async Python framework, OpenAPI docs  |
| **LLM**             | Anthropic Claude      | Superior reasoning and instruction following |
| **Database**        | PostgreSQL + SQLModel | Type-safe ORM, production-ready              |
| **Payment**         | Safaricom Daraja API  | M-Pesa integration for Kenyan market         |
| **Messaging**       | WhatsApp Cloud API    | Direct Meta integration, rich media support  |
| **PDF**             | ReportLab             | Industry standard PDF generation             |
| **Package Manager** | uv                    | Fast, modern Python package management       |

## Quick Start 🚀

### Prerequisites

- Python 3.13+
- PostgreSQL 17+
- uv package manager
- WhatsApp Business API credentials
- Daraja sandbox credentials
- Anthropic API key

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/sasabot.git
cd sasabot

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn src.api.main:app --reload
```

### Environment Configuration

See `.env.example` for all required variables. Key configurations:

```bash
DATABASE_URL=postgresql://user:pass@localhost/sasabot
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
ANTHROPIC_API_KEY=your_claude_api_key
DARAJA_CONSUMER_KEY=your_daraja_key
DARAJA_CALLBACK_URL=https://your-domain.com/api/v1/payments/daraja/callback
BASE_URL=https://your-domain.com
```
