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
#include <winioctl.h>

#include <algorithm>
#include <cstdint>
#include <cmath>
#include <cstring>
#include <ctime>
#include <cwchar>
#include <cwctype>
#include <functional>
#include <map>
#include <new>
#include <string>
#include <system_error>
#include <thread>
#include <tuple>
#include <unordered_map>
#include <vector>

namespace {

constexpr int KIND_FILE = 0;
constexpr int KIND_FOLDER = 1;
constexpr int KIND_ASK_PYTHON = 2;

constexpr int QUERY_BY_NAME = 1;    // GetFileInformationByName (Windows 11 24H2 and later)
constexpr int QUERY_BY_HANDLE = 2;  // open the entry itself and ask the handle
// The same, with the identity Python 3.11 reports: the 32-bit volume number and 64-bit file number of
// GetFileInformationByHandle. Python 3.12 and later report the 64-bit and 128-bit ones.
constexpr int QUERY_BY_HANDLE_SHORT = 3;

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

bool query_by_handle(const wchar_t* path, bool short_identity, StatBasic& out) {
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
        && (short_identity || GetFileInformationByHandleEx(handle, FileIdInfo, &identity, sizeof(identity)));
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
    if (short_identity) {
        out.VolumeSerialNumber.QuadPart = static_cast<LONGLONG>(plain.dwVolumeSerialNumber);
        std::memcpy(out.FileId128, &plain.nFileIndexLow, sizeof(plain.nFileIndexLow));
        std::memcpy(out.FileId128 + sizeof(plain.nFileIndexLow), &plain.nFileIndexHigh, sizeof(plain.nFileIndexHigh));
        return true;  // the upper eight bytes stay zero
    }
    out.VolumeSerialNumber.QuadPart = static_cast<LONGLONG>(identity.VolumeSerialNumber);
    std::memcpy(out.FileId128, identity.FileId.Identifier, sizeof(out.FileId128));
    return true;
}

bool query(const wchar_t* path, int how, StatBasic& out) {
    if (how == QUERY_BY_NAME) {
        ByNameQuery by_name = by_name_query();
        return by_name != nullptr && by_name(path, STAT_BASIC_BY_NAME, &out, sizeof(out));
    }
    return query_by_handle(path, how == QUERY_BY_HANDLE_SHORT, out);
}

const ULONG RECALL_ON_OPEN = 0x40000;

// ``attributes`` of a path with the recall-on-open bit replaced by the listing's (core/snapshot.py).
ULONG listed_recall(ULONG attributes, ULONG listed) {
    ULONG wanted = (attributes & ~RECALL_ON_OPEN) | (listed & RECALL_ON_OPEN);
    return wanted == 0 && attributes != 0 ? FILE_ATTRIBUTE_NORMAL : wanted;  // nothing left is "normal"
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
        // Only a directory listing may say "recall on open"; a query by name can set the same bit on
        // an ordinary file nobody has opened yet (see core/snapshot.py), so the listing's bit is kept.
        entry.attributes = found.dwFileAttributes & RECALL_ON_OPEN;
        StatBasic info;
        if (query(path.c_str(), how, info)) {
            info.FileAttributes = listed_recall(info.FileAttributes, entry.attributes);
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
    // No "#" format: built with the headers of Python 3.13 or later it calls a function that
    // Python 3.11 and 3.12 refuse ("PY_SSIZE_T_CLEAN macro must be defined"), found 2026-11-14.
    PyObject* snapshot = PyBytes_FromStringAndSize(reinterpret_cast<const char*>(entry.snapshot),
                                                   static_cast<Py_ssize_t>(entry.snapshot_size));
    if (snapshot == nullptr) {
        Py_DECREF(name);
        return nullptr;
    }
    return Py_BuildValue("(NiLdNI)", name, entry.kind, static_cast<long long>(entry.size), entry.modified, snapshot,
                         static_cast<unsigned int>(entry.attributes));
}

bool known_query(int how) {
    if (how == QUERY_BY_HANDLE || how == QUERY_BY_HANDLE_SHORT || (how == QUERY_BY_NAME && by_name_query() != nullptr)) {
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
    known = query(path.c_str(), how, info);
    if (known) {
        info.FileAttributes = listed_recall(info.FileAttributes, 0);  // no listing here to confirm it
        known = describe(info, file_times != 0, change_time != 0, entry);
    }
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

// ---------------------------------------------------------------------------------------------
// Reading a whole NTFS volume from its master file table (MFT).
//
// Listing every folder costs a call into the file system per folder and a query per entry. The MFT
// holds one record per file with the same metadata, and reading it is one sequential read of the
// volume. Measured 2026-11-15 on a 237 GB system volume (1.56 million records, 1.6 GB): see
// core/mft_scan.py.
//
// What it promises:
//   * It only reads: the volume and $MFT are opened for reading, nothing is written anywhere.
//   * Rows have the read_folder format, and a snapshot is built the way one from a query is, so the
//     scanner and every later check treat them alike. Those checks still compare a fresh os.lstat
//     with the recorded snapshot before any operation; an entry the table described differently is
//     then refused as changed, never acted on.
//   * Reparse points (links, cloud placeholders, system-compressed files) and records it cannot
//     fully describe are returned as "ask Python", exactly like read_folder.
//   * A record that fails its update-sequence check is counted in ``damaged``; core/mft_scan.py
//     then does not use the table at all.
// The table on disk can be a few seconds behind the running system.

constexpr std::uint64_t ORDINAL_MASK = 0xFFFFFFFFFFFFULL;
constexpr std::uint32_t ATTRIBUTE_STANDARD = 0x10;
constexpr std::uint32_t ATTRIBUTE_NAME = 0x30;
constexpr std::uint32_t ATTRIBUTE_DATA = 0x80;
constexpr std::uint32_t ATTRIBUTE_INDEX_ALLOCATION = 0xA0;
constexpr std::uint32_t ATTRIBUTE_REPARSE = 0xC0;
constexpr std::uint32_t ATTRIBUTE_END = 0xFFFFFFFF;
constexpr ULONG TABLE_ONLY_FLAGS = 0x40000 | 0x10000000 | 0x20000000;  // never reported by a query
constexpr std::uint8_t NAMESPACE_DOS = 2;         // the 8.3 alias of a name that is recorded separately
constexpr std::uint64_t FIRST_USER_RECORD = 16;   // the records below are the file system's own files
constexpr std::uint64_t ROOT_RECORD = 5;
constexpr std::size_t MFT_SECTOR = 512;           // update-sequence strides are 512 bytes whatever the sector size
constexpr std::size_t MFT_CHUNK = 8 * 1024 * 1024;
constexpr unsigned MFT_READERS = 4;
constexpr const char* MFT_CAPSULE = "je_file_tree._native.mft";

struct MftRecord {
    std::int64_t size = 0;
    std::int64_t created = 0;
    std::int64_t modified = 0;
    std::int64_t changed = 0;
    std::int64_t accessed = 0;
    std::uint32_t attributes = 0;
    std::uint32_t names = 0;      // names that are not 8.3 aliases: what os.lstat reports as the link count
    std::uint16_t sequence = 0;
    // One byte each, each written by one reading thread only: the first three by the thread that
    // meets the record itself, the last two by the thread that meets the record holding the attribute.
    std::uint8_t in_use = 0;
    std::uint8_t folder = 0;
    std::uint8_t described = 0;   // has standard information
    std::uint8_t sized = 0;       // has the start of its unnamed data
    std::uint8_t reparse = 0;
};

struct MftLink {
    std::uint64_t parent = 0;  // ordinal
    std::uint64_t child = 0;   // ordinal
    std::uint32_t name_at = 0;
    std::uint16_t name_length = 0;
    std::uint16_t parent_sequence = 0;
};

struct MftIndex {
    std::uint64_t serial = 0;
    std::uint64_t damaged = 0;
    std::vector<MftRecord> records;
    std::vector<MftLink> links;        // grouped by parent
    std::vector<std::uint32_t> first;  // links of folder n are [first[n], first[n + 1])
    std::vector<wchar_t> names;
};

struct MftPiece {  // a run of whole records: where it is in the table and on the volume
    std::uint64_t first_record = 0;
    std::uint64_t volume_offset = 0;
    std::uint32_t bytes = 0;
};

struct MftFound {  // what one reading thread collected
    std::vector<MftLink> links;
    std::vector<wchar_t> names;
    std::uint64_t damaged = 0;
    DWORD error = 0;
};

template <typename Value>
Value field(const unsigned char* at) {
    Value value;
    std::memcpy(&value, at, sizeof(value));
    return value;
}

// Put back the two bytes each 512-byte stride ends with; false when the record was torn.
bool fix_up(unsigned char* record, std::size_t size) {
    std::size_t offset = field<std::uint16_t>(record + 4);
    std::size_t count = field<std::uint16_t>(record + 6);
    if (count < 2 || (count - 1) * MFT_SECTOR != size || offset + count * 2 > size) {
        return false;
    }
    std::uint16_t expected = field<std::uint16_t>(record + offset);
    for (std::size_t stride = 1; stride < count; ++stride) {
        unsigned char* tail = record + stride * MFT_SECTOR - 2;
        if (field<std::uint16_t>(tail) != expected) {
            return false;
        }
        std::memcpy(tail, record + offset + stride * 2, 2);
    }
    return true;
}

void standard_information(const unsigned char* value, std::size_t length, MftRecord& record) {
    if (length < 36) {
        return;
    }
    record.created = field<std::int64_t>(value);
    record.modified = field<std::int64_t>(value + 8);
    record.changed = field<std::int64_t>(value + 16);
    record.accessed = field<std::int64_t>(value + 24);
    record.attributes = field<std::uint32_t>(value + 32);
    record.described = 1;
}

void file_name(const unsigned char* value, std::size_t length, std::uint64_t owner, MftFound& found) {
    if (length < 66) {
        return;
    }
    std::size_t characters = value[64];
    if (value[65] == NAMESPACE_DOS || characters == 0 || 66 + characters * 2 > length) {
        return;
    }
    std::uint64_t parent = field<std::uint64_t>(value);
    MftLink link;
    link.parent = parent & ORDINAL_MASK;
    link.parent_sequence = static_cast<std::uint16_t>(parent >> 48);
    link.child = owner;
    link.name_at = static_cast<std::uint32_t>(found.names.size());
    link.name_length = static_cast<std::uint16_t>(characters);
    found.names.resize(found.names.size() + characters);
    std::memcpy(found.names.data() + link.name_at, value + 66, characters * 2);
    found.links.push_back(link);
}

// One attribute of the record ``owner`` (the base record when it sits in an extension record).
void attribute(const unsigned char* at, std::size_t length, std::uint64_t owner, MftIndex& index, MftFound& found) {
    std::uint32_t type = field<std::uint32_t>(at);
    bool resident = at[8] == 0;
    bool unnamed = at[9] == 0;
    MftRecord& record = index.records[owner];
    if (type == ATTRIBUTE_REPARSE) {
        record.reparse = 1;
    } else if (type == ATTRIBUTE_INDEX_ALLOCATION && !resident) {
        // What Windows reports as the size of a folder: its file-name index outside the record
        // (0 while the index still fits inside). Found 2026-11-15: 49,236 of 123,279 folders compared.
        std::size_t name_at = field<std::uint16_t>(at + 10);
        if (at[9] == 4 && name_at + 8 <= length && std::memcmp(at + name_at, L"$I30", 8) == 0 && length >= 56
            && field<std::int64_t>(at + 16) == 0) {
            record.size = field<std::int64_t>(at + 48);
        }
    } else if (type == ATTRIBUTE_DATA && unnamed && !resident) {
        if (length >= 56 && field<std::int64_t>(at + 16) == 0) {  // the piece that starts the data carries its size
            record.size = field<std::int64_t>(at + 48);
            record.sized = 1;
        }
    } else if (resident && length >= 24) {
        std::size_t value_length = field<std::uint32_t>(at + 16);
        std::size_t value_at = field<std::uint16_t>(at + 20);
        if (value_at + value_length > length) {
            return;
        }
        if (type == ATTRIBUTE_STANDARD) {
            standard_information(at + value_at, value_length, record);
        } else if (type == ATTRIBUTE_NAME) {
            file_name(at + value_at, value_length, owner, found);
        } else if (type == ATTRIBUTE_DATA && unnamed) {
            record.size = static_cast<std::int64_t>(value_length);
            record.sized = 1;
        }
    }
}

void parse_record(unsigned char* data, std::size_t size, std::uint64_t ordinal, MftIndex& index, MftFound& found) {
    if (std::memcmp(data, "FILE", 4) != 0) {
        found.damaged += std::memcmp(data, "BAAD", 4) == 0 ? 1 : 0;  // anything else was never a record
        return;
    }
    if ((field<std::uint16_t>(data + 22) & 1) == 0) {
        return;  // not in use
    }
    if (!fix_up(data, size)) {
        ++found.damaged;
        return;
    }
    std::uint64_t base = field<std::uint64_t>(data + 32) & ORDINAL_MASK;
    std::uint64_t owner = base != 0 ? base : ordinal;
    if (owner >= index.records.size()) {
        ++found.damaged;
        return;
    }
    if (base == 0) {
        MftRecord& record = index.records[ordinal];
        record.sequence = field<std::uint16_t>(data + 16);
        record.folder = (field<std::uint16_t>(data + 22) & 2) != 0 ? 1 : 0;
        record.in_use = 1;
    }
    std::size_t at = field<std::uint16_t>(data + 20);
    std::size_t used = (std::min)(static_cast<std::size_t>(field<std::uint32_t>(data + 24)), size);
    while (at + 16 <= used && field<std::uint32_t>(data + at) != ATTRIBUTE_END) {
        std::size_t length = field<std::uint32_t>(data + at + 4);
        if (length < 16 || at + length > used) {
            ++found.damaged;
            return;
        }
        attribute(data + at, length, owner, index, found);
        at += length;
    }
}

HANDLE open_for_reading(const std::wstring& path, DWORD access) {
    return CreateFileW(path.c_str(), access, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
                       OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, nullptr);
}

// The pieces of the table, in table order, from the extents Windows reports for $MFT.
DWORD table_pieces(const std::wstring& drive, std::uint64_t cluster, std::uint64_t record_size,
                   std::uint64_t valid_bytes, std::vector<MftPiece>& pieces) {
    HANDLE table = open_for_reading(drive + L"\\$MFT", FILE_READ_ATTRIBUTES);
    if (table == INVALID_HANDLE_VALUE) {
        return GetLastError();
    }
    std::vector<std::uint64_t> buffer(8192);  // 64 KB, aligned for the extents
    STARTING_VCN_INPUT_BUFFER start = {};
    DWORD error = 0;
    std::uint64_t table_offset = 0;
    for (bool more = true; more && error == 0;) {
        DWORD returned = 0;
        more = false;
        if (!DeviceIoControl(table, FSCTL_GET_RETRIEVAL_POINTERS, &start, sizeof(start), buffer.data(),
                             static_cast<DWORD>(buffer.size() * sizeof(std::uint64_t)), &returned, nullptr)) {
            error = GetLastError();
            if (error != ERROR_MORE_DATA) {
                break;
            }
            error = 0;
            more = true;
        }
        const RETRIEVAL_POINTERS_BUFFER& found = *reinterpret_cast<const RETRIEVAL_POINTERS_BUFFER*>(buffer.data());
        LONGLONG previous = found.StartingVcn.QuadPart;
        for (DWORD number = 0; number < found.ExtentCount && error == 0; ++number) {
            LONGLONG next = found.Extents[number].NextVcn.QuadPart;
            LONGLONG lcn = found.Extents[number].Lcn.QuadPart;
            if (lcn < 0 || next <= previous) {
                error = ERROR_FILE_CORRUPT;  // a hole in the table: not something to guess about
                break;
            }
            std::uint64_t bytes = static_cast<std::uint64_t>(next - previous) * cluster;
            std::uint64_t volume_offset = static_cast<std::uint64_t>(lcn) * cluster;
            for (std::uint64_t done = 0; done < bytes && table_offset < valid_bytes;) {
                std::uint64_t take = (std::min)({bytes - done, static_cast<std::uint64_t>(MFT_CHUNK),
                                                valid_bytes - table_offset});
                pieces.push_back({table_offset / record_size, volume_offset + done, static_cast<std::uint32_t>(take)});
                done += take;
                table_offset += take;
            }
            previous = next;
        }
        start.StartingVcn.QuadPart = previous;
        more = more && found.ExtentCount != 0;
    }
    CloseHandle(table);
    return error;
}

// One reading thread: its own volume handle and buffer, pieces taken in turn.
void read_pieces(const std::wstring& volume_path, const std::vector<MftPiece>& pieces, std::size_t record_size,
                 LONG volatile* next, MftIndex& index, MftFound& found) {
    HANDLE volume = open_for_reading(volume_path, GENERIC_READ);
    void* buffer = VirtualAlloc(nullptr, MFT_CHUNK, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (volume == INVALID_HANDLE_VALUE || buffer == nullptr) {
        found.error = GetLastError() != 0 ? GetLastError() : ERROR_NOT_ENOUGH_MEMORY;
    }
    while (found.error == 0) {
        std::size_t number = static_cast<std::size_t>(InterlockedIncrement(next)) - 1;
        if (number >= pieces.size()) {
            break;
        }
        const MftPiece& piece = pieces[number];
        OVERLAPPED where = {};
        where.Offset = static_cast<DWORD>(piece.volume_offset);
        where.OffsetHigh = static_cast<DWORD>(piece.volume_offset >> 32);
        DWORD got = 0;
        if (!ReadFile(volume, buffer, piece.bytes, &got, &where) || got != piece.bytes) {
            found.error = GetLastError() != 0 ? GetLastError() : ERROR_READ_FAULT;
            break;
        }
        unsigned char* data = static_cast<unsigned char*>(buffer);
        for (std::size_t at = 0; at + record_size <= got; at += record_size) {
            parse_record(data + at, record_size, piece.first_record + at / record_size, index, found);
        }
    }
    if (buffer != nullptr) {
        VirtualFree(buffer, 0, MEM_RELEASE);
    }
    if (volume != INVALID_HANDLE_VALUE) {
        CloseHandle(volume);
    }
}

// Keep the links whose folder and file both exist as recorded, count names, and group by folder.
void group_links(MftIndex& index, std::vector<MftFound>& found) {
    std::vector<std::uint32_t>& first = index.first;
    first.assign(index.records.size() + 1, 0);
    std::size_t kept = 0;
    for (MftFound& part : found) {
        for (MftLink& link : part.links) {
            const MftRecord* parent = link.parent < index.records.size() ? &index.records[link.parent] : nullptr;
            MftRecord& child = index.records[link.child];
            bool valid = parent != nullptr && parent->in_use && parent->folder
                && parent->sequence == link.parent_sequence && child.in_use;
            if (!valid) {
                link.name_length = 0;  // dropped
                continue;
            }
            ++child.names;
            if (link.child < FIRST_USER_RECORD || link.child == link.parent) {
                link.name_length = 0;  // the file system's own files and the root's name for itself
                continue;
            }
            ++first[link.parent + 1];
            ++kept;
        }
    }
    for (std::size_t folder = 1; folder < first.size(); ++folder) {
        first[folder] += first[folder - 1];
    }
    index.links.resize(kept);
    std::vector<std::uint32_t> next(first.begin(), first.end() - 1);
    for (MftFound& part : found) {
        std::uint32_t moved = static_cast<std::uint32_t>(index.names.size());
        index.names.insert(index.names.end(), part.names.begin(), part.names.end());
        for (const MftLink& link : part.links) {
            if (link.name_length != 0) {
                MftLink& placed = index.links[next[link.parent]++];
                placed = link;
                placed.name_at += moved;
            }
        }
        std::vector<MftLink>().swap(part.links);
        std::vector<wchar_t>().swap(part.names);
    }
}

// Read and index the whole table of ``drive`` ("C:"). Returns 0 or the Windows error that stopped it.
DWORD read_table(const std::wstring& drive, MftIndex& index) {
    std::wstring volume_path = L"\\\\.\\" + drive;
    HANDLE volume = open_for_reading(volume_path, GENERIC_READ);
    if (volume == INVALID_HANDLE_VALUE) {
        return GetLastError();
    }
    NTFS_VOLUME_DATA_BUFFER data = {};
    DWORD returned = 0;
    BOOL known = DeviceIoControl(volume, FSCTL_GET_NTFS_VOLUME_DATA, nullptr, 0, &data, sizeof(data), &returned,
                                 nullptr);
    DWORD error = known ? 0 : GetLastError();
    CloseHandle(volume);
    if (error != 0) {
        return error;
    }
    std::uint64_t record_size = data.BytesPerFileRecordSegment;
    std::uint64_t cluster = data.BytesPerCluster;
    if (record_size < 2 * MFT_SECTOR || record_size % MFT_SECTOR != 0 || cluster % record_size != 0
        || MFT_CHUNK % record_size != 0 || data.MftValidDataLength.QuadPart <= 0) {
        return ERROR_NOT_SUPPORTED;
    }
    std::uint64_t valid = static_cast<std::uint64_t>(data.MftValidDataLength.QuadPart);
    std::vector<MftPiece> pieces;
    error = table_pieces(drive, cluster, record_size, valid - valid % record_size, pieces);
    if (error != 0) {
        return error;
    }
    index.serial = static_cast<std::uint64_t>(data.VolumeSerialNumber.QuadPart);
    index.records.resize(static_cast<std::size_t>(valid / record_size));
    std::vector<MftFound> found(MFT_READERS);
    LONG volatile next = 0;
    {
        std::vector<std::thread> readers;
        for (MftFound& part : found) {
            readers.emplace_back(read_pieces, std::cref(volume_path), std::cref(pieces),
                                 static_cast<std::size_t>(record_size), &next, std::ref(index), std::ref(part));
        }
        for (std::thread& reader : readers) {
            reader.join();
        }
    }
    for (const MftFound& part : found) {
        if (part.error != 0) {
            return part.error;
        }
        index.damaged += part.damaged;
    }
    group_links(index, found);
    return 0;
}

void free_table(PyObject* capsule) {
    delete static_cast<MftIndex*>(PyCapsule_GetPointer(capsule, MFT_CAPSULE));
}

// mft_open(drive) -> the indexed table of an NTFS volume ("C:"), read with the interpreter lock released
PyObject* mft_open(PyObject*, PyObject* arguments) {
    PyObject* text = nullptr;
    if (!PyArg_ParseTuple(arguments, "U", &text)) {
        return nullptr;
    }
    std::wstring drive;
    if (!wide_argument(text, drive)) {
        return nullptr;
    }
    if (drive.size() != 2 || drive[1] != L':' || !iswalpha(drive[0])) {
        PyErr_SetString(PyExc_ValueError, "a drive is a letter and a colon");
        return nullptr;
    }
    MftIndex* index = nullptr;
    DWORD error = 0;
    bool memory = false;
    Py_BEGIN_ALLOW_THREADS
    try {
        index = new MftIndex();
        error = read_table(drive, *index);
    } catch (const std::bad_alloc&) {
        memory = true;
    } catch (const std::system_error&) {
        error = ERROR_NOT_ENOUGH_MEMORY;  // a reading thread could not be started
    }
    Py_END_ALLOW_THREADS
    if (memory || error != 0) {
        delete index;
        return memory ? PyErr_NoMemory()
                      : PyErr_SetExcFromWindowsErrWithFilenameObject(PyExc_OSError, static_cast<int>(error), text);
    }
    PyObject* capsule = PyCapsule_New(index, MFT_CAPSULE, free_table);
    if (capsule == nullptr) {
        delete index;
    }
    return capsule;
}

MftIndex* table_of(PyObject* capsule) {
    return static_cast<MftIndex*>(PyCapsule_GetPointer(capsule, MFT_CAPSULE));  // sets TypeError/ValueError itself
}

// mft_info(table) -> (volume serial number, records, names, damaged records)
PyObject* mft_info(PyObject*, PyObject* arguments) {
    PyObject* capsule = nullptr;
    if (!PyArg_ParseTuple(arguments, "O", &capsule)) {
        return nullptr;
    }
    const MftIndex* index = table_of(capsule);
    if (index == nullptr) {
        return nullptr;
    }
    return Py_BuildValue("(KKKK)", static_cast<unsigned long long>(index->serial),
                         static_cast<unsigned long long>(index->records.size()),
                         static_cast<unsigned long long>(index->links.size()),
                         static_cast<unsigned long long>(index->damaged));
}

// ``record`` (number ``ordinal``) as an entry, the way describe() builds one from a query.
// ``short_identity``: the 32-bit volume number Python 3.11 reports (see QUERY_BY_HANDLE_SHORT).
void table_entry(const MftIndex& index, std::uint64_t ordinal, bool file_times, bool change_time,
                 bool short_identity, Entry& entry) {
    const MftRecord& record = index.records[ordinal];
    if (!record.described || record.reparse || (!record.folder && !record.sized)) {
        return;  // stays "ask Python"
    }
    StatBasic info;
    std::memset(&info, 0, sizeof(info));
    info.CreationTime.QuadPart = record.created;
    info.LastAccessTime.QuadPart = record.accessed;
    info.LastWriteTime.QuadPart = record.modified;
    info.ChangeTime.QuadPart = record.changed;
    info.EndOfFile.QuadPart = record.size;
    // The table keeps a flag of its own in the bit Windows documents as "recall on open" for directory
    // listings (found 2026-11-15: 104,161 ordinary files of a system volume carry it, and were counted
    // as taking no space). A file that really is recalled on open is a reparse point, handled above.
    // So does it with the two high bits that mark a record as holding an index: a hosted Windows
    // runner had 0x10000000 on an empty folder where os.lstat reports 0x10 (found 2026-11-15 by CI).
    info.FileAttributes = (record.attributes & ~TABLE_ONLY_FLAGS) | (record.folder ? FILE_ATTRIBUTE_DIRECTORY : 0);
    if (info.FileAttributes == 0) {
        info.FileAttributes = FILE_ATTRIBUTE_NORMAL;
    }
    info.NumberOfLinks = record.names;
    info.DeviceType = FILE_DEVICE_DISK;
    info.VolumeSerialNumber.QuadPart = static_cast<LONGLONG>(short_identity ? index.serial & 0xFFFFFFFFULL
                                                                            : index.serial);
    std::uint64_t reference = ordinal | (static_cast<std::uint64_t>(record.sequence) << 48);
    std::memcpy(info.FileId128, &reference, sizeof(reference));
    describe(info, file_times, change_time, entry);
}

// The folder a reference (record number and reuse sequence) names, or nullptr with OSError set.
const MftRecord* folder_of(const MftIndex& index, unsigned long long reference) {
    std::uint64_t ordinal = reference & ORDINAL_MASK;
    if (ordinal < index.records.size()) {
        const MftRecord& record = index.records[ordinal];
        if (record.in_use && record.folder && record.sequence == static_cast<std::uint16_t>(reference >> 48)) {
            return &record;
        }
    }
    PyErr_SetFromWindowsErr(ERROR_PATH_NOT_FOUND);
    return nullptr;
}

// mft_rows(table, folder reference, file_times, change_time, short_identity) -> read_folder rows of that folder
PyObject* mft_rows(PyObject*, PyObject* arguments) {
    PyObject* capsule = nullptr;
    unsigned long long reference = 0;
    int file_times = 0;
    int change_time = 0;
    int short_identity = 0;
    if (!PyArg_ParseTuple(arguments, "OKppp", &capsule, &reference, &file_times, &change_time, &short_identity)) {
        return nullptr;
    }
    const MftIndex* index = table_of(capsule);
    if (index == nullptr || folder_of(*index, reference) == nullptr) {
        return nullptr;
    }
    std::uint64_t folder = reference & ORDINAL_MASK;
    std::uint32_t begin = index->first[folder];
    std::uint32_t end = index->first[folder + 1];
    PyObject* rows = PyList_New(static_cast<Py_ssize_t>(end - begin));
    if (rows == nullptr) {
        return nullptr;
    }
    for (std::uint32_t number = begin; number < end; ++number) {
        const MftLink& link = index->links[number];
        Entry entry;
        entry.name.assign(index->names.data() + link.name_at, link.name_length);
        table_entry(*index, link.child, file_times != 0, change_time != 0, short_identity != 0, entry);
        PyObject* row = row_of(entry);
        if (row == nullptr) {
            Py_DECREF(rows);
            return nullptr;
        }
        PyList_SetItem(rows, static_cast<Py_ssize_t>(number - begin), row);  // takes the reference
    }
    return rows;
}

// mft_snapshot(table, reference, file_times, change_time, short_identity) -> that folder's own snapshot, or None
PyObject* mft_snapshot(PyObject*, PyObject* arguments) {
    PyObject* capsule = nullptr;
    unsigned long long reference = 0;
    int file_times = 0;
    int change_time = 0;
    int short_identity = 0;
    if (!PyArg_ParseTuple(arguments, "OKppp", &capsule, &reference, &file_times, &change_time, &short_identity)) {
        return nullptr;
    }
    const MftIndex* index = table_of(capsule);
    if (index == nullptr || folder_of(*index, reference) == nullptr) {
        return nullptr;
    }
    Entry entry;
    table_entry(*index, reference & ORDINAL_MASK, file_times != 0, change_time != 0, short_identity != 0, entry);
    if (entry.kind == KIND_ASK_PYTHON) {
        Py_RETURN_NONE;
    }
    return PyBytes_FromStringAndSize(reinterpret_cast<const char*>(entry.snapshot),
                                     static_cast<Py_ssize_t>(entry.snapshot_size));
}

// ---------------------------------------------------------------------------------------------
// Passes over a finished tree of nodes.
//
// After a scan the same worker walks the tree several times: for the saved history, the capacity
// ledger and the summary. Those loops run once per folder or per file in Python; here the same steps
// are taken with the node's attributes read directly. Each function does a bounded amount of work per
// call, so the caller can look at its cancel event and let the window go first in between, and each
// produces exactly what the Python code it stands in for produces (the tests compare the two).

struct NodeNames {
    PyObject* name = nullptr;
    PyObject* size = nullptr;
    PyObject* allocated = nullptr;
    PyObject* file_count = nullptr;
    PyObject* dir_count = nullptr;
    PyObject* modified = nullptr;
    PyObject* accounting = nullptr;
    PyObject* error = nullptr;
    PyObject* children = nullptr;
    PyObject* parent = nullptr;
    PyObject* is_dir = nullptr;
    PyObject* is_link = nullptr;
    PyObject* snapshot = nullptr;
};

NodeNames node_names;

bool intern_node_names() {
    struct Wanted { PyObject** slot; const char* text; };
    const Wanted wanted[] = {
        {&node_names.name, "name"}, {&node_names.size, "size"}, {&node_names.allocated, "allocated"},
        {&node_names.file_count, "file_count"}, {&node_names.dir_count, "dir_count"},
        {&node_names.modified, "modified"}, {&node_names.accounting, "accounting"}, {&node_names.error, "error"},
        {&node_names.children, "children"}, {&node_names.parent, "parent"}, {&node_names.is_dir, "is_dir"},
        {&node_names.is_link, "is_link"}, {&node_names.snapshot, "snapshot"},
    };
    for (const Wanted& one : wanted) {
        *one.slot = PyUnicode_InternFromString(one.text);
        if (*one.slot == nullptr) {
            return false;
        }
    }
    return true;
}

// Local time as export._iso_time writes it. That function calls time.localtime, which on Windows also
// builds the zone's name for every call: 6 of the 7 microseconds a folder cost (measured 2026-11-15).
// The two C runtime functions below are the ones time.localtime itself uses, taken from the runtime
// library already loaded in this process, so the zone rules and their state are Python's own.
bool json_string(PyObject* text, std::wstring& out);

typedef int(__cdecl* LocalTime)(struct tm*, const long long*);
typedef long long(__cdecl* UtcSeconds)(struct tm*);

struct LocalClock {
    LocalTime local = nullptr;
    UtcSeconds utc = nullptr;
};

LocalClock local_clock;

void find_local_clock() {  // called once, at module start
    HMODULE runtime = GetModuleHandleW(L"ucrtbase.dll");
    if (runtime != nullptr) {
        local_clock.local = reinterpret_cast<LocalTime>(GetProcAddress(runtime, "_localtime64_s"));
        local_clock.utc = reinterpret_cast<UtcSeconds>(GetProcAddress(runtime, "_mkgmtime64"));
    }
}

constexpr double LATEST_PLAIN_TIME = 32503680000.0;  // the year 3000: anything later is left to Python

// Append ``"YYYY-MM-DDTHH:MM:SS+HH:MM"`` (quoted) for a positive time; false when Python must format it.
bool local_time_text(double timestamp, std::wstring& out) {
    if (local_clock.local == nullptr || local_clock.utc == nullptr || !(timestamp > 0.0)
        || !(timestamp < LATEST_PLAIN_TIME)) {
        return false;
    }
    double whole = std::floor(timestamp);
    long long seconds = static_cast<long long>(whole);
    if (timestamp - whole >= 0.9999995) {
        ++seconds;  // round(timestamp, 6) reaches the next second
    }
    struct tm local = {};
    if (local_clock.local(&local, &seconds) != 0) {
        return false;
    }
    struct tm copy = local;
    long long offset = local_clock.utc(&copy) - seconds;
    if (offset % 60 != 0) {
        return false;
    }
    long long minutes = (offset < 0 ? -offset : offset) / 60;
    wchar_t buffer[40];
    swprintf(buffer, 40, L"\"%04d-%02d-%02dT%02d:%02d:%02d%lc%02lld:%02lld\"", local.tm_year + 1900, local.tm_mon + 1,
             local.tm_mday, local.tm_hour, local.tm_min, local.tm_sec, offset < 0 ? L'-' : L'+', minutes / 60,
             minutes % 60);
    out += buffer;
    return true;
}

// ``"modified": ...`` text of a node's time: formatted here when plain, by ``iso_time`` otherwise.
bool json_time(PyObject* modified, PyObject* iso_time, std::wstring& out) {
    double timestamp = PyFloat_AsDouble(modified);
    if (timestamp == -1.0 && PyErr_Occurred()) {
        return false;
    }
    if (timestamp <= 0.0) {
        out += L"\"\"";
        return true;
    }
    if (local_time_text(timestamp, out)) {
        return true;
    }
    PyObject* when = PyObject_CallFunctionObjArgs(iso_time, modified, nullptr);
    bool whole = when != nullptr && json_string(when, out);
    Py_XDECREF(when);
    return whole;
}

// An integer attribute; false with a Python error set.
bool integer_of(PyObject* node, PyObject* attribute, long long& value) {
    PyObject* found = PyObject_GetAttr(node, attribute);
    if (found == nullptr) {
        return false;
    }
    value = PyLong_AsLongLong(found);
    Py_DECREF(found);
    return !(value == -1 && PyErr_Occurred());
}

// Whether an attribute is true; -1 with a Python error set.
int truth_of(PyObject* node, PyObject* attribute) {
    PyObject* found = PyObject_GetAttr(node, attribute);
    if (found == nullptr) {
        return -1;
    }
    int truth = PyObject_IsTrue(found);
    Py_DECREF(found);
    return truth;
}

// ``text`` as json.dumps(text, ensure_ascii=False) writes it; false with a Python error set.
bool json_string(PyObject* text, std::wstring& out) {
    if (!PyUnicode_Check(text)) {
        PyErr_SetString(PyExc_TypeError, "a string is expected");
        return false;
    }
    Py_ssize_t length = 0;
    wchar_t* buffer = PyUnicode_AsWideCharString(text, &length);
    if (buffer == nullptr) {
        return false;
    }
    out.push_back(L'"');
    for (Py_ssize_t at = 0; at < length; ++at) {
        wchar_t one = buffer[at];
        switch (one) {
            case L'"': out += L"\\\""; break;
            case L'\\': out += L"\\\\"; break;
            case L'\n': out += L"\\n"; break;
            case L'\r': out += L"\\r"; break;
            case L'\t': out += L"\\t"; break;
            case L'\b': out += L"\\b"; break;
            case L'\f': out += L"\\f"; break;
            default:
                if (one < 0x20) {
                    wchar_t escaped[8];
                    swprintf(escaped, 8, L"\\u%04x", static_cast<unsigned>(one));
                    out += escaped;
                } else {
                    out.push_back(one);
                }
        }
    }
    out.push_back(L'"');
    PyMem_Free(buffer);
    return true;
}

bool json_integer(PyObject* node, PyObject* attribute, const wchar_t* label, std::wstring& out) {
    long long value = 0;
    if (!integer_of(node, attribute, value)) {
        return false;
    }
    out += label;
    out += std::to_wstring(value);
    return true;
}

// The two counted totals: the named ones unless the node carries ``accounting``.
bool json_accounted(PyObject* node, std::wstring& out) {
    PyObject* accounting = PyObject_GetAttr(node, node_names.accounting);
    if (accounting == nullptr) {
        return false;
    }
    bool whole = true;
    if (accounting == Py_None) {
        whole = json_integer(node, node_names.size, L", \"accounted_size\": ", out)
            && json_integer(node, node_names.allocated, L", \"accounted_allocated\": ", out);
    } else {
        const wchar_t* labels[] = {L", \"accounted_size\": ", L", \"accounted_allocated\": "};
        for (Py_ssize_t part = 0; whole && part < 2; ++part) {
            PyObject* item = PySequence_GetItem(accounting, part);
            long long value = item != nullptr ? PyLong_AsLongLong(item) : -1;
            Py_XDECREF(item);
            whole = item != nullptr && !(value == -1 && PyErr_Occurred());
            out += labels[part];
            out += std::to_wstring(value);
        }
    }
    Py_DECREF(accounting);
    return whole;
}

// The fields of one folder as export._folder_json writes them, without the closing brace.
bool json_fields(PyObject* node, PyObject* iso_time, std::wstring& out) {
    PyObject* name = PyObject_GetAttr(node, node_names.name);
    PyObject* modified = PyObject_GetAttr(node, node_names.modified);
    PyObject* error = PyObject_GetAttr(node, node_names.error);
    PyObject* parent = PyObject_GetAttr(node, node_names.parent);
    bool whole = name != nullptr && modified != nullptr && error != nullptr && parent != nullptr;
    if (whole) {
        out += L"{\"name\": ";
        whole = json_string(name, out)
            && json_integer(node, node_names.size, L", \"size\": ", out)
            && json_integer(node, node_names.allocated, L", \"allocated\": ", out)
            && json_integer(node, node_names.file_count, L", \"files\": ", out)
            && json_integer(node, node_names.dir_count, L", \"folders\": ", out);
    }
    if (whole) {
        out += L", \"modified\": ";
        whole = json_time(modified, iso_time, out) && json_accounted(node, out);
    }
    int failed = whole ? PyObject_IsTrue(error) : -1;
    if (failed > 0) {
        out += L", \"error\": ";
        whole = json_string(error, out);
    }
    int named = whole ? PyObject_IsTrue(name) : -1;
    if (whole && parent == Py_None && named == 0) {
        out += L", \"virtual\": true";  // a root over several scanned folders has no path
    }
    whole = whole && failed >= 0 && named >= 0;
    Py_XDECREF(name);
    Py_XDECREF(modified);
    Py_XDECREF(error);
    Py_XDECREF(parent);
    return whole;
}

// The folders among a node's children (links left out), in order; false with a Python error set.
bool folders_of(PyObject* node, std::vector<PyObject*>& folders) {
    PyObject* children = PyObject_GetAttr(node, node_names.children);
    Py_ssize_t count = children != nullptr ? PySequence_Size(children) : -1;
    bool whole = count >= 0;
    for (Py_ssize_t at = 0; whole && at < count; ++at) {
        PyObject* child = PySequence_GetItem(children, at);
        int folder = child != nullptr ? truth_of(child, node_names.is_dir) : -1;
        int link = folder > 0 ? truth_of(child, node_names.is_link) : 0;
        whole = folder >= 0 && link >= 0;
        if (whole && folder > 0 && link == 0) {
            folders.push_back(child);  // keeps the reference
        } else {
            Py_XDECREF(child);
        }
    }
    Py_XDECREF(children);
    if (!whole) {
        for (PyObject* kept : folders) {
            Py_DECREF(kept);
        }
        folders.clear();
    }
    return whole;
}

// local_time_text(timestamp) -> the text export._iso_time gives, or None when Python must format it
PyObject* local_time(PyObject*, PyObject* arguments) {
    double timestamp = 0.0;
    if (!PyArg_ParseTuple(arguments, "d", &timestamp)) {
        return nullptr;
    }
    std::wstring out;
    if (timestamp <= 0.0) {
        return PyUnicode_FromString("");
    }
    if (!local_time_text(timestamp, out)) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromWideChar(out.data() + 1, static_cast<Py_ssize_t>(out.size() - 2));  // without the quotes
}

// Take the last item off a list; a new reference, or nullptr with a Python error set.
PyObject* pop_last(PyObject* list) {
    Py_ssize_t count = PyList_Size(list);
    PyObject* item = count > 0 ? PyList_GetItem(list, count - 1) : nullptr;
    if (item == nullptr) {
        return nullptr;
    }
    Py_INCREF(item);
    if (PyList_SetSlice(list, count - 1, count, nullptr) != 0) {
        Py_DECREF(item);
        return nullptr;
    }
    return item;
}

// json_folders(pending, budget, iso_time, joiner) -> text
//   ``pending`` is a stack (a list): a folder still to write, None for "]}" and True for ", ". Up to
//   ``budget`` items are taken off it and written as export._folder_json would yield them, the pieces
//   joined by ``joiner``; the folders found inside a folder are put on the stack. Call until it is empty.
PyObject* json_folders(PyObject*, PyObject* arguments) {
    PyObject* pending = nullptr;
    PyObject* iso_time = nullptr;
    PyObject* joiner = nullptr;
    Py_ssize_t budget = 0;
    if (!PyArg_ParseTuple(arguments, "O!nOU", &PyList_Type, &pending, &budget, &iso_time, &joiner)) {
        return nullptr;
    }
    Py_ssize_t joiner_length = 0;
    wchar_t* joiner_text = PyUnicode_AsWideCharString(joiner, &joiner_length);
    if (joiner_text == nullptr) {
        return nullptr;
    }
    std::wstring between(joiner_text, static_cast<std::size_t>(joiner_length));
    PyMem_Free(joiner_text);
    std::wstring out;
    bool whole = true;
    for (Py_ssize_t taken = 0; whole && taken < budget && PyList_Size(pending) > 0; ++taken) {
        PyObject* item = pop_last(pending);
        if (item == nullptr) {
            return nullptr;
        }
        if (taken > 0) {
            out += between;
        }
        if (item == Py_None) {
            out += L"]}";
        } else if (item == Py_True) {
            out += L", ";
        } else {
            std::vector<PyObject*> folders;
            whole = json_fields(item, iso_time, out) && folders_of(item, folders);
            if (whole && folders.empty()) {
                out += L"}";
            } else if (whole) {
                out += L", \"children\": [";
                whole = PyList_Append(pending, Py_None) == 0;
                for (std::size_t at = folders.size(); at-- > 0;) {  // the first folder ends up on top
                    whole = whole && PyList_Append(pending, folders[at]) == 0
                        && (at == 0 || PyList_Append(pending, Py_True) == 0);
                    Py_DECREF(folders[at]);
                }
            }
        }
        Py_DECREF(item);
    }
    if (!whole) {
        return nullptr;
    }
    return PyUnicode_FromWideChar(out.data(), static_cast<Py_ssize_t>(out.size()));
}

// ---- the capacity ledger's file totals (core/capacity.py, _Counts) ----

constexpr const char* CAPACITY_CAPSULE = "je_file_tree._native.capacity";
constexpr Py_ssize_t SNAPSHOT_LINKS_AT = 72;

struct FileIdentity {
    std::uint64_t device = 0;
    std::uint64_t low = 0;
    std::uint64_t high = 0;
    bool operator<(const FileIdentity& other) const {
        return std::tie(device, low, high) < std::tie(other.device, other.low, other.high);
    }
};

struct LinkedFile {  // one file with several names: counted once, with its largest recorded allocation
    long long allocated = 0;
    bool in_bin = false;
    bool foreign = false;
};

struct CapacityCounts {
    long long named = 0;
    long long unique = 0;
    long long bin_seen = 0;
    long long foreign = 0;
    bool unknown = false;
    std::map<FileIdentity, LinkedFile> links;

    void count(long long allocated, bool in_bin, bool other_volume) {
        if (other_volume) {
            foreign += allocated;
        } else {
            unique += allocated;
            if (in_bin) {
                bin_seen += allocated;
            }
        }
    }
};

void free_capacity(PyObject* capsule) {
    delete static_cast<CapacityCounts*>(PyCapsule_GetPointer(capsule, CAPACITY_CAPSULE));
}

// capacity_new() -> the running totals of one ledger
PyObject* capacity_new(PyObject*, PyObject*) {
    CapacityCounts* counts = new (std::nothrow) CapacityCounts();
    if (counts == nullptr) {
        return PyErr_NoMemory();
    }
    PyObject* capsule = PyCapsule_New(counts, CAPACITY_CAPSULE, free_capacity);
    if (capsule == nullptr) {
        delete counts;
    }
    return capsule;
}

// _Counts.add for one file; false with a Python error set.
bool capacity_file(PyObject* file, bool has_device, std::uint64_t device, bool in_bin, CapacityCounts& counts) {
    long long allocated = 0;
    PyObject* snapshot = PyObject_GetAttr(file, node_names.snapshot);
    PyObject* error = PyObject_GetAttr(file, node_names.error);
    bool whole = snapshot != nullptr && error != nullptr && integer_of(file, node_names.allocated, allocated);
    if (whole && snapshot == Py_None) {
        counts.named += allocated;
        counts.unknown = true;
        counts.count(allocated, in_bin, false);
    } else if (whole) {
        char* data = nullptr;
        Py_ssize_t length = 0;
        whole = PyBytes_AsStringAndSize(snapshot, &data, &length) == 0;
        if (whole && length != static_cast<Py_ssize_t>(SNAPSHOT_SIZE)
            && length != static_cast<Py_ssize_t>(SNAPSHOT_SIZE + TIMES_SIZE)) {
            PyErr_SetString(PyExc_ValueError, "Invalid filesystem snapshot length");
            whole = false;
        }
        if (whole) {
            FileIdentity identity;
            std::uint32_t names = 0;
            std::memcpy(&identity.device, data, 8);
            std::memcpy(&identity.low, data + 8, 8);
            std::memcpy(&identity.high, data + 16, 8);
            std::memcpy(&names, data + SNAPSHOT_LINKS_AT, 4);
            bool other_volume = has_device && identity.device != device;
            bool known = identity.low != 0 || identity.high != 0;
            if (!other_volume) {
                counts.named += allocated;
            }
            counts.unknown = counts.unknown || !known || names == 0 || error != Py_None;
            if (known && names > 1) {
                auto found = counts.links.find(identity);
                if (found == counts.links.end()) {
                    counts.links[identity] = LinkedFile{allocated, in_bin, other_volume};
                } else {
                    found->second.allocated = (std::max)(found->second.allocated, allocated);
                    found->second.in_bin = found->second.in_bin || in_bin;
                }
            } else {
                counts.count(allocated, in_bin, other_volume);
            }
        }
    }
    Py_XDECREF(snapshot);
    Py_XDECREF(error);
    return whole;
}

// capacity_add(totals, children, device or None, in_bin) -> the folders among ``children`` (links too);
//   every file among them that is not a link is added to the totals as _Counts.add does.
PyObject* capacity_add(PyObject*, PyObject* arguments) {
    PyObject* capsule = nullptr;
    PyObject* children = nullptr;
    PyObject* device_given = nullptr;
    int in_bin = 0;
    if (!PyArg_ParseTuple(arguments, "OOOp", &capsule, &children, &device_given, &in_bin)) {
        return nullptr;
    }
    CapacityCounts* counts = static_cast<CapacityCounts*>(PyCapsule_GetPointer(capsule, CAPACITY_CAPSULE));
    std::uint64_t device = device_given != Py_None ? PyLong_AsUnsignedLongLong(device_given) : 0;
    Py_ssize_t count = counts != nullptr && !PyErr_Occurred() ? PySequence_Size(children) : -1;
    PyObject* folders = count >= 0 ? PyList_New(0) : nullptr;
    if (folders == nullptr) {
        return nullptr;
    }
    bool whole = true;
    try {
        for (Py_ssize_t at = 0; whole && at < count; ++at) {
            PyObject* child = PySequence_GetItem(children, at);
            int folder = child != nullptr ? truth_of(child, node_names.is_dir) : -1;
            if (folder > 0) {
                whole = PyList_Append(folders, child) == 0;
            } else if (folder == 0) {
                int link = truth_of(child, node_names.is_link);
                whole = link >= 0 && (link > 0 || capacity_file(child, device_given != Py_None, device, in_bin != 0,
                                                                *counts));
            } else {
                whole = false;
            }
            Py_XDECREF(child);
        }
    } catch (const std::bad_alloc&) {
        PyErr_NoMemory();
        whole = false;
    }
    if (!whole) {
        Py_DECREF(folders);
        return nullptr;
    }
    return folders;
}

// capacity_finish(totals) -> (named, unique, bin_seen, foreign, unknown), files with several names counted once
PyObject* capacity_finish(PyObject*, PyObject* arguments) {
    PyObject* capsule = nullptr;
    if (!PyArg_ParseTuple(arguments, "O", &capsule)) {
        return nullptr;
    }
    CapacityCounts* counts = static_cast<CapacityCounts*>(PyCapsule_GetPointer(capsule, CAPACITY_CAPSULE));
    if (counts == nullptr) {
        return nullptr;
    }
    for (const auto& linked : counts->links) {
        counts->count(linked.second.allocated, linked.second.in_bin, linked.second.foreign);
    }
    counts->links.clear();
    return Py_BuildValue("(LLLLO)", counts->named, counts->unique, counts->bin_seen, counts->foreign,
                         counts->unknown ? Py_True : Py_False);
}

// ---- the summary: largest files, totals per extension and per age (core/analysis.py, summarise) ----

constexpr const char* SUMMARY_CAPSULE = "je_file_tree._native.summary";
constexpr double SECONDS_PER_DAY = 86400.0;
constexpr int AGE_GROUPS = 5;
constexpr double OLDEST_DAYS[AGE_GROUPS - 1] = {30.0, 182.5, 365.0, 730.0};  // analysis.AGE_GROUPS; the last takes the rest

struct Total {
    long long size = 0;
    long long count = 0;
    long long accounted = 0;
};

struct Candidate {  // a file that may be among the largest; ``order`` is when the walk met it
    long long size = 0;
    long long order = 0;
    PyObject* node = nullptr;
};

// The worst candidate first: the smallest, and of equal ones the one met last.
bool better(const Candidate& left, const Candidate& right) {
    return left.size != right.size ? left.size > right.size : left.order < right.order;
}

struct SummaryState {
    Py_ssize_t limit = 0;
    double now = 0.0;
    bool accounted = false;
    long long seen = 0;
    std::vector<Candidate> largest;  // a heap with the worst candidate at the front
    std::unordered_map<std::wstring, Total> extensions;
    Total ages[AGE_GROUPS];

    ~SummaryState() {
        for (Candidate& candidate : largest) {
            Py_XDECREF(candidate.node);
        }
    }
};

void free_summary(PyObject* capsule) {
    delete static_cast<SummaryState*>(PyCapsule_GetPointer(capsule, SUMMARY_CAPSULE));
}

// summary_new(limit, now, accounted) -> the running summary of one tree
PyObject* summary_new(PyObject*, PyObject* arguments) {
    Py_ssize_t limit = 0;
    double now = 0.0;
    int accounted = 0;
    if (!PyArg_ParseTuple(arguments, "ndp", &limit, &now, &accounted)) {
        return nullptr;
    }
    SummaryState* state = new (std::nothrow) SummaryState();
    if (state == nullptr) {
        return PyErr_NoMemory();
    }
    state->limit = limit;
    state->now = now;
    state->accounted = accounted != 0;
    PyObject* capsule = PyCapsule_New(state, SUMMARY_CAPSULE, free_summary);
    if (capsule == nullptr) {
        delete state;
    }
    return capsule;
}

// analysis.age_of: the first group old enough; times that are not positive fall in the last one.
int age_group(double modified, double now) {
    if (modified <= 0) {
        return AGE_GROUPS - 1;
    }
    double days = (now - modified) / SECONDS_PER_DAY;
    int group = 0;
    while (group < AGE_GROUPS - 1 && OLDEST_DAYS[group] < days) {
        ++group;
    }
    return group;
}

// The counted size of a file: its named size unless it carries ``accounting``.
bool accounted_size(PyObject* file, long long size, long long& value) {
    PyObject* accounting = PyObject_GetAttr(file, node_names.accounting);
    if (accounting == nullptr) {
        return false;
    }
    value = size;
    bool whole = true;
    if (accounting != Py_None) {
        PyObject* first = PySequence_GetItem(accounting, 0);
        value = first != nullptr ? PyLong_AsLongLong(first) : -1;
        whole = first != nullptr && !(value == -1 && PyErr_Occurred());
        Py_XDECREF(first);
    }
    Py_DECREF(accounting);
    return whole;
}

// One file of the walk; false with a Python error set.
bool summary_file(PyObject* file, SummaryState& state) {
    long long size = 0;
    long long counted = 0;
    PyObject* name = PyObject_GetAttr(file, node_names.name);
    PyObject* modified = PyObject_GetAttr(file, node_names.modified);
    double when = modified != nullptr ? PyFloat_AsDouble(modified) : -1.0;
    Py_ssize_t length = 0;
    wchar_t* text = name != nullptr ? PyUnicode_AsWideCharString(name, &length) : nullptr;
    bool whole = text != nullptr && modified != nullptr && !(when == -1.0 && PyErr_Occurred())
        && integer_of(file, node_names.size, size) && (!state.accounted || accounted_size(file, size, counted));
    if (whole) {
        Py_ssize_t dot = length;
        while (dot > 0 && text[dot - 1] != L'.') {
            --dot;
        }
        --dot;  // the last dot, or -1 without one
        Total& extension = state.extensions[dot > 0 && dot < length - 1 ? std::wstring(text + dot, length - dot)
                                                                       : std::wstring()];
        extension.size += size;
        extension.count += 1;
        extension.accounted += counted;
        Total& age = state.ages[age_group(when, state.now)];
        age.size += size;
        age.count += 1;
        Candidate candidate{size, state.seen++, file};
        if (static_cast<Py_ssize_t>(state.largest.size()) < state.limit) {
            Py_INCREF(file);
            state.largest.push_back(candidate);
            std::push_heap(state.largest.begin(), state.largest.end(), better);
        } else if (state.limit > 0 && better(candidate, state.largest.front())) {
            std::pop_heap(state.largest.begin(), state.largest.end(), better);
            Py_DECREF(state.largest.back().node);
            Py_INCREF(file);
            state.largest.back() = candidate;
            std::push_heap(state.largest.begin(), state.largest.end(), better);
        }
    }
    if (text != nullptr) {
        PyMem_Free(text);
    }
    Py_XDECREF(name);
    Py_XDECREF(modified);
    return whole;
}

// summary_step(summary, stack, budget) -> None
//   Takes up to ``budget`` nodes off ``stack`` (a list) as analysis._files_and_extensions does: a link
//   is skipped, a folder's children go on the stack, a file is counted. Call until the stack is empty.
PyObject* summary_step(PyObject*, PyObject* arguments) {
    PyObject* capsule = nullptr;
    PyObject* stack = nullptr;
    Py_ssize_t budget = 0;
    if (!PyArg_ParseTuple(arguments, "OO!n", &capsule, &PyList_Type, &stack, &budget)) {
        return nullptr;
    }
    SummaryState* state = static_cast<SummaryState*>(PyCapsule_GetPointer(capsule, SUMMARY_CAPSULE));
    if (state == nullptr) {
        return nullptr;
    }
    bool whole = true;
    try {
        for (Py_ssize_t taken = 0; whole && taken < budget && PyList_Size(stack) > 0; ++taken) {
            PyObject* node = pop_last(stack);
            int link = node != nullptr ? truth_of(node, node_names.is_link) : -1;
            int folder = link == 0 ? truth_of(node, node_names.is_dir) : 0;
            whole = link >= 0 && folder >= 0;
            if (whole && link == 0 && folder > 0) {
                PyObject* children = PyObject_GetAttr(node, node_names.children);
                Py_ssize_t end = PyList_Size(stack);
                whole = children != nullptr && PyList_SetSlice(stack, end, end, children) == 0;
                Py_XDECREF(children);
            } else if (whole && link == 0) {
                whole = summary_file(node, *state);
            }
            Py_XDECREF(node);
        }
    } catch (const std::bad_alloc&) {
        PyErr_NoMemory();
        whole = false;
    }
    if (!whole) {
        return nullptr;
    }
    Py_RETURN_NONE;
}

// summary_finish(summary) -> (largest files, {extension as written: (size, count, counted size)}, [(size, count)] per age)
PyObject* summary_finish(PyObject*, PyObject* arguments) {
    PyObject* capsule = nullptr;
    if (!PyArg_ParseTuple(arguments, "O", &capsule)) {
        return nullptr;
    }
    SummaryState* state = static_cast<SummaryState*>(PyCapsule_GetPointer(capsule, SUMMARY_CAPSULE));
    if (state == nullptr) {
        return nullptr;
    }
    std::sort(state->largest.begin(), state->largest.end(), better);
    PyObject* largest = PyList_New(0);
    PyObject* extensions = PyDict_New();
    PyObject* ages = PyList_New(0);
    bool whole = largest != nullptr && extensions != nullptr && ages != nullptr;
    for (std::size_t at = 0; whole && at < state->largest.size(); ++at) {
        whole = PyList_Append(largest, state->largest[at].node) == 0;
    }
    for (auto found = state->extensions.begin(); whole && found != state->extensions.end(); ++found) {
        PyObject* key = PyUnicode_FromWideChar(found->first.data(), static_cast<Py_ssize_t>(found->first.size()));
        PyObject* value = Py_BuildValue("(LLL)", found->second.size, found->second.count, found->second.accounted);
        whole = key != nullptr && value != nullptr && PyDict_SetItem(extensions, key, value) == 0;
        Py_XDECREF(key);
        Py_XDECREF(value);
    }
    for (int group = 0; whole && group < AGE_GROUPS; ++group) {
        PyObject* value = Py_BuildValue("(LL)", state->ages[group].size, state->ages[group].count);
        whole = value != nullptr && PyList_Append(ages, value) == 0;
        Py_XDECREF(value);
    }
    if (!whole) {
        Py_XDECREF(largest);
        Py_XDECREF(extensions);
        Py_XDECREF(ages);
        return nullptr;
    }
    return Py_BuildValue("(NNN)", largest, extensions, ages);
}

PyMethodDef methods[] = {
    {"mft_open", mft_open, METH_VARARGS, "Read and index the master file table of an NTFS volume, read-only."},
    {"mft_info", mft_info, METH_VARARGS, "(volume serial number, records, names, damaged records) of a table."},
    {"mft_rows", mft_rows, METH_VARARGS, "The read_folder rows of one folder of a table, by file reference."},
    {"mft_snapshot", mft_snapshot, METH_VARARGS, "The snapshot of one folder of a table, or None."},
    {"local_time_text", local_time, METH_VARARGS,
     "The local time text of export._iso_time for a plain time, or None when Python must format it."},
    {"capacity_new", capacity_new, METH_NOARGS, "The running file totals of one capacity ledger."},
    {"capacity_add", capacity_add, METH_VARARGS, "Add the files among a folder's children; returns the folders."},
    {"capacity_finish", capacity_finish, METH_VARARGS, "(named, unique, bin_seen, foreign, unknown) of a ledger."},
    {"summary_new", summary_new, METH_VARARGS, "The running summary of one tree: (limit, now, accounted)."},
    {"summary_step", summary_step, METH_VARARGS, "Take a bounded number of nodes off the walk's stack."},
    {"summary_finish", summary_finish, METH_VARARGS, "(largest files, totals per extension, totals per age)."},
    {"json_folders", json_folders, METH_VARARGS,
     "Write a bounded number of folders of a tree as the folder JSON of exports and history."},
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
    find_local_clock();
    if (!intern_node_names()
        || PyModule_AddIntConstant(module, "KIND_FILE", KIND_FILE) != 0
        || PyModule_AddIntConstant(module, "KIND_FOLDER", KIND_FOLDER) != 0
        || PyModule_AddIntConstant(module, "KIND_ASK_PYTHON", KIND_ASK_PYTHON) != 0
        || PyModule_AddIntConstant(module, "QUERY_BY_NAME", QUERY_BY_NAME) != 0
        || PyModule_AddIntConstant(module, "QUERY_BY_HANDLE", QUERY_BY_HANDLE) != 0
        || PyModule_AddIntConstant(module, "QUERY_BY_HANDLE_SHORT", QUERY_BY_HANDLE_SHORT) != 0) {
        Py_DECREF(module);
        return nullptr;
    }
    return module;
}
