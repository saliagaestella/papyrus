from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging as lg


def send_email(documents):
    logger = lg.getLogger(send_email.__name__)
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "6inimartin6@gmail.com"
    receiver_email = [
        "saliagaestella@gmail.com",
        "inigo.martin.llorente@gmail.com",
        "burgalonso@gmail.com",
    ]
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
        logger.info("El correo ha sido enviado exitosamente.")
    except Exception as e:
        logger.info(f"Error al enviar el correo: {e}")
    finally:
        server.quit()

    return 0


def write_html(documents):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Newsletter</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #FAF7F0;
                color: #333;
                -webkit-appearance: none;
            }}
            .container {{
                max-width: 800px;
                margin: 20px auto;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                -webkit-appearance: none;
            }}
            h1 {{
                text-align: center;
                color: #05141C;
            }}
            h2 {{
                color: #89A231;
            }}
            p {{
                line-height: 1.6;
                color: #05141C;
            }}
            a {{
                color: #89A231;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .document {{
                margin-bottom: 20px;
                padding: 15px;
                border-bottom: 1px solid #ddd;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                font-size: 0.9em;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Resumen de Novedades Normativas: {date.today()}</h1>

            {''.join(f'''
            <div class="document">
                <h2>{document[1]["short_name"]}</h2>
                <p><strong>Etiquetas:</strong> {'; '.join(document[1]['etiquetas'])}</p>
                <p><strong>Stakeholders:</strong> {', '.join(document[1]['stakeholders'])}</p>
                <p><strong>Resumen:</strong> {document[1]['resumenes']}</p>
                <p><strong>Impacto:</strong> {'; '.join(document[1]['impactos'])}</p>
                <p><a href="https://www.boe.es/diario_boe/txt.php?id={key}">Leer más: {key}</a></p>
            </div>''' for key, document in documents.items())}

            <div class="footer">
                <p>&copy; {date.today().year} Papyrus. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
