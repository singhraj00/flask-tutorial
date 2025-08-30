from flask import Blueprint, render_template, request, flash, redirect
from ..models import ContactUs
from .. import db
from flask_login import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/about')
@login_required
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        new_contact = ContactUs(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect('/contact')
    return render_template('contact.html')
