import os
from openai import OpenAI
from .parser import IntentParser
from .planner import Planner
from .prompts import SYSTEM_PROMPT

class Agent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.parser = IntentParser(llm_client=self.client)
        self.planner = Planner()

    def run(self, query: str) -> str:
        """
        Main agent loop:
        1. Parse query
        2. Plan execution & Execute tools
        3. Generate final response
        """
        print(f"--- Processing query: {query} ---")
        
        # 1. Parse
        intent = self.parser.parse(query)
        print(f"Parsed Intent: {intent.intent_type}")
        if intent.constraints:
            print(f"Constraints: {intent.constraints}")

        # 2. Plan & Execute
        # In this simplified version, the planner executes the tools directly and returns data.
        execution_results = self.planner.plan(intent)
        
        # 3. Generate Final Answer
        response = self._generate_response(query, intent, execution_results)
        return response

    def _generate_response(self, query: str, intent, results: dict) -> str:
        """
        Generates a natural language response using the LLM and the tool results.
        """
        
        # Handle quick exits
        if "error" in results and results["error"] == "unrelated":
            return results["message"]
        
        if intent.intent_type == "greeting":
            return results.get("message", "Hello!")

        # Prepare context for the LLM
        products_found = results.get("products", [])
        
        context_str = f"User Query: {query}\n\n"
        context_str += f"Intent: {intent.intent_type}\n"
        context_str += f"Constraints: {intent.constraints}\n\n"
        
        if products_found:
            context_str += "Found Products:\n"
            for p in products_found:
                context_str += f"- {p['name']} (Age: {p['min_age']}+, Score: {p['popularity_global']:.2f})\n"
                context_str += f"  Description: {p['text_blob']}\n"
        else:
            context_str += "No specific products found matching the criteria.\n"

        # Call LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Here is the context of the search:\n{context_str}\n\nPlease provide a helpful recommendation to the user."}
        ]

        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        return completion.choices[0].message.content

