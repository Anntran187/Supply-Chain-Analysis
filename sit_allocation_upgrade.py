import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── 0. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("supply_chain_data.csv")
df.columns = [c.strip() for c in df.columns]
PROD_COL = "Product type"

# ── 1. Base replenishment logic (same as your existing project) ───────────────
df["Daily_Sales_Rate"] = df["Number of products sold"] / 30
df["Safety_Stock"]     = df["Daily_Sales_Rate"] * (df["Lead times"] * 0.5)
df["Reorder_Point"]    = (df["Daily_Sales_Rate"] * df["Lead times"]) + df["Safety_Stock"]
df["Target_Stock"]     = df["Reorder_Point"] * 1.5
df["Stock_Cover"]      = np.where(df["Daily_Sales_Rate"] > 0,
                                   df["Stock levels"] / df["Daily_Sales_Rate"], 0)
df["Coverage_Gap"]     = df["Stock_Cover"] - df["Lead times"]

# ── 2. NEW: Stock-in-Transit (SIT) ────────────────────────────────────────────
# SIT = units already on their way (shipping time × daily sales rate)
# This is a realistic proxy: goods ordered but not yet arrived
df["Stock_In_Transit"] = df["Daily_Sales_Rate"] * df["Shipping times"]

# Net Demand = what we actually still need after accounting for SIT & on-hand
# Net Demand = Target Stock - Stock On Hand - Stock In Transit
df["Net_Demand"] = (df["Target_Stock"] - df["Stock levels"] - df["Stock_In_Transit"]).clip(lower=0)

# Flag SIT impact: did SIT reduce or eliminate the replenishment need?
df["SIT_Reduces_Order"] = df["Stock_In_Transit"] >= (df["Target_Stock"] - df["Stock levels"])

# ── 3. NEW: Multi-Customer Allocation ─────────────────────────────────────────
# Simulate 3 customer markets (proxy for ANZ, Greater Asia, Indonesia)
np.random.seed(42)
markets = ["ANZ", "Greater Asia", "Indonesia"]
df["Customer_Market"] = np.random.choice(markets, size=len(df), p=[0.3, 0.4, 0.3])

# Each market has a priority weight for allocation
market_priority = {"ANZ": 1, "Greater Asia": 2, "Indonesia": 3}
df["Market_Priority"] = df["Customer_Market"].map(market_priority)

# Simulate available stock pool per category (70% of total production volume)
available_pool = df.groupby("Product type")["Production volumes"].sum() * 0.70

# Allocation function: distribute available stock proportionally by Net Demand,
# with priority tiebreaker
def allocate_stock(group, pool):
    category = group["Product type"].iloc[0]
    total_pool = pool.get(category, 0)
    total_net_demand = group["Net_Demand"].sum()

    if total_net_demand == 0:
        group["Allocated_Units"] = 0
        group["Allocation_Fill_Rate"] = 100.0
        return group

    # Sort by priority first, then by Net_Demand descending
    group = group.sort_values(["Market_Priority", "Net_Demand"], ascending=[True, False])

    # Proportional allocation capped by available pool
    group["Allocation_Ratio"] = group["Net_Demand"] / total_net_demand
    group["Allocated_Units"]  = (group["Allocation_Ratio"] * total_pool).round(0).astype(int)

    # Cap: no SKU gets more than its Net_Demand
    group["Allocated_Units"]  = group[["Allocated_Units", "Net_Demand"]].min(axis=1).astype(int)

    # Fill rate = allocated / net demand
    group["Allocation_Fill_Rate"] = np.where(
        group["Net_Demand"] > 0,
        (group["Allocated_Units"] / group["Net_Demand"] * 100).round(1),
        100.0
    )
    return group

df = df.groupby("Product type", group_keys=False).apply(
    lambda g: allocate_stock(g, available_pool)
)

