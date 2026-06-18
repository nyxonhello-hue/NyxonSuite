import customtkinter as ctk

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

app = ctk.CTk()
app.title('My App')
app.geometry('500x400')

label = ctk.CTkLabel(app, text='Minato test', font=('Arial',20))
label.pack(pady=10)

def on_click():
    print('Clicked')

btn = ctk.CTkButton(app, text='click', command='on_click', corner_radius=8)
btn.pack(pady=10)

entry = ctk.CTkEntry(app, placeholder_text='Type something....', width=200)
entry.pack(pady=10)

value = entry.get()

textbox = ctk.CTkTextbox(app, width=300, height=100)
textbox.pack(pady=10)

textbox.insert('0.0', 'initial text here')

app.mainloop()