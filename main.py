import discord
from discord.ext import commands
import chat_exporter
import asyncio
import qrcode
import io
import json 
import os
from discord.ui import View, Button, Modal, TextInput, Select
import aiohttp
import random
import string
import datetime
import fcntl
import time

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

UPI_FILE = "upi.json"
CASHBACK_FILE = "cashback.json"
I2C = 94
C2I = 92
CASHBACK_LOG_CHANNEL = 1425162358011199560
CASHBACK_HISTORY_CHANNEL = 1438889301709688954
EXCHANGERS_FILE = "exchangers.json"
CONFIG_FILE = "config.json"
TICKETS_FILE = "tickets.json"

I2C = 95
C2I = 92
PKR2C = 320
C2PKR = 260
C2C_FEES = 4
PAYPAL2C = 10
C2PAYPAL = 0

# Custom Emojis
EMOJI_TICK = "<:SW_tick:1433834224972206181>"
EMOJI_WARNING = "<:SW_warning:1433832107079368875>"
EMOJI_SHARE = "<:SW_share:1433832650736668824>"
EMOJI_DOT = "<:SW_dot:1433834092729860269>"
EMOJI_SERVICES = "<:SW_services:1433835593640443954>"
EMOJI_INR = "<:Inr:1409881943255945369>"
EMOJI_PKR = "<:pkr:1444254255287500852>"
EMOJI_CRYPTO = "<:crypto:1444251229344497664>"
EMOJI_PAYPAL = "<:Paypal:1444251160163782657>"

# Header Emojis
HEADER = "<:swappy_1:1433491465438498986><:swappy_2:1433491516751482951><:swappy_3:1433491719805997177><:swappy_4:1433491770712526979><:swappy_5:1433491812856889476><:swappy_6:1433491846981488762><:swappy_7:1433491893420818482><:swappy_8:1433491927143153774><:swappy_9:1433491957187088676><:emoji_84:1433491984001138889>"

# ============= SAFE FILE HANDLING FUNCTIONS =============
def load_stats_safe(stats_file):
    """Safely load stats with file locking and retry mechanism"""
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            if not os.path.exists(stats_file):
                return {"staff": {}, "clients": {}, "daily": {}, "monthly": {}, "yearly": {}}
            
            with open(stats_file, "r") as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    content = f.read().strip()
                    if not content:
                        return {"staff": {}, "clients": {}, "daily": {}, "monthly": {}, "yearly": {}}
                    return json.loads(content)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (IOError, json.JSONDecodeError) as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            print(f"Error loading stats after {max_retries} attempts: {e}")
            return {"staff": {}, "clients": {}, "daily": {}, "monthly": {}, "yearly": {}}
    
    return {"staff": {}, "clients": {}, "daily": {}, "monthly": {}, "yearly": {}}

def save_stats_safe(stats_file, stats):
    """Safely save stats with file locking and atomic write"""
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            temp_file = stats_file + f".tmp.{os.getpid()}"
            
            # Write to temp file first
            with open(temp_file, "w") as f:
                json.dump(stats, f, indent=4)
            
            # Now acquire exclusive lock and replace
            with open(stats_file, "a") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    os.replace(temp_file, stats_file)
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            print(f"Error saving stats after {max_retries} attempts: {e}")
            # Fallback: direct write without locking
            try:
                with open(stats_file, "w") as f:
                    json.dump(stats, f, indent=4)
                return True
            except:
                return False
    
    return False

def load_mm_stats_safe(mm_stats_file):
    """Safely load MM stats with file locking"""
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            if not os.path.exists(mm_stats_file):
                return {"mm_staff": {}, "mm_clients": {}}
            
            with open(mm_stats_file, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    content = f.read().strip()
                    if not content:
                        return {"mm_staff": {}, "mm_clients": {}}
                    return json.loads(content)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (IOError, json.JSONDecodeError) as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            print(f"Error loading MM stats: {e}")
            return {"mm_staff": {}, "mm_clients": {}}
    
    return {"mm_staff": {}, "mm_clients": {}}

def save_mm_stats_safe(mm_stats_file, mm_stats):
    """Safely save MM stats with file locking"""
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            temp_file = mm_stats_file + f".tmp.{os.getpid()}"
            
            with open(temp_file, "w") as f:
                json.dump(mm_stats, f, indent=4)
            
            with open(mm_stats_file, "a") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    os.replace(temp_file, mm_stats_file)
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            print(f"Error saving MM stats: {e}")
            try:
                with open(mm_stats_file, "w") as f:
                    json.dump(mm_stats, f, indent=4)
                return True
            except:
                return False
    
    return False

def load_exchangers():
    try:
        with open(EXCHANGERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_exchangers(data):
    with open(EXCHANGERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "i2c_category": None,
            "c2i_category": None,
            "pkr2c_category": None,
            "c2pkr_category": None,
            "paypal2c_category": None,
            "c2paypal_category": None,
            "c2c_category": None,
            "i2c_role": None,
            "c2i_role": None,
            "pkr2c_role": None,
            "c2pkr_role": None,
            "paypal2c_role": None,
            "c2paypal_role": None,
            "c2c_role": None,
            "exchanger_role": None,
            "owner_role": None,
            "leaderboard_channel": None,
            "transcript_channel": None
        }

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_tickets():
    try:
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_tickets(data):
    with open(TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_next_ticket_number(exchange_type):
    tickets = load_tickets()
    if exchange_type not in tickets:
        tickets[exchange_type] = {"counter": 0, "active": {}}
    tickets[exchange_type]["counter"] += 1
    save_tickets(tickets)
    return tickets[exchange_type]["counter"]

# ========================================================

def load_upi():
    try:
        with open(UPI_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_upi(data):
    with open(UPI_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_cashback():
    try:
        with open(CASHBACK_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_cashback(data):
    with open(CASHBACK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_cashback_code():
    return f"SWAPPYCASHBACK-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

def should_get_cashback():
    """50% chance to get cashback"""
    return random.random() < 0.50

def generate_cashback_amount():
    """Generate cashback amount based on weighted probabilities"""
    rand = random.random() * 100
    
    if rand < 0.0001:
        return 69
    elif rand < 0.01:
        return 20
    elif rand < 1.01:
        return 8
    elif rand < 3.51:
        return 5
    elif rand < 9.51:
        return 3
    elif rand < 19.51:
        return 2
    else:
        return 1

class UPIModal(Modal):
    def __init__(self, cashback_code, amount):
        super().__init__(title="Enter UPI ID for Cashback")
        self.cashback_code = cashback_code
        self.amount = amount
        
        self.upi_input = TextInput(
            label="UPI ID",
            placeholder="example@upi",
            required=True,
            max_length=100
        )
        self.add_item(self.upi_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        upi_id = self.upi_input.value
        
        cashback_data = load_cashback()
        
        if self.cashback_code in cashback_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} **Cashback Already Claimed**\n\n{EMOJI_SHARE} This cashback code has already been used and is no longer valid.\n{EMOJI_SHARE} Each code can only be claimed once.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        cashback_data[self.cashback_code] = {
            "user_id": interaction.user.id,
            "amount": self.amount,
            "upi_id": upi_id,
            "status": "pending",
            "claimed": True
        }
        save_cashback(cashback_data)
        
        log_channel = bot.get_channel(CASHBACK_LOG_CHANNEL)
        if log_channel:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} Cashback Request\n\n**Cashback Details**\n{EMOJI_SHARE} **Code:** `{self.cashback_code}`\n{EMOJI_SHARE} **Amount:** ₹{self.amount}\n{EMOJI_SHARE} **Status:** 🟡 Pending\n\n**User Information**\n{EMOJI_DOT} **User:** {interaction.user.mention}\n{EMOJI_DOT} **User ID:** `{interaction.user.id}`\n{EMOJI_DOT} **UPI ID:** `{upi_id}`",
                color=0x2ECC71
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            
            view = CashbackSentView(self.cashback_code, interaction.user.id, upi_id)
            await log_channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_TICK} Cashback Request Submitted\n\n{EMOJI_SHARE} Your cashback request has been submitted successfully!\n{EMOJI_SHARE} **Amount:** ₹{self.amount}\n{EMOJI_SHARE} **Code:** `{self.cashback_code}`\n\n-# {EMOJI_TICK} You will be notified once the payment is processed",
                color=0x2ECC71
            ),
            ephemeral=True
        )


class CashbackSentView(View):
    def __init__(self, cashback_code, user_id, upi_id):
        super().__init__(timeout=None)
        self.cashback_code = cashback_code
        self.user_id = user_id
        self.upi_id = upi_id
    
    @discord.ui.button(label="✓ Sent", style=discord.ButtonStyle.green, custom_id="cashback_sent")
    async def sent_button(self, interaction: discord.Interaction, button: Button):
        cashback_data = load_cashback()
        if self.cashback_code in cashback_data:
            cashback_data[self.cashback_code]["status"] = "sent"
            save_cashback(cashback_data)
            
            amount = cashback_data[self.cashback_code]["amount"]
            upi_id = cashback_data[self.cashback_code]["upi_id"]
            
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} Cashback Request\n\n**Cashback Details**\n{EMOJI_SHARE} **Code:** `{self.cashback_code}`\n{EMOJI_SHARE} **Amount:** ₹{amount}\n{EMOJI_TICK} **Status:** ✅ Sent\n\n**User Information**\n{EMOJI_DOT} **User:** <@{self.user_id}>\n{EMOJI_DOT} **User ID:** `{self.user_id}`\n{EMOJI_DOT} **UPI ID:** `{upi_id}`",
                color=0x00FF00
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            history_channel = bot.get_channel(CASHBACK_HISTORY_CHANNEL)
            if history_channel:
                history_embed = discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_TICK} Cashback Claimed\n\n**Cashback Details**\n{EMOJI_SHARE} **Code:** `{self.cashback_code}`\n{EMOJI_SHARE} **Amount:** ₹{amount}\n{EMOJI_SHARE} **Status:** ✅ Paid\n\n**User Information**\n{EMOJI_DOT} **Client:** **Anonymous**",
                    color=0x2ECC71
                )
                history_embed.set_footer(text="Made and managed by Swappy Exchange")
                await history_channel.send(embed=history_embed)
            
            try:
                user = await bot.fetch_user(self.user_id)
                notification_embed = discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_TICK} Cashback Sent!\n\n{EMOJI_SHARE} Your cashback of **₹{amount}** has been sent to your UPI!\n{EMOJI_SHARE} **Code:** `{self.cashback_code}`\n{EMOJI_SHARE} **UPI ID:** `{upi_id}`\n\n-# {EMOJI_TICK} Thank you for using Swappy Exchange!",
                    color=0x2ECC71
                )
                notification_embed.set_footer(text="Made and managed by Swappy Exchange")
                await user.send(embed=notification_embed)
            except:
                pass
    
    @discord.ui.button(label="Copy UPI", style=discord.ButtonStyle.blurple, custom_id="copy_upi")
    async def copy_upi_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"{self.upi_id}",
            ephemeral=True
        )

class ExchangeSelectDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="INR TO CRYPTO", emoji="<:Inr:1409881943255945369>"),
            discord.SelectOption(label="CRYPTO TO INR", emoji="<:Inr:1409881943255945369>"),
            discord.SelectOption(label="PKR TO CRYPTO", emoji="<:pkr:1444254255287500852>"),
            discord.SelectOption(label="CRYPTO TO PKR", emoji="<:pkr:1444254255287500852>"),
            discord.SelectOption(label="PAYPAL TO CRYPTO", emoji="<:Paypal:1444251160163782657>"),
            discord.SelectOption(label="CRYPTO TO PAYPAL", emoji="<:Paypal:1444251160163782657>"),
            discord.SelectOption(label="CRYPTO TO CRYPTO", emoji="<:crypto:1444251229344497664>")
        ]
        
        super().__init__(
            placeholder="Select your Exchange type",
            options=options,
            custom_id="exchange_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        exchange_type = self.values[0]
        modal = AmountModal(exchange_type)
        await interaction.response.send_modal(modal)

class ExchangeSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ExchangeSelectDropdown())

class AmountModal(Modal):
    def __init__(self, exchange_type):
        super().__init__(title=f"Enter Amount - {exchange_type}")
        self.exchange_type = exchange_type
        
        # Logic ko __init__ ke andar indent kiya
        if exchange_type in ["INR TO CRYPTO", "CRYPTO TO INR"]:
            placeholder = "500₹ or 5$"
        elif exchange_type in ["PKR TO CRYPTO", "CRYPTO TO PKR"]:
            placeholder = "500 PKR or 5$"
        elif exchange_type in ["PAYPAL TO CRYPTO", "CRYPTO TO PAYPAL"]:
            placeholder = "50€"
        else:
            placeholder = "5$"
        
        self.amount_input = TextInput(
            label="Amount",
            placeholder=placeholder,
            required=True,
            max_length=50
        )
        self.add_item(self.amount_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        amount_str = self.amount_input.value.strip()
        
        # Variables init
        amount_value = 0.0
        currency = ""

        try:
            # Logic flow aur indentation fix kiya
            if self.exchange_type == "INR TO CRYPTO":
                if "₹" in amount_str:
                    amount_value = float(amount_str.replace("₹", "").strip())
                    currency = "INR"
                else:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Format\n\n{EMOJI_SHARE} Please use ₹ symbol for INR (e.g., 500₹)",
                            color=0xFF0000
                        ),
                        ephemeral=True
                    )
                    return

            elif self.exchange_type == "PKR TO CRYPTO":
                if "PKR" in amount_str.upper():
                    amount_value = float(amount_str.upper().replace("PKR", "").strip())
                    currency = "PKR"
                else:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Format\n\n{EMOJI_SHARE} Please use PKR (e.g., 500 PKR)",
                            color=0xFF0000
                        ),
                        ephemeral=True
                    )
                    return

            elif self.exchange_type in ["CRYPTO TO INR", "CRYPTO TO PKR", "CRYPTO TO CRYPTO"]:
                if "$" in amount_str:
                    amount_value = float(amount_str.replace("$", "").strip())
                    currency = "USD"
                else:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Format\n\n{EMOJI_SHARE} Please use $ symbol (e.g., 5$)",
                            color=0xFF0000
                        ),
                        ephemeral=True
                    )
                    return

            elif self.exchange_type in ["PAYPAL TO CRYPTO", "CRYPTO TO PAYPAL"]:
                if "€" in amount_str:
                    amount_value = float(amount_str.replace("€", "").strip())
                    currency = "EUR"
                else:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Format\n\n{EMOJI_SHARE} Please use € symbol (e.g., 50€)",
                            color=0xFF0000
                        ),
                        ephemeral=True
                    )
                    return
            
            # Show payment method dropdown or crypto selection
            if self.exchange_type in ["PAYPAL TO CRYPTO", "CRYPTO TO PAYPAL"]:
                view = PaymentTypeSelect(self.exchange_type, amount_value, currency)
                await interaction.response.send_message(
                    embed=discord.Embed(
                        description=f"## {HEADER}\n{EMOJI_SERVICES} Select Payment Type",
                        color=0x2ECC71
                    ),
                    view=view,
                    ephemeral=True
                )
            elif self.exchange_type == "CRYPTO TO CRYPTO":
                view = CryptoSelect(self.exchange_type, amount_value, currency, None)
                await interaction.response.send_message(
                    embed=discord.Embed(
                        description=f"## {HEADER}\n{EMOJI_SERVICES} Select Cryptocurrency",
                        color=0x2ECC71
                    ),
                    view=view,
                    ephemeral=True
                )
            else:
                view = PaymentMethodSelect(self.exchange_type, amount_value, currency)
                await interaction.response.send_message(
                    embed=discord.Embed(
                        description=f"## {HEADER}\n{EMOJI_SERVICES} Select Payment Method",
                        color=0x2ECC71
                    ),
                    view=view,
                    ephemeral=True
                )

        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Amount\n\n{EMOJI_SHARE} Please enter a valid number.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
