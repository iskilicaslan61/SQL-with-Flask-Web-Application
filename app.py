from flask import Flask, render_template, request
import boto3
import pymysql

app = Flask(__name__)

# AWS region
AWS_REGION = 'us-east-1'  # Bunu kendi bölgenle değiştir

# Parameter Store’dan kullanıcı adı ve şifreyi okuyan fonksiyon
def get_parameter(name):
    ssm = boto3.client('ssm', region_name=AWS_REGION)
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']

# DB bilgilerini Parameter Store’dan al
DB_HOST = 'sql-with-flask-web-app.c5i6e2kemznc.us-east-1.rds.amazonaws.com'  # RDS endpoint
DB_USER = get_parameter('/sql/username')  # Parameter Store path
DB_PASS = get_parameter('/sql/password')  # Parameter Store path
DB_NAME = 'sql-with-flask-web-app'  # Veritabanı adı

# DB bağlantısı için fonksiyon (bağlantıyı her istekte açıp kapatmak daha sağlıklı)
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# Email arama fonksiyonu
def find_emails(app_name):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT email FROM users WHERE app_name=%s"
            cursor.execute(sql, (app_name,))
            result = cursor.fetchall()
            emails = [row['email'] for row in result]
    finally:
        conn.close()
    return emails

# Email ekleme fonksiyonu
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
