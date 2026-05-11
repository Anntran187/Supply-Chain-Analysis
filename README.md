# Supply Chain Demand & Inventory Analysis

## Overview
An end-to-end supply chain analysis of a personal care FMCG dataset (100 SKUs across skincare, haircare, and cosmetics), focused on demand planning, replenishment risk, and multi-market stock allocation across ANZ, Greater Asia, and Indonesia.

Includes an automated Net Demand model integrating Stock-in-Transit (SIT), 
a prioritized replenishment order proposal generator (Critical/High/Medium), 
and a market allocation engine with fill rate tracking.

## Objectives
- Identify SKUs where stock cover falls below reorder point (stockout risk)
- Integrate Stock-in-Transit (SIT) into Net Demand to avoid over-ordering
- Generate executable allocation proposals across 3 customer markets
- Compare revenue performance and replenishment priority across categories
- Surface supplier quality issues via defect rate analysis

## Key Findings
- **87% of SKUs** fall below reorder point — a systemic under-stocking issue relative to supplier lead times, not isolated cases
- **Skincare** drives the highest revenue ($241K) yet carries 95% stockout risk, top replenishment priority despite strong sales performance
- **$2.88M** in replenishment value identified; 38 SKUs flagged CRITICAL (stock runs out before next shipment if no action taken)
- **SIT integration** reduces unnecessary reorder for 11 SKUs, preventing excess stock build across categories
- **Allocation fill rate:** ANZ 91.5% | Greater Asia 90.8% | Indonesia 88.5%
- **85 SKUs** require replenishment after SIT netting (vs. 87 without SIT)

## Dashboards

### Performance Dashboard
![Supply Chain Dashboard](supply_chain_dashboard.png)

### Replenishment Order Proposal
![Replenishment Proposal](replenishment_proposal.png)
![Replenishment Table](replenishment_table.png)

### SIT Integration & Multi-Market Allocation
![SIT Allocation Dashboard](sit_allocation_dashboard.png)

## Planning Logic

| Metric | Formula |
|---|---|
| Daily Sales Rate | Units Sold / 30 |
| Safety Stock | Daily Sales Rate × (Lead Time × 0.5) |
| Reorder Point | (Daily Sales Rate × Lead Time) + Safety Stock |
| Stock In Transit (SIT) | Daily Sales Rate × Shipping Time |
| **Net Demand** | **Target Stock − On-Hand Stock − SIT** |
| Order Quantity | Target Stock − Current Stock |
| Allocation | Net Demand distributed by market priority & fill rate |

## Tools Used
- Python (Pandas, Matplotlib, NumPy)
- Dataset: Personal care FMCG supply chain (100 SKUs)

## Files
| File | Description |
|---|---|
| `supply_chain_analysis.py` | Base analysis + replenishment tool |
| `sit_allocation_upgrade.py` | SIT integration + multi-market allocation |
| `supply_chain_dashboard.png` | Performance overview dashboard |
| `replenishment_proposal.png` | Replenishment order proposal output |
| `sit_allocation_dashboard.png` | SIT & allocation dashboard |
| `allocation_proposal.csv` | Executable allocation output by market |
| `supply_chain_data.csv` | Source dataset |

## Author
Tran Nguyen Phuong Anh  
[LinkedIn](http://www.linkedin.com/in/anntran187) | tranng.phuonganh027@gmail.com
