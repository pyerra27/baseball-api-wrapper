# Releasing

Releases are built and published by [`.github/workflows/release.yml`](.github/workflows/release.yml). PyPI trusts that workflow directly (trusted publishing), so no API token is needed.

## Steps

1. **Bump the version.** Open a PR that sets `version` in `pyproject.toml` (the only place it lives) to the new `X.Y.Z`. CI runs ruff and pytest on Python 3.10–3.14. Merge it.
2. **Publish a GitHub Release** with the tag `vX.Y.Z` targeting `main`, and write the release notes there. Either:
   - on GitHub, go to Releases → Draft a new release, create the tag, then Publish; or
   - run `gh release create vX.Y.Z --target main --title "X.Y.Z" --notes "..."`
3. **Wait for the build.** The workflow checks that the tag matches the `pyproject.toml` version, then runs ruff, pytest, `python -m build` and `twine check`.
4. **Approve the upload.** The *Publish to PyPI* job waits on the `pypi` environment. Open the run in the Actions tab, then click Review deployments → Approve.
5. **Done.** The package goes to PyPI and the wheel and sdist are attached to the GitHub release.

## Dry run

To check that a release would build, without publishing anything:

```bash
gh workflow run release.yml --ref main
```

## If something goes wrong

- **The tag doesn't match the version, or the build or tests fail.** Nothing has been uploaded yet. Delete the release and its tag (`gh release delete vX.Y.Z --cleanup-tag`), fix `main`, and publish the release again.
- **You reject the deployment.** As above, nothing was uploaded.
- **The publish job fails after approval.** Check whether the version reached PyPI. If it didn't, re-run the failed jobs from the Actions tab. If it did, re-run only *Attach files to GitHub release*. A version number can never be uploaded to PyPI twice.

## One-time setup (already done)

- **PyPI:** baseball-api-wrapper → Publishing has a trusted publisher with owner `pyerra27`, repository `baseball-api-wrapper`, workflow `release.yml` and environment `pypi`.
- **GitHub:** Settings → Environments → `pypi` requires approval from `pyerra27` and only allows tags matching `v*`.
