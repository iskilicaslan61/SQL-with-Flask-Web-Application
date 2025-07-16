from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import boto3

def get_ssm_parameters():
    ssm = boto3.client('ssm', region_name='us-east-1')
    username_param = ssm.get_parameter(Name='/sql/username')
    password_param = ssm.get_parameter(Name='/sql/password', WithDecryption=True)
    username = username_param['Parameter']['Value']
    password = password_param['Parameter']['Value']
    return username, password

app = Flask(__name__)

db_username, db_password = get_ssm_parameters()

with open("/home/ec2-user/dbserver.endpoint", 'r', encoding='UTF-8') as f:
    db_host = f.readline().strip()

app.config['MYSQL_HOST'] = db_host
app.config['MYSQL_USER'] = db_username
app.config['MYSQL_PASSWORD'] = db_password
app.config['MYSQL_DB'] = 'Sql-with-Flask-Web-Application'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

def init_db():
    conn = mysql.connection
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
        ('cansin', 'cansin@google.com'),
        ('sencer', 'sencer@bmw.com'),
        ('uras', 'uras@mercedes.com'),
        ('ares', 'ares@porche.com'),
    ])
    conn.commit()
    cursor.close()

def find_emails(keyword):
    conn = mysql.connection
    cursor = conn.cursor()
    query = "SELECT username, email FROM users WHERE username LIKE %s"
    cursor.execute(query, ('%' + keyword + '%',))
    results = cursor.fetchall()
    cursor.close()
    if not results:
        return [("Not Found", "Not Found")]
    return results

def insert_email(name, email):
    if not name or not email:
        return 'Username or email cannot be empty!!'
    conn = mysql.connection
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
    # init_db()  # Sadece ilk seferde manuel çalıştırın, production için yorumda bırakın
    app.run(host='0.0.0.0', port=80, debug=True)
