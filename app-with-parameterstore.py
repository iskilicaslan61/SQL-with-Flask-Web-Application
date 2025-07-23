from flask import Flask, render_template, request
import boto3
import pymysql

app = Flask(__name__)

AWS_REGION = 'us-east-1'


def get_parameter(name):
    ssm = boto3.client('ssm', region_name=AWS_REGION)
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']


def get_rds_endpoint(db_instance_identifier):
    rds = boto3.client('rds', region_name=AWS_REGION)
    response = rds.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
    endpoint = response['DBInstances'][0]['Endpoint']['Address']
    return endpoint


DB_INSTANCE_IDENTIFIER = 'sql-flask-app-database'  # Replace with your actual DB instance identifier
DB_HOST = get_rds_endpoint(DB_INSTANCE_IDENTIFIER)
DB_USER = get_parameter('/sql/username')
DB_PASS = get_parameter('/sql/password')
DB_NAME = 'email_db' # Replace with your actual database name if different



def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    app_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL
                )
            """)
        conn.commit()
        print("Table 'users' ensured.")
    except Exception as e:
        print(f"Error initializing DB: {e}")
    finally:
        conn.close()


def find_emails(app_name):
    conn = get_db_connection()
    emails = []
    try:
        with conn.cursor() as cursor:
            sql = "SELECT app_name, email FROM users WHERE app_name=%s"
            cursor.execute(sql, (app_name,))
            result = cursor.fetchall()
            emails = [(row['app_name'], row['email']) for row in result]
        if not emails:
            emails = [(app_name, "No emails found for this app name.")]
    except Exception as e:
        print(f"Error occurred while fetching emails: {e}")
        emails = [(app_name, "Error occurred while fetching emails.")]
    finally:
        conn.close()
    return emails


def insert_email(app_name, email):
    if not app_name or not email:
        return 'App name or email cannot be empty!'

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check if this app_name and email already exists
            query = "SELECT * FROM users WHERE app_name = %s AND email = %s"
            cursor.execute(query, (app_name, email))
            result = cursor.fetchall()

            if not result:
                # Insert new user
                insert = "INSERT INTO users (app_name, email) VALUES (%s, %s)"
                cursor.execute(insert, (app_name, email))
                conn.commit()
                return f'App {app_name} and email {email} have been added successfully.'
            else:
                return f'App {app_name} with email {email} already exists.'
    except Exception as e:
        return f'An error occurred: {e}'
    finally:
        conn.close()


def delete_user(app_name):
    if not app_name:
        return 'App name cannot be empty!'
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "DELETE FROM users WHERE app_name = %s"
            cursor.execute(query, (app_name,))
            conn.commit()
            if cursor.rowcount > 0:
                return f'User(s) with app name {app_name} deleted successfully.'
            else:
                return f'No user found with app name {app_name}.'
    except Exception as e:
        return f'An error occurred: {e}'
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


@app.route('/delete', methods=['GET', 'POST'])
def delete_email():
    if request.method == 'POST':
        user_app_name = request.form['username']
        result_app = delete_user(user_app_name)
        return render_template('delete-email.html', result_html=result_app, show_result=True)
    else:
        return render_template('delete-email.html', show_result=False)


if __name__ == '__main__':
    init_db()  # first run to ensure the database is initialized
    app.run(host='0.0.0.0', port=8080, debug=True)