class PaymentTypeSelect(View):
    def __init__(self, exchange_type, amount, currency):
        super().__init__(timeout=180)
        self.exchange_type = exchange_type
        self.amount = amount
        self.currency = currency
        
        select = Select(
            placeholder="Choose payment type",
            options=[
                discord.SelectOption(label="Balance", value="Balance"),
                discord.SelectOption(label="Card", value="Card")
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        payment_type = interaction.data["values"][0]
        
        view = CryptoSelect(self.exchange_type, self.amount, self.currency, payment_type)
        await interaction.response.edit_message(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} Select Cryptocurrency",
                color=0x2ECC71
            ),
            view=view
        )

class PaymentMethodSelect(View):
    def __init__(self, exchange_type, amount, currency):
        super().__init__(timeout=180)
        self.exchange_type = exchange_type
        self.amount = amount
        self.currency = currency
        
        if exchange_type in ["INR TO CRYPTO", "CRYPTO TO INR"]:
            options = [
                discord.SelectOption(label="FAMPAY", value="FAMPAY"),
                discord.SelectOption(label="PHONEPE", value="PHONEPE"),
                discord.SelectOption(label="GPAY", value="GPAY"),
                discord.SelectOption(label="NAVI", value="NAVI"),
                discord.SelectOption(label="OMNI", value="OMNI"),
                discord.SelectOption(label="MOBIKWIK", value="MOBIKWIK"),
                discord.SelectOption(label="AMAZON PAY", value="AMAZON PAY"),
                discord.SelectOption(label="OTHERS", value="OTHERS")
            ]
        elif exchange_type in ["PKR TO CRYPTO", "CRYPTO TO PKR"]:
            options = [
                discord.SelectOption(label="EASYPAISA", value="EASYPAISA"),
                discord.SelectOption(label="SADAPAY", value="SADAPAY"),
                discord.SelectOption(label="NAYAPAY", value="NAYAPAY"),
                discord.SelectOption(label="UPAISA", value="UPAISA"),
                discord.SelectOption(label="JAZZCASH", value="JAZZCASH"),
                discord.SelectOption(label="NET-BANKING", value="NET-BANKING"),
                discord.SelectOption(label="OTHER", value="OTHER")
            ]
        else:
            options = []
        
        select = Select(
            placeholder="Choose payment method",
            options=options
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        payment_method = interaction.data["values"][0]
        
        view = CryptoSelect(self.exchange_type, self.amount, self.currency, payment_method)
        await interaction.response.edit_message(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} Select Cryptocurrency",
                color=0x2ECC71
            ),
            view=view
        )

class CryptoSelect(View):
    def __init__(self, exchange_type, amount, currency, payment_method):
        super().__init__(timeout=180)
        self.exchange_type = exchange_type
        self.amount = amount
        self.currency = currency
        self.payment_method = payment_method
        
        select = Select(
            placeholder="Choose cryptocurrency",
            options=[
                discord.SelectOption(label="LTC", value="LTC"),
                discord.SelectOption(label="ETH", value="ETH"),
                discord.SelectOption(label="SOL", value="SOL"),
                discord.SelectOption(label="USDT", value="USDT"),
                discord.SelectOption(label="USDC", value="USDC"),
                discord.SelectOption(label="BTC", value="BTC"),
                discord.SelectOption(label="POLYGON", value="POLYGON"),
                discord.SelectOption(label="OTHERS", value="OTHERS")
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        crypto = interaction.data["values"][0]
        
        view = ConfirmationView(self.exchange_type, self.amount, self.currency, self.payment_method, crypto, interaction.user)
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Important Notice\n\n{EMOJI_SHARE} **Do not deal outside the ticket**\n{EMOJI_SHARE} We are not responsible for scams outside tickets\n{EMOJI_SHARE} Always verify exchanger details before proceeding\n\n**Your Exchange Details:**\n{EMOJI_DOT} Type: ```{self.exchange_type}```\n{EMOJI_DOT} Amount: ```{self.amount} {self.currency}```\n{EMOJI_DOT} Payment: ```{self.payment_method if self.payment_method else 'N/A'}```\n{EMOJI_DOT} Crypto: ```{crypto}```",
            color=0xFFA500
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        
        await interaction.response.edit_message(embed=embed, view=view)

# ============= CONFIRMATION VIEW =============
class ConfirmationView(View):
    def __init__(self, exchange_type, amount, currency, payment_method, crypto, user):
        super().__init__(timeout=180)
        self.exchange_type = exchange_type
        self.amount = amount
        self.currency = currency
        self.payment_method = payment_method
        self.crypto = crypto
        self.user = user
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        await self.create_ticket(interaction)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Cancelled\n\n{EMOJI_SHARE} Exchange request cancelled.",
                color=0xFF0000
            ),
            view=None
        )
    
    async def create_ticket(self, interaction: discord.Interaction):
        # FIRST: Respond to interaction immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        config = load_config()
        guild = interaction.guild
        
        # Map exchange type to category and role
        category_key = None
        role_key = None
        prefix = ""
        
        if self.exchange_type == "INR TO CRYPTO":
            category_key = "i2c_category"
            role_key = "i2c_role"
            prefix = "i2c"
        elif self.exchange_type == "CRYPTO TO INR":
            category_key = "c2i_category"
            role_key = "c2i_role"
            prefix = "c2i"
        elif self.exchange_type == "PKR TO CRYPTO":
            category_key = "pkr2c_category"
            role_key = "pkr2c_role"
            prefix = "pkr2c"
        elif self.exchange_type == "CRYPTO TO PKR":
            category_key = "c2pkr_category"
            role_key = "c2pkr_role"
            prefix = "c2pkr"
        elif self.exchange_type == "PAYPAL TO CRYPTO":
            category_key = "paypal2c_category"
            role_key = "paypal2c_role"
            prefix = "paypal2c"
        elif self.exchange_type == "CRYPTO TO PAYPAL":
            category_key = "c2paypal_category"
            role_key = "c2paypal_role"
            prefix = "c2paypal"
        elif self.exchange_type == "CRYPTO TO CRYPTO":
            category_key = "c2c_category"
            role_key = "c2c_role"
            prefix = "c2c"
        
        category_id = config.get(category_key)
        role_id = config.get(role_key)
        
        if not category_id:
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Configuration Error\n\n{EMOJI_SHARE} Category not configured for this exchange type.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Category channel not found.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        # Get ticket number
        ticket_num = get_next_ticket_number(prefix)
        channel_name = f"{prefix}-{ticket_num}"
        
        # Create channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        if role_id:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
        
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
        
        # Save ticket to database
        tickets = load_tickets()
        if prefix not in tickets:
            tickets[prefix] = {"counter": ticket_num, "active": {}}
        
        tickets[prefix]["active"][str(channel.id)] = {
            "number": ticket_num,
            "creator": self.user.id,
            "exchange_type": self.exchange_type,
            "amount": self.amount,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "crypto": self.crypto,
            "claimed": False,
            "claimer": None
        }
        save_tickets(tickets)
        
        # Send message in channel
        role_mention = f"<@&{role_id}>" if role_id else ""
        await channel.send(f"{self.user.mention} {role_mention}")
        
        # Server description embed
        server_embed = discord.Embed(
            title="SWAPPY EXCHANGES",
            description="Welcome to Swappy Exchange! Please wait for an exchanger to claim your ticket.",
            color=0x2ECC71
        )
        server_embed.set_footer(text="Made and managed by Swappy Exchange")
        await channel.send(embed=server_embed)
        
        # Ticket details embed
        details_embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Exchange Request Details\n\n{EMOJI_DOT} **Exchange Type**\n```{self.exchange_type}```\n{EMOJI_DOT} **Amount**\n ```{self.amount} {self.currency}```\n{EMOJI_DOT} **Payment Method**\n ```{self.payment_method if self.payment_method else 'N/A'}```\n{EMOJI_DOT} **Cryptocurrency**\n ```{self.crypto}```",
            color=0x2ECC71
        )
        details_embed.set_footer(text="Made and managed by Swappy Exchange")
        
        # Buttons
        view = TicketButtonsView(channel.id, prefix)
        await channel.send(embed=details_embed, view=view)
        
        # Use followup instead of response.edit_message
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_TICK} Ticket Created\n\n{EMOJI_SHARE} Your ticket has been created: {channel.mention}",
                color=0x2ECC71
            ),
            ephemeral=True
        )

class TicketButtonsView(View):
    def __init__(self, channel_id, prefix):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.prefix = prefix
        
        self.add_item(Button(label="Claim", style=discord.ButtonStyle.green, custom_id=f"claim_{channel_id}"))
        self.add_item(Button(label="Close", style=discord.ButtonStyle.red, custom_id=f"close_{channel_id}"))
        self.add_item(Button(label="Unclaim", style=discord.ButtonStyle.grey, custom_id=f"unclaim_{channel_id}"))

class CashbackView(View):
    def __init__(self, cashback_code, amount):
        super().__init__(timeout=None)
        self.cashback_code = cashback_code
        self.amount = amount
    
    @discord.ui.button(label="🎁 Claim Cashback", style=discord.ButtonStyle.green)
    async def enter_upi(self, interaction: discord.Interaction, button: Button):
        cashback_data = load_cashback()
        if self.cashback_code in cashback_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Cashback Already Claimed\n\n{EMOJI_SHARE} This cashback code has already been used and is no longer valid.\n{EMOJI_SHARE} Each code can only be claimed once.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        modal = UPIModal(self.cashback_code, self.amount)
        await interaction.response.send_modal(modal)

