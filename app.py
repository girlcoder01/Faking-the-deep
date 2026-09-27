```python
import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components

if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

from combined_detect import analyze_combined

LOGO_PATH = "assets/logo.png" if os.path.exists("assets/logo.png") else "logo.png"
HAS_LOGO = os.path.exists(LOGO_PATH)

st.set_page_config(
    page_title="Faking the Deep",
    page_icon=LOGO_PATH if HAS_LOGO else "🔍",
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&display=swap');

    .stApp {
        background: linear-gradient(145deg, #fbf7ff 0%, #f1f5fe 50%, #fff1f6 100%);
        font-family: 'Quicksand', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #4a4063;
    }

    h1 {
        color: #7b4397 !important;
        background: linear-gradient(120deg, #8a4fff, #f66d9b, #5ea8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        text-shadow: 0px 2px 10px rgba(230, 180, 240, 0.4);
    }
    
    h2, h3 {
        color: #6c5b7b !important;
        font-weight: 700 !important;
    }

    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.85);
        border: 2px dashed #d2b4ff !important;
        border-radius: 24px !important;
        padding: 18px !important;
        box-shadow: 0 8px 24px rgba(186, 160, 230, 0.15) !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #ff9bbb !important;
        box-shadow: 0 10px 28px rgba(255, 170, 200, 0.25) !important;
        transform: translateY(-2px);
    }

    .stButton > button {
        background: linear-gradient(135deg, #a17fe0 0%, #ff8ab3 50%, #7dbdff 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 10px 28px !important;
        box-shadow: 0 6px 18px rgba(220, 130, 200, 0.35) !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover {
        transform: scale(1.04) translateY(-2px) !important;
        box-shadow: 0 10px 24px rgba(200, 110, 190, 0.45) !important;
        color: white !important;
    }

    [data-testid="stVideo"] {
        border-radius: 22px !important;
        overflow: hidden !important;
        border: 3px solid #f2e4ff !important;
        box-shadow: 0 10px 25px rgba(140, 120, 200, 0.15) !important;
    }

    [data-testid="stAlert"] {
        border-radius: 20px !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 6px 18px rgba(160, 140, 200, 0.12) !important;
    }
    div[data-testid="stAlert"]:has(div:contains("Overall Verdict: REAL")) {
        background-color: #eafaf1 !important;
        color: #1e7e48 !important;
        border: 2px solid #b7f0cd !important;
    }
    div[data-testid="stAlert"]:has(div:contains("Overall Verdict: LIKELY FAKE")) {
        background-color: #fff0f4 !important;
        color: #c93b63 !important;
        border: 2px solid #ffd1df !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.85);
        border: 2px solid #eeddff;
        border-radius: 20px;
        padding: 14px 20px;
        box-shadow: 0 6px 18px rgba(190, 170, 230, 0.15);
        display: inline-block;
    }
    [data-testid="stMetricValue"] {
        color: #7d4fd9 !important;
        font-weight: 700 !important;
    }

    [data-testid="column"] {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 22px;
        padding: 16px 18px;
        border: 2px solid #f1e2ff;
        box-shadow: 0 8px 20px rgba(190, 170, 230, 0.12);
        transition: transform 0.25s ease;
    }
    [data-testid="column"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 25px rgba(220, 170, 210, 0.22);
    }

    hr {
        border-color: #ecd5ff !important;
        opacity: 0.7;
    }

    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
        font-size: 13.5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_arduino_button(label: str, confidence: float):
    tag = "FAKE" if "FAKE" in str(label).upper() else "REAL"
    payload = f"{tag}:{confidence}\\n"

    html_code = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 12px 0;">
      <button id="connect-btn" style="
        background: linear-gradient(135deg, #a17fe0, #ff8ab3);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 24px;
        font-size: 13.5px;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(200, 130, 200, 0.35);
        transition: all 0.25s ease;
      ">
        🔌 Pair Arduino
      </button>
      <span id="serial-status" style="margin-left: 12px; font-size: 13.5px; font-weight: 600; color: #7f6e91;">Ready</span>
    </div>

    <script>
      const btn = document.getElementById('connect-btn');
      const status = document.getElementById('serial-status');
      const payload = "{payload}";

      async function sendData(port) {{
        try {{
          if (!port.readable && !port.writable) {{
            await port.open({{ baudRate: 9600 }});
          }}
          const encoder = new TextEncoder();
          const writer = port.writable.getWriter();
          await writer.write(encoder.encode(payload));
          writer.releaseLock();
          status.innerText = "⚡ Sent: " + payload.trim();
          status.style.color = "#7b4397";
        }} catch (err) {{
          status.innerText = "Send failed: " + err.message;
          status.style.color = "#e55381";
        }}
      }}

      btn.addEventListener('click', async () => {{
        if (!("serial" in navigator)) {{
          alert("Web Serial is only supported in desktop Chrome, Edge, or Opera.");
          return;
        }}
        try {{
          status.innerText = "Opening port selector...";
          const port = await navigator.serial.requestPort({{ filters: [] }});
          await sendData(port);
        }} catch (err) {{
          status.innerText = "No device chosen / " + err.message;
          status.style.color = "#8b7e9b";
        }}
      }});

      (async () => {{
        if ("serial" in navigator) {{
          const ports = await navigator.serial.getPorts();
          if (ports.length > 0) {{
            await sendData(ports[0]);
          }}
        }}
      }})();
    </script>
    """
    components.html(html_code, height=65)


if HAS_LOGO:
    st.image(LOGO_PATH, width=140)

st.title("Faking the Deep")
st.caption(
    "Upload a short video clip with a visible face and audio. This "
    "checks the video you upload using three signals: facial video "
    "analysis, audio analysis, and AI movement judgment."
)

uploaded_file = st.file_uploader(
    "Upload a video clip (mp4, mov, avi)", type=["mp4", "mov", "avi"]
)

if uploaded_file is not None:
    st.video(uploaded_file)

    if st.button("Analyze"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            with st.spinner("Analyzing video, audio, and movement... this can take a minute"):
                result = analyze_combined(tmp_path)

            if result.get("label") == "REAL":
                st.success(f"✅ Overall Verdict: {result.get('label')}")
            else:
                st.error(f"⚠️ Overall Verdict: {result.get('label')}")

            st.metric("Overall Confidence", f"{result.get('confidence')}%")

            render_arduino_button(result.get("label", ""), result.get("confidence", 0))

            st.divider()
            st.subheader("Breakdown by signal")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**🎥 Video (face)**")
                if result.get("video_result"):
                    st.write(f"{result['video_result'].get('label')}")
                    st.write(f"{result['video_result'].get('confidence')}%")
                else:
                    st.write("Not available")
                    st.caption(str(result.get("video_error", "")))

            with col2:
                st.markdown("**🔊 Audio**")
                if result.get("audio_result"):
                    st.write(f"{result['audio_result'].get('label')}")
                    st.write(f"{result['audio_result'].get('confidence')}%")
                else:
                    st.write("Skipped")
                    st.caption(str(result.get("audio_error", "")))

            with col3:
                st.markdown("**🏃 Movement (Gemini)**")
                if result.get("movement_result"):
                    st.write(f"{result['movement_result'].get('label')}")
                    st.write(f"{result['movement_result'].get('confidence')}%")
                    st.caption(str(result["movement_result"].get("reasoning", "")))
                else:
                    st.write("Not available")
                    st.caption(str(result.get("movement_error", "")))

            st.info(
                "This is a lightweight demo built from pretrained/off-the-shelf "
                "models, not a forensic-grade tool. Treat results as a signal, "
                "not a verdict."
            )

        except Exception as e:
            st.error(f"Something went wrong: {e}")
        finally:
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

```
