import streamlit as st
import wfdb
import neurokit2 as nk
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

st.title("ECG Signal Analysis Dashboard")

record_number = st.sidebar.selectbox(
    "Select ECG Record",
     ["100","101","102","103","104","105","106","107"]
)

duration = st.sidebar.slider(
    "ECG Duration (seconds)",
    5,
    60,
    10
)

st.write("Selected record:", record_number)

st.write(
    "Biomedical Engineering Summer Project"
)

sampling_rate = 360

record = wfdb.rdrecord(f"data/{record_number}")

ecg = record.p_signal[:, 0]
num_samples = duration * sampling_rate
ecg = ecg[:num_samples]

cleaned = nk.ecg_clean(ecg, sampling_rate=360)

signals, info = nk.ecg_peaks(
    cleaned,
    sampling_rate=360
)
number_of_beats = len(info["ECG_R_Peaks"])
heart_rate = (number_of_beats / duration) * 60

st.metric(
    label="Heart Rate",
    value=f"{heart_rate} BPM"
)



time = np.arange(len(cleaned)) / sampling_rate

fig, ax = plt.subplots(figsize=(12,4))
ax.plot(time, cleaned)
ax.scatter(
    info["ECG_R_Peaks"] / sampling_rate,
    cleaned[info["ECG_R_Peaks"]],
    color="red"
)

ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Voltage (mv)")
ax.set_title("Filtered ECG")
st.pyplot(fig)

fig.savefig(
    "output/plots/ecg_plot.png",
    dpi=300
)

try:
    hrv = nk.hrv(info, sampling_rate=360)
    sdnn = hrv["HRV_SDNN"].iloc[0]
    rmssd = hrv["HRV_RMSSD"].iloc[0]
    st.metric("SDNN", f"{sdnn:.2f} ms")
    st.metric("RMSSD", f"{rmssd:.2f} ms")

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