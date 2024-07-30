import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from pos_app_logic import process_form_data, reset_form_fields, execute_query, execute_raw_query
from datetime import datetime
from posip import posip_addresses

def get_ip_by_location(entry_location):
    # Check if the entry_location is present in posip_addresses
    if entry_location in posip_addresses:
        location_set = posip_addresses[entry_location]
        
        # Assuming machine_no (mach_code) determines the exact IP and location
        machine_no = entry_machine_no.get()
        if machine_no in location_set:
            return location_set[machine_no]['ip'], location_set[machine_no]['location']
    
    # Return None if location or machine_no is not found
    return None, None

def create_connection(entry_location):
    ip, location_name = get_ip_by_location(entry_location)
    if ip:
        connection_message = f"{location_name} | {ip}"
    else:
        connection_message = f"Location with code {entry_location} and machine number {entry_machine_no.get()} not found."
    
    # Update the label with the connection message
    connection_message_label.config(text=connection_message)
    return connection_message

def on_submit():
    sbu_code = entry_sbu_code.get()
    location = entry_location.get()
    machine_no = entry_machine_no.get()
    
    # Update the connection message
    connection_message = create_connection(location)
    
    date = entry_date.entry.get()  # Get selected date from DateEntry widget
    if date:
        date = datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')  # Format date to 'YYYY-MM-DD'
    
    receipt_no = entry_receipt_no.get()
    status = status_combobox.get()

    if not location or not date:
        print("Location and Date are required fields.")
        return


    receipt_no_list = receipt_no.split(",") if receipt_no else []

    # Construct the SQL query for detailed results
    query = ("SELECT * FROM pos_txn_mas "
             f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND mach_code='{machine_no}' AND txn_date='{date}' ")
    

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

    if status:
        if status == 'VALID':
            query += " AND inv_status='VALID'"
        elif status == 'CAN':
            query += " AND inv_status='CAN'"

    # Construct the SQL query for sum of net_amt
    sumquery = ("SELECT SUM(net_amt) FROM pos_txn_mas "
                f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND txn_date='{date}' AND mach_code='{machine_no}'")
    

        
    if receipt_no_list:
        sumquery += " AND (" + " OR ".join(receipt_conditions) + ")"

    if status:
        if status == 'VALID':
            sumquery += " AND inv_status='VALID'"
        elif status == 'CAN':
            sumquery += " AND inv_status='CAN'"

    # Construct the SQL query for total sum of net_amt (without receipt number filter)
    total_sum_query = ("SELECT SUM(net_amt) FROM pos_txn_mas "
                      f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}'  AND mach_code='{machine_no}' AND txn_date='{date}'")
    
    if status:
        if status == 'VALID':
            total_sum_query += " AND inv_status='VALID'"
        elif status == 'CAN':
            total_sum_query += " AND inv_status='CAN'"

    # Set the query to the raw SQL query entry
    entry_raw_query.delete(1.0, "end")
    entry_raw_query.insert("end", query)

    # Execute the query and display detailed results
    rows, columns = execute_query(sbu_code, location, machine_no, date, receipt_no_list, status)
    
    
    display_results(rows, columns)

    # Execute the sum query
    sum_rows, sum_columns = execute_raw_query(sumquery, location, machine_no)
    
    
    if sum_rows:
        total_sum = sum_rows[0][0]  # Assuming the result is a single value
        # Display the sum somewhere in your GUI, e.g., update a label
        label_sum_value.config(text=f"{total_sum}")

    # Execute the total sum query (without receipt number filter)
    total_sum_rows, total_sum_columns = execute_raw_query(total_sum_query, location, machine_no)
    if total_sum_rows:
        total_sum_value = total_sum_rows[0][0]  # Assuming the result is a single value
        # Display the total sum somewhere in your GUI, e.g., update a label
        label_total_sum_value.config(text=f"{total_sum_value}")

def on_execute_raw_query():
    raw_query = entry_raw_query.get("1.0", "end-1c")  # Get raw SQL query from Text widget
    location = entry_location.get()  # Assuming you have a location field for IP selection
    machine_no = entry_machine_no.get()

    if raw_query:
        rows, columns = execute_raw_query(raw_query, location, machine_no)
        display_results(rows, columns)


def display_results(rows, columns):
    # Clear existing data in Treeview
    treeview.delete(*treeview.get_children())
    
    if rows:
        # Populate the Treeview with new data
        treeview['columns'] = columns
        treeview["show"] = "headings"  # Hide the default blank column at the beginning
        
        # Configure Treeview style
        style = ttk.Style()
        style.configure("Treeview", background="white", foreground="black", rowheight=25, fieldbackground="light yellow")
        style.configure("Treeview.Heading", font=('Helvetica', 8, 'bold'))
        style.configure("Treeview.Cell", borderwidth=1, relief="solid")
        
        for col in columns:
            treeview.heading(col, text=col)
            treeview.column(col, width=100, anchor="center")  # Adjust anchor as needed
        
        # Batch insert rows
        for index, row in enumerate(rows, start=1):
            treeview.insert('', 'end', iid=index, values=row, tags=("Treeview.Cell",))
        
        # Set the row count
        row_count_label_pos_mas_value.config(text=f"{len(rows)}")
    else:
        # If no rows found, display a message
        treeview['columns'] = []
        treeview.insert('', 'end', values=["No data found."])
        row_count_label_pos_mas_value.config(text="0")

def on_reset():
    # Clear Treeview widget
    treeview.delete(*treeview.get_children())
    
    # Delete display labels for selected sum and total sum
    label_sum_value.config(text="")
    label_total_sum_value.config(text="")
    
    # Clear SQL command displayed in the query text area
    entry_raw_query.delete(1.0, "end")
    
    # Clear connection message
    connection_message_label.config(text="")
    
    # Reset row count label
    row_count_label_pos_mas_value.config(text="")
    
    # Reset form fields
    reset_form_fields([entry_location, entry_machine_no, entry_receipt_no, entry_raw_query])
    
    # Reset DateEntry widget to empty
    entry_date.delete(0, 'end')
    
    # Reset status combobox
    status_combobox.set("")
    
    # Optionally, reset default value in entry_sbu_code
    entry_sbu_code.delete(0, 'end')
    entry_sbu_code.insert(0, "830")
    
def create_pos_mas_tab(notebook):
    pos_mas_tab = ttk.Frame(notebook)
    notebook.add(pos_mas_tab, text="POS MAS")
    
    form_frame = ttk.Labelframe(pos_mas_tab, text="Pos එකේ Mas Table එක", padding=(20, 10))
    form_frame.pack(padx=10, pady=10, fill="both", expand="yes")

    global entry_sbu_code, entry_location, entry_machine_no, entry_date, entry_receipt_no, status_combobox
    global label_sum_value, label_total_sum_value, treeview, entry_raw_query
    global connection_message_label, row_count_label_pos_mas, row_count_label_pos_mas_value
    
    label_sbu_code = ttk.Label(form_frame, text="SBU Code")
    label_sbu_code.grid(row=0, column=0, padx=5, pady=5, sticky=W)
    default_sbu_code = "830"
    entry_sbu_code = ttk.Entry(form_frame, bootstyle="info", width=30)
    entry_sbu_code.insert(0, default_sbu_code)
    entry_sbu_code.grid(row=0, column=1, padx=5, pady=5, sticky=E)

    label_location = ttk.Label(form_frame, text="Location")
    label_location.grid(row=1, column=0, padx=5, pady=5, sticky=W)
    entry_location = ttk.Entry(form_frame, bootstyle="info", width=30)
    entry_location.grid(row=1, column=1, padx=5, pady=5, sticky=E)

    label_machine_no = ttk.Label(form_frame, text="Machine No (optional, comma-separated)")
    label_machine_no.grid(row=2, column=0, padx=5, pady=5, sticky=W)
    entry_machine_no = ttk.Entry(form_frame, bootstyle="info", width=30)
    entry_machine_no.grid(row=2, column=1, padx=5, pady=5, sticky=E)

    label_date = ttk.Label(form_frame, text="Date")
    label_date.grid(row=3, column=0, padx=5, pady=5, sticky=W)
    entry_date = DateEntry(form_frame, bootstyle="info", width=25)
    entry_date.grid(row=3, column=1, padx=5, pady=5, sticky=E)

    label_receipt_no = ttk.Label(form_frame, text="Receipt No (optional, comma-separated)")
    label_receipt_no.grid(row=4, column=0, padx=5, pady=5, sticky=W)
    entry_receipt_no = ttk.Entry(form_frame, bootstyle="info", width=30)
    entry_receipt_no.grid(row=4, column=1, padx=5, pady=5, sticky=E)

    label_status = ttk.Label(form_frame, text="Status")
    label_status.grid(row=5, column=0, padx=5, pady=5, sticky=W)
    status_combobox = ttk.Combobox(form_frame, bootstyle="info", values=["", "VALID", "CAN"], width=28)
    status_combobox.grid(row=5, column=1, padx=5, pady=5, sticky=E)
    
    button_frame = ttk.Frame(form_frame)
    button_frame.grid(row=6, columnspan=2, pady=10)

    submit_button = ttk.Button(button_frame, text="Submit", bootstyle=SUCCESS, command=on_submit)
    submit_button.grid(row=0, column=0, padx=10, pady=5)

    reset_button = ttk.Button(button_frame, text="Reset", bootstyle=DANGER, command=on_reset)
    reset_button.grid(row=0, column=1, padx=5, pady=5)

    # Add a new frame for connection message and sum labels on the top right side
    top_right_frame = ttk.Frame(form_frame)
    top_right_frame.grid(row=0, column=2, rowspan=6, padx=5, pady=5, sticky=NE)

    # Define a style for the label
    style = ttk.Style()
    style.configure("PinkBold.TLabel", foreground="#E30B5C", font=("TkDefaultFont", 10, "bold"))

    # Add connection message label to the top right frame
    connection_message_label = ttk.Label(top_right_frame, text="", style="PinkBold.TLabel")
    connection_message_label.grid(row=0, column=0, padx=5, pady=5, sticky='nw')

    # Add sum and total sum labels inside the new frame
    label_sum = ttk.Label(top_right_frame, text="Sum:")
    label_sum.grid(row=1, column=0, padx=5, pady=5, sticky=W)
    label_sum_value = ttk.Label(top_right_frame, text="")
    label_sum_value.grid(row=1, column=1, padx=5, pady=5, sticky=W)

    label_total_sum = ttk.Label(top_right_frame, text="Total Sum:")
    label_total_sum.grid(row=2, column=0, padx=5, pady=5, sticky=W)
    label_total_sum_value = ttk.Label(top_right_frame, text="")
    label_total_sum_value.grid(row=2, column=1, padx=5, pady=5, sticky=W)    
    
    row_count_label_pos_mas = ttk.Label(top_right_frame, text="Row Count: ")
    row_count_label_pos_mas.grid(row=3, column=0, padx=5, pady=5, sticky=W)
    row_count_label_pos_mas_value = ttk.Label(top_right_frame, text="")
    row_count_label_pos_mas_value.grid(row=3, column=1, padx=5, pady=5, sticky=W)

    raw_query_frame = ttk.Labelframe(pos_mas_tab, text="Raw SQL Query", padding=(20, 10))
    raw_query_frame.pack(padx=10, pady=10, fill="both", expand="yes")

    entry_raw_query = ttk.Text(raw_query_frame, height=7)
    entry_raw_query.pack(padx=5, pady=5, fill="both", expand="yes")

    execute_raw_query_button = ttk.Button(raw_query_frame, text="Execute Raw Query", bootstyle=SUCCESS, command=on_execute_raw_query)
    execute_raw_query_button.pack(padx=5, pady=5)

    results_frame = ttk.Labelframe(pos_mas_tab, text="Results", padding=(20, 10))
    results_frame.pack(padx=10, pady=10, fill="both", expand="yes")

    treeview = ttk.Treeview(results_frame)
    treeview.pack(padx=5, pady=5, fill="both", expand="yes")

    return pos_mas_tab
