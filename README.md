# Supply Chain Demand & Inventory Analysis

## Overview
An exploratory analysis of a beauty e-commerce supply chain dataset (100 SKUs across skincare, haircare, and cosmetics categories), focused on identifying replenishment risk, revenue performance, and supplier quality signals.

Includes an automated replenishment order proposal generator with priority classification (Critical/High/Medium) to support data-driven restocking decisions.

## Objectives
- Identify SKUs where stock cover falls below reorder point (stockout risk)
- Compare revenue performance across product categories
- Generate prioritized replenishment order proposals with recommended order quantities
- Surface supplier quality issues via defect rate analysis

## Key Findings
- **87% of SKUs** require replenishment — 38 Critical, 26 High, 23 Medium
- **Skincare** generates the highest revenue ($241K) but has the highest stockout risk (95% of SKUs)
- **Total replenishment value** needed: $2,888,671 across all categories
- Reorder logic uses Safety Stock buffer to account for lead time variability

## Dashboards
### Performance Dashboard
![Supply Chain Dashboard](supply_chain_dashboard.png)

### Replenishment Order Proposal Tool
![Replenishment Proposal](replenishment_proposal.png)

## Replenishment Logic
| Metric | Formula |
|---|---|
| Daily Sales Rate | Units Sold / 30 |
| Safety Stock | Daily Sales Rate × (Lead Time × 0.5) |
| Reorder Point | (Daily Sales Rate × Lead Time) + Safety Stock |
| Order Quantity | Target Stock − Current Stock |

## Tools Used
- Python (Pandas, Matplotlib, NumPy)
- Dataset: Beauty e-commerce supply chain (Kaggle)

## Files
| File | Description |
|---|---|
| `supply_chain_analysis_v2.py` | Full analysis + replenishment tool |
| `supply_chain_dashboard.png` | Performance overview dashboard |
| `replenishment_proposal.png` | Order proposal output |
| `supply_chain_data.csv` | Source dataset |

## How to Run
```bash
pip install pandas matplotlib numpy
python supply_chain_analysis_v2.py
```
## Author
Tran Nguyen Phuong Anh  
[LinkedIn](http://www.linkedin.com/in/anntran187) | tranng.phuonganh027@gmail.com
