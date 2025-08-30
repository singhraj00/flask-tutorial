from flask import Blueprint, render_template,request, flash, redirect,url_for
from .. import db
from ..models import Services
from werkzeug.utils import secure_filename
import os 
from flask import current_app
import pandas as pd 

services_bp = Blueprint('services', __name__)

@services_bp.route('/services')
def services():
    all_services = Services.query.order_by(Services.created_at.desc()).all()
    return render_template('services/list_services.html', services=all_services)

@services_bp.route("/add", methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        link = request.form["link"]

        # File Upload
        file = request.files["image"]
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            new_service = Services(
                title=title,
                description=description,
                image_url=filename,  # Save only the filename in the DB
                link=link
            )
            db.session.add(new_service)
            db.session.commit()

            flash("Service added successfully!", "success")
            return redirect('/services')
        else:
            flash("Image is required", "danger")

    return render_template("services/add_service.html")


@services_bp.route("/update/<int:service_id>", methods=["GET", "POST"])
def update_service(service_id):
    service = Services.query.get_or_404(service_id)

    if request.method == "POST":
        service.title = request.form["title"]
        service.description = request.form["description"]
        service.link = request.form["link"]

        # If a new image is uploaded
        file = request.files.get("image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            service.image_url = filename  # Update the image URL

        db.session.commit()
        flash("Service updated successfully!", "success")
        return redirect("/services")

    return render_template("services/update_service.html", service=service)


@services_bp.route("/delete/<int:service_id>/confirm", methods=["GET", "POST"])
def confirm_delete_service(service_id):
    service = Services.query.get_or_404(service_id)

    if request.method == "POST":
        db.session.delete(service)
        db.session.commit()
        flash("Service deleted successfully!", "success")
        return redirect(url_for("services.services"))

    return render_template("services/confirm_delete.html", service=service)

## Advanced Feature 
# --- Bulk Import Route ---
@services_bp.route("/import", methods=["GET", "POST"])
def import_services():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Please upload a file (CSV or Excel)", "danger")
            return redirect(url_for("services.import_services"))

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            # Detect file type
            if filename.endswith(".csv"):
                df = pd.read_csv(filepath)
            elif filename.endswith(".xlsx") or filename.endswith(".xls"):
                df = pd.read_excel(filepath)
            else:
                flash("Only CSV or Excel files are supported", "danger")
                return redirect(url_for("services.import_services"))

            # Normalize all column names to lowercase
            df.columns = [col.lower() for col in df.columns]  # Convert all column names to lowercase

            # Column Mapping
            column_mapping = {
                "title": ["title", "name", "course_name", "service_title"],
                "description": ["description", "short_description", "desc", "course_desc"],
                "image_url": ["image_url", "image", "service_image", "course_image"],
                "link": ["link", "url", "course_link", "service_link"]
            }

            # Renaming columns based on the mapping (case-insensitive)
            for db_field, possible_columns in column_mapping.items():
                for col in possible_columns:
                    col_lower = col.lower()  # Normalize column name to lowercase
                    if col_lower in df.columns:
                        df = df.rename(columns={col_lower: db_field})
                        break  # Stop once we find a matching column name

            # Check if required columns are in the file after renaming
            required_cols = {"title", "description", "link", "image_url"}
            if not required_cols.issubset(df.columns):
                flash(f"File must contain columns: {', '.join(required_cols)}", "danger")
                return redirect(url_for("services.import_services"))

            # Insert or update each row in the DB
            for _, row in df.iterrows():
                # Check if the service already exists based on the title or link
                existing_service = Services.query.filter(
                    (Services.title == row["title"]) | (Services.link == row["link"])
                ).first()

                if existing_service:
                    # If the service exists, update the existing service
                    existing_service.description = row["description"]
                    existing_service.link = row["link"]
                    existing_service.image_url = row.get("image_url", existing_service.image_url)  
                    db.session.commit()
                    flash(f"Service '{row['title']}' updated successfully!", "success")
                else:
                    # If the service does not exist, create a new one
                    new_service = Services(
                        title=row["title"],
                        description=row["description"],
                        link=row["link"],
                        image_url=row.get("image_url", "")  
                    )
                    db.session.add(new_service)
                    db.session.commit()
                    flash(f"Service '{row['title']}' imported successfully!", "success")

        except Exception as e:
            flash(f"Error while importing: {str(e)}", "danger")

        finally:
            # Delete temp file after processing
            if os.path.exists(filepath):
                os.remove(filepath)

        return redirect(url_for("services.services"))

    return render_template("services/import_services.html")

