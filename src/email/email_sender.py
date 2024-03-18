import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(documents):
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "6inimartin6@gmail.com"
    receiver_email = ["saliagaestella@gmail.com", "inigo.martin.llorente@gmail.com"]
    password = "bvyo vmpg crfc hihl"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Newsletter"
    message["From"] = sender_email
    message["To"] = ", ".join(receiver_email)

    html_content = write_html(documents)

    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("El correo ha sido enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
    finally:
        server.quit()

    return 0


def write_html(documents):
    html_content = f"""
    <html>
    <head>
        <title>Newsletter</title>
    </head>
    <body>
        <h1>Resumen de Novedades Normativas</h1>"""

    for key, document in documents.items():
        output_final = document[1]
        html_content += f"""
            <h2>ID: {key}</h2>
            <p><strong>Etiquetas:</strong> {', '.join(output_final['etiquetas'])}</p>
            <p><strong>Stakeholders:</strong> {', '.join(output_final['stakeholders'])}</p>
            <p><strong>Resumen:</strong> {output_final['resumenes']}</p>
            <p><strong>Impacto:</strong> {' '.join(output_final['impactos'])}</p>
            <p></p>
        """
    html_content += """
        </body>
        </html>
        """

    return html_content
