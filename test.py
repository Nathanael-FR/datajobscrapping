import pandas as pd

data = {
    "job_desc":"test",
    "job_title":"test,",
    "salary":"test.",
}

df = pd.DataFrame(data, index=[0])
df.to_csv("test.csv", index=False)