# UEFN Scene Graph

UEFN Scene Graph entities, components, prefabs. Bundles the scenegraph skill.

Desktop plugin for [UEFN-Ducky](https://github.com/UEFN-Ducky/UEFN-Ducky) (`scenegraph`).
Install or update from **Settings → Store** in the app — do not install from a zip by hand.

## Build

The Store ships this plugin compiled and signed (UEFN Ducky 1.2.357 or newer):

```bash
py scripts/release.py --publish --changelog "…"   # commit + push, compiled build, upload, publish
py scripts/build_zip.py --compiled                 # compiled zip only, to test
py scripts/build_zip.py                            # readable zip (release.py --plain ships it: escape hatch only)
```

Builds go only through the UEFN Ducky build engine (the UEFN-Ducky checkout next to this repo, or `DUCKY_REPO`), never Nuitka or zig by hand. The engine builds for every x86-64 CPU and then disassembles the backend: it refuses a build with AVX, AVX-512, BMI or any other instruction some PCs lack, and so does the Store on upload. Skills ship as files and load in both builds.

Before a release, install the readable and the compiled zip into a throwaway Ducky and check both register the same tools and workflow nodes, and that they still work after the plugin reloads. After it, check the download with the start-up license check (signature, id and version, compiled), not only the signature.

## License

MIT. Copyright (c) 2026 Mindful Path Company, LLC. See [LICENSE](LICENSE).
