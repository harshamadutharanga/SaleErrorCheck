import mysql.connector
from testip import ip_addresses
import subprocess
import time
import os


def get_ip_by_location(location_code):
    for location_set in ip_addresses.values():
        if location_code in location_set:
            return location_set[location_code]['ip']
    return None

def ping_ip(ip_address):
    """ Ping an IP address and return True if successful, False otherwise. """
    try:
        command = ['ping', '-n', '1', ip_address] if os.name == 'nt' else ['ping', '-c', '1', ip_address]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        if result.returncode == 0:
            return True
        else:
            return False
    except subprocess.TimeoutExpired:
        print(f"Timeout: Ping to {ip_address} timed out.")
        return False
    except Exception as e:
        print(f"Error during ping: {e}")
        return False

def create_connection(location_code):
    ip = get_ip_by_location(location_code)
    if not ip:
        raise ValueError(f"Invalid location code '{location_code}'")

    # Check if IP is online
    if not ping_ip(ip):
        print(f"Location '{location_code}' is offline.")
        return None

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
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Example usage:
if __name__ == "__main__":
    location_code = 'some_location_code'
    connection = create_connection(location_code)
    if connection:
        # Proceed with database operations
        cursor = connection.cursor()
        # Perform queries, fetch data, etc.
        cursor.close()
        connection.close()
    else:
        # Handle offline location or connection failure
        print("Unable to establish connection.")

####### execute query MAS table start ########

def execute_query(sbu_code, location_code, machine_no_list, txn_date, receipt_no_list, status):
    connection = create_connection(location_code)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Build the base query
        query = ("SELECT * FROM rms_pos_txn_mas "
                 "WHERE sbu_code=%s AND loc_code=%s AND txn_date=%s")
        params = [sbu_code, location_code, txn_date]

        # Append additional filters if provided
        if machine_no_list:
            machine_conditions = []
            for item in machine_no_list:
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-')
                    machine_conditions.append("mach_code BETWEEN %s AND %s")
                    params.extend([start, end])
                else:
                    machine_conditions.append("mach_code=%s")
                    params.append(item)
            query += " AND (" + " OR ".join(machine_conditions) + ")"
            
        if receipt_no_list:
            receipt_conditions = []
            for item in receipt_no_list:
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-')
                    receipt_conditions.append("receiptno BETWEEN %s AND %s")
                    params.extend([start, end])
                else:
                    receipt_conditions.append("receiptno=%s")
                    params.append(item)
            query += " AND (" + " OR ".join(receipt_conditions) + ")"

        if status:
            if status == 'VALID':
                query += " AND inv_status='VALID'"
            elif status == 'CAN':
                query += " AND inv_status='CAN'"

        # Execute the query with form inputs as parameters
        cursor.execute(query, params)

        # Fetch all rows of the query result
        rows = cursor.fetchall()

        # Fetch column names if cursor.description is not None
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        # Close cursor and connection
        cursor.close()
        connection.close()

        return rows, columns

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return [], []

def execute_raw_query(raw_query, location_code):
    connection = create_connection(location_code)  # Use the location code for connection
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Execute the raw SQL query
        cursor.execute(raw_query)

        # Fetch all rows of the query result
        rows = cursor.fetchall()

        # Fetch column names if cursor.description is not None
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        # Close cursor and connection
        cursor.close()
        connection.close()

        return rows, columns

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return [], []

def process_form_data(sbu_code, location, machine_no, date, receipt_no, status):
    # Placeholder function for processing form data
    print(f"Processing form data: {sbu_code}, {location}, {machine_no}, {date}, {receipt_no}, {status}")

def reset_form_fields(entries):
    # Placeholder function for resetting form fields
    for entry in entries:
        entry.delete(0, 'end')



########### Execute Query DET Table start ############