# ── 4. Priority classification (updated with Net Demand) ─────────────────────
def classify_priority(row):
    if row["Net_Demand"] == 0:
        return "OK"
    gap = row["Coverage_Gap"]
    if gap < -15:  return "CRITICAL"
    elif gap < -5: return "HIGH"
    else:          return "MEDIUM"

df["Priority"] = df.apply(classify_priority, axis=1)

# ── 5. Dashboard ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor("#0d1117")
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

COLORS = {"CRITICAL": "#e05252", "HIGH": "#f0a500", "MEDIUM": "#f5d020", "OK": "#4caf84"}
CAT_COLORS = {"skincare": "#7b9ef0", "haircare": "#f07b9e", "cosmetics": "#7bf0c4"}
MKT_COLORS = {"ANZ": "#7b9ef0", "Greater Asia": "#f0a500", "Indonesia": "#4caf84"}

def style_ax(ax, title):
    ax.set_facecolor("#161b22")
    ax.tick_params(colors="white", labelsize=8)
    ax.title.set_color("white"); ax.title.set_fontsize(10); ax.title.set_fontweight("bold")
    ax.set_title(title)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.xaxis.label.set_color("white"); ax.yaxis.label.set_color("white")

# 5a. SIT vs On-Hand vs Net Demand by category
ax1 = fig.add_subplot(gs[0, 0])
cats = df.groupby("Product type")[["Stock levels","Stock_In_Transit","Net_Demand"]].mean()
x = np.arange(len(cats)); w = 0.25
ax1.bar(x-w, cats["Stock levels"],     w, label="On-Hand",   color="#7b9ef0")
ax1.bar(x,   cats["Stock_In_Transit"], w, label="SIT",        color="#f0a500")
ax1.bar(x+w, cats["Net_Demand"],       w, label="Net Demand", color="#e05252")
ax1.set_xticks(x); ax1.set_xticklabels(cats.index, rotation=15)
ax1.legend(fontsize=7, labelcolor="white", facecolor="#161b22")
style_ax(ax1, "Avg On-Hand vs SIT vs Net Demand")

# 5b. Fill rate by market
ax2 = fig.add_subplot(gs[0, 1])
fill = df.groupby("Customer_Market")["Allocation_Fill_Rate"].mean()
bars = ax2.bar(fill.index, fill.values,
               color=[MKT_COLORS[m] for m in fill.index])
for bar, val in zip(bars, fill.values):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f"{val:.1f}%", ha="center", va="bottom", color="white", fontsize=8)
ax2.set_ylim(0, 115); ax2.set_ylabel("Avg Fill Rate (%)")
style_ax(ax2, "Allocation Fill Rate by Market")

# 5c. SIT impact: how many SKUs had order reduced by SIT
ax3 = fig.add_subplot(gs[0, 2])
sit_impact = df.groupby("Product type")["SIT_Reduces_Order"].sum()
ax3.bar(sit_impact.index, sit_impact.values,
        color=[CAT_COLORS[c] for c in sit_impact.index])
ax3.set_ylabel("# SKUs where SIT covers gap")
style_ax(ax3, "SKUs Where SIT Eliminates Reorder")

# 5d. Net Demand heatmap by market & category
ax4 = fig.add_subplot(gs[1, :2])
pivot = df.pivot_table(values="Net_Demand", index="Customer_Market",
                       columns="Product type", aggfunc="sum")
im = ax4.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
ax4.set_xticks(range(len(pivot.columns))); ax4.set_xticklabels(pivot.columns, color="white")
ax4.set_yticks(range(len(pivot.index)));   ax4.set_yticklabels(pivot.index,   color="white")
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax4.text(j, i, f"{pivot.values[i,j]:.0f}", ha="center", va="center",
                 color="black", fontsize=9, fontweight="bold")
plt.colorbar(im, ax=ax4, label="Net Demand (units)").ax.yaxis.label.set_color("white")
style_ax(ax4, "Net Demand Heatmap by Market × Category")

