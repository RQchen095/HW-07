def split(x):
	x=x.split(",")
	school=x[0].replace("我是","")
	print(f"學校:{school}")
	print(f"姓名:{x[2]}")

#只有執行
if __name__ == "__main__":
	name="我是靜宜大學,資管二B,張伊傑"
	split(name)