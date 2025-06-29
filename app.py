from flask import Flask, render_template, request, redirect, url_for,session,flash,jsonify
import mysql.connector
from mysql.connector import pooling
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'Depression10#'

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Depression10#",
    database="supermarket_db"
)

# Configure the connection pool
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,  # Adjust the pool size as needed
    host="localhost",
    user="root",
    password="#mysql@885",
    database="supermarket_db"
)


# Get connection from pool
def get_db_connection():
    return connection_pool.get_connection()


# Cursor object to interact with the database
cursor = db.cursor()

# Route for the homepage
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        cursor = db.cursor()
        cursor.execute("SELECT role FROM Employee WHERE employee_id = %s AND password = %s", (user_id, password))
        result = cursor.fetchone()

        if result:
            role = result[0]
            session['user_id'] = user_id  # Store user ID in session
            session['role'] = role  # Store user role in session

            if role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif role =='Cashier':
                return redirect(url_for('cashier_dashboard'))
            elif role =='Block Incharge':
                return redirect(url_for('block_manager_dashboard'))
            elif role =='Warehouse Manager':
                return redirect(url_for('warehouse_manager_dashboard'))
           
        else:
            flash('Invalid User ID or Password')

    return render_template('login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'Admin':
        return redirect(url_for('login'))
    # Admin dashboard content
    return render_template('admin_dashboard.html')
@app.route('/cashier_dashboard')
def cashier_dashboard():
    if session.get('role') != 'Cashier':
        return redirect(url_for('login'))
    # Cashier dashboard content
    return render_template('cashier_dashboard.html')


@app.route('/warehouse_manager_dashboard')
def warehouse_manager_dashboard():
    if session.get('role') != 'Warehouse Manager':
        return redirect(url_for('login'))
    
    # Get a connection from the pool
    connection = get_db_connection()
    if connection is None:
        block_alerts = ["Unable to connect to the database. Please check your connection settings."]
        warehouse_alerts = block_alerts
        return render_template('warehouse_manager_dashboard.html', block_alerts=block_alerts, warehouse_alerts=warehouse_alerts)
    
    cursor = connection.cursor()
    try:
        # Fetch products with zero stock in blocks
        cursor.execute("SELECT product_id, product_type FROM Product WHERE block_count = 0")
        zero_block_count_products = cursor.fetchall()
        block_alerts = [f"'{product_type}' (ID: {product_id}) has zero stock in block. Please transfer items." 
                        for product_id, product_type in zero_block_count_products]
        
        # Fetch products with zero stock in warehouse
        cursor.execute("SELECT product_id, product_type FROM Product WHERE warehouse_count = 0")
        zero_warehouse_count_products = cursor.fetchall()
        warehouse_alerts = [f"'{product_type}' (ID: {product_id}) has zero stock in warehouse. Please order from supplier." 
                            for product_id, product_type in zero_warehouse_count_products]
        
    except mysql.connector.Error as err:
        print("Error executing query:", err)
        block_alerts = ["An error occurred while fetching data."]
        warehouse_alerts = block_alerts
    finally:
        cursor.close()
        connection.close()
    
    return render_template('warehouse_manager_dashboard.html', block_alerts=block_alerts, warehouse_alerts=warehouse_alerts)


@app.route('/block_manager_dashboard')
def block_manager_dashboard():
    if session.get('role') != 'Block Incharge':
        return redirect(url_for('login'))
    # Block manager dashboard content
    return render_template('block_manager_dashboard.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('login'))



# Employee management routes (existing)
@app.route('/employee')
def manage_employee():
    cursor.execute("SELECT * FROM Employee")
    employees = cursor.fetchall()
    return render_template('employee.html', employees=employees)

# Add new employee (existing)
@app.route('/add_employee', methods=['POST'])
def add_employee():
    # Get form data
    employee_id = request.form['employee_id']
    employee_name = request.form['employee_name']
    employee_contact = request.form['employee_contact']
    employee_dob = request.form['employee_dob']
    employee_email = request.form['employee_email']
    employee_address = request.form['employee_address']
    gender = request.form['gender']

    # Insert the new employee into the database
    query = """
    INSERT INTO Employee (employee_id, employee_name, employee_contact, employee_dob, employee_email, employee_address, gender)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (employee_id, employee_name, employee_contact, employee_dob, employee_email, employee_address, gender)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_employee'))

# Delete employees (existing)
@app.route('/delete_employees', methods=['POST'])
def delete_employees():
    employee_ids = request.form.getlist('employee_ids')
    if employee_ids:
        query = "DELETE FROM Employee WHERE employee_id IN (%s)" % ','.join(['%s'] * len(employee_ids))
        cursor.execute(query, tuple(employee_ids))
        db.commit()
    return redirect(url_for('manage_employee'))

# Edit employees (existing)
@app.route('/edit_employees', methods=['POST'])
def edit_employees():
    employee_ids = request.form.getlist('employee_ids')
    employees_to_edit = []
    for emp_id in employee_ids:
        cursor.execute("SELECT * FROM Employee WHERE employee_id = %s", (emp_id,))
        employee = cursor.fetchone()
        employees_to_edit.append(employee)
    return render_template('edit_employees.html', employees=employees_to_edit)

# Update employees (existing)
@app.route('/update_employees', methods=['POST'])
def update_employees():
    for key, value in request.form.items():
        employee_id = key.split('-')[1]
        if key.startswith('name-'):
            cursor.execute("UPDATE Employee SET employee_name = %s WHERE employee_id = %s", (value, employee_id))
        elif key.startswith('contact-'):
            cursor.execute("UPDATE Employee SET employee_contact = %s WHERE employee_id = %s", (value, employee_id))
        elif key.startswith('dob-'):
            cursor.execute("UPDATE Employee SET employee_dob = %s WHERE employee_id = %s", (value, employee_id))
        elif key.startswith('email-'):
            cursor.execute("UPDATE Employee SET employee_email = %s WHERE employee_id = %s", (value, employee_id))
        elif key.startswith('address-'):
            cursor.execute("UPDATE Employee SET employee_address = %s WHERE employee_id = %s", (value, employee_id))
        elif key.startswith('gender-'):
            cursor.execute("UPDATE Employee SET gender = %s WHERE employee_id = %s", (value, employee_id))
    db.commit()
    return redirect(url_for('manage_employee'))

# Display all offers
@app.route('/offer_details')
def manage_offer():
    cursor.execute("SELECT * FROM OfferDetails")
    offers = cursor.fetchall()
    return render_template('offer_details.html', offers=offers)

# Add new offer
@app.route('/add_offer', methods=['POST'])
def add_offer():
    # Get form data
    offer_id = request.form['offer_id']
    offer_type = request.form['offer_type']
    offer_details = request.form['offer_details']
    offer_start_date = request.form['offer_start_date']
    offer_end_date = request.form['offer_end_date']

    # Insert the new offer into the database
    query = """
    INSERT INTO OfferDetails (offers_id, offers_type, offers_details, offers_start_date, offers_end_date)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (offer_id, offer_type, offer_details, offer_start_date, offer_end_date)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_offer'))

# Delete offers
@app.route('/delete_offers', methods=['POST'])
def delete_offers():
    offer_ids = request.form.getlist('offer_ids')
    if offer_ids:
        query = "DELETE FROM OfferDetails WHERE offers_id IN (%s)" % ','.join(['%s'] * len(offer_ids))
        cursor.execute(query, tuple(offer_ids))
        db.commit()
    return redirect(url_for('manage_offer'))

# Edit offers
@app.route('/edit_offers', methods=['POST'])
def edit_offers():
    offer_ids = request.form.getlist('offer_ids')
    offers_to_edit = []
    for offer_id in offer_ids:
        cursor.execute("SELECT * FROM OfferDetails WHERE offers_id = %s", (offer_id,))
        offer = cursor.fetchone()
        offers_to_edit.append(offer)
    return render_template('edit_offers.html', offers=offers_to_edit)

# Update offers
@app.route('/update_offers', methods=['POST'])
def update_offers():
    for key, value in request.form.items():
        offer_id = key.split('-')[1]
        if key.startswith('type-'):
            cursor.execute("UPDATE OfferDetails SET offers_type = %s WHERE offers_id = %s", (value, offer_id))
        elif key.startswith('details-'):
            cursor.execute("UPDATE OfferDetails SET offers_details = %s WHERE offers_id = %s", (value, offer_id))
        elif key.startswith('start_date-'):
            cursor.execute("UPDATE OfferDetails SET offers_start_date = %s WHERE offers_id = %s", (value, offer_id))
        elif key.startswith('end_date-'):
            cursor.execute("UPDATE OfferDetails SET offers_end_date = %s WHERE offers_id = %s", (value, offer_id))
    db.commit()
    return redirect(url_for('manage_offer'))



# Display all customer types
@app.route('/customer_types')
def manage_customer_type():
    cursor.execute("SELECT * FROM CustomerType")
    customer_types = cursor.fetchall()
    return render_template('customer_types.html', customer_types=customer_types)

# Add new customer type
@app.route('/add_customer_type', methods=['POST'])
def add_customer_type():
    # Get form data
    type_id = request.form['type_id']
    type_name = request.form['type_name']

    # Insert the new customer type into the database
    query = """
    INSERT INTO CustomerType (type_id, type_name)
    VALUES (%s, %s)
    """
    values = (type_id, type_name)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_customer_type'))

# Delete customer types
@app.route('/delete_customer_types', methods=['POST'])
def delete_customer_types():
    type_ids = request.form.getlist('type_ids')
    if type_ids:
        query = "DELETE FROM CustomerType WHERE type_id IN (%s)" % ','.join(['%s'] * len(type_ids))
        cursor.execute(query, tuple(type_ids))
        db.commit()
    return redirect(url_for('manage_customer_type'))

# Edit customer types
@app.route('/edit_customer_types', methods=['POST'])
def edit_customer_types():
    type_ids = request.form.getlist('type_ids')
    types_to_edit = []
    for type_id in type_ids:
        cursor.execute("SELECT * FROM CustomerType WHERE type_id = %s", (type_id,))
        customer_type = cursor.fetchone()
        types_to_edit.append(customer_type)
    return render_template('edit_customer_types.html', customer_types=types_to_edit)

# Update customer types
@app.route('/update_customer_types', methods=['POST'])
def update_customer_types():
    for key, value in request.form.items():
        type_id = key.split('-')[1]
        if key.startswith('name-'):
            cursor.execute("UPDATE CustomerType SET type_name = %s WHERE type_id = %s", (value, type_id))
    db.commit()
    return redirect(url_for('manage_customer_type'))


# Display all customers
@app.route('/customers')
def manage_customer():
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    return render_template('customers.html', customers=customers)

# Add new customer
@app.route('/add_customer', methods=['POST'])
def add_customer():
    # Get form data
    customer_id = request.form['customer_id']
    customer_name = request.form['customer_name']
    customer_contact = request.form['customer_contact']
    date_of_birth = request.form['date_of_birth']
    email = request.form['email']
    address = request.form['address']
    gender = request.form['gender']
    customer_type_id = request.form.get('customer_type_id')  # Can be null
    membership_to = request.form['membership_to']
    membership_from = request.form['membership_from']

    # Insert the new customer into the database
    query = """
    INSERT INTO Customer (customer_id, customer_name, customer_contact, date_of_birth, email, address, gender, customer_type_id, membership_to, membership_to_from)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (customer_id, customer_name, customer_contact, date_of_birth, email, address, gender, customer_type_id, membership_to, membership_from)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_customer'))

# Delete customers
@app.route('/delete_customers', methods=['POST'])
def delete_customers():
    customer_ids = request.form.getlist('customer_ids')
    if customer_ids:
        query = "DELETE FROM Customer WHERE customer_id IN (%s)" % ','.join(['%s'] * len(customer_ids))
        cursor.execute(query, tuple(customer_ids))
        db.commit()
    return redirect(url_for('manage_customer'))


@app.route('/edit_customers', methods=['POST'])
def edit_customers():
    customer_ids = request.form.getlist('customer_ids')
    customers_to_edit = []
    
    # Fetch the customer types from the CustomerType table
    cursor.execute("SELECT * FROM CustomerType")
    customer_types = cursor.fetchall()

    for cust_id in customer_ids:
        cursor.execute("SELECT * FROM Customer WHERE customer_id = %s", (cust_id,))
        customer = cursor.fetchone()
        customers_to_edit.append(customer)
    
    # Pass both customers and customer types to the template
    return render_template('edit_customers.html', customers=customers_to_edit, customer_types=customer_types)


# Update customers
@app.route('/update_customers', methods=['POST'])
def update_customers():
    for key, value in request.form.items():
        customer_id = key.split('-')[1]
        if key.startswith('name-'):
            cursor.execute("UPDATE Customer SET customer_name = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('contact-'):
            cursor.execute("UPDATE Customer SET customer_contact = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('dob-'):
            cursor.execute("UPDATE Customer SET date_of_birth = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('email-'):
            cursor.execute("UPDATE Customer SET email = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('address-'):
            cursor.execute("UPDATE Customer SET address = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('gender-'):
            cursor.execute("UPDATE Customer SET gender = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('type_id-'):
            cursor.execute("UPDATE Customer SET customer_type_id = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('membership_to-'):
            cursor.execute("UPDATE Customer SET membership_to = %s WHERE customer_id = %s", (value, customer_id))
        elif key.startswith('membership_from-'):
            cursor.execute("UPDATE Customer SET membership_to_from = %s WHERE customer_id = %s", (value, customer_id))
    db.commit()
    return redirect(url_for('manage_customer'))


# Display all warehouses
@app.route('/warehouse')
def manage_warehouse():
    cursor.execute("SELECT * FROM Warehouse")
    warehouses = cursor.fetchall()
    return render_template('warehouse.html', warehouses=warehouses)

# Add new warehouse
@app.route('/add_warehouse', methods=['POST'])
def add_warehouse():
    # Get form data
    warehouse_no = request.form['warehouse_no']
    warehouse_name = request.form['warehouse_name']

    # Insert the new warehouse into the database
    query = """
    INSERT INTO Warehouse (warehouse_no, warehouse_name)
    VALUES (%s, %s)
    """
    values = (warehouse_no, warehouse_name)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_warehouse'))

# Delete warehouses
@app.route('/delete_warehouses', methods=['POST'])
def delete_warehouses():
    warehouse_nos = request.form.getlist('warehouse_nos')
    if warehouse_nos:
        query = "DELETE FROM Warehouse WHERE warehouse_no IN (%s)" % ','.join(['%s'] * len(warehouse_nos))
        cursor.execute(query, tuple(warehouse_nos))
        db.commit()
    return redirect(url_for('manage_warehouse'))

# Edit warehouses
@app.route('/edit_warehouses', methods=['POST'])
def edit_warehouses():
    warehouse_nos = request.form.getlist('warehouse_nos')
    warehouses_to_edit = []
    for warehouse_no in warehouse_nos:
        cursor.execute("SELECT * FROM Warehouse WHERE warehouse_no = %s", (warehouse_no,))
        warehouse = cursor.fetchone()
        warehouses_to_edit.append(warehouse)
    return render_template('edit_warehouses.html', warehouses=warehouses_to_edit)

# Update warehouses
@app.route('/update_warehouses', methods=['POST'])
def update_warehouses():
    for key, value in request.form.items():
        warehouse_no = key.split('-')[1]
        if key.startswith('name-'):
            cursor.execute("UPDATE Warehouse SET warehouse_name = %s WHERE warehouse_no = %s", (value, warehouse_no))
    db.commit()
    return redirect(url_for('manage_warehouse'))


# Display all blocks
@app.route('/blocks')
def manage_block():
    cursor.execute("SELECT * FROM Block")
    blocks = cursor.fetchall()
    return render_template('blocks.html', blocks=blocks)

# Add new block
@app.route('/add_block', methods=['POST'])
def add_block():
    # Get form data
    block_id = request.form['block_id']
    block_name = request.form['block_name']
    block_incharge_id = request.form.get('block_incharge_id')  # Can be null

    # Insert the new block into the database
    query = """
    INSERT INTO Block (block_id, block_name, block_incharge_id)
    VALUES (%s, %s, %s)
    """
    values = (block_id, block_name, block_incharge_id)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_block'))

# Delete blocks
@app.route('/delete_blocks', methods=['POST'])
def delete_blocks():
    block_ids = request.form.getlist('block_ids')
    if block_ids:
        query = "DELETE FROM Block WHERE block_id IN (%s)" % ','.join(['%s'] * len(block_ids))
        cursor.execute(query, tuple(block_ids))
        db.commit()
    return redirect(url_for('manage_block'))

# Edit blocks
@app.route('/edit_blocks', methods=['POST'])
def edit_blocks():
    block_ids = request.form.getlist('block_ids')
    blocks_to_edit = []
    for blk_id in block_ids:
        cursor.execute("SELECT * FROM Block WHERE block_id = %s", (blk_id,))
        block = cursor.fetchone()
        blocks_to_edit.append(block)
    return render_template('edit_blocks.html', blocks=blocks_to_edit)

# Update blocks
@app.route('/update_blocks', methods=['POST'])
def update_blocks():
    for key, value in request.form.items():
        block_id = key.split('-')[1]
        if key.startswith('name-'):
            cursor.execute("UPDATE Block SET block_name = %s WHERE block_id = %s", (value, block_id))
        elif key.startswith('incharge_id-'):
            cursor.execute("UPDATE Block SET block_incharge_id = %s WHERE block_id = %s", (value, block_id))
    db.commit()
    return redirect(url_for('manage_block'))


# Display all categories
@app.route('/categories')
def manage_category():
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    return render_template('categories.html', categories=categories)

# Add new category
@app.route('/add_category', methods=['POST'])
def add_category():
    # Get form data
    category_id = request.form['category_id']
    category_name = request.form['category_name']
    store_id = request.form['store_id']
    warehouse_no = request.form.get('warehouse_no')  # Can be null

    # Insert the new category into the database
    query = """
    INSERT INTO Category (category_id, category_name, store_id, warehouse_no)
    VALUES (%s, %s, %s, %s)
    """
    values = (category_id, category_name, store_id, warehouse_no)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_category'))

# Delete categories
@app.route('/delete_categories', methods=['POST'])
def delete_categories():
    category_ids = request.form.getlist('category_ids')
    if category_ids:
        query = "DELETE FROM Category WHERE category_id IN (%s)" % ','.join(['%s'] * len(category_ids))
        cursor.execute(query, tuple(category_ids))
        db.commit()
    return redirect(url_for('manage_category'))

# # Edit categories
# @app.route('/edit_categories', methods=['POST'])
# def edit_categories():
#     category_ids = request.form.getlist('category_ids')
#     categories_to_edit = []
#     for cat_id in category_ids:
#         cursor.execute("SELECT * FROM Category WHERE category_id = %s", (cat_id,))
#         category = cursor.fetchone()
#         categories_to_edit.append(category)
#     return render_template('edit_categories.html', categories=categories_to_edit)

# Edit categories
# @app.route('/edit_categories', methods=['POST'])
# def edit_categories():
#     category_ids = request.form.getlist('category_ids')
#     categories_to_edit = []

#     for cat_id in category_ids:
#         cursor.execute("SELECT * FROM Category WHERE category_id = %s", (cat_id,))
#         category = cursor.fetchone()
#         categories_to_edit.append(category)
    
#     # Fetch store IDs from the Block table
#     cursor.execute("SELECT block_id FROM Block")
#     store_ids = cursor.fetchall()
    
#     # Fetch warehouse numbers from the Warehouse table
#     cursor.execute("SELECT warehouse_no FROM Warehouse")
#     warehouse_nos = cursor.fetchall()
    
#     return render_template('edit_categories.html', 
#                            categories=categories_to_edit, 
#                            store_ids=store_ids, 
#                            warehouse_nos=warehouse_nos)



# Edit categories
@app.route('/edit_categories', methods=['POST'])
def edit_categories():
    category_ids = request.form.getlist('category_ids')
    categories_to_edit = []

    for cat_id in category_ids:
        cursor.execute("SELECT * FROM Category WHERE category_id = %s", (cat_id,))
        category = cursor.fetchone()
        if category:
            categories_to_edit.append(category)
    
    # Fetch store IDs from the Block table
    cursor.execute("SELECT block_id FROM Block")
    store_ids = cursor.fetchall()
    
    # Fetch warehouse numbers from the Warehouse table
    cursor.execute("SELECT warehouse_no FROM Warehouse")
    warehouse_nos = cursor.fetchall()
    
    return render_template('edit_categories.html', 
                           categories=categories_to_edit, 
                           store_ids=store_ids, 
                           warehouse_nos=warehouse_nos)


# Update categories
@app.route('/update_categories', methods=['POST'])
def update_categories():
    for key, value in request.form.items():
        category_id = key.split('-')[1]
        if key.startswith('name-'):
            cursor.execute("UPDATE Category SET category_name = %s WHERE category_id = %s", (value, category_id))
        elif key.startswith('store_id-'):
            cursor.execute("UPDATE Category SET store_id = %s WHERE category_id = %s", (value, category_id))
        elif key.startswith('warehouse_no-'):
            cursor.execute("UPDATE Category SET warehouse_no = %s WHERE category_id = %s", (value, category_id))
    db.commit()
    return redirect(url_for('manage_category'))

# Display all payment modes
@app.route('/payment_modes')
def manage_payment_mode():
    cursor.execute("SELECT * FROM PaymentMode")
    payment_modes = cursor.fetchall()
    return render_template('payment_modes.html', payment_modes=payment_modes)

# Add new payment mode
@app.route('/add_payment_mode', methods=['POST'])
def add_payment_mode():
    # Get form data
    payment_mode_id = request.form['payment_mode_id']
    mode_of_payment = request.form['mode_of_payment']
    offer_id = request.form.get('offer_id')  # Can be null

    # Insert the new payment mode into the database
    query = """
    INSERT INTO PaymentMode (payment_mode_id, mode_of_payment, offer_id)
    VALUES (%s, %s, %s)
    """
    values = (payment_mode_id, mode_of_payment, offer_id)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_payment_mode'))

# Delete payment modes
@app.route('/delete_payment_modes', methods=['POST'])
def delete_payment_modes():
    payment_mode_ids = request.form.getlist('payment_mode_ids')
    if payment_mode_ids:
        query = "DELETE FROM PaymentMode WHERE payment_mode_id IN (%s)" % ','.join(['%s'] * len(payment_mode_ids))
        cursor.execute(query, tuple(payment_mode_ids))
        db.commit()
    return redirect(url_for('manage_payment_mode'))

# Edit payment modes
@app.route('/edit_payment_modes', methods=['POST'])
def edit_payment_modes():
    payment_mode_ids = request.form.getlist('payment_mode_ids')
    payment_modes_to_edit = []
    for mode_id in payment_mode_ids:
        cursor.execute("SELECT * FROM PaymentMode WHERE payment_mode_id = %s", (mode_id,))
        payment_mode = cursor.fetchone()
        payment_modes_to_edit.append(payment_mode)
    return render_template('edit_payment_modes.html', payment_modes=payment_modes_to_edit)

# Update payment modes
@app.route('/update_payment_modes', methods=['POST'])
def update_payment_modes():
    for key, value in request.form.items():
        payment_mode_id = key.split('-')[1]
        if key.startswith('mode-'):
            cursor.execute("UPDATE PaymentMode SET mode_of_payment = %s WHERE payment_mode_id = %s", (value, payment_mode_id))
        elif key.startswith('offer_id-'):
            cursor.execute("UPDATE PaymentMode SET offer_id = %s WHERE payment_mode_id = %s", (value, payment_mode_id))
    db.commit()
    return redirect(url_for('manage_payment_mode'))

# Display all invoices
@app.route('/invoice_details')
def manage_invoice():
    cursor.execute("SELECT * FROM InvoiceDetails")
    invoices = cursor.fetchall()
    return render_template('invoice_details.html', invoices=invoices)

# Add new invoice
@app.route('/add_invoice', methods=['POST'])
def add_invoice():
    # Get form data
    inv_id = request.form['inv_id']
    cust_id = request.form.get('cust_id')  # Can be null
    amount = request.form['amount']
    inv_date = request.form['inv_date']
    payment_mode_id = request.form.get('payment_mode_id')  # Can be null
    cashier_id = request.form.get('cashier_id')  # Can be null

    # Insert the new invoice into the database
    query = """
    INSERT INTO InvoiceDetails (inv_id, cust_id, amount, inv_date, payment_mode_id, cashier_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (inv_id, cust_id, amount, inv_date, payment_mode_id, cashier_id)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_invoice'))

# Delete invoices
@app.route('/delete_invoices', methods=['POST'])
def delete_invoices():
    inv_ids = request.form.getlist('inv_ids')
    if inv_ids:
        query = "DELETE FROM InvoiceDetails WHERE inv_id IN (%s)" % ','.join(['%s'] * len(inv_ids))
        cursor.execute(query, tuple(inv_ids))
        db.commit()
    return redirect(url_for('manage_invoice'))

# Edit invoices
@app.route('/edit_invoices', methods=['POST'])
def edit_invoices():
    inv_ids = request.form.getlist('inv_ids')
    invoices_to_edit = []
    for inv_id in inv_ids:
        cursor.execute("SELECT * FROM InvoiceDetails WHERE inv_id = %s", (inv_id,))
        invoice = cursor.fetchone()
        invoices_to_edit.append(invoice)
    return render_template('edit_invoices.html', invoices=invoices_to_edit)

# Update invoices
@app.route('/update_invoices', methods=['POST'])
def update_invoices():
    for key, value in request.form.items():
        inv_id = key.split('-')[1]
        if key.startswith('cust_id-'):
            cursor.execute("UPDATE InvoiceDetails SET cust_id = %s WHERE inv_id = %s", (value, inv_id))
        elif key.startswith('amount-'):
            cursor.execute("UPDATE InvoiceDetails SET amount = %s WHERE inv_id = %s", (value, inv_id))
        elif key.startswith('inv_date-'):
            cursor.execute("UPDATE InvoiceDetails SET inv_date = %s WHERE inv_id = %s", (value, inv_id))
        elif key.startswith('payment_mode_id-'):
            cursor.execute("UPDATE InvoiceDetails SET payment_mode_id = %s WHERE inv_id = %s", (value, inv_id))
        elif key.startswith('cashier_id-'):
            cursor.execute("UPDATE InvoiceDetails SET cashier_id = %s WHERE inv_id = %s", (value, inv_id))
    db.commit()
    return redirect(url_for('manage_invoice'))

# Display all products
@app.route('/products')
def manage_product():
    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()
    return render_template('products.html', products=products)

# Add new product
@app.route('/add_product', methods=['POST'])
def add_product():
    # Get form data
    product_id = request.form['product_id']
    product_type = request.form['product_type']
    brand = request.form['brand']
    cost_price = request.form['cost_price']
    weight = request.form['weight']
    selling_price = request.form['selling_price']
    category_id = request.form.get('category_id')  # Can be null
    offer_id = request.form.get('offer_id')  # Can be null
    block_count = request.form['block_count']
    warehouse_count = request.form['warehouse_count']

    # Insert the new product into the database
    query = """
    INSERT INTO Product (product_id, product_type, brand, cost_price, weight, selling_price, category_id, offer_id, block_count, warehouse_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (product_id, product_type, brand, cost_price, weight, selling_price, category_id, offer_id, block_count, warehouse_count)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_product'))

# Delete products
@app.route('/delete_products', methods=['POST'])
def delete_products():
    product_ids = request.form.getlist('product_ids')
    if product_ids:
        query = "DELETE FROM Product WHERE product_id IN (%s)" % ','.join(['%s'] * len(product_ids))
        cursor.execute(query, tuple(product_ids))
        db.commit()
    return redirect(url_for('manage_product'))


@app.route('/edit_products', methods=['POST'])
def edit_products():
    product_ids = request.form.getlist('product_ids')
    products_to_edit = []
    
    # Fetch the products to edit
    for prod_id in product_ids:
        cursor.execute("SELECT * FROM Product WHERE product_id = %s", (prod_id,))
        product = cursor.fetchone()
        products_to_edit.append(product)
    
    # Fetch categories
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    
    # Fetch offers
    cursor.execute("SELECT * FROM OfferDetails")
    offers = cursor.fetchall()
    
    return render_template('edit_products.html', products=products_to_edit, categories=categories, offers=offers)



# Update products
@app.route('/update_products', methods=['POST'])
def update_products():
    for key, value in request.form.items():
        product_id = key.split('-')[1]
        if key.startswith('type-'):
            cursor.execute("UPDATE Product SET product_type = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('brand-'):
            cursor.execute("UPDATE Product SET brand = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('cost_price-'):
            cursor.execute("UPDATE Product SET cost_price = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('weight-'):
            cursor.execute("UPDATE Product SET weight = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('selling_price-'):
            cursor.execute("UPDATE Product SET selling_price = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('category_id-'):
            cursor.execute("UPDATE Product SET category_id = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('offer_id-'):
            cursor.execute("UPDATE Product SET offer_id = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('block_count-'):
            cursor.execute("UPDATE Product SET block_count = %s WHERE product_id = %s", (value, product_id))
        elif key.startswith('warehouse_count-'):
            cursor.execute("UPDATE Product SET warehouse_count = %s WHERE product_id = %s", (value, product_id))
    db.commit()
    return redirect(url_for('manage_product'))

# Display all purchases (Buys)
@app.route('/buys')
def manage_buys():
    cursor.execute("SELECT * FROM Buys")
    buys = cursor.fetchall()
    return render_template('buys.html', buys=buys)

# Add new purchase entry (Buys)
@app.route('/add_buy', methods=['POST'])
def add_buy():
    # Get form data
    product_id = request.form['product_id']
    invoice_id = request.form['invoice_id']
    quantity = request.form['quantity']
    cost = request.form['cost']

    # Insert the new purchase entry into the database
    query = """
    INSERT INTO Buys (product_id, invoice_id, quantity, cost)
    VALUES (%s, %s, %s, %s)
    """
    values = (product_id, invoice_id, quantity, cost)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_buys'))

# Delete purchase entries (Buys)
@app.route('/delete_buys', methods=['POST'])
def delete_buys():
    product_invoice_pairs = request.form.getlist('product_invoice_pairs')
    if product_invoice_pairs:
        for pair in product_invoice_pairs:
            product_id, invoice_id = pair.split(',')
            cursor.execute("DELETE FROM Buys WHERE product_id = %s AND invoice_id = %s", (product_id, invoice_id))
        db.commit()
    return redirect(url_for('manage_buys'))

# Edit purchase entries (Buys)
@app.route('/edit_buys', methods=['POST'])
def edit_buys():
    product_invoice_pairs = request.form.getlist('product_invoice_pairs')
    buys_to_edit = []
    for pair in product_invoice_pairs:
        product_id, invoice_id = pair.split(',')
        cursor.execute("SELECT * FROM Buys WHERE product_id = %s AND invoice_id = %s", (product_id, invoice_id))
        buy = cursor.fetchone()
        buys_to_edit.append(buy)
    return render_template('edit_buys.html', buys=buys_to_edit)

# Update purchase entries (Buys)
@app.route('/update_buys', methods=['POST'])
def update_buys():
    for key, value in request.form.items():
        product_id, invoice_id = key.split('-')[1].split(',')
        if key.startswith('quantity-'):
            cursor.execute("UPDATE Buys SET quantity = %s WHERE product_id = %s AND invoice_id = %s", (value, product_id, invoice_id))
        elif key.startswith('cost-'):
            cursor.execute("UPDATE Buys SET cost = %s WHERE product_id = %s AND invoice_id = %s", (value, product_id, invoice_id))
    db.commit()
    return redirect(url_for('manage_buys'))

# Display all feedback entries
@app.route('/feedback')
def manage_feedback():
    cursor.execute("SELECT * FROM Feedback")
    feedbacks = cursor.fetchall()
    return render_template('feedback.html', feedbacks=feedbacks)

# Add new feedback
@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    # Get form data
    review_id = request.form['review_id']
    review_text = request.form['review_text']
    rating = request.form['rating']
    review_date = request.form['review_date']
    cust_id = request.form.get('cust_id')  # Can be null
    invoice_id = request.form.get('invoice_id')  # Can be null

    # Insert the new feedback into the database
    query = """
    INSERT INTO Feedback (review_id, review_text, rating, review_date, cust_id, invoice_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (review_id, review_text, rating, review_date, cust_id, invoice_id)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_feedback'))

# Delete feedback entries
@app.route('/delete_feedbacks', methods=['POST'])
def delete_feedbacks():
    review_ids = request.form.getlist('review_ids')
    if review_ids:
        query = "DELETE FROM Feedback WHERE review_id IN (%s)" % ','.join(['%s'] * len(review_ids))
        cursor.execute(query, tuple(review_ids))
        db.commit()
    return redirect(url_for('manage_feedback'))

# Edit feedback entries
@app.route('/edit_feedbacks', methods=['POST'])
def edit_feedbacks():
    review_ids = request.form.getlist('review_ids')
    feedbacks_to_edit = []
    for review_id in review_ids:
        cursor.execute("SELECT * FROM Feedback WHERE review_id = %s", (review_id,))
        feedback = cursor.fetchone()
        feedbacks_to_edit.append(feedback)
    return render_template('edit_feedbacks.html', feedbacks=feedbacks_to_edit)

# Update feedback entries
@app.route('/update_feedbacks', methods=['POST'])
def update_feedbacks():
    for key, value in request.form.items():
        review_id = key.split('-')[1]
        if key.startswith('text-'):
            cursor.execute("UPDATE Feedback SET review_text = %s WHERE review_id = %s", (value, review_id))
        elif key.startswith('rating-'):
            cursor.execute("UPDATE Feedback SET rating = %s WHERE review_id = %s", (value, review_id))
        elif key.startswith('date-'):
            cursor.execute("UPDATE Feedback SET review_date = %s WHERE review_id = %s", (value, review_id))
        elif key.startswith('cust_id-'):
            cursor.execute("UPDATE Feedback SET cust_id = %s WHERE review_id = %s", (value, review_id))
        elif key.startswith('invoice_id-'):
            cursor.execute("UPDATE Feedback SET invoice_id = %s WHERE review_id = %s", (value, review_id))
    db.commit()
    return redirect(url_for('manage_feedback'))


# Display all return slips
@app.route('/return_slips')
def manage_return_slips():
    cursor.execute("SELECT * FROM ReturnSlip")
    return_slips = cursor.fetchall()
    return render_template('return_slips.html', return_slips=return_slips)

# Add new return slip
@app.route('/add_return_slip', methods=['POST'])
def add_return_slip():
    # Get form data
    slip_no = request.form['slip_no']
    inv_id = request.form['inv_id']
    product_id = request.form['product_id']
    quantity = request.form['quantity']
    return_date = request.form['return_date']

    # Insert the new return slip into the database
    query = """
    INSERT INTO ReturnSlip (slip_no, inv_id, product_id, quantity, return_date)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (slip_no, inv_id, product_id, quantity, return_date)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('manage_return_slips'))

# Delete return slips
@app.route('/delete_return_slips', methods=['POST'])
def delete_return_slips():
    slip_ids = request.form.getlist('slip_ids')
    if slip_ids:
        query = "DELETE FROM ReturnSlip WHERE slip_no IN (%s)" % ','.join(['%s'] * len(slip_ids))
        cursor.execute(query, tuple(slip_ids))
        db.commit()
    return redirect(url_for('manage_return_slips'))

# Edit return slips
@app.route('/edit_return_slips', methods=['POST'])
def edit_return_slips():
    slip_ids = request.form.getlist('slip_ids')
    return_slips_to_edit = []
    for slip_no in slip_ids:
        cursor.execute("SELECT * FROM ReturnSlip WHERE slip_no = %s", (slip_no,))
        return_slip = cursor.fetchone()
        return_slips_to_edit.append(return_slip)
    return render_template('edit_return_slips.html', return_slips=return_slips_to_edit)

# Update return slips
@app.route('/update_return_slips', methods=['POST'])
def update_return_slips():
    for key, value in request.form.items():
        slip_no, product_id = key.split('-')[1].split(',')
        if key.startswith('quantity-'):
            cursor.execute("UPDATE ReturnSlip SET quantity = %s WHERE slip_no = %s AND product_id = %s", (value, slip_no, product_id))
        elif key.startswith('return_date-'):
            cursor.execute("UPDATE ReturnSlip SET return_date = %s WHERE slip_no = %s AND product_id = %s", (value, slip_no, product_id))
    db.commit()
    return redirect(url_for('manage_return_slips'))

# Route to fetch customer suggestions based on input
@app.route('/get_customer_suggestions', methods=['GET'])
def get_customer_suggestions():
    term = request.args.get('term', '')
    cursor.execute("SELECT customer_name, type_name FROM Customer INNER JOIN CustomerType ON Customer.customer_type_id = CustomerType.type_id WHERE customer_name LIKE %s", (f"%{term}%",))
    customers = cursor.fetchall()
    suggestions = [{'name': c[0], 'type': c[1]} for c in customers]
    return jsonify(suggestions)

# Route to fetch product suggestions based on input
@app.route('/get_product_suggestions', methods=['GET'])
def get_product_suggestions():
    term = request.args.get('term', '')
    cursor.execute("SELECT product_id, product_type, selling_price FROM Product WHERE product_type LIKE %s", (f"%{term}%",))
    products = cursor.fetchall()
    suggestions = [{'id': p[0], 'type': p[1], 'price': p[2]} for p in products]
    return jsonify(suggestions)

@app.route('/manage_inventory')
def manage_inventory():
    # Logic to manage inventory goes here
    return render_template('manage_inventory.html')

@app.route('/track_movement')
def track_movement():
    # Logic to display product movement tracking form
    # Fetch past transfers to display in the template
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ProductTransferHistory")
    past_transfers = cursor.fetchall()
    connection.close()

    return render_template('track_movement.html', past_transfers=past_transfers)

@app.route('/order_products')
def order_products():
    # Logic for ordering products goes here
    return render_template('order_products.html')

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/submit_complaints', methods=['GET', 'POST'])
def submit_complaints():
    if request.method == 'POST':
        # Capture form data
        supplier = request.form['supplier']
        product_name = request.form['product']
        issue = request.form['issue']
        description = request.form['description']
        priority = request.form['priority']

        # Handle file upload if present
        attachment = request.files['attachments']
        attachment_path = None
        if attachment and attachment.filename != '':
            filename = secure_filename(attachment.filename)
            attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            attachment.save(attachment_path)

            # Store only the path relative to the 'static' folder
            attachment_path = f'uploads/{filename}'

        # Insert data into the Complaints table
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO Complaints (supplier, product_name, issue, description, priority, attachment_path)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (supplier, product_name, issue, description, priority, attachment_path))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('submit_complaints'))

    # Fetch past complaints for display
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Complaints ORDER BY date DESC")
    past_complaints = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('submit_complaints.html', past_complaints=past_complaints)



@app.route('/get_block_suggestions')
def get_block_suggestions():
    query = request.args.get('query', '')
    cursor.execute("SELECT block_name FROM Block WHERE block_name LIKE %s OR block_id LIKE %s", (f'%{query}%', f'%{query}%'))
    blocks = [row[0] for row in cursor.fetchall()]
    return jsonify(blocks)



@app.route('/submit_transfer', methods=['POST'])
def submit_transfer():
    block = request.form['block']
    product_id = request.form['product']
    date = request.form['date']
    time = request.form['time']
    quantity = int(request.form['quantity'])

    # Get a connection from the pool
    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch product details
    cursor.execute("SELECT block_count, warehouse_count FROM Product WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    if product:
        block_count, warehouse_count = product

        # Check warehouse stock
        if warehouse_count < quantity:
            error_message = "Not enough stock in the warehouse."
            connection.close()
            return redirect(url_for('transfer_success', status='error', error_message=error_message))

        # Update counts and record transfer
        new_warehouse_count = warehouse_count - quantity
        new_block_count = block_count + quantity
        cursor.execute("""
            UPDATE Product
            SET warehouse_count = %s, block_count = %s
            WHERE product_id = %s
        """, (new_warehouse_count, new_block_count, product_id))

        cursor.execute("""
            INSERT INTO ProductTransferHistory (block_name, product_id, transfer_date, transfer_time, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (block, product_id, date, time, quantity))

        connection.commit()
        connection.close()

        # Redirect to success page
        return redirect(url_for('transfer_success', status='success'))

    else:
        error_message = "Product not found."
        connection.close()
        return redirect(url_for('transfer_success', status='error', error_message=error_message))

@app.route('/transfer_success')
def transfer_success():
    status = request.args.get('status', '')
    error_message = request.args.get('error_message', '')

    return render_template('transfer_success.html', status=status, error_message=error_message)


# Route to suggest customers based on name input
@app.route('/suggest_customers', methods=['GET'])
def suggest_customers():
    name = request.args.get('name')
    cursor = db.cursor(dictionary=True)
    # Fetch customers with their type based on partial match in name
    cursor.execute("""
        SELECT c.customer_id, c.customer_name, ct.type_name AS customer_type
        FROM Customer AS c
        LEFT JOIN CustomerType AS ct ON c.customer_type_id = ct.type_id
        WHERE c.customer_name LIKE %s
    """, (f"%{name}%",))
    customers = cursor.fetchall()
    cursor.close()
    return jsonify({'customers': customers})


# Route to suggest products based on name input
@app.route('/suggest_products', methods=['GET'])
def suggest_products():
    name = request.args.get('name')
    cursor = db.cursor(dictionary=True)
    # Fetch products with their IDs, names, and selling prices based on partial match in product name
    cursor.execute("""
        SELECT product_id, product_type AS name, selling_price
        FROM Product
        WHERE product_type LIKE %s
    """, (f"%{name}%",))
    products = cursor.fetchall()
    cursor.close()
    return jsonify({'products': products})


@app.route('/add_customer2', methods=['POST'])
def add_customer2():
    # Get form data
    # customer_id = request.form['customer_id']
    customer_name = request.form['customer_name']
    customer_contact = request.form['customer_contact']
    date_of_birth = request.form['date_of_birth']
    email = request.form['email']
    address = request.form['address']
    gender = request.form['gender']
    customer_type_id = request.form.get('customer_type_id')  # Can be null
    membership_to = request.form['membership_to']
    membership_to_from = request.form.get('membership_to_from')
    
    customer_type_id = customer_type_id if customer_type_id else None
    # Insert the new customer into the database
    query = """
    INSERT INTO Customer ( customer_name, customer_contact, date_of_birth, email, address, gender, customer_type_id, membership_to, membership_to_from)
    VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = ( customer_name, customer_contact, date_of_birth, email, address, gender, customer_type_id, membership_to, membership_to_from)

    cursor.execute(query, values)
    db.commit()

    flash("Customer added successfully!", "success")
    return redirect(url_for('cashier_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)