import mysql.connector
from posip import posip_addresses
from typing import Union
import subprocess
import time
import os


def get_ip_by_location(location_code: str, machine_code: str) -> Union[str, None]:
    if location_code in posip_addresses and machine_code in posip_addresses[location_code]:
        return posip_addresses[location_code][machine_code]['ip']
    return None

def ping_ip(ip_address: str) -> bool:
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

def create_connection(location_code: str, machine_code: str):
    ip = get_ip_by_location(location_code, machine_code)
    if not ip:
        raise ValueError(f"Invalid location code '{location_code}' or machine code '{machine_code}'")

    # Check if POS system is online
    if not ping_ip(ip):
        print(f"Error: POS at location '{location_code}' with machine '{machine_code}' is offline.")
        return None

    connection_params = {
        'host': ip,
        'port': 3306,
        'user': 'harsha',
        'password': 'har%123',
        'database': 'posdb',
        'charset': 'utf8'
    }

    try:
        connection = mysql.connector.connect(**connection_params)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

####### execute query MAS table start ########
def execute_query(sbu_code, location_code, machine_no, txn_date, receipt_no_list, status):
    connection = create_connection(location_code, machine_no)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Build the base query
        query = ("SELECT * FROM pos_txn_mas "
                 "WHERE sbu_code=%s AND loc_code=%s AND mach_code=%s AND txn_date=%s")
        params = [sbu_code, location_code, machine_no, txn_date]

        # Append additional filters if provided     
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
    finally:
        cursor.close()
        connection.close()

def execute_raw_query(raw_query, location_code,  machine_no):
    connection = create_connection(location_code, machine_no)  # Use the location code for connection
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
    finally:
        cursor.close()
        connection.close()

def process_form_data(sbu_code, location, machine_no, date, receipt_no, status):
    # Placeholder function for processing form data
    print(f"Processing form data: {sbu_code}, {location}, {machine_no}, {date}, {receipt_no}, {status}")
    

def reset_form_fields(entries):
    # Placeholder function for resetting form fields
    for entry in entries:
        entry.delete(0, 'end')

        



########### Execute Query DET Table start ############

def execute_query_det(sbu_code, location_code, machine_no, txn_date, receipt_no_list, status, seq_no_list):
    connection = create_connection(location_code, machine_no)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Build the base query
        query = ("SELECT * FROM pos_txn_det "
                 "WHERE sbu_code=%s AND loc_code=%s AND mach_code=%s AND txn_date=%s ")
        params = [sbu_code, location_code, machine_no, txn_date]

        # Append additional filters if provided            
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
    finally:
        cursor.close()
        connection.close()


def execute_raw_query_det(raw_query, location_code, machine_no):
    connection = create_connection(location_code, machine_no)
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
    finally:
        cursor.close()
        connection.close()


def process_form_data_det(sbu_code, location, machine_no, date, receipt_no, status, seq_no):
    # Placeholder function for processing form data
    print(f"Processing form data: {sbu_code}, {location}, {machine_no}, {date}, {receipt_no}, {status}, {seq_no}")

def reset_form_fields_det(entries):
    # Placeholder function for resetting form fields
    for entry in entries:
        entry.delete(0, 'end')
        

########### Execute Query Pay Details start ############

def execute_query_pay(sbu_code, location_code, machine_no, txn_date, receipt_no_list, paymode):
    connection = create_connection(location_code, machine_no)
    if not connection:
        return [], []

    try:
        cursor = connection.cursor()

        # Build the base query
        query = ("SELECT * FROM pos_pay_details "
                 "WHERE sbu_code=%s AND loc_code=%s AND mach_code=%s AND txn_date=%s")
        params = [sbu_code, location_code, machine_no, txn_date]

        # Append additional filters if provided            
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
    finally:
        cursor.close()
        connection.close()


def execute_raw_query_pay(raw_query, location_code, machine_no):
    connection = create_connection(location_code, machine_no)
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
    finally:
        cursor.close()
        connection.close()


def process_form_data_pay(sbu_code, location, machine_no, date, receipt_no, paymode):
    # Placeholder function for processing form data
    print(f"Processing form data: {sbu_code}, {location}, {machine_no}, {date}, {receipt_no}, {paymode}")

def reset_form_fields_pay(entries):
    # Placeholder function for resetting form fields
    for entry in entries:
        entry.delete(0, 'end')        
        