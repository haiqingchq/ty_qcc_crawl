import pandas as pd


def test_excel():
    df = pd.read_excel("../data/1.xlsx", engine='openpyxl')
    index = df.loc[df["借款人企业名称"] == "泗阳金顺台板厂"].index[0]
    df.at[index, "社会统一信用代码"] = "91321323MA1MGG747N"
    df.to_excel("2.xlsx")


def test_finally():
    int_list = []
    try:
        try:
            for i in range(100):
                int_list.append(int(i))
        except AttributeError:
            pass
    finally:
        print(int_list)


if __name__ == '__main__':
    test_finally()