class DoneConfirmationView(View):
    def __init__(self, ctx, user, amt_float, currency_symbol, crypto_upper, deal_type):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.user = user
        self.amt_float = amt_float
        self.currency_symbol = currency_symbol
        self.crypto_upper = crypto_upper
        self.deal_type = deal_type
        self.message = None
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Access Denied\n\n{EMOJI_SHARE} Only {self.user.mention} can confirm this exchange.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            await self.message.delete()
        except:
            pass
        
        await self.complete_exchange()
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Access Denied\n\n{EMOJI_SHARE} Only {self.user.mention} can decline this exchange.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            await self.message.delete()
        except:
            pass
        
        await self.ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Exchange Cancelled\n\n{EMOJI_SHARE} The exchange has not been logged.",
                color=0xFF0000
            )
        )
    
    async def complete_exchange(self):
        role_id = 1418550582960193616
        log_channel_id = 1438999681580535920
        stats_file = "stats.json"
        
        config = load_config()
        cat_inr_to_crypto = 1436393106600759346
        cat_crypto_to_inr = 1418551133890416671
        cat_pkr2c = config.get("pkr2c_category")
        cat_c2pkr = config.get("c2pkr_category")
        cat_paypal2c = config.get("paypal2c_category")
        cat_c2paypal = config.get("c2paypal_category")
        transcript_channel_id = config.get("transcript_channel")
        
        try:
            guild = self.ctx.guild
            log_channel = guild.get_channel(log_channel_id)
            
            stats = load_stats_safe(stats_file)
            
            for key in ["staff", "clients", "daily", "monthly", "yearly", "weekly"]:
                if key not in stats:
                    stats[key] = {}
            
            now = datetime.datetime.now()
            day_key = now.strftime("%Y-%m-%d")
            month_key = now.strftime("%Y-%m")
            year_key = str(now.year)
            week_key = now.strftime("%Y-W%U")  # Week number
            
            staff_id = str(self.ctx.author.id)
            client_id = str(self.user.id)
            
            # Initialize stats
            if staff_id not in stats["staff"]:
                stats["staff"][staff_id] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0, "total_amt_pkr": 0, "total_amt_eur": 0}
            else:
                for key in ["total_amt_usd", "total_amt_inr", "total_amt_pkr", "total_amt_eur"]:
                    if key not in stats["staff"][staff_id]:
                        stats["staff"][staff_id][key] = 0
            
            if client_id not in stats["clients"]:
                stats["clients"][client_id] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0, "total_amt_pkr": 0, "total_amt_eur": 0}
            else:
                for key in ["total_amt_usd", "total_amt_inr", "total_amt_pkr", "total_amt_eur"]:
                    if key not in stats["clients"][client_id]:
                        stats["clients"][client_id][key] = 0
            
            # Initialize time-based stats
            for time_key, time_type in [(day_key, "daily"), (month_key, "monthly"), (year_key, "yearly"), (week_key, "weekly")]:
                if time_key not in stats[time_type]:
                    stats[time_type][time_key] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0, "total_amt_pkr": 0, "total_amt_eur": 0}
                else:
                    for key in ["total_amt_usd", "total_amt_inr", "total_amt_pkr", "total_amt_eur"]:
                        if key not in stats[time_type][time_key]:
                            stats[time_type][time_key][key] = 0
            
            # Update deals count
            stats["staff"][staff_id]["total_deals"] += 1
            stats["clients"][client_id]["total_deals"] += 1
            stats["daily"][day_key]["total_deals"] += 1
            stats["monthly"][month_key]["total_deals"] += 1
            stats["yearly"][year_key]["total_deals"] += 1
            stats["weekly"][week_key]["total_deals"] += 1
            
            # Update amount based on currency
            if self.currency_symbol == '$':
                currency_key = "total_amt_usd"
            elif self.currency_symbol == '₹':
                currency_key = "total_amt_inr"
            elif self.currency_symbol == '€':
                currency_key = "total_amt_eur"
            else:  # PKR
                currency_key = "total_amt_pkr"
            
            stats["staff"][staff_id][currency_key] += self.amt_float
            stats["clients"][client_id][currency_key] += self.amt_float
            stats["daily"][day_key][currency_key] += self.amt_float
            stats["monthly"][month_key][currency_key] += self.amt_float
            stats["yearly"][year_key][currency_key] += self.amt_float
            stats["weekly"][week_key][currency_key] += self.amt_float
            
            success = save_stats_safe(stats_file, stats)
            if not success:
                print("WARNING: Failed to save stats!")
            
            # Log embed
            amt_int = int(self.amt_float)
            log_embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_TICK} Exchange Done\n\n**Client**\n{EMOJI_DOT} {self.user.mention}\n\n**Exchanger**\n{EMOJI_DOT} {self.ctx.author.mention}\n\n**Deal**\n{EMOJI_DOT} {self.deal_type}\n\n**Amount**\n{EMOJI_DOT} {self.currency_symbol}{amt_int}\n\n**Crypto**\n{EMOJI_DOT} {self.crypto_upper}",
                color=0x2ECC71
            )
            log_embed.set_footer(text="Made and managed by Swappy Exchange")
            await log_channel.send(embed=log_embed)
            
            # Send transcript to transcript channel
            if transcript_channel_id:
                transcript_channel = guild.get_channel(transcript_channel_id)
                if transcript_channel:
                    try:
                        transcript = await chat_exporter.export(self.ctx.channel)
                        if transcript:
                            transcript_file = discord.File(
                                io.BytesIO(transcript.encode()),
                                filename=f"transcript-{self.ctx.channel.name}.html"
                            )
                            
                            transcript_embed = discord.Embed(
                                description=f"## {HEADER}\n{EMOJI_SERVICES} Deal Transcript\n\n**Client:** {self.user.mention}\n**Exchanger:** {self.ctx.author.mention}\n**Amount:** {self.currency_symbol}{amt_int}\n**Crypto:** {self.crypto_upper}",
                                color=0x2ECC71
                            )
                            transcript_embed.set_footer(text="Made and managed by Swappy Exchange")
                            
                            await transcript_channel.send(embed=transcript_embed, file=transcript_file)
                    except Exception as e:
                        print(f"Error sending transcript: {e}")
            
            # Confirmation embed
            embed_confirm = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_TICK} Exchange Logged\n\n{EMOJI_SHARE} The exchange has been recorded successfully.",
                color=0x2ECC71
            )
            embed_confirm.set_footer(text="Made and managed by Swappy Exchange")
            await self.ctx.send(embed=embed_confirm)
            
            # Send +rep message
            if self.ctx.channel.category.id == cat_inr_to_crypto:
                rep_message = f"+rep {self.ctx.author.id} UPI -> {self.crypto_upper} | {self.currency_symbol}{self.amt_float}"
            elif self.ctx.channel.category.id == cat_crypto_to_inr:
                rep_message = f"+rep {self.ctx.author.id} {self.crypto_upper} -> UPI | {self.currency_symbol}{self.amt_float}"
            elif cat_pkr2c and self.ctx.channel.category.id == cat_pkr2c:
                rep_message = f"+rep {self.ctx.author.id} PKR -> {self.crypto_upper} | {self.currency_symbol}{self.amt_float}"
            elif cat_c2pkr and self.ctx.channel.category.id == cat_c2pkr:
                rep_message = f"+rep {self.ctx.author.id} {self.crypto_upper} -> PKR | {self.currency_symbol}{self.amt_float}"
            elif cat_paypal2c and self.ctx.channel.category.id == cat_paypal2c:
                rep_message = f"+rep {self.ctx.author.id} PayPal -> {self.crypto_upper} | {self.currency_symbol}{self.amt_float}"
            elif cat_c2paypal and self.ctx.channel.category.id == cat_c2paypal:
                rep_message = f"+rep {self.ctx.author.id} {self.crypto_upper} -> PayPal | {self.currency_symbol}{self.amt_float}"
            else:
                rep_message = f"+rep {self.ctx.author.id} Exchange | {self.currency_symbol}{self.amt_float}"
            
            await self.ctx.send(rep_message)
            
            # Rename channel
            try:
                new_channel_name = f"done-by-{self.ctx.author.name}"
                await self.ctx.channel.edit(name=new_channel_name)
            except:
                pass
            
            # Cashback system
            if should_get_cashback():
                cashback_code = generate_cashback_code()
                cashback_amount = generate_cashback_amount()
                
                try:
                    cashback_embed = discord.Embed(
                        description=f"## {HEADER}\n{EMOJI_SERVICES} Congratulations! Cashback Reward\n\n{EMOJI_TICK} You've received a **cashback reward** for your recent exchange!\n\n{EMOJI_SHARE} **Cashback Code:** `{cashback_code}`\n{EMOJI_SHARE} **Cashback Amount:** ₹{cashback_amount}\n\n-# {EMOJI_DOT} Click the button below to enter your UPI ID and claim your cashback",
                        color=0x2ECC71
                    )
                    cashback_embed.set_footer(text="Made and managed by Swappy Exchange")
                    
                    view = CashbackView(cashback_code, cashback_amount)
                    await self.user.send(embed=cashback_embed, view=view)
                except:
                    pass
            else:
                try:
                    no_cashback_embed = discord.Embed(
                        description=f"## {HEADER}\n{EMOJI_SERVICES} Cashback Reward\n\n{EMOJI_WARNING} **Better Luck Next Time!**\n\n{EMOJI_SHARE} You didn't receive a cashback this time, but don't worry!\n{EMOJI_SHARE} Keep exchanging for more chances to win cashback rewards.\n\n-# {EMOJI_DOT} Thank you for using Swappy Exchange!",
                        color=0xFFA500
                    )
                    no_cashback_embed.set_footer(text="Made and managed by Swappy Exchange")
                    await self.user.send(embed=no_cashback_embed)
                except:
                    pass
            
        except Exception as e:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} {e}",
                color=0xFF0000
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            await self.ctx.send(embed=embed)
            print(f"Exception in done command: {e}")
            import traceback
            traceback.print_exc()

class LeaderboardView(View):
    def __init__(self, stats):
        super().__init__(timeout=None)
        self.stats = stats
        self.show_inr = False
    
    @discord.ui.button(label="Toggle to INR", style=discord.ButtonStyle.blurple, custom_id="toggle_currency")
    async def toggle_currency(self, interaction: discord.Interaction, button: Button):
        self.show_inr = not self.show_inr
        button.label = "Toggle to USD" if self.show_inr else "Toggle to INR"
        
        embed = self.generate_leaderboard_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Search User", style=discord.ButtonStyle.green, custom_id="search_user")
    async def search_user(self, interaction: discord.Interaction, button: Button):
        modal = UserSearchModal(self.stats)
        await interaction.response.send_modal(modal)
    
    def generate_leaderboard_embed(self):
        clients = self.stats.get("clients", {})
        
        if self.show_inr:
            sorted_clients = sorted(
                clients.items(),
                key=lambda x: x[1].get("total_amt_inr", 0),
                reverse=True
            )[:10]
            
            description = f"## {HEADER}\n{EMOJI_SERVICES} Top 10 Clients (INR)\n\n"
            
            medals = ["🥇", "🥈", "🥉"]
            for idx, (user_id, data) in enumerate(sorted_clients):
                rank = medals[idx] if idx < 3 else f"**{idx + 1}.**"
                deals = data.get("total_deals", 0)
                amount = data.get("total_amt_inr", 0)
                description += f"{rank} <@{user_id}>\n{EMOJI_DOT} Deals: **{deals}** | Volume: **₹{amount:,.2f}**\n\n"
        else:
            sorted_clients = sorted(
                clients.items(),
                key=lambda x: x[1].get("total_amt_usd", 0),
                reverse=True
            )[:10]
            
            description = f"## {HEADER}\n{EMOJI_SERVICES} Top 10 Clients (USD)\n\n"
            
            medals = ["🥇", "🥈", "🥉"]
            for idx, (user_id, data) in enumerate(sorted_clients):
                rank = medals[idx] if idx < 3 else f"**{idx + 1}.**"
                deals = data.get("total_deals", 0)
                amount = data.get("total_amt_usd", 0)
                description += f"{rank} <@{user_id}>\n{EMOJI_DOT} Deals: **{deals}** | Volume: **${amount:,.2f}**\n\n"
        
        embed = discord.Embed(description=description, color=0x2ECC71)
        embed.set_footer(text="Made and managed by Swappy Exchange")
        return embed

class UserSearchModal(Modal):
    def __init__(self, stats):
        super().__init__(title="Search User")
        self.stats = stats
        
        self.user_input = TextInput(
            label="Username or User ID",
            placeholder="Enter username or user ID",
            required=True
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        search_query = self.user_input.value.strip()
        
        # Try to find user by ID first
        user_id = None
        if search_query.isdigit():
            user_id = search_query
        else:
            # Search by username (FIXED INDENTATION HERE)
            for member in interaction.guild.members:
                if member.name.lower() == search_query.lower() or member.display_name.lower() == search_query.lower():
                    user_id = str(member.id)
                    break
        
        if not user_id or user_id not in self.stats.get("clients", {}):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} User Not Found\n\n{EMOJI_SHARE} No client data found for this user.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        data = self.stats["clients"][user_id]
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Client Stats\n\n"
                        f"**User:** <@{user_id}>\n\n"
                        f"**Statistics**\n"
                        f"{EMOJI_DOT} Total Deals: **{data.get('total_deals', 0)}**\n"
                        f"{EMOJI_DOT} USD Volume: **${data.get('total_amt_usd', 0):,.2f}**\n"
                        f"{EMOJI_DOT} INR Volume: **₹{data.get('total_amt_inr', 0):,.2f}**\n"
                        f"{EMOJI_DOT} PKR Volume: **{data.get('total_amt_pkr', 0):,.2f} PKR**\n"
                        f"{EMOJI_DOT} EUR Volume: **€{data.get('total_amt_eur', 0):,.2f}**",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def leaderboard(ctx):
    """Send client leaderboard to configured channel"""
    admin_role_id = 1427890290794172416
    try:
        await ctx.message.delete()
    except:
        pass

    if not any(r.id == admin_role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    config = load_config()
    leaderboard_channel_id = config.get("leaderboard_channel")

    if not leaderboard_channel_id:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Configuration Error\n\n{EMOJI_SHARE} Leaderboard channel not configured. Use `.setconfig` to set it.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    channel = ctx.guild.get_channel(leaderboard_channel_id)
    if not channel:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Channel Not Found\n\n{EMOJI_SHARE} Leaderboard channel not found.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    stats = load_stats_safe("stats.json")
    view = LeaderboardView(stats)
    embed = view.generate_leaderboard_embed()

    await channel.send(embed=embed, view=view)

    await ctx.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Success\n\n{EMOJI_SHARE} Leaderboard sent to {channel.mention}",
            color=0x2ECC71
        )
    )

class ForceDoneView(View):
    def __init__(self, ctx, user, amt_float, currency_symbol, crypto_upper, deal_type):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.user = user
        self.amt_float = amt_float
        self.currency_symbol = currency_symbol
        self.crypto_upper = crypto_upper
        self.deal_type = deal_type
    
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        config = load_config()
        owner_role_id = config.get("owner_role")
        
        if not owner_role_id or not any(r.id == owner_role_id for r in interaction.user.roles):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} Only owners can approve force done requests.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Complete the exchange - Ensure DoneConfirmationView class exists in your code
        confirmation_view = DoneConfirmationView(self.ctx, self.user, self.amt_float, self.currency_symbol, self.crypto_upper, self.deal_type)
        await confirmation_view.complete_exchange()
        
        await interaction.message.edit(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_TICK} Force Done Approved\n\n{EMOJI_SHARE} Exchange has been logged by {interaction.user.mention}",
                color=0x2ECC71
            ),
            view=None
        )
    
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject_button(self, interaction: discord.Interaction, button: Button):
        config = load_config()
        owner_role_id = config.get("owner_role")
        
        if not owner_role_id or not any(r.id == owner_role_id for r in interaction.user.roles):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} Only owners can reject force done requests.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
            return
        
        await interaction.response.edit_message(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Force Done Rejected\n\n{EMOJI_SHARE} Request rejected by {interaction.user.mention}",
                color=0xFF0000
            ),
            view=None
        )

@bot.command()
async def forcedone(ctx, user: discord.User = None, amt: str = None, crypto: str = None):
    """Force done when client is offline (requires owner approval)"""
    role_id = 1418550582960193616
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not user or not amt or not crypto:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.forcedone <user> <amount with ₹/$/ €/PKR> <crypto name>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not any(r.id == role_id for r in ctx.author.roles):
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    # Extract amount and currency symbol
    if amt.startswith('₹') or amt.startswith('$') or amt.startswith('€'):
        currency_symbol = amt[0]
        amt_value = amt[1:]
    elif amt.endswith('₹') or amt.endswith('$') or amt.endswith('€'):
        currency_symbol = amt[-1]
        amt_value = amt[:-1]
    elif 'PKR' in amt.upper():
        currency_symbol = 'PKR'
        amt_value = amt.upper().replace('PKR', '').strip()
    else:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Amount Format\n\n{EMOJI_SHARE} Amount must include ₹, $, €, or PKR symbol.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not amt_value.replace(".", "", 1).isdigit():
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Amount\n\n{EMOJI_SHARE} Amount must be a number.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    amt_float = float(amt_value)
    crypto_upper = crypto.upper()
    
    config = load_config()
    owner_role_id = config.get("owner_role")
    
    if not owner_role_id:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Configuration Error\n\n{EMOJI_SHARE} Owner role not configured.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    # Get config for categories
    cat_inr_to_crypto = 1436393106600759346
    cat_crypto_to_inr = 1418551133890416671
    cat_pkr2c = config.get("pkr2c_category")
    cat_c2pkr = config.get("c2pkr_category")
    cat_paypal2c = config.get("paypal2c_category")
    cat_c2paypal = config.get("c2paypal_category")
    
    # Determine deal type
    if ctx.channel.category and ctx.channel.category.id == cat_inr_to_crypto:
        deal_type = "INR to Crypto"
    elif ctx.channel.category and ctx.channel.category.id == cat_crypto_to_inr:
        deal_type = "Crypto to INR"
    elif cat_pkr2c and ctx.channel.category and ctx.channel.category.id == cat_pkr2c:
        deal_type = "PKR to Crypto"
    elif cat_c2pkr and ctx.channel.category and ctx.channel.category.id == cat_c2pkr:
        deal_type = "Crypto to PKR"
    elif cat_paypal2c and ctx.channel.category and ctx.channel.category.id == cat_paypal2c:
        deal_type = "PayPal to Crypto"
    elif cat_c2paypal and ctx.channel.category and ctx.channel.category.id == cat_c2paypal:
        deal_type = "Crypto to PayPal"
    else:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Category\n\n{EMOJI_SHARE} This command can only be used in exchange categories.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    # Send approval request
    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_WARNING} Force Done Request\n\n"
                    f"**Exchanger:** {ctx.author.mention}\n"
                    f"**Client:** {user.mention} (Offline)\n"
                    f"**Amount:** {currency_symbol}{amt_float}\n"
                    f"**Crypto:** {crypto_upper}\n"
                    f"**Deal Type:** {deal_type}\n\n"
                    f"{EMOJI_SHARE} Exchanger wants to force complete this deal because client is offline.\n"
                    f"{EMOJI_SHARE} Please review the ticket and approve or reject.",
        color=0xFFA500
    )
    embed.set_footer(text="Made and managed by Swappy Exchange")
    
    view = ForceDoneView(ctx, user, amt_float, currency_symbol, crypto_upper, deal_type)
    
    await ctx.send(content=f"<@&{owner_role_id}>", embed=embed, view=view)

