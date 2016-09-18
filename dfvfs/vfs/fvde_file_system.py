# -*- coding: utf-8 -*-
"""The FVDE file system implementation."""

import pyfvde

from dfvfs.lib import fvde
from dfvfs.lib import definitions
from dfvfs.lib import errors
from dfvfs.path import fvde_path_spec
from dfvfs.resolver import resolver
from dfvfs.vfs import fvde_file_entry
from dfvfs.vfs import root_only_file_system


class FVDEFileSystem(root_only_file_system.RootOnlyFileSystem):
  """Class that implements a file system using FVDE."""

  TYPE_INDICATOR = definitions.TYPE_INDICATOR_FVDE

  def __init__(self, resolver_context):
    """Initializes a file system.

    Args:
      resolver_context (Context): resolver context.
    """
    super(FVDEFileSystem, self).__init__(resolver_context)
    self._fvde_volume = None
    self._file_object = None

  def _Close(self):
    """Closes the file system.

    Raises:
      IOError: if the close failed.
    """
    self._fvde_volume.close()
    self._fvde_volume = None

    self._file_object.close()
    self._file_object = None

  def _Open(self, path_spec, mode='rb'):
    """Opens the file system defined by path specification.

    Args:
      path_spec (PathSpec): path specification.
      mode (Optional[str]): file access mode. The default is 'rb'
          read-only binary.

    Raises:
      AccessError: if the access to open the file was denied.
      IOError: if the file system could not be opened.
      PathSpecError: if the path specification is incorrect.
      ValueError: if the path specification is invalid.
    """
    if not path_spec.HasParent():
      raise errors.PathSpecError(
          u'Unsupported path specification without parent.')

    resolver.Resolver.key_chain.ExtractCredentialsFromPathSpec(path_spec)

    fvde_volume = pyfvde.volume()
    file_object = resolver.Resolver.OpenFileObject(
        path_spec.parent, resolver_context=self._resolver_context)

    try:
      fvde.FVDEVolumeOpen(
          fvde_volume, path_spec, file_object, resolver.Resolver.key_chain)
    except:
      file_object.close()
      raise

    self._fvde_volume = fvde_volume
    self._file_object = file_object

  def GetFVDEVolume(self):
    """Retrieves the FVDE volume.

    Returns:
      pyfvde.volume: FVDE volume.
    """
    return self._fvde_volume

  def GetFileEntryByPathSpec(self, path_spec):
    """Retrieves a file entry for a path specification.

    Args:
      path_spec (PathSpec): path specification.

    Returns:
      FVDEFileEntry: file entry or None.
    """
    return fvde_file_entry.FVDEFileEntry(
        self._resolver_context, self, path_spec, is_root=True, is_virtual=True)

  def GetRootFileEntry(self):
    """Retrieves the root file entry.

    Returns:
      FVDEFileEntry: file entry or None.
    """
    path_spec = fvde_path_spec.FVDEPathSpec(parent=self._path_spec.parent)
    return self.GetFileEntryByPathSpec(path_spec)