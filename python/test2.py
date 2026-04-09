def sum():
    data = input("請輸入西元出生年月日：")
    total = 0
    for char in data:
        total = total + int(char)
    print(f"您的西元出生年月日相加總和為：", total)

sum()

