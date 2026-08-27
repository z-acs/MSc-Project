import math
import time
from itertools import combinations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Rule-based Dashboard Network System", page_icon="📊", layout="wide")
st.title("📊 Rule-based Dashboard Network System")
st.write(
    "Upload a CSV dataset and select any number of variables you want to analyse. "
    "The system detects variable types and uses predefined rules to generate "
    "a compact dashboard and identify relationships between its visualisations."
)
analysis_start_time = time.perf_counter()


def style_figure(fig, height=430):
    fig.update_layout(
        template="plotly_white", height=height, title={"x": 0.5, "xanchor": "center"},
        margin=dict(l=45, r=30, t=70, b=45), legend_title_text=""
    )
    fig.update_xaxes(showgrid=False, automargin=True)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)", automargin=True)
    return fig


def parse_temporal_series(series):
    return pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)


def detect_variable_type(series):
    if pd.api.types.is_numeric_dtype(series):
        return "Numerical"
    non_null = series.dropna()
    if len(non_null):
        try:
            if parse_temporal_series(non_null).notna().mean() >= 0.80:
                return "Temporal"
        except Exception:
            pass
    return "Categorical"


def add_dashboard_chart(charts, title, fig, reason, rule, variables):
    charts.append({
        "title": title, "figure": style_figure(fig, 390), "reason": reason,
        "rule": rule, "variables": list(variables)
    })


