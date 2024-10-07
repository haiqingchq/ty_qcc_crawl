import pandas as pd


def test_excel():
    df = pd.read_excel("../data/data.xlsx", engine='openpyxl')
    index = df.loc[df["借款人企业名称"] == "泗阳金顺台板厂"].index[0]
    df.at[index, "社会统一信用代码"] = "91321323MA1MGG747N"
    df.to_excel("2.xlsx")
