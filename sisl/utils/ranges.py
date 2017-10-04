from __future__ import print_function, division

import re
from functools import partial
from itertools import groupby

from numpy import zeros, ones, cumsum, take, int32

from sisl._help import _map as map

__all__ = ['strmap', 'strseq', 'lstranges', 'erange', 'list2range', 'fileindex']
__all__ += ['array_arange']


# Function to change a string to a range of integers
def strmap(func, s, sep='b'):
    """ Parse a string as though it was a slice and map all entries using ``func``.

    Examples
    --------
    >>> strmap('1')
    [func('1')]
    >>> strmap('1-2')
    [func('1-2')]
    >>> strmap('1-10[2-3]')
    [( func('1-10'), func('2-3'))]

    Parameters
    ----------
    func : function
       function to parse every match with
    s    : str
       the string that should be parsed
    sep  : {'b', 'c', '*', 's'}, optional
       separator used, ``'b'`` is square brackets, ``'c'``, curly braces, and ``'*'``/``'s'`` is the star
    """

    if sep == 'b':
        segment = re.compile(r'\[(.+)\]\[(.+)\]|(.+)\[(.+)\]|(.+)')
        sep1, sep2 = '[', ']'
    elif sep == '*' or sep == 's':
        segment = re.compile(r'\*(.+)\*\*(.+)\*|(.+)\*(.+)\*|(.+)')
        sep1, sep2 = '*', '*'
    elif sep == 'c':
        segment = re.compile(r'\{(.+)\}\{(.+)\}|(.+)\{(.+)\}|(.+)')
        sep1, sep2 = '{', '}'

    # Create list
    l = []

    commas = s.replace(' ', '').split(',')

    # Collect all the comma separated quantities that
    # may be selected by [..,..]
    i = 0
    while i < len(commas) - 1:
        if commas[i].count(sep1) == commas[i].count(sep2):
            i = i + 1
        else:
            # there must be more [ than ]
            commas[i] = commas[i] + "," + commas[i+1]
            del commas[i+1]

    # Check the last input...
    i = len(commas) - 1
    if commas[i].count(sep1) != commas[i].count(sep2):
        raise ValueError("Unbalanced string: not enough {} and {}".format(sep1, sep2))

    # Now we have a comma-separated list
    # with collected brackets.
    for seg in commas:

        # Split it in groups of reg-exps
        m = segment.findall(seg)[0]

        if len(m[0]) > 0:
            # this is: [..][..]
            rhs = strmap(func, m[1])
            for el in strmap(func, m[0]):
                l.append((el, rhs))

        elif len(m[2]) > 0:
            # this is: ..[..]
            l.append((strseq(func, m[2]), strmap(func, m[3])))

        elif len(m[4]) > 0:
            l.append(strseq(func, m[4]))

    return l


def strseq(cast, s):
    """ Accept a string and return the casted tuples of content based on ranges.

    Parameters
    ----------
    cast: function
       parser of the individual elements
    s: str
       string with content

    Examples
    --------
    >>> strmap(int, '3')
    3
    >>> strmap(int, '3-6')
    (3, 6)
    >>> strmap(int, '3:2:7')
    (3, 2, 7)
    >>> strmap(float, '3.2:6.3')
    (3.2, 6.3)
    """
    if ':' in s:
        return tuple(cast(ss) if len(ss.strip()) > 0 else None for ss in s.split(':'))
    elif '-' in s:
        return tuple(cast(ss) if len(ss.strip()) > 0 else None for ss in s.split('-'))
    return cast(s)


def erange(*args):
    """ Returns the range with both ends includede """
    if len(args) == 3:
        return range(args[0], args[2]+1, args[1])
    return range(args[0], args[1]+1)


