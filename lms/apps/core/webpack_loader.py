from webpack_loader.loader import WebpackLoader

from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.functional import cached_property
from pathlib import Path
import json


class BundleDirectoryWebpackLoader(WebpackLoader):
    """
    Returns chunk url relative to the bundle directory ignoring public path.
    """
    def get_chunk_url(self, chunk):
        rel_path = '{0}{1}'.format(self.config['BUNDLE_DIR_NAME'],
                                   chunk['name'])
        return staticfiles_storage.url(rel_path)


class TestingWebpackLoader(WebpackLoader):
    def get_bundle(self, bundle_name):
        """
        Mocks `render_bundle` template tag to avoid WebpackBundleLookupError
        on running tests.

        The name and URL don't matter, the file doesn't need to exist.
        """
        return [{'name': 'test.bundle.js', 'url': 'https://localhost:8000/static/bundles/test.bundle.js'}]


class ViteManifestLoader(WebpackLoader):
    """
    Adapter that lets django-webpack-loader consume Vite's manifest.json.
    """

    @cached_property
    def _manifest(self):
        try:
            with open(self.config["STATS_FILE"], encoding="utf-8") as f:
                return json.load(f)
        except IOError as exc:  # pragma: no cover - delegated to parent error path
            raise IOError(
                "Error reading {0}. Are you sure vite has generated "
                "the manifest and the path is correct?".format(self.config["STATS_FILE"])
            ) from exc

    def load_assets(self):
        manifest = self._manifest

        assets = {}
        chunks = {}

        def register_asset(path_str):
            if path_str not in assets:
                assets[path_str] = {"name": path_str}

        def collect_imports(entry_key, seen):
            collected = []
            entry = manifest.get(entry_key, {})
            for imp in entry.get("imports", []):
                if imp in seen:
                    continue
                seen.add(imp)
                imp_entry = manifest.get(imp, {})
                imp_file = imp_entry.get("file")
                if imp_file:
                    register_asset(imp_file)
                    collected.append(imp_file)
                for css_path in imp_entry.get("css", []):
                    register_asset(css_path)
                    collected.append(css_path)
                collected.extend(collect_imports(imp, seen))
            return collected

        for key, entry in manifest.items():
            if not entry.get("isEntry"):
                continue

            entry_file = entry.get("file")
            if not entry_file:
                continue

            register_asset(entry_file)

            bundle_name = entry.get("name") or Path(key).stem
            chunk_files = [entry_file]

            # Include imported chunks so render_bundle can emit vendor/code-split files.
            chunk_files.extend(collect_imports(key, set()))

            # Also include CSS emitted for this entry to allow extension filtering.
            for css_path in entry.get("css", []):
                register_asset(css_path)
                chunk_files.append(css_path)

            # Extra assets (images/fonts) referenced from this entry.
            for asset_path in entry.get("assets", []):
                register_asset(asset_path)
                chunk_files.append(asset_path)

            chunks[bundle_name] = chunk_files

        return {"status": "done", "chunks": chunks, "assets": assets}
