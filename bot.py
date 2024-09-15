import os
import discord
from openai import AzureOpenAI
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv(override=True)

openai = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# Set up Discord bot
TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize conversation history
conversation_history = {}


async def get_recent_messages(channel, limit=15):
    messages = []
    async for message in channel.history(limit=limit):
        messages.append({"author": message.author.name, "content": message.content})
    return list(reversed(messages))  # Reverse to get chronological order


async def should_respond(message):
    # Prepare conversation history for the LLM
    history = await get_recent_messages(message.channel)
    prompt = f"You are in a Discord Group Chat. Here's the recent conversation:\n\n"

    for entry in history[-5:]:  # Consider last 5 messages for context
        prompt += f"{entry['author']}: {entry['content']}\n"

    prompt += f"\nBased on this conversation, should you respond to the last message? Answer with 'Yes' or 'No' and a brief explanation."

    print(prompt)
    # Query the LLM
    response = openai.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    decision = response.choices[0].message.content.strip().lower()
    print(decision)
    return decision.startswith("yes")


async def generate_response(message):
    history = await get_recent_messages(message.channel)
    prompt = f"You are in a Discord Group Chat. Here's the recent conversation:\n\n"

    for entry in history[-5:]:  # Consider last 5 messages for context
        prompt += f"{entry['author']}: {entry['content']}\n"

    prompt += f"\nGenerate a response to the last message."

    response = openai.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = str(message.channel.id)

    # Update conversation history
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []

    conversation_history[channel_id].append(
        {"author": message.author.name, "content": message.content}
    )

    # Decide whether to respond
    if await should_respond(message):
        response = await generate_response(message)
        await message.channel.send(response)

    # Limit conversation history to last 50 messages
    conversation_history[channel_id] = conversation_history[channel_id][-50:]

    await bot.process_commands(message)


# Run the bot
bot.run(TOKEN)