# 5e. Allocation output: top 15 SKUs by Net Demand
ax5 = fig.add_subplot(gs[1, 2])
top15 = df.nlargest(15, "Net_Demand")[["SKU","Net_Demand","Allocated_Units","Priority"]]
y_pos = range(len(top15))
ax5.barh(y_pos, top15["Net_Demand"],     color="#e05252", alpha=0.6, label="Net Demand")
ax5.barh(y_pos, top15["Allocated_Units"],color="#4caf84", alpha=0.9, label="Allocated")
ax5.set_yticks(y_pos); ax5.set_yticklabels(top15["SKU"], fontsize=7)
ax5.legend(fontsize=7, labelcolor="white", facecolor="#161b22")
ax5.set_xlabel("Units")
style_ax(ax5, "Top 15 SKUs: Net Demand vs Allocated")

# 5f. Priority breakdown post-SIT
ax6 = fig.add_subplot(gs[2, 0])
pri_counts = df["Priority"].value_counts()
wedge_colors = [COLORS.get(p, "#888") for p in pri_counts.index]
ax6.pie(pri_counts.values, labels=pri_counts.index, colors=wedge_colors,
        autopct="%1.0f%%", textprops={"color":"white","fontsize":8})
style_ax(ax6, "Priority Distribution (Net Demand)")

# 5g. Market allocation summary table
ax7 = fig.add_subplot(gs[2, 1:])
ax7.axis("off")
summary = df.groupby("Customer_Market").agg(
    SKUs=("SKU","count"),
    Total_Net_Demand=("Net_Demand","sum"),
    Total_Allocated=("Allocated_Units","sum"),
    Avg_Fill_Rate=("Allocation_Fill_Rate","mean")
).reset_index()
summary["Avg_Fill_Rate"] = summary["Avg_Fill_Rate"].map("{:.1f}%".format)
summary["Total_Net_Demand"] = summary["Total_Net_Demand"].map("{:,.0f}".format)
summary["Total_Allocated"]  = summary["Total_Allocated"].map("{:,.0f}".format)
summary.columns = ["Market","SKUs","Net Demand","Allocated","Fill Rate"]
tbl = ax7.table(cellText=summary.values, colLabels=summary.columns,
                loc="center", cellLoc="center")
tbl.auto_set_font_size(False); tbl.set_fontsize(9)
for (r,c), cell in tbl.get_celld().items():
    cell.set_facecolor("#21262d" if r == 0 else "#161b22")
    cell.set_text_props(color="white")
    cell.set_edgecolor("#30363d")
style_ax(ax7, "Market Allocation Summary")

fig.suptitle("Supply Chain – SIT Integration & Multi-Market Allocation\nPersonal Care FMCG | ANZ · Greater Asia · Indonesia",
             color="white", fontsize=13, fontweight="bold", y=0.98)

plt.savefig("sit_allocation_dashboard.png", dpi=150, bbox_inches="tight",
            facecolor="#0d1117")
print("✅ Dashboard saved: sit_allocation_dashboard.png")

# ── 6. Export allocation order proposal ──────────────────────────────────────
output_cols = ["SKU","Product type","Customer_Market","Stock levels",
               "Stock_In_Transit","Net_Demand","Allocated_Units",
               "Allocation_Fill_Rate","Priority","Coverage_Gap"]
proposal = df[df["Net_Demand"] > 0][output_cols].sort_values(
    ["Market_Priority","Priority","Net_Demand"],
    ascending=[True, True, False]
)
proposal.to_csv("allocation_proposal.csv", index=False)
print(f"✅ Allocation proposal saved: allocation_proposal.csv ({len(proposal)} SKUs)")
print("\n── Market Summary ──")
print(df.groupby("Customer_Market")[["Net_Demand","Allocated_Units","Allocation_Fill_Rate"]].mean().round(1))