@bot.command()
async def calc(ctx, *, expression: str = None):
    try: await ctx.message.delete()
    except: pass
    if not expression:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.calc <expression>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    allowed = "0123456789+-*/(). "
    if any(c not in allowed for c in expression):
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Characters\n\n{EMOJI_SHARE} Invalid characters in expression!",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    try:
        result = eval(expression)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Calculator\n\n**Expression**\n```{expression}```\n\n**Result**\n```{result}```",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await asyncio.sleep(1)
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} {e}",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await asyncio.sleep(1)
        await ctx.send(embed=embed)

@bot.command()
async def panel(ctx):
    """Create the exchange panel"""
    admin_role_id = 1427890290794172416
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not any(r.id == admin_role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    # Header message
    header_msg = "# <:anc:1444259034604769360> | Swappy Exchanges"
    await ctx.send(header_msg)
    
    # First embed - Terms
    terms_embed = discord.Embed(
        description="> By opening a ticket, you automatically agree to our https://discord.com/channels/1407180277708619846/1418466504898379826\n> - For Third-Party Exchanges https://discord.com/channels/1407180277708619846/1427179960702992385",
        color=0x2ECC71
    )
    await ctx.send(embed=terms_embed)
    
    # Second embed - Rates
    rates_embed = discord.Embed(
        description="## <:globe:1444258478930657300> | Exchange Rates\n### <:INR:1444251114387013774> INR Exchanges:\n> - INR to Crypto: 95/$\n> - Crypto to INR: 92/$\n### <:Paypal:1444251160163782657> Paypal Exchanges\n> - Paypal to Crypto: 10% Fees (Min. Fees - €0.50)\n> - Crypto to Paypal: 0% Fees\n### <:pkr:1444254255287500852> PKR Exchanges\n> - PKR to Crypto: 320/$\n> - Crypto to PKR: 260/$\n## <:crypto:1444251229344497664> Crypto Exchanges\n> - Crypto to Crypto: 4% Fees + (Transaction Fees)",
        color=0x2ECC71
    )
    
    # Exchange dropdown
    view = ExchangeSelectView()
    await ctx.send(embed=rates_embed, view=view)

@bot.command()
async def exchanger(ctx, user: discord.User = None, limit: str = None):
    """Toggle exchanger - Hire or Remove"""
    admin_role_id = 1427890290794172416
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not any(r.id == admin_role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not user:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.exchanger @user <limit in USD>` (to hire)\n{EMOJI_SHARE} **Usage:** `.exchanger @user` (to remove if already hired)",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    exchangers = load_exchangers()
    config = load_config()
    user_id = str(user.id)
    exchanger_role_id = config.get("exchanger_role")
    
    # Check if already hired (toggle logic)
    if user_id in exchangers:
        # Remove exchanger
        del exchangers[user_id]
        save_exchangers(exchangers)
        
        # Remove role
        if exchanger_role_id:
            role = ctx.guild.get_role(exchanger_role_id)
            if role and role in user.roles:
                await user.remove_roles(role)
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Exchanger Removed\n\n**User**\n{EMOJI_DOT} {user.mention}\n\n{EMOJI_SHARE} Exchanger has been removed from the system.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await asyncio.sleep(1)
        await ctx.send(embed=embed)
        return
    
    # Hire new exchanger
    if not limit:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Missing Limit\n\n{EMOJI_SHARE} Please provide a limit in USD to hire this exchanger.\n{EMOJI_DOT} Example: `.exchanger @user 100`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    try:
        limit_usd = float(limit.replace("$", "").strip())
        limit_inr = limit_usd * C2I
        limit_pkr = limit_usd * C2PKR
        
        exchangers[user_id] = {
            "name": user.name,
            "limit_usd": limit_usd,
            "limit_inr": limit_inr,
            "limit_pkr": limit_pkr
        }
        save_exchangers(exchangers)
        
        # Assign role
        if exchanger_role_id:
            role = ctx.guild.get_role(exchanger_role_id)
            if role:
                await user.add_roles(role)
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Exchanger Hired\n\n**Exchanger**\n{EMOJI_DOT} {user.mention}\n\n**Limits**\n{EMOJI_DOT} USD: ${limit_usd:.2f}\n{EMOJI_DOT} INR: ₹{limit_inr:.2f}\n{EMOJI_DOT} PKR: {limit_pkr:.2f} PKR\n\n{EMOJI_SHARE} Exchanger role assigned successfully.",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await asyncio.sleep(1)
        await ctx.send(embed=embed)
        
    except ValueError:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Limit\n\n{EMOJI_SHARE} Please provide a valid number for the limit.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)

@bot.command()
async def add(ctx, user: discord.User = None):
    try: await ctx.message.delete()
    except: pass
    
    if not user:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.add @user` or `.add <user_id>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    try:
        # User ko View aur Send permissions dena
        await ctx.channel.set_permissions(user, read_messages=True, send_messages=True)
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} User Added\n\n{EMOJI_SHARE} {user.mention} has been added to the ticket.",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Failed to add user. Check bot permissions.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)

@bot.command()
async def remove(ctx, user: discord.User = None):
    try: await ctx.message.delete()
    except: pass
    
    if not user:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.remove @user` or `.remove <user_id>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    try:
        # User se permissions wapas lena (View False kar dena)
        await ctx.channel.set_permissions(user, read_messages=False, send_messages=False)
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} User Removed\n\n{EMOJI_SHARE} {user.mention} has been removed from the ticket.",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Failed to remove user.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)

@bot.command()
async def claim(ctx):
    """Claim a ticket"""
    if not isinstance(ctx.channel, discord.TextChannel):
        return
    
    channel_id = str(ctx.channel.id)
    tickets = load_tickets()
    exchangers = load_exchangers()
    user_id = str(ctx.author.id)
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Find ticket
    ticket_data = None
    prefix = None
    for pref, data in tickets.items():
        if "active" in data and channel_id in data["active"]:
            ticket_data = data["active"][channel_id]
            prefix = pref
            break
    
    if not ticket_data:
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} This is not a valid ticket channel.",
                color=0xFF0000
            )
        )
        return
    
    if ticket_data.get("claimed"):
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Already Claimed\n\n{EMOJI_SHARE} This ticket has already been claimed.",
                color=0xFF0000
            )
        )
        return
    
    # Check if user is an exchanger
    if user_id not in exchangers:
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Not Authorized\n\n{EMOJI_SHARE} You are not registered as an exchanger.",
                color=0xFF0000
            )
        )
        return
    
    # Check limit
    exchanger_data = exchangers[user_id]
    amount = ticket_data["amount"]
    currency = ticket_data["currency"]
    
    if currency == "USD":
        limit_key = "limit_usd"
    elif currency == "INR":
        limit_key = "limit_inr"
    elif currency == "PKR":
        limit_key = "limit_pkr"
    else:
        limit_key = "limit_usd"
    
    if amount > exchanger_data[limit_key]:
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Limit Exceeded\n\n{EMOJI_SHARE} Amount exceeds your limit\n{EMOJI_DOT} Your Limit: {exchanger_data[limit_key]:.2f} {currency}\n{EMOJI_DOT} Ticket Amount: {amount:.2f} {currency}",
                color=0xFF0000
            )
        )
        return
    
    # Claim ticket
    ticket_data["claimed"] = True
    ticket_data["claimer"] = ctx.author.id
    save_tickets(tickets)
    
    # Update channel name
    new_name = f"claimed-by-{ctx.author.name}"
    await ctx.channel.edit(name=new_name)
    
    # Update permissions
    config = load_config()
    role_key = f"{prefix}_role"
    role_id = config.get(role_key)
    
    overwrites = ctx.channel.overwrites
    if role_id:
        role = ctx.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=False)
    
    overwrites[ctx.author] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    creator = ctx.guild.get_member(ticket_data["creator"])
    if creator:
        overwrites[creator] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    await ctx.channel.edit(overwrites=overwrites)
    
    # Send claimed message
    await ctx.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Ticket Claimed\n\n{EMOJI_SHARE} Ticket claimed by {ctx.author.mention}",
            color=0x2ECC71
        )
    )
    
    # Send tutorial embed
    tutorial_embed = discord.Embed(
        description=f"## __ Important — Tutorial:__\n- The **exchange request** shall be handled by the **Exchanger**, we have either collected a security deposit from them or they have claimed using their bypass. You must now send them the ticket amount to their details, afterwards click the **Sent Payment button** immediately. You may **Remove Exchanger** for any reason you please.\n\n- __**Do not send any higher than the ticket amount.**__\n   - Do not deal outside of a claimed ticket.\n   - Make sure to read the terms provided below.\n   - Be sure to ping any online staff for guidance/support.\n   - Do not press any buttons without reading the description.",
        color=15839539
    )
    tutorial_embed.set_author(
        name="Swappy Exchanges",
        icon_url="https://i.ibb.co/SXskChxj/b32620c149c2ba37886f44ffcdf6459f.webp[/img][/url]"
    )
    tutorial_embed.set_thumbnail(url="https://i.ibb.co/SXskChxj/b32620c149c2ba37886f44ffcdf6459f.webp[/img][/url]")
    
    await ctx.send(embed=tutorial_embed)

@bot.command()
async def unclaim(ctx):
    """Unclaim a ticket"""
    if not isinstance(ctx.channel, discord.TextChannel):
        return
    
    channel_id = str(ctx.channel.id)
    tickets = load_tickets()
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Find ticket
    ticket_data = None
    prefix = None
    for pref, data in tickets.items():
        if "active" in data and channel_id in data["active"]:
            ticket_data = data["active"][channel_id]
            prefix = pref
            break
    
    if not ticket_data:
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} This is not a valid ticket channel.",
                color=0xFF0000
            )
        )
        return
    
    if not ticket_data.get("claimed"):
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Not Claimed\n\n{EMOJI_SHARE} This ticket is not claimed yet.",
                color=0xFF0000
            )
        )
        return
    
    # Unclaim ticket
    ticket_data["claimed"] = False
    ticket_data["claimer"] = None
    save_tickets(tickets)
    
    # Restore channel name
    ticket_num = ticket_data["number"]
    new_name = f"{prefix}-{ticket_num}"
    await ctx.channel.edit(name=new_name)
    
    # Restore permissions
    config = load_config()
    role_key = f"{prefix}_role"
    role_id = config.get(role_key)
    
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }
    
    creator = ctx.guild.get_member(ticket_data["creator"])
    if creator:
        overwrites[creator] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    if role_id:
        role = ctx.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
    
    await ctx.channel.edit(overwrites=overwrites)
    
    await ctx.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Ticket Unclaimed\n\n{EMOJI_SHARE} Ticket has been unclaimed successfully.",
            color=0x2ECC71
        )
    )

@bot.command()
async def close(ctx):
    """Close a ticket with transcript"""
    if not isinstance(ctx.channel, discord.TextChannel):
        return
    
    channel_id = str(ctx.channel.id)
    tickets = load_tickets()
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Find ticket
    ticket_data = None
    prefix = None
    for pref, data in tickets.items():
        if "active" in data and channel_id in data["active"]:
            ticket_data = data["active"][channel_id]
            prefix = pref
            break
    
    if not ticket_data:
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} This is not a valid ticket channel.",
                color=0xFF0000
            )
        )
        return
    
    # Check permissions
    if ctx.author.id != ticket_data["creator"] and ctx.author.id != ticket_data.get("claimer"):
        await ctx.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} Only ticket creator or claimer can close the ticket.",
                color=0xFF0000
            )
        )
        return
    
    # Generate transcript
    await ctx.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Generating Transcript\n\n{EMOJI_SHARE} Please wait...",
            color=0x2ECC71
        )
    )
    
    transcript = await chat_exporter.export(ctx.channel)
    
    if transcript is None:
        transcript_file = None
    else:
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{ctx.channel.name}.html"
        )
    
    # Send DM to creator
    creator = ctx.guild.get_member(ticket_data["creator"])
    if creator:
        try:
            creator_embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} Ticket Closed\n\n{EMOJI_SHARE} Your ticket **{ctx.channel.name}** has been closed.\n\n**Ticket Details:**\n{EMOJI_DOT} Exchange Type: {ticket_data['exchange_type']}\n{EMOJI_DOT} Amount: {ticket_data['amount']} {ticket_data['currency']}\n{EMOJI_DOT} Crypto: {ticket_data['crypto']}",
                color=0x2ECC71
            )
            creator_embed.set_footer(text="Made and managed by Swappy Exchange")
            
            if transcript_file:
                await creator.send(embed=creator_embed, file=transcript_file)
                # Regenerate file for claimer
                transcript_file = discord.File(
                    io.BytesIO(transcript.encode()),
                    filename=f"transcript-{ctx.channel.name}.html"
                )
            else:
                await creator.send(embed=creator_embed)
        except:
            pass
    
    # Send DM to claimer
    claimer_id = ticket_data.get("claimer")
    if claimer_id:
        claimer = ctx.guild.get_member(claimer_id)
        if claimer:
            try:
                claimer_embed = discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_SERVICES} Ticket Closed\n\n{EMOJI_SHARE} Ticket **{ctx.channel.name}** has been closed.\n\n**Ticket Details:**\n{EMOJI_DOT} Exchange Type: {ticket_data['exchange_type']}\n{EMOJI_DOT} Amount: {ticket_data['amount']} {ticket_data['currency']}\n{EMOJI_DOT} Crypto: {ticket_data['crypto']}",
                    color=0x2ECC71
                )
                claimer_embed.set_footer(text="Made and managed by Swappy Exchange")
                
                if transcript_file:
                    await claimer.send(embed=claimer_embed, file=transcript_file)
                else:
                    await claimer.send(embed=claimer_embed)
            except:
                pass
    
    # Remove from tickets
    del tickets[prefix]["active"][channel_id]
    save_tickets(tickets)
    
    await ctx.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Closing Ticket\n\n{EMOJI_SHARE} This ticket will be deleted in 5 seconds...",
            color=0x2ECC71
        )
    )
    
    await asyncio.sleep(5)
    await ctx.channel.delete()
        
@bot.command()
async def upi(ctx, upi_id: str = None, amt: str = None):
    try: await ctx.message.delete()
    except: pass
    if not upi_id or not amt:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.upi <upi_id> <amt>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    try:
        upi_uri = f"upi://pay?pa={upi_id}&pn=Recipient&am={amt}&tn=I have authorised this payment and received the product&cu=INR"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(upi_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="upi_qr.png")
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} UPI Payment QR\n\n{EMOJI_SHARE} **Pay:** `{amt} INR`\n{EMOJI_SHARE} **To:** `{upi_id}`",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        embed.set_image(url="attachment://upi_qr.png")
        await asyncio.sleep(1)
        await ctx.send(file=file, embed=embed)
    except Exception as e:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} {e}",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await asyncio.sleep(1)
        await ctx.send(embed=embed)
        
@bot.command()
async def setupi(ctx, slot: str = None, upi_id: str = None):
    try: await ctx.message.delete()
    except: pass
    if not slot or not upi_id:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.setupi <slot> <upi_id>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    try:
        with open("upi.json","r") as f: data = json.load(f)
    except: data = {}
    user_id = str(ctx.author.id)
    if user_id not in data: data[user_id] = {}
    data[user_id][slot] = upi_id
    with open("upi.json","w") as f: json.dump(data,f,indent=4)
    await asyncio.sleep(1)
    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_TICK} UPI Saved\n\n{EMOJI_SHARE} Slot `{slot}` saved for your UPI.",
        color=0x2ECC71
    )
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)

@bot.command()
async def qr(ctx, slot: str = None, amt: str = None):
    try: await ctx.message.delete()
    except: pass
    
    if not slot or not amt:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Correct Usage:**\n```\n.qr <slot> <amount>\n```\n{EMOJI_DOT} **Example:** `.qr slot1 500`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    try:
        with open("upi.json","r") as f: data = json.load(f)
    except: data = {}
    
    user_id = str(ctx.author.id)
    
    if user_id not in data or slot not in data[user_id]:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Slot Not Found\n\n{EMOJI_SHARE} The slot **`{slot}`** doesn't exist in your UPI slots.\n\n{EMOJI_DOT} Use `.setupi` to configure your UPI slots first.\n{EMOJI_DOT} Use `.upi <upi id> <amt>` to generate a qr without saving upi id.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    upi_id = data[user_id][slot]
    
    try:
        upi_uri = f"upi://pay?pa={upi_id}&pn=Recipient&am={amt}&tn=I have authorised this payment and received the product&cu=INR"
        qr = qrcode.QRCode(box_size=10,border=4)
        qr.add_data(upi_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="upi_qr.png")
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} UPI Payment QR Code\n\n**Payment Details**\n{EMOJI_DOT} **Amount:** ₹{amt}\n{EMOJI_DOT} **UPI Slot:** `{slot}`\n{EMOJI_DOT} **UPI ID:** `{upi_id}`\n\n{EMOJI_TICK} Scan the QR code below to complete the payment\n\n-# {EMOJI_SHARE} Make sure to scan carefully and verify the amount before paying",
            color=0x2ECC71
        )
        embed.set_footer(text=f"Made and managed by Swappy Exchange • Generated for {ctx.author.name}")
        embed.set_image(url="attachment://upi_qr.png")
        
        await asyncio.sleep(1)
        await ctx.send(file=file, embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} QR Generation Failed\n\n{EMOJI_SHARE} Failed to generate QR code\n\n**Error Details:**\n```\n{str(e)}\n```\n\n{EMOJI_DOT} Please try again or contact support if the issue persists.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await asyncio.sleep(1)
        await ctx.send(embed=embed)
        
@bot.command()
async def rm(ctx, user: discord.User = None):
    try:
        await ctx.message.delete()
    except:
        pass

    role_id = 1418550582960193616
    if not any(r.id == role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not allowed to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    if not user:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.rm <user>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    try:
        channel_link = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}"
        dm_embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Exchange Reminder\n\n{EMOJI_SHARE} You have an ongoing exchange ticket. Please respond in it.\n\n[**Go to Channel**]({channel_link})",
            color=0x2ECC71
        )
        dm_embed.set_footer(text="Made and managed by Swappy Exchange")
        await user.send(embed=dm_embed)

        await asyncio.sleep(1)
        confirm = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Successfully Sent\n\n{EMOJI_SHARE} Message sent to {user.mention}",
            color=0x2ECC71
        )
        confirm.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=confirm)

    except Exception as e:
        await asyncio.sleep(1)
        err = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Could not send DM to {user.mention}",
            color=0xE74C3C
        )
        err.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=err)
        
@bot.command()
async def timer(ctx, time: str = None):
    import re
    try: await ctx.message.delete()
    except: pass
    if not time:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.timer <time>` (e.g., 10s, 5m, 1h, 1d)",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    match = re.match(r"^(\d+)([smhd])$", time)
    if not match:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Format\n\n{EMOJI_SHARE} Please use `s`, `m`, `h`, or `d` for time units.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    value, unit = int(match.group(1)), match.group(2)
    seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    total_time = value * seconds
    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_SERVICES} Timer Started\n\n{EMOJI_SHARE} Timer set for **{time}**.",
        color=0x2ECC71
    )
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)
    await asyncio.sleep(total_time)
    done_embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_TICK} Timer Completed\n\n{EMOJI_SHARE} The timer has been completed.",
        color=0x2ECC71
    )
    done_embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(content=ctx.author.mention, embed=done_embed)
    
