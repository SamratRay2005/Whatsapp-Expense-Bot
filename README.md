# WhatsApp Expense Bot

WhatsApp Expense Bot is a Rasa-based chatbot application that lets you add, categorize, and query your expenses directly from WhatsApp. It leverages pre-trained language models (using Hugging Face Transformers) for expense categorization via zero-shot classification and Named Entity Recognition (NER), and stores expense data in an SQLite database.

## Features

- **Expense Entry:** Add expenses using natural language messages.
- **Automated Categorization:** Expenses are automatically categorized (e.g., coffee, food, travel) using a combination of overrides, NER, and zero-shot classification.
- **Expense Queries:** Retrieve summaries of your spending by category (e.g., "How much have I spent on coffee?").
- **Secure Credential Management:** Uses environment variables to securely store sensitive credentials.
- **Modular and Extendable:** Easily extend the functionality or integrate with other messaging platforms.

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/SamratRay2005/Whatsapp-Expense-Bot.git
   cd Whatsapp-Expense-Bot
