# 💱 Freek Exchange Bot - Discord Crypto & UPI Exchange System

A comprehensive, full-featured Discord bot designed to manage peer-to-peer Indian Rupee (UPI) and Cryptocurrency exchanges (I2C / C2I) with automated QR code billing and audit logs.

## ✨ Key Features
- **Dual Conversion Engine**:
  - **I2C (INR to Crypto)**: Calculates cryptocurrency equivalent at dynamic exchange rates.
  - **C2I (Crypto to INR)**: Calculates Indian Rupee payout with fee deduction.
- **Dynamic QR Code Generation**: Automatically generates customized UPI payment QR codes directly inside Discord tickets via `qrcode`.
- **Automated Ticket Transcripts**: Saves full chat transcripts via `chat_exporter` upon ticket closure.
- **Cashback & Loyalty System**: Logs customer cashback rewards and points in `cashback.json` and dedicated log channels.
- **Exchanger Inventory Tracking**: Real-time balance and liquidity tracking for approved exchangers via `exchangers.json`.

## 🛠️ Installation & Setup
1. Clone repository:
   ```bash
   git clone https://github.com/loveslaw/Freek-exchange-bot.git
   cd Freek-exchange-bot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configuration:
   - Configure bot settings in `config.json`.
   - Set up UPI ID in `upi.json`.
   - Provide your Discord Bot Token.
4. Launch the bot:
   ```bash
   python main.py
   ```

## 📌 Commands
- `.exchange` - Start a new exchange request
- `.upi` - Display current active UPI payment handle
- `.cashback` - Check accrued user cashback
- `.stats` - View exchange volume statistics
