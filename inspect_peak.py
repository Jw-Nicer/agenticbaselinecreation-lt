
import pandas as pd

file = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Peak Vista - AMN Download.xls"
# Inspect rows 5-10 where headers likely are
df = pd.read_excel(file, header=None, skiprows=5, nrows=5)
print(df)
