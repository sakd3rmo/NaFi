import os
import asyncio
import pexpect
import hashlib
import base64
import secrets
import uuid
import shutil
import mimetypes
import zipfile
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

# Load konfigurasi dari .env file
load_dotenv()

# Inisialisasi Flask
app = Flask(__name__, static_url_path='', static_folder='templates')

# Mengambil variabel lingkungan
NAS_IP = os.getenv("NAS_IP")
NAS_SSH_PORT = os.getenv("NAS_SSH_PORT")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
RESULT_FOLDER = os.getenv("RESULT_FOLDER")

# Cek apakah variabel lingkungan telah diset
if not all([NAS_IP, NAS_SSH_PORT, UPLOAD_FOLDER, RESULT_FOLDER]):
    raise EnvironmentError("One or more environment variables are missing!")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULT_FOLDER"] = RESULT_FOLDER

# MIME Types dan Ekstensi File yang Diperbolehkan
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'tar', 'rar', 'gzip', 'docx', 'doc', 'xlsx', 'csv'}
ALLOWED_MIME_TYPES = {
    'txt': 'text/plain',
    'pdf': 'application/pdf',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'zip': 'application/zip',
    'tar': 'application/x-tar',
    'rar': 'application/x-rar-compressed',
    'gzip': 'application/gzip',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'csv': 'text/csv'
}

# Fungsi untuk menghasilkan kunci dari password
def generate_key_from_password(password):
    hash_key = hashlib.sha256(password.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(hash_key[:32]))

# Fungsi untuk mengenkripsi nama file
def encrypt_name(name, fernet):
    base_name, ext = os.path.splitext(name)
    encrypted_name = fernet.encrypt(base_name.encode()).decode()
    return f"{encrypted_name}{ext}"

# Fungsi untuk mendekripsi nama file
def decrypt_name(encrypted_name, fernet):
    encrypted_base, ext = os.path.splitext(encrypted_name)
    try:
        decrypted_base = fernet.decrypt(encrypted_base.encode()).decode()
    except InvalidToken:
        raise ValueError("File or password is incorrect for decryption.")
    return f"{decrypted_base}{ext}"

# Fungsi untuk memeriksa ekstensi dan MIME type file
def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type != ALLOWED_MIME_TYPES.get(ext, None):
        return False

    return True

# Fungsi untuk menghasilkan nama acak
def random_filename(extension):
    salt = secrets.token_hex(8)  # Salt 16 karakter (64 bit)
    return f"{uuid.uuid4().hex}{salt}{extension}"

# Fungsi untuk mengunggah file ke NAS menggunakan Rsync dengan password
async def upload_to_nas_rsync_with_password(file_path, file_name, nas_username, nas_password, destination):
    remote_path = f"{nas_username}@{NAS_IP}:{destination}"
    rsync_command = f"rsync -avz -e \"ssh -p {NAS_SSH_PORT}\" {file_path} {remote_path}/{file_name}"

    async def run_rsync():
        try:
            child = pexpect.spawn(rsync_command)
            child.expect("password:")
            child.sendline(nas_password)
            child.expect(pexpect.EOF)
            return True
        except Exception as e:
            print(f"Error Rsync with password: {e}")
            return False

    result = await run_rsync()
    return result

# Fungsi untuk mengunggah beberapa file menggunakan paralelisme dengan asyncio
async def upload_multiple_files_to_nas(files, nas_username, nas_password, destination):
    tasks = []
    for file_path in files:
        file_name = os.path.basename(file_path)
        tasks.append(upload_to_nas_rsync_with_password(file_path, file_name, nas_username, nas_password, destination))

    results = await asyncio.gather(*tasks)
    return results

# Fungsi untuk mengompres file menjadi zip
def compress_files_to_zip(files, zip_name):
    zip_path = os.path.join(RESULT_FOLDER, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))
    return zip_path

# Fungsi untuk membersihkan folder setelah selesai
def clean_up_folders():
    for folder in [UPLOAD_FOLDER, RESULT_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

# Halaman Utama
@app.route("/")
def index():
    return render_template("index.html")

# Endpoint untuk Upload dan Proses File
@app.route("/process", methods=["POST"])
async def process_file():
    if "files" not in request.files or "password" not in request.form:
        return "Files and passwords must be uploaded.", 400

    uploaded_files = request.files.getlist("files")
    password = request.form["password"]
    action = request.form.get("action")
    result_option = request.form.get("result")
    nas_username = request.form.get("nas_username")
    nas_password = request.form.get("nas_password")
    nas_destination = request.form.get("nas_destination")

    if len(uploaded_files) == 0:
        return "No files selected.", 400

    fernet = generate_key_from_password(password)
    processed_files = []
    try:
        for uploaded_file in uploaded_files:
            if uploaded_file.filename == "" or not allowed_file(uploaded_file.filename):
                return "The uploaded file is invalid.", 400

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(uploaded_file.filename))
            uploaded_file.save(file_path)

            try:
                if action == "encrypt":
                    new_name = encrypt_name(uploaded_file.filename, fernet)
                elif action == "decrypt":
                    new_name = decrypt_name(uploaded_file.filename, fernet)
                else:
                    return "Invalid action.", 400
            except ValueError as e:
                return str(e), 400

            new_file_path = os.path.join(app.config["RESULT_FOLDER"], new_name)
            shutil.move(file_path, new_file_path)
            processed_files.append(new_file_path)

        if result_option == "download":
            if len(processed_files) == 1:
                response = send_file(processed_files[0], as_attachment=True)
            else:
                zip_name = random_filename('.zip')
                zip_path = compress_files_to_zip(processed_files, zip_name)
                processed_files.append(zip_path)
                response = send_file(zip_path, as_attachment=True)
        elif result_option == "upload":
            if not nas_username or not nas_password or not nas_destination:
                return "NAS information is incomplete.", 400
            results = await upload_multiple_files_to_nas(processed_files, nas_username, nas_password, nas_destination)
            # Check upload results
            if all(results):
                return "Files successfully encrypted and uploaded to NAS.", 200
            elif any(results):
                return "Files successfully encrypted, but some files failed to upload to NAS.", 200
            else:
                return "Files were successfully encrypted, but the upload to NAS failed. Please check the username, password, or destination directory again.", 500
        else:
            return "Invalid result option.", 400

    finally:
        for file_path in processed_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        clean_up_folders()

    return response

# Main
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

"""
# HTTPS (Opsional)
if __name__ == "__main__":
    # Start Apps with SSL
    app.run(
        debug=True,
        host="0.0.0.0",
        ssl_context=('certs/localhost.crt', 'certs/localhost.key')
    )
"""
