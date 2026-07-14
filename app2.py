import streamlit as st
import wfdb
import neurokit2 as nk
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time

st.title("ECG Signal Analysis Dashboard") 

mode = st.sidebar.radio(
    "Select Mode",
    ("MIT-BIH Arrhythmia Database", "Live ECG")
)

record_number = st.sidebar.selectbox(
    "Select ECG Record from MIT-BIH Arrhythmia Database",
     ["100","101","102","103","104","105","106","107"]
)

uploaded_file = st.sidebar.file_uploader(
    "Upload ECG CSV File",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write(df)

sampling_rate = st.sidebar.number_input(
    "Sampling Rate (Hz)",
    min_value=100,
    max_value=1000,
    value=360,
    step=10

)

duration = st.sidebar.slider(
    "ECG Duration (seconds)",
    5,
    60,
    10
)

st.write(
    "Biomedical Engineering Summer Project"
)
 
if mode == "Live ECG":
    st.write("Live ECG mode.")

    ecg = nk.ecg_simulate(duration=duration, sampling_rate=sampling_rate)
    
    buffer = []
    plot_placeholder = st.empty()

    window = 5

    update_interval = 0.2
    samples_per_update = int(sampling_rate * update_interval)

    for i in range(0, len(ecg), samples_per_update):
        buffer.extend(ecg[i:i + samples_per_update])
        buffer = buffer[-sampling_rate * window:]

        current_end = i / sampling_rate
        current_start = max(0, current_end - window)

        if current_start < 0:
            current_start = 0

        time_segment = np.linspace(current_start, current_end, len(buffer))

        fig, ax = plt.subplots(figsize=(16,16))
        ax.plot(time_segment + (current_end - window), buffer, color="black", linewidth=1)
        ax.set_facecolor("#ffe6e6")
        ax.set_xlim(current_end - window, current_end)
        ax.set_ylim(-2, 2)
        ax.set_xticks(np.arange(current_end - window, current_end, 0.2))
        ax.set_yticks(np.arange(-2, 2.1, 0.5))
        ax.grid(which="major", color="lightpink", linewidth=1.0)
        
        ax.set_xticks(np.arange( current_end - window, current_end, 0.04), minor=True)
        ax.set_yticks(np.arange(-2, 2.1, 0.1), minor=True)
        ax.grid(which="minor", color="lightgrey", linewidth=0.5)
        
        ax.set_aspect(0.04/0.1, adjustable='box')

        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Voltage (mv)")
        ax.set_title("Live ECG Recording")
        plot_placeholder.pyplot(fig)

        time.sleep(update_interval)

else:
    st.write("MIT-BIH Arrhythmia Database mode.")
    st.write("Selected record:", record_number)

sampling_rate = sampling_rate

record = wfdb.rdrecord(f"data/{record_number}")

ecg = record.p_signal[:, 0]
num_samples = duration * sampling_rate
ecg = ecg[:num_samples]

mode = st.sidebar.radio("ECG Signal Processing Mode", ["Raw", "Filtered"])

if mode == "Filtered":
    # Clean the ECG signal using NeuroKit2
    cleaned = nk.ecg_clean(ecg, sampling_rate=sampling_rate)
    
else:
    cleaned = ecg

# Extract R-peaks and calculate heart rate
signals, info = nk.ecg_peaks(
    cleaned,
    sampling_rate=sampling_rate
)
number_of_beats = len(info["ECG_R_Peaks"])
duration = len(cleaned) / sampling_rate
heart_rate = (number_of_beats / duration) * 60

st.metric(
    label="Heart Rate",
    value=f"{heart_rate} BPM"
)


time = np.arange(len(cleaned)) / sampling_rate

window=5
total_duration = len(cleaned) / sampling_rate
if total_duration > window:
    start_sec = st.slider(
         "Scroll through the ECG signal using the slider below:",
        min_value=0,
        max_value=int(total_duration - window),
        value=0
    )

else:
    start_sec = 0

end_sec = start_sec + window

start_idx = int(start_sec * sampling_rate)
end_idx   = int(end_sec * sampling_rate)
segment = cleaned[start_idx:end_idx]
time_segment = time[start_idx:end_idx]

# Plot the cleaned ECG signal with R-peaks
fig, ax = plt.subplots(figsize=(16,16))
ax.plot(time, cleaned, color="black", linewidth=1)
ax.scatter(
    info["ECG_R_Peaks"] / sampling_rate,
    cleaned[info["ECG_R_Peaks"]],
    color="red"
)
ax.set_facecolor("#ffe6e6")
ax.set_xlim(time_segment[0], time_segment[-1])   # restrict to 5s
ax.set_ylim(-2, 2)

ax.set_xticks(np.arange(time_segment[0], time_segment[-1], 0.2))
ax.set_yticks(np.arange(-2, 2.1, 0.5))
ax.grid(which="major", color="lightpink", linewidth=1.0)

ax.set_xticks(np.arange(time_segment[0], time_segment[-1], 0.04), minor=True)
ax.set_yticks(np.arange(-2, 2.1, 0.1), minor=True)
ax.grid(which="minor", color="lightgrey", linewidth=0.5)

ax.set_aspect(0.04/0.1, adjustable='box')

if mode=="Filtered":
    ax.set_title("Filtered ECG Signal")

else:
    ax.set_title("Raw ECG Signal")



ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Voltage (mv)")
st.pyplot(fig)


 
# Save the plot as a PNG file
fig.savefig(
    "output/plots/ecg_plot.png",
    dpi=300
)

# Calculate HRV metrics
try:
    hrv = nk.hrv(info, sampling_rate=sampling_rate)
    sdnn = hrv["HRV_SDNN"].iloc[0]
    rmssd = hrv["HRV_RMSSD"].iloc[0]
    st.metric("SDNN", f"{sdnn:.2f} ms")
    st.metric("RMSSD", f"{rmssd:.2f} ms")

# In case HRV metrics cannot be calculated
except Exception:
    st.warning("Not enough ECG data to calculate HRV reliably")

results = pd.DataFrame({

    "Heart Rate":[heart_rate]

})

results["SDNN"] = sdnn
results["RMSSD"] = rmssd

csv = results.to_csv(index=False)

st.download_button(
    "Download Results",
    csv,
    file_name="ecg_results.csv",
    mime="text/csv"
)

st.markdown("---")
st.markdown("""
### About
            
This project analyzes ECG signals from the MIT-BIH Arrhythmia Database
            
Developed using Python, Streamlit, WFDB and NeuroKit2.
""")