def generate_dashboard_charts(data, selected_columns, variable_types, max_charts=4):
    charts, used = [], set()
    nums = [c for c in selected_columns if variable_types[c] == "Numerical"]
    cats = [c for c in selected_columns if variable_types[c] == "Categorical"]
    temps = [c for c in selected_columns if variable_types[c] == "Temporal"]

    def room(sig):
        return len(charts) < max_charts and sig not in used

    def add(sig, title, fig, reason, rule):
        if room(sig):
            add_dashboard_chart(charts, title, fig, reason, rule, sig[1:])
            used.add(sig)

    def top_categories(frame, column, n):
        return frame[frame[column].isin(frame[column].value_counts().head(n).index)]

    # Three-variable rules
    for t in temps:
        for n in nums:
            for c in cats:
                if len(charts) >= max_charts:
                    break
                sig = ("temp_num_cat", t, n, c)
                if not room(sig):
                    continue
                p = data[[t, n, c]].copy()
                p[t] = parse_temporal_series(p[t])
                p = p.dropna()
                if p.empty:
                    continue
                p = top_categories(p, c, 8)
                grouped = p.groupby([t, c])[n].mean().reset_index()
                title = f"{n} over {t} by {c}"
                add(
                    sig, title,
                    px.line(grouped, x=t, y=n, color=c, markers=True, title=title),
                    "One temporal, one numerical and one categorical variable are available, so a multi-series line chart is used to compare numerical trends across categories over time.",
                    "Temporal + Numerical + Categorical -> Multi-series Line Chart"
                )
            if len(charts) >= max_charts:
                break
        if len(charts) >= max_charts:
            break

    for x, y in combinations(nums, 2):
        for c in cats:
            if len(charts) >= max_charts:
                break
            sig = ("num_num_cat", x, y, c)
            if not room(sig):
                continue
            p = data[[x, y, c]].dropna()
            if p.empty:
                continue
            p = top_categories(p, c, 8)
            title = f"{x} vs {y} by {c}"
            add(
                sig, title, px.scatter(p, x=x, y=y, color=c, opacity=0.7, title=title),
                "Two numerical variables and one categorical variable are available, so a grouped scatter plot is used to compare the numerical relationship across categories.",
                "Numerical + Numerical + Categorical -> Grouped Scatter Plot"
            )
        if len(charts) >= max_charts:
            break

    for x, y, size in combinations(nums, 3):
        if len(charts) >= max_charts:
            break
        sig = ("three_num", x, y, size)
        if not room(sig):
            continue
        p = data[[x, y, size]].dropna()
        if p.empty or not (p[size] >= 0).all():
            continue
        title = f"{x} vs {y}, sized by {size}"
        add(
            sig, title, px.scatter(p, x=x, y=y, size=size, opacity=0.7, title=title),
            "Three numerical variables are available, so a bubble chart uses two variables on the axes and the third as marker size.",
            "3 Numerical -> Bubble Chart"
        )

    # Two-variable rules
    for t in temps:
        for n in nums:
            if len(charts) >= max_charts:
                break
            sig = ("temp_num", t, n)
            if not room(sig):
                continue
            p = data[[t, n]].copy()
            p[t] = parse_temporal_series(p[t])
            p = p.dropna()
            if p.empty:
                continue
            grouped = p.groupby(t)[n].mean().reset_index().sort_values(t)
            title = f"{n} over {t}"
            add(
                sig, title, px.line(grouped, x=t, y=n, markers=True, title=title),
                "A temporal and a numerical variable are available, so a line chart is used to show change over time.",
                "Temporal + Numerical -> Line Chart"
            )
        if len(charts) >= max_charts:
            break

    for c in cats:
        for n in nums:
            if len(charts) >= max_charts:
                break
            sig = ("cat_num", c, n)
            if not room(sig):
                continue
            p = data[[c, n]].dropna()
            if p.empty:
                continue
            grouped = p.groupby(c)[n].mean().reset_index().sort_values(n, ascending=False).head(15)
            title = f"Average {n} by {c}"
            add(
                sig, title,
                px.bar(grouped, x=c, y=n, title=title, labels={n: f"Average {n}"}),
                "A categorical and a numerical variable are available, so a bar chart is used for category-based comparison.",
                "Categorical + Numerical -> Bar Chart"
            )
        if len(charts) >= max_charts:
            break

    for x, y in combinations(nums, 2):
        if len(charts) >= max_charts:
            break
        sig = ("num_num", x, y)
        if not room(sig):
            continue
        p = data[[x, y]].dropna()
        if p.empty:
            continue
        title = f"{x} vs {y}"
        add(
            sig, title, px.scatter(p, x=x, y=y, opacity=0.7, title=title),
            "Two numerical variables are available, so a scatter plot is used to examine their relationship.",
            "Numerical + Numerical -> Scatter Plot"
        )

    for c1, c2 in combinations(cats, 2):
        if len(charts) >= max_charts:
            break
        sig = ("cat_cat", c1, c2)
        if not room(sig):
            continue
        p = data[[c1, c2]].dropna()
        if p.empty:
            continue
        p = top_categories(p, c1, 12)
        grouped = p.groupby([c1, c2]).size().reset_index(name="Count")
        title = f"{c1} by {c2}"
        add(
            sig, title,
            px.bar(grouped, x=c1, y="Count", color=c2, barmode="group", title=title),
            "Two categorical variables are available, so a grouped bar chart is used to compare category combinations.",
            "Categorical + Categorical -> Grouped Bar Chart"
        )

    for t in temps:
        for c in cats:
            if len(charts) >= max_charts:
                break
            sig = ("temp_cat", t, c)
            if not room(sig):
                continue
            p = data[[t, c]].copy()
            p[t] = parse_temporal_series(p[t])
            p = p.dropna()
            if p.empty:
                continue
            p = top_categories(p, c, 8)
            grouped = p.groupby([t, c]).size().reset_index(name="Count")
            title = f"{c} over {t}"
            add(
                sig, title,
                px.line(grouped, x=t, y="Count", color=c, markers=True, title=title),
                "A temporal and a categorical variable are available, so a multi-series line chart is used to compare category frequencies over time.",
                "Temporal + Categorical -> Multi-series Line Chart"
            )
        if len(charts) >= max_charts:
            break

    # Single-variable fallback rules
    for n in nums:
        if len(charts) >= max_charts:
            break
        sig = ("single_num", n)
        if not room(sig) or data[n].dropna().empty:
            continue
        title = f"Distribution of {n}"
        add(
            sig, title, px.histogram(data, x=n, nbins=30, title=title),
            "A numerical variable is available, so a histogram is used to show its distribution.",
            "Numerical -> Histogram"
        )

    for c in cats:
        if len(charts) >= max_charts:
            break
        sig = ("single_cat", c)
        if not room(sig):
            continue
        counts = data[c].fillna("Missing").astype(str).value_counts().head(15).reset_index()
        if counts.empty:
            continue
        counts.columns = [c, "Count"]
        title = f"Frequency of {c}"
        add(
            sig, title, px.bar(counts, x=c, y="Count", title=title, labels={"Count": "Frequency"}),
            "A categorical variable is available, so a bar chart is used to compare category frequencies.",
            "Categorical -> Bar Chart"
        )

    for t in temps:
        if len(charts) >= max_charts:
            break
        sig = ("single_temp", t)
        if not room(sig):
            continue
        p = data[[t]].copy()
        p[t] = parse_temporal_series(p[t])
        p = p.dropna()
        if p.empty:
            continue
        counts = p.groupby(t).size().reset_index(name="Count").sort_values(t)
        title = f"Observations over {t}"
        add(
            sig, title, px.line(counts, x=t, y="Count", markers=True, title=title),
            "A temporal variable is available, so a line chart is used to show observations over time.",
            "Temporal -> Line Chart"
        )

    return charts[:max_charts]


