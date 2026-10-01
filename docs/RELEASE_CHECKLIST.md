# Release Checklist

## Product verification

- [ ] Run `ruff format --check .`.
- [ ] Run `ruff check .`.
- [ ] Run `pytest`.
- [ ] Run `python -m compileall -q src`.
- [ ] Launch `lasergrbl-macos --demo` and complete a simulated job.
- [ ] Verify connection, status, jog, pause, resume, and abort against supported hardware.
- [ ] Generate G-code from a small grayscale image and review the path.
- [ ] Open and save a G-code file.
- [ ] Test the packaged `.app` on a clean macOS account.

## Safety and documentation

- [ ] Review the safety warning and `docs/SAFETY.md`.
- [ ] Confirm that user-visible behavior matches the README.
- [ ] Update `CHANGELOG.md` and `ROADMAP.md`.
- [ ] Confirm the version in `pyproject.toml`, `src/lasergrbl_macos/__init__.py`, and the PyInstaller spec.
- [ ] Regenerate the interface screenshot if the layout changed.

## GitHub release

- [ ] Merge the release changes to `main`.
- [ ] Confirm CI and Security workflows pass.
- [ ] Create an annotated version tag such as `v0.2.0`.
- [ ] Push the tag and wait for the macOS Release workflow.
- [ ] Download and verify the generated zip and SHA-256 checksum.
- [ ] Edit the generated release notes into a user-focused summary.
- [ ] Mark pre-1.0 releases as pre-releases when appropriate.

## Promotion

- [ ] Upload `assets/social-preview.png` in repository settings.
- [ ] Set the repository description, website, and topics from `docs/PROMOTION_KIT.md`.
- [ ] Enable GitHub Pages with GitHub Actions and run the `GitHub Pages` workflow.
- [ ] Publish the release announcement.
- [ ] Open or update the hardware compatibility feedback issue.
- [ ] Monitor issues for installation and safety-critical reports.
