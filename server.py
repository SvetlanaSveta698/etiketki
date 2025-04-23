from flask import Flask, request, send_file, send_from_directory
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from barcode import EAN13
from barcode.writer import ImageWriter
from PIL import Image
import os

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/generate', methods=['POST'])
def generate_labels():
    excel_file = request.files.get('excel_file')
    if not excel_file:
        return "Нет файла", 400

    try:
        width = float(request.form.get('width_mm', 0))
        height = float(request.form.get('height_mm', 0))
    except ValueError:
        return "Неверные размеры", 400

    df = pd.read_excel(excel_file)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width * mm, height * mm))

    for _, row in df.iterrows():
        # Надпись над штрихкодом
        pdf.setFont("Helvetica", int(row.get('font_size', 5)))
        pdf.drawCentredString((width / 2) * mm, (height - 10) * mm, "ЧайКофеГрад")

        # Текст под штрихкодом
        text_y = height - 20
        for text in [str(row.get('article', '')), str(row.get('brand', '')), str(row.get('name', ''))]:
            pdf.drawCentredString((width / 2) * mm, text_y * mm, text)
            text_y -= 5

        # Генерация штрихкода
        barcode = EAN13(str(row.get('barcode', '')).zfill(13), writer=ImageWriter())
        barcode_img = barcode.render(writer_options={"module_width": 0.35, "module_height": 24})
        img_io = BytesIO()
        barcode_img.save(img_io, format='PNG')
        img_io.seek(0)
        barcode_pil = Image.open(img_io)

        # Вставка штрихкода
        pdf.drawInlineImage(barcode_pil, (width/2 - 20) * mm, 5 * mm, width=40 * mm, height=24 * mm)
        pdf.showPage()

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="etiketki.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
