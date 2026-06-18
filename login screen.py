import customtkinter as ctk

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

app=ctk.CTk()
app.title('Login')
app.geometry('400x300')

frame = ctk.CTkFrame(app, corner_radius=12)
frame.place(relx=0.5, rely=0.5, anchor='center')

ctk.CTkLabel(frame, text='Sign In', font=('Arial',20,'bold')).pack(pady=(20,10))

username = ctk.CTkEntry(frame, placeholder_text='username', width=220)
username.pack(pady=8)
password = ctk.CTkEntry(frame, placeholder_text='password', show='*', width=220)
password.pack(pady=8)

status = ctk.CTkLabel(frame, text='', text_color='red')
status.pack()

def login():
    if username.get() == 'minato' and password.get() == '1122':
        status.configure(text=' Access granted', text_color='green')
    else:
        status.configure(text=' invalid credentials', text_color='red')

ctk.CTkButton(frame, text='Login',command=login, width=220).pack(pady=(8,20))            

app.mainloop()