import smtplib
import dns.resolver
import os
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import Flask-CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for the app

# Function to validate the email format
def validate_email_format(email):
    import re
    regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(regex, email) is not None

# Function to validate the domain using DNS MX records
def validate_domain(email):
    domain = email.split('@')[-1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.NoAnswer:
        return False
    except Exception:
        return False

# Function to validate email existence using SMTP
def verify_email_smtp(email):
    domain = email.split('@')[-1]
    try:
        # Get the MX records for the domain
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(mx_records[0].exchange)

        # Connect to the mail server
        server = smtplib.SMTP(mx_record)
        server.set_debuglevel(0)
        server.helo()
        # Use a dummy email as the sender
        server.mail('noreply@yourdomain.com')  
        code, message = server.rcpt(email)
        server.quit()
        return code == 250  # 250 means the email is valid
    except Exception as e:
        print(f"SMTP Verification Error: {e}")
        return False




@app.route('/verify_email', methods=['POST'])
def verify_email():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Step 1: Validate email format
    if not validate_email_format(email):
        return jsonify({"valid": False, "message": "Invalid email format"})

    # Step 2: Validate domain
    if not validate_domain(email):
        return jsonify({"valid": False, "message": "Invalid email domain"})

    # Step 3: Verify email existence via SMTP
    if verify_email_smtp(email):
        return jsonify({"valid": True, "message": "Email exists"})
    else:
        return jsonify({"valid": False, "message": "Email does not exist or is undeliverable"})


if __name__ == '__main__':
    app.run(debug=True)
else:
    # Required for Vercel
    app = app