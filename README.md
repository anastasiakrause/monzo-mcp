# Monzo MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> Give Claude AI read-only access to your Monzo bank account through the Model Context Protocol.

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/en/thumb/9/95/Monzo_logo.svg/1200px-Monzo_logo.svg.png" alt="Monzo Logo" width="200"/>
</p>

---

## Overview

This MCP server enables Claude to securely interact with your Monzo bank account, providing insights into your spending habits, account balances, and transaction history—all through natural conversation.

### Key Features

| Feature | Description |
|---------|-------------|
| **Account Overview** | View all Monzo accounts (current, joint, Flex) |
| **Balance Tracking** | Real-time balance and daily spending |
| **Transaction History** | Browse up to 90 days of transactions |
| **Smart Analysis** | Detect subscriptions and frequent merchants |
| **Savings Pots** | Monitor your savings goals |
| **Push Notifications** | Send custom alerts to your Monzo app |

### Security First

- **Read-only access** — Cannot move money or modify account settings
- **OAuth 2.0** — Industry-standard authentication
- **Local tokens** — Credentials never leave your machine
- **Open source** — Full transparency, audit the code yourself

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude AI                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol (stdio)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Monzo MCP Server                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      FastMCP                               │  │
│  │  ┌─────────┐ ┌──────────────┐ ┌──────────┐ ┌───────────┐  │  │
│  │  │Accounts │ │ Transactions │ │ Analysis │ │   Pots    │  │  │
│  │  │  Tools  │ │    Tools     │ │  Tools   │ │  Tools    │  │  │
│  │  └────┬────┘ └──────┬───────┘ └────┬─────┘ └─────┬─────┘  │  │
│  └───────┼─────────────┼──────────────┼─────────────┼────────┘  │
│          └─────────────┴──────────────┴─────────────┘           │
│                              │                                   │
│                     ┌────────▼────────┐                         │
│                     │  Monzo Client   │                         │
│                     │  (async httpx)  │                         │
│                     └────────┬────────┘                         │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               │ HTTPS + Bearer Token
                               ▼
                    ┌─────────────────────┐
                    │    Monzo API        │
                    │  api.monzo.com      │
                    └─────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- A Monzo account
- Claude Code CLI

### 1. Create a Monzo Developer App

1. Visit [developers.monzo.com](https://developers.monzo.com)
2. Sign in and click **"New OAuth Client"**
3. Configure your app:

   | Field | Value |
   |-------|-------|
   | Name | `Claude MCP` (or anything you like) |
   | Redirect URL | `http://localhost:8080/callback` |
   | Confidentiality | `Confidential` |

4. Save your **Client ID** and **Client Secret**

### 2. Install the Server

```bash
# Clone the repository
git clone https://github.com/yourusername/monzo-mcp.git
cd monzo-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### 3. Configure Credentials

```bash
# Copy example configuration
cp .env.example .env

# Add your credentials to .env
MONZO_CLIENT_ID=oauth2client_xxxxx
MONZO_CLIENT_SECRET=mnzconf.xxxxx
```

### 4. Authenticate with Monzo

```bash
python scripts/auth.py
```

This opens your browser for Monzo login. After approving:

> **Important**: Open your Monzo app within 5 minutes to approve the login request, otherwise you'll be limited to 90 days of transaction history.

### 5. Connect to Claude Code

Add to your Claude Code configuration (`~/.claude.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "monzo": {
      "command": "/path/to/monzo-mcp/venv/bin/python",
      "args": ["-m", "monzo_mcp.server"],
      "cwd": "/path/to/monzo-mcp"
    }
  }
}
```

---

## Available Tools

### Account Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `get_accounts` | — | List all Monzo accounts with IDs |
| `get_balance` | `account_id` | Current balance, total balance, today's spending |

### Transaction Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_transactions` | `account_id`, `limit?` | Recent transactions (default: 20, max: 100) |
| `get_transaction` | `transaction_id` | Detailed info including merchant address |

### Analysis Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_subscriptions` | `account_id` | Detect recurring payments (Netflix, Spotify, etc.) |
| `list_frequent_merchants` | `account_id`, `min_transactions?` | Find merchants you visit often |

### Savings Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_pots` | `account_id` | All savings pots with balances and goals |

### Notification Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `create_feed_item` | `account_id`, `title`, `body` | Push notification to Monzo app |

---

## Example Conversations

**You:** "What's my current balance?"

**Claude:** *Uses `get_accounts` then `get_balance`*
> Your current account balance is £1,234.56. You've spent £45.20 today.

---

**You:** "Show me my subscriptions"

**Claude:** *Uses `list_subscriptions`*
> I found 4 recurring payments:
> - Netflix: £15.99/month
> - Spotify: £10.99/month
> - iCloud: £2.99/month
>
> Estimated monthly total: £29.97

---

**You:** "Where do I spend the most money?"

**Claude:** *Uses `list_frequent_merchants`*
> Your top merchants this month:
> 1. Tesco (12 transactions) - £156.78
> 2. TfL (8 transactions) - £42.50
> 3. Pret A Manger (6 transactions) - £31.20

---

## Project Structure

```
monzo-mcp/
├── src/monzo_mcp/
│   ├── __init__.py          # Package metadata
│   ├── server.py            # MCP server entry point
│   ├── monzo_client.py      # Async Monzo API client
│   ├── models.py            # Data classes & exceptions
│   ├── constants.py         # Configuration constants
│   ├── utils.py             # Shared utilities
│   ├── analysis.py          # Subscription detection logic
│   └── tools/
│       ├── __init__.py      # Tool registration
│       ├── accounts.py      # Account tools
│       ├── transactions.py  # Transaction tools
│       ├── analysis.py      # Analysis tools
│       ├── pots.py          # Pot tools
│       └── feed.py          # Feed/notification tools
├── scripts/
│   └── auth.py              # OAuth authentication flow
├── pyproject.toml           # Package configuration
├── .env.example             # Environment template
└── README.md
```

---

## Limitations

| Limitation | Reason |
|------------|--------|
| **90-day history** | Monzo's Strong Customer Authentication (SCA) requirement |
| **Personal use only** | Monzo API terms prohibit public applications |
| **Rate limits** | API calls are throttled; avoid rapid requests |
| **No money movement** | Intentional design choice for security |

---

## Troubleshooting

### "Access token expired"
```bash
python scripts/auth.py
```
Re-authenticate and approve in the Monzo app.

### "Rate limited"
Wait 5-10 minutes before making more requests.

### "No transactions found"
Ensure you approved the login in your Monzo app within 5 minutes of authenticating.

### Server won't start
Check that your virtual environment is activated and credentials are in `.env`.

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/

# Run type checking
mypy src/

# Run tests
pytest
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Monzo](https://monzo.com) for their excellent API
- [Anthropic](https://anthropic.com) for Claude and the MCP protocol
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server framework

---

<p align="center">
  Made with ❤️ for the Claude + Monzo community
</p>
