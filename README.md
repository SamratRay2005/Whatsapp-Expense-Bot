# WhatsApp Expense Bot

WhatsApp Expense Bot is a chatbot built with [Rasa](https://rasa.com/) that lets you add, categorize, and query your expenses directly from WhatsApp. The bot uses Rasa's NLU and dialogue management capabilities alongside custom actions written with the Rasa SDK. It leverages pre-trained language models (via Hugging Face Transformers) for tasks such as zero-shot classification and Named Entity Recognition (NER) to automatically categorize expenses. All expense data is stored in an SQLite database.

## Features

- **Expense Entry:** Users can send natural language messages to record expenses.
- **Automated Categorization:** Expenses are categorized (e.g., coffee, food, travel) using a combination of rule-based overrides, NER, and zero-shot classification.
- **Expense Queries:** Users can ask questions like “How much have I spent on coffee?” and receive a summary of expenses.
- **Secure Credential Management:** Sensitive details (e.g., API keys) are managed via environment variables.
- **Built on Rasa:** Leverages Rasa’s NLU and dialogue management to create a robust conversational agent.

## How to Run

To run the bot, open **three separate terminals** and execute the following commands:

**Terminal 1:** Start the Rasa server with API enabled, CORS configured, and debugging information:

```bash
rasa run --enable-api --cors "*" --debug
rasa run actions
ngrok http 5005
