from abc import ABCMeta, abstractmethod, abstractproperty
from pywps._compat import text_type, StringIO
import tempfile

class SOURCE_TYPE:
    MEMORY = 0
    FILE = 1
    STREAM = 2
    DATA = 3


class FormatBase(object):
    """Input/output format specification
    """
    def __init__(self, mimetype, schema=None, encoding=None, validator=None):
        self.mimetype = mimetype
        self.schema = schema
        self.encoding = encoding
        self.validator = validator


class DataTypeAbstract(object):
    """LiteralObject data_type abstract class
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def convert(self, value):
        return value


class DataValidatorAbstract(object):
    """LiteralObject validator
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(self, value):
        """Make sure, given value is ok according to LiteralInput definition
        """
        return True


class IOHandler(object):
    """Basic IO class. Provides functions, to accept input data in file,
    memory object and stream object and give them out in all three types

    >>> # setting up tempory directory for testing environment
    >>> import os
    >>> from io import RawIOBase
    >>> from io import FileIO
    >>> import types
    >>>
    >>> ioh_file = IOHandler(tempdir=tmp)
    >>> assert isinstance(ioh_file, IOHandler)
    >>>
    >>> # Create test file input
    >>> fileobj = open(os.path.join(tmp, 'myfile.txt'), 'w')
    >>> fileobj.write('ASDF ASFADSF ASF ASF ASDF ASFASF')
    >>> fileobj.close()
    >>>
    >>> # testing file object on input
    >>> ioh_file.file = fileobj.name
    >>> assert ioh_file.source_type == SOURCE_TYPE.FILE
    >>> file = ioh_file.file
    >>> stream = ioh_file.stream
    >>>
    >>> assert file == fileobj.name
    >>> assert isinstance(stream, RawIOBase)
    >>> # skipped assert isinstance(ioh_file.memory_object, POSH)
    >>>
    >>> # testing stream object on input
    >>> ioh_stream = IOHandler(tempdir=tmp)
    >>> assert ioh_stream.tempdir == tmp
    >>> ioh_stream.stream = FileIO(fileobj.name,'r')
    >>> assert ioh_stream.source_type == SOURCE_TYPE.STREAM
    >>> file = ioh_stream.file
    >>> stream = ioh_stream.stream
    >>>
    >>> assert open(file).read() == ioh_file.stream.read()
    >>> assert isinstance(stream, RawIOBase)
    >>> # skipped assert isinstance(ioh_stream.memory_object, POSH)
    >>>
    >>> # testing in memory object object on input
    >>> # skipped ioh_mo = IOHandler(tempdir=tmp)
    >>> # skipped ioh_mo.memory_object = POSH
    >>> # skipped assert ioh_mo.source_type == SOURCE_TYPE.MEMORY
    >>> # skipped file = ioh_mo.file
    >>> # skipped stream = ioh_mo.stream
    >>> # skipped posh = ioh_mo.memory_object
    >>> #
    >>> # skipped assert open(file).read() == ioh_file.stream.read()
    >>> # skipped assert isinstance(ioh_mo.stream, RawIOBase)
    >>> # skipped assert isinstance(ioh_mo.memory_object, POSH)
    """

    def __init__(self, tempdir=None):
        self.source_type = None
        self.source = None
        self._tempfile = None
        self.tempdir = tempdir

    def set_file(self, filename):
        """Set source as file name"""
        self.source_type = SOURCE_TYPE.FILE
        self.source = filename

    def set_memory_object(self, memory_object):
        """Set source as in memory object"""
        self.source_type = SOURCE_TYPE.MEMORY

    def set_stream(self, stream):
        """Set source as stream object"""
        self.source_type = SOURCE_TYPE.STREAM
        self.source = stream

    def set_data(self, data):
        """Set source as simple datatype e.g. string, number"""
        self.source_type = SOURCE_TYPE.DATA
        self.source = data

    def get_file(self):
        """Get source as file name"""
        if self.source_type == SOURCE_TYPE.FILE:
            return self.source

        elif self.source_type == SOURCE_TYPE.STREAM or\
             self.source_type == SOURCE_TYPE.DATA:

            if self._tempfile:
                return self._tempfile
            else:
                (opening, stream_file_name) = tempfile.mkstemp(dir=self.tempdir)
                stream_file = open(stream_file_name, 'w')

                if self.source_type == SOURCE_TYPE.STREAM:
                    stream_file.write(self.source.read())
                else:
                    stream_file.write(self.source)

                stream_file.close()
                self._tempfile = str(stream_file_name)
                return self._tempfile

    def get_memory_object(self):
        """Get source as memory object"""
        raise Exception("setmemory_object not implemented, Soeren promissed to implement at WPS Workshop on 23rd of January 2014")

    def get_stream(self):
        """Get source as stream object"""
        if self.source_type == SOURCE_TYPE.FILE:
            from io import FileIO
            return FileIO(self.source, mode='r', closefd=True)
        elif self.source_type == SOURCE_TYPE.STREAM:
            return self.source
        elif self.source_type == SOURCE_TYPE.DATA:
            return StringIO(text_type(self.source))

    def get_data(self):
        """Get source as simple data object"""
        if self.source_type == SOURCE_TYPE.FILE:
            file_handler = open(self.source, mode='r')
            content = file_handler.read()
            file_handler.close()
            return content
        elif self.source_type == SOURCE_TYPE.STREAM:
            return self.source.read()
        elif self.source_type == SOURCE_TYPE.DATA:
            return self.source

    # Properties
    file = property(fget=get_file, fset=set_file)
    memory_object = property(fget=get_memory_object, fset=set_memory_object)
    stream = property(fget=get_stream, fset=set_stream)
    data = property(fget=get_data, fset=set_data)


