from app import db, create_app
from app.models import ApplicationType, Category, OSSupport, FHIRSupport, Speciality, PricingLicense, DesignedFor, EHRSupport

app = create_app()

def seed_table(model, names):
    for name in names:
        if not model.query.filter_by(name=name).first():
            db.session.add(model(name=name))
    db.session.commit()

with app.app_context():
    # Ensure tables are created
    db.create_all()

    try:
        # Application Type
        app_types = ['Bulk Data', 'SMART', 'SMART Health Cards']
        seed_table(ApplicationType, app_types)

        # Categories
        categories = [
            'Care Coordination', 'Clinical Research', 'Data Visualization', 'Disease Management',
            'Genomics', 'Medication', 'Patient Engagement', 'Population Health', 'Risk Calculation',
            'FHIR Tools', 'COVID-19', 'Telehealth'
        ]
        seed_table(Category, categories)

        # OS Support
        os_supports = ['iOS', 'Android', 'Web', 'Mac', 'Windows', 'Linux']
        seed_table(OSSupport, os_supports)

        # FHIR Support
        fhir_supports = ['DSTU 1', 'DSTU 2', 'STU 3', 'R4']
        seed_table(FHIRSupport, fhir_supports)

        # Speciality
        specialties = [
            'Anesthesiology', 'Cardiology', 'Gastrointestinal', 'Infectious Disease', 'Neurology',
            'Obstetrics', 'Oncology', 'Pediatrics', 'Pulmonary', 'Renal', 'Rheumatology', 'Trauma',
            'Primary care'
        ]
        seed_table(Speciality, specialties)

        # Pricing/License
        pricings = ['Open Source', 'Free', 'Per User', 'Site-Based', 'Other']
        seed_table(PricingLicense, pricings)

        # Designed For
        designed_fors = ['Clinicians', 'Patients', 'Patients & Clinicians', 'IT']
        seed_table(DesignedFor, designed_fors)

        # EHR Support
        ehr_supports = ['Allscripts', 'Athena Health', 'Epic', 'Cerner']
        seed_table(EHRSupport, ehr_supports)

        print("Database seeded successfully!")
    except Exception as e:
        print(f"Seeding failed: {str(e)}")
        db.session.rollback()