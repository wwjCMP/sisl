"""
====================================
Utility routines (:mod:`sisl.utils`)
====================================

.. module:: sisl.utils

Several utility functions are used throughout sisl.

Range routines
==============

.. autosummary::
   :toctree:

   array_arange - fast creation of sub-aranges
   strmap
   strseq
   lstranges
   erange
   list2str
   fileindex

Miscellaneous routines
======================

.. autosummary::
   :toctree:

   str_spec
   direction - abc/012 -> 012
   angle - radian to degree
   iter_shape
   math_eval

"""

from .cmd import *
from .misc import *
from .ranges import *

__all__ = [s for s in dir() if not s.startswith('_')]

#for rm in ['cmd', 'misc', 'ranges']:
#    __all__.remove(rm)
