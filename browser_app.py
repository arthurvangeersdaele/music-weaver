import os 
from datetime import datetime

# Import the required modules (chack for automated installation in run.py)
import streamlit as st
import streamlit.components.v1 as components
import sounddevice as sd
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import time


# Ensure the uploads directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Creating global variables
# |--> to store selected signature
if 'selected_signature_image' not in st.session_state:
    # default_path = os.path.join("uploads", "example.jpg")
    st.session_state.selected_signature_image = None
# |--> to store selected output audio source
if 'relevant_audio_outputs' not in st.session_state:
    st.session_state.relevant_audio_outputs = None
# |--> to store selected output audio source
if 'selected_audio_output' not in st.session_state:
    st.session_state.selected_audio_output = None
# |--> to store if oscilloscope is running
if "run" not in st.session_state:
    st.session_state.run = False
# |--> to store latest audio data  
duration = 1  # 50ms buffer
samplerate = 44100
frames = int(samplerate * duration)
if "latest_data" not in st.session_state:
    st.session_state.latest_data = np.zeros(frames)

# Save signature image 
def save_uploaded_file(uploaded_file):
    """Save uploaded image to local uploads directory."""
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


# Understanding audio input/output sources devices
def list_audio_devices_info():
    """Returns a DataFrame with all input/output devices and parameters."""
    devices = sd.query_devices()
    df = pd.DataFrame(devices)
    return df

# Return the relevant microphones inputs and audio ouputs
def list_audio_IO():
    """List all available  sound card outpuuts."""
    devices = sd.query_devices()
    df = pd.DataFrame(devices)
    IO_list = [device['name'] for device in devices if device['max_input_channels'] > 0]
    return IO_list

def detect_active_audio_IO(duration=1, threshold=0.01, samplerate=44100):
    """
    List only microphones or audio output devices that are currently active.
    
    - duration: Time in seconds to check for signal.
    - threshold: Signal level threshold to consider the device as active.
    - samplerate: Audio sample rate for the test.
    """
    devices = sd.query_devices()
    all_devices = []
    active_devices = []

    for idx, device in enumerate(devices):
        all_devices.append(device['name'])
        try:
            # Check microphones (input devices)
            if device['max_input_channels'] > 0:
                with sd.InputStream(device=idx, channels=1, samplerate=samplerate) as stream:
                    data = stream.read(int(samplerate * duration))[0]
                    if np.any(np.abs(data) > threshold):
                        active_devices.append(device['name'])

            # Check speakers (output devices)
            elif device['max_output_channels'] > 0:
                # Generate test tone
                tone = 0.1 * np.sin(2 * np.pi * 440 * np.arange(samplerate * duration) / samplerate)
                try:
                    with sd.OutputStream(device=idx, channels=1, samplerate=samplerate):
                        sd.play(tone, samplerate=samplerate, device=idx, blocking=True)
                        active_devices.append(device['name'])  # Assume output success = active
                except Exception:
                    continue

        except Exception:
            continue  # Skip inaccessible or invalid devices
    st.session_state.relevant_audio_outputs = all_devices
    return 1

def list_active_audio_IO():
    return st.session_state.relevant_audio_outputs

def get_device_index(name):
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['name'] == name:
            print(i)
            return i
    return None

def get_device_channels(device_name):
    for device in sd.query_devices():
        if device['name'] == device_name:
            return device['max_input_channels']
    raise ValueError(f"Device '{device_name}' not found.")


# --- Streamlit UI ---

# --- CONFIG & PAGE ---
st.set_page_config(page_title="Main Page", layout="centered")
# st.markdown("<h1 style='color:#1ed760;'>Real Time Sound Visualizer</h1>", unsafe_allow_html=True)
components.html("""
<div style="text-align:center; padding: 1rem;">
  <h1 class="shiny-title">Real Time Sound Visualizer</h1>
</div>

<style>
@keyframes shine {
  0% { background-position: -150%; }
  100% { background-position: 0%; }
}

.shiny-title {
  font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
  font-size: 2.8rem;
  font-weight: 700;
  background: linear-gradient(
    120deg,
    lime 0%,
    #eec94f 50%,
    lime 100%
  );
  background-size: 200% 300%;
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
  -webkit-text-fill-color: transparent;
  animation: shine 20s ease infinite;
}
</style>
""", height=150)

