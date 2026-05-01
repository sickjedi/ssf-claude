from decimal import Decimal, InvalidOperation
from flask import render_template, redirect, url_for, flash, abort, request, make_response, g
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload, subqueryload
from app import db
from app.audit import log_action
from app.invoices import bp
from app.invoices.forms import InvoiceForm
from app.invoices.pdf_generator import generate_invoice_pdf
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.customer import Customer, PersonCustomer, CompanyCustomer
from app.models.item import Item
from app.models.member import Member
from app.models.user import User, Role
from app.tenant import require_tenant

_INVOICE_LOAD_OPTIONS = [joinedload(Invoice.customer), subqueryload(Invoice.items)]


def _generate_invoice_number(year):
    max_seq = db.session.query(
        func.max(func.cast(func.split_part(Invoice.invoice_number, '/', 1), db.Integer))
    ).filter(
        Invoice.organisation_id == g.tenant.id,
        Invoice.invoice_number.like(f'%/{year}')
    ).scalar()
    seq = (max_seq or 0) + 1
    return f'{seq:02d}/{year}'


def _customer_choices():
    customers = Customer.query.filter_by(organisation_id=g.tenant.id).order_by(Customer.customer_type).all()
    return [(c.id, f'{c.display_name} ({c.customer_type})') for c in customers]


def _items_data():
    items = Item.query.filter_by(organisation_id=g.tenant.id).order_by(Item.item_name).all()
    return [{'id': i.id, 'name': i.item_name, 'price': float(i.item_price)} for i in items]


def _parse_items():
    item_ids = request.form.getlist('item_id[]')
    names = request.form.getlist('item_name[]')
    prices = request.form.getlist('item_price[]')
    quantities = request.form.getlist('item_quantity[]')

    if len({len(item_ids), len(names), len(prices), len(quantities)}) > 1:
        flash('Item data was malformed — array lengths do not match.', 'danger')
        return None  # None signals the error was already flashed; [] means no items

    items = []
    parse_errors = False
    for item_id, name, price, qty in zip(item_ids, names, prices, quantities):
        if not name.strip():
            continue
        try:
            items.append({
                'item_id': int(item_id) if item_id else None,
                'item_name': name.strip(),
                'item_price': Decimal(price),
                'item_quantity': int(qty),
            })
        except (ValueError, TypeError, InvalidOperation):
            parse_errors = True

    if parse_errors:
        flash('Some items could not be parsed and were skipped.', 'warning')

    return items


@bp.route('/')
@login_required
def index():
    require_tenant()
    sort = request.args.get('sort', 'date')
    direction = request.args.get('dir', 'desc')
    desc = direction == 'desc'

    base_q = Invoice.query.filter_by(organisation_id=g.tenant.id)

    if sort == 'total':
        invoices = base_q.options(*_INVOICE_LOAD_OPTIONS).all()
        invoices.sort(key=lambda inv: inv.total, reverse=desc)
    elif sort == 'number':
        invoices = base_q.options(*_INVOICE_LOAD_OPTIONS).order_by(
            Invoice.invoice_number.desc() if desc else Invoice.invoice_number.asc()
        ).all()
    elif sort == 'customer':
        name_col = func.coalesce(PersonCustomer.customer_name, CompanyCustomer.company_name)
        invoices = base_q.options(*_INVOICE_LOAD_OPTIONS).join(
            Customer, Invoice.customer_id == Customer.id
        ).order_by(name_col.desc() if desc else name_col.asc()).all()
    else:  # date (default)
        invoices = base_q.options(*_INVOICE_LOAD_OPTIONS).order_by(
            Invoice.invoice_date.desc() if desc else Invoice.invoice_date.asc()
        ).all()

    return render_template('invoices/index.html', invoices=invoices, sort=sort, direction=direction)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.can_write:
        abort(403)
    require_tenant()

    form = InvoiceForm()
    form.customer_id.choices = _customer_choices()

    if form.validate_on_submit():
        parsed = _parse_items()
        if parsed is None:
            return render_template('invoices/form.html', form=form, title='Add Invoice', invoice=None, items=[], items_json=_items_data())
        if not parsed:
            flash('At least one item is required.', 'danger')
            return render_template('invoices/form.html', form=form, title='Add Invoice', invoice=None, items=[], items_json=_items_data())

        invoice = Invoice(
            invoice_number=_generate_invoice_number(form.invoice_date.data.year),
            invoice_date=form.invoice_date.data,
            customer_id=form.customer_id.data,
            organisation_id=g.tenant.id,
        )
        db.session.add(invoice)
        db.session.flush()

        for item_data in parsed:
            db.session.add(InvoiceItem(invoice_id=invoice.id, **item_data))

        db.session.commit()
        log_action('CREATE', 'Invoice', f'Created invoice {invoice.invoice_number} (ID: {invoice.id})')
        flash(f'Invoice {invoice.invoice_number} created.', 'success')
        return redirect(url_for('invoices.view', invoice_id=invoice.id))

    return render_template('invoices/form.html', form=form, title='Add Invoice', invoice=None, items=[], items_json=_items_data())


