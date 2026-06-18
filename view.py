import customtkinter as ctk

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

app = ctk.CTk()
app.title('My App')
app.geometry('500x400')

tabs = ctk.CTkTabview(app, width=400, height=300)
tabs.pack(pady=20)

tabs.add('Home')
tabs.add('settings')

ctk.CTkLabel(tabs.tab('Home'), text='Welcome!').pack(pady=20)
ctk.CTkLabel(tabs.tab('settings'), text='settings go here').pack(pady=20)

app.mainloop()