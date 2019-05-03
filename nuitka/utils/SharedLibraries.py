#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" This module deals with finding and information about shared libraries.

"""

import array
import os
from sys import getfilesystemencoding

from nuitka.__past__ import unicode  # pylint: disable=I0021,redefined-builtin
from nuitka.PythonVersions import python_version
from nuitka.utils.WindowsResources import (
    RT_MANIFEST,
    deleteWindowsResources,
    getResourcesFromDLL,
)

from .Utils import isAlpineLinux


def localDLLFromFilesystem(name, paths):
    for path in paths:
        for root, _dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)


def locateDLL(dll_name):
    import ctypes.util

    dll_name = ctypes.util.find_library(dll_name)

    if dll_name is None:
        return None

    if os.path.sep in dll_name:
        # Use this from ctypes instead of rolling our own.
        # pylint: disable=protected-access

        so_name = ctypes.util._get_soname(dll_name)

        if so_name is not None:
            return os.path.join(os.path.dirname(dll_name), so_name)
        else:
            return dll_name

    if isAlpineLinux():
        return localDLLFromFilesystem(
            name=dll_name, paths=["/lib", "/usr/lib", "/usr/local/lib"]
        )

    import subprocess

    process = subprocess.Popen(
        args=["/sbin/ldconfig", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, _stderr = process.communicate()

    dll_map = {}

    for line in stdout.splitlines()[1:]:
        assert line.count(b"=>") == 1, line
        left, right = line.strip().split(b" => ")
        assert b" (" in left, line
        left = left[: left.rfind(b" (")]

        if python_version >= 300:
            left = left.decode(getfilesystemencoding())
            right = right.decode(getfilesystemencoding())

        if left not in dll_map:
            dll_map[left] = right

    return dll_map[dll_name]


def getSxsFromDLL(filename):
    """ List the SxS manifests of a Windows DLL.

    Args:
        filename: Filename of DLL to investigate

    Returns:
        List of resource names that are manifests.

    """

    return getResourcesFromDLL(filename, RT_MANIFEST)


def removeSxsFromDLL(filename):
    """ Remove the Windows DLL SxS manifest.

    Args:
        filename: Filename to remove SxS manifests from
    """
    # There may be more files that need this treatment, these are from scans
    # with the "find_sxs_modules" tool.
    if os.path.normcase(os.path.basename(filename)) not in (
        "sip.pyd",
        "win32ui.pyd",
        "winxpgui.pyd",
    ):
        return

    res_names = getSxsFromDLL(filename)

    if res_names:
        deleteWindowsResources(filename, RT_MANIFEST, res_names)


def getWindowsDLLVersion(filename):
    """ Return DLL version information from a file.

        If not present, it will be (0, 0, 0, 0), otherwise it will be
        a tuple of 4 numbers.
    """
    # Get size needed for buffer (0 if no info)
    import ctypes.wintypes

    if type(filename) is unicode:
        GetFileVersionInfoSizeW = ctypes.windll.version.GetFileVersionInfoSizeW
        GetFileVersionInfoSizeW.argtypes = [
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.LPDWORD,  # @UndefinedVariable
        ]
        GetFileVersionInfoSizeW.restype = ctypes.wintypes.HANDLE
        size = GetFileVersionInfoSizeW(filename, None)
    else:
        size = ctypes.windll.version.GetFileVersionInfoSizeA(filename, None)

    if not size:
        return (0, 0, 0, 0)

    # Create buffer
    res = ctypes.create_string_buffer(size)
    # Load file informations into buffer res

    if type(filename) is unicode:
        # Python3 needs our help here.
        GetFileVersionInfo = ctypes.windll.version.GetFileVersionInfoW
        GetFileVersionInfo.argtypes = [
            ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.LPVOID,
        ]
        GetFileVersionInfo.restype = ctypes.wintypes.BOOL

    else:
        # Python2 just works.
        GetFileVersionInfo = ctypes.windll.version.GetFileVersionInfoA

    success = GetFileVersionInfo(filename, 0, size, res)
    # This cannot really fail anymore.
    assert success

    r = ctypes.wintypes.UINT()
    l = ctypes.wintypes.UINT()

    # Look for codepages
    VerQueryValueA = ctypes.windll.version.VerQueryValueA

    # This doesn't exist yet for Python2
    PUINT = ctypes.POINTER(ctypes.wintypes.UINT)

    VerQueryValueA.argtypes = [
        ctypes.wintypes.LPCVOID,
        ctypes.wintypes.LPCSTR,
        PUINT,
        PUINT,
    ]
    VerQueryValueA.restype = ctypes.wintypes.BOOL

    VerQueryValueA(res, br"\VarFileInfo\Translation", r, l)

    if not l.value:
        return (0, 0, 0, 0)

    codepages = array.array("H", ctypes.string_at(r.value, l.value))
    codepage = tuple(codepages[:2].tolist())

    # Extract information
    VerQueryValueA(res, br"\StringFileInfo\%04x%04x\FileVersion" % codepage, r, l)

    data = ctypes.string_at(r.value, l.value)[4 * 2 :]

    import struct

    data = struct.unpack("HHHH", data[: 4 * 2])

    return data[1], data[0], data[3], data[2]
