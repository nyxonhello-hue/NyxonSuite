
public class Account {
    String name;
    int pin;
    double balance;

  public Account(String name, int pin, double balance){
        this.name = name;
        this.pin = pin;
        this.balance =balance;
}
    public double deposit(double amount){
        this.balance += amount;
        return this.balance;
    } 
    
    public double withdraw(double amount){
        if (amount<=balance) {
            balance -= amount;
        }else{
            System.out.print("Insufficient balance");
        }
        return balance;
    }
    public double showBalance(){
        return balance;
    }
    public boolean checkPin(int inputPin){
        return this.pin == inputPin;
    }   

        public static void main(String[] args) {
        Account acc = new Account("Minto",1234, 5000);
        acc.deposit(1000);
        acc.withdraw(3888);

        System.out.println("Balance: " + acc.showBalance());
        }
}


