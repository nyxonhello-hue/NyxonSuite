import java.util.Scanner;

public class Login{
    public static void main(String[] args) {
        
        
        Scanner input = new Scanner(System.in);
        int start = 0;
        int limit = 3;
        while (start < limit){
            System.out.print("Enter username: ");
            String name = input.nextLine();
            System.out.println("Enter password");
            String pass = input.nextLine();
        
            if (name.equals("minato") && pass.equals("password")) {
                System.out.println("You have successfully Login, Welcome "+ name);
                break;
            }
            else{
                System.out.println("Invalid username or password");
            }

        }        
            
        input.close();

    }
}