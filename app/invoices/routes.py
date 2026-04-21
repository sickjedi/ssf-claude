import json
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app import db
from app.invoices import bp
from app.invoices.forms import InvoiceForm
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.customer import Customer
from app.models.item import Item


def _generate_invoice_number(year):
    invoices = Invoice.query.filter(Invoice.invoice_number.like(f'%/{year}')).all()
    if invoices:
        seq = max(int(inv.invoice_number.split('/')[0]) for inv in invoices) + 1
    else:
        seq = 1
    return f'{seq:02d}/{year}'


def _customer_choices():
    customers = Customer.query.order_by(Customer.customer_type).all()
    return [(c.id, f'{c.display_name} ({c.customer_type})') for c in customers]


def _items_json():
    items = Item.query.order_by(Item.item_name).all()
    return json.dumps([{'id': i.id, 'name': i.item_name, 'price': i.item_price} for i in items])


def _parse_items():
    item_ids = request.form.getlist('item_id[]')
    names = request.form.getlist('item_name[]')
    prices = request.form.getlist('item_price[]')
    quantities = request.form.getlist('item_quantity[]')
    items = []
    for item_id, name, price, qty in zip(item_ids, names, prices, quantities):
        if name.strip():
            try:
                items.append({
                    'item_id': int(item_id) if item_id else None,
                    'item_name': name.strip(),
                    'item_price': float(price),
                    'item_quantity': int(qty),
                })
            except (ValueError, TypeError):
                pass
    return items


@bp.route('/')
@login_required
def index():
    invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
    return render_template('invoices/index.html', invoices=invoices)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.can_write:
        abort(403)

    form = InvoiceForm()
    form.customer_id.choices = _customer_choices()

    if form.validate_on_submit():
        parsed = _parse_items()
        if not parsed:
            flash('At least one item is required.', 'danger')
            return render_template('invoices/form.html', form=form, title='Add Invoice', invoice=None, items=[], items_json=_items_json())

        invoice = Invoice(
            invoice_number=_generate_invoice_number(form.invoice_date.data.year),
            invoice_date=form.invoice_date.data,
            customer_id=form.customer_id.data,
        )
        db.session.add(invoice)
        db.session.flush()

        for item_data in parsed:
            db.session.add(InvoiceItem(invoice_id=invoice.id, **item_data))

        db.session.commit()
        flash(f'Invoice {invoice.invoice_number} created.', 'success')
        return redirect(url_for('invoices.view', invoice_id=invoice.id))

    return render_template('invoices/form.html', form=form, title='Add Invoice', invoice=None, items=[], items_json=_items_json())


@bp.route('/<int:invoice_id>')
@login_required
def view(invoice_id):
    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    return render_template('invoices/view.html', invoice=invoice)


@bp.route('/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(invoice_id):
    if not current_user.can_write:
        abort(403)

    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    form = InvoiceForm()
    form.customer_id.choices = _customer_choices()

    if form.validate_on_submit():
        parsed = _parse_items()
        if not parsed:
            flash('At least one item is required.', 'danger')
            existing_items = _invoice_items_data(invoice)
            return render_template('invoices/form.html', form=form, title='Edit Invoice',
                                   invoice=invoice, items=existing_items, items_json=_items_json())

        invoice.invoice_date = form.invoice_date.data
        invoice.customer_id = form.customer_id.data

        for item in invoice.items:
            db.session.delete(item)
        db.session.flush()

        for item_data in parsed:
            db.session.add(InvoiceItem(invoice_id=invoice.id, **item_data))

        db.session.commit()
        flash(f'Invoice {invoice.invoice_number} updated.', 'success')
        return redirect(url_for('invoices.view', invoice_id=invoice.id))

    form.invoice_date.data = invoice.invoice_date
    form.customer_id.data = invoice.customer_id

    return render_template('invoices/form.html', form=form, title='Edit Invoice',
                           invoice=invoice, items=_invoice_items_data(invoice), items_json=_items_json())


def _invoice_items_data(invoice):
    return [{'item_id': i.item_id or '', 'item_name': i.item_name,
              'item_price': i.item_price, 'item_quantity': i.item_quantity}
            for i in invoice.items]


@bp.route('/<int:invoice_id>/delete', methods=['POST'])
@login_required
def delete(invoice_id):
    if not current_user.can_delete:
        abort(403)

    invoice = db.session.get(Invoice, invoice_id) or abort(404)
    number = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    flash(f'Invoice {number} deleted.', 'success')
    return redirect(url_for('invoices.index'))
