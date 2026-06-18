import java.util.Scanner; 
import java.util.ArrayList;

public class StudenM {
    ArrayList<student> students = new ArrayList<>();
    Scanner input = new Scanner(System.in);

    public void Menu(){
        while (true) {
            System.out.println("Chioce an option");
            System.out.println("1.Add student");
            System.out.println("2.View student");
            System.out.println("3.Search student");
            System.out.println("4.Delete student");
            System.out.println("5.Exit");
            int choice = input.nextInt();

            switch (choice) {
                case 1 -> addstudent();
                case 2 -> viewstudent();
                case 3 -> searchstudent();
                case 4 -> deletestudent();
                case 5 -> {System.out.println("Exiting");
                    return;
                }    
            
                default ->
                    System.out.println("Invalid input");
                }   
        }
    }
    public void addstudent(){
        System.out.println("Enter student name");
        String name = input.nextLine();
        System.out.println("Enter student ID");
        int id = input.nextInt();
        System.out.println("Enter student age");
        int age = input.nextInt();
        students.add(new student(name, age, id));
        System.out.println("studented added");
    }
    public void viewstudent(){
        if(students.isEmpty()){
            System.out.println("There are no students");
        }
        else{
            for(student s : students){
                System.out.println(s);
            }
        }
    }
    public void searchstudent(){
        System.out.println("enter student Id");
        int id = input.nextInt();

        for(student s : students){
            if (s.getId() == id) {
                System.out.println(s);
               return; 
            }

        }
        System.out.println("student not found");
     }
    public void deletestudent(){}

 
   
}
class student{
    String name;
    int age;
    int id;



    public student(String name, int age, int id){
        this.name = name;
        this.age = age;
        this.id = id;
    }

}