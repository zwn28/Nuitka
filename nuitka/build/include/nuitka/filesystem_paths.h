//     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
//
#ifndef __NUITKA_FILESYSTEM_PATH_OPS_H__
#define __NUITKA_FILESYSTEM_PATH_OPS_H__

// Have a type for filename type different on Linux and Win32.
#if defined(_WIN32)
#define filename_char_t wchar_t
#define FILENAME_EMPTY_STR L""
#define FILENAME_SEP_STR L"\\"
#define FILENAME_SEP_CHAR L'\\'
#define FILENAME_FORMAT_STR "%ls"
#define appendStringSafeFilename appendWStringSafeW
#define appendCharSafeFilename appendWCharSafeW
#define FILENAME_TMP_STR L".tmp"
#define FILENAME_AWAY_STR L".away"
#define expandTemplatePathFilename expandTemplatePathW
#else
#define filename_char_t char
#define FILENAME_EMPTY_STR ""
#define FILENAME_SEP_STR "/"
#define FILENAME_SEP_CHAR '/'
#define FILENAME_FORMAT_STR "%s"
#define appendStringSafeFilename appendStringSafe
#define appendCharSafeFilename appendCharSafe
#define FILENAME_TMP_STR ".tmp"
#define FILENAME_AWAY_STR ".away"
#define expandTemplatePathFilename expandTemplatePath
#endif

#if defined(_WIN32)
#include <windows.h>
#endif

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <wchar.h>

// Have a type for file type different on Linux and Win32.
#if defined(_WIN32)
#define FILE_HANDLE HANDLE
#define FILE_HANDLE_NULL INVALID_HANDLE_VALUE
#else
#define FILE_HANDLE FILE *
#define FILE_HANDLE_NULL NULL
#endif

// Defined by Python headers, for onefile we do it ourselves.
#ifndef MAXPATHLEN
#define MAXPATHLEN 4096
#endif

// Get path of the running binary.
extern filename_char_t *getBinaryPath(void);

extern FILE_HANDLE openFileForReading(filename_char_t const *filename);
extern FILE_HANDLE createFileForWriting(filename_char_t const *filename);
extern int64_t getFileSize(FILE_HANDLE file_handle);
extern bool readFileChunk(FILE_HANDLE file_handle, void *buffer, size_t size);
extern bool writeFileChunk(FILE_HANDLE file_handle, void *buffer, size_t size);
extern bool closeFile(FILE_HANDLE target_file);

extern int getFileMode(filename_char_t const *filename);
extern bool copyFile(filename_char_t const *source, filename_char_t const *dest, int mode);
extern bool deleteFile(filename_char_t const *filename);
extern bool renameFile(filename_char_t const *source, filename_char_t const *dest);

#endif