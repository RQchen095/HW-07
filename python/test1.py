def squary(y):
    print("{}的平方為{}".format(y,y*y))

x=int(input("請輸入整數:"))

if(x<=0):
    print(f"你輸入的數字是{x}小魚等魚0")
else:
    print(f"你輸入的數字是{x}大魚0")
for i in range(1,x+1):
    squary(i) 
