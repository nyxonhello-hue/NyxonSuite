import java.util.Random;
import java.util.Scanner;
public class guess {
    public static void main(String[] args) {
        Scanner input = new Scanner(System.in);
        Random rand = new Random();

        System.out.println("Guess the number between 0 to 100");
        int num = input.nextInt();

        int com = rand.nextInt(10);

        if(num == com){
            System.out.println("Correct you guess right");
        }
        else if(num > com){
            System.out.println("Too high");
        }
        else if(num < com){
             System.out.println("Too low");
        }
        else {
             System.out.println("Invalid input");
        }


        input.close();

    }
}
