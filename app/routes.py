# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, abort
from flask_login import login_required, current_user
from app import db
from app.models import SmartApp, ApplicationType, Category, OSSupport, FHIRSupport, Speciality, PricingLicense, DesignedFor, EHRSupport
from app.forms import SmartAppForm, GalleryFilterForm
from sqlalchemy import or_, and_
import os
import logging
from werkzeug.utils import secure_filename
import uuid

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

gallery_bp = Blueprint('gallery', __name__)

# Absolute path to the upload folder inside the container
UPLOAD_FOLDER = '/app/uploads/'
ALLOWED_EXTENSIONS = {'jpg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@gallery_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    absolute_upload_folder = os.path.abspath(UPLOAD_FOLDER)
    logger.debug(f"Attempting to serve file: {filename} from {absolute_upload_folder}")
    try:
        return send_from_directory(absolute_upload_folder, filename)
    except FileNotFoundError:
        logger.error(f"File not found: {os.path.join(absolute_upload_folder, filename)}")
        abort(404)

@gallery_bp.route('/')
def index():
    return redirect(url_for('gallery.gallery'))

@gallery_bp.route('/gallery', methods=['GET', 'POST'])
def gallery():
    form = GalleryFilterForm()
    query = SmartApp.query
    filter_params = {}

    # Handle search
    search_term = request.args.get('search', '').strip()
    if search_term:
        query = query.filter(
            or_(
                SmartApp.name.ilike(f'%{search_term}%'),
                SmartApp.description.ilike(f'%{search_term}%'),
                SmartApp.developer.ilike(f'%{search_term}%')
            )
        )
        filter_params['search'] = search_term

    # Existing filter logic
    application_type_ids = request.args.getlist('application_type', type=int)
    category_ids = request.args.getlist('category', type=int)
    os_support_ids = request.args.getlist('os_support', type=int)
    fhir_support_ids = request.args.getlist('fhir_support', type=int)
    speciality_ids = request.args.getlist('speciality', type=int)
    pricing_license_ids = request.args.getlist('pricing_license', type=int)
    designed_for_ids = request.args.getlist('designed_for', type=int)
    ehr_support_ids = request.args.getlist('ehr_support', type=int)

    if application_type_ids:
        query = query.filter(SmartApp.application_type_id.in_(application_type_ids))
        filter_params['application_type'] = application_type_ids
    if category_ids:
        query = query.filter(or_(*[SmartApp.categories.contains(str(cid)) for cid in category_ids]))
        filter_params['category'] = category_ids
    if os_support_ids:
        query = query.filter(or_(*[SmartApp.os_support.contains(str(oid)) for oid in os_support_ids]))
        filter_params['os_support'] = os_support_ids
    if fhir_support_ids:
        query = query.filter(SmartApp.fhir_compatibility_id.in_(fhir_support_ids))
        filter_params['fhir_support'] = fhir_support_ids
    if speciality_ids:
        query = query.filter(or_(*[SmartApp.specialties.contains(str(sid)) for sid in speciality_ids]))
        filter_params['speciality'] = speciality_ids
    if pricing_license_ids:
        query = query.filter(SmartApp.licensing_pricing_id.in_(pricing_license_ids))
        filter_params['pricing_license'] = pricing_license_ids
    if designed_for_ids:
        query = query.filter(SmartApp.designed_for_id.in_(designed_for_ids))
        filter_params['designed_for'] = designed_for_ids
    if ehr_support_ids:
        query = query.filter(or_(*[SmartApp.ehr_support.contains(str(eid)) for eid in ehr_support_ids]))
        filter_params['ehr_support'] = ehr_support_ids

    apps = query.all()
    for app in apps:
        logger.debug(f"App ID: {app.id}, logo_url: {app.logo_url}")
    return render_template(
        'gallery.html',
        apps=apps,
        form=form,
        filter_params=filter_params,
        application_types=ApplicationType.query.all(),
        categories=Category.query.all(),
        os_supports=OSSupport.query.all(),
        fhir_supports=FHIRSupport.query.all(),
        specialties=Speciality.query.all(),
        pricing_licenses=PricingLicense.query.all(),
        designed_fors=DesignedFor.query.all(),
        ehr_supports=EHRSupport.query.all()
    )

@gallery_bp.route('/gallery/<int:app_id>')
def app_detail(app_id):
    app = SmartApp.query.get_or_404(app_id)
    logger.debug(f"App Detail ID: {app_id}, logo_url: {app.logo_url}, app_images: {app.app_images}")
    app_categories = []
    if app.categories:
        category_ids = [int(cid) for cid in app.categories.split(',') if cid]
        app_categories = Category.query.filter(Category.id.in_(category_ids)).all()

    app_specialties = []
    if app.specialties:
        speciality_ids = [int(sid) for sid in app.specialties.split(',') if sid]
        app_specialties = Speciality.query.filter(Speciality.id.in_(speciality_ids)).all()

    app_os_supports = []
    if app.os_support:
        os_ids = [int(oid) for oid in app.os_support.split(',') if oid]
        app_os_supports = OSSupport.query.filter(OSSupport.id.in_(os_ids)).all()

    app_ehr_supports = []
    if app.ehr_support:
        ehr_ids = [int(eid) for eid in app.ehr_support.split(',') if eid]
        app_ehr_supports = EHRSupport.query.filter(EHRSupport.id.in_(ehr_ids)).all()

    return render_template(
        'app_detail.html',
        app=app,
        app_categories=app_categories,
        app_specialties=app_specialties,
        app_os_supports=app_os_supports,
        app_ehr_supports=app_ehr_supports
    )

@gallery_bp.route('/gallery/register', methods=['GET', 'POST'])
@login_required
def register():
    form = SmartAppForm()
    if form.validate_on_submit():
        scopes = form.scopes.data
        valid_scopes = all(
            scope.strip().startswith(('patient/', 'user/', 'launch', 'openid', 'fhirUser', 'offline_access', 'online_access'))
            for scope in scopes.split(',')
            if scope.strip()
        )
        if not valid_scopes or not scopes.strip():
            flash('Invalid SMART scopes. Use formats like patient/Patient.read, launch/patient.', 'danger')
            return render_template('register.html', form=form)

        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            logger.debug(f"Ensured {UPLOAD_FOLDER} exists")
        except Exception as e:
            logger.error(f"Failed to create {UPLOAD_FOLDER}: {e}")
            flash('Error creating upload directory.', 'danger')
            return render_template('register.html', form=form)

        if form.application_type_new.data:
            app_type = ApplicationType(name=form.application_type_new.data)
            db.session.add(app_type)
            db.session.commit()
            form.application_type.data = app_type.id
        if form.categories_new.data:
            category = Category(name=form.categories_new.data)
            db.session.add(category)
            db.session.commit()
            form.categories.data.append(category.id)
        if form.os_support_new.data:
            os_support = OSSupport(name=form.os_support_new.data)
            db.session.add(os_support)
            db.session.commit()
            form.os_support.data.append(os_support.id)
        if form.fhir_compatibility_new.data:
            fhir = FHIRSupport(name=form.fhir_compatibility_new.data)
            db.session.add(fhir)
            db.session.commit()
            form.fhir_compatibility.data = fhir.id
        if form.specialties_new.data:
            speciality = Speciality(name=form.specialties_new.data)
            db.session.add(speciality)
            db.session.commit()
            form.specialties.data.append(speciality.id)
        if form.licensing_pricing_new.data:
            pricing = PricingLicense(name=form.licensing_pricing_new.data)
            db.session.add(pricing)
            db.session.commit()
            form.licensing_pricing.data = pricing.id
        if form.designed_for_new.data:
            designed = DesignedFor(name=form.designed_for_new.data)
            db.session.add(designed)
            db.session.commit()
            form.designed_for.data = designed.id
        if form.ehr_support_new.data:
            ehr = EHRSupport(name=form.ehr_support_new.data)
            db.session.add(ehr)
            db.session.commit()
            form.ehr_support.data.append(ehr.id)

        logo_url = form.logo_url.data
        if form.logo_upload.data:
            file = form.logo_upload.data
            if allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                logger.debug(f"Attempting to save logo to {save_path}")
                try:
                    file.save(save_path)
                    if os.path.exists(save_path):
                        logger.debug(f"Successfully saved logo to {save_path}")
                    else:
                        logger.error(f"Failed to save logo to {save_path}")
                        flash('Failed to save logo.', 'danger')
                        return render_template('register.html', form=form)
                    logo_url = f"/uploads/{filename}"
                    logger.debug(f"Set logo_url to {logo_url}")
                except Exception as e:
                    logger.error(f"Error saving logo to {save_path}: {e}")
                    flash('Error saving logo.', 'danger')
                    return render_template('register.html', form=form)

        app_images = []
        if form.app_image_urls.data:
            app_images.extend([url.strip() for url in form.app_image_urls.data.splitlines() if url.strip().startswith(('http://', 'https://'))])
        if form.app_image_uploads.data:
            file = form.app_image_uploads.data
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                logger.debug(f"Attempting to save app image to {save_path}")
                try:
                    file.save(save_path)
                    if os.path.exists(save_path):
                        logger.debug(f"Successfully saved app image to {save_path}")
                    else:
                        logger.error(f"Failed to save app image to {save_path}")
                        flash('Failed to save app image.', 'danger')
                        return render_template('register.html', form=form)
                    app_images.append(f"/uploads/{filename}")
                except Exception as e:
                    logger.error(f"Error saving app image to {save_path}: {e}")
                    flash('Error saving app image.', 'danger')
                    return render_template('register.html', form=form)

        app = SmartApp(
            name=form.name.data,
            description=form.description.data,
            developer=form.developer.data,
            contact_email=form.contact_email.data,
            logo_url=logo_url or None,
            launch_url=form.launch_url.data,
            client_id=form.client_id.data,
            scopes=scopes,
            website=form.website.data or None,
            designed_for_id=form.designed_for.data,
            application_type_id=form.application_type.data,
            fhir_compatibility_id=form.fhir_compatibility.data,
            categories=','.join(map(str, form.categories.data)) if form.categories.data else None,
            specialties=','.join(map(str, form.specialties.data)) if form.specialties.data else None,
            licensing_pricing_id=form.licensing_pricing.data,
            os_support=','.join(map(str, form.os_support.data)) if form.os_support.data else None,
            app_images=','.join(app_images) if app_images else None,
            ehr_support=','.join(map(str, form.ehr_support.data)) if form.ehr_support.data else None,
            user_id=current_user.id
        )
        db.session.add(app)
        try:
            db.session.commit()
            logger.debug(f"Registered app ID: {app.id}, logo_url: {app.logo_url}, app_images: {app.app_images}")
        except Exception as e:
            logger.error(f"Error committing app to database: {e}")
            db.session.rollback()
            flash('Error saving app to database.', 'danger')
            return render_template('register.html', form=form)
        flash('App registered successfully!', 'success')
        return redirect(url_for('gallery.gallery'))
    return render_template('register.html', form=form)

@gallery_bp.route('/gallery/edit/<int:app_id>', methods=['GET', 'POST'])
@login_required
def edit_app(app_id):
    app = SmartApp.query.get_or_404(app_id)
    if app.user_id != current_user.id:
        flash('You can only edit your own apps.', 'danger')
        return redirect(url_for('gallery.app_detail', app_id=app_id))

    form = SmartAppForm(obj=app)
    if not form.is_submitted():
        if app.categories:
            form.categories.data = [int(cid) for cid in app.categories.split(',') if cid]
        if app.specialties:
            form.specialties.data = [int(sid) for sid in app.specialties.split(',') if sid]
        if app.os_support:
            form.os_support.data = [int(oid) for oid in app.os_support.split(',') if oid]
        if app.ehr_support:
            form.ehr_support.data = [int(eid) for eid in app.ehr_support.split(',') if eid]
        if app.app_images:
            current_images = [img for img in app.app_images.split(',') if img.startswith(('http://', 'https://', '/uploads/'))]
            form.app_image_urls.data = '\n'.join(current_images)
        else:
            form.app_image_urls.data = ''

    if form.validate_on_submit():
        scopes = form.scopes.data
        valid_scopes = all(
            scope.strip().startswith(('patient/', 'user/', 'launch', 'openid', 'fhirUser', 'offline_access', 'online_access'))
            for scope in scopes.split(',')
            if scope.strip()
        )
        if not valid_scopes or not scopes.strip():
            flash('Invalid SMART scopes. Use formats like patient/Patient.read, launch/patient.', 'danger')
            return render_template('edit_app.html', form=form, app=app)

        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            logger.debug(f"Ensured {UPLOAD_FOLDER} exists")
        except Exception as e:
            logger.error(f"Failed to create {UPLOAD_FOLDER}: {e}")
            flash('Error creating upload directory.', 'danger')
            return render_template('edit_app.html', form=form, app=app)

        if form.application_type_new.data:
            app_type = ApplicationType(name=form.application_type_new.data)
            db.session.add(app_type)
            db.session.commit()
            form.application_type.data = app_type.id
        if form.categories_new.data:
            category = Category(name=form.categories_new.data)
            db.session.add(category)
            db.session.commit()
            if form.categories.data is None:
                form.categories.data = []
            form.categories.data.append(category.id)
        if form.os_support_new.data:
            os_support = OSSupport(name=form.os_support_new.data)
            db.session.add(os_support)
            db.session.commit()
            if form.os_support.data is None:
                form.os_support.data = []
            form.os_support.data.append(os_support.id)
        if form.fhir_compatibility_new.data:
            fhir = FHIRSupport(name=form.fhir_compatibility_new.data)
            db.session.add(fhir)
            db.session.commit()
            form.fhir_compatibility.data = fhir.id
        if form.specialties_new.data:
            speciality = Speciality(name=form.specialties_new.data)
            db.session.add(speciality)
            db.session.commit()
            if form.specialties.data is None:
                form.specialties.data = []
            form.specialties.data.append(speciality.id)
        if form.licensing_pricing_new.data:
            pricing = PricingLicense(name=form.licensing_pricing_new.data)
            db.session.add(pricing)
            db.session.commit()
            form.licensing_pricing.data = pricing.id
        if form.designed_for_new.data:
            designed = DesignedFor(name=form.designed_for_new.data)
            db.session.add(designed)
            db.session.commit()
            form.designed_for.data = designed.id
        if form.ehr_support_new.data:
            ehr = EHRSupport(name=form.ehr_support_new.data)
            db.session.add(ehr)
            db.session.commit()
            if form.ehr_support.data is None:
                form.ehr_support.data = []
            form.ehr_support.data.append(ehr.id)

        logo_url = form.logo_url.data
        if form.logo_upload.data:
            file = form.logo_upload.data
            if allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                logger.debug(f"Attempting to save updated logo to {save_path}")
                try:
                    file.save(save_path)
                    if os.path.exists(save_path):
                        logger.debug(f"Successfully saved updated logo to {save_path}")
                    else:
                        logger.error(f"Failed to save updated logo to {save_path}")
                        flash('Failed to save logo.', 'danger')
                        return render_template('edit_app.html', form=form, app=app)
                    logo_url = f"/uploads/{filename}"
                    logger.debug(f"Set logo_url to {logo_url}")
                except Exception as e:
                    logger.error(f"Error saving updated logo to {save_path}: {e}")
                    flash('Error saving logo.', 'danger')
                    return render_template('edit_app.html', form=form, app=app)
        elif not logo_url:
            logo_url = app.logo_url

        app_images = [url.strip() for url in form.app_image_urls.data.splitlines() if url.strip()]
        if form.app_image_uploads.data:
            file = form.app_image_uploads.data
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                logger.debug(f"Attempting to save updated app image to {save_path}")
                try:
                    file.save(save_path)
                    if os.path.exists(save_path):
                        logger.debug(f"Successfully saved updated app image to {save_path}")
                    else:
                        logger.error(f"Failed to save updated app image to {save_path}")
                        flash('Failed to save app image.', 'danger')
                        return render_template('edit_app.html', form=form, app=app)
                    app_images.append(f"/uploads/{filename}")
                except Exception as e:
                    logger.error(f"Error saving updated app image to {save_path}: {e}")
                    flash('Error saving app image.', 'danger')
                    return render_template('edit_app.html', form=form, app=app)

        app.name = form.name.data
        app.description = form.description.data
        app.developer = form.developer.data
        app.contact_email = form.contact_email.data
        app.logo_url = logo_url
        app.launch_url = form.launch_url.data
        app.client_id = form.client_id.data
        app.scopes = scopes
        app.website = form.website.data or None
        app.designed_for_id = form.designed_for.data
        app.application_type_id = form.application_type.data
        app.fhir_compatibility_id = form.fhir_compatibility.data
        app.categories = ','.join(map(str, form.categories.data)) if form.categories.data else None
        app.specialties = ','.join(map(str, form.specialties.data)) if form.specialties.data else None
        app.licensing_pricing_id = form.licensing_pricing.data
        app.os_support = ','.join(map(str, form.os_support.data)) if form.os_support.data else None
        app.app_images = ','.join(app_images) if app_images else None
        app.ehr_support = ','.join(map(str, form.ehr_support.data)) if form.ehr_support.data else None
        try:
            db.session.commit()
            logger.debug(f"Updated app ID: {app.id}, logo_url: {app.logo_url}, app_images: {app.app_images}")
        except Exception as e:
            logger.error(f"Error committing app update to database: {e}")
            db.session.rollback()
            flash('Error updating app in database.', 'danger')
            return render_template('edit_app.html', form=form, app=app)
        flash('App updated successfully!', 'success')
        return redirect(url_for('gallery.app_detail', app_id=app_id))

    return render_template('edit_app.html', form=form, app=app)

@gallery_bp.route('/gallery/delete/<int:app_id>', methods=['POST'])
@login_required
def delete_app(app_id):
    app = SmartApp.query.get_or_404(app_id)
    if app.user_id != current_user.id:
        flash('You can only delete your own apps.', 'danger')
        return redirect(url_for('gallery.app_detail', app_id=app_id))
    db.session.delete(app)
    db.session.commit()
    flash(f'App "{app.name}" deleted successfully.', 'success')
    return redirect(url_for('gallery.gallery'))

@gallery_bp.route('/my-listings')
@login_required
def my_listings():
    apps = SmartApp.query.filter_by(user_id=current_user.id).all()
    return render_template('my_listings.html', apps=apps)

@gallery_bp.route('/test/add')
@login_required
def add_test_app():
    logo_url = "https://via.placeholder.com/150"
    app_images = "https://via.placeholder.com/300"

    test_app = SmartApp(
        name="Test App",
        description="A sample SMART on FHIR app.",
        developer="Test Developer",
        contact_email="test@example.com",
        logo_url=logo_url,
        launch_url="https://example.com/launch",
        client_id="test-client-id",
        scopes="patient/Patient.read,launch/patient",
        website="https://example.com",
        designed_for_id=DesignedFor.query.filter_by(name="Clinicians").first().id if DesignedFor.query.filter_by(name="Clinicians").first() else None,
        application_type_id=ApplicationType.query.filter_by(name="SMART").first().id if ApplicationType.query.filter_by(name="SMART").first() else None,
        fhir_compatibility_id=FHIRSupport.query.filter_by(name="R4").first().id if FHIRSupport.query.filter_by(name="R4").first() else None,
        categories=','.join(str(c.id) for c in Category.query.filter(Category.name.in_(["Clinical", "Patient Engagement"])).all()) if Category.query.filter(Category.name.in_(["Clinical", "Patient Engagement"])).all() else None,
        specialties=','.join(str(s.id) for s in Speciality.query.filter(Speciality.name.in_(["Cardiology", "General Practice"])).all()) if Speciality.query.filter(Speciality.name.in_(["Cardiology", "General Practice"])).all() else None,
        licensing_pricing_id=PricingLicense.query.filter_by(name="Free").first().id if PricingLicense.query.filter_by(name="Free").first() else None,
        os_support=','.join(str(o.id) for o in OSSupport.query.filter(OSSupport.name.in_(["Web", "iOS", "Android"])).all()) if OSSupport.query.filter(OSSupport.name.in_(["Web", "iOS", "Android"])).all() else None,
        app_images=app_images,
        ehr_support=','.join(str(e.id) for e in EHRSupport.query.filter(EHRSupport.name.in_(["Epic", "Cerner"])).all()) if EHRSupport.query.filter(EHRSupport.name.in_(["Epic", "Cerner"])).all() else None,
        user_id=current_user.id
    )
    db.session.add(test_app)
    db.session.commit()
    logger.debug(f"Test app ID: {test_app.id}, logo_url: {test_app.logo_url}")
    flash('Test app added successfully!', 'success')
    return redirect(url_for('gallery.gallery'))