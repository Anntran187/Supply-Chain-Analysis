# Supply Chain Demand & Inventory Analysis

## Overview
An exploratory analysis of a beauty e-commerce supply chain dataset (100 SKUs across skincare, haircare, and cosmetics categories), focused on identifying replenishment risk, revenue performance, and supplier quality signals.

## Objectives
- Identify SKUs where stock cover falls below supplier lead time (stockout risk)
- Compare revenue performance across product categories
- Surface supplier quality issues via defect rate analysis
- Support data-driven prioritization of replenishment actions

## Key Findings
- **81% of SKUs** have stock cover below their lead time — indicating systemic under-stocking relative to replenishment cycles
- **Skincare** generates the highest revenue ($241K) but also has the highest stockout risk rate (92.5%)
- **Haircare** shows the widest gap between stock cover and lead time, suggesting forecasting misalignment
- Defect rates show no strong correlation with revenue/unit — supplier quality is not being priced in

## Dashboard Preview
![Supply Chain Dashboard](supply_chain_dashboard.png)

## Tools Used
- Python (Pandas, Matplotlib)
- Data source: Simulated beauty e-commerce supply chain dataset (Kaggle)

## Files
| File | Description |
|------|-------------|
| `supply_chain_analysis.py` | Full analysis and visualization script |
| `supply_chain_dashboard.png` | Output dashboard |
| `supply_chain_data.csv` | Source dataset |

## How to Run
```bash
pip install pandas matplotlib numpy
python supply_chain_analysis.py
```

## Author
Tran Nguyen Phuong Anh  
[LinkedIn](https://linkedin.com/in/your-link) | tranng.phuonganh027@gmail.com
