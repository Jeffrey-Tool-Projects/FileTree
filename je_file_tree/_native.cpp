// Native folder reading for the Windows scanner: list one folder and read every entry's metadata
// without holding the interpreter lock, so the scanner's worker threads run in parallel.
//
// Why it exists (measured 2026-11-14, 80,000 small files, warm cache, 8 logical processors): the
// Python scanner took 3.3 s whether it used 1, 2, 4 or 8 threads, because each entry costs an
// os.lstat call plus Python work under the interpreter lock; a bare os.scandir walk took 0.67 s.
//
// What it promises:
//   * The snapshot bytes are exactly what snapshot.pack_snapshot(os.lstat(path)) gives. Later
//     operations compare a fresh os.lstat with the recorded snapshot, so a difference would make
//     them refuse every entry. core/native_scan.py checks this against os.lstat before use and
//     turns the module off when it does not hold.
//   * It only reads. No file is opened for data, written, renamed or removed.
//   * Anything unusual (a link or other reparse point, a device, a failed query, a time outside
//     the plain range) is returned as "ask Python" and handled by the existing os.lstat code.
//
// Built against the stable ABI (Python 3.11+): one binary serves every later version.

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#ifndef _WIN32
#error "je_file_tree._native is built on Windows only; other systems use the Python scanner."
#endif

#include <windows.h>

#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

