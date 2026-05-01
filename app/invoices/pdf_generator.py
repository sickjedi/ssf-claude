import os
from fpdf import FPDF, XPos, YPos

_WINDOWS_FONT_DIR = os.path.join(os.environ.get('WINDIR', os.environ.get('SystemRoot', r'C:\Windows')), 'Fonts')
_LIBERATION_FONT_DIR = '/usr/share/fonts/truetype/liberation'

if os.path.exists(os.path.join(_WINDOWS_FONT_DIR, 'arial.ttf')):
    _ARIAL = os.path.join(_WINDOWS_FONT_DIR, 'arial.ttf')
    _ARIAL_B = os.path.join(_WINDOWS_FONT_DIR, 'arialbd.ttf')
elif os.path.exists(os.path.join(_LIBERATION_FONT_DIR, 'LiberationSans-Regular.ttf')):
    _ARIAL = os.path.join(_LIBERATION_FONT_DIR, 'LiberationSans-Regular.ttf')
    _ARIAL_B = os.path.join(_LIBERATION_FONT_DIR, 'LiberationSans-Bold.ttf')
else:
    raise RuntimeError(
        'No suitable font found for PDF generation. '
        'Install Liberation Sans (linux) or ensure Arial is available (windows).'
    )

_NL = {'new_x': XPos.LMARGIN, 'new_y': YPos.NEXT}


def generate_invoice_pdf(invoice, settings, president_name):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(left=20, top=20, right=20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font('Arial', '', _ARIAL)
    pdf.add_font('Arial', 'B', _ARIAL_B if os.path.exists(_ARIAL_B) else _ARIAL)
    pdf.add_page()

    L = 20
    W = 170

    # Header
    y0 = pdf.get_y()

    if settings.name:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(34, 34, 34)
        pdf.cell(W * 0.55, 7, settings.name, **_NL)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(68, 68, 68)
    for val in filter(None, [settings.address, settings.city]):
        pdf.cell(W * 0.55, 5, val, **_NL)
    if settings.oib:
        pdf.cell(W * 0.55, 5, f'OIB: {settings.oib}', **_NL)
    if settings.iban:
        pdf.cell(W * 0.55, 5, f'IBAN: {settings.iban}', **_NL)
    left_y = pdf.get_y()

    pdf.set_xy(L + W * 0.55, y0)
    pdf.set_text_color(26, 26, 26)
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(W * 0.45, 10, 'INVOICE', align='R', **_NL)
    pdf.set_x(L + W * 0.55)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(68, 68, 68)
    pdf.cell(W * 0.45, 5, f'No: {invoice.invoice_number}', align='R', **_NL)
    pdf.set_x(L + W * 0.55)
    pdf.cell(W * 0.45, 5, f'Date: {invoice.invoice_date.strftime("%d.%m.%Y")}', align='R', **_NL)

    pdf.set_y(max(left_y, pdf.get_y()) + 10)

    # Bill To
    _label(pdf, L, W, 'BILL TO')
    pdf.set_text_color(34, 34, 34)
    if invoice.customer.customer_type == 'person':
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(W, 6, invoice.customer.customer_name, **_NL)
        if invoice.customer.customer_address:
            pdf.set_font('Arial', '', 10)
            pdf.cell(W, 5, invoice.customer.customer_address, **_NL)
    else:
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(W, 6, invoice.customer.company_name, **_NL)
        pdf.set_font('Arial', '', 10)
        if invoice.customer.company_address:
            pdf.cell(W, 5, invoice.customer.company_address, **_NL)
        if invoice.customer.company_oib:
            pdf.cell(W, 5, f'OIB: {invoice.customer.company_oib}', **_NL)

    pdf.ln(8)

    # Items table
    _label(pdf, L, W, 'ITEMS')
    col = [W * 0.50, W * 0.20, W * 0.10, W * 0.20]

    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(85, 85, 85)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(col[0], 7, 'DESCRIPTION', fill=True)
    pdf.cell(col[1], 7, 'UNIT PRICE', align='R', fill=True)
    pdf.cell(col[2], 7, 'QTY', align='R', fill=True)
    pdf.cell(col[3], 7, 'SUBTOTAL', align='R', fill=True, **_NL)
    pdf.set_draw_color(204, 204, 204)
    pdf.line(L, pdf.get_y(), L + W, pdf.get_y())

    pdf.set_text_color(34, 34, 34)
    pdf.set_font('Arial', '', 10)
    for item in invoice.items:
        pdf.cell(col[0], 7, item.item_name)
        pdf.cell(col[1], 7, f'{item.item_price:.2f}', align='R')
        pdf.cell(col[2], 7, str(item.item_quantity), align='R')
        pdf.cell(col[3], 7, f'{item.subtotal:.2f}', align='R', **_NL)
        pdf.set_draw_color(238, 238, 238)
        pdf.line(L, pdf.get_y(), L + W, pdf.get_y())

    pdf.ln(1)
    pdf.set_draw_color(51, 51, 51)
    pdf.line(L, pdf.get_y(), L + W, pdf.get_y())
    pdf.ln(3)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(col[0] + col[1] + col[2], 7, 'Total', align='R')
    pdf.cell(col[3], 7, f'{invoice.total:.2f}', align='R', **_NL)

    pdf.ln(10)

    # Footer
    pdf.set_draw_color(221, 221, 221)
    pdf.line(L, pdf.get_y(), L + W, pdf.get_y())
    pdf.ln(3)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(102, 102, 102)

    if settings.iban:
        pay = f'Payment to: {settings.iban}'
        if settings.name:
            pay += f' \u2014 {settings.name}'
        pdf.cell(W, 5, pay, **_NL)

    pdf.multi_cell(W, 5, 'Udruga Tvornica Znanosti nije u sustavu PDV-a prema \u010dlanku 90 stavku 2 zakona o PDV-i. PDV nije obra\u010dunat.')

    if president_name:
        pdf.cell(W, 5, f'Odgovorna osoba za izdavanje ra\u010duna: {president_name}', **_NL)

    return bytes(pdf.output())


def _label(pdf, L, W, text):
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(136, 136, 136)
    pdf.cell(W, 5, text, **_NL)
    pdf.set_draw_color(221, 221, 221)
    pdf.line(L, pdf.get_y(), L + W, pdf.get_y())
    pdf.ln(3)
