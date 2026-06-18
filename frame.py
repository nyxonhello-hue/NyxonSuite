import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme('blue')

app = ctk.CTk()
app.title('minato')
app.geometry('500x500')

sidebar = ctk.CTkFrame(app, width=150, corner_radius=0)
sidebar.pack(side='left', fill='y')

main = ctk.CTkFrame(app)
main.pack(side = 'right', fill='both', expand=True, padx=10, pady=10)

ctk.CTkLabel(sidebar, text='menu').pack(pady=10)
ctk.CTkLabel(main, text='content here').pack(pady=10)


app.mainloop()

