from pathlib import Path

FORMAT_MATRIX = {
    "images": {
        "extensions": ["png", "jpg", "jpeg", "webp", "svg", "gif", "bmp", "tiff", "tif", "ico", "psd", "eps", "heic", "heif", "ai", "dds", "tga", "raw", "cr2", "nef", "orf", "sr2", "inf", "pbm", "pgm", "ppm", "pnm", "pcx", "wbmp"],
        "targets": ["png", "jpg", "jpeg", "webp", "pdf", "gif", "bmp", "tiff", "ico", "tga"]
    },
    "documents": {
        "extensions": ["pdf", "docx", "doc", "txt", "rtf", "odt", "html", "htm", "xps", "epub", "pages", "md", "tex", "pdfx", "wpd", "wps", "abw", "lwp", "rst", "sdw"],
        "targets": ["pdf", "docx", "txt", "html", "epub", "rtf"]
    },
    "audio": {
        "extensions": ["mp3", "wav", "m4a", "flac", "aac", "ogg", "wma", "amr", "aiff", "aif", "opus", "pcm", "alac", "m4b", "m4p", "mp2", "mp1", "ac3", "dts", "ra", "rm", "voc", "iff", "mka", "wv", "ape", "shn", "cdr", "oga", "mid", "midi"],
        "targets": ["mp3", "wav", "m4a", "flac", "aac", "ogg", "wma", "opus"]
    },
    "video": {
        "extensions": ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "3gp", "mpeg", "mpg", "m4v", "vob", "ogv", "ts", "mts", "m2ts", "divx", "xvid", "rmvb", "asf", "amv", "qt", "f4v", "f4p", "f4a", "f4b", "m2v", "m1v", "svi", "3g2"],
        "targets": ["mp4", "mkv", "avi", "mov", "webm", "mp3", "wav", "gif"]
    },
    "spreadsheets": {
        "extensions": ["xls", "xlsx", "csv", "ods", "tsv", "xlsm", "xltx", "xltm", "xlsb", "xml", "numbers", "dif", "dbf", "slk", "sxc", "fods", "qpw", "wb1", "wb3"],
        "targets": ["xlsx", "csv", "pdf", "ods", "html"]
    },
    "presentations": {
        "extensions": ["ppt", "pptx", "odp", "pps", "ppsx", "pot", "potx", "key", "keynote", "dps", "sda", "sxd", "sti", "otp", "fodp", "uop", "pptm", "potm", "ppsm"],
        "targets": ["pptx", "pdf", "odp", "html"]
    },
    "ebooks": {
        "extensions": ["epub", "mobi", "azw3", "fb2", "lit", "lrf", "prc", "pdb", "pml", "rb", "snb", "tcr", "cbz", "cbr", "cbc", "chm", "djvu", "htmlz", "txtz"],
        "targets": ["epub", "mobi", "pdf", "txt", "azw3"]
    },
    "archives": {
        "extensions": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso", "tgz", "tbz2", "tlz", "txz", "z", "lz", "lzma", "lzh", "arj", "cab", "dmg", "wim", "xar", "zipx", "ace", "apk", "jar", "war", "ear", "cpio", "rpm", "deb"],
        "targets": ["zip", "tar", "gz", "7z"]
    },
    "fonts": {
        "extensions": ["ttf", "otf", "woff", "woff2", "eot", "sfnt", "pfa", "pfb", "afm", "bin", "bdf", "pcf", "pmf", "ttf.vfont", "otc", "suit", "ttc", "dfont", "snf", "gxf"],
        "targets": ["ttf", "otf", "woff", "woff2"]
    },
    "vectors": {
        "extensions": ["svg", "ai", "eps", "cdr", "wmf", "emf", "dxf", "dwg", "plt", "cgm", "svgz", "fxg", "pdfa", "fig", "sk", "sk1", "skencil", "vml", "xarv", "hpgl"],
        "targets": ["svg", "png", "pdf", "eps"]
    },
    "cad_3d": {
        "extensions": ["stl", "obj", "fbx", "3ds", "dae", "ply", "iges", "step", "stp", "blend", "c4d", "ma", "mb", "max", "lwo", "lws", "lxo", "skp", "wrz", "wrl", "x3d"],
        "targets": ["stl", "obj", "fbx", "dxf"]
    }
}


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def get_allowed_targets(filename: str) -> list[str]:
    ext = get_extension(filename)
    for config in FORMAT_MATRIX.values():
        if ext in config["extensions"]:
            return config["targets"]
    return []


def get_category(filename: str) -> str | None:
    ext = get_extension(filename)
    for category, config in FORMAT_MATRIX.items():
        if ext in config["extensions"]:
            return category
    return None
