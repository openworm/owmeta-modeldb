import re
from shutil import copyfileobj

from bs4 import BeautifulSoup
from owmeta_core.datasource import DataSource, Informational
from owmeta_core.dataobject import (DatatypeProperty,
                                    PythonClassDescription,
                                    PythonModule,
                                    ClassResolutionFailed,
                                    DATAOBJECT_PROPERTY_NAME_PREFIX)
from owmeta_core import BASE_CONTEXT
from owmeta_core.context import ClassContext
from owmeta_core.dataobject_property import DatatypeProperty as DODatatypeProperty
import requests
from rdflib.namespace import Namespace


BASE_SCHEMA_URL = 'http://schema.openworm.org/2020/07/sci/modeldb'
BASE_DATA_URL = 'http://data.openworm.org/sci/modeldb'


CONTEXT = ClassContext(imported=(BASE_CONTEXT,),
                      ident=BASE_SCHEMA_URL,
                      base_namespace=BASE_SCHEMA_URL + '#')


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
    download_url = soup.find(id='downloadmodelzip')['href']
    data.append(dict(id='download_url', values=[download_url]))
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
    '''
    Creates a Property sub-class for properties defined on ModelDB pages. We don't define
    them statically to avoid the cost of managing additions of properties
    '''
    global GENERATED_PROPERTIES

    property_name = 'ModelDB_' + local_id
    prop_class = GENERATED_PROPERTIES.get(property_name)

    if not prop_class:
        declare_class_description = declare_class_description_generator(local_id, display_name)
        prop_class = type(property_name,
                (ModelDB, DODatatypeProperty,),
                dict(link_name=local_id,
                     label=display_name,
                     base_namespace=ModelDBDataSource.schema_namespace,
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


class ModelDB:
    base_namespace = Namespace(BASE_SCHEMA_URL + '/')
    base_data_namespace = Namespace(BASE_DATA_URL + '/')


class ModelDBDataSource(ModelDB, DataSource):
    '''
    A data source of a single ModelDB record
    '''

    class_context = CONTEXT
    accession_id = Informational(display_name='Accession ID',
            description='Accession ID within ModelDB',
            multiple=False)
    download_url = Informational(display_name='Download URL',
            description='URL for downloading',
            multiple=False)
    base_directory = Informational(display_name='Base Model Directory',
            Description='Base directory of the downloaded model archive')

    key_property = 'accession_id'

    def __getattr__(self, name):
        # Tries to load the property from the graph
        if name.startswith(DATAOBJECT_PROPERTY_NAME_PREFIX):
            # Skip attributes that we *really* shouldn't be able to resolve
            return super().__getattr__(name)
        cd_type = ModelDBPropertyClassDescription.contextualize(self.context).query
        try:
            pclass = cd_type(local_id=name).resolve_class()
            return self.attach_property(pclass)
        except ClassResolutionFailed:
            raise AttributeError(name)

    def download(self, dest, base_url='https://senselab.med.yale.edu', session=None):
        '''
        Download model files. Note that if the destination file already exists, it will be
        overwritten without warning if the operating system permits that.

        Parameters
        ----------
        dest : str
            Destination file for the download.
        base_url : str, optional
            Base URL for the download
        session : requests.session.Session, optional
            Session to use for the download. If not provided, a new session will be
            created
        '''
        if session is None:
            session = requests.Session()
        response = session.get(base_url + self.download_url(), stream=True)
        with open(dest, 'wb') as out:
            copyfileobj(response.raw, out)

    @classmethod
    def scrape_to_datasource(cls, accession, session=None, init_params=None):
        '''
        Scrape a ModelDB page into a `owmeta_core.datasource.DataSource`

        Parameters
        ----------
        accession : str or int
            Accession number or URL for the model
        session : requests.Session
            Session to use for getting the document. Optional.
        init_params : dict, optional
            Additional parameters to the DataSource created

        Returns
        -------
        ModelDBDataSource
            The datasource created from the indicated ModelDB page

        See Also
        --------
        `scrape` shares some parameters
        '''
        data = scrape(accession, session)

        if init_params is None:
            init_params = dict()

        res = cls(**init_params)

        for d in data:
            if d['id'] == 'accession_id':
                for v in d['values']:
                    res.accession_id(v)
                continue
            elif d['id'] == 'download_url':
                for v in d['values']:
                    res.download_url(v)
                continue
            prop_class = create_property_class(d['id'], d['display_name'])
            prop = res.attach_property(prop_class)
            for v in d['values']:
                prop(v)

        return res


class ModelDBPropertyClassDescription(ModelDB, PythonClassDescription):
    '''
    Description of a `ModelDBDataSource` property
    '''

    local_id = DatatypeProperty(__doc__='ID used on the page')
    display_name = DatatypeProperty(__doc__='Display name')

    key_properties = ('name', 'module', 'local_id')

    def resolve_class(self):
        local_id = self.local_id()
        if not local_id:
            raise ClassResolutionFailed('Missing local_id')

        display_name = self.display_name()
        if not display_name:
            raise ClassResolutionFailed('Missing display_name')
        return create_property_class(local_id, display_name)