namespace {

constexpr int KIND_FILE = 0;
constexpr int KIND_FOLDER = 1;
constexpr int KIND_ASK_PYTHON = 2;

constexpr int QUERY_BY_NAME = 1;    // GetFileInformationByName (Windows 11 24H2 and later)
constexpr int QUERY_BY_HANDLE = 2;  // open the entry itself and ask the handle

constexpr std::uint32_t MODE_FOLDER = 0040000;
constexpr std::uint32_t MODE_FILE = 0100000;
constexpr std::int64_t TICKS_PER_SECOND = 10000000;
constexpr std::int64_t SECONDS_1601_TO_1970 = 11644473600LL;
// Nanoseconds since 1970 must fit 64 bits (years 1678 to 2262); times outside go to Python.
constexpr std::int64_t SMALLEST_TICKS = (SECONDS_1601_TO_1970 - 9223372035LL) * TICKS_PER_SECOND;
constexpr std::int64_t LARGEST_TICKS = (SECONDS_1601_TO_1970 + 9223372035LL) * TICKS_PER_SECOND;

constexpr std::size_t SNAPSHOT_SIZE = 76;  // "<Q16sq16s16sIII" of core/snapshot.py
constexpr std::size_t TIMES_SIZE = 16;     // "<dd": access and birth time of a regular file

struct StatBasic {  // FILE_STAT_BASIC_INFORMATION
    LARGE_INTEGER FileId;
    LARGE_INTEGER CreationTime;
    LARGE_INTEGER LastAccessTime;
    LARGE_INTEGER LastWriteTime;
    LARGE_INTEGER ChangeTime;
    LARGE_INTEGER AllocationSize;
    LARGE_INTEGER EndOfFile;
    ULONG FileAttributes;
    ULONG ReparseTag;
    ULONG NumberOfLinks;
    ULONG DeviceType;
    ULONG DeviceCharacteristics;
    ULONG Reserved;
    LARGE_INTEGER VolumeSerialNumber;
    unsigned char FileId128[16];
};

constexpr int STAT_BASIC_BY_NAME = 3;  // FileStatBasicByNameInfo
typedef BOOL(WINAPI* ByNameQuery)(PCWSTR, int, PVOID, ULONG);

ByNameQuery by_name_query() {
    static ByNameQuery query = nullptr;
    static bool looked = false;
    if (!looked) {  // called first with the interpreter lock held (module start)
        HMODULE library = LoadLibraryExW(L"api-ms-win-core-file-l2-1-4.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
        if (library != nullptr) {
            query = reinterpret_cast<ByNameQuery>(GetProcAddress(library, "GetFileInformationByName"));
        }
        looked = true;
    }
    return query;
}

bool is_disk(ULONG device) {
    // The device types for which os.lstat reports a file or folder rather than a character device.
    return device == FILE_DEVICE_DISK || device == FILE_DEVICE_VIRTUAL_DISK || device == FILE_DEVICE_NETWORK_FILE_SYSTEM
        || device == FILE_DEVICE_CD_ROM || device == FILE_DEVICE_CD_ROM_FILE_SYSTEM || device == FILE_DEVICE_DISK_FILE_SYSTEM
        || device == FILE_DEVICE_DFS;
}

bool query_by_handle(const wchar_t* path, StatBasic& out) {
    HANDLE handle = CreateFileW(path, FILE_READ_ATTRIBUTES, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                nullptr, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
                                nullptr);
    if (handle == INVALID_HANDLE_VALUE) {
        return false;
    }
    BY_HANDLE_FILE_INFORMATION plain = {};
    FILE_BASIC_INFO basic = {};
    FILE_ID_INFO identity = {};
    bool known = GetFileType(handle) == FILE_TYPE_DISK
        && GetFileInformationByHandle(handle, &plain)
        && GetFileInformationByHandleEx(handle, FileBasicInfo, &basic, sizeof(basic))
        && GetFileInformationByHandleEx(handle, FileIdInfo, &identity, sizeof(identity));
    CloseHandle(handle);
    if (!known) {
        return false;
    }
    std::memset(&out, 0, sizeof(out));
    out.CreationTime = basic.CreationTime;
    out.LastAccessTime = basic.LastAccessTime;
    out.LastWriteTime = basic.LastWriteTime;
    out.ChangeTime = basic.ChangeTime;
    out.EndOfFile.HighPart = static_cast<LONG>(plain.nFileSizeHigh);
    out.EndOfFile.LowPart = plain.nFileSizeLow;
    out.FileAttributes = plain.dwFileAttributes;
    out.NumberOfLinks = plain.nNumberOfLinks;
    out.DeviceType = FILE_DEVICE_DISK;
    out.VolumeSerialNumber.QuadPart = static_cast<LONGLONG>(identity.VolumeSerialNumber);
    std::memcpy(out.FileId128, identity.FileId.Identifier, sizeof(out.FileId128));
    return true;
}

bool query(const wchar_t* path, int how, StatBasic& out) {
    if (how == QUERY_BY_NAME) {
        ByNameQuery by_name = by_name_query();
        return by_name != nullptr && by_name(path, STAT_BASIC_BY_NAME, &out, sizeof(out));
    }
    return query_by_handle(path, out);
}

struct Entry {
    std::wstring name;
    int kind = KIND_ASK_PYTHON;
    std::int64_t size = 0;
    double modified = 0.0;
    std::uint32_t attributes = 0;
    unsigned char snapshot[SNAPSHOT_SIZE + TIMES_SIZE];
    std::size_t snapshot_size = 0;
};

bool plain_ticks(std::int64_t ticks) {
    return ticks >= SMALLEST_TICKS && ticks <= LARGEST_TICKS;
}

std::int64_t nanoseconds(std::int64_t ticks) {
    return (ticks / TICKS_PER_SECOND - SECONDS_1601_TO_1970) * 1000000000LL + (ticks % TICKS_PER_SECOND) * 100;
}

double seconds(std::int64_t ticks) {  // the sum os.stat_result makes for st_mtime
    return static_cast<double>(ticks / TICKS_PER_SECOND - SECONDS_1601_TO_1970)
        + 1e-9 * static_cast<double>((ticks % TICKS_PER_SECOND) * 100);
}

template <typename Value>
void put(unsigned char*& at, Value value) {
    std::memcpy(at, &value, sizeof(value));  // x86-64 and ARM64 Windows are little-endian
    at += sizeof(value);
}

void put_wide(unsigned char*& at, std::int64_t value) {  // a signed 128-bit little-endian integer
    put(at, value);
    put(at, static_cast<std::int64_t>(value < 0 ? -1 : 0));
}

// Fill ``entry`` from ``info``; false leaves it as "ask Python".
bool describe(const StatBasic& info, bool file_times, bool change_time, Entry& entry) {
    std::int64_t written = info.LastWriteTime.QuadPart;
    std::int64_t changed = change_time ? info.ChangeTime.QuadPart : info.CreationTime.QuadPart;
    if ((info.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0 || info.ReparseTag != 0 || !is_disk(info.DeviceType)
        || !plain_ticks(written) || !plain_ticks(changed) || info.EndOfFile.QuadPart < 0) {
        return false;
    }
    bool folder = (info.FileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0;
    unsigned char* at = entry.snapshot;
    put(at, static_cast<std::uint64_t>(info.VolumeSerialNumber.QuadPart));
    std::memcpy(at, info.FileId128, 16);
    at += 16;
    put(at, static_cast<std::int64_t>(info.EndOfFile.QuadPart));
    put_wide(at, nanoseconds(written));
    put_wide(at, nanoseconds(changed));
    put(at, folder ? MODE_FOLDER : MODE_FILE);
    put(at, static_cast<std::uint32_t>(info.FileAttributes));
    put(at, static_cast<std::uint32_t>(info.NumberOfLinks));
    if (file_times && !folder) {
        if (!plain_ticks(info.LastAccessTime.QuadPart) || !plain_ticks(info.CreationTime.QuadPart)) {
            return false;
        }
        put(at, seconds(info.LastAccessTime.QuadPart));
        put(at, seconds(info.CreationTime.QuadPart));
    }
    entry.snapshot_size = static_cast<std::size_t>(at - entry.snapshot);
    entry.kind = folder ? KIND_FOLDER : KIND_FILE;
    entry.size = info.EndOfFile.QuadPart;
    entry.modified = seconds(written);
    entry.attributes = info.FileAttributes;
    return true;
}

std::wstring child_prefix(const std::wstring& folder) {
    // What os.scandir puts before an entry's name: a separator unless the path already ends in one.
    if (folder.empty()) {
        return folder;
    }
    wchar_t last = folder.back();
    return (last == L'\\' || last == L'/' || last == L':') ? folder : folder + L'\\';
}

// List ``folder`` into ``entries``. Returns 0, or the Windows error that stopped the listing.
DWORD list_folder(const std::wstring& folder, int how, bool file_times, bool change_time, std::vector<Entry>& entries) {
    std::wstring prefix = child_prefix(folder);
    std::wstring pattern = prefix + L"*.*";
    WIN32_FIND_DATAW found;
    HANDLE listing = FindFirstFileExW(pattern.c_str(), FindExInfoBasic, &found, FindExSearchNameMatch, nullptr,
                                      FIND_FIRST_EX_LARGE_FETCH);
    if (listing == INVALID_HANDLE_VALUE) {
        DWORD error = GetLastError();
        return error == ERROR_FILE_NOT_FOUND ? 0 : error;  // an empty root lists nothing, as os.scandir has it
    }
    DWORD error = 0;
    std::wstring path;
    do {
        const wchar_t* name = found.cFileName;
        if (name[0] == L'.' && (name[1] == 0 || (name[1] == L'.' && name[2] == 0))) {
            continue;
        }
        Entry entry;
        entry.name = name;
        path.assign(prefix).append(entry.name);
        StatBasic info;
        if (query(path.c_str(), how, info)) {
            describe(info, file_times, change_time, entry);
        }
        entries.push_back(std::move(entry));
    } while (FindNextFileW(listing, &found));
    error = GetLastError();
    FindClose(listing);
    return error == ERROR_NO_MORE_FILES ? 0 : error;
}

bool wide_argument(PyObject* text, std::wstring& out) {
    Py_ssize_t length = 0;
    wchar_t* buffer = PyUnicode_AsWideCharString(text, &length);
    if (buffer == nullptr) {
        return false;
    }
    bool whole = static_cast<Py_ssize_t>(wcslen(buffer)) == length;  // no embedded null character
    if (whole) {
        out.assign(buffer, static_cast<std::size_t>(length));
    } else {
        PyErr_SetString(PyExc_ValueError, "embedded null character in path");
    }
    PyMem_Free(buffer);
    return whole;
}

PyObject* row_of(const Entry& entry) {
    PyObject* name = PyUnicode_FromWideChar(entry.name.data(), static_cast<Py_ssize_t>(entry.name.size()));
    if (name == nullptr) {
        return nullptr;
    }
    if (entry.kind == KIND_ASK_PYTHON) {
        PyObject* row = Py_BuildValue("(NiLdOI)", name, entry.kind, 0LL, 0.0, Py_None, 0U);
        return row;
    }
    return Py_BuildValue("(NiLdy#I)", name, entry.kind, static_cast<long long>(entry.size), entry.modified,
                         reinterpret_cast<const char*>(entry.snapshot), static_cast<Py_ssize_t>(entry.snapshot_size),
                         static_cast<unsigned int>(entry.attributes));
}

bool known_query(int how) {
    if (how == QUERY_BY_HANDLE || (how == QUERY_BY_NAME && by_name_query() != nullptr)) {
        return true;
    }
    PyErr_SetString(PyExc_ValueError, "unknown or unavailable metadata query");
    return false;
}

// read_folder(path, file_times, change_time, query) -> [(name, kind, size, modified, snapshot, attributes), ...]
PyObject* read_folder(PyObject*, PyObject* arguments) {
    PyObject* text = nullptr;
    int file_times = 0;
    int change_time = 0;
    int how = 0;
    if (!PyArg_ParseTuple(arguments, "Uppi", &text, &file_times, &change_time, &how) || !known_query(how)) {
        return nullptr;
    }
    std::wstring folder;
    if (!wide_argument(text, folder)) {
        return nullptr;
    }
    std::vector<Entry> entries;
    DWORD error = 0;
    bool memory = false;
    Py_BEGIN_ALLOW_THREADS
    try {
        error = list_folder(folder, how, file_times != 0, change_time != 0, entries);
    } catch (const std::bad_alloc&) {
        memory = true;
    }
    Py_END_ALLOW_THREADS
    if (memory) {
        return PyErr_NoMemory();
    }
    if (error != 0) {
        return PyErr_SetExcFromWindowsErrWithFilenameObject(PyExc_OSError, static_cast<int>(error), text);
    }
    PyObject* rows = PyList_New(static_cast<Py_ssize_t>(entries.size()));
    if (rows == nullptr) {
        return nullptr;
    }
    for (std::size_t index = 0; index < entries.size(); ++index) {
        PyObject* row = row_of(entries[index]);
        if (row == nullptr) {
            Py_DECREF(rows);
            return nullptr;
        }
        PyList_SetItem(rows, static_cast<Py_ssize_t>(index), row);  // takes the reference
    }
    return rows;
}

// snapshot(path, file_times, change_time, query) -> bytes, or None when Python must answer
PyObject* snapshot(PyObject*, PyObject* arguments) {
    PyObject* text = nullptr;
    int file_times = 0;
    int change_time = 0;
    int how = 0;
    if (!PyArg_ParseTuple(arguments, "Uppi", &text, &file_times, &change_time, &how) || !known_query(how)) {
        return nullptr;
    }
    std::wstring path;
    if (!wide_argument(text, path)) {
        return nullptr;
    }
    StatBasic info;
    Entry entry;
    bool known = false;
    Py_BEGIN_ALLOW_THREADS
    known = query(path.c_str(), how, info) && describe(info, file_times != 0, change_time != 0, entry);
    Py_END_ALLOW_THREADS
    if (!known) {
        Py_RETURN_NONE;
    }
    return PyBytes_FromStringAndSize(reinterpret_cast<const char*>(entry.snapshot),
                                     static_cast<Py_ssize_t>(entry.snapshot_size));
}

PyObject* by_name_available(PyObject*, PyObject*) {
    return PyBool_FromLong(by_name_query() != nullptr);
}

PyMethodDef methods[] = {
    {"read_folder", read_folder, METH_VARARGS,
     "List one folder: (name, kind, size, modified, snapshot, attributes) per entry, read-only."},
    {"snapshot", snapshot, METH_VARARGS, "The packed no-follow snapshot of one path, or None."},
    {"by_name_available", by_name_available, METH_NOARGS, "Whether Windows offers the one-call metadata query."},
    {nullptr, nullptr, 0, nullptr},
};

PyModuleDef definition = {
    PyModuleDef_HEAD_INIT, "je_file_tree._native", "Read-only native folder listing for the Windows scanner.", -1,
    methods, nullptr, nullptr, nullptr, nullptr,
};

}  // namespace

PyMODINIT_FUNC PyInit__native(void) {
    PyObject* module = PyModule_Create(&definition);
    if (module == nullptr) {
        return nullptr;
    }
    by_name_query();  // resolve once here, under the interpreter lock
    if (PyModule_AddIntConstant(module, "KIND_FILE", KIND_FILE) != 0
        || PyModule_AddIntConstant(module, "KIND_FOLDER", KIND_FOLDER) != 0
        || PyModule_AddIntConstant(module, "KIND_ASK_PYTHON", KIND_ASK_PYTHON) != 0
        || PyModule_AddIntConstant(module, "QUERY_BY_NAME", QUERY_BY_NAME) != 0
        || PyModule_AddIntConstant(module, "QUERY_BY_HANDLE", QUERY_BY_HANDLE) != 0) {
        Py_DECREF(module);
        return nullptr;
    }
    return module;
}
