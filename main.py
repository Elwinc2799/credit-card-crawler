import pandas as pd
import requests
from bs4 import BeautifulSoup


def extract_cashback_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    min_income_value = 0
    min_income_section = soup.find('section', class_='Summary')
    if min_income_section:
        min_income_tag = min_income_section.find('dt', string='Min. Income')
        min_income_value = min_income_tag.find_next('dd').find('span').get_text(
            strip=True) if min_income_tag else "No Info"

    cashback_section = soup.find('section', class_='Tile', id='cashback')

    if cashback_section:
        cashback_info = []

        # Extract data from cashback table
        table = cashback_section.find('table')

        # Check if the table exists
        if table:
            # Extract all rows in the table
            rows = table.find_all('tr')[1:]  # Exclude the header row
            for row in rows:
                columns = row.find_all('td')

                # Ensure there are at least 4 columns before accessing their attributes
                if len(columns) >= 4:
                    category = columns[0].text.strip()
                    cashback_rate = columns[1].find('span').text.strip() if columns[1].find('span') else columns[
                        1].text.strip()
                    monthly_cap = columns[2].text.strip()
                    spend = columns[3].text.strip()

                    cashback_info.append({
                        'Cashback Category': category,
                        'Cashback Rate': cashback_rate,
                        'Monthly Cap': monthly_cap,
                        'Spend': spend
                    })
        return cashback_info, min_income_value
    else:
        return None, min_income_value


def extract_annual_fee_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    fees_section = soup.find('section', class_='Tile', id='fees')

    if fees_section:
        annual_fee_info = []

        # Extract data from annual fee section
        annual_fee_dl = fees_section.find('dl')
        annual_fee_dt = annual_fee_dl.find('dt', string='Annual Fee')

        if annual_fee_dt:
            # Extract only the specific annual fee information
            annual_fee_dd = annual_fee_dt.find_next('dd')

            # Process and format the annual fee information
            for li in annual_fee_dd.find_all('li'):
                annual_fee_info.append(li.find('span').text.strip() + ' ' + li.text.strip()[len(li.find('span').text):])

        return annual_fee_info
    else:
        return None


def extract_annual_fee_simple_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    summary_section = soup.find('section', class_='Summary')

    if summary_section:
        annual_fee_simple = summary_section.find('dt', string='Annual Fee').find_next('dd').text.strip()
        return annual_fee_simple
    else:
        return None


url = "https://ringgitplus.com/en/credit-card/cashback/"
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the section with class "Sidebar"
    sidebar_section = soup.find('section', class_='Sidebar')

    # Initialize lists to store data
    rows = []

    # Mapping of bank names
    # ["AEON", "Alliance Bank", "HSBC", "Public Bank", "RHB", "Standard Chartered", "UOB"]   # sign-up offers bank list
    bank_names = ["AEON", "Affin", "Alliance Bank", "Ambank", "BSN", "Bank Rakyat", "CIMB", "HSBC", "Hong Leong",
                  "Maybank", "OCBC", "Public", "RHB", "Standard Chartered", "UOB"]  # cashback bank list

    # Iterate through each list item under the "Products CRCD" class
    for li in sidebar_section.find('ul', class_='Products CRCD').find_all('li'):
        # Extract data from each list item
        card_name = li.find('h3').find('a').text.strip()
        cashback = li.find('dt', string='Cashback').find_next('dd').text.strip()
        card_link = li.find('h3').find('a')['href']

        # Correcting card link
        full_card_link = f"https://ringgitplus.com{card_link}"

        # Determine the bank name based on card name
        matched_bank_names = [bank for bank in bank_names if bank.lower() in card_name.lower()]

        # Use the first matched bank name, or assign None if no match found
        corrected_bank_name = matched_bank_names[0] if matched_bank_names else None

        # Extract cashback info
        cashback_info, min_income = extract_cashback_info(requests.get(full_card_link).text)

        # Extract annual fee info
        annual_fee_info = extract_annual_fee_info(requests.get(full_card_link).text)

        # Extract annual fee simple info
        annual_fee_simple = extract_annual_fee_simple_info(requests.get(full_card_link).text)

        # Create rows for each cashback info
        if cashback_info:
            for info in cashback_info:
                rows.append({
                    'Bank Name': corrected_bank_name,
                    'Card Name': card_name,
                    'Min Income': min_income,
                    'Cashback': cashback,  # Add Cashback column
                    'Cashback Category': info['Cashback Category'],
                    'Cashback Rate': info['Cashback Rate'],
                    'Monthly Cap': info['Monthly Cap'],
                    'Spend': info['Spend'],
                    'Annual Fee': '\n'.join(annual_fee_info),  # Join annual fee info with newline
                    'Annual Fee Simple': annual_fee_simple,  # Add Annual Fee Simple column
                    'Card Link': full_card_link
                })
        else:
            # If no cashback info, create a row with null values
            rows.append({
                'Bank Name': corrected_bank_name,
                'Card Name': card_name,
                'Min Income': min_income,
                'Cashback': cashback,  # Add Cashback column
                'Cashback Category': None,
                'Cashback Rate': None,
                'Monthly Cap': None,
                'Spend': None,
                'Annual Fee': '\n'.join(annual_fee_info),  # Join annual fee info with newline
                'Annual Fee Simple': annual_fee_simple,  # Add Annual Fee Simple column
                'Card Link': full_card_link
            })

    # Create a DataFrame
    df = pd.DataFrame(rows)

    # Reorder columns (move 'Card Link' to the last position)
    df = df[['Bank Name', 'Card Name', 'Min Income', 'Cashback', 'Cashback Category', 'Cashback Rate', 'Monthly Cap',
             'Spend', 'Annual Fee', 'Annual Fee Simple', 'Card Link']]

    # Export DataFrame to Excel
    excel_filename = "credit_card_data.xlsx"
    df.to_excel(excel_filename, index=False)

    print(f"Data has been exported to {excel_filename}")

else:
    print(f"Failed to fetch the page. Status Code: {response.status_code}")