# # --- SIGNATURE UPLOAD ---
# st.header("Choose your vibing signature")

# uploaded_file = st.file_uploader("New from device", type=["jpg", "jpeg", "png"])
# upload_dir = "uploads"
# os.makedirs(upload_dir, exist_ok=True)

# if uploaded_file:
#     img = Image.open(uploaded_file)
#     if img.width > 1000 or img.height > 1000:
#         st.error("Image dimensions must be ≤ 1000x1000 pixels.")
#     else:
#         saved_path = os.path.join(upload_dir, uploaded_file.name)
#         img.save(saved_path)
#         st.session_state.selected_signature_image = saved_path

# # --- SELECT FROM PREVIOUSLY UPLOADED ---
# if os.path.exists(upload_dir):
#     image_files = [f for f in os.listdir(upload_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
#     if image_files:
#         st.session_state.selected_signature_image = os.path.join(upload_dir, st.selectbox("Previously uploaded", image_files)) 
#     else:
#         st.warning("No images found in the 'uploads' folder.")

# # --- OPTION TO DISABLE SIGNATURE ---
# disable_signature = st.checkbox("No signature", value=False)
# if disable_signature:
#     st.session_state.selected_signature_image = None

# # --- CONSISTENT IMAGE DISPLAY ---
# if st.session_state.get("selected_signature_image"):
#     st.image(st.session_state.selected_signature_image, caption="Uploaded Signature", width=200)

# Select Source
selected = False
st.header("Select an audio input/output")

get_active_sources = st.button("Start Active Source Detection")

if get_active_sources:
    detect_active_audio_IO()

IO = list_active_audio_IO()

if IO:
    selected = st.selectbox("Select an audio output source:", IO)
    st.session_state.selected_audio_output = selected  # Update global variable
elif get_active_sources:
    st.warning("No audio output detected.")


# Ensure audio output is selected
if get_active_sources and 'selected_audio_output' not in st.session_state:
    st.warning("No audio output selected.")

# Start/Stop Buttons
if selected:
    if st.button("Start"):
        st.session_state.run = True
    if st.button("Stop"):
        st.session_state.run = False

# Placeholder for plot
plot_placeholder = st.empty()
# Inject HTML with custom background
plot_placeholder.markdown(
    """
    <div style='background-color:red; padding:20px; border-radius:10px;'>
        <h4 style='color:#333;'>This is a styled placeholder</h4>
    </div>
    """,
    unsafe_allow_html=True
)

# Start real-time stream
def audio_callback(indata, frames, time, status):
    st.session_state.latest_data = indata[:, 0]



source_is_input = False;

# Audio Stream Loop
if st.session_state.run:
    try:
        with sd.InputStream(device=get_device_index(st.session_state.selected_audio_output), callback=audio_callback, channels=get_device_channels(st.session_state.selected_audio_output), samplerate=samplerate, blocksize=frames):
            while st.session_state.run:
                fig, ax = plt.subplots(figsize=(12, 1.8), facecolor='black')
                ax.plot(st.session_state.latest_data, color='lime', linewidth=1)
                ax.set_ylim(-1.05, 1.05)
                ax.axis('off')
                plot_placeholder.pyplot(fig)
                sd.sleep(50)  # allow time for updates
    except Exception as e:
        st.error(f"Error: {e}")
        

if(selected and not source_is_input):
    st.warning("Selected device not recognized.")
#---------------------------------------------------------------------------------------------------------------------------------------
# [DEV] Display list of devices
# device_info = list_audio_devices_info()
# st.dataframe(device_info)

# # List microphones
# def list_microphones():
#     devices = sd.query_devices()
#     return [device['name'] for device in devices if device['max_input_channels'] > 0]

