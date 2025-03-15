def format_large_number(number):
        '''Format large numbers into a readable format with B, M suffixes.'''
        if number is None:
            return 'Unknown'
        
        try:
            if number >= 1_000_000_000:
                return f'${number / 1_000_000_000:.2f}B'
            elif number >= 1_000_000:
                return f'${number / 1_000_000:.2f}M'
            else:
                return f'${number:,.2f}'
        except (TypeError, ValueError):
            return f'${number}'