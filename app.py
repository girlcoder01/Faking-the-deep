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
    """
    Renders a browser-native Web Serial button.
    Allows a user in Chrome/Edge to send the verdict directly to their
    locally plugged-in Arduino LCD from the hosted cloud app.
    """
    tag = "FAKE" if "FAKE" in str(label).upper() else "REAL"
    payload = f"{tag}:{confidence}\\n"

    html_code = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin-top: 15px; margin-bottom: 15px;">
      <button id="serial-btn" style="
        background: linear-gradient(135deg, #00878a, #005c5f);
        color: white;
        border: none;
        padding: 10px 18px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
      ">
        🔌 Push Result to Arduino LCD
      </button>
      <div id="serial-status" style="margin-top: 8px; font-size: 13px; color: #444;"></div>
    </div>

    <script>
      const btn = document.getElementById('serial-btn');
      const status = document.getElementById('serial-status');

      btn.addEventListener('click', async () => {{
        if (!("serial" in navigator)) {{
          status.innerHTML = "⚠️ <b>Web Serial not supported.</b> Please use Google Chrome or Edge.";
          status.style.color = "#d93025";
          return;
        }}

        try {{
          status.innerText = "Requesting USB port access...";
          status.style.color = "#444";

          // 1. Pick port
          const port = await navigator.serial.requestPort();

          // 2. Only open if Chrome hasn't opened it already
          if (!port.readable && !port.writable) {{
            try {{
              await port.open({{ baudRate: 9600 }});
            }} catch (openErr) {{
              // If already open, ignore and proceed to write
              if (!openErr.message.includes("already open")) {{
                throw openErr;
              }}
            }}
          }}

          status.innerText = "Transmitting to Arduino LCD...";

          // 3. Write data directly to the stream
          const encoder = new TextEncoder();
          const writer = port.writable.getWriter();
          await writer.write(encoder.encode("{payload}"));
          
          // 4. Release writer lock (leave port state intact for Chrome)
          writer.releaseLock();

          status.innerText = "✅ Sent '{tag}:{confidence}' to Arduino LCD!";
          status.style.color = "#0f9d58";

        }} catch (err) {{
          if (err.name === 'NotFoundError') {{
            status.innerText = "Connection cancelled (no port selected).";
            status.style.color = "#666";
          }} else {{
            status.innerText = "❌ Serial Error: " + err.message;
            status.style.color = "#d93025";
          }}
        }}
      }});
    </script>
    """
    components.html(html_code, height=95)


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
