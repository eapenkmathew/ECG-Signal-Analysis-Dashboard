import wfdb
import matplotlib.pyplot as plt
record= wfdb.rdrecord("data/100")
signal= record.p_signal[:3600,1]
plt.figure(figsize=(15,5))
plt.plot(signal)
plt.title("ECG Signal")
plt.xlabel("Samples")
plt.ylabel("Voltage (mv)")
plt.show()