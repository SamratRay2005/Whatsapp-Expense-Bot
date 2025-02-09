from typing import Any, Text, Dict, List
import sqlite3
import datetime
import re
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# Import the Hugging Face pipelines for zero-shot classification and NER.
from transformers import pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Candidate labels for expense categories.
# (We include both "coffee" and "food" among other categories.)
CANDIDATE_LABELS = ["online_food", "travel", "groceries", "coffee", "food", "others"]

# Initialize the zero-shot classification model once.
try:
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    logger.info("Zero-shot classification model loaded successfully.")
except Exception as e:
    logger.error("Failed to load zero-shot classification model: %s", e)
    classifier = None  # Fallback to None (handle as needed)

# Initialize the NER pipeline once.
try:
    ner_pipeline = pipeline("ner", grouped_entities=True)
    logger.info("NER pipeline loaded successfully.")
except Exception as e:
    logger.error("Failed to load NER pipeline: %s", e)
    ner_pipeline = None

DATABASE = 'expenses.db'

def init_db() -> None:
    """
    Initialize the SQLite database and create the 'expenses' table if it doesn't exist.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            create_table_query = """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    amount REAL,
                    category TEXT,
                    date TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """
            c.execute(create_table_query)
            conn.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error("Error initializing database: %s", e)

# Initialize the database when the actions server starts.
init_db()

def get_expense_category(message: str) -> List[str]:
    """
    Determine the expense categories using a combination of special overrides,
    NER-based mapping, and zero-shot classification.

    Overrides:
      - If the message contains a chai-related term (e.g. "chai") without also containing
        an explicit coffee-related term, classify it as ["food"].
      - If the message mentions dining terms (like "dinner", "restaurant", "lunch", or "breakfast")
        without any coffee-specific keywords, classify it as ["food"].
      - If the message contains coffee-specific terms (e.g. "coffee", "cappuccino", "filter coffee",
        "cold coffee"), classify it as ["coffee", "food"].

    Args:
        message: The expense description message.

    Returns:
        A list of category strings for the expense.
    """
    lowered = message.lower()

    # --- Special override for chai ---
    if "chai" in lowered and "coffee" not in lowered:
        logger.info("Override: detected chai-related term without coffee, classifying as 'food'")
        return ["food"]

    # --- Special override for dining ---
    if (("dinner" in lowered or "restaurant" in lowered or "lunch" in lowered or "breakfast" in lowered)
            and ("coffee" not in lowered and "cappuccino" not in lowered and "filter coffee" not in lowered and "cold coffee" not in lowered)):
        logger.info("Override: detected dining-related term without coffee, classifying as 'food'")
        return ["food"]

    # --- Special override for coffee ---
    if "coffee" in lowered or "cappuccino" in lowered or "filter coffee" in lowered or "cold coffee" in lowered:
        logger.info("Override: detected coffee-related terms in message, classifying as both 'coffee' and 'food'")
        return ["coffee", "food"]

    # --- Step 1: Attempt NER-based mapping ---
    if ner_pipeline:
        try:
            entities = ner_pipeline(message)
            for ent in entities:
                token = ent.get("word", "").lower()
                if token in ["starbucks", "cappuccino", "cold coffee"]:
                    logger.info("NER mapping: token '%s' mapped to 'coffee'", token)
                    return ["coffee", "food"]
                if token in ["ola", "uber", "train"]:
                    logger.info("NER mapping: token '%s' mapped to 'travel'", token)
                    return ["travel"]
                if token in ["swiggy", "blinkit"]:
                    logger.info("NER mapping: token '%s' mapped to 'online_food'", token)
                    return ["online_food"]
                # Add more mappings as needed.
        except Exception as e:
            logger.error("NER error: %s", e)
    
    # --- Step 2: Fallback to zero-shot classification ---
    if classifier:
        try:
            result = classifier(message, candidate_labels=CANDIDATE_LABELS)
            top_label = result["labels"][0]
            # If the top label is either "coffee" or "food", check for a chai override.
            if top_label in ["coffee", "food"]:
                if "chai" in lowered and "coffee" not in lowered:
                    logger.info("Zero-shot override: detected chai-related term, classifying as 'food'")
                    return ["food"]
                logger.info("Zero-shot classification: top label '%s' triggers both 'coffee' and 'food'", top_label)
                return ["coffee", "food"]
            else:
                logger.info("Zero-shot classification: top label '%s'", top_label)
                return [top_label]
        except Exception as e:
            logger.error("Zero-shot classification error: %s", e)
    
    # Default fallback if both methods fail.
    return ["others"]

class ActionAddExpense(Action):
    def name(self) -> Text:
        return "action_add_expense"
    
    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logger.info("ActionAddExpense called.")
        message = tracker.latest_message.get('text', '')
        amount = None

        # First, attempt to extract the amount from Rasa entities.
        for ent in tracker.latest_message.get('entities', []):
            if ent.get('entity') == 'amount':
                try:
                    amount = float(ent.get('value'))
                    logger.info("Amount extracted from entity: %s", amount)
                    break  # Use the first valid amount found.
                except Exception as e:
                    logger.error("Error extracting amount from entity: %s", e)
                    amount = None
        
        # Fallback: use a regex to extract the first number from the message.
        if amount is None:
            pattern = r"[₹$]?(\d+(?:\.\d{1,2})?)"
            match = re.search(pattern, message)
            if match:
                try:
                    amount = float(match.group(1))
                    logger.info("Amount extracted via regex: %s", amount)
                except Exception as e:
                    logger.error("Regex extraction error: %s", e)
                    amount = None

        if amount is None:
            dispatcher.utter_message(text="I could not detect an expense amount. Please include an amount.")
            return []

        # Determine the expense categories (this now returns a list).
        categories = get_expense_category(message)
        # Store as a comma-separated string.
        category_str = ", ".join(categories)

        # Use today's date as the default (ISO format).
        date_str = datetime.date.today().isoformat()

        # Insert the expense into the database.
        try:
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                insert_query = "INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)"
                c.execute(insert_query, (message, amount, category_str, date_str))
                conn.commit()
                logger.info("Expense recorded: '%s', Amount: %s, Categories: '%s', Date: %s",
                            message, amount, category_str, date_str)
        except Exception as e:
            dispatcher.utter_message(text="There was an error recording your expense.")
            logger.error("SQLite Error during insertion: %s", e)
            return []
        
        dispatcher.utter_message(text="Your expense has been recorded.")
        return []

class ActionQueryExpense(Action):
    def name(self) -> Text:
        return "action_query_expense"
    
    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        query_text = tracker.latest_message.get('text', '').lower()
        category = None
        date_filter = None

        # Check for a date filter ("yesterday").
        if "yesterday" in query_text:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date_filter = yesterday.isoformat()
            logger.info("Date filter applied: %s", date_filter)
        
        # For query categorization we use simple keyword matching.
        # For example, a query for "coffee" should return only those expenses that include "coffee" in their category.
        if "coffee" in query_text:
            category = "coffee"
        elif any(word in query_text for word in ["online", "swiggy", "blinkit"]):
            category = "online_food"
        elif any(word in query_text for word in ["grocery", "groceries", "zepto", "bigbasket"]):
            category = "groceries"
        elif any(word in query_text for word in ["travel", "ola", "uber", "train"]):
            category = "travel"
        elif "food" in query_text:
            category = "food"
        logger.info("Query category determined: %s", category)

        # Build the SQL query based on provided filters.
        try:
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                base_query = "SELECT description, amount, date, category FROM expenses"
                params: List[Any] = []
                conditions: List[str] = []
                
                if category is not None:
                    # Use a LIKE query so that if the stored category is "coffee, food"
                    # it will match when the user queries for "coffee" (and only those with coffee will be returned).
                    conditions.append("category LIKE ?")
                    params.append(f"%{category}%")
                if date_filter is not None:
                    conditions.append("date = ?")
                    params.append(date_filter)
                
                if conditions:
                    query = f"{base_query} WHERE " + " AND ".join(conditions)
                else:
                    query = base_query

                logger.info("Executing query: %s with params %s", query, params)
                c.execute(query, tuple(params))
                rows = c.fetchall()
        except Exception as e:
            dispatcher.utter_message(text="There was an error retrieving your expenses.")
            logger.error("SQLite Error during query: %s", e)
            return []
        
        # Build the response message.
        if rows:
            total = sum(row[1] for row in rows)
            response = ""
            if category and not date_filter:
                if category == "online_food":
                    response += f"Your total spending on online food orders is ₹{total}:\n"
                elif category == "coffee":
                    response += f"Your total expenditure on coffee/food is ₹{total}:\n"
                elif category == "travel":
                    response += f"Your total travel expenditure is ₹{total}:\n"
                elif category == "groceries":
                    response += f"Your total grocery expenditure is ₹{total}:\n"
                elif category == "food":
                    response += f"Your total food expenditure is ₹{total}:\n"
                else:
                    response += f"Your total expenditure on {category} is ₹{total}:\n"
            elif date_filter and not category:
                response += f"Here are your expenses from {date_filter}:\n"
            elif date_filter and category:
                response += f"Here are your {category} expenses from {date_filter}:\n"
            else:
                response += f"Your total expenses so far are ₹{total}:\n"
            
            for desc, amt, exp_date, exp_category in rows:
                response += f"- \"{desc}\": ₹{amt} on {exp_date} (Categories: {exp_category})\n"
        else:
            response = "No expenses found for the given criteria."
        
        dispatcher.utter_message(text=response)
        return []
