import streamlit as st
import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from database.models import init_db
from database.crud import (
    register_camera, get_all_cameras, get_camera,
    get_all_sightings, get_sightings_by_camera,
    clear_camera_sightings, delete_camera,
    get_all_investigations
)
from core.processor import process_video
from nlp.query_parser import parse_query
from investigation.multi_camera import run_investigation
from investigation.timeline import (
    build_timeline_chart, build_relation_graph, build_comparison_table
)
from alerts.notifier import send_alert, build_alert_body

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VideoGPT - Intelligent Surveillance",
    page_icon="camera",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0e1117; }
[data-testid="stSidebar"] { background-color: #1a1a2e; }
.stButton>button {
    background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
    color:white; border:none; border-radius:8px;
    padding:0.5rem 1.2rem; font-weight:bold;
}
.stButton>button:hover { opacity:0.85; }
h1,h2,h3 { color:#00FF88 !important; }
.metric-card {
    background:#1a1a2e; border-radius:10px; padding:15px;
    border-left:4px solid #667eea; margin:5px;
}
.found-box {
    background:#001a00; border:2px solid #00FF88;
    border-radius:10px; padding:15px; margin:10px 0;
}
.notfound-box {
    background:#1a0000; border:2px solid #FF4444;
    border-radius:10px; padding:15px; margin:10px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Initialise DB ─────────────────────────────────────────────────────────────
init_db()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## VideoGPT")
    st.markdown("*Intelligent Surveillance Analysis*")
    st.divider()
    page = st.radio("Navigate", [
        "Dashboard",
        "Camera Manager",
        "Process Videos",
        "Search and Query",
        "Multi-Camera Investigation",
        "Analytics",
        "Event Logs"
    ])
    st.divider()
    st.caption("BSc CSE Final Year Project")
    st.caption("MUST Mirpur | 2026")
    st.caption("Aleena Khurshid | Huma Nazr")


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.title("VideoGPT Dashboard")
    st.markdown(
        "*Intelligent Video Surveillance Analysis Using "
        "Computer Vision and Natural Language Queries*"
    )
    st.divider()

    all_s   = get_all_sightings()
    all_c   = get_all_cameras()
    all_inv = get_all_investigations()
    plates  = set(s.plate_number for s in all_s if s.plate_number != "UNKNOWN")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cameras Registered", len(all_c))
    c2.metric("Total Sightings",    len(all_s))
    c3.metric("Unique Plates",      len(plates))
    c4.metric("Investigations Run",  len(all_inv))

    st.divider()
    st.subheader("Quick Search")
    q = st.text_input(
        "Type your query:",
        placeholder=(
            'Try: "show red cars in gate1"  or  '
            '"investigate ABC-1234 in gate1 gate3"'
        )
    )
    if st.button("Search") and q:
        with st.spinner("Analysing..."):
            parsed = parse_query(q)
            result = run_investigation(parsed)
        st.success(result.get("summary", "Done."))
        if result["type"] == "search":
            rows = result.get("results", [])
            if rows:
                df = pd.DataFrame(rows)
                cols = [c for c in
                        ["camera_id","plate","vehicle_type",
                         "color","timestamp_video","direction"]
                        if c in df.columns]
                st.dataframe(df[cols], use_container_width=True)
            else:
                st.info("No results found.")
        else:
            tl = result.get("timeline", [])
            if tl:
                st.dataframe(pd.DataFrame(tl), use_container_width=True)

    st.divider()
    st.subheader("Registered Cameras")
    if not all_c:
        st.info("No cameras yet. Go to Camera Manager.")
    for cam in all_c:
        ca, cb = st.columns([4, 1])
        with ca:
            st.markdown(f"**{cam.camera_id.upper()}** - {cam.location}")
            st.caption(f"{cam.video_path}")
        with cb:
            cnt = len(get_sightings_by_camera(cam.camera_id))
            st.metric("Sightings", cnt)


# ══════════════════════════════════════════════════════════════════════════════
# CAMERA MANAGER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Camera Manager":
    st.title("Camera Manager")
    st.markdown("Register and manage camera gates.")
    st.divider()

    with st.expander("Add or Update Camera", expanded=True):
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            cam_id   = st.text_input("Camera ID",
                                     placeholder="gate1",
                                     help="e.g. gate1, gate2, gate3")
            location = st.text_input("Location",
                                     placeholder="Main Entrance")
        with r1c2:
            description = st.text_area("Description",
                                       placeholder="CCTV camera at main gate",
                                       height=80)
            video_path  = st.text_input(
                "Video File Path",
                placeholder="data/videos/gate1/footage.mp4"
            )
        if st.button("Save Camera"):
            if cam_id and video_path:
                register_camera(
                    cam_id.lower().strip(),
                    location, description, video_path
                )
                st.success(f"Camera '{cam_id}' saved.")
                st.rerun()
            else:
                st.error("Camera ID and Video Path are required.")

    st.divider()
    st.subheader("Registered Cameras")
    cameras = get_all_cameras()
    if not cameras:
        st.info("No cameras registered yet.")
    else:
        for cam in cameras:
            with st.container():
                ca, cb, cc = st.columns([3, 2, 1])
                with ca:
                    st.markdown(f"### {cam.camera_id.upper()}")
                    st.caption(f"Location: {cam.location}")
                    st.caption(f"Video: {cam.video_path}")
                    exists = os.path.exists(cam.video_path)
                    st.caption(f"File: {'Found' if exists else 'Not Found'}")
                with cb:
                    cnt = len(get_sightings_by_camera(cam.camera_id))
                    st.metric("Sightings", cnt)
                with cc:
                    if st.button("Delete", key=f"del_{cam.camera_id}"):
                        delete_camera(cam.camera_id)
                        st.rerun()
                    if st.button("Clear Data", key=f"clr_{cam.camera_id}"):
                        clear_camera_sightings(cam.camera_id)
                        st.success("Cleared.")
                        st.rerun()
                st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# PROCESS VIDEOS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Process Videos":
    st.title("Process Videos")
    st.markdown(
        "Run the AI detection pipeline (YOLO + ALPR + Color) "
        "on registered camera videos."
    )
    st.divider()

    cameras = get_all_cameras()
    if not cameras:
        st.warning("No cameras registered. Go to Camera Manager first.")
    else:
        cam_map  = {cam.camera_id: cam for cam in cameras}
        selected = st.multiselect(
            "Select cameras to process:",
            options=list(cam_map.keys()),
            default=list(cam_map.keys())[:1]
        )

        pc1, pc2 = st.columns(2)
        with pc1:
            frame_skip = st.slider(
                "Frame Skip (higher = faster, less detail)", 1, 30, 5)
        with pc2:
            conf_thresh = st.slider(
                "Detection Confidence Threshold", 0.1, 0.9, 0.45, 0.05)

        if st.button("Start Processing", type="primary"):
            if not selected:
                st.error("Select at least one camera.")
            else:
                for cam_id in selected:
                    cam = cam_map[cam_id]
                    if not os.path.exists(cam.video_path):
                        st.error(
                            f"{cam_id}: Video not found at {cam.video_path}")
                        continue

                    st.markdown(f"### Processing {cam_id.upper()}...")
                    pb   = st.progress(0)
                    stat = st.empty()

                    def make_cb(pb_ref, stat_ref, cid):
                        def cb(pct):
                            pb_ref.progress(min(pct, 99))
                            stat_ref.text(f"{cid}: {pct}% complete")
                        return cb

                    os.environ["FRAME_SKIP"]           = str(frame_skip)
                    os.environ["CONFIDENCE_THRESHOLD"] = str(conf_thresh)

                    with st.spinner(f"Running on {cam_id}..."):
                        res = process_video(
                            cam_id, cam.video_path,
                            make_cb(pb, stat, cam_id)
                        )

                    pb.progress(100)
                    if "error" in res:
                        st.error(f"Error: {res['error']}")
                    else:
                        st.success(
                            f"{cam_id} complete. "
                            f"Frames: {res['frames_processed']} | "
                            f"Detections: {res['detections']} | "
                            f"Time: {res['elapsed_sec']}s"
                        )

        st.divider()
        st.subheader("Camera Status")
        for cam in cameras:
            cnt = len(get_sightings_by_camera(cam.camera_id))
            sc1, sc2, sc3 = st.columns([2, 1, 1])
            sc1.text(cam.camera_id)
            sc2.text(f"{cnt} sightings")
            sc3.text("Processed" if cnt > 0 else "Not yet processed")


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH AND QUERY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Search and Query":
    st.title("Natural Language Search")
    st.markdown(
        "Search surveillance data using plain English. "
        "Powered by Groq LLM + YOLOv8 + EasyOCR."
    )
    st.divider()

    examples = [
        "",
        "Show all red cars in gate1",
        "Find white trucks in gate2 and gate3",
        "Show motorcycles entering gate1",
        "Find blue vehicles in gate3",
        "Show all buses",
    ]
    chosen = st.selectbox("Example queries:", examples)
    query  = st.text_input(
        "Your query:", value=chosen,
        placeholder="e.g. show red cars entering gate1"
    )

    if st.button("Search", type="primary") and query:
        with st.spinner("Parsing query with LLM..."):
            parsed = parse_query(query)

        st.markdown("**Parsed Parameters:**")
        st.json(parsed)

        with st.spinner("Searching database..."):
            result = run_investigation(parsed)

        st.divider()
        st.success(result.get("summary", "Done."))

        if result["type"] == "search":
            rows = result.get("results", [])
            if not rows:
                st.info("No matching vehicles found.")
            else:
                df = pd.DataFrame(rows)
                show = [c for c in
                        ["camera_id","plate","vehicle_type","color",
                         "timestamp_video","direction","timestamp_real"]
                        if c in df.columns]
                st.dataframe(df[show], use_container_width=True)

                frame_items = [r for r in rows
                               if r.get("frame_path") and
                               os.path.exists(r["frame_path"])]
                if frame_items:
                    st.subheader("Evidence Frames")
                    img_cols = st.columns(min(3, len(frame_items)))
                    for idx, item in enumerate(frame_items[:6]):
                        with img_cols[idx % 3]:
                            st.image(
                                item["frame_path"],
                                caption=(
                                    f"{item['camera_id']} | "
                                    f"{item['plate']} | "
                                    f"{item['timestamp_video']:.1f}s"
                                ),
                                use_column_width=True
                            )


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-CAMERA INVESTIGATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Multi-Camera Investigation":
    st.title("Multi-Camera Investigation")
    st.markdown(
        "Trace a vehicle across multiple camera gates. "
        "Build timeline, compare plates, view relation graph, send alerts."
    )
    st.divider()

    cameras = get_all_cameras()
    cam_ids = [c.camera_id for c in cameras] if cameras else \
              ["gate1", "gate2", "gate3"]

    st.subheader("Investigation Parameters")
    ic1, ic2 = st.columns([2, 1])
    with ic1:
        nl_q = st.text_input(
            "Natural Language Query:",
            placeholder=(
                'e.g. "investigate theft car ABC-1234 '
                'in gate1 gate2 gate3"'
            )
        )
    with ic2:
        plate_direct = st.text_input(
            "Or enter plate directly:", placeholder="ABC-1234")

    sel_gates = st.multiselect(
        "Select Gates to Investigate:",
        options=cam_ids,
        default=cam_ids[:min(3, len(cam_ids))]
    )

    chk1, chk2, chk3 = st.columns(3)
    with chk1:
        send_email = st.checkbox("Send Gmail Alert", value=False)
    with chk2:
        st.checkbox("Auto-play clips", value=True)
    with chk3:
        inv_btn = st.button("Start Investigation", type="primary")

    if inv_btn:
        if nl_q:
            with st.spinner("Parsing query..."):
                parsed = parse_query(nl_q)
            if sel_gates and not parsed.get("cameras"):
                parsed["cameras"] = sel_gates
        elif plate_direct:
            parsed = {
                "action":  "investigate",
                "plate":   plate_direct.upper().strip(),
                "cameras": sel_gates
            }
        else:
            st.error("Enter a query or plate number.")
            st.stop()

        st.markdown("**Parsed:**")
        st.json(parsed)
        st.divider()

        with st.spinner("Running multi-camera investigation..."):
            result = run_investigation(parsed)

        plate    = result.get("plate", "N/A")
        found    = result.get("cameras_found", [])
        searched = result.get("cameras_searched", [])
        match    = result.get("match_pct", 0)
        timeline = result.get("timeline", [])
        gaps     = result.get("gaps", [])

        # Summary
        if found:
            st.markdown(f"""
            <div class="found-box">
            <h3>Vehicle Found</h3>
            <p><strong>Plate:</strong> {plate} &nbsp;|&nbsp;
               <strong>Found in:</strong> {", ".join(found)} &nbsp;|&nbsp;
               <strong>Match:</strong> {match}%</p>
            <p>{result.get("summary","")}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="notfound-box">
            <h3>Vehicle Not Found</h3>
            <p>Plate <strong>{plate}</strong> was not detected
               in the selected cameras.</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Plate",          plate)
        m2.metric("Cameras Found",  f"{len(found)}/{len(searched)}")
        m3.metric("Match Score",    f"{match}%")
        m4.metric("Total Sightings", result.get("total_sightings", 0))
        st.divider()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Timeline",
            "Relation Graph",
            "Plate Comparison",
            "Evidence Frames",
            "Alerts"
        ])

        with tab1:
            st.subheader("Investigation Timeline")
            fig_tl = build_timeline_chart(timeline, plate)
            st.plotly_chart(fig_tl, use_container_width=True)
            if timeline:
                df_tl  = pd.DataFrame(timeline)
                show   = [c for c in
                          ["camera_id","plate","vehicle_type","color",
                           "timestamp_video","direction","timestamp_real"]
                          if c in df_tl.columns]
                st.dataframe(df_tl[show], use_container_width=True)

        with tab2:
            st.subheader("Camera Relation Graph")
            if searched:
                st.plotly_chart(
                    build_relation_graph(result),
                    use_container_width=True
                )
            if gaps:
                st.subheader("Travel Time Between Gates")
                for g in gaps:
                    st.markdown(
                        f"**{g['from'].upper()}** to "
                        f"**{g['to'].upper()}** : {g['gap_str']} "
                        f"({g['gap_seconds']}s)"
                    )

        with tab3:
            st.subheader("Plate Comparison Matrix")
            df_comp = build_comparison_table(result)
            if not df_comp.empty:
                st.dataframe(df_comp, use_container_width=True)

            if searched:
                st.subheader("Detection Status per Gate")
                gcols = st.columns(len(searched))
                for i, cam in enumerate(searched):
                    is_found = cam in found
                    color    = "#00FF88" if is_found else "#FF4444"
                    status   = "FOUND" if is_found else "NOT DETECTED"
                    with gcols[i]:
                        st.markdown(f"""
                        <div style="text-align:center;
                                    background:#1a1a2e;
                                    border-radius:10px;
                                    padding:20px;
                                    border:2px solid {color}">
                        <h3 style="color:white">{cam.upper()}</h3>
                        <h2 style="color:{color}">{status}</h2>
                        </div>
                        """, unsafe_allow_html=True)

        with tab4:
            st.subheader("Evidence Frames")
            frames = [t for t in timeline
                      if t.get("frame_path") and
                      os.path.exists(t["frame_path"])]
            if frames:
                fc = st.columns(min(3, len(frames)))
                for idx, item in enumerate(frames[:9]):
                    with fc[idx % 3]:
                        st.image(
                            item["frame_path"],
                            caption=(
                                f"{item['camera_id'].upper()} | "
                                f"{item['plate']} | "
                                f"{item['timestamp_video']:.1f}s"
                            ),
                            use_column_width=True
                        )
            else:
                st.info(
                    "No saved frames available. "
                    "Process videos first to generate evidence frames."
                )

        with tab5:
            st.subheader("Alerts and Logging")
            alert_body = build_alert_body(result)
            st.text_area("Alert Preview:", value=alert_body, height=200)

            al1, al2 = st.columns(2)
            with al1:
                if st.button("Send Gmail Alert"):
                    subj = f"VideoGPT Alert - Vehicle {plate} Detected"
                    ok   = send_alert(subj, alert_body)
                    if ok:
                        st.success("Alert sent.")
                    else:
                        st.error(
                            "Alert failed. Check Gmail credentials in .env")
            with al2:
                st.download_button(
                    "Download Report",
                    data=alert_body,
                    file_name=(
                        f"investigation_{plate}_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    ),
                    mime="text/plain"
                )


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Analytics":
    st.title("Analytics Dashboard")
    st.divider()

    all_s = get_all_sightings()
    if not all_s:
        st.info("No data yet. Process some videos first.")
    else:
        import plotly.express as px

        df = pd.DataFrame([{
            "camera_id":    s.camera_id,
            "vehicle_type": s.vehicle_type,
            "vehicle_color":s.vehicle_color,
            "direction":    s.direction,
            "plate":        s.plate_number,
            "timestamp":    s.timestamp_video
        } for s in all_s])

        ac1, ac2 = st.columns(2)
        with ac1:
            st.subheader("Vehicles by Type")
            fig1 = px.pie(df, names="vehicle_type",
                          color_discrete_sequence=px.colors.qualitative.Set3)
            fig1.update_layout(paper_bgcolor="#0e1117", font_color="white")
            st.plotly_chart(fig1, use_container_width=True)

        with ac2:
            st.subheader("Vehicles by Color")
            vc = df["vehicle_color"].value_counts().reset_index()
            vc.columns = ["color", "count"]
            fig2 = px.bar(vc, x="color", y="count",
                          color="color",
                          color_discrete_sequence=px.colors.qualitative.Bold)
            fig2.update_layout(paper_bgcolor="#0e1117", font_color="white",
                               plot_bgcolor="#0e1117")
            st.plotly_chart(fig2, use_container_width=True)

        ac3, ac4 = st.columns(2)
        with ac3:
            st.subheader("Detections per Camera")
            cc = df["camera_id"].value_counts().reset_index()
            cc.columns = ["camera", "count"]
            fig3 = px.bar(cc, x="camera", y="count", color="camera",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig3.update_layout(paper_bgcolor="#0e1117", font_color="white",
                               plot_bgcolor="#0e1117")
            st.plotly_chart(fig3, use_container_width=True)

        with ac4:
            st.subheader("Entry vs Exit")
            fig4 = px.pie(
                df, names="direction",
                color_discrete_map={
                    "entering": "#00FF88",
                    "exiting":  "#FF4444",
                    "unknown":  "#888888"
                }
            )
            fig4.update_layout(paper_bgcolor="#0e1117", font_color="white")
            st.plotly_chart(fig4, use_container_width=True)

        st.subheader("Detection Timeline")
        fig5 = px.histogram(
            df, x="timestamp", color="camera_id",
            nbins=50, barmode="overlay",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig5.update_layout(paper_bgcolor="#0e1117", font_color="white",
                           plot_bgcolor="#0e1117")
        st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# EVENT LOGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Event Logs":
    st.title("Event Logs")
    st.divider()

    t_sight, t_inv = st.tabs(["Vehicle Sightings", "Investigations"])

    with t_sight:
        all_s = get_all_sightings()
        if not all_s:
            st.info("No sightings yet.")
        else:
            df = pd.DataFrame([{
                "ID":           s.id,
                "Camera":       s.camera_id,
                "Plate":        s.plate_number,
                "Type":         s.vehicle_type,
                "Color":        s.vehicle_color,
                "Direction":    s.direction,
                "Video Time s": s.timestamp_video,
                "Timestamp":    (s.timestamp_real.strftime("%Y-%m-%d %H:%M:%S")
                                 if s.timestamp_real else ""),
                "Plate Conf":   f"{s.plate_confidence:.2f}"
            } for s in all_s])

            lc1, lc2, lc3 = st.columns(3)
            with lc1:
                cf = st.multiselect("Camera", df["Camera"].unique().tolist())
            with lc2:
                tf = st.multiselect("Type",   df["Type"].unique().tolist())
            with lc3:
                pf = st.text_input("Plate contains")

            fdf = df.copy()
            if cf:
                fdf = fdf[fdf["Camera"].isin(cf)]
            if tf:
                fdf = fdf[fdf["Type"].isin(tf)]
            if pf:
                fdf = fdf[fdf["Plate"].str.contains(
                    pf.upper(), na=False)]

            st.metric("Records", f"{len(fdf)} / {len(df)}")
            st.dataframe(fdf, use_container_width=True, height=460)
            st.download_button(
                "Export CSV",
                data=fdf.to_csv(index=False),
                file_name="sightings.csv",
                mime="text/csv"
            )

    with t_inv:
        all_inv = get_all_investigations()
        if not all_inv:
            st.info("No investigations yet.")
        else:
            for inv in all_inv:
                ts = (inv.created_at.strftime("%Y-%m-%d %H:%M")
                      if inv.created_at else "")
                label = (inv.query_text or "")[:70]
                with st.expander(f"[{ts}] {label}"):
                    st.text(f"Query : {inv.query_text}")
                    st.text(f"Params: {inv.parsed_params}")
                    st.text(f"Result: {inv.result_summary}")
                    st.text(f"Alert : {inv.alert_sent}")
