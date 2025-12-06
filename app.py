from flask import Flask, request, render_template_string, redirect
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os 
from dotenv import load_dotenv

app = Flask(__name__)
REPORTS_FILE = "reports.json"

# --- Gmail config --- 
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS").split(",")   # admins who receive reports

# --- Load and save reports ---
def load_reports():
    if not os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, "w") as f:
            json.dump([], f)
    with open(REPORTS_FILE, "r") as f:
        return json.load(f)

def save_reports(reports):
    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, indent=4)

# --- Send Gmail ---
def send_email_to_admin(report):
    subject = f"New Waste Report ID {report['id']}"
    body = f"""
New waste report submitted:

ID: {report['id']}
Type: {report['type']}
Description: {report['description']}
Location: ({report['latitude']}, {report['longitude']})
"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        for admin_email in ADMIN_EMAILS:
            msg['To'] = admin_email
            server.sendmail(EMAIL_ADDRESS, admin_email, msg.as_string())
        server.quit()
        print("Email sent to admins!")
    except Exception as e:
        print("Email failed:", e)

# --- HTML templates ---
HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Barangay Waste Report</title>
</head>
<body>
<h2>Submit Waste Report</h2>
{% if success %}
<p style="color:green;">Report submitted! Admins notified.</p>
{% endif %}
<form method="POST">
Latitude: <input name="latitude" required><br>
Longitude: <input name="longitude" required><br>
Type of Garbage: <input name="type" required><br>
Description: <input name="description" required><br>
<button type="submit">Submit Report</button>
</form>
<p><a href="/admin">Admin View</a></p>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
</head>
<body>
<h2>Admin Panel - Waste Reports</h2>
{% if reports|length == 0 %}
<p>No reports yet.</p>
{% else %}
<table border="1">
<tr>
<th>ID</th>
<th>Latitude</th>
<th>Longitude</th>
<th>Type</th>
<th>Description</th>
<th>Action</th>
</tr>
{% for r in reports %}
<tr>
<td>{{ r.id }}</td>
<td>{{ r.latitude }}</td>
<td>{{ r.longitude }}</td>
<td>{{ r.type }}</td>
<td>{{ r.description }}</td>
<td><a href="/delete/{{ r.id }}">Delete</a></td>
</tr>
{% endfor %}
</table>
{% endif %}
<p><a href="/report">Go to Report Page</a></p>
</body>
</html>
"""

# --- Routes ---
@app.route("/")
def home():
    return redirect("/report")

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        waste_type = request.form["type"]
        description = request.form["description"]

        reports = load_reports()
        report_id = len(reports) + 1
        new_report = {
            "id": report_id,
            "latitude": latitude,
            "longitude": longitude,
            "type": waste_type,
            "description": description
        }
        reports.append(new_report)
        save_reports(reports)

        send_email_to_admin(new_report)
        return render_template_string(HTML_FORM, success=True)
    return render_template_string(HTML_FORM, success=False)

@app.route("/admin")
def admin():
    reports = load_reports()
    return render_template_string(HTML_ADMIN, reports=reports)

@app.route("/delete/<int:report_id>")
def delete(report_id):
    reports = load_reports()
    reports = [r for r in reports if r["id"] != report_id]
    save_reports(reports)
    return redirect("/admin")

# --- Start server ---
if __name__ == "__main__":
    app.run(debug=True)
