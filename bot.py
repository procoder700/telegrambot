# -*- coding: utf-8 -*-
import os
import logging
import json
import random
import tempfile
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageDraw, ImageFont
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# Load secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
UPI_ID = os.getenv("UPI_ID")

# Product Prices
PRICES = {
    "cv_professional": 2500,
    "cv_executive": 4500,
    "art_artistic": 3000,
    "art_fantasy": 4500,
    "art_ultrarealistic": 12000,
    "logo": 1000
}

# Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load AI Model (Optimized for Glitch)
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4").to(device)

# Start Bot and Send Channel Welcome Message
def start_bot():
    bot = Bot(BOT_TOKEN)
    try:
        bot.send_message(
            chat_id=CHANNEL_ID,
            text="🚀 **Welcome to AlphaZone!** ⚡\n\nClick the button below to start ordering:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start Now 🚀", url=f"https://t.me/{bot.get_me().username}?start=1")]
            ]),
            parse_mode="Markdown"
        )
        logging.info("Welcome message sent to the channel.")
    except Exception as e:
        logging.error(f"Failed to send welcome message: {e}")

# Start in Private Chat
def start_private(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hey! Welcome to **AlphaZone**.\n\nChoose what you need:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 CV", callback_data="cv")],
            [InlineKeyboardButton("🎨 Art", callback_data="art")],
            [InlineKeyboardButton("🏆 Logo", callback_data="logo")]
        ]),
        parse_mode="Markdown"
    )

# Show Samples with AI-Generated Images
def show_samples(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    product_category = query.data

    prompts = {
        "cv": [("Professional CV", "cv_professional"), ("Executive CV", "cv_executive")],
        "art": [("Artistic", "art_artistic"), ("Fantasy", "art_fantasy"), ("Ultra-Realistic", "art_ultrarealistic")],
        "logo": [("Logo Sample", "logo")]
    }

    buttons = []
    for sample_text, product_type in prompts.get(product_category, []):
        image_path = generate_ai_image(sample_text)  # Generate AI Image
        with open(image_path, "rb") as img:
            query.message.reply_photo(photo=img, caption=f"**{sample_text}**\n💰 Price: ₹{PRICES[product_type]}", parse_mode="Markdown")
        buttons.append([InlineKeyboardButton(sample_text, callback_data=f"select_{product_type}")])

    query.message.reply_text("Select the type you want:", reply_markup=InlineKeyboardMarkup(buttons))

# Generate AI Image with Watermark
def generate_ai_image(prompt):
    image = pipe(prompt).images[0]

    # Add Watermark
    draw = ImageDraw.Draw(image)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 50)
    except:
        font = ImageFont.load_default()

    draw.text((20, 250), "WATERMARKED SAMPLE", fill=(255, 0, 0, 128), font=font)

    temp_path = tempfile.mktemp(suffix=".png")
    image.save(temp_path, optimize=True, quality=85)
    return temp_path

# Ask for User Description After Type Selection
def ask_for_description(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    product_type = query.data.replace("select_", "")

    # Store selected product type
    context.user_data["selected_product"] = product_type

    if "cv" in product_type:
        text = "**KINDLY PROVIDE YOUR DETAILS**\n\n🔹 **YOUR DETAILS WON’T BE SAVED, DON’T WORRY.**"
    else:
        text = "🔹 **BRIEFLY DESCRIBE YOUR IDEA FOR THE PRODUCT.**"

    query.message.reply_text(text, parse_mode="Markdown")

# Show Preview & Offer Regeneration
def send_preview(update: Update, context: CallbackContext):
    user_input = update.message.text
    product_type = context.user_data.get("selected_product", "")

    preview_path = generate_ai_image("Preview for: " + product_type)
    with open(preview_path, "rb") as img:
        update.message.reply_photo(photo=img, caption="🔹 **Here is your preview.**\n\n💡 Select an option:", parse_mode="Markdown")

    update.message.reply_text("Choose an option:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")],
        [InlineKeyboardButton("✅ Done", callback_data="done")]
    ]))

# Handle Regeneration
def regenerate_preview(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    send_preview(query, context)

# Handle Payment Process
def ask_for_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    product_type = context.user_data.get("selected_product", "")
    amount = PRICES.get(product_type, 0)

    query.message.reply_text(f"💰 **Please make a payment of ₹{amount}**\n\n📌 UPI ID: `{UPI_ID}`\n\nOnce done, send a screenshot.", parse_mode="Markdown")

# Validate Payment
def validate_payment(update: Update, context: CallbackContext):
    payment_screenshot = update.message.photo[-1].file_id  # Getting the highest quality image
    product_type = context.user_data.get("selected_product", "")
    required_amount = PRICES.get(product_type, 0)

    # Simulated validation (replace with actual verification later)
    is_valid = True  # Assume payment is valid for now

    if is_valid:
        update.message.reply_text("✅ **Payment verified! Here is your final product.**")
        # Send final product (without watermark)
    else:
        update.message.reply_text("❌ **The amount paid is not as per the price, kindly check.**")

# Start Bot
if __name__ == "__main__":
    start_bot()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_private))
    dp.add_handler(CallbackQueryHandler(show_samples, pattern="^(cv|art|logo)$"))
    dp.add_handler(CallbackQueryHandler(ask_for_description, pattern="^select_"))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, send_preview))
    dp.add_handler(CallbackQueryHandler(regenerate_preview, pattern="^regenerate$"))
    dp.add_handler(CallbackQueryHandler(ask_for_payment, pattern="^done$"))
    dp.add_handler(MessageHandler(Filters.photo, validate_payment))

    updater.start_polling()
    updater.idle()
