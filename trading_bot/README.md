# PrimeTrade Bot 🤖

A clean, production-structured **Python trading bot** for the **Binance Futures Testnet (USDT-M)**.
Place Market, Limit, and Stop orders via a simple CLI — with full logging, input validation, and error handling.

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance Futures REST API client (signing, HTTP)
│   ├── orders.py            # Order placement logic + CLI output formatting
│   ├── validators.py        # Input validation for all order parameters
│   └── logging_config.py   # Structured logging (file + console handlers)
├── logs/
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── cli.py                   # CLI entry point (argparse subcommands)
├── requirements.txt
├── .env.example             # Credentials template
├── .env                     # Your real credentials (DO NOT commit)
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Steps

### 1. Register on Binance Futures Testnet

1. Go to: **https://testnet.binancefuture.com**
2. Sign up / log in.
3. Navigate to **API Key Management**.
4. Click **Generate** to create your API Key and Secret.
5. **Copy both values** — you will not see the secret again.

---

### 2. Clone / Open the Project in VS Code

```powershell
# Open VS Code in the project folder
cd d:\primetrade\trading_bot
code .
```

---

### 3. Create a Virtual Environment

Open the **VS Code integrated terminal** (`Ctrl + `` ` ``):

```powershell
# Create the virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# If you get a permissions error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

### 5. Configure Your API Credentials

```powershell
# Copy the template
copy .env.example .env
```

Then open `.env` in VS Code and replace the placeholder values:

```env
BINANCE_API_KEY=paste_your_api_key_here
BINANCE_API_SECRET=paste_your_api_secret_here
```

> ⚠️ **Never commit your `.env` file.** It is already excluded by `.gitignore`.

---

## 🚀 How to Run

All commands are run from the `trading_bot/` directory with your virtual environment active.

### ✅ Check Connectivity

```powershell
python cli.py ping
```

**Output:**
```
────────────────────────────────────────────────────────────
  🌐  CONNECTIVITY CHECK
────────────────────────────────────────────────────────────
  Testnet URL  : https://testnet.binancefuture.com
  Server Time  : 1746714313022 ms
  Status       : ✅ Connected
────────────────────────────────────────────────────────────
```

---

### 💰 Check Account Balance

```powershell
python cli.py account
```

---

### 📈 Place a MARKET Order

```powershell
# BUY 0.01 BTC at market price
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# SELL 0.1 ETH at market price
python cli.py place-order --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
```

---

### 📉 Place a LIMIT Order

```powershell
# SELL 0.01 BTC at $98,000 (GTC)
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 98000

# BUY 0.01 BTC at $90,000 with IOC time-in-force
python cli.py place-order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 90000 --time-in-force IOC
```

---

### 🛑 Place a STOP-LIMIT Order (Bonus)

```powershell
# Trigger a SELL when price hits $85,500, execute SELL limit at $85,000
python cli.py place-order --symbol BTCUSDT --side SELL --type STOP --quantity 0.01 --price 85000 --stop-price 85500
```

---

### 🛑 Place a STOP-MARKET Order (Bonus)

```powershell
# Trigger a market SELL when price hits $2,500
python cli.py place-order --symbol ETHUSDT --side SELL --type STOP_MARKET --quantity 0.1 --stop-price 2500
```

---

### 🔍 Query an Existing Order

```powershell
python cli.py query-order --symbol BTCUSDT --order-id 4751348291
```

---

### 🗑️ Cancel an Open Order

```powershell
python cli.py cancel-order --symbol BTCUSDT --order-id 4751348402
```

---

### 📖 View Full Help

```powershell
python cli.py --help
python cli.py place-order --help
```

---

## 📋 Full CLI Reference

| Command | Required Flags | Optional Flags |
|---|---|---|
| `ping` | — | — |
| `account` | — | — |
| `place-order` | `--symbol` `--side` `--type` `--quantity` | `--price` `--stop-price` `--time-in-force` `--reduce-only` |
| `query-order` | `--symbol` `--order-id` | — |
| `cancel-order` | `--symbol` `--order-id` | — |

### Supported Order Types

| Type | Price | Stop Price | Use Case |
|---|---|---|---|
| `MARKET` | ❌ Not needed | ❌ Not needed | Instant execution at market |
| `LIMIT` | ✅ Required | ❌ Not needed | Execute at specific price or better |
| `STOP_MARKET` | ❌ Not needed | ✅ Required | Market order triggered at stop price |
| `STOP` | ✅ Required | ✅ Required | Limit order triggered at stop price |

---

## 📂 Log Files

Logs are automatically written to `logs/trading_bot_YYYYMMDD.log`.

Each log entry follows this format:
```
2026-05-08 18:30:01 | INFO     | trading_bot.client | Order placed successfully. orderId=4751348291 status=FILLED
```

- **DEBUG** entries contain full request payloads and raw API responses.
- **INFO** entries capture key lifecycle events (order placed, cancelled, etc.).
- **WARNING** entries flag non-critical issues (e.g. price ignored for MARKET).
- **ERROR** entries capture API errors, network failures, and validation errors.

Sample log files are provided in the `logs/` directory:
- `logs/market_order_sample.log` — MARKET BUY order
- `logs/limit_order_sample.log` — LIMIT SELL order

---

## 🔧 Architecture

```
cli.py (argparse CLI)
  │
  ├── validates input → bot/validators.py
  ├── creates client  → bot/client.py   (HMAC signing + HTTP)
  └── places order    → bot/orders.py   (orchestration + display)
                            │
                            └── bot/logging_config.py (all layers log here)
```

### Design Decisions

| Decision | Rationale |
|---|---|
| Pure `requests` (no SDK) | Shows understanding of the raw API; no hidden behaviour |
| `python-dotenv` | Keeps credentials out of code; standard industry practice |
| Layered architecture | `client` → `orders` → `cli` — each layer has one responsibility |
| `logging` to file | Full DEBUG trace in file; only warnings on console (no noise) |
| Fail-fast validation | All inputs validated before any network call is made |

---

## 🧪 Assumptions

1. You are using the **USDT-M** Binance Futures Testnet (not COIN-M).
2. The testnet base URL `https://testnet.binancefuture.com` is used for all API calls.
3. Quantities and prices use the standard decimal format accepted by Binance (e.g. `0.01` for BTC).
4. Hedge-mode (`positionSide`) is **not** used; orders default to `BOTH` side (one-way mode).
5. No retry logic is implemented — the app is fail-fast and surfaces errors immediately.

---

## 📦 Requirements

```
requests>=2.31.0
python-dotenv>=1.0.0
```

Python **3.8+** is required.

---

## 🔒 Security

- API credentials are loaded exclusively from environment variables / `.env`.
- `.env` is listed in `.gitignore` and will never be committed.
- Signatures use **HMAC-SHA256** per Binance specification.

---

## 📬 Contact

Built for the PrimeTrade Python Developer hiring assessment.
