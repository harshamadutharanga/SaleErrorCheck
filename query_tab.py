import mysql.connector
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from app_logic import process_form_data, reset_form_fields, execute_query, execute_raw_query
from datetime import datetime
from testip import ip_addresses
import tkinter as tk
from tkinter import messagebox, simpledialog
import re

# Define global variables
entry_location = None
entry_sbu_code = None
treeview = None
row_count_label_value = None
entry_edit = None
connection_message_label = None
top_right_frame = None
query_entry = None
table_list = None
where_button = None
insert_button = None

def get_ip_by_location(entry_location):
    for location_set in ip_addresses.values():
        if entry_location in location_set:
            return location_set[entry_location]['ip'], location_set[entry_location]['location']
    return None, None

def create_connection(entry_location):
    ip, location_name = get_ip_by_location(entry_location)
    if ip:
        connection_message = f"{location_name} | {ip}"
        connection_params = {
            'host': ip,
            'port': 3306,
            'user': 'harsha',
            'password': 'har%123',
            'database': 'marksys',
            'charset': 'utf8'
        }

        try:
            connection = mysql.connector.connect(**connection_params)
            fetch_tables(connection)  # Fetch tables after connecting
            connection.close()  # Close the connection after fetching
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection_message = "Failed to connect to database."
    else:
        connection_message = f"Location with code {entry_location} not found."
    
    connection_message_label.config(text=connection_message)
    return connection_message

def fetch_tables(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        table_list.delete(0, tk.END)  # Clear previous table entries
        for (table_name,) in tables:
            table_list.insert(tk.END, table_name)  # Add table names to the Listbox
        
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

def on_submit():
    location = entry_location.get()
    create_connection(location)

def on_run_query():
    global table_double_click_called
    raw_query = query_entry.get("1.0", "end-1c")
    location = entry_location.get()

    if raw_query:
        if table_double_click_called:
            limit_value = simpledialog.askinteger("Limit", "Enter the number of rows to display:", minvalue=1)
            if limit_value is not None:
                if "LIMIT" in raw_query.upper():
                    raw_query = raw_query.rsplit("LIMIT", 1)[0].strip()
                raw_query += f" LIMIT {limit_value}"

            # Update the query entry field
            query_entry.delete("1.0", tk.END)
            query_entry.insert(tk.END, raw_query)

        # Execute the query and fetch results
        try:
            rows, columns = execute_raw_query(raw_query, location)
            display_query_results(rows, columns)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        
        # Reset the flag after running the query
        table_double_click_called = False


def display_query_results(rows, columns):
    treeview.delete(*treeview.get_children())

    if rows:
        treeview['columns'] = columns
        treeview["show"] = "headings"

        for col in columns:
            min_width = 100
            treeview.heading(col, text=col)
            treeview.column(col, width=min_width, anchor="center", stretch=tk.NO)

        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=('Helvetica', 8), 
                        background="white", foreground="black", fieldbackground="light yellow")
        style.configure("Treeview.Heading", font=('Helvetica', 8, 'bold'), 
                        background="#17a2b8", foreground="white")

        for index, row in enumerate(rows, start=1):
            treeview.insert('', 'end', iid=index, values=row)

        row_count_label_value.config(text=f"{len(rows)}")
        treeview.bind("<Double-Button-1>", on_treeview_double_click)  # Bind double-click event to the Treeview
    else:
        treeview['columns'] = []
        treeview.insert('', 'end', values=["No data found."])
        row_count_label_value.config(text="0")

def on_treeview_click(event):
    # Get the item that was clicked
    item = treeview.identify('item', event.x, event.y)
    if item:
        # Get the column where the click happened
        col = treeview.identify_column(event.x)
        if col:
            # Remove the green cell tag from all cells
            for row in treeview.get_children():
                treeview.item(row, tags=())
            
            # Apply green cell tag to the clicked cell
            treeview.item(item, tags=('GreenCell',))

def on_treeview_double_click(event):
    # Get the item and the column that was clicked
    selected_item = treeview.focus()
    column_id = treeview.identify_column(event.x)  # Get the column ID
    col_index = int(column_id.replace('#', '')) - 1  # Convert column ID to index
    
    if where_button['text'] == "Command":
        if selected_item and col_index >= 0:
            # Get the name of the column (header)
            col_name = treeview.heading(column_id)["text"]
        
            # Prompt user for the value to replace in the new query
            value = simpledialog.askstring("Input", f"Enter value for {col_name}:")
        
            if value is not None and value.strip():  # Ensure a value is entered
                # Get the current query
                current_query = query_entry.get('1.0', 'end-1c').strip()

                # Check if there's already a WHERE clause in the query
                if "WHERE" in current_query.upper():
                    # Append the new condition with AND if there are already conditions
                    if current_query.strip().upper().endswith("WHERE"):
                        new_query = f"{current_query} {col_name}='{value.strip()}'"
                    else:
                        new_query = f"{current_query} AND {col_name}='{value.strip()}'"
                else:
                    # Add the WHERE clause with the first condition
                    new_query = f"{current_query} WHERE {col_name}='{value.strip()}'"

                # Update the query entry field
                query_entry.delete("1.0", tk.END)
                query_entry.insert(tk.END, new_query)
    else:
        # Copy current cell value to clipboard
        current_value = treeview.item(selected_item, 'values')[col_index]
        treeview.clipboard_clear()  # Clear the clipboard
        treeview.clipboard_append(current_value)  # Append the current cell value to the clipboard
        treeview.update()  # Update clipboard to ensure the value is available

        # Show message indicating value is copied
        messagebox.showinfo("Copied to Clipboard", f"Value '{current_value}' copied to clipboard.")

