import customtkinter as ctk

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

app = ctk.CTk()
app.title("minato")
app.geometry('500x400')

# checkbox
check_var = ctk.BooleanVar()
checkbox = ctk.CTkCheckBox(app, text='I agree', variable=check_var)
checkbox.pack()

#switch
switch_var = ctk.StringVar(value='on')
switch = ctk.CTkSwitch(app, text='Dark mode', variable=switch_var, onvalue='on', offvalue='off')
switch.pack()

#slider
slider = ctk.CTkSlider(app, from_=0, to=100, command=lambda v: print(v))
slider.pack()

#Dropdown
dropdown = ctk.CTkOptionMenu(app, values=['Option1', 'Option2', 'OPtion3'])
dropdown.pack()
print(dropdown.get())

# progress Bar
progress = ctk.CTkProgressBar(app)
progress.pack()
progress.set(0.6)

app.mainloop()