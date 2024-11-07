import os
from flask import Flask, render_template, request, send_file
from googletrans import Translator  # Alternative translation library
from docx import Document
import fitz  # PyMuPDF
from io import BytesIO

app = Flask(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# List of supported languages for the dropdown
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('pt', 'Portuguese'),
    ('ru', 'Russian'),
    ('zh-cn', 'Chinese')
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def translate_text(text, target_language):
    translator = Translator()
    try:
        translated_text = translator.translate(text, dest=target_language).text
        return translated_text
    except Exception as e:
        print(f"Error translating text: {e}")
        return text  # Return original text if translation fails

def process_docx(file, target_language):
    doc = Document(file)
    for para in doc.paragraphs:
        if para.text.strip():  # Skip empty paragraphs
            translated_text = translate_text(para.text, target_language)
            para.text = translated_text
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output

def process_pdf(file, target_language):
    pdf_doc = fitz.open(stream=file.read(), filetype="pdf")
    translated_text = ""
    for page in pdf_doc:
        text = page.get_text("text")
        translated_text += translate_text(text, target_language) + "\n\n"

    # Convert the translated text into a PDF format again
    new_pdf = fitz.open()
    new_page = new_pdf.new_page(width=pdf_doc[0].rect.width, height=pdf_doc[0].rect.height)
    new_page.insert_text((72, 72), translated_text, fontsize=12)
    output = BytesIO()
    new_pdf.save(output)
    output.seek(0)
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        target_language = request.form.get('language')
        
        if file.filename == '' or not allowed_file(file.filename):
            return "Invalid file type or no file selected", 400

        # Process the file
        if file and allowed_file(file.filename):
            filename = file.filename
            if filename.endswith('.docx'):
                translated_file = process_docx(file, target_language)
                return send_file(translated_file, as_attachment=True, download_name=f"translated_{filename}")
            elif filename.endswith('.pdf'):
                translated_file = process_pdf(file, target_language)
                return send_file(translated_file, as_attachment=True, download_name=f"translated_{filename}")
    
    return render_template('index.html', languages=LANGUAGES)

if __name__ == '__main__':
    app.run(debug=True)
