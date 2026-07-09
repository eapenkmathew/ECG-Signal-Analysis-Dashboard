import wfdb
import neurokit2 as nk
import matplotlib.pyplot as plt
import pandas as pd

record = wfdb.rdrecord("data/100")
ecg = record.p_signal[:, 0]
ecg = ecg[:3600]

cleaned = nk.ecg_clean(ecg, sampling_rate=100)

signals, info = nk.ecg_peaks(
    cleaned,
    sampling_rate=360
)

hrv = nk.hrv(info, sampling_rate=360,  show=False)

plt.figure(figsize=(15,5))

plt.plot(cleaned)
plt.scatter(
    info ["ECG_R_Peaks"],
    cleaned[info["ECG_R_Peaks"]],
    color="red",
    label="R Peaks"
)

plt.legend()
plt.title("Detected Heartbeats")
plt.show()

print(info["ECG_R_Peaks"])

number_of_beats = len(info["ECG_R_Peaks"])
print(number_of_beats)

heart_rate = number_of_beats * 6
print(f"Heart Rate: {heart_rate} BPM")

if heart_rate < 60:
    print("Brachychardia")

elif heart_rate > 100:
    print("Tachychardia")

else:
    print("Normal Heart Rate")

print(hrv)
print("SDNN:", hrv["HRV_SDNN"].iloc[0], "ms")
print("RMSSD:", hrv["HRV_RMSSD"].iloc[0], "ms")

results = pd.DataFrame({
    "Heart Rate (BPM)": [heart_rate],
    "SDNN (ms)": [hrv["HRV_SDNN"].iloc[0]],
    "RMSSD (ms)": [hrv["HRV_RMSSD"].iloc[0]]
})

results.to_csv(
    "output/csv/hrv_results.csv",
    index=False
)

if heart_rate < 60:
    print("Heart rate indicates Brachychardia.")

elif heart_rate > 100:
    print("Heart rate indicates Tachychardia.")

else:
    print("Heart rate is within normal resting range.")