import telethon
import asyncio
import dotenv
import os
import datetime
import json

dotenv.load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

with open("config.json", "r") as f:
    config = json.load(f)

CHANNEL = config["CHANNEL"]
DAYS = config["DAYS"]


def parse_quote(text) -> str | None:
    if not text or "©" not in text:
        return None
    quote = text.split("©")[0].strip()
    return quote


def parse_author(text) -> str | None:
    if not text or "©" not in text:
        return None
    author = text.split("©")[1].strip().split(" ")[0]
    return author or None


def count_reactions(message: telethon.tl.types.Message) -> int:
    if not message.reactions or not message.reactions.results:
        return 0
    return sum(reaction.count for reaction in message.reactions.results)


async def collect_messages(client: telethon.TelegramClient) -> list:
    messages = []
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=DAYS)

    async for message in client.iter_messages(CHANNEL, offset_date=now):
        if message.date < cutoff:
            break
        if message.text is None:
            continue
        if "©" not in message.text: # отсеиваем не цитаты
            continue
        messages.append(message)

    return messages


def build_report_json(messages: list) -> dict:
    quotes = []
    author_reaction_count = {}

    for message in messages:
        author = parse_author(message.text)
        if not author:
            continue

        quote = parse_quote(message.text)
        if not quote:
            continue

        reactions = count_reactions(message)
        
        quotes.append({
            "quote": quote,
            "author": author,
            "reactions": reactions,
        })
        author_reaction_count[author] = author_reaction_count.get(author, 0) + reactions

    all_quotes = [{"quote": q["quote"], "author": q["author"], "reactions": q["reactions"]} for q in quotes]


    top_quotes_sorted = sorted(quotes, key=lambda x: x["reactions"], reverse=True)
    top_quotes = [
        {"quote": q["quote"], "reaction_count": q["reactions"]}
        for q in top_quotes_sorted[0:3]
    ]


    top_authors_sorted = sorted(author_reaction_count.items(), key=lambda x: x[1], reverse=True)
    top_authors = [
        {"author": author, "reaction_count": count}
        for author, count in top_authors_sorted[0:5]
    ]

    top_quote = None
    if top_quotes_sorted:
        best = top_quotes_sorted[0]
        top_quote = {
            "quote": best["quote"],
            "author": best["author"],
            "reaction_count": best["reactions"],
        }

    return {
        "quotes": all_quotes,
        "top_authors": top_authors,
        "top_quotes": top_quotes,
        "top_quote": top_quote,
        "summary": {
            "total_quotes": len(quotes),
            "total_authors": len(author_reaction_count),
            "total_reactions": sum(q["reactions"] for q in quotes),
        },
    }


def save_report(report: dict) -> None:
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/report_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)


async def main():
    client = telethon.TelegramClient("session", API_ID, API_HASH)
    await client.start()
    try:
        messages = await collect_messages(client)
        report = build_report_json(messages)
        save_report(report)
        print("Done")
    finally:
        await client.disconnect()



asyncio.run(main())
