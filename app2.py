import streamlit as st
import wfdb
import neurokit2 as nk
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time
from scipy.signal import find_peaks 
import serial
import math
import itertools
from collections import deque
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages

def generate_pdf(signal, time_data, average_hr, minimum_hr, maximum_hr, sampling_rate):

    signal = np.array(signal)
    time_data = np.array(time_data)

    pdf = PdfPages("ECG_Report.pdf")

    samples_per_strip = sampling_rate * 10

    total_strips = math.ceil(
        len(signal) / samples_per_strip
    )


    for i in range(total_strips):

        start = i * samples_per_strip
        end = start + samples_per_strip

        strip_signal = signal[start:end]
        strip_time = time_data[start:end]

        min_length = min(
            len(strip_signal),
            len(strip_time)
        )

        strip_signal = strip_signal[:min_length]
        strip_time = strip_time[:min_length]


        fig, ax = plt.subplots(figsize=(12,4))

        for x in np.arange(
            strip_time[0],
            strip_time[-1],
            0.04
        ):
            ax.axvline(
                x,
                color="#ffd6d6",
                linewidth=0.5
            )

        for x in np.arange(
            strip_time[0],
            strip_time[-1],
            0.2
        ):
            ax.axvline(
                x,
                color="#ff9999",
                linewidth=1
            )


        for y in np.arange(-3,3,0.1):
            ax.axhline(
                y,
                color="#ffd6d6",
                linewidth=0.5
            )


        for y in np.arange(-3,3,0.5):
            ax.axhline(
                y,
                color="#ff9999",
                linewidth=1
            )


        ax.plot(
            strip_time,
            strip_signal,
            color="black",
            linewidth=1
        )

        ax.set_xlim(
            strip_time[0],
            strip_time[-1]
        )

        ax.set_ylim(-3,3)

        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Amplitude")

        ax.set_title(
            f"ECG Strip {i+1}/{total_strips}"
        )


        pdf.savefig(fig)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8,5))

    ax.axis("off")

    summary = f"""
    ECG Report Summary

    Total recording time:
    {len(signal)/sampling_rate:.1f} seconds

    Sampling rate:
    {sampling_rate} Hz

    Average HR:
    {average_hr:.1f} BPM

    Minimum HR:
    {minimum_hr:.1f} BPM

    Maximum HR:
    {maximum_hr:.1f} BPM
    """

    ax.text(
        0.1,
        0.8,
        summary,
        fontsize=14
    )


    pdf.savefig(fig)
    plt.close(fig)
    pdf.close()

    return "ECG_Report.pdf"

st.success("ECG PDF Report Generated: ECG_Report.pdf")

st.title("ECG Signal Analysis Dashboard") 

