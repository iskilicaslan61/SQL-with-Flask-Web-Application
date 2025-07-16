from flask import Flask, render_template, request
import mysql.connector
import boto3


def get_ssm_parameters():
    ssm = boto3.client('ssm', region_name='us-east-1')

    # AWS SSM Parametrelerini çek
    username_param = ssm.get_parameter(Name='/sql/username')
    password_param = ssm.get_parameter(Name="/sql/password", WithDecryption=True)


    # Parametre değerlerini al
    username = username_param['Parameter']['Value']
    password = password_param['Parameter']['Value']

    return username, password

# Flask uygulamanızı oluşturun
app = Flask(__name__)

# SSM'den parametreleri çek
db_username, db_password = get_ssm_parameters()
db_endpoint = open("/home/ec2-user/dbserver.endpoint", 'r', encoding='UTF-8')

# Configure mysql database

app.config['MYSQL_DATABASE_HOST'] = db_endpoint.readline().strip()
app.config['MYSQL_DATABASE_USER'] = db_username
app.config['MYSQL_DATABASE_PASSWORD'] = db_password
app.config['MYSQL_DATABASE_DB'] = 'Sql-with-Flask-Web-Application'
app.config['MYSQL_DATABASE_PORT'] = 3306
db_endpoint.close()
mysql = MySQL()
mysql.init_app(app) 
connection = mysql.connect()
connection.autocommit(True)
cursor = connection.cursor()

def get_db_connection():
    return mysql.connector.connect(**db_config)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("""
        CREATE TABLE users(
            username VARCHAR(255) NOT NULL PRIMARY KEY,
            email VARCHAR(255)
        )
    """)
    cursor.executemany("""
        INSERT INTO users (username, email) VALUES (%s, %s)
    """, [
        ('dora', 'dora@amazon.com'),
        ('cansın', 'cansın@google.com'),
        ('sencer', 'sencer@bmw.com'),
        ('uras', 'uras@mercedes.com'),
        ('ares', 'ares@porche.com'),
    ])
    conn.commit()
    cursor.close()
    conn.close()

def find_emails(keyword):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT username, email FROM users WHERE username LIKE %s"
    cursor.execute(query, ('%' + keyword + '%',))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    if not results:
        return [("Not Found", "Not Found")]
    return results

def insert_email(name, email):
    if not name or not email:
        return 'Username or email cannot be empty!!'

    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT username FROM users WHERE username = %s"
    cursor.execute(query, (name,))
    exists = cursor.fetchone()
    if exists:
        response = f"User {name} already exists"
    else:
        insert = "INSERT INTO users (username, email) VALUES (%s, %s)"
        cursor.execute(insert, (name, email))
        conn.commit()
        response = f"User {name} and {email} have been added successfully"
    cursor.close()
    conn.close()
    return response

@app.route('/', methods=['GET', 'POST'])
def emails():
    if request.method == 'POST':
        user_app_name = request.form['user_keyword']
        user_emails = find_emails(user_app_name)
        return render_template('emails.html', name_emails=user_emails, keyword=user_app_name, show_result=True)
    else:
        return render_template('emails.html', show_result=False)

@app.route('/add', methods=['GET', 'POST'])
def add_email():
    if request.method == 'POST':
        user_app_name = request.form['username']
        user_app_email = request.form['useremail']
        result_app = insert_email(user_app_name, user_app_email)
        return render_template('add-email.html', result_html=result_app, show_result=True)
    else:
        return render_template('add-email.html', show_result=False)

if __name__ == '__main__':
    init_db()  # Initialize database tables and data once
    app.run(host='0.0.0.0', port=80, debug=True)
