"""
Minimal upload UI. Run with:
 
    streamlit run app.py
 
Only build/run this AFTER detect.py has worked on a test video from the
command line — see README.md.
"""
 
import tempfile
import os
import streamlit as st
 
from combined_detect import analyze_combined
 
st.set_page_config(page_title="Deepfake Video Checker", page_icon="🔍")
 
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
            os.unlink(tmp_path)
 
