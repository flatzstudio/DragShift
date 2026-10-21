# Third-Party Notices

## FFmpeg

DragShift bundles FFmpeg 7.1 from the pinned `imageio-ffmpeg==0.6.0` Python
distribution. The macOS arm64 binary is obtained at build time with
`imageio_ffmpeg.get_ffmpeg_exe()` and included in the application bundle. The
binary identifies itself as `ffmpeg-macos-aarch64-v7.1`. Its `-version`,
`-buildconf` and `-L` outputs report FFmpeg 7.1, the configuration below, and
GNU GPL version 2 or later respectively. The upstream build enables `--enable-gpl` and
`libx264`, `libx265`, `libvpx`, `libmp3lame`, `libopus`, `libvorbis`, `libaom`
and `libsvtav1`; the binary reports GPL-2.0-or-later, not GPLv3.

Verified configure options (the complete `ffmpeg -buildconf` output should be
archived with any release source bundle):

```text
--enable-gpl --enable-libvmaf --enable-libopenjpeg --enable-libopus
--enable-libmp3lame --enable-libx264 --enable-libx265 --enable-libvpx
--enable-libwebp --enable-libass --enable-libfreetype --enable-fontconfig
--enable-libtheora --enable-libvorbis --enable-libsnappy --enable-libaom
--enable-libvidstab --enable-libzimg --enable-libsvtav1 --enable-libharfbuzz
--enable-libkvazaar --enable-ffplay --enable-postproc --enable-neon
--enable-runtime-cpudetect --disable-indev=qtkit --disable-indev=x11grab_xcb
```

FFmpeg project: <https://ffmpeg.org/>
FFmpeg source: <https://git.ffmpeg.org/ffmpeg.git>
GPL version 2 license: <https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt>
Pinned provider source: <https://github.com/imageio/imageio-ffmpeg/tree/v0.6.0>
Binary repository: <https://github.com/imageio/imageio-binaries/tree/master/ffmpeg>
Pinned provider package: <https://pypi.org/project/imageio-ffmpeg/0.6.0/>

The `imageio-ffmpeg` Python wrapper is BSD-2-Clause; its platform-specific
wheel carries the separate FFmpeg executable. The FFmpeg binary was built with
GPL-enabled external codecs. The build configuration alone is not the complete
corresponding source: exact FFmpeg source, versions/source for the linked
external libraries, patches, and the scripts/environment needed to reproduce
the binary have not been collected or verified for this build. The upstream
`imageio-binaries` repository contains the binary but is not itself a source
archive for those components.

This is a compliance status notice, not legal advice. FFmpeg's legal page says
that `--enable-gpl` changes FFmpeg's license to GPL-2.0-or-later. If the FFmpeg
executable is redistributed, the distributor must satisfy the applicable GPL
source/offer terms for that executable and its covered components. This does
not by itself relicense DragShift's separate MIT-licensed source; do not
represent the whole bundle as MIT-only. Complete corresponding-source materials
for this build are missing, so publishing an app binary containing it is
blocked. Source-only publication of this repository does not include the
ignored `.app`/FFmpeg binaries; installing its pinned Python dependency obtains
the provider wheel separately from PyPI.

The repository license and notices do not establish that codec patent rights
are cleared. Patent obligations may vary by codec and jurisdiction.

## Python dependencies and tools

The dependency constraints in `requirements.txt` are mostly open lower bounds,
not a lock file. The versions below are a local inventory snapshot from the
macOS arm64/Python 3.12 environment used for this review; they do not establish
the versions installed by another user, platform, CI run, or future build.
License labels were read from installed distribution metadata and checked
against project documentation where linked. Metadata is an inventory aid, not
a substitute for preserving each exact distribution's license and notices.

