import re

vol: float = 0.0
fees: float = 0.0
pnl: float = 0.0

with open('paper_trading.log', 'rb') as f:
    for line in f:
        try:
            line_str = line.decode('utf-8', errors='ignore')
            
            # Volume matching: Fill {size} @ {price}
            m_vol = re.search(r'Fill ([\d\.]+) @ ([\d\.]+)', line_str)
            if m_vol:
                vol += float(m_vol.group(1)) * float(m_vol.group(2))
                
            # Fee matching: Fee: ${fee}
            m_fee = re.search(r'Fee: \$([\d\.]+)', line_str)
            if m_fee:
                fees += float(m_fee.group(1))
                
            # Market Closed PNL matching: PNL: ${pnl}
            if 'Market Closed' in line_str:
                m_pnl = re.search(r'PNL: \$([\-\d\.]+)', line_str)
                if m_pnl:
                    pnl += float(m_pnl.group(1))
                    
        except Exception as e:
            pass

print(f"Total Traded Volume: ${vol:,.2f}")
print(f"Total Fees Paid (Market Close): ${fees:,.2f}")
print(f"Total Net P&L from Stale Closes: ${pnl:,.2f}")
