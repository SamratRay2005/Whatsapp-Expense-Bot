# WhatsApp Expense Bot

WhatsApp Expense Bot is a chatbot built with [Rasa](https://rasa.com/) that lets you add, categorize, and query your expenses directly from WhatsApp. The bot leverages Rasa's NLU and dialogue management capabilities along with custom actions written with the Rasa SDK. Pre-trained language models (via Hugging Face Transformers) are used for tasks like zero-shot classification and Named Entity Recognition (NER) to automatically categorize expenses. All expense data is stored in an SQLite database.

## Features

- **Expense Entry:** Record expenses by sending natural language messages.
- **Automated Categorization:** Automatically categorize expenses (e.g., coffee, food, travel) using rule-based overrides, NER, and zero-shot classification.
- **Expense Queries:** Ask questions like “How much have I spent on coffee?” and get an expense summary.
- **Secure Credential Management:** Sensitive details (e.g., API keys) are securely managed via environment variables.
- **Built on Rasa:** Utilizes Rasa’s robust NLU and dialogue management framework.

## How to Run

To run the bot, open **three separate terminals** and execute the following commands:

### Terminal 1
~~~bash
rasa run --enable-api --cors "*" --debug
~~~

### Terminal 2
~~~bash
rasa run actions
~~~

### Terminal 3
~~~bash
ngrok http 5005
~~~

## Configuring Twilio

1. **Copy the ngrok URL:**  
   After running `ngrok`, copy the HTTPS link displayed in the terminal.

2. **Update Twilio Sandbox Settings:**  
   In Twilio, navigate to the **Messaging** section and go to **Send a WhatsApp message** → **Sandbox Settings**.  
   In the webhook field, append `/webhooks/twilio/webhook` to your ngrok URL.

   For example, if your ngrok URL is:
   ~~~arduino
   https://abc123.ngrok.io
   ~~~

   then set the webhook URL to:
   ~~~bash
   https://abc123.ngrok.io/webhooks/twilio/webhook
   ~~~

3. **Update `credentials.yml`:**  
   Edit your `credentials.yml` file to include your Twilio credentials:
   ~~~yaml
   twilio:
     account_sid: ${TWILIO_ACCOUNT_SID}
     auth_token: ${TWILIO_AUTH_TOKEN}
     twilio_number: ${TWILIO_NUMBER}
   ~~~

   Replace the environment variables with your actual Twilio details or set these values in your environment.

Happy chatting and expense tracking!