class SimpleHandler(IOHandler):
    """Data handler for Literal In- and Outputs

    >>> class Int_type(object):
    ...     @staticmethod
    ...     def convert(value): return int(value)
    >>>
    >>> class MyValidator(object):
    ...     @staticmethod
    ...     def validate(inpt): return 0 < inpt.data < 3
    >>>
    >>> inpt = SimpleHandler(data_type = Int_type)
    >>> inpt.validator = MyValidator
    >>>
    >>> inpt.data = 1
    >>> inpt.validator.validate(inpt)
    True
    >>> inpt.data = 5
    >>> inpt.validator.validate(inpt)
    False
    """

    def __init__(self, tempdir=None, data_type=None):
        IOHandler.__init__(self, tempdir)
        self.data_type = data_type
        self._validator = None

    def set_data(self, data):
        """Set data value. input data are converted into target format
        """
        if self.data_type:
            data = self.data_type.convert(data)
        IOHandler.set_data(self, data)

    @property
    def validator(self):
        return self._validator

    @validator.setter
    def validator(self, validator):
        self._validator = validator


class BasicLiteralInput(SimpleHandler):
    """LiteralInput input abstract class
    """

    def __init__(self, tempdir=None):
        SimpleHandler.__init__(self, tempdir=None)


class BasicLiteralOutput(SimpleHandler):
    """Basic LiteralOutput class
    """

    def __init__(self, tempdir=None):
        SimpleHandler.__init__(self, tempdir=None)
        self._storage = None

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage


class BasicBBoxInput(SimpleHandler):
    """Basic Bounding box input abstract class
    """

    def __init__(self, tempdir=None):
        SimpleHandler.__init__(self, tempdir=None)


class BasicBBoxOutput(SimpleHandler):
    """Basic BoundingBox output class
    """

    def __init__(self, tempdir=None):
        SimpleHandler.__init__(self, tempdir=None)
        self._storage = None

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage


class ComplexInput(IOHandler):
    """Complex input abstract class

    >>> ci = ComplexInput()
    >>> ci.validator = 1
    >>> ci.validator
    1
    """

    def __init__(self, tempdir=None, data_format=None):
        IOHandler.__init__(self, tempdir)

        self.data_format = data_format


class ComplexOutput(IOHandler):
    """Complex output abstract class

    >>> # temporary configuration
    >>> import ConfigParser
    >>> from pywps.storage import *
    >>> config = ConfigParser.RawConfigParser()
    >>> config.add_section('FileStorage')
    >>> config.set('FileStorage', 'target', './')
    >>> config.add_section('server')
    >>> config.set('server', 'outputurl', 'http://foo/bar/filestorage')
    >>>
    >>> # create temporary file
    >>> tiff_file = open('file.tiff', 'w')
    >>> tiff_file.write("AA")
    >>> tiff_file.close()
    >>>
    >>> co = ComplexOutput()
    >>> co.set_file('file.tiff')
    >>> fs = FileStorage(config)
    >>> co.storage = fs
    >>>
    >>> url = co.get_url() # get url, data are stored
    >>>
    >>> co.get_stream().read() # get data - nothing is stored
    'AA'
    """

    def __init__(self, tempdir=None, data_format=None):
        IOHandler.__init__(self, tempdir)

        self.data_format = data_format
        self._storage = None

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage

    def get_url(self):
        """Return URL pointing to data
        """
        (outtype, storage, url) = self.storage.store(self)
        return url


if __name__ == "__main__":
    import doctest
    import os
    from contextlib import contextmanager
    from path import path
    @contextmanager
    def temp_dir():
        tmp = path(tempfile.mkdtemp())
        try:
            yield tmp
        finally:
            tmp.rmtree()

    with temp_dir() as tmp:
        os.chdir(tmp)
        doctest.testmod()
