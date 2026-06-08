number_1 = int(input("What is your first number: "))
number_2 = int(input("What is your second number: "))
operator = input("Enter Operator: ")

# if condition:
#     code
# else:
#     code


if number_1 > number_2:
    name = input("What is your name: ")
    print(name)
    print("Number 1 is bigger")

elif operator == "+":
    print(number_1 + number_2)

elif number_1 == number_2:
    print("They're equal")
    age = input("What is your age: ")
    print(age)
else:
    print("Number 2 wins")