def execute_query_det(sbu_code, location_code, machine_no_list, txn_date, receipt_no_list, status, seq_no_list):
    connection = create_connection(location_code)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Build the base query
        query = ("SELECT * FROM rms_pos_txn_det "
                 "WHERE sbu_code=%s AND loc_code=%s AND txn_date=%s")
        params = [sbu_code, location_code, txn_date]

        # Append additional filters if provided
        if machine_no_list:
            machine_conditions = []
            for item in machine_no_list:
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-')
                    machine_conditions.append("mach_code BETWEEN %s AND %s")
                    params.extend([start, end])
                else:
                    machine_conditions.append("mach_code=%s")
                    params.append(item)
            query += " AND (" + " OR ".join(machine_conditions) + ")"
            
        if receipt_no_list:
            receipt_conditions = []
            for item in receipt_no_list:
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-')
                    receipt_conditions.append("receiptno BETWEEN %s AND %s")
                    params.extend([start, end])
                else:
                    receipt_conditions.append("receiptno=%s")
                    params.append(item)
            query += " AND (" + " OR ".join(receipt_conditions) + ")"

        if seq_no_list:
            seq_conditions = []
            for item in seq_no_list:
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-')
                    seq_conditions.append("seq_no BETWEEN %s AND %s")
                    params.extend([start, end])
                else:
                    seq_conditions.append("seq_no=%s")
                    params.append(item)
            query += " AND (" + " OR ".join(seq_conditions) + ")"

        if status:
            if status == 'VALID':
                query += " AND inv_status='VALID'"
            elif status == 'CAN':
                query += " AND inv_status='CAN'"

        # Execute the query with form inputs as parameters
        cursor.execute(query, params)

        # Fetch all rows of the query result
        rows = cursor.fetchall()

        # Fetch column names if cursor.description is not None
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        # Close cursor and connection
        cursor.close()
        connection.close()

        return rows, columns

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return [], []


def execute_raw_query_det(raw_query, location_code):
    connection = create_connection(location_code)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Execute the raw SQL query
        cursor.execute(raw_query)

        # Fetch all rows of the query result
        rows = cursor.fetchall()

        # Fetch column names if cursor.description is not None
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        # Close cursor and connection
        cursor.close()
        connection.close()

        return rows, columns

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return [], []


def process_form_data_det(sbu_code, location, machine_no, date, receipt_no, status, seq_no):
    # Placeholder function for processing form data
    print(f"Processing form data: {sbu_code}, {location}, {machine_no}, {date}, {receipt_no}, {status}, {seq_no}")

def reset_form_fields_det(entries):
    # Placeholder function for resetting form fields
    for entry in entries:
        entry.delete(0, 'end')
        

########### Execute Query Pay Details start ############

def execute_query_pay(sbu_code, location_code, machine_no_list, txn_date, receipt_no_list, paymode):
    connection = create_connection(location_code)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Build the base query
        query = ("SELECT * FROM rms_pos_pay_details "
                 "WHERE sbu_code=%s AND loc_code=%s AND txn_date=%s")
        params = [sbu_code, location_code, txn_date]

        # Append additional filters if provided
        if machine_no_list:
            machine_conditions = []
            for item in machine_no_list:
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-')
                    machine_conditions.append("mach_code BETWEEN %s AND %s")
                    params.extend([start, end])
                else:
                    machine_conditions.append("mach_code=%s")
                    params.append(item)
            query += " AND (" + " OR ".join(machine_conditions) + ")"
            
        if receipt_no_list:
            receipt_conditions = []
            for item in receipt_no_list:
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-')
                    receipt_conditions.append("receiptno BETWEEN %s AND %s")
                    params.extend([start, end])
                else:
                    receipt_conditions.append("receiptno=%s")
                    params.append(item)
            query += " AND (" + " OR ".join(receipt_conditions) + ")"


        if paymode:
            if paymode == 'cr':
                query += " AND pay_mode='cr'"
            elif paymode == 'cs':
                query += " AND pay_mode='cs'"
            elif paymode == 'qr':
                query += " AND pay_mode='qr'"
            elif paymode == 'gv':
                query += " AND pay_mode='gv'"
            elif paymode == 'ly':
                query += " AND pay_mode='ly'"
            elif paymode == 'ch':
                query += " AND pay_mode='ch'"
            elif paymode == 'fm':
                query += " AND pay_mode='fm'"

        # Execute the query with form inputs as parameters
        cursor.execute(query, params)

        # Fetch all rows of the query result
        rows = cursor.fetchall()

        # Fetch column names if cursor.description is not None
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        # Close cursor and connection
        cursor.close()
        connection.close()

        return rows, columns

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return [], []


def execute_raw_query_pay(raw_query, location_code):
    connection = create_connection(location_code)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Execute the raw SQL query
        cursor.execute(raw_query)

        # Fetch all rows of the query result
        rows = cursor.fetchall()

        # Fetch column names if cursor.description is not None
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        # Close cursor and connection
        cursor.close()
        connection.close()

        return rows, columns

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return [], []


def process_form_data_pay(sbu_code, location, machine_no, date, receipt_no, paymode):
    # Placeholder function for processing form data
    print(f"Processing form data: {sbu_code}, {location}, {machine_no}, {date}, {receipt_no}, {paymode}")

def reset_form_fields_pay(entries):
    # Placeholder function for resetting form fields
    for entry in entries:
        entry.delete(0, 'end')        