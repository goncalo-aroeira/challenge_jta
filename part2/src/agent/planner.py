from typing import List, Dict, Any
from src.recsys.tools import search_products
from .parser import UserIntent

class Planner:
    """
    Decides which tools to call and in what order based on the parsed intent.
    """
    def __init__(self):
        pass

    def plan(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Executes tools based on the intent and returns the results.
        """
        results = {}
        
        if intent.intent_type == "unrelated":
            return {"error": "unrelated", "message": "I can only help with Nintendo Switch products."}
        
        if intent.intent_type == "greeting":
            return {"message": "Hello! How can I help you with Nintendo Switch games today?"}

        if intent.intent_type in ["search_product", "recommendation"]:
            # Extract constraints
            c = intent.constraints
            
            # Call search_products tool
            products = search_products(
                store=c.store if c else None,
                max_age=c.max_age if c else None,
                exclude_franchise=c.exclude_franchise if c else None,
                segment=c.category if c and c.category in ["Games", "Console", "Accessories"] else "Games",
                limit=5
            )
            
            results["products"] = products
            
            # TODO: If we had more tools (like get_product_details, find_similar), we would chain them here.
            # For now, we just return the search results.
            
        return results