@bot.command()
async def done(ctx, user: discord.User = None, amt: str = None, crypto: str = None):
    role_id = 1418550582960193616
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not user or not amt or not crypto:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.done <user> <amount with ₹/$/ €/PKR> <crypto name>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    # Extract amount and currency symbol
    if amt.startswith('₹') or amt.startswith('$') or amt.startswith('€'):
        currency_symbol = amt[0]
        amt_value = amt[1:]
    elif amt.endswith('₹') or amt.endswith('$') or amt.endswith('€'):
        currency_symbol = amt[-1]
        amt_value = amt[:-1]
    elif 'PKR' in amt.upper():
        currency_symbol = 'PKR'
        amt_value = amt.upper().replace('PKR', '').strip()
    else:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Amount Format\n\n{EMOJI_SHARE} Amount must include ₹, $, €, or PKR symbol.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not amt_value.replace(".", "", 1).isdigit():
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Amount\n\n{EMOJI_SHARE} Amount must be a number.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not any(r.id == role_id for r in ctx.author.roles):
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    amt_float = float(amt_value)
    crypto_upper = crypto.upper()
    
    try:
        guild = ctx.guild
        
        # Get config for categories
        config = load_config()
        cat_inr_to_crypto = 1436393106600759346
        cat_crypto_to_inr = 1418551133890416671
        cat_pkr2c = config.get("pkr2c_category")
        cat_c2pkr = config.get("c2pkr_category")
        cat_paypal2c = config.get("paypal2c_category")
        cat_c2paypal = config.get("c2paypal_category")
        
        # Determine deal type
        if ctx.channel.category and ctx.channel.category.id == cat_inr_to_crypto:
            deal_type = "INR to Crypto"
        elif ctx.channel.category and ctx.channel.category.id == cat_crypto_to_inr:
            deal_type = "Crypto to INR"
        elif cat_pkr2c and ctx.channel.category and ctx.channel.category.id == cat_pkr2c:
            deal_type = "PKR to Crypto"
        elif cat_c2pkr and ctx.channel.category and ctx.channel.category.id == cat_c2pkr:
            deal_type = "Crypto to PKR"
        elif cat_paypal2c and ctx.channel.category and ctx.channel.category.id == cat_paypal2c:
            deal_type = "PayPal to Crypto"
        elif cat_c2paypal and ctx.channel.category and ctx.channel.category.id == cat_c2paypal:
            deal_type = "Crypto to PayPal"
        else:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Category\n\n{EMOJI_SHARE} This command can only be used in exchange categories.",
                color=0xFF0000
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            await ctx.send(embed=embed)
            return
        
        # Send confirmation embed with buttons
        confirm_embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Confirm Exchange\n\n{user.mention}, have you received the funds?\n\n**Exchange Details:**\n{EMOJI_DOT} Amount: {currency_symbol}{amt_float}\n{EMOJI_DOT} Crypto: {crypto_upper}\n{EMOJI_DOT} Deal Type: {deal_type}",
            color=0xFFA500
        )
        confirm_embed.set_footer(text="Made and managed by Swappy Exchange")
        
        view = DoneConfirmationView(ctx, user, amt_float, currency_symbol, crypto_upper, deal_type)
        message = await ctx.send(content=user.mention, embed=confirm_embed, view=view)
        view.message = message
        
    except Exception as e:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} {e}",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        print(f"Exception in done command: {e}")
        import traceback
        traceback.print_exc()

@bot.command()
async def tdone(ctx, user: discord.User = None, amt: str = None, crypto: str = None):
    role_id = 1418550582960193616
    cat_inr_to_crypto = 1419565434369216522
    cat_crypto_to_inr = 1443244934533746768
    log_channel_id = 1438999681580535920
    stats_file = "tstats.json"
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not user or not amt or not crypto:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.done <user> <amount with ₹/$> <crypto name>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    # Extract amount and currency symbol
    if amt.startswith('₹') or amt.startswith('$'):
        currency_symbol = amt[0]
        amt_value = amt[1:]
    elif amt.endswith('₹') or amt.endswith('$'):
        currency_symbol = amt[-1]
        amt_value = amt[:-1]
    else:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Amount Format\n\n{EMOJI_SHARE} Amount must include ₹ or $ symbol.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not amt_value.replace(".", "", 1).isdigit():
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Amount\n\n{EMOJI_SHARE} Amount must be a number.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not any(r.id == role_id for r in ctx.author.roles):
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    amt_float = float(amt_value)
    amt_int = int(amt_float)
    crypto_upper = crypto.upper()
    
    try:
        guild = ctx.guild
        log_channel = guild.get_channel(log_channel_id)
        
        if ctx.channel.category and ctx.channel.category.id == cat_inr_to_crypto:
            deal_type = "INR to Crypto"
        elif ctx.channel.category and ctx.channel.category.id == cat_crypto_to_inr:
            deal_type = "Crypto to INR"
        else:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Category\n\n{EMOJI_SHARE} This command can only be used in exchange categories.",
                color=0xFF0000
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            await ctx.send(embed=embed)
            return
        
        # ============ FIX: Use safe loading with file locking ============
        stats = load_stats_safe(stats_file)
        
        # Ensure all top-level keys exist
        for key in ["staff", "clients", "daily", "monthly", "yearly"]:
            if key not in stats:
                stats[key] = {}
        # ================================================================
        
        # Get current date
        now = datetime.datetime.now()
        day_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")
        year_key = str(now.year)
        
        staff_id = str(ctx.author.id)
        client_id = str(user.id)
        
        # Initialize staff stats if not exists
        if staff_id not in stats["staff"]:
            stats["staff"][staff_id] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0}
        else:
            if "total_amt_usd" not in stats["staff"][staff_id]:
                stats["staff"][staff_id]["total_amt_usd"] = 0
            if "total_amt_inr" not in stats["staff"][staff_id]:
                stats["staff"][staff_id]["total_amt_inr"] = 0
        
        # Initialize client stats if not exists
        if client_id not in stats["clients"]:
            stats["clients"][client_id] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0}
        else:
            if "total_amt_usd" not in stats["clients"][client_id]:
                stats["clients"][client_id]["total_amt_usd"] = 0
            if "total_amt_inr" not in stats["clients"][client_id]:
                stats["clients"][client_id]["total_amt_inr"] = 0
        
        # Initialize time-based stats
        if day_key not in stats["daily"]:
            stats["daily"][day_key] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0}
        else:
            if "total_amt_usd" not in stats["daily"][day_key]:
                stats["daily"][day_key]["total_amt_usd"] = 0
            if "total_amt_inr" not in stats["daily"][day_key]:
                stats["daily"][day_key]["total_amt_inr"] = 0
        
        if month_key not in stats["monthly"]:
            stats["monthly"][month_key] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0}
        else:
            if "total_amt_usd" not in stats["monthly"][month_key]:
                stats["monthly"][month_key]["total_amt_usd"] = 0
            if "total_amt_inr" not in stats["monthly"][month_key]:
                stats["monthly"][month_key]["total_amt_inr"] = 0
        
        if year_key not in stats["yearly"]:
            stats["yearly"][year_key] = {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0}
        else:
            if "total_amt_usd" not in stats["yearly"][year_key]:
                stats["yearly"][year_key]["total_amt_usd"] = 0
            if "total_amt_inr" not in stats["yearly"][year_key]:
                stats["yearly"][year_key]["total_amt_inr"] = 0
        
        # Update all stats based on currency
        stats["staff"][staff_id]["total_deals"] += 1
        stats["clients"][client_id]["total_deals"] += 1
        stats["daily"][day_key]["total_deals"] += 1
        stats["monthly"][month_key]["total_deals"] += 1
        stats["yearly"][year_key]["total_deals"] += 1
        
        if currency_symbol == '$':
            stats["staff"][staff_id]["total_amt_usd"] += amt_float
            stats["clients"][client_id]["total_amt_usd"] += amt_float
            stats["daily"][day_key]["total_amt_usd"] += amt_float
            stats["monthly"][month_key]["total_amt_usd"] += amt_float
            stats["yearly"][year_key]["total_amt_usd"] += amt_float
        else:  # ₹
            stats["staff"][staff_id]["total_amt_inr"] += amt_float
            stats["clients"][client_id]["total_amt_inr"] += amt_float
            stats["daily"][day_key]["total_amt_inr"] += amt_float
            stats["monthly"][month_key]["total_amt_inr"] += amt_float
            stats["yearly"][year_key]["total_amt_inr"] += amt_float
        
        # ============ FIX: Use safe saving with file locking ============
        success = save_stats_safe(stats_file, stats)
        if not success:
            print("WARNING: Failed to save stats!")
        # ================================================================
        
        # Log embed
        log_embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Exchange Done\n\n**Client**\n{EMOJI_DOT} {user.mention}\n\n**Exchanger**\n{EMOJI_DOT} {ctx.author.mention}\n\n**Deal**\n{EMOJI_DOT} {deal_type}\n\n**Amount**\n{EMOJI_DOT} {currency_symbol}{amt_int}\n\n**Crypto**\n{EMOJI_DOT} {crypto_upper}",
            color=0x2ECC71
        )
        log_embed.set_footer(text="Made and managed by Swappy Exchange")
        await log_channel.send(embed=log_embed)
        
        # Confirmation embed
        embed_confirm = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Exchange Logged\n\n{EMOJI_SHARE} The exchange has been recorded successfully.",
            color=0x2ECC71
        )
        embed_confirm.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed_confirm)
        
        # Send +rep message based on category with User ID (with decimal support)
        if ctx.channel.category.id == cat_inr_to_crypto:
            rep_message = f"+rep {ctx.author.id} UPI -> {crypto_upper} | {currency_symbol}{amt_float}"
        elif ctx.channel.category.id == cat_crypto_to_inr:
            rep_message = f"+rep {ctx.author.id} {crypto_upper} -> UPI | {currency_symbol}{amt_float}"
        
        await ctx.send(rep_message)
        
        # Rename channel to done-by-username
        try:
            new_channel_name = f"done-by-{ctx.author.name}"
            await ctx.channel.edit(name=new_channel_name)
        except:
            pass
        
        # Check if user should get cashback
        if should_get_cashback():
            cashback_code = generate_cashback_code()
            cashback_amount = generate_cashback_amount()
            
            try:
                cashback_embed = discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_SERVICES} Congratulations! Cashback Reward\n\n{EMOJI_TICK} You've received a **cashback reward** for your recent exchange!\n\n{EMOJI_SHARE} **Cashback Code:** `{cashback_code}`\n{EMOJI_SHARE} **Cashback Amount:** ₹{cashback_amount}\n\n-# {EMOJI_DOT} Click the button below to enter your UPI ID and claim your cashback",
                    color=0x2ECC71
                )
                cashback_embed.set_footer(text="Made and managed by Swappy Exchange")
                
                view = CashbackView(cashback_code, cashback_amount)
                await user.send(embed=cashback_embed, view=view)
            except:
                pass
        else:
            try:
                no_cashback_embed = discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_SERVICES} Cashback Reward\n\n{EMOJI_WARNING} **Better Luck Next Time!**\n\n{EMOJI_SHARE} You didn't receive a cashback this time, but don't worry!\n{EMOJI_SHARE} Keep exchanging for more chances to win cashback rewards.\n\n-# {EMOJI_DOT} Thank you for using Swappy Exchange!",
                    color=0xFFA500
                )
                no_cashback_embed.set_footer(text="Made and managed by Swappy Exchange")
                await user.send(embed=no_cashback_embed)
            except:
                pass
        
    except Exception as e:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} {e}",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        print(f"Exception in tdone command: {e}")
        import traceback
        traceback.print_exc()

