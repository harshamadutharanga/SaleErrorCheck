# pos_pay_details_tab.py

import tkinter as tk
import ttkbootstrap as ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from pos_app_logic import process_form_data_pay, reset_form_fields_pay, execute_query_pay, execute_raw_query_pay

from posip import posip_addresses

def get_ip_by_location(entry_location):
    # Check if the entry_location is present in posip_addresses
    if entry_location in posip_addresses:
        location_set = posip_addresses[entry_location]
        
        # Assuming machine_no (mach_code) determines the exact IP and location
        machine_no = entry_machine_no_pay.get()
        if machine_no in location_set:
            return location_set[machine_no]['ip'], location_set[machine_no]['location']
    
    # Return None if location or machine_no is not found
    return None, None

def create_connection(entry_location):
    ip, location_name = get_ip_by_location(entry_location)
    if ip:
        connection_message = f"{location_name} | {ip}"
    else:
        connection_message = f"Location with code {entry_location} and machine number {entry_machine_no_pay.get()} not found."
    
    # Update the label with the connection message
    connection_message_label.config(text=connection_message)
    return connection_message

def on_submit(pay_details_tab):
    sbu_code = entry_sbu_code_pay.get()
    location = entry_location_pay.get()
    machine_no = entry_machine_no_pay.get()
    
    # Update the connection message
    connection_message = create_connection(location)
    
    date = entry_date_pay.entry.get()  # Get selected date from DateEntry widget
    if date:
        date = datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')  # Format date to 'YYYY-MM-DD'
   
    receipt_no = entry_receipt_no_pay.get()
    paymode = paymode_combobox_pay.get()

    if not location or not date:
        print("Location and Date are required fields.")
        return

    receipt_no_list = receipt_no.split(",") if receipt_no else []

    # Construct the SQL query for detailed results
    query = ("SELECT * FROM pos_pay_details "
             f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND mach_code='{machine_no}' AND txn_date='{date}'")
    
        
    if receipt_no_list:
        receipt_conditions = []
        for item in receipt_no_list:
            item = item.strip()
            if '-' in item:
                start, end = item.split('-')
                receipt_conditions.append(f"receiptno BETWEEN '{start}' AND '{end}'")
            else:
                receipt_conditions.append(f"receiptno='{item}'")
        query += " AND (" + " OR ".join(receipt_conditions) + ")"

    # Add paymode condition if specified
    if paymode:
        query += f" AND pay_mode='{paymode}'"

    # Construct the SQL query for sum of amount
    sumquery = ("SELECT SUM(amount) FROM pos_pay_details "
                f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND mach_code='{machine_no}' AND txn_date='{date}'")
        
    if receipt_no_list:
        sumquery += " AND (" + " OR ".join(receipt_conditions) + ")"
        
    if paymode:
        sumquery += f" AND pay_mode='{paymode}'"

    # Construct the SQL query for total sum of amount (including all receipt numbers)
    total_sum_query = ("SELECT SUM(amount) FROM pos_pay_details "
                      f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND mach_code='{machine_no}' AND txn_date='{date}'")

    # Set the query to the raw SQL query entry
    entry_raw_query_pay.delete(1.0, "end")
    entry_raw_query_pay.insert("end", query)

    # Execute the query and display detailed results
    rows, columns = execute_query_pay(sbu_code, location, machine_no, date, receipt_no_list, paymode)
    display_results(rows, columns)

    # Execute the sum query
    sum_rows, sum_columns = execute_raw_query_pay(sumquery, location, machine_no)
    if sum_rows:
        total_sum = sum_rows[0][0]  # Assuming the result is a single value
        # Display the sum somewhere in your GUI, e.g., update a label
        label_sum_value_pay.config(text=f"{total_sum}")

    # Execute the total sum query (including all receipt numbers)
    total_sum_rows, total_sum_columns = execute_raw_query_pay(total_sum_query, location, machine_no)
    if total_sum_rows:
        total_sum_value = total_sum_rows[0][0]  # Assuming the result is a single value
        # Display the total sum somewhere in your GUI, e.g., update a label
        label_total_sum_value_pay.config(text=f"{total_sum_value}")

    # If a paymode is specified, add or update its label and amount
    if paymode:
        paymode_sum_query = ("SELECT SUM(amount) FROM pos_pay_details "
                             f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND txn_date='{date}'"
                             f" AND pay_mode='{paymode}'")

        if receipt_no_list:
            paymode_sum_query += " AND (" + " OR ".join(receipt_conditions) + ")"
        
        paymode_sum_rows, paymode_sum_columns = execute_raw_query_pay(paymode_sum_query, location, machine_no)
        if paymode_sum_rows:
            paymode_sum = paymode_sum_rows[0][0]  # Assuming the result is a single value
            # Display the paymode sum in a label
            if paymode not in paymode_labels:
                paymode_labels[paymode] = ttk.Label(pay_details_tab, text="", padding=(10, 5))
                paymode_labels[paymode].pack(side="left", padx=10)
            paymode_labels[paymode].config(text=f"{paymode.upper()} Sum: {paymode_sum}")
            
def on_execute_raw_query_pay():
    raw_query = entry_raw_query_pay.get("1.0", "end-1c")  # Get raw SQL query from Text widget
    location = entry_location_pay.get()  # Assuming you have a location field for IP selection
    machine_no = entry_machine_no_pay.get()  # Assuming you have a machine_no field for IP selection

    if raw_query:
        rows, columns = execute_raw_query_pay(raw_query, location, machine_no)
        display_results(rows, columns)            

# Assuming treeview_pay and row_count_label_pay are globally defined widgets

def display_results(rows, columns):
    # Clear existing data in Treeview
    treeview_pay.delete(*treeview_pay.get_children())
    
    if rows and columns:
        # Configure the Treeview with new columns
        treeview_pay['columns'] = columns
        for col in columns:
            treeview_pay.heading(col, text=col)
            treeview_pay.column(col, width=100, anchor="center")

        # Set Treeview style to show grid lines and bootstrap style
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=('Helvetica', 8), 
                        background="white", foreground="black", fieldbackground="light yellow")
        
        style.configure("Treeview.Heading", font=('Helvetica', 8, 'bold'))
        style.map("Treeview", background=[('selected', 'blue')])
        
        # Configure style for cell border
        style.configure("Treeview.Cell", borderwidth=1, relief="solid")

        # Insert rows into the Treeview
        for index, row in enumerate(rows, start=1):
            treeview_pay.insert('', 'end', iid=index, values=row, tags=("Treeview.Cell",))

        # Update row count label
        row_count_label_pay_value.config(text=f"{len(rows)}")
    else:
        # If no rows found, display a message
        treeview_pay['columns'] = ["No data found"]
        treeview_pay.insert('', 'end', values=["No data found"])
        row_count_label_pay_value.config(text="0")



def on_reset():
    # Clear Treeview widget
    treeview_pay.delete(*treeview_pay.get_children())
    
    # Delete display labels for selected sum and total sum
    label_sum_value_pay.config(text="")
    label_total_sum_value_pay.config(text="")
    
    # Clear SQL command displayed in the query text area
    entry_raw_query_pay.delete(1.0, "end")
    
    # Clear connection message
    connection_message_label.config(text="")
    
    # Reset row count label
    row_count_label_pay_value.config(text="")
    
    # Clear all pay mode labels
    for label in paymode_labels.values():
        label.config(text="")
    
    # Reset form fields
    reset_form_fields_pay([entry_location_pay, entry_machine_no_pay, entry_receipt_no_pay, paymode_combobox_pay, entry_raw_query_pay])
    
    # Reset DateEntry widget to empty
    entry_date_pay.delete(0, 'end')
    
    # Reset status combobox
    paymode_combobox_pay.set("")
    
    # Optionally, reset default value in entry_sbu_code
    entry_sbu_code_pay.delete(0, 'end')
    entry_sbu_code_pay.insert(0, "830")

def create_pos_pay_details_tab(notebook):
    pos_pay_details_tab = ttk.Frame(notebook)
    notebook.add(pos_pay_details_tab, text="POS PAY")
    
    form_frame_pay = ttk.Labelframe(pos_pay_details_tab, text="Pos එකේ Payment Details Table එක", padding=(20, 10))
    form_frame_pay.pack(padx=10, pady=10, fill="both", expand="yes")
    
    global entry_sbu_code_pay, entry_location_pay, entry_machine_no_pay, entry_date_pay
    global entry_receipt_no_pay, paymode_combobox_pay, label_sum_value_pay, label_total_sum_value_pay,row_count_label_pay_value
    global treeview_pay, entry_raw_query_pay, paymode_labels, paymode
    global connection_message_label, row_count_label_pay

    paymode_labels = {}

    label_sbu_code_pay = ttk.Label(form_frame_pay, text="SBU Code")
    label_sbu_code_pay.grid(row=0, column=0, padx=5, pady=5, sticky=W)
    entry_sbu_code_pay = ttk.Entry(form_frame_pay, bootstyle="info", width=30)
    entry_sbu_code_pay.insert(0, "830")
    entry_sbu_code_pay.grid(row=0, column=1, padx=5, pady=5, sticky=E)

    label_location_pay = ttk.Label(form_frame_pay, text="Location")
    label_location_pay.grid(row=1, column=0, padx=5, pady=5, sticky=W)
    entry_location_pay = ttk.Entry(form_frame_pay, bootstyle="info", width=30)
    entry_location_pay.grid(row=1, column=1, padx=5, pady=5, sticky=E)

    label_machine_no_pay = ttk.Label(form_frame_pay, text="Machine No (optional, comma-separated)")
    label_machine_no_pay.grid(row=2, column=0, padx=5, pady=5, sticky=W)
    entry_machine_no_pay = ttk.Entry(form_frame_pay, bootstyle="info", width=30)
    entry_machine_no_pay.grid(row=2, column=1, padx=5, pady=5, sticky=E)

    label_date_pay = ttk.Label(form_frame_pay, text="Date")
    label_date_pay.grid(row=3, column=0, padx=5, pady=5, sticky=W)
    entry_date_pay = DateEntry(form_frame_pay, bootstyle="info", width=25)
    entry_date_pay.grid(row=3, column=1, padx=5, pady=5, sticky=E)

    label_receipt_no_pay = ttk.Label(form_frame_pay, text="Receipt No (optional, comma-separated)")
    label_receipt_no_pay.grid(row=4, column=0, padx=5, pady=5, sticky=W)
    entry_receipt_no_pay = ttk.Entry(form_frame_pay, bootstyle="info", width=30)
    entry_receipt_no_pay.grid(row=4, column=1, padx=5, pady=5, sticky=E)

    label_pay_mode_pay = ttk.Label(form_frame_pay, text="Pay Mode (optional)")
    label_pay_mode_pay.grid(row=5, column=0, padx=5, pady=5, sticky=W)
    paymode_combobox_pay = ttk.Combobox(form_frame_pay, values=["cs", "cr", "qr", "gv", "ly", "ch", "fm"], bootstyle="info", width=28)
    paymode_combobox_pay.grid(row=5, column=1, padx=5, pady=5, sticky=E)

    button_submit_pay = ttk.Button(form_frame_pay, text="Submit", bootstyle="success", command=lambda: on_submit(pos_pay_details_tab))
    button_submit_pay.grid(row=6, column=0, padx=5, pady=10, sticky=E)

    button_reset_pay = ttk.Button(form_frame_pay, text="Reset", bootstyle="warning", command=on_reset)
    button_reset_pay.grid(row=6, column=1, padx=5, pady=10, sticky=W)
    
    # Add a new frame for connection message and sum labels on the top right side
    top_right_frame = ttk.Frame(form_frame_pay)
    top_right_frame.grid(row=0, column=2, rowspan=6, padx=5, pady=5, sticky='ne')

    # Define a style for the label
    style = ttk.Style()
    style.configure("PinkBold.TLabel", foreground="#E30B5C", font=("TkDefaultFont", 10, "bold"))

    # Add connection message label to the top right frame
    connection_message_label = ttk.Label(top_right_frame, text="", style="PinkBold.TLabel")
    connection_message_label.grid(row=0, column=0, padx=5, pady=5, sticky='nw')


    # Add sum and total sum labels inside the new frame
    label_sum = ttk.Label(top_right_frame, text="Sum:")
    label_sum.grid(row=1, column=0, padx=5, pady=5, sticky=W)
    label_sum_value_pay = ttk.Label(top_right_frame, text="")
    label_sum_value_pay.grid(row=1, column=1, padx=5, pady=5, sticky=W)

    label_total_sum = ttk.Label(top_right_frame, text="Total Sum:")
    label_total_sum.grid(row=2, column=0, padx=5, pady=5, sticky=W)
    label_total_sum_value_pay = ttk.Label(top_right_frame, text="")
    label_total_sum_value_pay.grid(row=2, column=1, padx=5, pady=5, sticky=W)
   
    row_count_label_pay = ttk.Label(top_right_frame, text="Row Count: ")
    row_count_label_pay.grid(row=3, column=0, padx=5, pady=5, sticky=W)
    row_count_label_pay_value = ttk.Label(top_right_frame, text="")
    row_count_label_pay_value.grid(row=3, column=1, padx=5, pady=5, sticky=W)
    
    raw_query_frame_pay = ttk.Labelframe(pos_pay_details_tab, text="Raw SQL Query", padding=(20, 10))
    raw_query_frame_pay.pack(padx=10, pady=10, fill="both", expand="yes")
    
    entry_raw_query_pay = ttk.Text(raw_query_frame_pay, width=160, height=7, wrap="word")
    entry_raw_query_pay.pack(padx=20, pady=10, fill="both", expand=True)
    
    execute_raw_query_button = ttk.Button(raw_query_frame_pay, text="Execute Raw Query", bootstyle=SUCCESS, command=on_execute_raw_query_pay)
    execute_raw_query_button.pack(padx=5, pady=5)
    
    results_frame_pay = ttk.Labelframe(pos_pay_details_tab, text="Results", padding=(20, 10))
    results_frame_pay.pack(padx=10, pady=10, fill="both", expand="yes")
    
    treeview_pay = ttk.Treeview(results_frame_pay, show='headings')
    treeview_pay.pack(fill="both", expand="yes", padx=10, pady=10)
    
    return pos_pay_details_tab


    