def build_dashboard_relationships(charts):
    relationships = []
    for i, j in combinations(range(len(charts)), 2):
        shared = sorted(set(charts[i]["variables"]) & set(charts[j]["variables"]))
        if shared:
            relationships.append({"source": i, "target": j, "shared_variables": shared})
    return relationships


def create_dashboard_network_figure(charts, relationships):
    if not charts:
        return None
    count = len(charts)
    positions = {
        i: (math.cos(2 * math.pi * i / count - math.pi / 2), math.sin(2 * math.pi * i / count - math.pi / 2))
        for i in range(count)
    }
    edge_x, edge_y = [], []
    for r in relationships:
        sx, sy = positions[r["source"]]
        tx, ty = positions[r["target"]]
        edge_x += [sx, tx, None]
        edge_y += [sy, ty, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines", hoverinfo="skip",
        line=dict(width=1.5, color="rgba(80,80,80,0.55)")
    )
    node_x, node_y, node_text, node_hover = [], [], [], []
    for i, chart in enumerate(charts):
        x, y = positions[i]
        node_x.append(x); node_y.append(y); node_text.append(f"Chart {i + 1}")
        node_hover.append(f"<b>Chart {i + 1}</b><br>{chart['title']}<br>Variables: {', '.join(chart['variables'])}")
    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=node_text,
        textposition="bottom center", hovertext=node_hover, hoverinfo="text",
        marker=dict(size=34, color="white", line=dict(width=2, color="black"))
    )
    fig = go.Figure(data=[edge_trace, node_trace])
    for r in relationships:
        sx, sy = positions[r["source"]]
        tx, ty = positions[r["target"]]
        fig.add_annotation(
            x=(sx + tx) / 2, y=(sy + ty) / 2, text=", ".join(r["shared_variables"]),
            showarrow=False, font=dict(size=11), bgcolor="white",
            bordercolor="rgba(120,120,120,0.45)", borderwidth=1
        )
    fig.update_layout(
        template="plotly_white", height=430, margin=dict(l=30, r=30, t=40, b=30),
        xaxis=dict(visible=False, range=[-1.35, 1.35]),
        yaxis=dict(visible=False, range=[-1.35, 1.35], scaleanchor="x", scaleratio=1),
        showlegend=False, hovermode="closest"
    )
    return fig


def show_chart(chart, index):
    st.markdown(f"#### {chart['title']}")
    st.plotly_chart(chart["figure"], use_container_width=True, key=f"dashboard_chart_{index}")
    with st.expander("Why this chart?"):
        st.write(chart["reason"])
        st.caption(chart["rule"])


# 1. Dataset upload
st.header("1. Upload Dataset")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file is None:
    st.info("Please upload a CSV file to begin.")
    st.stop()
try:
    df = pd.read_csv(uploaded_file)
    st.success("Dataset uploaded successfully.")
except Exception as e:
    st.error(f"Unable to read the CSV file: {e}")
    st.stop()
if df.empty:
    st.warning("The uploaded dataset is empty.")
    st.stop()

# 2. Dataset overview
st.header("2. Dataset Overview")
rows, columns = df.shape
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Rows", f"{rows:,}")
with col2:
    st.metric("Total Columns", columns)
PREVIEW_ROWS = PREVIEW_COLUMNS = 8
preview_df = df.iloc[:min(PREVIEW_ROWS, rows), :min(PREVIEW_COLUMNS, columns)]
st.subheader("Dataset Preview")
st.caption(
    f"Showing the first {min(PREVIEW_ROWS, rows)} rows and {min(PREVIEW_COLUMNS, columns)} columns of a dataset containing "
    f"{rows:,} rows × {columns} columns."
)
st.dataframe(preview_df, use_container_width=True, hide_index=True)
if columns > PREVIEW_COLUMNS:
    st.caption(f"Preview limited to the first {PREVIEW_COLUMNS} columns. The complete dataset contains {columns} columns.")

