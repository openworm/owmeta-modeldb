from owmeta_core.data import Data
from owmeta_core.context import Context
from owmeta_core.dataobject import PythonModule
from owmeta_core.dataobject_property import Property
from owmeta_modeldb import ModelDBPropertyClassDescription


def test_resolve_property_class_staged():
    cd = ModelDBPropertyClassDescription(
            local_id='test_property',
            display_name='Test Property')
    assert issubclass(cd.resolve_class(), Property)


def test_resolve_property_class_stored():
    conf = Data()
    conf.init()
    ctxid = 'http://example.org/ctx'
    ctx0 = Context(ctxid, conf=conf)
    modname = ModelDBPropertyClassDescription.__module__
    mod = ctx0(PythonModule)(name=modname)
    cd = ctx0(ModelDBPropertyClassDescription)(
            name='ModelDB_test_property',
            local_id='test_property',
            display_name='Test Property',
            module=mod)
    ctx0.save()

    ctx1 = Context(ctxid, conf=conf)
    ctx1.stored(ModelDBPropertyClassDescription)(ident=cd.identifier)
    assert issubclass(cd.resolve_class(), Property)
