"""
Supply Chain Demand & Inventory Analysis
Author: Tran Nguyen Phuong Anh
Dataset: E-commerce beauty supply chain (skincare, haircare, cosmetics)
Purpose: Analyze demand patterns, stock cover, and supplier lead time risk
         to support replenishment planning decisions.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# ── Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("supply_chain_data.csv")

# ── Derived metrics ────────────────────────────────────────────────────────
# Stock Cover (weeks) = Stock / (Units Sold / avg weeks proxy)
# Using lead time as planning horizon reference
df["stock_cover_days"] = (df["Stock levels"] / df["Number of products sold"]) * 30
df["stockout_risk"] = df["stock_cover_days"] < df["Lead times"]  # True = at risk

# Revenue per unit
df["revenue_per_unit"] = df["Revenue generated"] / df["Number of products sold"]

# ── Aggregations ────────────────────────────────────────────────────────────
by_type = df.groupby("Product type").agg(
    total_revenue=("Revenue generated", "sum"),
    avg_stock_cover=("stock_cover_days", "mean"),
    avg_lead_time=("Lead times", "mean"),
    stockout_risk_count=("stockout_risk", "sum"),
    total_skus=("SKU", "count"),
    avg_defect_rate=("Defect rates", "mean"),
).reset_index()

by_type["stockout_risk_pct"] = (
    by_type["stockout_risk_count"] / by_type["total_skus"] * 100
)

# Top 10 SKUs by revenue
top10 = df.nlargest(10, "Revenue generated")[
    ["SKU", "Product type", "Revenue generated", "stock_cover_days", "Lead times", "stockout_risk"]
]

# ── Plot ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 12))
fig.patch.set_facecolor("#F8F9FA")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38)

COLORS = {"haircare": "#4C9BE8", "skincare": "#F4845F", "cosmetics": "#6BCB77"}
color_list = [COLORS[p] for p in by_type["Product type"]]

# ── Chart 1: Revenue by Category ──────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
bars = ax1.bar(by_type["Product type"], by_type["total_revenue"] / 1000,
               color=color_list, edgecolor="white", linewidth=1.5)
ax1.set_title("Total Revenue by Category", fontweight="bold", fontsize=11)
ax1.set_ylabel("Revenue (USD '000)")
ax1.set_facecolor("#FFFFFF")
for bar, val in zip(bars, by_type["total_revenue"]):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
             f"${val/1000:.1f}K", ha="center", va="bottom", fontsize=9, fontweight="bold")

# ── Chart 2: Avg Stock Cover vs Lead Time ─────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
x = np.arange(len(by_type))
w = 0.35
ax2.bar(x - w/2, by_type["avg_stock_cover"], w, label="Avg Stock Cover (days)",
        color=color_list, edgecolor="white")
ax2.bar(x + w/2, by_type["avg_lead_time"], w, label="Avg Lead Time (days)",
        color=["#B0C4DE", "#F4A07A", "#A8E6A3"], edgecolor="white")
ax2.set_xticks(x)
ax2.set_xticklabels(by_type["Product type"])
ax2.set_title("Stock Cover vs Lead Time", fontweight="bold", fontsize=11)
ax2.set_ylabel("Days")
ax2.legend(fontsize=8)
ax2.set_facecolor("#FFFFFF")
ax2.axhline(y=by_type["avg_lead_time"].mean(), color="red",
            linestyle="--", alpha=0.5, linewidth=1, label="Avg lead time")

# ── Chart 3: Stockout Risk % ──────────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
wedges, texts, autotexts = ax3.pie(
    by_type["stockout_risk_count"],
    labels=by_type["Product type"],
    autopct="%1.0f%%",
    colors=list(COLORS.values()),
    startangle=90,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
)
ax3.set_title("Stockout Risk Distribution\n(SKUs where stock < lead time)", 
              fontweight="bold", fontsize=11)

# ── Chart 4: Top 10 SKUs by Revenue + Risk Flag ───────────────────────────
ax4 = fig.add_subplot(gs[1, :2])
top10_sorted = top10.sort_values("Revenue generated", ascending=True)
bar_colors = ["#E74C3C" if risk else "#2ECC71" for risk in top10_sorted["stockout_risk"]]
bars4 = ax4.barh(top10_sorted["SKU"], top10_sorted["Revenue generated"],
                 color=bar_colors, edgecolor="white")
ax4.set_title("Top 10 Revenue SKUs  |  🔴 Stockout Risk   🟢 Safe",
              fontweight="bold", fontsize=11)
ax4.set_xlabel("Revenue (USD)")
ax4.set_facecolor("#FFFFFF")
for bar, val in zip(bars4, top10_sorted["Revenue generated"]):
    ax4.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
             f"${val:,.0f}", va="center", fontsize=8)

# ── Chart 5: Defect Rate vs Revenue per Unit ──────────────────────────────
ax5 = fig.add_subplot(gs[1, 2])
for ptype, group in df.groupby("Product type"):
    ax5.scatter(group["Defect rates"], group["revenue_per_unit"],
                label=ptype, color=COLORS[ptype], alpha=0.7, s=50)
ax5.set_title("Defect Rate vs Revenue/Unit\n(Supplier Quality Signal)", 
              fontweight="bold", fontsize=11)
ax5.set_xlabel("Defect Rate")
ax5.set_ylabel("Revenue per Unit (USD)")
ax5.legend(fontsize=8)
ax5.set_facecolor("#FFFFFF")

# ── Header ─────────────────────────────────────────────────────────────────
fig.suptitle(
    "Supply Chain Performance Dashboard  |  Beauty E-commerce",
    fontsize=15, fontweight="bold", y=0.98, color="#2C3E50"
)

plt.savefig("supply_chain_dashboard.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("✅ Dashboard saved: supply_chain_dashboard.png")

# ── Summary Table ──────────────────────────────────────────────────────────
print("\n📊 Key Findings:")
print(by_type[["Product type", "total_revenue", "avg_stock_cover",
               "avg_lead_time", "stockout_risk_pct", "avg_defect_rate"]].to_string(index=False))

at_risk = df[df["stockout_risk"]].shape[0]
print(f"\n⚠️  {at_risk} SKUs ({at_risk}%) have stock cover below their lead time → replenishment priority")
print(f"💰  Highest revenue category: {by_type.loc[by_type['total_revenue'].idxmax(), 'Product type']}")