@bot.command()
async def cashback(ctx):
    """Admin only command to view all cashback requests"""
    admin_role_id = 1427890290794172416
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not any(r.id == admin_role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    cashback_data = load_cashback()
    
    if not cashback_data:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Cashback Records\n\n{EMOJI_DOT} No cashback records found.",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_SERVICES} Cashback Records",
        color=0x2ECC71
    )
    
    for code, data in list(cashback_data.items())[:10]:
        status_emoji = "✅" if data["status"] == "sent" else "🟡"
        embed.add_field(
            name=f"{status_emoji} {code}",
            value=f"{EMOJI_DOT} **User:** <@{data['user_id']}>\n{EMOJI_DOT} **Amount:** ₹{data['amount']}\n{EMOJI_DOT} **UPI:** `{data['upi_id']}`\n{EMOJI_DOT} **Status:** {data['status'].title()}",
            inline=False
        )
    
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)

@bot.command(aliases=["p"])
async def profile(ctx, user: discord.User = None):
    stats_file = "stats.json"
    mm_stats_file = "mm_stats.json"
    
    try: 
        await ctx.message.delete()
    except: 
        pass
    
    await asyncio.sleep(1)
    
    if not user:
        user = ctx.author
    
    # ============ FIX: Use safe loading ============
    stats = load_stats_safe(stats_file)
    mm_stats = load_mm_stats_safe(mm_stats_file)
    # ==============================================
    
    uid = str(user.id)
    
    # Get stats with backward compatibility
    client_data = stats["clients"].get(uid, {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0})
    staff_data = stats["staff"].get(uid, {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0})
    mm_data = mm_stats["mm_staff"].get(uid, {"total_deals": 0, "total_amt": 0})
    
    # Ensure both currency fields exist
    client_usd = client_data.get("total_amt_usd", client_data.get("total_amt", 0))
    client_inr = client_data.get("total_amt_inr", 0)
    staff_usd = staff_data.get("total_amt_usd", staff_data.get("total_amt", 0))
    staff_inr = staff_data.get("total_amt_inr", 0)
    
    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_SERVICES} Profile - {user.name}\n\n**User ID**\n{EMOJI_DOT} {user.id}\n\n**Server Joined**\n{EMOJI_DOT} {user.joined_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n**Client Stats**\n{EMOJI_DOT} Total Deals: **{client_data['total_deals']}**\n{EMOJI_DOT} Total Exchanged (USD): **${client_usd:,.2f}**\n{EMOJI_DOT} Total Exchanged (INR): **₹{client_inr:,.2f}**\n\n**Staff Stats**\n{EMOJI_DOT} Total Deals: **{staff_data['total_deals']}**\n{EMOJI_DOT} Total Exchanged (USD): **${staff_usd:,.2f}**\n{EMOJI_DOT} Total Exchanged (INR): **₹{staff_inr:,.2f}**\n\n**MM Stats**\n{EMOJI_DOT} Total Deals: **{mm_data['total_deals']}**\n{EMOJI_DOT} Total Amount: **${mm_data['total_amt']:,.2f}**",
        color=0x2ECC71
    )
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)


@bot.command()
async def stats(ctx):
    stats_file = "stats.json"
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    await asyncio.sleep(1)
    
    stats = load_stats_safe(stats_file)
    
    now = datetime.datetime.now()
    day_key = now.strftime("%Y-%m-%d")
    month_key = now.strftime("%Y-%m")
    year_key = str(now.year)
    week_key = now.strftime("%Y-W%U")
    
    # Get stats or default to 0
    daily_data = stats.get("daily", {}).get(day_key, {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0, "total_amt_pkr": 0, "total_amt_eur": 0})
    weekly_data = stats.get("weekly", {}).get(week_key, {"total_deals": 0, "total_amt_usd": 0, "total_amt_inr": 0, "total_amt_pkr": 0, "total_amt_eur": 0})
    
    # Calculate monthly (current month only)
    monthly_deals = 0
    monthly_usd = 0
    monthly_inr = 0
    monthly_pkr = 0
    monthly_eur = 0
    
    for key, data in stats.get("daily", {}).items():
        if key.startswith(month_key):
            monthly_deals += data.get("total_deals", 0)
            monthly_usd += data.get("total_amt_usd", 0)
            monthly_inr += data.get("total_amt_inr", 0)
            monthly_pkr += data.get("total_amt_pkr", 0)
            monthly_eur += data.get("total_amt_eur", 0)
    
    # Calculate yearly (current year only)
    yearly_deals = 0
    yearly_usd = 0
    yearly_inr = 0
    yearly_pkr = 0
    yearly_eur = 0
    
    for key, data in stats.get("daily", {}).items():
        if key.startswith(year_key):
            yearly_deals += data.get("total_deals", 0)
            yearly_usd += data.get("total_amt_usd", 0)
            yearly_inr += data.get("total_amt_inr", 0)
            yearly_pkr += data.get("total_amt_pkr", 0)
            yearly_eur += data.get("total_amt_eur", 0)
    
    # Backward compatibility
    daily_usd = daily_data.get("total_amt_usd", daily_data.get("total_amt", 0))
    daily_inr = daily_data.get("total_amt_inr", 0)
    daily_pkr = daily_data.get("total_amt_pkr", 0)
    daily_eur = daily_data.get("total_amt_eur", 0)
    
    weekly_usd = weekly_data.get("total_amt_usd", weekly_data.get("total_amt", 0))
    weekly_inr = weekly_data.get("total_amt_inr", 0)
    weekly_pkr = weekly_data.get("total_amt_pkr", 0)
    weekly_eur = weekly_data.get("total_amt_eur", 0)
    
    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_SERVICES} Exchange Statistics\n\n"
                    f"**Daily Stats ({day_key})**\n"
                    f"{EMOJI_DOT} Total Deals: **{daily_data['total_deals']}**\n"
                    f"{EMOJI_DOT} USD: **${daily_usd:,.2f}**\n"
                    f"{EMOJI_DOT} INR: **₹{daily_inr:,.2f}**\n"
                    f"{EMOJI_DOT} PKR: **{daily_pkr:,.2f} PKR**\n"
                    f"{EMOJI_DOT} EUR: **€{daily_eur:,.2f}**\n\n"
                    f"**Weekly Stats (Week {week_key.split('-W')[1]})**\n"
                    f"{EMOJI_DOT} Total Deals: **{weekly_data['total_deals']}**\n"
                    f"{EMOJI_DOT} USD: **${weekly_usd:,.2f}**\n"
                    f"{EMOJI_DOT} INR: **₹{weekly_inr:,.2f}**\n"
                    f"{EMOJI_DOT} PKR: **{weekly_pkr:,.2f} PKR**\n"
                    f"{EMOJI_DOT} EUR: **€{weekly_eur:,.2f}**\n\n"
                    f"**Monthly Stats ({month_key})**\n"
                    f"{EMOJI_DOT} Total Deals: **{monthly_deals}**\n"
                    f"{EMOJI_DOT} USD: **${monthly_usd:,.2f}**\n"
                    f"{EMOJI_DOT} INR: **₹{monthly_inr:,.2f}**\n"
                    f"{EMOJI_DOT} PKR: **{monthly_pkr:,.2f} PKR**\n"
                    f"{EMOJI_DOT} EUR: **€{monthly_eur:,.2f}**\n\n"
                    f"**Yearly Stats ({year_key})**\n"
                    f"{EMOJI_DOT} Total Deals: **{yearly_deals}**\n"
                    f"{EMOJI_DOT} USD: **${yearly_usd:,.2f}**\n"
                    f"{EMOJI_DOT} INR: **₹{yearly_inr:,.2f}**\n"
                    f"{EMOJI_DOT} PKR: **{yearly_pkr:,.2f} PKR**\n"
                    f"{EMOJI_DOT} EUR: **€{yearly_eur:,.2f}**",
        color=0x2ECC71
    )
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)

