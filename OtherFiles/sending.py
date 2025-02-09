from twilio.rest import Client

# Twilio Credentials
ACCOUNT_SID = "xxx"
AUTH_TOKEN = "xxx"

# Initialize Twilio Client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Send a WhatsApp message
message = client.messages.create(
    from_="whatsapp:+14155238886",  # Twilio Sandbox Number
    to="whatsapp:+917908706657",  # User's WhatsApp Number
    body="Hello Samrat"
)

# Print message SID
print(f"Message sent with SID: {message.sid}")
