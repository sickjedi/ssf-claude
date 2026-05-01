from flask import render_template, redirect, url_for, flash, abort, request, g
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.audit import log_action
from app.customers import bp
from app.customers.forms import CustomerForm
from app.models.customer import Customer, PersonCustomer, CompanyCustomer
from app.tenant import require_tenant


@bp.route('/')
@login_required
def index():
    require_tenant()
    sort = request.args.get('sort', 'name')
    direction = request.args.get('dir', 'asc')
    desc = direction == 'desc'

    q = Customer.query.filter_by(organisation_id=g.tenant.id)
    if sort == 'type':
        q = q.order_by(Customer.customer_type.desc() if desc else Customer.customer_type.asc())
    else:  # name (default)
        name_col = func.coalesce(PersonCustomer.customer_name, CompanyCustomer.company_name)
        q = q.order_by(name_col.desc() if desc else name_col.asc())

    customers = q.all()
    return render_template('customers/index.html', customers=customers, sort=sort, direction=direction)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.can_write:
        abort(403)
    require_tenant()

    form = CustomerForm()
    if form.validate_on_submit():
        if form.customer_type.data == 'person':
            customer = PersonCustomer(
                customer_name=form.customer_name.data,
                customer_address=form.customer_address.data or None,
                organisation_id=g.tenant.id,
            )
        else:
            if CompanyCustomer.query.filter_by(company_name=form.company_name.data, organisation_id=g.tenant.id).first():
                flash('A company with this name already exists.', 'danger')
                return render_template('customers/form.html', form=form, title='Add Customer')
            if form.company_oib.data and CompanyCustomer.query.filter_by(company_oib=form.company_oib.data, organisation_id=g.tenant.id).first():
                flash('A company with this OIB already exists.', 'danger')
                return render_template('customers/form.html', form=form, title='Add Customer')
            customer = CompanyCustomer(
                company_name=form.company_name.data,
                company_address=form.company_address.data,
                company_oib=form.company_oib.data,
                organisation_id=g.tenant.id,
            )

        db.session.add(customer)
        db.session.commit()
        log_action('CREATE', 'Customer', f'Added {customer.customer_type} {customer.display_name} (ID: {customer.id})')
        flash(f'Customer {customer.display_name} added.', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/form.html', form=form, title='Add Customer')


@bp.route('/<int:customer_id>')
@login_required
def view(customer_id):
    require_tenant()
    customer = db.session.get(Customer, customer_id)
    if customer is None or customer.organisation_id != g.tenant.id:
        abort(404)
    return render_template('customers/view.html', customer=customer)


@bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(customer_id):
    if not current_user.can_write:
        abort(403)
    require_tenant()

    customer = db.session.get(Customer, customer_id)
    if customer is None or customer.organisation_id != g.tenant.id:
        abort(404)
    form = CustomerForm()

    if form.validate_on_submit():
        if customer.customer_type == 'person':
            customer.customer_name = form.customer_name.data
            customer.customer_address = form.customer_address.data or None
        else:
            existing_name = CompanyCustomer.query.filter_by(company_name=form.company_name.data, organisation_id=g.tenant.id).first()
            if existing_name and existing_name.id != customer.id:
                flash('A company with this name already exists.', 'danger')
                return render_template('customers/form.html', form=form, title='Edit Customer', customer=customer)
            existing_oib = CompanyCustomer.query.filter_by(company_oib=form.company_oib.data, organisation_id=g.tenant.id).first()
            if existing_oib and existing_oib.id != customer.id:
                flash('A company with this OIB already exists.', 'danger')
                return render_template('customers/form.html', form=form, title='Edit Customer', customer=customer)
            customer.company_name = form.company_name.data
            customer.company_address = form.company_address.data
            customer.company_oib = form.company_oib.data

        db.session.commit()
        log_action('UPDATE', 'Customer', f'Updated {customer.customer_type} {customer.display_name} (ID: {customer.id})')
        flash(f'Customer {customer.display_name} updated.', 'success')
        return redirect(url_for('customers.view', customer_id=customer.id))

    # Always lock the type — it cannot be changed after creation
    form.customer_type.data = customer.customer_type
    # Pre-populate other fields only on GET; on POST keep what the user submitted
    if request.method == 'GET':
        if customer.customer_type == 'person':
            form.customer_name.data = customer.customer_name
            form.customer_address.data = customer.customer_address
        else:
            form.company_name.data = customer.company_name
            form.company_address.data = customer.company_address
            form.company_oib.data = customer.company_oib

    return render_template('customers/form.html', form=form, title='Edit Customer', customer=customer)


@bp.route('/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete(customer_id):
    if not current_user.can_delete:
        abort(403)
    require_tenant()

    customer = db.session.get(Customer, customer_id)
    if customer is None or customer.organisation_id != g.tenant.id:
        abort(404)

    if customer.invoices:
        flash('Cannot delete a customer with existing invoices.', 'danger')
        return redirect(url_for('customers.view', customer_id=customer.id))

    name = customer.display_name
    cid = customer.id
    db.session.delete(customer)
    db.session.commit()
    log_action('DELETE', 'Customer', f'Deleted customer {name} (ID: {cid})')
    flash(f'Customer {name} deleted.', 'success')
    return redirect(url_for('customers.index'))
