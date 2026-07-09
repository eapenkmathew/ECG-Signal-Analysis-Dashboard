import wfdb
record= wfdb.rdrecord("../data/100")
print(record.p_signal[:10])
