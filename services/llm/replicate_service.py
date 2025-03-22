import os
import replicate
from typing import Tuple, Dict, Any
from services.llm.prompts.prompt_stock_analysis import StockAnalysisPrompt

class ReplicateService:
    def __init__(self):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

    def get_financial_insight(self, stock_data: Dict) -> Tuple[str, str]:
        try:
            # Format the input data for the model
            input_data = self.format_input(stock_data)

            prediction = self.client.predictions.create(
                'meta/meta-llama-3-70b-instruct',
                input={
                    'prompt': input_data,
                    'temperature': 0.75,
                    'max_length': 2048,
                    'top_p': 0.9
                }
            )

            prediction.wait()

            if prediction.status == 'failed':
                return f'Error generating insight: {prediction.error}', 'error_id'
            
            prediction_id = prediction.id
            output = prediction.output

            # For streaming output, combine all output
            if isinstance(output, list):
                full_output = ''.join(output)
            else:
                full_output = str(output)

            return full_output, prediction_id
        except Exception as e:
            return f'Error generating insight: {str(e)}'
        
    def format_input(self, stock_data: Dict) -> str:
        '''Format stock data into a prompt for the LLM to analyze.'''
        if 'error' in stock_data:
            return f'Error retrieving stock data: {stock_data["error"]}'
        
        # Extract and format data
        formatted_data = StockAnalysisPrompt.format_data(stock_data)
        
        # Build prompt with formatted data
        prompt = StockAnalysisPrompt.build_prompt(formatted_data)
        
        return prompt