data_mode = st.sidebar.radio(
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
 
if data_mode == "Live ECG":
    st.write("Live ECG mode.")
    
    if "serial_connection" not in st.session_state:
        st.session_state.serial_connection = serial.Serial(
        'COM3',
        230400,
        timeout=1
    )
        st.session_state.serial_connection.reset_input_buffer()
    ser = st.session_state.serial_connection

    sampling_rate = 250  
    window = 5       
    update_interval = 0.01
    live_buffer = deque(maxlen=sampling_rate * window)
    plot_placeholder = st.empty()
    hr_placeholder = st.empty()

    last_peak_update = time.time()
    info = {"ECG_R_Peaks": np.array([], dtype=int)}

    fig, ax = plt.subplots(figsize=(12,4))
    ax.set_facecolor("#ffe6e6")
    
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
    ax.yaxis.set_major_locator(MultipleLocator(0.5))
    ax.xaxis.set_minor_locator(MultipleLocator(0.04))
    ax.yaxis.set_minor_locator(MultipleLocator(0.1))
    ax.minorticks_on()
    
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Live ECG Recording")


    st.empty()
    total_samples = 0
    heart_rate_history = []
    average_hr = 0
    minimum_hr = 0
    maximum_hr = 0

    col1, col2, col3, col4 = st.columns(4)
    current_placeholder = col1.empty()
    average_placeholder = col2.empty()
    minimum_placeholder = col3.empty()
    maximum_placeholder = col4.empty()

    if "raw_recording" not in st.session_state:
        st.session_state.raw_recording = []

    if "recorded_time" not in st.session_state:
        st.session_state.recorded_time = []

    if "pdf_ready" not in st.session_state:
        st.session_state.pdf_ready = False

    generate_report = st.button(
        "Generate PDF Report",
        key="generate_pdf"
    )

    while True:
        while ser.in_waiting:
            try:
                value = float(ser.readline().decode().strip())
                live_buffer.append(value)
                st.session_state.raw_recording.append(value)
                total_samples += 1
            except ValueError:
                pass

        if len(live_buffer) < sampling_rate:
            continue

        signal = np.array(live_buffer)
        signal = signal - np.mean(signal)

        filtered = nk.ecg_clean(
            signal,
            sampling_rate=250
        )

        filtered = filtered/1000   

        if time.time() - last_peak_update > 0.5:

            signals, info = nk.ecg_peaks(
            filtered,
            sampling_rate=sampling_rate,
            correct_artifacts=True
        )

          
            last_peak_update = time.time()

        start_time = (total_samples - len(filtered)) / sampling_rate
        ax.clear()

        for x in np.arange(start_time, start_time + window + 0.04, 0.04):
            ax.axvline(
                x,
                color="#ffd6d6",
                linewidth=0.5,
                zorder=0
            )

        for x in np.arange(start_time, start_time + window + 1, 0.2):
            ax.axvline(
                x,
                color="#ff9999",
                linewidth=1.2,
                zorder=0
            )

        for y in np.arange(-3, 3.1, 0.1):
            ax.axhline(
                y,
                color="#ffd6d6",
                linewidth=0.5,
                zorder=0
            )

        for y in np.arange(-3, 3.1, 0.5):
            ax.axhline(
                y,
                color="#ff9999",
                linewidth=1.2,
                zorder=0
            )


        t = start_time + np.arange(len(filtered)) / sampling_rate
        line, = ax.plot(t, filtered, color="black", linewidth=1)
        line.set_data(t, filtered)

        ax.set_xlim(start_time, start_time + window)
        ax.set_ylim(-3, 3)
        ax.set_aspect('auto')
        
        if len(info["ECG_R_Peaks"]) >= 2:
            rr = np.diff(info["ECG_R_Peaks"]) / sampling_rate
            hr = 60 / np.mean(rr)

            heart_rate_history.append(hr)
            current_hr = heart_rate_history[-1]
            average_hr = np.mean(heart_rate_history)
            minimum_hr = np.min(heart_rate_history)
            maximum_hr = np.max(heart_rate_history)

            current_placeholder.metric("Current HR", f"{current_hr:.1f} BPM")
            average_placeholder.metric("Average", f"{average_hr:.1f} BPM")
            minimum_placeholder.metric("Minimum", f"{minimum_hr:.1f} BPM")
            maximum_placeholder.metric("Maximum", f"{maximum_hr:.1f} BPM")

        plot_placeholder.pyplot(fig)

        if generate_report:
            
            full_signal = np.array(st.session_state.raw_recording)
            full_signal = full_signal - np.mean(full_signal)

            filtered_full = nk.ecg_clean(
                full_signal,
                sampling_rate=sampling_rate
            )

            filtered_full = filtered_full / 1000

            time_data = np.arange(len(filtered_full)) / sampling_rate

            generate_pdf(
                filtered_full,
                time_data,
                average_hr,
                minimum_hr,
                maximum_hr,
                sampling_rate
            )

            st.session_state.pdf_ready = True

            if st.session_state.pdf_ready:

                with open("ECG_Report.pdf", "rb") as file:

                    st.download_button(
                        "Download ECG PDF Report",
                        file,
                        file_name="ECG_Report.pdf",
                        mime="application/pdf",
                        key="download_pdf"
                    )

        time.sleep(update_interval)



elif data_mode == "MIT-BIH Arrhythmia Database":
    st.write("MIT-BIH Arrhythmia Database mode.")
    st.write("Selected record:", record_number)

sampling_rate = sampling_rate

record = wfdb.rdrecord(f"data/{record_number}")

ecg = record.p_signal[:, 0]
num_samples = duration * sampling_rate
ecg = ecg[:num_samples]

processing_mode = st.sidebar.radio("ECG Signal Processing Mode", ["Raw", "Filtered"])

if processing_mode == "Filtered":
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

if processing_mode=="Filtered":
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