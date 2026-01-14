
from importlib.metadata import version, PackageNotFoundError
from packaging.requirements import Requirement

def check_requirements(requirements_file="requirements.txt"):
    """
    Validate installed packages against version specifiers in requirements_file.
    - Skips pip directives (-r, -c, -e, --options)
    - Skips VCS/URL/direct references (git+, http(s)://, file:, path-like)
    - Strips inline comments after requirements
    Raises RuntimeError on the first mismatch/missing package.
    """
    def is_pip_directive(line: str) -> bool:
        return (
            line.startswith(("-r", "-c", "-e", "--"))  # include pip options
        )

    def is_direct_reference(line: str) -> bool:
        # PEP 508 supports "name @ url", but many requirement files also include
        # bare URLs/VCS/paths that pip understands. We'll skip these for runtime checking.
        return (
            " @" in line or
            line.startswith(("git+", "http://", "https://", "file:", "/")) or
            line.endswith(".whl")
        )

    with open(requirements_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue  # skip blank lines and full-line comments

            if is_pip_directive(line) or is_direct_reference(line):
                continue  # skip lines that importlib/packaging can't validate cleanly

            # Strip inline comments: everything after ' #' or '  #' is treated as a comment
            # (avoids stripping '#' inside most URLs, since we already skip URL lines above)
            # If your file uses comments without preceding space, use split('#', 1)[0] instead.
            if " #" in line:
                line = line.split(" #", 1)[0].rstrip()

            # Now parse the requirement
            try:
                req = Requirement(line)
            except Exception as e:
                raise RuntimeError(f"Cannot parse requirement line: {raw_line.strip()}\nReason: {e}")

            # Respect environment markers (e.g., ; python_version < "3.11")
            if req.marker and not req.marker.evaluate():
                continue

            # Check installed version
            try:
                installed_version = version(req.name)
            except PackageNotFoundError:
                raise RuntimeError(f"Missing package: {req.name} (required: {req.specifier or 'any'})")

            # Validate version against the specifier
            if req.specifier and not req.specifier.contains(installed_version, prereleases=True):
                raise RuntimeError(
                    f"{req.name}=={installed_version} does not satisfy {req.specifier}"
                )

   


