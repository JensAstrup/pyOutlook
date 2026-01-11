# Distribution Guide

This guide covers how to build, upload, and distribute new versions of pyOutlook to PyPI and update documentation on Read the Docs.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Pre-Release Checklist](#pre-release-checklist)
- [Uploading to PyPI with Twine](#uploading-to-pypi-with-twine)
- [Generating and Uploading Documentation to Read the Docs](#generating-and-uploading-documentation-to-read-the-docs)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before distributing a new version, ensure you have the following installed:

```bash
# Install build tools
pip install build twine

# Install documentation dependencies
pip install -r requirements.dev.txt
```

You'll also need:
- Access to the PyPI account for `pyOutlook`
- Access to the Read the Docs project for `pyoutlook`

## Pre-Release Checklist

Before uploading a new version:

1. **Update the version number** in `pyproject.toml`:
   ```toml
   [project]
   version = "5.0.2"  # Update to new version
   ```

2. **Run the test suite** to ensure everything passes:
   ```bash
   pytest
   ```

3. **Update CHANGELOG or release notes** (if maintained)

4. **Ensure all changes are committed** to your version control system

5. **Build the documentation locally** to verify it generates correctly:
   ```bash
   cd docs
   make html
   ```

## Uploading to PyPI with Twine

### Step 1: Clean Previous Builds

Remove any existing build artifacts:

```bash
# Remove old distributions
rm -rf dist/*
rm -rf build/*
rm -rf src/*.egg-info
```

### Step 2: Build the Package

Build both wheel and source distributions:

```bash
# Build the package
python -m build
```

This will create:
- `dist/pyOutlook-X.Y.Z-py3-none-any.whl` (wheel distribution)
- `dist/pyOutlook-X.Y.Z.tar.gz` (source distribution)

### Step 3: Verify the Build

Check that the built package contains the expected files:

```bash
# List contents of the wheel
python -m zipfile -l dist/pyOutlook-*.whl

# List contents of the source distribution
tar -tzf dist/pyOutlook-*.tar.gz | head -20
```

### Step 4: Test Upload to TestPyPI (Recommended)

Before uploading to production PyPI, test with TestPyPI:

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: Your TestPyPI API token (pypi-...)
```

Test the package from TestPyPI:

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pyOutlook==X.Y.Z
```

### Step 5: Upload to Production PyPI

Once verified, upload to the production PyPI:

```bash
# Upload to PyPI
python -m twine upload dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: Your PyPI API token (pypi-...)
```

**Note**: PyPI API tokens should be created at https://pypi.org/manage/account/token/

### Step 6: Verify the Upload

Check that your package appears on PyPI:

1. Visit https://pypi.org/project/pyOutlook/
2. Verify the new version is listed
3. Test installation:
   ```bash
   pip install --upgrade pyOutlook
   ```

## Generating and Uploading Documentation to Read the Docs

Read the Docs can automatically build documentation from your repository, but you can also build and verify locally before pushing.

### Step 1: Build Documentation Locally

Generate the HTML documentation:

```bash
cd docs
make html
```

The built documentation will be in `docs/build/html/`.

### Step 2: Verify Documentation Locally

Open the built documentation in your browser:

```bash
# On macOS
open docs/build/html/index.html

# On Linux
xdg-open docs/build/html/index.html

# On Windows
start docs/build/html/index.html
```

Verify that:
- All pages render correctly
- API documentation is complete
- No broken links (you can check with `make linkcheck`)

### Step 3: Commit and Push Changes

If you've made documentation changes, commit and push them:

```bash
git add docs/
git commit -m "Update documentation for version X.Y.Z"
git push origin main  # or your release branch
```

### Step 4: Trigger Read the Docs Build

Read the Docs typically builds automatically when you push to your repository. To manually trigger a build:

1. Go to https://readthedocs.org/projects/pyoutlook/
2. Navigate to **Builds** → **Build Version**
3. Select the branch/version you want to build
4. Click **Build**

### Step 5: Verify Documentation on Read the Docs

1. Wait for the build to complete (usually 1-5 minutes)
2. Visit http://pyoutlook.readthedocs.io/en/latest/
3. Verify all content is correct and up-to-date

### Advanced: Building Documentation for Multiple Versions

If you want to maintain documentation for multiple versions:

1. In Read the Docs dashboard, go to **Admin** → **Versions**
2. Enable versions you want to maintain
3. Each version will build automatically when you tag releases

To tag a release:

```bash
git tag -a v5.0.2 -m "Release version 5.0.2"
git push origin v5.0.2
```

## Troubleshooting

### Build Errors

**Error: `ModuleNotFoundError` during build**

- Ensure all dependencies are listed in `pyproject.toml` under `[project.dependencies]`
- Check that import paths are correct

**Error: `InvalidVersion` or version format errors**

- Verify version number in `pyproject.toml` follows PEP 440 (e.g., `5.0.2`, not `v5.0.2`)

### Twine Upload Errors

**Error: `HTTPError: 403 Forbidden`**

- Verify your PyPI API token is correct
- Ensure you're using `__token__` as the username (with underscores, not hyphens)
- Check that your token hasn't expired

**Error: `HTTPError: 400 File already exists`**

- The version you're trying to upload already exists on PyPI
- Increment the version number in `pyproject.toml`

### Documentation Build Errors

**Error: Sphinx build warnings/errors**

- Check for syntax errors in `.rst` files
- Verify all referenced modules exist
- Run `make linkcheck` to find broken links

**Read the Docs build fails**

- Check the build log in the Read the Docs dashboard
- Verify `requirements.txt` or `docs/requirements.txt` includes Sphinx and dependencies
- Ensure the Python version in Read the Docs settings matches your local environment

### Verification Issues

**Package installs but imports fail**

- Verify `__init__.py` files exist in all packages
- Check that package structure matches `[tool.setuptools.packages.find]` in `pyproject.toml`

**Documentation missing modules**

- Ensure `sphinx-apidoc` has been run to generate API documentation
- Check that all modules are included in `docs/source/pyOutlook.rst`

## Additional Resources

- [PyPI Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Read the Docs Documentation](https://docs.readthedocs.io/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
