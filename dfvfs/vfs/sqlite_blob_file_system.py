# -*- coding: utf-8 -*-
"""The SQLite blob file system implementation."""

from dfvfs.lib import definitions
from dfvfs.lib import errors
from dfvfs.path import sqlite_blob_path_spec
from dfvfs.resolver import resolver
from dfvfs.vfs import sqlite_blob_file_entry
from dfvfs.vfs import file_system


class SQLiteBlobFileSystem(file_system.FileSystem):
  """Class that implements a file system object using SQLite blob."""

  TYPE_INDICATOR = definitions.TYPE_INDICATOR_SQLITE_BLOB

  def __init__(self, resolver_context):
    """Initializes a file system object.

    Args:
      resolver_context: the resolver context (instance of resolver.Context).
    """
    super(SQLiteBlobFileSystem, self).__init__(resolver_context)
    self._file_object = None
    self._number_of_rows = None

  def _Close(self):
    """Closes the file system object.

    Raises:
      IOError: if the close failed.
    """
    self._file_object.close()
    self._file_object = None
    self._number_of_rows = None

  def _Open(self, path_spec, mode='rb'):
    """Opens the file system object defined by path specification.

    Args:
      path_spec: a path specification (instance of path.PathSpec).
      mode: optional file access mode. The default is 'rb' read-only binary.

    Raises:
      AccessError: if the access to open the file was denied.
      IOError: if the file system object could not be opened.
      PathSpecError: if the path specification is incorrect.
      ValueError: if the path specification is invalid.
    """
    if not path_spec.HasParent():
      raise errors.PathSpecError(
          u'Unsupported path specification without parent.')

    file_object = resolver.Resolver.OpenFileObject(
        path_spec.parent, resolver_context=self._resolver_context)

    self._file_object = file_object

  def FileEntryExistsByPathSpec(self, path_spec):
    """Determines if a file entry for a path specification exists.

    Args:
      path_spec: a path specification (instance of path.PathSpec).

    Returns:
      Boolean indicating if the file entry exists.
    """
    # All checks for correct path spec is done in SQLiteBlobFile.
    # Therefore, attempt to open the path specification and
    # check if errors occurred.
    try:
      file_object = resolver.Resolver.OpenFileObject(
          path_spec, resolver_context=self._resolver_context)
    except (errors.AccessError, errors.PathSpecError, IOError, ValueError):
      return False

    file_object.close()
    return True

  def GetFileEntryByPathSpec(self, path_spec):
    """Retrieves a file entry for a path specification.

    Args:
      path_spec: a path specification (instance of path.PathSpec).

    Returns:
      A file entry (instance of vfs.FileEntry) or None.
    """
    row_index = getattr(path_spec, u'row_index', None)
    row_condition = getattr(path_spec, u'row_condition', None)

    # If no row_index or row_condition is provided, return a directory.
    if row_index is None and row_condition is None:
      return sqlite_blob_file_entry.SQLiteBlobFileEntry(
          self._resolver_context, self, path_spec, is_root=True,
          is_virtual=True)
    else:
      return sqlite_blob_file_entry.SQLiteBlobFileEntry(
          self._resolver_context, self, path_spec)

  def GetRootFileEntry(self):
    """Retrieves the root file entry.

    Returns:
      A file entry (instance of vfs.FileEntry) or None.
    """
    path_spec = sqlite_blob_path_spec.SQLiteBlobPathSpec(
        table_name=self._path_spec.table_name,
        column_name=self._path_spec.column_name,
        parent=self._path_spec.parent)
    return self.GetFileEntryByPathSpec(path_spec)

  def GetNumberOfRows(self, path_spec):
    """Returns the number of rows the table has."""
    if self._number_of_rows is not None:
      return self._number_of_rows

    file_object = resolver.Resolver.OpenFileObject(
        path_spec, resolver_context=self._resolver_context)
    self._number_of_rows = file_object.GetNumberOfRows()
    file_object.close()
    return self._number_of_rows