@bot.command()
async def mmdone(ctx, user: discord.User = None, amount_crypto: str = None, crypto: str = None):
    role_id = 1418550582960193616
    mm_log_channel_id = 1438902559631872121
    mm_stats_file = "mm_stats.json"
    cat_inr_to_crypto = 1436393106600759346
    cat_crypto_to_inr = 1418551133890416671
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not user or not amount_crypto or not crypto:
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.mmdone <user> <amount> <crypto>`\n**Example:** `.mmdone @user $22.96 USDT`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not any(r.id == role_id for r in ctx.author.roles):
        await asyncio.sleep(1)
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    try:
        guild = ctx.guild
        log_channel = guild.get_channel(mm_log_channel_id)
        
        if not log_channel:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Configuration Error\n\n{EMOJI_SHARE} MM log channel not found. Please contact administrator.",
                color=0xFF0000
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            await ctx.send(embed=embed)
            return
        
        # Determine deal type based on category
        if ctx.channel.category and ctx.channel.category.id == cat_inr_to_crypto:
            deal_type = "UPI -> Crypto"
        elif ctx.channel.category and ctx.channel.category.id == cat_crypto_to_inr:
            deal_type = "Crypto -> UPI"
        else:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Category\n\n{EMOJI_SHARE} This command can only be used in exchange categories.",
                color=0xFF0000
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            await ctx.send(embed=embed)
            return
        
        crypto_upper = crypto.upper()
        
        # ============ FIX: Use safe loading ============
        mm_stats = load_mm_stats_safe(mm_stats_file)
        # ==============================================
        
        staff_id = str(ctx.author.id)
        client_id = str(user.id)
        
        # Initialize if not exists
        if staff_id not in mm_stats["mm_staff"]:
            mm_stats["mm_staff"][staff_id] = {"total_deals": 0, "total_amt": 0}
        
        if client_id not in mm_stats["mm_clients"]:
            mm_stats["mm_clients"][client_id] = {"total_deals": 0, "total_amt": 0}
        
        # Extract amount for stats (remove $ and ₹)
        amt_for_stats = float(amount_crypto.replace("$", "").replace("₹", ""))
        
        # Update stats
        mm_stats["mm_staff"][staff_id]["total_deals"] += 1
        mm_stats["mm_staff"][staff_id]["total_amt"] += amt_for_stats
        mm_stats["mm_clients"][client_id]["total_deals"] += 1
        mm_stats["mm_clients"][client_id]["total_amt"] += amt_for_stats
        
        # ============ FIX: Use safe saving ============
        success = save_mm_stats_safe(mm_stats_file, mm_stats)
        if not success:
            print("WARNING: Failed to save MM stats!")
        # =============================================
        
        # Log embed
        log_embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} MM Deal Done\n\n**Client**\n{EMOJI_DOT} {user.mention}\n\n**MM**\n{EMOJI_DOT} {ctx.author.mention}\n\n**Deal Type**\n{EMOJI_DOT} {deal_type}\n\n**Amount**\n{EMOJI_DOT} {amount_crypto} {crypto_upper}",
            color=0x2ECC71
        )
        log_embed.set_footer(text="Made and managed by Swappy Exchange")
        await log_channel.send(embed=log_embed)
        
        # Send rep message with crypto name
        rep_message = f"+rep {ctx.author.mention} Middleman Held [{amount_crypto} {crypto_upper}] | {deal_type}"
        await ctx.send(rep_message)
        
        # Confirmation embed
        embed_confirm = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} MM Deal Logged\n\n{EMOJI_SHARE} The MM deal has been recorded successfully.",
            color=0x2ECC71
        )
        embed_confirm.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed_confirm)
    
    except Exception as e:
        embed_error = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} An error occurred: {str(e)}",
            color=0xFF0000
        )
        embed_error.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed_error)
    
@bot.command()
async def tos(ctx):
    import discord, asyncio

    role_id = 1427890290794172416
    try:
        await ctx.message.delete()
    except:
        pass

    if not any(r.id == role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not allowed to use this command.",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        return

    tos_text = """
{HEADER}

## <:SW_services:1433835593640443954> **Staff Rules, Guidelines & Policy**

**General Conduct**

{EMOJI_DOT} You must remain professional at all times.
If a client behaves rudely or aggressively, do not argue — simply stay calm and tag your senior for assistance.
Always follow your senior's instructions; do not argue or disobey their orders.

{EMOJI_DOT} You are not allowed to use self-bots under any circumstances.

{EMOJI_DOT} Do not misuse or attempt to exploit any server bots.
If you discover any loophole or bug, report it to the admins instead of abusing it.

{EMOJI_DOT} If you are marked as a scammer in any known or reputed server, you will be immediately removed, and your security deposit will not be refunded.

{EMOJI_DOT} If your Discord account gets compromised or token-grabbed, the server team will not be responsible, and you will be removed from staff for security reasons.

{EMOJI_DOT} No external promotions are allowed — you cannot promote other servers or businesses in your status, bio, or any chat.

{EMOJI_DOT} You cannot make clients wait more than 10 minutes during a deal. Always respond promptly and professionally.
---
{HEADER}

## <:SW_tick:1433834224972206181> **Deal Rules**

{EMOJI_DOT} You cannot claim tickets beyond your assigned maximum limit.

{EMOJI_DOT} After every successful deal, you must ask the client to vouch in the vouch channel.

{EMOJI_DOT} If you are unable to handle a full deal due to your maximum limit, you must:
__Either use Parts (split the deal into sections), or use MM / AutoMM.__
{EMOJI_WARNING} ***When using Parts, you may not exceed 2 parts per deal.***

{EMOJI_DOT} You must always include "Swappy" or server-related content in your bio/status to show affiliation.

{EMOJI_DOT} Inside tickets, maintain professional behavior at all times.
***No toxicity, no childish behavior, and no unprofessional replies.***
---
{HEADER}

## <:SW_warning:1433832107079368875> **Security & Retirement Policy**

{EMOJI_DOT} Your maximum deal limit (max) will always be **half of your security deposit.**
__Example: If you submitted $100 as security, your max limit will be $50.__

{EMOJI_DOT} You can retire only after **30 days** from your hiring date.

{EMOJI_DOT} Your security deposit will be refunded within **3–5 days** after your retirement, provided you meet all the conditions.

{EMOJI_DOT} You must have completed at least **20 successful deals** before applying for resignation.

{EMOJI_DOT} Swappy does not charge any transaction fee during refunds.
You will receive the same amount you deposited. ***Stable coins are preferred for all transactions.***

{EMOJI_DOT} If you retire before 30 days, you will receive only **80%** of your security refund.

{EMOJI_DOT} If any report or dispute is opened against you, you will be restricted until the case is resolved.
{EMOJI_WARNING} ***If the report is proven valid, you will be suspended without refund.***

{EMOJI_DOT} If you are marked **DWC (Do Not Work With)**, you will be suspended until the mark is cleared.

{EMOJI_DOT} Your security cannot be decreased, but it can be increased anytime.

{EMOJI_DOT} You must keep both your **staff key** and **application transcript** safely.
__These are mandatory for your security refund. If you lose either, your refund will not be processed.__
---
{HEADER}

## <:SW_share:1433832650736668824> **Ticket Handling & Deal Rules**

{EMOJI_DOT} You may claim **2 tickets** at once, but the total amount of all claimed tickets must remain under your limit.

{EMOJI_DOT} limit not like if you paid $100 then $100 is your limit.

{EMOJI_DOT} if you paid $100 then limit is $50 must say under half limit of your max security deposit.

{EMOJI_DOT} You must never argue with clients in tickets. Stay professional and calm.

{EMOJI_DOT} You are not allowed to DM clients for deals. ***All deals must happen within the ticket*** to ensure proper logging.

{EMOJI_DOT} You cannot change rates inside a ticket — you must follow the **current official server rates.**

{EMOJI_DOT} Once you claim a ticket, you cannot go offline until the deal is complete.

{EMOJI_DOT} You cannot give your UPI or address before informing the client how much they will receive **(the total amount)**.

{EMOJI_DOT} You must not use or exploit any ticket claim loopholes.
__Always use the official claim button only.__

{EMOJI_DOT} You cannot force a client to pay the full amount if the deal was agreed in parts.

{EMOJI_DOT} After claiming a ticket, you cannot back out by saying you don't have enough funds.
You must complete the deal or escalate to a senior if a genuine issue arises.

{EMOJI_DOT} You cannot leave an ongoing deal unless there is a serious and valid reason.
{EMOJI_WARNING} ***If you must leave, inform a Senior Staff and get approval first.***

{EMOJI_DOT} Client information (numbers, IDs, chats, etc.) must stay **confidential.**
No leaking or sharing of client data outside the ticket is allowed.

{EMOJI_DOT} You must not spam or overuse mentions in tickets.
Mentions should be used rarely and only when necessary.
"""

    sections = tos_text.split("---")
    for section in sections:
        if section.strip() == "":
            continue
        embed = discord.Embed(
            description=section.strip()
                .replace("{HEADER}", HEADER)
                .replace("{EMOJI_DOT}", EMOJI_DOT)
                .replace("{EMOJI_WARNING}", EMOJI_WARNING)
                .replace("{EMOJI_SHARE}", EMOJI_SHARE)
                .replace("{EMOJI_TICK}", EMOJI_TICK),
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        await asyncio.sleep(1)
        
        
@bot.command()
async def help(ctx, query: str = None):
    try:
        await ctx.message.delete()
    except:
        pass

    # Dictionary containing Description and Usage for every command
    cmd_details = {
        # General / Utility
        "help": {"desc": "Shows this help message.", "usage": ".help [command]"},
        "profile": {"desc": "View user statistics and profile.", "usage": ".profile [@user]"},
        "stats": {"desc": "View server exchange statistics.", "usage": ".stats"},
        "tos": {"desc": "Displays Staff Rules, Guidelines & Policy.", "usage": ".tos"},
        "calc": {"desc": "Calculate a mathematical expression.", "usage": ".calc <expression>"},
        "timer": {"desc": "Set a timer.", "usage": ".timer <time> (e.g. 10m)"},
        
        # Calculators / Rates
        "i2c": {"desc": "Convert INR to Crypto value.", "usage": ".i2c <amount>"},
        "c2i": {"desc": "Convert Crypto value to INR.", "usage": ".c2i <amount>"},
        "bal": {"desc": "Check LTC address balance.", "usage": ".bal <address>"},
        
        # Payment / Wallets
        "upi": {"desc": "Generate a UPI QR code.", "usage": ".upi <upi_id> <amount>"},
        "setupi": {"desc": "Save UPI ID to a slot.", "usage": ".setupi <slot> <upi_id>"},
        "qr": {"desc": "Generate QR from saved slot.", "usage": ".qr <slot> <amount>"},
        "setaddy": {"desc": "Save a crypto address to a slot.", "usage": ".setaddy <slot> <address>"},
        "addy": {"desc": "List your saved crypto addresses.", "usage": ".addy"},
        
        # Ticket Management
        "claim": {"desc": "Claim a ticket (Exchanger only).", "usage": ".claim"},
        "unclaim": {"desc": "Unclaim a ticket.", "usage": ".unclaim"},
        "close": {"desc": "Close the ticket and generate transcript.", "usage": ".close"},
        "add": {"desc": "Add a user to the ticket.", "usage": ".add <@user>"},
        "remove": {"desc": "Remove a user from the ticket.", "usage": ".remove <@user>"},
        
        # Staff / Exchanger
        "done": {"desc": "Log a completed exchange.", "usage": ".done <@user> <amount> <crypto>"},
        "tdone": {"desc": "Log a completed exchange (Alt).", "usage": ".tdone <@user> <amount> <crypto>"},
        "mmdone": {"desc": "Log a Middleman deal.", "usage": ".mmdone <@user> <amount> <crypto>"},
        "rm": {"desc": "Send a DM reminder to user.", "usage": ".rm <@user>"},
        
        # Admin / Config
        "panel": {"desc": "Send the Exchange Panel.", "usage": ".panel"},
        "exchanger": {"desc": "Set exchanger limits.", "usage": ".exchanger <@user> <limit_usd>"},
        "cashback": {"desc": "View cashback requests.", "usage": ".cashback"},
        "setconfig": {"desc": "Configure bot settings.", "usage": ".setconfig <type> <cat/role> <id>"},
        "viewconfig": {"desc": "View current bot configuration.", "usage": ".viewconfig"}
    }

    # If specific command queried
    if query:
        query = query.lower()
        if query in cmd_details:
            data = cmd_details[query]
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} **Command Help: {query}**\n\n"
                            f"{EMOJI_DOT} **Description:** {data['desc']}\n"
                            f"{EMOJI_DOT} **Usage:** `{data['usage']}`",
                color=0x2ECC71
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} **Not Found**\n\n"
                            f"{EMOJI_SHARE} Command `{query}` does not exist.",
                color=0xFF0000
            )
            embed.set_footer(text="Made and managed by Swappy Exchange")
            await ctx.send(embed=embed)
        return

    # Main Help Embed (Categorized)
    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_SERVICES} **Swappy Exchange Commands**\n"
                    f"{EMOJI_SHARE} Use `.help <command>` for specific details.",
        color=0x2ECC71
    )

    # Helper function to join commands for display
    def get_cmds(list_keys):
        return ", ".join([f"`{c}`" for c in list_keys])

    # Defining categories
    categories = [
        ("👤 User & Utility", ["profile", "stats", "calc", "tos", "timer"]),
        ("💰 Calculators & Rates", ["i2c", "c2i", "bal"]),
        ("💳 Payments & Addresses", ["upi", "setupi", "qr", "setaddy", "addy"]),
        ("🎫 Ticket Management", ["claim", "unclaim", "close", "add", "remove"]),
        ("🛡️ Staff & Exchanger", ["done", "tdone", "mmdone", "rm"]),
        ("⚙️ Admin & Config", ["panel", "exchanger", "cashback", "setconfig", "viewconfig"])
    ]

    for name, cmds in categories:
        embed.add_field(
            name=f"{EMOJI_DOT} **{name}**",
            value=f"{EMOJI_SHARE} {get_cmds(cmds)}",
            inline=False
        )

    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)

    query = query.lower()
    if query in commands_list:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Help - {query}\n\n{EMOJI_SHARE} {commands_list[query]}",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_WARNING} Help\n\n{EMOJI_SHARE} No command or category found with `{query}`.",
        color=0xFF0000
    )
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)
    
@bot.command()
async def setaddy(ctx, slot: int = None, *, address: str = None):
    try:
        await ctx.message.delete()
    except:
        pass
    await asyncio.sleep(1)

    if slot is None or address is None:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.setaddy <slot> <address>`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    file = "addresses.json"
    if os.path.exists(file):
        with open(file, "r") as f:
            data = json.load(f)
    else:
        data = {}

    uid = str(ctx.author.id)
    if uid not in data:
        data[uid] = {}

    data[uid][str(slot)] = address

    with open(file, "w") as f:
        json.dump(data, f, indent=4)

    embed = discord.Embed(
        description=f"## {HEADER}\n{EMOJI_TICK} Address Saved\n\n{EMOJI_SHARE} **Slot:** {slot}\n{EMOJI_SHARE} **Address:** `{address}`",
        color=0x2ECC71
    )
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)
    
@bot.command()
async def addy(ctx):

    try:
        await ctx.message.delete()
    except:
        pass
    await asyncio.sleep(1)

    file = "addresses.json"
    if not os.path.exists(file):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} No Addresses\n\n{EMOJI_SHARE} No addresses saved.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    with open(file, "r") as f:
        data = json.load(f)

    uid = str(ctx.author.id)
    if uid not in data or not data[uid]:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} No Addresses\n\n{EMOJI_SHARE} You have no saved addresses.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return

    description = f"## {HEADER}\n{EMOJI_SERVICES} Your Saved Addresses\n\n"
    for slot, address in data[uid].items():
        description += f"{EMOJI_DOT} **Slot {slot}:** `{address}`\n"
    
    embed = discord.Embed(description=description, color=0x2ECC71)
    embed.set_footer(text="Made and managed by Swappy Exchange")

    view = View(timeout=None)

    for slot, address in data[uid].items():
        async def send_addr(interaction, addr=address):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        description=f"## {HEADER}\n{EMOJI_WARNING} Access Denied\n\n{EMOJI_SHARE} You can't access this.",
                        color=0xFF0000
                    ),
                    ephemeral=True
                )
                return
            await interaction.response.send_message(addr)

        btn = Button(label=f"Slot {slot}", style=discord.ButtonStyle.green)
        btn.callback = send_addr
        view.add_item(btn)

    await ctx.send(embed=embed, view=view)
    
class BalanceView(discord.ui.View):
    def __init__(self, address, confirmed, unconfirmed, usd_value):
        super().__init__(timeout=None)
        self.address = address
        self.confirmed = confirmed
        self.unconfirmed = unconfirmed
        self.usd_value = usd_value
        self.show_usd = False

    @discord.ui.button(label="Toggle USD/LTC", style=discord.ButtonStyle.grey)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.show_usd = not self.show_usd
        if self.show_usd:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} LTC Balance (in USD)\n\n{EMOJI_SHARE} **Address:** `{self.address}`\n\n{EMOJI_DOT} **Confirmed:** ${self.usd_value['confirmed']:.2f}\n{EMOJI_DOT} **Unconfirmed:** ${self.usd_value['unconfirmed']:.2f}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} LTC Balance\n\n{EMOJI_SHARE} **Address:** `{self.address}`\n\n{EMOJI_DOT} **Confirmed:** {self.confirmed:.8f} LTC\n{EMOJI_DOT} **Unconfirmed:** {self.unconfirmed:.8f} LTC",
                color=discord.Color.blurple()
            )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await interaction.response.edit_message(embed=embed, view=self)