def on_insert():
    if insert_button['text'] == "Insert":
        insert_button.config(text="Set Value")
        # Get the current query from the query_entry
        raw_query = query_entry.get("1.0", "end-1c").strip()

        # Check if "LIMIT" is present and remove it
        if "LIMIT" in raw_query.upper():
            raw_query = raw_query.rsplit("LIMIT", 1)[0].strip()
    
            # Update the query entry field to add WHERE clause
            query_entry.delete("1.0", tk.END)
            query_entry.insert(tk.END, raw_query + " VALUES ")
            
        if "SELECT * FROM" in raw_query.upper():
            raw_query = raw_query.rsplit("SELECT * FROM", 1)[0].strip()
            
            # Update the query entry field to add WHERE clause
            query_entry.delete("1.0", tk.END)
            query_entry.insert(tk.END, raw_query + " INSERT INTO ")
                    
    else:   
        insert_button.config(text="Insert")

def on_save_edit():
    selected_item = treeview.focus()
    if selected_item:
        new_value = entry_edit.get()
        column = treeview.identify_column(treeview.winfo_pointerx(), treeview.winfo_pointery())
        col_index = int(column.replace('#', '')) - 1
        
        values = list(treeview.item(selected_item, 'values'))
        values[col_index] = new_value  # Update the selected cell value
        treeview.item(selected_item, values=values)  # Update the treeview with new values
        
        entry_edit.grid_forget()  # Hide the entry field after editing

def on_reset():
    treeview.delete(*treeview.get_children())
    connection_message_label.config(text="")
    row_count_label_value.config(text="")
    where_button.config(text="Where")
    reset_form_fields([entry_location])
    query_entry.delete("1.0", tk.END)
    entry_sbu_code.delete(0, 'end')
    entry_sbu_code.insert(0, "830")
    
# Define a global flag to check if table double-click was called
table_double_click_called = False

def on_table_double_click(event):
    global table_double_click_called
    selected_table = table_list.get(table_list.curselection())
    query_entry.delete("1.0", tk.END)  # Clear the query entry field
    query_entry.insert(tk.END, f"SELECT * FROM {selected_table}")
    
    # Set the flag to indicate table double-click occurred
    table_double_click_called = True
    
def on_where_query():
    if where_button['text'] == "Where":
        where_button.config(text="Command")
        # Get the current query from the query_entry
        raw_query = query_entry.get("1.0", "end-1c").strip()

        # Check if "LIMIT" is present and remove it
        if "LIMIT" in raw_query.upper():
            raw_query = raw_query.rsplit("LIMIT", 1)[0].strip()
    
            # Update the query entry field to add WHERE clause
            query_entry.delete("1.0", tk.END)
            query_entry.insert(tk.END, raw_query + " WHERE ")
        
    else:   
        where_button.config(text="Where")

def create_query_tab(notebook):
    query_tab = ttk.Frame(notebook)
    notebook.add(query_tab, text="Marksys")

    sub_notebook = ttk.Notebook(query_tab)
    sub_notebook.pack(fill="both", expand=True, padx=10, pady=10)

    tab_management_frame = ttk.Frame(query_tab)
    tab_management_frame.pack(fill="x", padx=10, pady=5)
    
    add_tab_button = ttk.Button(tab_management_frame, text="+ Add Tab", command=lambda: create_query_sub_tab(sub_notebook))
    add_tab_button.pack(side="right")

    create_query_sub_tab(sub_notebook)

