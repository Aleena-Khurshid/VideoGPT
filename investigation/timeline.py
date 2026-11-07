import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd


def build_timeline_chart(timeline: list, plate: str) -> go.Figure:
    if not timeline:
        fig = go.Figure()
        fig.add_annotation(text="No sightings found", showarrow=False,
                           font=dict(size=18, color="gray"))
        fig.update_layout(title=f"Timeline - {plate}",
                          plot_bgcolor="#0e1117",
                          paper_bgcolor="#0e1117",
                          font_color="white")
        return fig

    df = pd.DataFrame(timeline)
    cameras = sorted(df["camera_id"].unique())
    cam_y   = {c: i for i, c in enumerate(cameras)}
    df["y_pos"] = df["camera_id"].map(cam_y)
    colors  = px.colors.qualitative.Set1

    fig = go.Figure()
    for i, cam in enumerate(cameras):
        sub = df[df["camera_id"] == cam]
        direction_val = sub["direction"].iloc[0] if len(sub) > 0 else ""
        fig.add_trace(go.Scatter(
            x=sub["timestamp_video"],
            y=sub["y_pos"],
            mode="markers+text",
            name=cam,
            marker=dict(size=16, color=colors[i % len(colors)],
                        symbol="circle",
                        line=dict(width=2, color="white")),
            text=sub["plate"],
            textposition="top center",
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"Camera: {cam}<br>"
                "Time: %{x:.1f}s<br>"
                f"Direction: {direction_val}<extra></extra>"
            )
        ))

    sorted_tl = sorted(timeline, key=lambda x: x["timestamp_video"])
    for i in range(len(sorted_tl) - 1):
        p1, p2 = sorted_tl[i], sorted_tl[i + 1]
        fig.add_shape(
            type="line",
            x0=p1["timestamp_video"], y0=cam_y[p1["camera_id"]],
            x1=p2["timestamp_video"], y1=cam_y[p2["camera_id"]],
            line=dict(color="rgba(255,255,100,0.4)", width=2, dash="dot")
        )

    fig.update_layout(
        title=dict(text=f"Investigation Timeline - Plate: {plate}",
                   font=dict(size=18, color="white")),
        xaxis=dict(title="Video Timestamp (seconds)", color="white",
                   gridcolor="#2a2a2a"),
        yaxis=dict(tickvals=list(cam_y.values()),
                   ticktext=list(cam_y.keys()),
                   color="white", gridcolor="#2a2a2a"),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="white",
        legend=dict(bgcolor="#1a1a1a", bordercolor="#444"),
        height=420
    )
    return fig


def build_relation_graph(result: dict) -> go.Figure:
    G = nx.DiGraph()
    cameras_searched = result.get("cameras_searched", [])
    cameras_found    = result.get("cameras_found", [])
    gaps             = result.get("gaps", [])
    plate            = result.get("plate", "")

    for cam in cameras_searched:
        G.add_node(cam, found=(cam in cameras_found))
    for gap in gaps:
        G.add_edge(gap["from"], gap["to"], label=gap["gap_str"])

    pos = nx.spring_layout(G, seed=42, k=2)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color="#FFD700"),
        hoverinfo="none", mode="lines"
    )

    node_x      = [pos[n][0] for n in G.nodes()]
    node_y      = [pos[n][1] for n in G.nodes()]
    node_colors = ["#00FF88" if G.nodes[n]["found"] else "#FF4444"
                   for n in G.nodes()]
    node_text   = [f"{'YES' if G.nodes[n]['found'] else 'NO'} {n}"
                   for n in G.nodes()]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=node_text,
        textposition="bottom center",
        marker=dict(size=30, color=node_colors,
                    line=dict(width=2, color="white"))
    )

    annotations = []
    for u, v, data in G.edges(data=True):
        mx = (pos[u][0] + pos[v][0]) / 2
        my = (pos[u][1] + pos[v][1]) / 2
        annotations.append(dict(
            x=mx, y=my,
            text=f"{data.get('label', '')}",
            showarrow=False,
            font=dict(color="#FFD700", size=12),
            bgcolor="rgba(0,0,0,0.5)"
        ))

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(text=f"Camera Relation Graph - {plate}",
                       font=dict(size=16, color="white")),
            showlegend=False,
            hovermode="closest",
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            font_color="white",
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=420
        )
    )
    return fig


def build_comparison_table(result: dict) -> pd.DataFrame:
    comparison = result.get("comparison", {})
    rows = []
    for cam, info in comparison.items():
        rows.append({
            "Camera":      cam,
            "Plate Found": "YES" if info["found"] else "NO",
            "Sightings":   info["sighting_count"],
            "Plates Seen": ", ".join(info["plates"]) if info["plates"] else "-"
        })
    return pd.DataFrame(rows)
