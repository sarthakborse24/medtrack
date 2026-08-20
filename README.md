# MedTrack — Cloud-Enabled Healthcare Management System

A Flask web application connecting patients and doctors via AWS DynamoDB and SNS.

---

## Features

| Feature | Details |
|---|---|
| Patient registration & login | Hashed passwords (`werkzeug.security`), never plaintext |
| Doctor login | Separate session role, RBAC enforced on every route |
| Appointment booking | Patient picks doctor, date, time; SNS notification sent |
| Diagnosis reports | Doctor submits diagnosis tied to an appointment; SNS notification sent |
| Medical history | Patient sees own records; doctors see only their patients' records |

---

## Project Structure

```
MedTrack/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── decorators.py        # RBAC decorators (patient_required, doctor_required)
│   ├── notifications.py     # SNS notification functions
│   ├── models/
│   │   ├── db.py            # Shared DynamoDB resource helper
│   │   ├── patient.py
│   │   ├── doctor.py
│   │   ├── appointment.py
│   │   └── diagnosis.py
│   ├── routes/
│   │   ├── auth.py          # Register, login (patient + doctor), logout
│   │   ├── patients.py      # Patient dashboard & history
│   │   ├── doctors.py       # Doctor dashboard, diagnosis, patient history
│   │   └── appointments.py  # Appointment booking
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── auth/            # register.html, login.html, doctor_login.html
│       ├── patient/         # dashboard.html, history.html
│       ├── doctor/          # dashboard.html, patient_history.html, diagnosis_form.html
│       ├── appointments/    # book.html
│       └── errors/          # 403.html
├── config.py                # All config loaded from env vars
├── create_tables.py         # DynamoDB table provisioning script
├── run.py                   # Flask entry point
├── requirements.txt
├── .env.example             # Required env var template (no real secrets)
└── README.md
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

**.env contents:**

```env
SECRET_KEY=your-very-secret-key-here
FLASK_DEBUG=false

AWS_REGION=us-east-1

PATIENTS_TABLE=MedTrack_Patients
DOCTORS_TABLE=MedTrack_Doctors
APPOINTMENTS_TABLE=MedTrack_Appointments
DIAGNOSIS_REPORTS_TABLE=MedTrack_DiagnosisReports

SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MedTrackNotifications
```


### 3. AWS Credentials

MedTrack uses **boto3's default credential chain** — no hardcoded keys ever.

**Locally**, authenticate via any of:
- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
- AWS SSO / profiles

**In production (EC2/ECS/Lambda)**, attach an IAM role — no keys needed.

#### IAM Policies — Two Roles

**App runtime user** (scoped-down, day-to-day):
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:Scan",
    "sns:Publish"
  ],
  "Resource": "*"
}
```

**Admin / provisioning user** (one-time setup only — for `create_tables.py`):
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:CreateTable",
    "dynamodb:DescribeTable",
    "dynamodb:ListTables"
  ],
  "Resource": "*"
}
```

> **Note:** Do NOT re-run `create_tables.py` with the scoped-down app user — it
> requires `CreateTable`/`DescribeTable` permissions that the app user intentionally
> does not have. Use a separate admin profile or the AWS Console for table management.

### 4. Provision DynamoDB Tables

Run **once** before starting the app (requires admin IAM permissions):

```bash
python create_tables.py
```

This creates all 4 tables and waits for them to become ACTIVE. It is idempotent — safe to run multiple times.

> **Note:** GSIs on `PatientID` and `DoctorID` for the Appointments table should be
> added via the AWS console or CDK/CloudFormation after initial table creation.

### 5. Create Doctor Accounts

**Option A — Via the web UI (recommended):**

Navigate to `/doctor/register` and enter the admin secret code (set via `ADMIN_SECRET` in `.env`).

**Option B — Via Python script:**

```python
from dotenv import load_dotenv; load_dotenv()
from app import create_app
app = create_app()

with app.app_context():
    from werkzeug.security import generate_password_hash
    from app.models.doctor import create_doctor
    create_doctor(
        name="Alice Patel",
        email="alice@hospital.com",
        password_hash=generate_password_hash("SecurePass123"),
        specialization="General Practice",
        phone="+1 555 000 0001",
    )
    print("Doctor created.")
```

### 6. Run the Application

```bash
python run.py
```

The app starts at **http://localhost:5000**.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Flask session secret — use a long random string |
| `FLASK_DEBUG` | ❌ | Set to `true` to enable debug mode (default: `false`) |
| `AWS_REGION` | ✅ | AWS region for DynamoDB and SNS |
| `PATIENTS_TABLE` | ✅ | DynamoDB table name for patients |
| `DOCTORS_TABLE` | ✅ | DynamoDB table name for doctors |
| `APPOINTMENTS_TABLE` | ✅ | DynamoDB table name for appointments |
| `DIAGNOSIS_REPORTS_TABLE` | ✅ | DynamoDB table name for diagnosis reports |
| `SNS_TOPIC_ARN` | ❌ | SNS topic ARN for notifications (notifications skipped if empty) |
| `ADMIN_SECRET` | ✅ | Secret code required to register a doctor account via `/doctor/register` |

---

## Security Notes

- Passwords hashed with `werkzeug.security.generate_password_hash` (PBKDF2-SHA256)
- No AWS credentials hardcoded — boto3 default credential chain only
- `SECRET_KEY` loaded from env var — never hardcoded
- Debug mode OFF by default
- Role-based access control: patient routes reject doctor sessions and vice versa
- Doctors can only view patient history for patients they have appointments with
- All form inputs validated server-side
