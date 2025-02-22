import replicate
import os

class ReplicateService:
    def __init__(self):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

    def get_financial_insight(self, stock_data: dict) -> str:
        try:
            # Format the input data for the model
            input_data = self.format_data(stock_data)

            output = self.client.run(
                "meta/meta-llama-3-8b-instruct",
                input={
                    "prompt": input_data
                }
            )
            return output
        except Exception as e:
            return f"Error generating insight: {str(e)}"
        
    def format_data(self, stock_data: dict) -> str:
        # Format the stock data into a prompt for the model
        return "Hello! Please briefly explain yourself."