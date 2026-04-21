from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.items import bp
from app.items.forms import ItemForm
from app.models.item import Item


@bp.route('/')
@login_required
def index():
    items = Item.query.order_by(Item.item_name).all()
    return render_template('items/index.html', items=items)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.can_write:
        abort(403)

    form = ItemForm()
    if form.validate_on_submit():
        item = Item(item_name=form.item_name.data, item_price=float(form.item_price.data))
        db.session.add(item)
        db.session.commit()
        flash(f'Item "{item.item_name}" added.', 'success')
        return redirect(url_for('items.index'))

    return render_template('items/form.html', form=form, title='Add Item')


@bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    if not current_user.can_write:
        abort(403)

    item = db.session.get(Item, item_id) or abort(404)
    form = ItemForm(obj=item)

    if form.validate_on_submit():
        item.item_name = form.item_name.data
        item.item_price = float(form.item_price.data)
        db.session.commit()
        flash(f'Item "{item.item_name}" updated.', 'success')
        return redirect(url_for('items.index'))

    return render_template('items/form.html', form=form, title='Edit Item', item=item)


@bp.route('/<int:item_id>/delete', methods=['POST'])
@login_required
def delete(item_id):
    if not current_user.can_delete:
        abort(403)

    item = db.session.get(Item, item_id) or abort(404)
    name = item.item_name
    db.session.delete(item)
    db.session.commit()
    flash(f'Item "{name}" deleted.', 'success')
    return redirect(url_for('items.index'))
