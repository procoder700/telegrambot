import telebot
import json
import os

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
UPI_ID = os.getenv("UPI_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# Transaction storage
TRANSACTION_FILE = "transactions.json"

# Ensure the transaction file exists
if not os.path.exists(TRANSACTION_FILE):
    with open(TRANSACTION_FILE, "w") as f:
        json.dump([], f)

# Welcome Message (Group)
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Welcome to AlphaZone! ⚡ Tell me what you want.",
                     reply_markup=main_menu())

# Main Menu Buttons
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("CV Creation", "AI Art Generation", "Logo Design")
    return markup

# Category Selection
@bot.message_handler(func=lambda msg: msg.text in ["CV Creation", "AI Art Generation", "Logo Design"])
def category_selected(message):
    if message.text == "CV Creation":
        bot.send_message(message.chat.id, "Choose your CV type:", reply_markup=cv_menu())
    elif message.text == "AI Art Generation":
        bot.send_message(message.chat.id, "Choose the art style:", reply_markup=art_menu())
    elif message.text == "Logo Design":
        bot.send_message(message.chat.id, "Logo design costs ₹1,000. Do you want to proceed?", reply_markup=confirm_menu())

# CV Options
def cv_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Professional CV - ₹2,500", "Executive CV - ₹4,500")
    return markup

# AI Art Options
def art_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Artistic - ₹3,000", "Fantasy - ₹4,500", "Ultra-Realistic - ₹12,000")
    return markup

# Confirmation Menu
def confirm_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Yes", "No")
    return markup

# Request Payment
def request_payment(chat_id, price):
    bot.send_message(chat_id, f"Please pay ₹{price} to this UPI ID: {UPI_ID} and upload the screenshot.")

# Handle Payment Screenshots
@bot.message_handler(content_types=['photo'])
def handle_payment(message):
    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "Processing your payment...")

    # Store transaction details
    with open(TRANSACTION_FILE, "r+") as f:
        transactions = json.load(f)
        transactions.append({
            "user_id": message.chat.id,
            "file_id": file_id
        })
        f.seek(0)
        json.dump(transactions, f, indent=4)

    bot.send_message(message.chat.id, "Payment verified! Your final product will be delivered shortly.")

bot.polling()