# 3. Data quality
st.header("3. Data Quality Check")
missing_counts = df.isnull().sum()
quality_messages = [f"'{c}' contains {missing_counts[c]} missing value(s)." for c in df.columns if missing_counts[c] > 0]
if quality_messages:
    st.warning("Potential data quality issues were detected. The system will continue where possible.")
    with st.expander("View data quality details"):
        for message in quality_messages:
            st.write(f"- {message}")
else:
    st.success("No obvious missing-data issues were detected.")

# 4. Variable type detection
st.header("4. Variable Type Detection")
auto_variable_types = {c: detect_variable_type(df[c]) for c in df.columns}
variable_types = auto_variable_types.copy()
type_table = pd.DataFrame({"Variable": list(auto_variable_types), "Detected Type": list(auto_variable_types.values())})
st.dataframe(type_table, use_container_width=True, hide_index=True)

# 5. Variable selection
st.header("5. Select Variables")
st.write(
    "Select the variables you are interested in analysing. You choose what data to analyse, while the system decides which "
    "visualisation is most appropriate."
)
selected_columns = st.multiselect("Select variables:", options=df.columns.tolist())
if not selected_columns:
    st.info("Select at least one variable to receive a visualisation recommendation.")
    st.stop()
st.subheader("Review Selected Variable Types")
st.write(
    "The system automatically detects each variable type. If a column is stored in a way that does not reflect its analytical "
    "meaning (for example, a numeric-coded category or identifier), you can correct its type before visualisation recommendations are generated."
)
type_options = ["Numerical", "Categorical", "Temporal"]
for c in selected_columns:
    detected = auto_variable_types[c]
    variable_types[c] = st.selectbox(
        f"{c}", options=type_options, index=type_options.index(detected), key=f"type_override_{c}",
        help=f"Automatically detected as {detected}. Change only if the column's analytical meaning is different."
    )
st.subheader("Selected Variables")
selected_type_df = pd.DataFrame({
    "Variable": selected_columns,
    "Auto-detected Type": [auto_variable_types[c] for c in selected_columns],
    "Analysis Type": [variable_types[c] for c in selected_columns]
})
st.dataframe(selected_type_df, use_container_width=True, hide_index=True)

# 6. Optional filters
st.header("6. Optional Data Filters")
st.caption("Filters are optional. They are applied only to the data used for visualisation and do not change the original uploaded dataset.")
filtered_df = df.copy()
selected_categorical_columns = [c for c in selected_columns if variable_types[c] == "Categorical"]
for c in selected_categorical_columns:
    values = filtered_df[c].dropna().astype(str).value_counts().index.tolist()
    if len(values) <= 100:
        chosen = st.multiselect(f"Filter categories for '{c}' (optional):", options=values, default=values, key=f"filter_{c}")
        if chosen:
            filtered_df = filtered_df[filtered_df[c].astype(str).isin(chosen)]
    else:
        st.caption(f"Category filter for '{c}' is not shown because the variable contains more than 100 unique values.")

