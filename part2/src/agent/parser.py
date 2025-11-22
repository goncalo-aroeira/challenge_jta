import os
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- Pydantic Models for Structured Output ---

class SearchConstraints(BaseModel):
    min_age: Optional[int] = Field(None, description="Minimum age for the product")
    max_age: Optional[int] = Field(None, description="Maximum age for the product")
    store: Optional[Literal["Store A", "Store B", "Store C"]] = Field(None, description="Specific store preference")
    category: Optional[str] = Field(None, description="Product category (e.g. Games, Console)")
    franchise: Optional[str] = Field(None, description="Game franchise (e.g. Mario, Zelda)")
    exclude_franchise: Optional[str] = Field(None, description="Franchise to exclude")

class UserIntent(BaseModel):
    intent_type: Literal["search_product", "recommendation", "unrelated", "greeting"] = Field(..., description="The type of user intent")
    query_summary: str = Field(..., description="A summary of what the user wants")
    constraints: Optional[SearchConstraints] = Field(None, description="Constraints extracted from the query")
    mentioned_products: List[str] = Field(default_factory=list, description="Specific products mentioned in the query")

# --- Parser Class ---

class IntentParser:
    """
    Analyzes the user's query to extract intent, constraints, and preferences.
    """
    def __init__(self, llm_client: Optional[OpenAI] = None):
        self.client = llm_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def parse(self, query: str) -> UserIntent:
        """
        Uses OpenAI Structured Outputs to parse the user query.
        """
        system_prompt = """You are an intent parser for a Nintendo Switch store recommendation system.
        Analyze the user's query and extract structured information.
        
        - If the user asks for a pizza or something unrelated to Nintendo/Gaming, classify as 'unrelated'.
        - If the user says 'Hi' or 'Hello', classify as 'greeting'.
        - If the user asks for a specific game or recommendations, classify as 'search_product' or 'recommendation'.
        - Extract constraints like age, store, and franchises.
        """

        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",  # Or gpt-4o, depending on availability/cost
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                response_format=UserIntent,
            )
            return completion.choices[0].message.parsed
        except Exception as e:
            print(f"Error parsing intent: {e}")
            # Fallback for error cases
            return UserIntent(intent_type="unrelated", query_summary="Error parsing query")