@bot.command(aliases=["balance"])
async def bal(ctx, address: str):
    try:
        await ctx.message.delete()
    except:
        pass
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd") as resp:
            price_data = await resp.json()
            ltc_usd = price_data["litecoin"]["usd"]
        async with session.get(f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance") as resp:
            if resp.status != 200:
                embed = discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Invalid LTC address or error fetching data.",
                    color=0xFF0000
                )
                embed.set_footer(text="Made and managed by Swappy Exchange")
                return await ctx.send(embed=embed)
            data = await resp.json()
        confirmed = data.get("balance", 0) / 1e8
        unconfirmed = data.get("unconfirmed_balance", 0) / 1e8
        usd_value = {"confirmed": confirmed * ltc_usd, "unconfirmed": unconfirmed * ltc_usd}
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} LTC Balance\n\n{EMOJI_SHARE} **Address:** `{address}`\n\n{EMOJI_DOT} **Confirmed:** {confirmed:.8f} LTC\n{EMOJI_DOT} **Unconfirmed:** {unconfirmed:.8f} LTC",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed, view=BalanceView(address, confirmed, unconfirmed, usd_value))

@bot.command()
async def i2c(ctx, *, amount: str):
    try:
        await ctx.message.delete()
    except:
        pass
    
    try:
        if "$" in amount:
            amt = float(amount.replace("$", "").strip()) * I2C
            crypto_amt = float(amount.replace("$", "").strip())
        else:
            amt = float(amount.strip())
            crypto_amt = amt / I2C
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} INR → Crypto\n\n{EMOJI_DOT} **INR:** ₹{amt:.2f}\n{EMOJI_DOT} **Crypto:** ${crypto_amt:.2f}",
            color=discord.Color.random()
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
    except:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Format\n\n{EMOJI_SHARE} Example: `.i2c 100` or `.i2c $10`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)

@bot.command()
async def c2i(ctx, *, amount: str):
    try:
        await ctx.message.delete()
    except:
        pass
    
    try:
        if "$" in amount:
            crypto_amt = float(amount.replace("$", "").strip())
            inr_amt = crypto_amt * C2I
        else:
            inr_amt = float(amount.strip())
            crypto_amt = inr_amt / C2I
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Crypto → INR\n\n{EMOJI_DOT} **Crypto:** ${crypto_amt:.2f}\n{EMOJI_DOT} **INR:** ₹{inr_amt:.2f}",
            color=discord.Color.random()
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
    except:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Format\n\n{EMOJI_SHARE} Example: `.c2i 100` or `.c2i $10`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)

@bot.command()
async def setconfig(ctx, exchange_type: str = None, setting_type: str = None, value: str = None):
    """
    Setup configuration for exchange system
    Usage: .setconfig <exchange_type> <category/role> <id>
    Example: .setconfig i2c category 123456789
    Example: .setconfig i2c role 987654321
    """
    admin_role_id = 1427890290794172416
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not any(r.id == admin_role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if not exchange_type or not setting_type or not value:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Usage Error\n\n{EMOJI_SHARE} **Usage:** `.setconfig <type> <category/role> <id>`\n\n**Exchange Types:**\n{EMOJI_DOT} i2c, c2i, pkr2c, c2pkr, paypal2c, c2paypal, c2c\n\n**Examples:**\n{EMOJI_DOT} `.setconfig i2c category 123456789`\n{EMOJI_DOT} `.setconfig i2c role 987654321`",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    valid_types = ["i2c", "c2i", "pkr2c", "c2pkr", "paypal2c", "c2paypal", "c2c"]
    if exchange_type.lower() not in valid_types:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Type\n\n{EMOJI_SHARE} Valid types: {', '.join(valid_types)}",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    if setting_type.lower() not in ["category", "role"]:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid Setting\n\n{EMOJI_SHARE} Use 'category' or 'role'",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    try:
        value_id = int(value)
        config = load_config()
        
        key = f"{exchange_type.lower()}_{setting_type.lower()}"
        config[key] = value_id
        save_config(config)
        
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Configuration Updated\n\n{EMOJI_DOT} **Type:** {exchange_type.upper()}\n{EMOJI_DOT} **Setting:** {setting_type.title()}\n{EMOJI_DOT} **Value:** {value_id}",
            color=0x2ECC71
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        
    except ValueError:
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Invalid ID\n\n{EMOJI_SHARE} Please provide a valid numeric ID",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)

@bot.command()
async def viewconfig(ctx):
    """View current configuration"""
    admin_role_id = 1427890290794172416
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not any(r.id == admin_role_id for r in ctx.author.roles):
        embed = discord.Embed(
            description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} You are not authorized to use this command.",
            color=0xFF0000
        )
        embed.set_footer(text="Made and managed by Swappy Exchange")
        await ctx.send(embed=embed)
        return
    
    config = load_config()
    
    description = f"## {HEADER}\n{EMOJI_SERVICES} Current Configuration\n\n"
    
    for key, value in config.items():
        if value:
            description += f"{EMOJI_DOT} **{key}:** {value}\n"
        else:
            description += f"{EMOJI_DOT} **{key}:** Not Set\n"
    
    embed = discord.Embed(description=description, color=0x2ECC71)
    embed.set_footer(text="Made and managed by Swappy Exchange")
    await ctx.send(embed=embed)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        
        if custom_id.startswith("claim_"):
            await handle_claim_button(interaction)
        elif custom_id.startswith("close_"):
            await handle_close_button(interaction)
        elif custom_id.startswith("unclaim_"):
            await handle_unclaim_button(interaction)

async def handle_claim_button(interaction: discord.Interaction):
    # Defer first to prevent timeout
    try:
        await interaction.response.defer()
    except:
        return
    
    channel_id = str(interaction.channel.id)
    tickets = load_tickets()
    exchangers = load_exchangers()
    user_id = str(interaction.user.id)
    
    # Find ticket
    ticket_data = None
    prefix = None
    for pref, data in tickets.items():
        if "active" in data and channel_id in data["active"]:
            ticket_data = data["active"][channel_id]
            prefix = pref
            break
    
    if not ticket_data:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Ticket data not found.",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    if ticket_data.get("claimed"):
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Already Claimed\n\n{EMOJI_SHARE} This ticket has already been claimed.",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    # Check if user is an exchanger
    if user_id not in exchangers:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Not Authorized\n\n{EMOJI_SHARE} You are not registered as an exchanger.",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    # Check limit
    exchanger_data = exchangers[user_id]
    amount = ticket_data["amount"]
    currency = ticket_data["currency"]
    
    if currency == "USD":
        limit_key = "limit_usd"
    elif currency == "INR":
        limit_key = "limit_inr"
    elif currency == "PKR":
        limit_key = "limit_pkr"
    else:
        limit_key = "limit_usd"
    
    if amount > exchanger_data[limit_key]:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Limit Exceeded\n\n{EMOJI_SHARE} Amount exceeds your limit\n{EMOJI_DOT} Your Limit: {exchanger_data[limit_key]:.2f} {currency}\n{EMOJI_DOT} Ticket Amount: {amount:.2f} {currency}",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    # Claim ticket
    ticket_data["claimed"] = True
    ticket_data["claimer"] = interaction.user.id
    save_tickets(tickets)
    
    # Update channel name
    new_name = f"claimed-by-{interaction.user.name}"
    await interaction.channel.edit(name=new_name)
    
    # Update permissions
    config = load_config()
    role_key = f"{prefix}_role"
    role_id = config.get(role_key)
    
    overwrites = interaction.channel.overwrites
    if role_id:
        role = interaction.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=False)
    
    overwrites[interaction.user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    creator = interaction.guild.get_member(ticket_data["creator"])
    if creator:
        overwrites[creator] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    await interaction.channel.edit(overwrites=overwrites)
    
    # Send claimed message
    await interaction.followup.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Ticket Claimed\n\n{EMOJI_SHARE} Ticket claimed by {interaction.user.mention}",
            color=0x2ECC71
        )
    )
    
    # Send tutorial embed
    tutorial_embed = discord.Embed(
        description=f"## __ Important — Tutorial:__\n- The **exchange request** shall be handled by the **Exchanger**, we have either collected a security deposit from them or they have claimed using their bypass. You must now send them the ticket amount to their details, afterwards click the **Sent Payment button** immediately. You may **Remove Exchanger** for any reason you please.\n\n- __**Do not send any higher than the ticket amount.**__\n   - Do not deal outside of a claimed ticket.\n   - Make sure to read the terms provided below.\n   - Be sure to ping any online staff for guidance/support.\n   - Do not press any buttons without reading the description.",
        color=15839539
    )
    tutorial_embed.set_author(
        name="Swappy Exchanges",
        icon_url="https://media.discordapp.net/attachments/1439987229882847292/1447310321373941863/b32620c149c2ba37886f44ffcdf6459f_1.webp?ex=69372846&is=6935d6c6&hm=056a61be50d6e0ced3558796aa1b63bfc67e4a5b02b84e9adba6354ff7db4076&=&format=webp"
    )
    tutorial_embed.set_thumbnail(url="https://media.discordapp.net/attachments/1439987229882847292/1447310321373941863/b32620c149c2ba37886f44ffcdf6459f_1.webp?ex=69372846&is=6935d6c6&hm=056a61be50d6e0ced3558796aa1b63bfc67e4a5b02b84e9adba6354ff7db4076&=&format=webp")
    
    await interaction.channel.send(embed=tutorial_embed)

async def handle_unclaim_button(interaction: discord.Interaction):
    # Defer first
    try:
        await interaction.response.defer()
    except:
        return
    
    channel_id = str(interaction.channel.id)
    tickets = load_tickets()
    
    # Find ticket
    ticket_data = None
    prefix = None
    for pref, data in tickets.items():
        if "active" in data and channel_id in data["active"]:
            ticket_data = data["active"][channel_id]
            prefix = pref
            break
    
    if not ticket_data:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Ticket data not found.",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    if not ticket_data.get("claimed"):
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Not Claimed\n\n{EMOJI_SHARE} This ticket is not claimed yet.",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    # Unclaim ticket
    ticket_data["claimed"] = False
    ticket_data["claimer"] = None
    save_tickets(tickets)
    
    # Restore channel name
    ticket_num = ticket_data["number"]
    new_name = f"{prefix}-{ticket_num}"
    await interaction.channel.edit(name=new_name)
    
    # Restore permissions
    config = load_config()
    role_key = f"{prefix}_role"
    role_id = config.get(role_key)
    
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }
    
    creator = interaction.guild.get_member(ticket_data["creator"])
    if creator:
        overwrites[creator] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    if role_id:
        role = interaction.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
    
    await interaction.channel.edit(overwrites=overwrites)
    
    await interaction.followup.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_TICK} Ticket Unclaimed\n\n{EMOJI_SHARE} Ticket has been unclaimed successfully.",
            color=0x2ECC71
        )
    )

async def handle_close_button(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
    except:
        return
    
    channel_id = str(interaction.channel.id)
    tickets = load_tickets()
    
    # Find ticket
    ticket_data = None
    prefix = None
    for pref, data in tickets.items():
        if "active" in data and channel_id in data["active"]:
            ticket_data = data["active"][channel_id]
            prefix = pref
            break
    
    if not ticket_data:
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Error\n\n{EMOJI_SHARE} Ticket data not found.",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    # Check permissions
    if interaction.user.id != ticket_data["creator"] and interaction.user.id != ticket_data.get("claimer"):
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"## {HEADER}\n{EMOJI_WARNING} Permission Denied\n\n{EMOJI_SHARE} Only ticket creator or claimer can close the ticket.",
                color=0xFF0000
            ),
            ephemeral=True
        )
        return
    
    # Generate transcript
    await interaction.followup.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Generating Transcript\n\n{EMOJI_SHARE} Please wait...",
            color=0x2ECC71
        )
    )
    
    transcript = await chat_exporter.export(interaction.channel)
    
    if transcript is None:
        transcript_file = None
    else:
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.html"
        )
    
    # Send DM to creator
    creator = interaction.guild.get_member(ticket_data["creator"])
    if creator:
        try:
            creator_embed = discord.Embed(
                description=f"## {HEADER}\n{EMOJI_SERVICES} Ticket Closed\n\n{EMOJI_SHARE} Your ticket **{interaction.channel.name}** has been closed.\n\n**Ticket Details:**\n{EMOJI_DOT} Exchange Type: {ticket_data['exchange_type']}\n{EMOJI_DOT} Amount: {ticket_data['amount']} {ticket_data['currency']}\n{EMOJI_DOT} Crypto: {ticket_data['crypto']}",
                color=0x2ECC71
            )
            creator_embed.set_footer(text="Made and managed by Swappy Exchange")
            
            if transcript_file:
                await creator.send(embed=creator_embed, file=transcript_file)
                transcript_file = discord.File(
                    io.BytesIO(transcript.encode()),
                    filename=f"transcript-{interaction.channel.name}.html"
                )
            else:
                await creator.send(embed=creator_embed)
        except:
            pass
    
    # Send DM to claimer
    claimer_id = ticket_data.get("claimer")
    if claimer_id:
        claimer = interaction.guild.get_member(claimer_id)
        if claimer:
            try:
                claimer_embed = discord.Embed(
                    description=f"## {HEADER}\n{EMOJI_SERVICES} Ticket Closed\n\n{EMOJI_SHARE} Ticket **{interaction.channel.name}** has been closed.\n\n**Ticket Details:**\n{EMOJI_DOT} Exchange Type: {ticket_data['exchange_type']}\n{EMOJI_DOT} Amount: {ticket_data['amount']} {ticket_data['currency']}\n{EMOJI_DOT} Crypto: {ticket_data['crypto']}",
                    color=0x2ECC71
                )
                claimer_embed.set_footer(text="Made and managed by Swappy Exchange")
                
                if transcript_file:
                    await claimer.send(embed=claimer_embed, file=transcript_file)
                else:
                    await claimer.send(embed=claimer_embed)
            except:
                pass
    
    # Remove from tickets
    del tickets[prefix]["active"][channel_id]
    save_tickets(tickets)
    
    await interaction.channel.send(
        embed=discord.Embed(
            description=f"## {HEADER}\n{EMOJI_SERVICES} Closing Ticket\n\n{EMOJI_SHARE} This ticket will be deleted in 5 seconds...",
            color=0x2ECC71
        )
    )
    
    await asyncio.sleep(5)
    await interaction.channel.delete()

bot.run("DISCORD_BOT_TOKEN_REPLACED_FOR_SECURITY")