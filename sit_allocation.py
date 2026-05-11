"""
Supply Chain – SIT Integration & Multi-Location Allocation
Author: Tran Nguyen Phuong Anh

DATA SOURCES (all real columns from dataset, zero fake data):
  Stock levels            → on-hand inventory per SKU
  Shipping times          → days in transit (1–10d); used to estimate SIT
  Order quantities        → units on order from supplier; allocation pool
  Lead times              → supplier lead time (days)
  Number of products sold → monthly sales; basis for daily demand rate
  Location                → customer city (Mumbai/Kolkata/Delhi/Bangalore/Chennai)
  Shipping carriers       → Carrier A/B/C
  Routes                  → Route A/B/C

METHODOLOGY:
  SIT        = Daily_Sales_Rate × Shipping_times
  Net_Demand = Target_Stock − Stock_On_Hand − SIT  (clipped ≥ 0)
  Allocation = Order_quantities pool distributed proportionally by Net_Demand
               within each Product type; capped at each SKU's Net_Demand
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── 0. Load ───────────────────────────────────────────────────────────────────
df = pd.read_csv("supply_chain_data.csv")
df.columns = [c.strip() for c in df.columns]

# ── 1. Base metrics ───────────────────────────────────────────────────────────
df["Daily_Sales_Rate"] = df["Number of products sold"] / 30
df["Safety_Stock"]     = df["Daily_Sales_Rate"] * (df["Lead times"] * 0.5)
df["Reorder_Point"]    = (df["Daily_Sales_Rate"] * df["Lead times"]) + df["Safety_Stock"]
df["Target_Stock"]     = df["Reorder_Point"] * 1.5
df["Stock_Cover"]      = df["Stock levels"] / df["Daily_Sales_Rate"]
df["Coverage_Gap"]     = df["Stock_Cover"] - df["Lead times"]

# ── 2. SIT using real Shipping times column ───────────────────────────────────
df["Stock_In_Transit"] = (df["Daily_Sales_Rate"] * df["Shipping times"]).round(1)
df["Net_Demand"]       = (
    df["Target_Stock"] - df["Stock levels"] - df["Stock_In_Transit"]
).clip(lower=0).round(1)
df["SIT_Covers_Gap"]   = (
    df["Stock_In_Transit"] >= (df["Target_Stock"] - df["Stock levels"])
)

# ── 3. Allocation using real Location + Order quantities columns ──────────────
loc_priority = {"Mumbai": 1, "Delhi": 2, "Kolkata": 3, "Bangalore": 4, "Chennai": 5}
df["Location_Priority"] = df["Location"].map(loc_priority)
available_pool = df.groupby("Product type")["Order quantities"].sum()

def compute_allocation(df, pool):
    results = []
    for cat, group in df.groupby("Product type"):
        group = group.copy().sort_values(
            ["Location_Priority", "Net_Demand"], ascending=[True, False]
        )
        total_pool = pool.get(cat, 0)
        total_nd   = group["Net_Demand"].sum()
        if total_nd == 0:
            group["Allocated_Units"]      = 0
            group["Allocation_Fill_Rate"] = 100.0
        else:
            group["Alloc_Ratio"]     = group["Net_Demand"] / total_nd
            group["Allocated_Units"] = (group["Alloc_Ratio"] * total_pool).round(0).astype(int)
            group["Allocated_Units"] = group[["Allocated_Units", "Net_Demand"]].min(axis=1).astype(int)
            group["Allocation_Fill_Rate"] = np.where(
                group["Net_Demand"] > 0,
                (group["Allocated_Units"] / group["Net_Demand"] * 100).round(1),
                100.0
            )
        results.append(group)
    return pd.concat(results)

df = compute_allocation(df, available_pool)

# ── 4. Priority (post-SIT) ────────────────────────────────────────────────────
def classify(row):
    if row["Net_Demand"] == 0:    return "OK"
    if row["Coverage_Gap"] < -15: return "CRITICAL"
    if row["Coverage_Gap"] < -5:  return "HIGH"
    return "MEDIUM"

df["Priority"] = df.apply(classify, axis=1)

# ── 5. Dashboard ──────────────────────────────────────────────────────────────
DARK_BG = "#0d1117"
CELL_BG = "#161b22"
BORDER  = "#30363d"
COLORS  = {"CRITICAL": "#e05252", "HIGH": "#f0a500", "MEDIUM": "#f5d020", "OK": "#4caf84"}
CAT_C   = {"skincare": "#7b9ef0", "haircare": "#f07b9e", "cosmetics": "#7bf0c4"}
LOC_C   = {"Mumbai": "#7b9ef0", "Kolkata": "#f07b9e",
           "Delhi": "#7bf0c4", "Bangalore": "#f0a500", "Chennai": "#e05252"}

def style(ax, title):
    ax.set_facecolor(CELL_BG)
    ax.set_title(title, color="white", fontsize=10, fontweight="bold")
    ax.tick_params(colors="white", labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor(DARK_BG)
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.50, wspace=0.35)

# 1: On-Hand vs SIT vs Net Demand
ax1 = fig.add_subplot(gs[0, 0])
cats = df.groupby("Product type")[["Stock levels", "Stock_In_Transit", "Net_Demand"]].mean()
x = np.arange(len(cats)); w = 0.25
ax1.bar(x-w, cats["Stock levels"],     w, label="On-Hand",    color="#7b9ef0")
ax1.bar(x,   cats["Stock_In_Transit"], w, label="SIT",        color="#f0a500")
ax1.bar(x+w, cats["Net_Demand"],       w, label="Net Demand", color="#e05252")
ax1.set_xticks(x); ax1.set_xticklabels(cats.index, rotation=15, color="white")
ax1.legend(fontsize=7, labelcolor="white", facecolor=CELL_BG)
ax1.set_ylabel("Avg Units")
style(ax1, "Avg On-Hand vs SIT vs Net Demand")

# 2: Fill Rate by Location
ax2 = fig.add_subplot(gs[0, 1])
fill = df.groupby("Location")["Allocation_Fill_Rate"].mean().sort_values(ascending=False)
bars = ax2.bar(fill.index, fill.values,
               color=[LOC_C[l] for l in fill.index], edgecolor=BORDER)
for bar, val in zip(bars, fill.values):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f"{val:.1f}%", ha="center", va="bottom", color="white", fontsize=8)
ax2.set_ylim(0, 115); ax2.set_ylabel("Avg Fill Rate (%)")
ax2.tick_params(axis="x", colors="white", labelsize=8)
style(ax2, "Allocation Fill Rate by Location")

# 3: SKUs where SIT covers gap
ax3 = fig.add_subplot(gs[0, 2])
sit_impact = df.groupby("Product type")["SIT_Covers_Gap"].sum()
bars3 = ax3.bar(sit_impact.index, sit_impact.values,
                color=[CAT_C[c] for c in sit_impact.index], edgecolor=BORDER)
for bar, val in zip(bars3, sit_impact.values):
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
             str(int(val)), ha="center", color="white", fontsize=10, fontweight="bold")
ax3.set_ylabel("# SKUs")
ax3.tick_params(axis="x", colors="white", labelsize=8)
style(ax3, "SKUs Where SIT Covers Gap\n(No Reorder Needed)")

# 4: Net Demand heatmap — Location × Category
ax4 = fig.add_subplot(gs[1, :2])
pivot = df.pivot_table(values="Net_Demand", index="Location",
                       columns="Product type", aggfunc="sum")
im = ax4.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
ax4.set_xticks(range(len(pivot.columns)))
ax4.set_xticklabels(pivot.columns, color="white", fontsize=9)
ax4.set_yticks(range(len(pivot.index)))
ax4.set_yticklabels(pivot.index, color="white", fontsize=9)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax4.text(j, i, f"{pivot.values[i,j]:,.0f}",
                 ha="center", va="center", color="black", fontsize=9, fontweight="bold")
cb = plt.colorbar(im, ax=ax4, label="Net Demand (units)")
cb.ax.yaxis.label.set_color("white"); cb.ax.tick_params(colors="white")
style(ax4, "Net Demand Heatmap: Location × Category")

# 5: Top 15 SKUs Net Demand vs Allocated
ax5 = fig.add_subplot(gs[1, 2])
top15 = df.nlargest(15, "Net_Demand")[["SKU", "Net_Demand", "Allocated_Units"]]
y_pos = range(len(top15))
ax5.barh(y_pos, top15["Net_Demand"],      color="#e05252", alpha=0.5, label="Net Demand")
ax5.barh(y_pos, top15["Allocated_Units"], color="#4caf84", alpha=0.9, label="Allocated")
ax5.set_yticks(y_pos); ax5.set_yticklabels(top15["SKU"], fontsize=7, color="white")
ax5.legend(fontsize=7, labelcolor="white", facecolor=CELL_BG)
ax5.set_xlabel("Units")
style(ax5, "Top 15 SKUs: Net Demand vs Allocated")

# 6: Priority pie
ax6 = fig.add_subplot(gs[2, 0])
pri = df["Priority"].value_counts()
ax6.pie(pri.values, labels=pri.index,
        colors=[COLORS.get(p, "#888") for p in pri.index],
        autopct="%1.0f%%", textprops={"color": "white", "fontsize": 8})
style(ax6, "Priority Distribution\n(Post-SIT Adjustment)")

# 7: Location summary table
ax7 = fig.add_subplot(gs[2, 1:])
ax7.axis("off")
summary = df.groupby("Location").agg(
    SKUs=("SKU", "count"),
    Avg_SIT=("Stock_In_Transit", "mean"),
    Total_Net_Demand=("Net_Demand", "sum"),
    Total_Allocated=("Allocated_Units", "sum"),
    Avg_Fill_Rate=("Allocation_Fill_Rate", "mean")
).reset_index().sort_values("Avg_Fill_Rate", ascending=False)
summary["Avg_SIT"]          = summary["Avg_SIT"].map("{:.1f}".format)
summary["Total_Net_Demand"] = summary["Total_Net_Demand"].map("{:,.0f}".format)
summary["Total_Allocated"]  = summary["Total_Allocated"].map("{:,.0f}".format)
summary["Avg_Fill_Rate"]    = summary["Avg_Fill_Rate"].map("{:.1f}%".format)
summary.columns = ["Location", "SKUs", "Avg SIT (units)", "Net Demand", "Allocated", "Fill Rate"]

tbl = ax7.table(cellText=summary.values, colLabels=summary.columns,
                loc="center", cellLoc="center")
tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1, 1.8)
for (r, c), cell in tbl.get_celld().items():
    cell.set_facecolor("#21262d" if r == 0 else CELL_BG)
    cell.set_text_props(color="white"); cell.set_edgecolor(BORDER)
style(ax7, "Location Allocation Summary")

fig.suptitle(
    "Supply Chain – SIT Integration & Multi-Location Allocation\n"
    "Beauty E-commerce  |  Mumbai · Kolkata · Delhi · Bangalore · Chennai",
    color="white", fontsize=13, fontweight="bold", y=0.99
)
plt.savefig("sit_allocation_dashboard.png", dpi=150,
            bbox_inches="tight", facecolor=DARK_BG)
print("✅ Dashboard saved.")

# ── 6. Export ─────────────────────────────────────────────────────────────────
out_cols = ["SKU", "Product type", "Location", "Shipping carriers", "Routes",
            "Stock levels", "Stock_In_Transit", "Net_Demand",
            "Order quantities", "Allocated_Units", "Allocation_Fill_Rate",
            "Priority", "Coverage_Gap"]
proposal = df[df["Net_Demand"] > 0].copy()
proposal = proposal.sort_values(
    ["Location_Priority", "Priority", "Net_Demand"],
    ascending=[True, True, False]
)[out_cols]
proposal.to_csv("allocation_proposal.csv", index=False)
print(f"✅ Allocation proposal: {len(proposal)} SKUs exported.")

print("\n── SIT Impact ──")
sit_n = df["SIT_Covers_Gap"].sum()
print(f"{sit_n} SKUs covered by SIT (no reorder needed)")
print(f"{len(df) - sit_n} SKUs require replenishment after SIT")

print("\n── Location Summary ──")
print(df.groupby("Location")[["Stock_In_Transit", "Net_Demand",
                               "Allocated_Units", "Allocation_Fill_Rate"]].mean().round(1))
