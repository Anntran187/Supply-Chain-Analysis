"""
Supply Chain Demand & Inventory Analysis + Replenishment Order Proposal Tool
Author: Tran Nguyen Phuong Anh
Dataset: E-commerce beauty supply chain (skincare, haircare, cosmetics)
Purpose: Analyze demand patterns, stock cover, and generate actionable
         replenishment order proposals to prevent stockouts.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import numpy as np

# ── Load & Validate ────────────────────────────────────────────────────────
df = pd.read_csv("supply_chain_data.csv")

# ── Core Metrics ───────────────────────────────────────────────────────────
# Daily sales rate (proxy: monthly sold / 30)
df["daily_sales_rate"] = df["Number of products sold"] / 30

# Stock Cover in days = current stock / daily sales rate
df["stock_cover_days"] = df["Stock levels"] / df["daily_sales_rate"].replace(0, np.nan)

# Safety Stock = daily sales rate × (lead time × 0.5) — buffer for variability
df["safety_stock"] = df["daily_sales_rate"] * (df["Lead times"] * 0.5)

# Reorder Point = (daily sales rate × lead time) + safety stock
df["reorder_point"] = (df["daily_sales_rate"] * df["Lead times"]) + df["safety_stock"]

# Stockout Risk: stock has fallen below reorder point
df["stockout_risk"] = df["Stock levels"] < df["reorder_point"]

# Coverage Gap: how many days short vs lead time
df["coverage_gap_days"] = df["stock_cover_days"] - df["Lead times"]

# ── Replenishment Order Proposal Logic ────────────────────────────────────
def calculate_order_qty(row):
    """
    Order Quantity = bring stock up to 2x lead time demand + safety stock
    Only order if stock is below reorder point.
    """
    if not row["stockout_risk"]:
        return 0
    target_stock = (row["daily_sales_rate"] * row["Lead times"] * 2) + row["safety_stock"]
    order_qty = max(0, target_stock - row["Stock levels"])
    return round(order_qty)

def assign_priority(row):
    if not row["stockout_risk"]:
        return "OK"
    gap = row["coverage_gap_days"]
    if gap < -15:
        return "CRITICAL"
    elif gap < -7:
        return "HIGH"
    else:
        return "MEDIUM"

df["recommended_order_qty"] = df.apply(calculate_order_qty, axis=1)
df["priority"] = df.apply(assign_priority, axis=1)
df["order_value_usd"] = df["recommended_order_qty"] * df["Price"]

# ── Replenishment Table ────────────────────────────────────────────────────
order_proposal = df[df["stockout_risk"]].copy()
order_proposal = order_proposal.sort_values(
    ["priority", "Revenue generated"],
    ascending=[True, False],
    key=lambda x: x.map({"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}) if x.name == "priority" else x
)

proposal_display = order_proposal[[
    "SKU", "Product type", "Stock levels", "stock_cover_days",
    "Lead times", "coverage_gap_days", "recommended_order_qty",
    "order_value_usd", "priority"
]].round(1)

# ── Category Aggregations ──────────────────────────────────────────────────
by_type = df.groupby("Product type").agg(
    total_revenue=("Revenue generated", "sum"),
    avg_stock_cover=("stock_cover_days", "mean"),
    avg_lead_time=("Lead times", "mean"),
    stockout_count=("stockout_risk", "sum"),
    total_skus=("SKU", "count"),
    total_order_value=("order_value_usd", "sum"),
).reset_index()
by_type["stockout_pct"] = (by_type["stockout_count"] / by_type["total_skus"] * 100).round(1)

priority_counts = df["priority"].value_counts()

# ── Color Maps ─────────────────────────────────────────────────────────────
CAT_COLORS = {"haircare": "#4C9BE8", "skincare": "#F4845F", "cosmetics": "#6BCB77"}
PRIORITY_COLORS = {"CRITICAL": "#E74C3C", "HIGH": "#F39C12", "MEDIUM": "#F1C40F", "OK": "#2ECC71"}

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 1: Performance Dashboard
# ══════════════════════════════════════════════════════════════════════════
fig1 = plt.figure(figsize=(16, 10))
fig1.patch.set_facecolor("#F8F9FA")
gs1 = gridspec.GridSpec(2, 3, figure=fig1, hspace=0.45, wspace=0.38)

# Chart 1: Revenue by Category
ax1 = fig1.add_subplot(gs1[0, 0])
color_list = [CAT_COLORS[p] for p in by_type["Product type"]]
bars = ax1.bar(by_type["Product type"], by_type["total_revenue"] / 1000,
               color=color_list, edgecolor="white", linewidth=1.5)
ax1.set_title("Total Revenue by Category", fontweight="bold", fontsize=11)
ax1.set_ylabel("Revenue (USD '000)")
ax1.set_facecolor("#FFFFFF")
for bar, val in zip(bars, by_type["total_revenue"]):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
             f"${val/1000:.1f}K", ha="center", va="bottom", fontsize=9, fontweight="bold")

# Chart 2: Stock Cover vs Lead Time
ax2 = fig1.add_subplot(gs1[0, 1])
x = np.arange(len(by_type))
w = 0.35
faded_colors = [c + "88" for c in color_list]  # same hue, 50% alpha via hex
ax2.bar(x - w/2, by_type["avg_stock_cover"], w, color=color_list, edgecolor="white")
ax2.bar(x + w/2, by_type["avg_lead_time"],   w, color=color_list, edgecolor="white", alpha=0.35)
ax2.set_xticks(x)
ax2.set_xticklabels(by_type["Product type"])
ax2.set_title("Stock Cover vs Lead Time\n(solid = stock cover, faded = lead time)", fontweight="bold", fontsize=11)
ax2.set_ylabel("Days")
# Manual legend: solid patch = Stock Cover, faded = Lead Time
legend_patches = [
    mpatches.Patch(color="#555555", label="Avg Stock Cover (days)"),
    mpatches.Patch(color="#aaaaaa", alpha=0.5, label="Avg Lead Time (days)"),
]
ax2.legend(handles=legend_patches, fontsize=8)
ax2.set_facecolor("#FFFFFF")

# Chart 3: Stockout Risk %
ax3 = fig1.add_subplot(gs1[0, 2])
ax3.pie(by_type["stockout_count"], labels=by_type["Product type"],
        autopct="%1.0f%%", colors=list(CAT_COLORS.values()),
        startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 2})
ax3.set_title("Stockout Risk Distribution\n(SKUs below reorder point)",
              fontweight="bold", fontsize=11)

# Chart 4: Top 10 SKUs by Revenue + Risk
ax4 = fig1.add_subplot(gs1[1, :2])
top10 = df.nlargest(10, "Revenue generated").sort_values("Revenue generated", ascending=True)
bar_colors_4 = [PRIORITY_COLORS[p] for p in top10["priority"]]
bars4 = ax4.barh(top10["SKU"], top10["Revenue generated"], color=bar_colors_4, edgecolor="white")
ax4.set_title("Top 10 Revenue SKUs  |  RED=Critical  ORANGE=High  YELLOW=Medium  GREEN=OK",
              fontweight="bold", fontsize=10)
ax4.set_xlabel("Revenue (USD)")
ax4.set_facecolor("#FFFFFF")
for bar, val in zip(bars4, top10["Revenue generated"]):
    ax4.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
             f"${val:,.0f}", va="center", fontsize=8)

# Chart 5: Coverage Gap Distribution
ax5 = fig1.add_subplot(gs1[1, 2])
ax5.hist(df["coverage_gap_days"].dropna(), bins=20, color="#4C9BE8",
         edgecolor="white", linewidth=0.8)
ax5.axvline(x=0, color="#E74C3C", linestyle="--", linewidth=2, label="Break-even (stock = lead time)")
ax5.set_title("Stock Coverage Gap Distribution\n(Negative = Stockout Risk)",
              fontweight="bold", fontsize=11)
ax5.set_xlabel("Coverage Gap (days)")
ax5.set_ylabel("Number of SKUs")
ax5.legend(fontsize=8)
ax5.set_facecolor("#FFFFFF")

fig1.suptitle("Supply Chain Performance Dashboard  |  Personal Care FMCG",
              fontsize=15, fontweight="bold", y=0.98, color="#2C3E50")
plt.savefig("supply_chain_dashboard.png", dpi=150, bbox_inches="tight",
            facecolor=fig1.get_facecolor())
print("Dashboard 1 saved.")

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 2: Replenishment Order Proposal Tool
# ══════════════════════════════════════════════════════════════════════════
fig2 = plt.figure(figsize=(18, 14))
fig2.patch.set_facecolor("#F8F9FA")
gs2 = gridspec.GridSpec(3, 2, figure=fig2, hspace=0.55, wspace=0.35)

# Chart 1: Priority Breakdown (how many SKUs per priority)
ax_p1 = fig2.add_subplot(gs2[0, 0])
p_order = ["CRITICAL", "HIGH", "MEDIUM", "OK"]
p_vals = [priority_counts.get(p, 0) for p in p_order]
p_colors = [PRIORITY_COLORS[p] for p in p_order]
bars_p = ax_p1.bar(p_order, p_vals, color=p_colors, edgecolor="white", linewidth=1.5)
ax_p1.set_title("SKU Count by Replenishment Priority", fontweight="bold", fontsize=11)
ax_p1.set_ylabel("Number of SKUs")
ax_p1.set_facecolor("#FFFFFF")
for bar, val in zip(bars_p, p_vals):
    ax_p1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
               str(val), ha="center", fontweight="bold", fontsize=11)

# Chart 2: Total Order Value by Category
ax_p2 = fig2.add_subplot(gs2[0, 1])
order_by_cat = order_proposal.groupby("Product type")["order_value_usd"].sum()
ax_p2.bar(order_by_cat.index, order_by_cat.values / 1000,
          color=[CAT_COLORS[c] for c in order_by_cat.index],
          edgecolor="white", linewidth=1.5)
ax_p2.set_title("Total Replenishment Order Value\nby Category", fontweight="bold", fontsize=11)
ax_p2.set_ylabel("Order Value (USD '000)")
ax_p2.set_facecolor("#FFFFFF")
for i, (cat, val) in enumerate(order_by_cat.items()):
    ax_p2.text(i, val / 1000 + 0.1, f"${val/1000:.1f}K",
               ha="center", fontweight="bold", fontsize=10)

# Chart 3: Scatter — Revenue vs Coverage Gap (bubble = order qty)
ax_p3 = fig2.add_subplot(gs2[1, :])
for priority in ["CRITICAL", "HIGH", "MEDIUM"]:
    subset = order_proposal[order_proposal["priority"] == priority]
    if len(subset) == 0:
        continue
    sc = ax_p3.scatter(
        subset["coverage_gap_days"],
        subset["Revenue generated"],
        s=subset["recommended_order_qty"] * 0.5,
        c=PRIORITY_COLORS[priority],
        alpha=0.75,
        edgecolors="white",
        linewidth=0.8,
        label=priority
    )
ax_p3.axvline(x=0, color="black", linestyle="--", alpha=0.3)
ax_p3.set_title("Replenishment Priority Map\nX: Coverage Gap (days)  |  Y: Revenue  |  Bubble size: Order Qty",
                fontweight="bold", fontsize=11)
ax_p3.set_xlabel("Coverage Gap (days)  [more negative = more urgent]")
ax_p3.set_ylabel("Revenue Generated (USD)")
ax_p3.legend(title="Priority", fontsize=9)
ax_p3.set_facecolor("#FFFFFF")

# Chart 4: Top 15 CRITICAL/HIGH SKUs — Order Proposal Table
ax_p4 = fig2.add_subplot(gs2[2, :])
ax_p4.axis("off")

top_orders = order_proposal[order_proposal["priority"].isin(["CRITICAL", "HIGH"])].head(15)
table_data = []
for _, row in top_orders.iterrows():
    table_data.append([
        row["SKU"],
        row["Product type"].title(),
        f"{int(row['Stock levels'])}",
        f"{row['stock_cover_days']:.1f}d",
        f"{int(row['Lead times'])}d",
        f"{row['coverage_gap_days']:.1f}d",
        f"{int(row['recommended_order_qty'])} units",
        f"${row['order_value_usd']:,.0f}",
        row["priority"]
    ])

col_labels = ["SKU", "Category", "Current Stock", "Stock Cover",
              "Lead Time", "Gap", "Order Qty", "Order Value", "Priority"]

table = ax_p4.table(
    cellText=table_data,
    colLabels=col_labels,
    loc="center",
    cellLoc="center"
)
table.auto_set_font_size(False)
table.set_fontsize(8.5)
table.scale(1, 1.6)

# Style header
for j in range(len(col_labels)):
    table[0, j].set_facecolor("#2C3E50")
    table[0, j].set_text_props(color="white", fontweight="bold")

# Style rows by priority
for i, (_, row) in enumerate(top_orders.iterrows()):
    color = "#FADBD8" if row["priority"] == "CRITICAL" else "#FDEBD0"
    for j in range(len(col_labels)):
        table[i + 1, j].set_facecolor(color)

ax_p4.set_title("Replenishment Order Proposal — CRITICAL & HIGH Priority SKUs",
                fontweight="bold", fontsize=12, pad=20)

fig2.suptitle("Replenishment Order Proposal Tool  |  Personal Care FMCG Supply Chain",
              fontsize=15, fontweight="bold", y=0.98, color="#2C3E50")
plt.savefig("replenishment_proposal.png", dpi=150, bbox_inches="tight",
            facecolor=fig2.get_facecolor())
print("Dashboard 2 saved.")

# ── Console Summary ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("REPLENISHMENT SUMMARY")
print("="*60)
print(f"Total SKUs analyzed       : {len(df)}")
print(f"SKUs requiring reorder    : {df['stockout_risk'].sum()} ({df['stockout_risk'].mean()*100:.0f}%)")
print(f"  - CRITICAL priority     : {(df['priority']=='CRITICAL').sum()}")
print(f"  - HIGH priority         : {(df['priority']=='HIGH').sum()}")
print(f"  - MEDIUM priority       : {(df['priority']=='MEDIUM').sum()}")
total_order_val = df["order_value_usd"].sum()
print(f"Total replenishment value : ${total_order_val:,.0f}")
print(f"Highest risk category     : {by_type.loc[by_type['stockout_pct'].idxmax(), 'Product type'].title()} ({by_type['stockout_pct'].max():.0f}% SKUs at risk)")
print("="*60)
