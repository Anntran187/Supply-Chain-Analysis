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
- **87% of SKUs** fall below reorder point: indicating a systemic under-stocking issue relative to supplier lead times, not isolated cases.
- **Skincare** drives the highest revenue ($241K) yet carries a 95% stockout risk, the highest across all categories, making it the top replenishment priority despite strong sales performance.
- **$2.88M** in replenishment orders identified, with 38 SKUs flagged as CRITICAL, meaning stock will run out before the next shipment arrives if no action is taken.
- Haircare shows the widest gap between stock cover and lead time, suggesting demand is being consistently under-forecasted for this category.

## Dashboards
### Performance Dashboard
![Supply Chain Dashboard](supply_chain_dashboard.png)

### Replenishment Order Proposal Tool
![Replenishment Proposal](replenishment_proposal.png)
![Replenishment Table](replenishment_table.png)

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
| `supply_chain_analysis.py` | Full analysis + replenishment tool |
| `supply_chain_dashboard.png` | Performance overview dashboard |
| `replenishment_proposal.png` `replenishment_table.png` | Order proposal output |
| `supply_chain_data.csv` | Source dataset |

## Author
Tran Nguyen Phuong Anh  
[LinkedIn](http://www.linkedin.com/in/anntran187) | tranng.phuonganh027@gmail.com