def lstranges(lst, cast=erange):
    """ Convert a `strmap` list into expanded ranges """
    l = []
    # If an entry is a tuple, it means it is either
    # a range 0-1 == tuple(0, 1), or
    # a sub-range
    #   0[0-1], 0-1[0-1]
    if isinstance(lst, tuple):
        if len(lst) == 3:
            l.extend(cast(*lst))
        else:
            head = lstranges(lst[0], cast)
            bot = lstranges(lst[1], cast)
            if isinstance(head, list):
                for el in head:
                    l.append([el, bot])
            elif isinstance(bot, list):
                l.append([head, bot])
            else:
                l.extend(cast(head, bot))

    elif isinstance(lst, list):
        for lt in lst:
            ls = lstranges(lt, cast)
            if isinstance(ls, list):
                l.extend(ls)
            else:
                l.append(ls)
    else:
        return lst
    return l


def list2range(lst):
    """ Convert a list of elements into a string of ranges

    Examples
    --------
    >>> list2range([2, 4, 5, 6])
    2, 4-6
    >>> list2range([2, 4, 5, 6, 8, 9])
    2, 4-6, 8-9
    """
    lst = lst[:]
    lst.sort()
    # Create positions
    pos = [j - i for i, j in enumerate(lst)]
    t = 0
    rng = ''
    for _, els in groupby(pos):
        ln = len(list(els))
        el = lst[t]
        if t > 0:
            rng += ', '
        t += ln
        if ln == 1:
            rng += str(el)
        else:
            rng += '{}-{}'.format(el, el+ln-1)
    return rng


# Function to retrieve an optional index from the
# filename
#   file[0] returns:
#     file, 0
#   file returns:
#     file, None
#   file[0-1] returns
#     file, [0,1]
def fileindex(f, cast=int):
    """ Parses a filename string into the filename and the indices.

    This range can be formatted like this:
      file[1,2,3-6]
    in which case it will return:
      file, [1,2,3,4,5,6]

    Parameters
    ----------
    f : str
       filename to parse
    cast : function
       the function to cast the bracketed value
    """

    if '[' not in f:
        return f, None

    # Grab the filename
    f = f.split('[')
    fname = f.pop(0)
    # Re-join and remove the last ']'
    f = '['.join(f)
    if f[-1] == ']':
        f = f[:-1]
    ranges = strmap(cast, f)
    rng = lstranges(ranges)
    if len(rng) == 1:
        return fname, rng[0]
    return fname, rng


def array_arange(start, end=None, n=None, dtype=int32):
    """ Creates a single array from a sequence of `numpy.arange`

    Parameters
    ----------
    start : array_like
       a list of start elements for `numpy.arange`
    end : array_like
       a list of end elements (exclusive) for `numpy.arange`.
       This argument is not used if `n` is passed.
    n : array_like
       a list of counts of elements for `numpy.arange`.
       This is equivalent to ``end=start + n``.
    dtype : numpy.dtype
       the returned lists data-type

    Examples
    --------
    >>> array_arange([1, 5], [3, 6])
    [1, 2, 5]
    >>> array_arange([1, 6], [4, 9])
    [1, 2, 3, 6, 7, 8]
    >>> array_arange([1, 6], n=[2, 2])
    [1, 2, 6, 7]
    """
    _z = partial(zeros, dtype=dtype)
    _o = partial(ones, dtype=dtype)
    _c = partial(cumsum, dtype=dtype)

    # Tests show that the below code is faster than
    # implicit for-loops, or list-comprehensions
    # concatenate(map(..)
    # This below is much faster and does not require _any_
    # loops
    if n is None:
        # We really do need n to speed things up
        n = end - start
    # The below algorithm only works for non-zero n
    idx = n.nonzero()[0]

    # Grab corner case
    if len(idx) == 0:
        return _z(0)

    # Reduce size
    start = take(start, idx)
    n = take(n, idx)

    # Create array
    a = _o(n.sum())

    # set pointers such that we can
    # correct for final cumsum
    ptr = _c(n[:-1])
    a[0] = start[0]
    # Define start and correct for previous values
    a[ptr] = start[1:] - start[:-1] - n[:-1] + 1

    return _c(a)
