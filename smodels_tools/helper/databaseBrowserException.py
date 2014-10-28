"""
.. module:: databaseException
   :synopsis: Exception for databaseBrowser.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Wolfgang Magerl <wolfgang.magerl@gmail.com>

"""
class DatabaseNotFoundException(Exception):
    pass

class InvalidExperimentException(Exception):
    pass

class InvalidRunRestrictionException(Exception):
    pass