"""Generate an architecture diagram of the NutriTrackAI multi-agent LangGraph."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(14, 9))
ax.set_xlim(-1, 15)
ax.set_ylim(-1, 10)
ax.axis("off")
fig.patch.set_facecolor("#FAFAFA")

COLORS = {
    "start_end": "#1a1a2e",
    "router": "#6C63FF",
    "cooking": "#FF6B6B",
    "nutrition": "#4ECDC4",
    "grocery": "#FFB347",
    "tools": "#E8E8E8",
    "text_light": "#FFFFFF",
    "text_dark": "#1a1a2e",
    "edge": "#888888",
    "conditional": "#6C63FF",
}


def draw_node(x, y, w, h, label, sublabel, color, text_color="#FFFFFF"):
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.15", facecolor=color,
        edgecolor="#555555", linewidth=1.5, zorder=3,
    )
    ax.add_patch(box)
    ax.text(x, y + 0.15, label, ha="center", va="center",
            fontsize=11, fontweight="bold", color=text_color, zorder=4)
    if sublabel:
        ax.text(x, y - 0.25, sublabel, ha="center", va="center",
                fontsize=7.5, color=text_color, alpha=0.85, zorder=4)


def draw_circle(x, y, r, label, color):
    circle = plt.Circle((x, y), r, facecolor=color, edgecolor="#555555",
                         linewidth=1.5, zorder=3)
    ax.add_patch(circle)
    ax.text(x, y, label, ha="center", va="center",
            fontsize=9, fontweight="bold", color="#FFFFFF", zorder=4)


def draw_arrow(x1, y1, x2, y2, color="#888888", style="-|>", lw=1.5,
               linestyle="-", label="", label_offset=(0, 0.2)):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=lw,
            linestyle=linestyle, connectionstyle="arc3,rad=0",
        ),
        zorder=2,
    )
    if label:
        mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center",
                fontsize=7.5, color=color, fontstyle="italic", zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#FAFAFA",
                          edgecolor="none", alpha=0.9))


# ── Nodes ────────────────────────────────────────────────────────────────────

# START
draw_circle(1.5, 5, 0.4, "START", COLORS["start_end"])

# Router
draw_node(4.5, 5, 2.2, 1.2, "Router", "SOM: RouterDecision", COLORS["router"])

# Cooking Agent + Tools
draw_node(9, 8, 2.4, 1.2, "Cooking Agent", "cooking_rag, ingredient_weights", COLORS["cooking"])
draw_node(13, 8, 2.0, 1.0, "Cooking Tools", "ToolNode", COLORS["tools"], COLORS["text_dark"])

# Nutrition Agent + Tools
draw_node(9, 5, 2.4, 1.2, "Nutrition Agent", "macro_targets, meal_planner", COLORS["nutrition"])
draw_node(13, 5, 2.0, 1.0, "Nutrition Tools", "ToolNode", COLORS["tools"], COLORS["text_dark"])

# Grocery Agent + Tools
draw_node(9, 2, 2.4, 1.2, "Grocery Agent", "shopping_list, pantry_checker", COLORS["grocery"], COLORS["text_dark"])
draw_node(13, 2, 2.0, 1.0, "Grocery Tools", "ToolNode", COLORS["tools"], COLORS["text_dark"])

# END circles
for ey in [8, 5, 2]:
    draw_circle(13, ey - 1.4, 0.35, "END", COLORS["start_end"])

# ── Edges ────────────────────────────────────────────────────────────────────

# START -> Router
draw_arrow(1.9, 5, 3.4, 5)

# Router -> agents (conditional, dashed)
draw_arrow(5.6, 5.5, 7.8, 8, color=COLORS["conditional"], linestyle="--",
           label="cooking", label_offset=(-0.3, 0.2))
draw_arrow(5.6, 5.0, 7.8, 5, color=COLORS["conditional"], linestyle="--",
           label="nutrition", label_offset=(0, 0.3))
draw_arrow(5.6, 4.5, 7.8, 2, color=COLORS["conditional"], linestyle="--",
           label="grocery", label_offset=(-0.3, -0.2))

# Agent <-> Tools loops
for ay in [8, 5, 2]:
    draw_arrow(10.2, ay + 0.15, 12, ay + 0.15, label="tool calls", label_offset=(0, 0.25))
    draw_arrow(12, ay - 0.15, 10.2, ay - 0.15, label="results", label_offset=(0, -0.3))

# Agent -> END
for ay in [8, 5, 2]:
    draw_arrow(10.2, ay - 0.5, 12.7, ay - 1.1, color="#555555",
               label="no tools", label_offset=(0.4, 0.15))

# ── Legend ────────────────────────────────────────────────────────────────────

legend_y = 0.2
ax.text(0, legend_y, "Legend:", fontsize=9, fontweight="bold", color="#333")
legend_items = [
    ("Router (SOM)", COLORS["router"]),
    ("Cooking Agent", COLORS["cooking"]),
    ("Nutrition Agent", COLORS["nutrition"]),
    ("Grocery Agent", COLORS["grocery"]),
    ("ToolNode", COLORS["tools"]),
]
for i, (lbl, clr) in enumerate(legend_items):
    xoff = 1.8 + i * 2.6
    box = FancyBboxPatch((xoff, legend_y - 0.2), 0.4, 0.4,
                          boxstyle="round,pad=0.05", facecolor=clr,
                          edgecolor="#555555", linewidth=1)
    ax.add_patch(box)
    ax.text(xoff + 0.6, legend_y, lbl, fontsize=8, va="center", color="#333")

# Dashed = conditional
ax.annotate("", xy=(1.5, legend_y), xytext=(0.5, legend_y),
            arrowprops=dict(arrowstyle="-|>", color=COLORS["conditional"],
                            lw=1.5, linestyle="--"))
ax.text(0, legend_y - 0.5, "- - -> conditional edge     ——> static edge",
        fontsize=8, color="#555", va="center")

# Title
ax.text(7, 9.5, "NutriTrackAI — Multi-Agent LangGraph Architecture",
        ha="center", va="center", fontsize=16, fontweight="bold",
        color=COLORS["text_dark"])

plt.tight_layout()
plt.savefig("graph_architecture.png", dpi=200, bbox_inches="tight",
            facecolor="#FAFAFA", edgecolor="none")
print("Saved: graph_architecture.png")