def create_query_sub_tab(sub_notebook):
    sub_tab_index = len(sub_notebook.tabs()) + 1
    sub_tab_title = f"Sub Tab {sub_tab_index}"
    
    sub_tab = ttk.Frame(sub_notebook)
    tab_id = sub_notebook.add(sub_tab, text=sub_tab_title)
    
    # Create custom tab header with close button
    create_custom_tab_header(sub_notebook, tab_id, sub_tab_title)

    form_frame = ttk.Labelframe(sub_tab, text="Run Query", padding=(20, 10))
    form_frame.pack(padx=5, pady=5, fill="both", expand=True)
    form_frame.columnconfigure(0, weight=1)
    form_frame.columnconfigure(1, weight=4)

    global entry_sbu_code, entry_location, treeview, row_count_label_value, entry_edit
    global connection_message_label, top_right_frame, query_entry, root
    global table_list, where_button, insert_button
    
    label_sbu_code = ttk.Label(form_frame, text="SBU Code")
    label_sbu_code.grid(row=0, column=0, padx=2, pady=2, sticky="W")
    default_sbu_code = "830"
    entry_sbu_code = ttk.Entry(form_frame, bootstyle="info", width=20)
    entry_sbu_code.insert(0, default_sbu_code)
    entry_sbu_code.grid(row=0, column=1, pady=2, sticky="W")

    label_location = ttk.Label(form_frame, text="Location")
    label_location.grid(row=1, column=0, padx=2, pady=2, sticky="W")
    entry_location = ttk.Entry(form_frame, bootstyle="info", width=20)
    entry_location.grid(row=1, column=1, sticky="W")

    top_right_frame = ttk.Frame(form_frame)
    top_right_frame.grid(row=0, column=2, rowspan=6, padx=5, pady=5, sticky="NE")
    
    connection_message_label = ttk.Label(top_right_frame, text="", style="PinkBold.TLabel")
    connection_message_label.grid(row=0, column=0, padx=5, pady=5, sticky='nw')
    
    database_label = ttk.Label(top_right_frame, text="Database: Marksys", style="PinkBold.TLabel")
    database_label.grid(row=1, column=0, padx=5, pady=5, sticky='nw')
    
    button_frame = ttk.Frame(form_frame)
    button_frame.grid(row=2, columnspan=2, pady=10, padx=100, sticky='W')

    query_entry_frame = ttk.Labelframe(form_frame, text="Enter Query", padding=(10, 5))
    query_entry_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')

    query_entry = tk.Text(query_entry_frame, height=10, width=30)
    query_entry.pack(fill="both", expand=True)
    
    submit_button = ttk.Button(query_entry_frame, text="Submit", bootstyle="info", command=on_submit)
    submit_button.pack(side="left", padx=5, pady=5)
    
    where_button = ttk.Button(query_entry_frame, text="Where", bootstyle="warning", command=on_where_query)
    where_button.pack(side="left", padx=5, pady=5)
    
    insert_button = ttk.Button(query_entry_frame, text="Insert", bootstyle="info", command=on_insert)
    insert_button.pack(side="left", padx=5, pady=5)
    
    save_button = ttk.Button(query_entry_frame, text="Save Edit", bootstyle="success", command=on_save_edit)
    save_button.pack(side="left", padx=5, pady=5)
    
    reset_button = ttk.Button(query_entry_frame, text="Reset", bootstyle="danger", command=on_reset)
    reset_button.pack(side="left", padx=5, pady=5)

    run_query_button = ttk.Button(query_entry_frame, text="Run Query", bootstyle="info", command=on_run_query)
    run_query_button.pack(side="right", padx=5, pady=5)

    xscrollbar = ttk.Scrollbar(form_frame, orient='horizontal', command=query_entry.xview)
    xscrollbar.grid(row=4, column=0, columnspan=3, sticky='ew')

    treeview = ttk.Treeview(form_frame, xscrollcommand=xscrollbar.set)
    treeview.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')
    xscrollbar.config(command=treeview.xview)

    row_count_label_value = ttk.Label(form_frame, text="0")
    row_count_label_value.grid(row=6, column=0, columnspan=3, pady=5)

    form_frame.rowconfigure(5, weight=1)
    form_frame.columnconfigure(0, weight=1)

    entry_edit = ttk.Entry(form_frame)
    entry_edit.grid(row=6, column=1, padx=5, pady=5)
    entry_edit.grid_forget()  # Initially hide the entry

    table_list_frame = ttk.Labelframe(form_frame, text="Tables", padding=(10, 5))
    table_list_frame.grid(row=0, column=3, rowspan=6, padx=5, pady=5, sticky='nsew')

    table_list = tk.Listbox(table_list_frame, height=15, width=30)
    table_list.pack(fill="both", expand=True)
    table_list.bind("<Double-Button-1>", on_table_double_click)

def create_custom_tab_header(notebook, tab_id, tab_title):
    tab_frame = tk.Frame(notebook)
    
    tab_label = tk.Label(tab_frame, text=tab_title)
    tab_label.pack(side="left", padx=5, pady=5)
    
    close_button = tk.Button(tab_frame, text="X", width=2, command=lambda: close_tab(notebook, tab_id))
    close_button.pack(side="right", padx=5, pady=5)
    
    # Need to update the tab header with the new frame
    # This part is not supported directly by ttk.Notebook
    # To simulate custom headers, manage a dictionary to map tab_ids to custom headers

def close_tab(notebook, tab_id):
    if len(notebook.tabs()) > 1:
        notebook.forget(tab_id)
    else:
        messagebox.showwarning("Cannot Close Tab", "You must have at least one tab open.")

# Dummy functions for button commands
def on_submit():
    pass

def on_where_query():
    pass

def on_insert():
    pass

def on_save_edit():
    pass

def on_reset():
    pass

def on_run_query():
    pass

def on_table_double_click(event):
    pass

if __name__ == "__main__":
    root = tk.Tk()  # Initialize root window
    notebook = ttk.Notebook(root)
    create_query_tab(notebook)
    notebook.pack(fill="both", expand=True)
    root.mainloop()
