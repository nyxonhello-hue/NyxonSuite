import java.util.Scanner;

public class Ca{
    public static void main(String[] args) {
        Scanner input = new Scanner(System.in);
        System.out.println("Enter first number");
        float num1 = input.nextFloat();
        System.out.println("Enter second number");
        float num2 = input.nextFloat();
        System.out.println("Enter the operator (+,-,/,*)");
        char oper = input.next().charAt(0);
        if (oper=='+') {
            System.out.println("The sum is : "+ (num1 + num2)) ;
        }
        else if(oper=='-'){
            System.out.println("The differences is : "+ (num1 - num2));
        }
        else if(oper=='*'){
            System.out.println("The product is : "+ (num1 * num2));
        }
        else if(oper=='/'){
            System.out.println("The qoutous is : "+ (num1 / num2));
        }
        else {
            System.out.println("invalid input");
        }

        input.close();
    }

}