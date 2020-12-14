import re

import requests
from bs4 import BeautifulSoup


def scrape(accession, session=None):
    '''
    Scrape data from a ModelDB page

    Parameters
    ----------
    accession : str or int
        Accession number or URL for the model
    session : requests.Session
        Session to use for getting the document. Optional.
    '''
    if session is None:
        session = requests.Session()
    url = None
    if isinstance(accession, int):
        url = f'https://senselab.med.yale.edu/ModelDB/showmodel.cshtml?model={accession}'
    elif isinstance(accession, str):
        url = accession
    else:
        raise TypeError('Excepted an accession ID (an int) or a URL (a str)')
    resp = session.get(url)
    return scrape_file(resp.text)


def scrape_file(html_data):
    '''
    File object with HTML from a modeldb page

    html_data : object
        An object containing a modeldb page's data which is acceptable to
        `~bs4.BeautifulSoup` such as a string or file object
    '''
    soup = BeautifulSoup(html_data, 'html.parser')
    data = []
    modinfo = soup.find(id='tabs-1').table
    rows = (modinfo
            .find(text=re.compile('Model Information'))
            .find_next('table')
            .find_all('tr'))
    data.append(dict(id='modelname',
        values=[soup.find(id='modelname').text],
        display_name='Model Name'))
    descr_ref_row = modinfo.find_all('tr', recursive=False, limit=2)[1]
    description = descr_ref_row.br.previous_sibling.strip()
    data.append(dict(id='description', values=[description], display_name='Description'))
    for row in rows:
        record = dict()
        tds = row.find_all('td')
        record['display_name'] = tds[0].text.strip().rstrip(':')
        record['id'] = tds[1]['id']
        value_anchors = tds[1].find_all('a')
        if value_anchors:
            record['values'] = [x.text.rstrip(';') for x in value_anchors]
        else:
            text_value = tds[1].text
            if text_value:
                record['values'] = [text_value]
            else:
                continue
        data.append(record)
    return data
