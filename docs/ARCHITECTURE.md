## Design Philosophy

This implementation aims for clean architecture principles with clear separation of concerns:

**Layers:**
1. **API Layer** (`src/api/`) - HTTP endpoints, request/response handling
2. **Service Layer** (`src/services/`) - Business logic, orchestration
3. **Data Layer** (`src/data/`) - Persistence, repositories, DTOs
4. **Utilities** (`src/utilities/`) - Shared helpers, pure functions

## State Machine Pattern

### Why State Machine?

Traditional chatbots often use intent classification, which becomes complex with multi-turn conversations. A state machine provides:

- **Predictable Behavior** - Each state has defined entry/exit conditions
- **Context Preservation** - State + context = complete conversation state
- **Easy Testing** - Mock states, test transitions independently
- **Scalability** - Add new states without touching existing ones

### State Transition Logic

```python
# State machine decides which handler to use
handler = state_machine.get_handler(session.state)

# Handler processes message
response = await handler.handle(session, message_content)

# Response may include state transition
if "transition_to" in response:
    state_machine.transition_to(session_id, new_state)
    
# After transition, immediately execute new state's handler
new_handler = state_machine.get_handler(new_state)
new_response = await new_handler.handle(session, message_content)
````

### Handler Pattern

Each handler follows this contract:

```python
async def handle(
    session: ConversationSession,
    message_content: str,
    customer_name: str | None = None,
) -> dict:
    # Returns response dict with optional keys:
    # - "text": text message
    # - "list": list message structure
    # - "buttons": button message structure
    # - "document": document message
    # - "update_context": dict to merge into session context
    # - "transition_to": next conversation state
```

## Payment Flow Architecture

### STK Push Flow

```
User Confirms Booking
    ↓
PAYMENT_INITIATED Handler
    ↓
Validate Phone (Safaricom?)
    ↓ YES
DarajaClient.initiate_stk_push()
    ↓
Daraja API → Customer's Phone
    ↓
Customer Enters PIN
    ↓
Daraja → Our Callback Endpoint
    ↓
CallbackService.process_callback()
    ↓
Update Booking Status
    ↓
Generate PDF Receipt
    ↓
Send via WhatsApp
    ↓
IDLE State
```

## Data Model Design

### Context Storage Strategy

Session context stores ephemeral booking data:

```python
context = {
    # Service Selection
    "selected_category": "Hair Care",
    "selected_service_id": "hair_care_silk_press",
    "selected_service": {...},
    
    # DateTime Selection
    "selected_date": "2025-11-01",
    "selected_time": "14:00",
    "selected_datetime_display": "Friday, November 1 at 2:00 PM",
    
    # Payment
    "booking_id": 123,
    "booking_reference": "GLW-20251030-A3F9",
    "mpesa_phone_number": "+254722123456",  # If different from customer
    "mpesa_validation_attempts": 1,
}
```

Context is cleared on:

- Booking completion
- Booking cancellation
- Return to IDLE

### Booking Lifecycle

```
PENDING (payment_status) + PENDING (booking_status)
    ↓ Payment successful
PAID (payment_status) + CONFIRMED (booking_status)
    ↓ Service delivered
PAID + COMPLETED
```

Alternative paths:

- Payment failed → FAILED + PENDING
- User cancels → * + CANCELLED

## LLM Integration Strategy

### Prompt Engineering

**System Prompt** includes:

- Business information (services, hours, location)
- Current promotions
- Instructions to stay in character
- Guidance on when to suggest booking

**Few-shot Examples:**

- Service inquiries
- Price questions
- Location requests
- Booking triggers

### Intent Recognition

Current: LLM-based keyword matching Future: Dedicated intent classifier for speed/cost

```python
# Current approach
if "book" in message.lower() or "appointment" in message.lower():
    transition_to(BOOKING_SELECT_SERVICE)
```

