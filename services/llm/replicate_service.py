import os
import replicate
from services.llm.prompts.prompt_stock_analysis import StockAnalysisPrompt

class ReplicateService:
    def __init__(self):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

    def get_financial_insight(self, stock_data: dict) -> str:
        try:
            # Format the input data for the model
            input_data = self.format_input(stock_data)

            output_stream = self.client.run(
                "meta/meta-llama-3-70b-instruct",
                input={
                    "prompt": input_data,
                    "temperature": 0.75,
                    "max_length": 2048,
                    "top_p": 0.9
                }
            )

            # Combine all outputs from the stream
            full_output = ""
            for item in output_stream:
                full_output += item
            return full_output
        except Exception as e:
            return f"Error generating insight: {str(e)}"
        
    def format_input(self, stock_data: dict) -> str:
        """Format stock data into a prompt for the LLM to analyze."""
        if 'error' in stock_data:
            return f"Error retrieving stock data: {stock_data['error']}"
        
        # Extract and format data
        formatted_data = StockAnalysisPrompt.format_data(stock_data)
        
        # Build prompt with formatted data
        prompt = StockAnalysisPrompt.build_prompt(formatted_data)
        
        return prompt
