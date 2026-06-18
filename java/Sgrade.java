import java.util.Scanner;

public class Sgrade {
    public static void main(String[] args) {
        Scanner input = new Scanner(System.in);

        System.out.println("Enter your name");
        String name = input.nextLine();
        System.out.println("Enter your score");
        int score = input.nextInt();

        if (score >= 90 ) {
            System.out.println(name + " Garde: A");
        }
        else if(score >=75){
             System.out.println(name + " Garde: B");
        }
         else if(score >= 60){
             System.out.println(name + " Garde: C");
        }
         else if(score >= 45){
             System.out.println(name + " Garde: D");
        }else {
            System.out.println(name + " Garde: F");
        }

        input.close();
    }
}
