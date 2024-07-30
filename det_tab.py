import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from app_logic import process_form_data_det, reset_form_fields_det, execute_query_det, execute_raw_query_det
from testip import ip_addresses
import random

def get_ip_by_location(entry_location):
    for location_set in ip_addresses.values():
        if entry_location in location_set:
            return location_set[entry_location]['ip'], location_set[entry_location]['location']
    return None, None

def create_connection(entry_location):
    ip, location_name = get_ip_by_location(entry_location)
    if ip:
        connection_message = f"{location_name} | {ip}"
    else:
        connection_message = f"Location with code {entry_location} not found."
    
    # Update the label with the connection message
    connection_message_label.config(text=connection_message)
    return connection_message


def on_submit_det():
    sbu_code = entry_sbu_code_det.get()
    location = entry_location_det.get()
    machine_no = entry_machine_no_det.get()
    
    # Update the connection message
    connection_message = create_connection(location)
    
    date = entry_date_det.entry.get()  # Get selected date from DateEntry widget
    if date:
        date = datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')  # Format date to 'YYYY-MM-DD'
    
    receipt_no = entry_receipt_no_det.get()
    status = status_combobox_det.get()
    seq_no = entry_seq_no_det.get()  # Get seq_no input
    
    if not location or not date:
        print("Location and Date are required fields.")
        return

    machine_no_list = machine_no.split(",") if machine_no else []
    receipt_no_list = receipt_no.split(",") if receipt_no else []
    seq_no_list = seq_no.split(",") if seq_no else []

    # Construct the SQL query for detailed results
    query = ("SELECT * FROM rms_pos_txn_det "
             f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND txn_date='{date}'")
    
    if machine_no_list:
        machine_conditions = []
        for item in machine_no_list:
            item = item.strip()
            if '-' in item:
                start, end = item.split('-')
                machine_conditions.append(f"mach_code BETWEEN '{start}' AND '{end}'")
            else:
                machine_conditions.append(f"mach_code='{item}'")
        query += " AND (" + " OR ".join(machine_conditions) + ")"
        
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

    if seq_no_list:
        seq_conditions = []
        for item in seq_no_list:
            item = item.strip()
            if '-' in item:
                start, end = item.split('-')
                seq_conditions.append(f"seq_no BETWEEN '{start}' AND '{end}'")
            else:
                seq_conditions.append(f"seq_no='{item}'")
        query += " AND (" + " OR ".join(seq_conditions) + ")"
            

    if status:
        if status == 'VALID':
            query += " AND inv_status='VALID'"
        elif status == 'CAN':
            query += " AND inv_status='CAN'"

    # Construct the SQL query for sum of net_amt
    sumquery = ("SELECT SUM(price*qty-disc_amt) FROM rms_pos_txn_det "
                f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND txn_date='{date}'")
    
    if machine_no_list:
        sumquery += " AND (" + " OR ".join(machine_conditions) + ")"
        
    if receipt_no_list:
        sumquery += " AND (" + " OR ".join(receipt_conditions) + ")"
        
    if seq_no_list:
        sumquery += " AND (" + " OR ".join(seq_conditions) + ")"

    if status:
        if status == 'VALID':
            sumquery += " AND inv_status='VALID'"
        elif status == 'CAN':
            sumquery += " AND inv_status='CAN'"

    # Construct the SQL query for total sum of net_amt (including all receipt numbers)
    total_sum_query = ("SELECT SUM(price*qty-disc_amt) FROM rms_pos_txn_det "
                      f"WHERE sbu_code='{sbu_code}' AND loc_code='{location}' AND txn_date='{date}'")
    
    if machine_no_list:
        total_sum_query += f" AND mach_code='{machine_no}'"
    
    if status:
        if status == 'VALID':
            total_sum_query += " AND inv_status='VALID'"
        elif status == 'CAN':
            total_sum_query += " AND inv_status='CAN'"
            
        UnfinalizedQuery = f"""
    SELECT ar.receiptno
    FROM (
        SELECT receiptno
        FROM rms_pos_txn_mas
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
        UNION
        SELECT receiptno
        FROM rms_pos_txn_det
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
    ) ar
    LEFT JOIN (
        SELECT receiptno
        FROM rms_pos_txn_mas
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
    ) mr ON ar.receiptno = mr.receiptno
    LEFT JOIN (
        SELECT receiptno
        FROM rms_pos_txn_det
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
    ) dr ON ar.receiptno = dr.receiptno
    WHERE mr.receiptno IS NULL
      AND dr.receiptno IS NULL

    UNION

    -- Select receipt numbers that are in pos_txn_mas but not in pos_txn_det
    SELECT mas_receipts.receiptno
    FROM (
        SELECT receiptno
        FROM rms_pos_txn_mas
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
    ) mas_receipts
    LEFT JOIN (
        SELECT receiptno
        FROM rms_pos_txn_det
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
    ) det_receipts ON mas_receipts.receiptno = det_receipts.receiptno
    WHERE det_receipts.receiptno IS NULL

    UNION

    -- Select receipt numbers that are in rms_pos_txn_det but not in pos_txn_mas
    SELECT det_receipts.receiptno
    FROM (
        SELECT receiptno
        FROM rms_pos_txn_det
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
    ) det_receipts
    LEFT JOIN (
        SELECT receiptno
        FROM rms_pos_txn_mas
        WHERE sbu_code='{sbu_code}'
          AND loc_code='{location}'
          AND txn_date='{date}'
          AND mach_code='{machine_no}'
          AND inv_status='{status}'
    ) mas_receipts ON det_receipts.receiptno = mas_receipts.receiptno
    WHERE mas_receipts.receiptno IS NULL;
    """ 
    
    ExceptionQuery = "SELECT mach_code, user_id, err_desc, reciptno, net_value, det_value FROM rms_pos_excep_rpt_tmp"           

    # Set the query to the raw SQL query entry
    entry_raw_query_det.delete(1.0, "end")
    entry_raw_query_det.insert("end", query)

    # Execute the query and display detailed results
    rows, columns = execute_query_det(sbu_code, location, machine_no_list, date, receipt_no_list, status, seq_no_list)
    display_results(rows, columns)

    # Execute the sum query
    sum_rows, sum_columns = execute_raw_query_det(sumquery, location)
    if sum_rows:
        total_sum = sum_rows[0][0]  # Assuming the result is a single value
        # Display the sum somewhere in your GUI, e.g., update a label
        label_sum_value_det.config(text=f"{total_sum}")

    # Execute the total sum query (including all receipt numbers)
    total_sum_rows, total_sum_columns = execute_raw_query_det(total_sum_query, location)
    if total_sum_rows:
        total_sum_value = total_sum_rows[0][0]  # Assuming the result is a single value
        # Display the total sum somewhere in your GUI, e.g., update a label
        label_total_sum_value_det.config(text=f"{total_sum_value}")
        
    UnfinalizedQuery_rows, UnfinalizedQuery_columns = execute_raw_query_det(UnfinalizedQuery, location)
    print("UnfinalizedQuery_rows:", UnfinalizedQuery_rows)
    print("UnfinalizedQuery_columns:", UnfinalizedQuery_columns)
    if UnfinalizedQuery_rows:
        receipt_numbers = ", ".join([str(row[0]) for row in UnfinalizedQuery_rows])  # Assuming receipt numbers are in the first column
        Unfinalize_value_det.config(text=receipt_numbers)
    else:
        Unfinalize_value_det.config(text="No Unfinalized Receipts found.")  # Handle case where no results are returned    
        
    ExceptionQuery_rows, ExceptionQuery_columns = execute_raw_query_det(ExceptionQuery, location)
    print("ExceptionQuery_rows:", ExceptionQuery_rows)
    print("ExceptionQuery_columns:", ExceptionQuery_columns)
    
    # List of smiley emojis   
    smiley_emojis = ["😊", "😄", "😁", "😃", "😂"]
    

    def update_emoji(label):
        # Choose a random smiley emoji
        smiley_emoji = random.choice(smiley_emojis)
        # Update the label with the new emoji
        label.config(text=smiley_emoji)
        # Schedule the function to be called again after 500 milliseconds
        label.after(500, update_emoji, label)
        

    # Create labels within the top_right_frame
    Exception = ttk.Label(top_right_frame, text="Exception: ")
    Exception.grid(row=5, column=0, padx=5, pady=5, sticky=ttk.W)

    Exception_value = ttk.Label(top_right_frame, text="", font=("Arial", 10), foreground="blue", background="yellow")
    Exception_value.grid(row=5, column=1, padx=5, pady=5, sticky=ttk.W)

    # Check for exception query results
    if ExceptionQuery_rows:
        # Convert each row to a string and join them with commas
        Exception_details = "; ".join([", ".join(map(str, row)) for row in ExceptionQuery_rows])
        # Update the label with the exception details
        Exception_value.config(text=Exception_details)
    else:
        # Start the emoji animation
        update_emoji(Exception_value)

def on_execute_raw_query_det():
    raw_query = entry_raw_query_det.get("1.0", "end-1c")  # Get raw SQL query from Text widget
    location = entry_location_det.get()  # Assuming you have a location field for IP selection

    if raw_query:
        rows, columns = execute_raw_query_det(raw_query, location)
        display_results(rows, columns)


def display_results(rows, columns):
    # Clear existing data in Treeview
    treeview_det.delete(*treeview_det.get_children())
    
    if rows:
        # Populate the Treeview with new data
        treeview_det['columns'] = columns
        treeview_det["show"] = "headings"  # Hide the default column
        
        for col in columns:
            treeview_det.heading(col, text=col)
            treeview_det.column(col, width=100, anchor="center")  # Adjust anchor as needed
        
        # Set Treeview style to show grid lines and bootstrap style
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=('Helvetica', 8), 
                        background="white", foreground="black", fieldbackground="light yellow")
        
        style.configure("Treeview.Heading", font=('Helvetica', 8, 'bold'))
        style.map("Treeview", background=[('selected', 'blue')])
        
        # Configure style for cell border
        style.configure("Treeview.Cell", borderwidth=1, relief="solid")

        # Batch insert rows
        for index, row in enumerate(rows, start=1):
            treeview_det.insert('', 'end', iid=index, values=row, tags=("Treeview.Cell",))
        
        # Set the row count
        row_count_label_value_det.config(text=f"{len(rows)}")
    else:
        # If no rows found, display a message
        treeview_det['columns'] = []
        treeview_det.insert('', 'end', values=["No data found."])
        row_count_label_value_det.config(text="0")

def on_reset():
    # Clear Treeview widget
    treeview_det.delete(*treeview_det.get_children())
    
    # Delete display labels for selected sum and total sum
    label_sum_value_det.config(text="")
    label_total_sum_value_det.config(text="")
    
    # Clear SQL command displayed in the query text area
    entry_raw_query_det.delete(1.0, "end")
    
    # Clear connection message
    connection_message_label.config(text="")
    
    # Reset row count label
    row_count_label_value_det.config(text="")
    
    Unfinalize_value_det.config(text="")
    
    # Reset form fields
    reset_form_fields_det([entry_location_det, entry_machine_no_det, entry_receipt_no_det, entry_seq_no_det, entry_raw_query_det])
       
    # Reset exception count label
    Exception_value.config(text="")
    
    # Reset DateEntry widget to empty
    entry_date_det.delete(0, 'end')
    
    # Reset status combobox
    status_combobox_det.set("")
    
    # Optionally, reset default value in entry_sbu_code
    entry_sbu_code_det.delete(0, 'end')
    entry_sbu_code_det.insert(0, "830")
    
    
    

def create_det_tab(notebook):
    det_tab = ttk.Frame(notebook)
    notebook.add(det_tab, text="DET")
    
    form_frame_det = ttk.Labelframe(det_tab, text="Server Details Table", padding=(20, 10))
    form_frame_det.pack(padx=10, pady=10, fill="both", expand="yes")

    global entry_sbu_code_det, entry_location_det, entry_machine_no_det, entry_date_det
    global entry_receipt_no_det, status_combobox_det, label_sum_value_det, label_total_sum_value_det, Unfinalize_det, Unfinalize_value_det,row_count_label_value_det, Exception, Exception_value
    global treeview_det, entry_raw_query_det, entry_seq_no_det,ExceptionQuery_rows, top_right_frame 
    global connection_message_label, row_count_label_det
    
    label_sbu_code_det = ttk.Label(form_frame_det, text="SBU Code")
    label_sbu_code_det.grid(row=0, column=0, padx=5, pady=5, sticky=W)
    entry_sbu_code_det = ttk.Entry(form_frame_det, bootstyle="info", width=30)
    entry_sbu_code_det.insert(0, "830")
    entry_sbu_code_det.grid(row=0, column=1, padx=5, pady=5, sticky=E)

    label_location_det = ttk.Label(form_frame_det, text="Location")
    label_location_det.grid(row=1, column=0, padx=5, pady=5, sticky=W)
    entry_location_det = ttk.Entry(form_frame_det, bootstyle="info", width=30)
    entry_location_det.grid(row=1, column=1, padx=5, pady=5, sticky=E)

    label_machine_no_det = ttk.Label(form_frame_det, text="Machine No (optional, comma-separated)")
    label_machine_no_det.grid(row=2, column=0, padx=5, pady=5, sticky=W)
    entry_machine_no_det = ttk.Entry(form_frame_det, bootstyle="info", width=30)
    entry_machine_no_det.grid(row=2, column=1, padx=5, pady=5, sticky=E)

    label_date_det = ttk.Label(form_frame_det, text="Date")
    label_date_det.grid(row=3, column=0, padx=5, pady=5, sticky=W)
    entry_date_det = DateEntry(form_frame_det, bootstyle="info", width=25)
    entry_date_det.grid(row=3, column=1, padx=5, pady=5, sticky=E)

    label_receipt_no_det = ttk.Label(form_frame_det, text="Receipt No (optional, comma-separated)")
    label_receipt_no_det.grid(row=4, column=0, padx=5, pady=5, sticky=W)
    entry_receipt_no_det = ttk.Entry(form_frame_det, bootstyle="info", width=30)
    entry_receipt_no_det.grid(row=4, column=1, padx=5, pady=5, sticky=E)
    
    label_seq_no_det = ttk.Label(form_frame_det, text="Seq No (optional, comma-separated)")
    label_seq_no_det.grid(row=5, column=0, padx=5, pady=5, sticky=W)
    entry_seq_no_det = ttk.Entry(form_frame_det, bootstyle="info", width=30)
    entry_seq_no_det.grid(row=5, column=1, padx=5, pady=5, sticky=E)

    label_status = ttk.Label(form_frame_det, text="Status (optional)")
    label_status.grid(row=6, column=0, padx=5, pady=5, sticky=W)
    status_combobox_det = ttk.Combobox(form_frame_det, values=["VALID", "CAN"], bootstyle="info", width=28)
    status_combobox_det.grid(row=6, column=1, padx=5, pady=5, sticky=E)

    button_submit_det = ttk.Button(form_frame_det, text="Submit", bootstyle="success", command=on_submit_det)
    button_submit_det.grid(row=7, column=0, padx=5, pady=10, sticky=E)

    button_reset_det = ttk.Button(form_frame_det, text="Reset", bootstyle="warning", command=on_reset)
    button_reset_det.grid(row=7, column=1, padx=5, pady=10, sticky=W)
    
    # Add a new frame for connection message and sum labels on the top right side
    top_right_frame = ttk.Frame(form_frame_det)
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
    label_sum_value_det = ttk.Label(top_right_frame, text="")
    label_sum_value_det.grid(row=1, column=1, padx=5, pady=5, sticky=W)

    label_total_sum = ttk.Label(top_right_frame, text="Total Sum:")
    label_total_sum.grid(row=2, column=0, padx=5, pady=5, sticky=W)
    label_total_sum_value_det = ttk.Label(top_right_frame, text="")
    label_total_sum_value_det.grid(row=2, column=1, padx=5, pady=5, sticky=W)
    
    row_count_label_det = ttk.Label(top_right_frame, text="Row Count: ")
    row_count_label_det.grid(row=3, column=0, padx=5, pady=5, sticky=W)
    row_count_label_value_det = ttk.Label(top_right_frame, text="")
    row_count_label_value_det.grid(row=3, column=1, padx=5, pady=5, sticky=W)
    
    Unfinalize_det = ttk.Label(top_right_frame, text="Unfinalized: ")
    Unfinalize_det.grid(row=4, column=0, padx=5, pady=5, sticky=W)
    Unfinalize_value_det = ttk.Label(top_right_frame, text="")
    Unfinalize_value_det.grid(row=4, column=1, padx=5, pady=5, sticky=W)
    
    raw_query_frame_det = ttk.Labelframe(det_tab, text="Raw SQL Query", padding=(20, 10))
    raw_query_frame_det.pack(padx=10, pady=10, fill="both", expand="yes")
    
    entry_raw_query_det = ttk.Text(raw_query_frame_det, width=160, height=7, wrap="word")
    entry_raw_query_det.pack(padx=20, pady=10, fill="both", expand=True)
    
    execute_raw_query_button = ttk.Button(raw_query_frame_det, text="Execute Raw Query", bootstyle=SUCCESS, command=on_execute_raw_query_det)
    execute_raw_query_button.pack(padx=5, pady=5)
    
    results_frame_det = ttk.Labelframe(det_tab, text="Results", padding=(20, 10))
    results_frame_det.pack(padx=10, pady=10, fill="both", expand="yes")
    
    treeview_det = ttk.Treeview(results_frame_det)
    treeview_det.pack(fill="both", expand="yes", padx=10, pady=10)

    
    return det_tab
