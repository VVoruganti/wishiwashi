from dotenv import load_dotenv
import os
from openai import AzureOpenAI

load_dotenv(override=True)

import asyncio

openai = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

messages = []


def convo():
    global messages
    completion = openai.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=messages,
    )
    return completion.choices[0].message.content


async def chat():
    global messages
    while True:
        user_input = input(">>> ")
        if user_input == "exit":
            return

        messages.append({"role": "user", "content": user_input})
        output = convo()
        messages.append({"role": "assistant", "content": output})
        print(output)


if __name__ == "__main__":
    asyncio.run(chat())