@bp.route('/<int:invoice_id>')
@login_required
def view(invoice_id):
    require_tenant()
    invoice = db.session.get(Invoice, invoice_id)
    if invoice is None or invoice.organisation_id != g.tenant.id:
        abort(404)
    return render_template('invoices/view.html', invoice=invoice)


@bp.route('/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(invoice_id):
    if not current_user.can_write:
        abort(403)
    require_tenant()

    invoice = db.session.get(Invoice, invoice_id)
    if invoice is None or invoice.organisation_id != g.tenant.id:
        abort(404)
    form = InvoiceForm()
    form.customer_id.choices = _customer_choices()

    if form.validate_on_submit():
        parsed = _parse_items()
        if parsed is None:
            return render_template('invoices/form.html', form=form, title='Edit Invoice',
                                   invoice=invoice, items=_invoice_items_data(invoice), items_json=_items_data())
        if not parsed:
            flash('At least one item is required.', 'danger')
            return render_template('invoices/form.html', form=form, title='Edit Invoice',
                                   invoice=invoice, items=_invoice_items_data(invoice), items_json=_items_data())

        invoice.invoice_date = form.invoice_date.data
        invoice.customer_id = form.customer_id.data

        for item in invoice.items:
            db.session.delete(item)
        db.session.flush()

        for item_data in parsed:
            db.session.add(InvoiceItem(invoice_id=invoice.id, **item_data))

        db.session.commit()
        log_action('UPDATE', 'Invoice', f'Updated invoice {invoice.invoice_number} (ID: {invoice.id})')
        flash(f'Invoice {invoice.invoice_number} updated.', 'success')
        return redirect(url_for('invoices.view', invoice_id=invoice.id))

    form.invoice_date.data = invoice.invoice_date
    form.customer_id.data = invoice.customer_id

    return render_template('invoices/form.html', form=form, title='Edit Invoice',
                           invoice=invoice, items=_invoice_items_data(invoice), items_json=_items_data())


def _invoice_items_data(invoice):
    return [{'item_id': i.item_id or '', 'item_name': i.item_name,
              'item_price': i.item_price, 'item_quantity': i.item_quantity}
            for i in invoice.items]


@bp.route('/<int:invoice_id>/pdf')
@login_required
def pdf(invoice_id):
    require_tenant()
    invoice = db.session.get(Invoice, invoice_id)
    if invoice is None or invoice.organisation_id != g.tenant.id:
        abort(404)

    president = (User.query
                 .join(Member, User.member_id == Member.id)
                 .filter(Member.organisation_id == g.tenant.id,
                         User.role == Role.PRESIDENT)
                 .first())
    president_name = president.member.full_name if president else None

    pdf_bytes = generate_invoice_pdf(invoice, g.tenant, president_name)

    filename = f'invoice_{invoice.invoice_number.replace("/", "-")}.pdf'
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@bp.route('/<int:invoice_id>/delete', methods=['POST'])
@login_required
def delete(invoice_id):
    if not current_user.can_delete:
        abort(403)
    require_tenant()

    invoice = db.session.get(Invoice, invoice_id)
    if invoice is None or invoice.organisation_id != g.tenant.id:
        abort(404)
    number = invoice.invoice_number
    inv_id = invoice.id
    db.session.delete(invoice)
    db.session.commit()
    log_action('DELETE', 'Invoice', f'Deleted invoice {number} (ID: {inv_id})')
    flash(f'Invoice {number} deleted.', 'success')
    return redirect(url_for('invoices.index'))
