import smtplib
import zipfile
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email_with_zip_photos_simple(
    smtp_server, 
    port, 
    sender_email, 
    sender_password,
    receiver_email, 
    subject, 
    text_message, 
    photo_paths,
    zip_filename="photos.zip"
):
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w') as zipf:
            for photo_path in photo_paths:
                if os.path.exists(photo_path):
                    zipf.write(photo_path, os.path.basename(photo_path))
                else:
                    print(f"Файл не найден: {photo_path}")
        
        zip_buffer.seek(0)
        
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        
        # Добавляем текст
        msg.attach(MIMEText(text_message, 'plain'))
        
        # Добавляем ZIP-архив
        zip_part = MIMEBase('application', 'zip')
        zip_part.set_payload(zip_buffer.getvalue())
        encoders.encode_base64(zip_part)
        zip_part.add_header(
            'Content-Disposition', 
            f'attachment; filename="{zip_filename}"')
        msg.attach(zip_part)
        
        # Отправляем
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"Письмо с архивом '{zip_filename}' успешно отправлено!")
        return True
        
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")
        return False