| Component (snapshot version) | License information | Scope / unresolved items |
|---|---|---|
| PyMuPDF (2.0) | AGPL-3.0 or Artifex commercial license | Imported by the app. No commercial grant has been established. Resolve the applicable license and obligations before distributing the application; source publication does not itself settle this question. [Project licensing](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) |
| PyMuPDF4LLM (2.0), PyMuPDF_layout (2.0) | Not identified in installed wheel metadata; wheel had no license file | Transitive PyMuPDF dependencies. Verify authoritative license terms for the exact distributions and their MuPDF components. |
| PySide6, PySide6_Addons, PySide6_Essentials, shiboken6 (6.12.0) | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only in package metadata | App uses PySide6. Qt libraries, plugins, and PyInstaller bundle contents were not completely inventoried; license selection and LGPL/GPL compliance remain unreviewed. [Qt for Python license guidance](https://doc.qt.io/qtforpython-6/licenses.html) |
| Pillow (13.0.0) | MIT-CMU in package metadata | Pillow may include native codec libraries; inventory and retain notices from the exact platform wheel. |
| pillow-heif (1.8.1) | BSD-3-Clause in package metadata | Wheel also includes `LICENSES_bundled.txt`; audit the bundled native components and retain both license files. |
| NumPy (2.5.4) | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | Multiple third-party components have separate notices in the wheel. Preserve the complete license directory. |
| python-docx (1.2.0) | MIT | Preserve its copyright and permission notice. |
| lxml (6.1.3) | BSD-3-Clause | Transitive dependency; preserve its notice and audit bundled libxml2/libxslt components in the exact wheel. |
| PyObjC core, Cocoa, Quartz (12.2.2) | MIT | macOS-only; preserve copyright and permission notices. |
| imageio-ffmpeg (0.6.0) | BSD-2-Clause | Python wrapper only; does not replace the separate FFmpeg terms above. |
| networkx (3.7), onnxruntime (1.31.0), PyYAML (6.0.3), psutil (7.2.2), tabulate (0.10.0) | BSD-3-Clause, MIT, MIT, BSD-3-Clause, MIT respectively, per installed metadata | Present in the local environment as transitive dependencies. ONNX Runtime includes a `ThirdPartyNotices.txt`; retain it and review native components if included in a build. |
| PyInstaller (6.22.3) | GPL-2.0-or-later with a special exception for distributing applications built with it; certain files are Apache-2.0 | Build tool, not an app runtime license. The exception does not override the licenses of bundled dependencies. [License](https://pyinstaller.org/en/stable/license.html) |
| pytest (9.1.1), altgraph (0.17.5), macholib (1.16.4), pyinstaller-hooks-contrib (2026.8) | MIT, MIT, MIT, not identified in installed metadata respectively | Test/build tooling, generally not shipped as app runtime. Confirm exact licenses for any redistributed tooling or included files. |

The local environment also contains PyInstaller/pytest transitive packages that
are not necessarily included in a release. This table is deliberately not a
complete SBOM: it does not establish the exact dependency graph for each target,
all system libraries, Qt plugins, native wheel contents, or what PyInstaller
collects. Generate and review a platform-specific inventory from each final
build, then include all applicable license texts and notices before publishing
binaries. CI also installs platform system packages (including a separate
system FFmpeg on Linux) that are not represented by `requirements.txt`.

The MIT license applies to DragShift's own code only. This notice is an
inventory-in-progress, not legal advice or a representation that the source or
application bundle is license-cleared. Resolve the PyMuPDF/related packages and
Qt license choices before determining the terms for redistributing the
application. Resolve FFmpeg corresponding-source requirements before shipping
any bundle containing that executable.

## Sources and scope

- [PyMuPDF license and copyright](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright)
- [Qt for Python licenses](https://doc.qt.io/qtforpython-6/licenses.html)
- [PyInstaller license and exception](https://pyinstaller.org/en/stable/license.html)
- [imageio-ffmpeg v0.6.0 license](https://github.com/imageio/imageio-ffmpeg/blob/v0.6.0/LICENSE)
- Installed wheel metadata and license files in the local macOS arm64/Python 3.12 environment described above.

Upstream DragShift license: MIT; retain `LICENSE` and its copyright/permission
notice. See `LICENSE`.
