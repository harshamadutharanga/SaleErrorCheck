import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from det_tab import create_det_tab
from mas_tab import create_mas_tab
from pay_details_tab import create_pay_details_tab
from pos_mas_tab import create_pos_mas_tab
from pos_det_tab import create_pos_det_tab
from pos_pay_details_tab import create_pos_pay_details_tab
from query_tab import create_query_tab

def switch_theme():
    theme = "darkly" if theme_var.get() else "flatly"
    app.style.theme_use(theme)
    configure_tab_style()
    switch_button.config(text="Dark Theme" if theme_var.get() else "Light Theme")

def configure_tab_style():
    style = ttk.Style()
    style.configure('TNotebook.Tab', width=20)  # Set the desired width for the tabs
    style.map('TNotebook.Tab',
              background=[('selected', style.colors.success)],
              foreground=[('selected', 'white')])

def main():
    global app, theme_var, switch_button

    app = ttk.Window(themename="flatly")
    app.title("Arpico Sale Error fix >> Devoloped By Harsha Palihawadana")
    app.geometry("1200x800")

    # Create a frame for the switch button
    switch_frame = ttk.Frame(app)
    switch_frame.pack(side="top", fill="x", pady=5)

    # Create a switch button with blue color
    theme_var = tk.BooleanVar(value=False)
    switch_button = ttk.Checkbutton(
        switch_frame,
        text="Light Theme",
        variable=theme_var,
        bootstyle="success-round-toggle",
        command=switch_theme
    )
    switch_button.pack(side="right", padx=10)

    configure_tab_style()

    # Create a notebook with tabs aligned to the right
    notebook = ttk.Notebook(app, bootstyle="primary", style='TNotebook')
    notebook.pack(fill="both", expand="yes")

    global mas_widgets, det_widgets, pay_details_widgets, pos_mas_widgets, pos_det_widgets, pos_pay_widgets, query_tab
    mas_widgets = create_mas_tab(notebook)
    det_widgets = create_det_tab(notebook)
    pay_details_widgets = create_pay_details_tab(notebook)

    
    # Create and add new tabs for POS MAS, POS DET, and POS PAY
    pos_mas_widgets = create_pos_mas_tab(notebook)
    pos_det_widgets = create_pos_det_tab(notebook)
    pos_pay_widgets = create_pos_pay_details_tab(notebook)
    
    query_tab = create_query_tab(notebook)

    # Initialize the widgets in the new tabs (if any)
    # pos_mas_widgets = create_pos_mas_tab(notebook)  # Uncomment and define if needed
    # pos_det_widgets = create_pos_det_tab(notebook)  # Uncomment and define if needed
    # pos_pay_widgets = create_pos_pay_details_tab(notebook)  # Uncomment and define if needed

    app.mainloop()

if __name__ == "__main__":
    main()