selected_temporal_columns = [c for c in selected_columns if variable_types[c] == "Temporal"]
for c in selected_temporal_columns:
    temporal_values = parse_temporal_series(filtered_df[c]).dropna()
    if not temporal_values.empty:
        min_date, max_date = temporal_values.min().date(), temporal_values.max().date()
        date_range = st.date_input(
            f"Filter date range for '{c}' (optional):", value=(min_date, max_date),
            min_value=min_date, max_value=max_date, key=f"date_filter_{c}"
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range
            converted = parse_temporal_series(filtered_df[c])
            filtered_df = filtered_df[(converted.dt.date >= start_date) & (converted.dt.date <= end_date)]

if len(filtered_df) == 0:
    st.warning("The selected filters produced no rows. Please adjust the filters to continue.")
    st.stop()
elif len(filtered_df) < len(df):
    st.info(f"Filters applied: {len(filtered_df):,} of {len(df):,} rows will be used for the visualisation.")
else:
    st.caption(f"No rows were removed by the current filters. {len(filtered_df):,} rows will be used.")

# 7. Dashboard generation
st.header("7. Automatically Generated Dashboard")
st.write(
    "Select any number of variables. The selected variables are treated as a candidate pool, and the recommendation engine searches supported "
    "one-, two- and three-variable combinations to build a compact dashboard."
)
dashboard_charts = generate_dashboard_charts(filtered_df, selected_columns, variable_types, max_charts=4)
metric1, metric2, metric3 = st.columns(3)
with metric1:
    st.metric("Rows Used", f"{len(filtered_df):,}")
with metric2:
    st.metric("Variables Selected", len(selected_columns))
with metric3:
    st.metric("Charts Generated", len(dashboard_charts))

if not dashboard_charts:
    st.warning(
        "No supported visualisations could be generated from the current selection. Try choosing variables with numerical, categorical or "
        "temporal relationships supported by the rule base."
    )
else:
    st.subheader("Dashboard Visualisations")
    for index in range(0, len(dashboard_charts), 2):
        left_chart, right_chart = st.columns(2)
        with left_chart:
            show_chart(dashboard_charts[index], index)
        if index + 1 < len(dashboard_charts):
            with right_chart:
                show_chart(dashboard_charts[index + 1], index + 1)
    st.caption(
        "All dashboard visualisations use the same filtered dataset. There is no limit on the number of variables that may be selected; "
        "the dashboard displays up to four complementary charts to maintain readability."
    )

# 8. Dashboard network
st.header("8. Dashboard Network Relationships")
if len(dashboard_charts) < 2:
    st.info("At least two dashboard visualisations are required to construct visualisation relationships.")
else:
    dashboard_relationships = build_dashboard_relationships(dashboard_charts)
    st.write("Each dashboard visualisation is treated as a node. Two nodes are connected when their charts share one or more variables.")
    if dashboard_relationships:
        relationship_df = pd.DataFrame([
            {
                "Visualisation 1": f"Chart {r['source'] + 1}: {dashboard_charts[r['source']]['title']}",
                "Visualisation 2": f"Chart {r['target'] + 1}: {dashboard_charts[r['target']]['title']}",
                "Shared Variable(s)": ", ".join(r["shared_variables"])
            }
            for r in dashboard_relationships
        ])
        st.subheader("Visualisation Relationships")
        st.dataframe(relationship_df, use_container_width=True, hide_index=True)
        network_figure = create_dashboard_network_figure(dashboard_charts, dashboard_relationships)
        st.subheader("Dashboard Network")
        left_space, network_area, right_space = st.columns([1, 4, 1])
        with network_area:
            st.plotly_chart(network_figure, use_container_width=True, key="dashboard_network_figure")
        st.caption(
            "Edges indicate shared variables between dashboard visualisations. This relationship structure provides the network representation "
            "of the generated dashboard."
        )
    else:
        st.info("The generated visualisations do not currently share variables, so no network edges were created.")

# 9. Evaluation summary
analysis_time = time.perf_counter() - analysis_start_time
with st.expander("View analysis summary"):
    st.write(f"**Original dataset size:** {len(df):,} rows × {len(df.columns)} columns")
    st.write(f"**Rows used after filtering:** {len(filtered_df):,}")
    st.write(f"**Selected variables:** {len(selected_columns)}")
    st.write(f"**Dashboard charts generated:** {len(dashboard_charts)}")
    st.write(f"**Current processing time:** {analysis_time:.3f} seconds")
    st.caption("The processing time is provided as a lightweight measure to support later performance evaluation with datasets of different sizes.")

# 10. Recommendation rules
with st.expander("View recommendation rules"):
    st.write("The recommendation engine uses the following mappings when constructing the dashboard:")
    rules_df = pd.DataFrame({
        "Selected Variable Types": [
            "1 Numerical", "1 Categorical", "1 Temporal", "Numerical + Numerical", "Categorical + Numerical",
            "Temporal + Numerical", "Categorical + Categorical", "Temporal + Categorical",
            "Temporal + Numerical + Categorical", "Numerical + Numerical + Categorical", "3 Numerical"
        ],
        "Recommended Visualisation": [
            "Histogram", "Bar Chart", "Line Chart", "Scatter Plot", "Bar Chart", "Line Chart", "Grouped Bar Chart",
            "Multi-series Line Chart", "Multi-series Line Chart", "Grouped Scatter Plot", "Bubble Chart"
        ]
    })
    st.dataframe(rules_df, use_container_width=True, hide_index=True)

st.success("Dashboard network analysis completed. You can change the selected variables or filters to generate another dashboard network.")