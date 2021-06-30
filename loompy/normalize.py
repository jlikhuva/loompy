import numpy as np
import scipy.sparse as sparse
from typing import *
import html
import logging


def normalize_attr_strings(a: np.ndarray) -> np.ndarray:
	"""
	Take an np.ndarray of all kinds of string-like elements, and return an array of ascii (np.string_) objects
	"""
	if np.issubdtype(a.dtype, np.object_):
		# if np.all([type(x) is str for x in a]) or np.all([type(x) is np.str_ for x in a]) or np.all([type(x) is np.unicode_ for x in a]):
		if np.all([(type(x) is str or type(x) is np.str_ or type(x) is np.unicode_) for x in a]):
			return np.array([x.encode('ascii', 'xmlcharrefreplace') for x in a])
		elif np.all([type(x) is np.string_ for x in a]) or np.all([type(x) is np.bytes_ for x in a]):
			return a.astype("string_")
		else:
			logging.debug(f"Attribute contains mixed object types ({np.unique([str(type(x)) for x in a])}); casting all to string")
			return np.array([str(x) for x in a], dtype="string_")
	elif np.issubdtype(a.dtype, np.string_) or np.issubdtype(a.dtype, np.object_):
		return a
	elif np.issubdtype(a.dtype, np.str_) or np.issubdtype(a.dtype, np.unicode_):
		return np.array([x.encode('ascii', 'xmlcharrefreplace') for x in a])
	else:
		raise ValueError("String values must be object, ascii or unicode.")


def normalize_attr_array(a: Any) -> np.ndarray:
	"""
	Take all kinds of array-like inputs and normalize to a one-dimensional np.ndarray
	"""
	if type(a) is np.ndarray:
		return a
	elif type(a) is np.matrix:
		if a.shape[0] == 1:
			return np.array(a)[0, :]
		elif a.shape[1] == 1:
			return np.array(a)[:, 0]
		else:
			raise ValueError("Attribute values must be 1-dimensional.")
	elif type(a) is list or type(a) is tuple:
		return np.array(a)
	elif sparse.issparse(a):
		return normalize_attr_array(a.todense())
	else:
		raise ValueError("Argument must be a list, tuple, numpy matrix, numpy ndarray or sparse matrix.")


def normalize_attr_values(a: Any, use_object_strings: bool = False) -> np.ndarray:
	"""
	Take all kinds of input values and validate/normalize them.
	
	Args:
		a	List, tuple, np.matrix, np.ndarray or sparse matrix
			Elements can be strings, numbers or bools
	
	Returns
		a_normalized    An np.ndarray with elements conforming to one of the valid Loom attribute types
	
	Remarks:
		This method should be used to prepare the values to be stored in the HDF5 file. You should not
		return the values to the caller; for that, use materialize_attr_values()
	"""
	scalar = False
	if np.isscalar(a):
		a = np.array([a])
		scalar = True
	arr = normalize_attr_array(a)
	if np.issubdtype(arr.dtype, np.integer) or np.issubdtype(arr.dtype, np.floating):
		pass  # We allow all these types
	elif np.issubdtype(arr.dtype, np.character) or np.issubdtype(arr.dtype, np.object_):
		if use_object_strings:
			arr = np.array([str(elm) for elm in a], dtype=object)
		else:
			arr = normalize_attr_strings(arr)
	elif np.issubdtype(arr.dtype, np.bool_):
		arr = arr.astype('ubyte')
	if scalar:
		return arr[0]
	else:
		return arr


def materialize_attr_values(a: np.ndarray) -> np.ndarray:
	scalar = False
	if np.isscalar(a):
		scalar = True
		a = np.array([a])
	result: np.ndarray = None   # This second clause takes care of attributes stored as variable-length ascii, which can be generated by loomR or Seurat
	if np.issubdtype(a.dtype, np.string_) or np.issubdtype(a.dtype, np.object_):
		# First ensure that what we load is valid ascii (i.e. ignore anything outside 7-bit range)
		if hasattr(a, "decode"):  # This takes care of Loom files that store strings as UTF8, which comes in as str and doesn't have a decode method
			temp = np.array([x.decode('ascii', 'ignore') for x in a])
		else:
			temp = a
		# Then unescape XML entities and convert to unicode
		try:
			result = np.array([html.unescape(x) for x in temp.astype(str)], dtype=object)
		except:  # Dirty hack to handle UTF-8 non-break-space in scalar strings. TODO: Rewrite this whole method completely!
			if type(a[0]) == np.bytes_:
				result = [ a[0].replace(b'\xc2\xa0', b'') ]
	elif np.issubdtype(a.dtype, np.str_) or np.issubdtype(a.dtype, np.unicode_):
		result = np.array(a.astype(str), dtype=object)
	else:
		result = a
	if scalar:
		return result[0]
	else:
		return result
