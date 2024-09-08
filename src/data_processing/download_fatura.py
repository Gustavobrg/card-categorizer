import imaplib
import email
import os
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config

def baixar_anexos_email():
    """
    Conecta ao Gmail, busca e-mails com base no remetente e palavra-chave no assunto, baixa anexos e retorna seus caminhos.

    Retorna:
        list: Lista de caminhos dos arquivos anexados baixados.
    """

    # Configurações do Gmail
    EMAIL_HOST = 'imap.gmail.com'
    EMAIL_PORT = 993
    EMAIL_USER = config.EMAIL_USER
    EMAIL_PASS = config.EMAIL_PASS
    FOLDER = 'inbox'
    REMITENTE = config.REMITENTE
    SUBJECT_KEYWORD = config.SUBJECT_KEYWORD
    DATE_FORMAT = '%d-%b-%Y'

    # Calcula a data de 30 dias atrás
    date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime(DATE_FORMAT)

    # Conecta ao servidor de e-mail
    mail = imaplib.IMAP4_SSL(EMAIL_HOST, EMAIL_PORT)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select(FOLDER)

    # Pesquisa por e-mails do remetente específico, com a palavra-chave no assunto, e recebidos nos últimos 30 dias
    search_criteria = f'(FROM "{REMITENTE}" SUBJECT "{SUBJECT_KEYWORD}" SINCE "{date_30_days_ago}")'
    status, data = mail.search(None, search_criteria)

    if status != 'OK':
        print(f'Erro na busca: {status}')
        mail.logout()
        return []

    # Obtém IDs dos e-mails
    email_ids = data[0].split()

    if not email_ids:
        print('Nenhum e-mail encontrado.')
        mail.logout()
        return []

    arquivos_baixados = []

    # Itera sobre os e-mails encontrados
    for email_id in email_ids:
        # Obtém o e-mail
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])

        # Itera sobre as partes do e-mail
        for part in msg.walk():
            # Se a parte for um anexo
            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                filename = part.get_filename()
                if filename:
                    # Salva o anexo no diretório atual
                    filepath = os.path.join("data/", filename)
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    arquivos_baixados.append(filepath)
                    print(f'Arquivo {filename} salvo como {filepath}')

    # Logout e desconecta
    mail.logout()

    return arquivos_baixados