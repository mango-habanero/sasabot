# SasaBot - WhatsApp Salon Booking Assistant 💅
A production-ready WhatsApp chatbot for Glow Haven Beauty Lounge, enabling customers to ask questions, book appointments, and pay deposits seamlessly through conversational AI.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Deployed on Railway](https://img.shields.io/badge/deployed-Railway-blueviolet.svg)](https://railway.app/)

## 🚀 Live Demo

**🔗 Repository:** https://github.com/mango-habanero/sasabot

**📱 WhatsApp Test Number:** [Contact for access]

**🌐 API Base URL:** https://sasabot-production.up.railway.app

**📚 API Documentation:** https://sasabot-production.up.railway.app/docs

**❤️ Health Check:** https://sasabot-production.up.railway.app/api/v1/health

### Try It Out

1. Send a WhatsApp message to the test number: **"Hi"**
2. Ask questions: *"What are your opening hours?"* or *"How much is a silk press?"*
3. Start booking: **"I want to book an appointment"**
4. Complete the full flow and receive your PDF receipt via WhatsApp!
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
git clone https://github.com/mangohabanero/sasabot.git
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

## 🎯 Deliverables Status

All 5 required features have been successfully implemented:

| # | Feature             | Status     | Notes                                             |
|---|---------------------|------------|---------------------------------------------------|
| 1 | General Questions   | ✅ Complete | Powered by Claude AI with business context        |
| 2 | Appointment Booking | ✅ Complete | Multi-step flow with service, date/time selection |
| 3 | Deposit Payments    | ✅ Complete | M-Pesa STK Push via Daraja API (sandbox)          |
| 4 | PDF Receipts        | ✅ Complete | Auto-generated professional receipts              |
| 5 | Feedback System     | ⏭️ Future  | Scope prioritized booking & payment flow          |

**Implementation Highlights:**
- 🏗️ State machine architecture for predictable conversation flow
- 🔄 Full context management across multi-turn conversations
- 💳 Safaricom phone validation with fallback M-Pesa number collection
- 📄 Professional PDF receipts with booking details
- 🔒 Type-safe API with comprehensive error handling
- 📊 Structured logging for production observability
- 🐳 Docker containerization for consistent deployments
