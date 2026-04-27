from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.customers import bp
from app.customers.forms import CustomerForm
from app.models.customer import Customer, PersonCustomer, CompanyCustomer


@bp.route('/')
@login_required
def index():
    sort = request.args.get('sort', 'name')
    direction = request.args.get('dir', 'asc')
    desc = direction == 'desc'

    q = Customer.query
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

    form = CustomerForm()
    if form.validate_on_submit():
        if form.customer_type.data == 'person':
            customer = PersonCustomer(
                customer_name=form.customer_name.data,
                customer_address=form.customer_address.data or None,
            )
        else:
            existing = CompanyCustomer.query.filter_by(company_oib=form.company_oib.data).first()
            if existing:
                flash('A company with this OIB already exists.', 'danger')
                return render_template('customers/form.html', form=form, title='Add Customer')
            customer = CompanyCustomer(
                company_name=form.company_name.data,
                company_address=form.company_address.data,
                company_oib=form.company_oib.data,
            )

        db.session.add(customer)
        db.session.commit()
        flash(f'Customer {customer.display_name} added.', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/form.html', form=form, title='Add Customer')


@bp.route('/<int:customer_id>')
@login_required
def view(customer_id):
    customer = db.session.get(Customer, customer_id) or abort(404)
    return render_template('customers/view.html', customer=customer)


@bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(customer_id):
    if not current_user.can_write:
        abort(403)

    customer = db.session.get(Customer, customer_id) or abort(404)
    form = CustomerForm()

    if form.validate_on_submit():
        if customer.customer_type == 'person':
            customer.customer_name = form.customer_name.data
            customer.customer_address = form.customer_address.data or None
        else:
            existing = CompanyCustomer.query.filter_by(company_oib=form.company_oib.data).first()
            if existing and existing.id != customer.id:
                flash('A company with this OIB already exists.', 'danger')
                return render_template('customers/form.html', form=form, title='Edit Customer', customer=customer)
            customer.company_name = form.company_name.data
            customer.company_address = form.company_address.data
            customer.company_oib = form.company_oib.data

        db.session.commit()
        flash(f'Customer {customer.display_name} updated.', 'success')
        return redirect(url_for('customers.view', customer_id=customer.id))

    form.customer_type.data = customer.customer_type
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

    customer = db.session.get(Customer, customer_id) or abort(404)

    if customer.invoices:
        flash('Cannot delete a customer with existing invoices.', 'danger')
        return redirect(url_for('customers.view', customer_id=customer.id))

    name = customer.display_name
    db.session.delete(customer)
    db.session.commit()
    flash(f'Customer {name} deleted.', 'success')
    return redirect(url_for('customers.index'))
