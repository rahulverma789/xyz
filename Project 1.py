instructions = """
Instructions:
+ -> Addition
- -> Subtraction
* -> Multiplication
/ -> Division
% -> Remainder
** -> Power

"""
print(instructions)

def calculator():
    while True:
        isValid = False
        
        # Get the first number
        while not isValid:
            num1 = input("Enter the first number: ")
            if num1.lower() == 'exit':
                return
            try:
                num1 = float(num1)
                isValid = True
            except ValueError:
                print("Invalid input. Please enter a number.")

        isValid = False
        
        # Get the second number
        while not isValid:
            num2 = input("Enter the second number: ")
            if num2.lower() == 'exit':
                return
            try:
                num2 = float(num2)
                isValid = True
            except ValueError:
                print("Invalid input. Please enter a number.")

        isValid = False
        
        # Get the operator
        while not isValid:
            operator = input("Choose an operator from the list above: ")
            if operator.lower() == 'exit':
                return
            elif operator not in ['+', '-', '*', '/', '%', '**']:
                print("Invalid operation. Please choose a valid operator.")
            else:
                isValid = True

        # Perform the calculation
        if operator == "+":
            result = num1 + num2
        elif operator == "-":
            result = num1 - num2
        elif operator == "*":
            result = num1 * num2
        elif operator == "/":
            try:
                result = num1 / num2
            except ZeroDivisionError as error:
                result = str(error)
        elif operator == "%":
            result = num1 % num2
        elif operator == "**":
            result = num1 ** num2

        # Print the result
        print(f"{num1} {operator} {num2} = {result}")

# Run the calculator
calculator()
