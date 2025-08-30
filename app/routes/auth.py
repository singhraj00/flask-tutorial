from flask import Blueprint, render_template, request, redirect, flash
from ..models import User, OTP
from .. import db, mail, login_manager
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from datetime import datetime, timedelta
import random

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
        flash('Invalid email or password', 'danger')
        return redirect('/login')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', 'danger')
            return redirect('/register')
        hashed = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

# Forgot password & verify OTP
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            last_otp = OTP.query.filter_by(email=email).order_by(OTP.created_at.desc()).first()

            # Check agar pichhla OTP valid hai (10 min ke andar)
            if last_otp and datetime.utcnow() < last_otp.created_at + timedelta(minutes=10):
                remaining = int((last_otp.created_at + timedelta(minutes=10) - datetime.utcnow()).total_seconds() // 60)

                # Purana OTP hi resend karo
                reset_url = f"http://127.0.0.1:5000/verify-otp?email={email}"
                msg = Message(
                    subject="🔐 Password Reset Request",
                    recipients=[email],
                    sender="yourname@gmail.com"
                )
                msg.html = render_template("email/otp_email.html", otp_code=last_otp.otp_code, url=reset_url)
                mail.send(msg)

                flash(f'OTP already sent earlier. We have resent it again. Valid for {remaining} more minutes.', 'info')
                return redirect(f'/verify-otp?email={email}')

            # Agar OTP nahi hai ya expire ho gaya hai → naya generate karo
            otp_code = str(random.randint(100000, 999999))
            new_otp = OTP(email=email, otp_code=otp_code)
            db.session.add(new_otp)
            db.session.commit()

            reset_url = f"http://127.0.0.1:5000/verify-otp?email={email}"
            msg = Message(
                subject="🔐 Password Reset Request",
                recipients=[email],
                sender="yourname@gmail.com"
            )
            msg.html = render_template("email/otp_email.html", otp_code=otp_code, url=reset_url)
            mail.send(msg)

            flash('OTP sent to your email. Valid for 10 minutes.', 'info')
            return redirect(f'/verify-otp?email={email}')
        
        flash('Email not found', 'danger')
        return redirect('/forgot-password')
    
    return render_template('forgot_password.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email', '')
    if request.method == 'POST':
        email = request.form['email']
        otp_code = request.form['otp']
        otp_entry = OTP.query.filter_by(email=email, otp_code=otp_code, is_used=False).first()
        if otp_entry and not otp_entry.is_expired():
            otp_entry.is_used = True
            db.session.commit()
            flash('OTP verified! You can reset password.', 'success')
            return redirect(f'/reset-password?email={email}')
        flash('Invalid or expired OTP.', 'danger')
        return redirect(f'/verify-otp?email={email}')
    return render_template('verify_otp.html', email=email)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email', '')
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password reset successfully.', 'success')
            return redirect('/login')
        flash('User not found.', 'danger')
        return redirect('/reset-password')
    return render_template('reset_password.html', email=email)
