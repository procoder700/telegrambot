import telebot
import json
import os
import random
from datetime import datetime
from image_gen import text2im  # AI-powered image generation

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

# Store user data temporarily (deleted after payment)
user_data = {}

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
    user_data[message.chat.id] = {"category": message.text}
    
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

# Sample Generation (AI-powered)
def generate_sample(category, sub_type):
    prompt = f"{category} {sub_type} sample with watermark"
    image = text2im({"prompt": prompt, "size": "512x512", "n": 1})
    return image["image"]

# Handle Selection
@bot.message_handler(func=lambda msg: msg.text in ["Professional CV - ₹2,500", "Executive CV - ₹4,500",
                                                   "Artistic - ₹3,000", "Fantasy - ₹4,500", "Ultra-Realistic - ₹12,000"])
def handle_selection(message):
    chat_id = message.chat.id
    user_data[chat_id]["sub_type"] = message.text
    category = user_data[chat_id]["category"]
    sub_type = message.text.split(" - ")[0]
    
    # Generate AI-powered sample with watermark
    sample = generate_sample(category, sub_type)
    bot.send_photo(chat_id, sample, caption=f"Here is your {sub_type} sample with watermark.\nPrice: {message.text}")

    bot.send_message(chat_id, "Do you want to proceed or regenerate?", reply_markup=preview_menu())

# Preview Options
def preview_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Regenerate", "Done")
    return markup

# Handle Regeneration
@bot.message_handler(func=lambda msg: msg.text == "Regenerate")
def regenerate_sample(message):
    chat_id = message.chat.id
    category = user_data[chat_id]["category"]
    sub_type = user_data[chat_id]["sub_type"].split(" - ")[0]

    # Generate a new AI-powered sample
    sample = generate_sample(category, sub_type)
    bot.send_photo(chat_id, sample, caption=f"Here is your new {sub_type} sample with watermark.\nPrice: {user_data[chat_id]['sub_type']}")

# Handle Payment Request
@bot.message_handler(func=lambda msg: msg.text == "Done")
def request_payment(message):
    chat_id = message.chat.id
    price = user_data[chat_id]["sub_type"].split(" - ₹")[1]
    bot.send_message(chat_id, f"Please pay ₹{price} to this UPI ID: {UPI_ID} and upload the screenshot.")

# Handle Payment Screenshots
@bot.message_handler(content_types=['photo'])
def handle_payment(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    
    bot.send_message(chat_id, "Processing your payment...")

    # Store transaction details
    transaction = {
        "user_id": chat_id,
        "amount": user_data[chat_id]["sub_type"].split(" - ₹")[1],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "screenshot_id": file_id,
        "transaction_id": message.caption if message.caption else "Unknown"
    }

    with open(TRANSACTION_FILE, "r+") as f:
        transactions = json.load(f)
        transactions.append(transaction)
        f.seek(0)
        json.dump(transactions, f, indent=4)

    # Generate final AI-powered product (without watermark)
    category = user_data[chat_id]["category"]
    sub_type = user_data[chat_id]["sub_type"].split(" - ")[0]
    final_product = generate_sample(category, sub_type)  # No watermark this time

    bot.send_photo(chat_id, final_product, caption="✅ Payment verified! Here is your final product.")

    # Delete user details after product delivery
    del user_data[chat_id]

bot.polling()
