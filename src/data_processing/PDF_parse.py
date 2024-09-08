import pdfplumber
import pandas as pd
import re
import pikepdf
import io
import os
import sys
from datetime import datetime
import pycountry

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config

def extrair_fatura_pdf(pdf_path, csv_output_path):
    """
    Abre um PDF protegido por senha, extrai transações financeiras e salva os dados em um arquivo CSV.

    Args:
        pdf_path (str): Caminho para o arquivo PDF.
        csv_output_path (str): Caminho para salvar o arquivo CSV de saída.

    Retorna:
        pd.DataFrame: DataFrame contendo as transações extraídas do PDF.
    """
    
    def extract_transactions_from_line(line):
        """
        Extrai múltiplas transações de uma linha de texto do PDF.

        Args:
            line (str): Linha de texto contendo uma ou mais transações.

        Retorna:
            list: Lista de transações extraídas.
        """
        transactions = []
        # Regex para capturar as transações
        pattern = re.compile(r'(\d{2}/\d{2})\s+([A-Za-z0-9* .,]+?)\s+([A-Z]{2})\s+([A-Z$]+)\s+([\d.,-]+)')
        
        # Encontrar todas as correspondências
        for match in pattern.finditer(line):
            date = match.group(1)
            transaction = match.group(2).strip()
            country = match.group(3)
            currency = match.group(4)
            amount = match.group(5).replace(',', '.').strip()  # Normaliza a vírgula para ponto
            if amount.endswith('-'):
                amount = '-' + amount[:-1]  # Corrige valores negativos no formato "123,45-"
            transactions.append([date, transaction, country, currency, amount])
        
        return transactions

    def determine_year(date_str, due_date_month):
        """
        Determina o ano para uma data com base no mês de vencimento.

        Args:
            date_str (str): Data da transação no formato 'dd/mm'.
            due_date_month (int): Mês de vencimento da fatura.

        Retorna:
            int: Ano da transação.
        """
        day, month = map(int, date_str.split('/'))
        if month == 12 and due_date_month == 1:
            return pd.Timestamp.now().year - 1
        else:
            return pd.Timestamp.now().year

    def is_valid_date(date_str):
        """
        Verifica se a data está no formato 'yyyy-mm-dd'.

        Args:
            date_str (str): Data a ser verificada.

        Retorna:
            bool: Verdadeiro se a data for válida, falso caso contrário.
        """
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def is_valid_country_code(country_code):
        """
        Verifica se o código do país é uma sigla de dois caracteres válidos.

        Args:
            country_code (str): Código do país a ser verificado.

        Retorna:
            bool: Verdadeiro se o código do país for válido, falso caso contrário.
        """
        return pycountry.countries.get(alpha_2=country_code) is not None

    def is_valid_float(value):
        """
        Verifica se o valor pode ser convertido para float.

        Args:
            value (str): Valor a ser verificado.

        Retorna:
            bool: Verdadeiro se o valor for um float válido, falso caso contrário.
        """
        try:
            float(value)
            return True
        except ValueError:
            return False

    def is_valid_currency(currency_code):
        # Lista abrangente de símbolos de moeda
        valid_symbols = [
            "R$", "$", "€", "£", "¥", "₹", "₽", "₩", "₺", "₫", "₪", "₭", "₮", "₨", "₣", "₲", "₼", "₦", "₧", "₨", "៛", "₨", "৳"
        ]
    
        # Verifica se o símbolo está na lista de símbolos válidos
        return currency_code in valid_symbols

    # Lista para armazenar todas as transações extraídas
    all_transactions = []
    senha = config.PDF_PASS
    # Abra o PDF protegido por senha usando pikepdf
    with pikepdf.open(pdf_path, password=senha) as pdf:
        # Usando um buffer de memória para armazenar o PDF desbloqueado
        with io.BytesIO() as buffer:
            pdf.save(buffer)
            buffer.seek(0)

            # Abra o PDF desbloqueado na memória usando pdfplumber
            with pdfplumber.open(buffer) as pdf_desbloqueado:
                for page in pdf_desbloqueado.pages:
                    text = page.extract_text()
                    if "Detalhamento da Fatura" in text:  # Procura o trecho relevante
                        lines = text.split("\n")
                        for line in lines:
                            transactions = extract_transactions_from_line(line)
                            if transactions:
                                all_transactions.extend(transactions)
    
    # Verifica se há transações e converte em um DataFrame
    if all_transactions:
        due_date_month = 12  # Você pode ajustar esse valor conforme necessário
        all_transactions_updated = []
        for transaction in all_transactions:
            date_str, trans, country, currency, amount = transaction
            year = determine_year(date_str, due_date_month)
            date_updated = f"{year}-{date_str[3:]}-{date_str[:2]}"

            # Valida os dados
            if (is_valid_date(date_updated) and 
                is_valid_country_code(country) and 
                is_valid_float(amount) and 
                is_valid_currency(currency)):
                all_transactions_updated.append([date_updated, trans, country, currency, amount])
            else:
                print(f"Dados inválidos encontrados: Data: {date_updated}, País: {country}, Moeda: {currency}, Valor: {amount}")
        
        df = pd.DataFrame(all_transactions_updated, columns=["Data", "Transação", "País", "Moeda", "Valor"])
        df.to_csv(csv_output_path, index=False)
        print(f'Arquivo CSV salvo como {csv_output_path}')
        return df
    else:
        print("Nenhuma transação encontrada.")
        return pd.DataFrame()  # Retorna um DataFrame vazio caso não encontre transações
