"""
Minimal upload UI. Run with:
 
    streamlit run app.py
 
Only build/run this AFTER detect.py has worked on a test video from the
command line — see README.md.
"""

import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components

# Bridge Streamlit Secrets to environment variables for Gemini before imports
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

from combined_detect import analyze_combined

st.set_page_config(page_title="Deepfake Video Checker", page_icon="🔍")


def render_arduino_button(label: str, confidence: float):
    tag = "FAKE" if "FAKE" in str(label).upper() else "REAL"
    payload = f"{tag}:{confidence}\\n"

    html_code = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 10px 0;">
      <button id="connect-btn" style="
        background: #00878a;
        color: white;
        border: none;
        padding: 9px 16px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
      ">
        🔌 Pair Arduino for Auto-Sync
      </button>
      <span id="serial-status" style="margin-left: 10px; font-size: 13px; color: #555;">Ready</span>
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
          status.style.color = "#0f9d58";
        }} catch (err) {{
          status.innerText = "Send failed: " + err.message;
          status.style.color = "#d93025";
        }}
      }}

      // On click, prompt user explicitly
      btn.addEventListener('click', async () => {{
        if (!("serial" in navigator)) {{
          alert("Web Serial is only supported in desktop Chrome, Edge, or Opera.");
          return;
        }}
        try {{
          status.innerText = "Opening port selector...";
          // Request any USB serial device with empty filter
          const port = await navigator.serial.requestPort({{ filters: [] }});
          await sendData(port);
        }} catch (err) {{
          status.innerText = "No device chosen / " + err.message;
          status.style.color = "#666";
        }}
      }});

      // Auto-send if browser already has a granted device
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
    # Render with clean height
    components.html(html_code, height=65)


st.title("🔍 Deepfake Video Checker")
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

            if result["label"] == "REAL":
                st.success(f"✅ Overall Verdict: {result['label']}")
            else:
                st.error(f"⚠️ Overall Verdict: {result['label']}")
            
            st.metric("Overall Confidence", f"{result['confidence']}%")

            # Arduino LCD output widget
            render_arduino_button(result["label"], result["confidence"])

            st.divider()
            st.subheader("Breakdown by signal")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**🎥 Video (face)**")
                if result["video_result"]:
                    st.write(f"{result['video_result']['label']}")
                    st.write(f"{result['video_result']['confidence']}%")
                else:
                    st.write("Not available")
                    st.caption(str(result["video_error"]))

            with col2:
                st.markdown("**🔊 Audio**")
                if result["audio_result"]:
                    st.write(f"{result['audio_result']['label']}")
                    st.write(f"{result['audio_result']['confidence']}%")
                else:
                    st.write("Skipped")
                    st.caption(str(result["audio_error"]))

            with col3:
                st.markdown("**🏃 Movement (Gemini)**")
                if result["movement_result"]:
                    st.write(f"{result['movement_result']['label']}")
                    st.write(f"{result['movement_result']['confidence']}%")
                    st.caption(result["movement_result"]["reasoning"])
                else:
                    st.write("Not available")
                    st.caption(str(result["movement_error"]))

            st.info(
                "This is a lightweight demo built from pretrained/off-the-shelf "
                "models, not a forensic-grade tool. Treat results as a signal, "
                "not a verdict."
            )

        except Exception as e:
            st.error(f"Something went wrong: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
