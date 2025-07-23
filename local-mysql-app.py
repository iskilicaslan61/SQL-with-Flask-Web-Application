from flask import Flask, render_template, request
import pymysql

app = Flask(__name__)

# Local MySQL database connection parameters
# Replace these with your actual local MySQL database credentials
DB_HOST = 'localhost'  # Local MySQL server address
# If you are using a different port, specify it here (default MySQL port is 3306)
# DB_PORT = 3306  # Uncomment if using a non-default port
DB_USER = 'root'  # Replace with your MySQL root username   
DB_PASS = 'password'  # Replace with your MySQL root password
DB_NAME = 'data_db'        

# Veritabanı bağlantısı
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# Email arama
def find_emails(app_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT app_name, email FROM users WHERE app_name=%s"
            cursor.execute(sql, (app_name,))
            result = cursor.fetchall()
            emails = [(row['app_name'], row['email']) for row in result]
    finally:
        conn.close()
    return emails

# Email ekleme
def insert_email(app_name, email):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO users (app_name, email) VALUES (%s, %s)"
            cursor.execute(sql, (app_name, email))
        conn.commit()
        return "Email başarıyla eklendi."
    except Exception as e:
        return f"Hata oluştu: {e}"
    finally:
        conn.close()

# Ana sayfa - Email arama
@app.route('/', methods=['GET', 'POST'])
def emails():
    if request.method == 'POST':
        user_app_name = request.form['user_keyword']
        user_emails = find_emails(user_app_name)
        return render_template('emails.html', name_emails=user_emails, keyword=user_app_name, show_result=True)
    else:
        return render_template('emails.html', show_result=False)

# Email ekleme sayfası
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
    app.run(host='0.0.0.0', port=5000, debug=True)  # 5000 portunu kullan
