import re

import requests
from bs4 import BeautifulSoup
from owmeta_core.datasource import DataSource
from owmeta_core.dataobject import (DatatypeProperty,
                                    PythonClassDescription,
                                    PythonModule,
                                    ClassResolutionFailed)
from owmeta_core.dataobject_property import DatatypeProperty as DODatatypeProperty


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
    Scrape data from an HTML document of a modeldb page

    Parameters
    ----------
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
    data.append(dict(id='accession_id',
        display_name='Accession ID',
        values=[int(modinfo.find(id='modelid').text)]))
    data.append(dict(id='modelname',
        values=[soup.find(id='modelname').text],
        display_name='Model Name'))
    descr_ref_row = modinfo.find_all('tr', recursive=False, limit=2)[1]
    description = descr_ref_row.br.previous_sibling.strip()
    data.append(dict(id='description', values=[description], display_name='Description'))
    for row in rows:
        field = dict()
        tds = row.find_all('td')
        field['display_name'] = tds[0].text.strip().rstrip(':')
        field['id'] = tds[1]['id']
        value_anchors = tds[1].find_all('a')
        if value_anchors:
            field['values'] = [x.text.rstrip(';') for x in value_anchors]
        else:
            text_value = tds[1].text
            if text_value:
                field['values'] = [text_value]
            else:
                continue
        data.append(field)
    return data


GENERATED_PROPERTIES = dict()


def create_property_class(local_id, display_name):
    global GENERATED_PROPERTIES

    property_name = 'ModelDB_' + local_id
    prop_class = GENERATED_PROPERTIES.get(property_name)

    if not prop_class:
        link_name = local_id
        declare_class_description = declare_class_description_generator(local_id, display_name)
        prop_class = type(property_name,
                (DODatatypeProperty,),
                dict(link_name=link_name,
                     label=display_name,
                     declare_class_description=declare_class_description))
        GENERATED_PROPERTIES[property_name] = prop_class

    return prop_class


def declare_class_description_generator(local_id, display_name):
    def declare_class_description(self):
        cd = ModelDBPropertyClassDescription.contextualize(self.context)()

        mo = PythonModule.contextualize(self.context)()
        mo.name(self.__module__)

        cd.module(mo)
        cd.name(self.__name__)
        cd.local_id(local_id)
        cd.display_name(display_name)

        return cd
    return declare_class_description


class ModelDBPropertyClassDescription(PythonClassDescription):
    local_id = DatatypeProperty(__doc__='ID used on the page')
    display_name = DatatypeProperty(__doc__='Display name')

    key_properties = ['name', 'module', 'local_id']

    def resolve_class(self):
        local_id = self.local_id()
        if not local_id:
            raise ClassResolutionFailed('Missing local_id')

        display_name = self.display_name()
        if not display_name:
            raise ClassResolutionFailed('Missing display_name')
        return create_property_class(local_id, display_name)


def scrape_to_datasource(accession, session):
    '''
    Scrape a ModelDB page into a `owmeta_core.datasource.DataSource`

    See Also
    --------
    `scrape` - parameters are the same
    '''
    data = scrape(accession)
    res = ModelDBDataSource()
    for d in data:
        if d['id'] == 'accession_id':
            for v in d['values']:
                res.accession_id(v)
            continue
        prop_class = create_property_class(d['id'], d['display_name'])
        prop = res.attach_property(prop_class)
        for v in d['values']:
            prop(v)

    return res


class ModelDBDataSource(DataSource):
    '''
    A data source of a single ModelDB record
    '''
    accession_id = DatatypeProperty(__doc__='Accession ID within ModelDB',
            label='Accession ID')
