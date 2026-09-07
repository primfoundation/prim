# Foundation bootstrap reference tools

These additions do not replace the existing TypeScript SDK or the independent
`sdk-python` branch. They make the first profile-publication and delivery-record
contracts executable locally before production integration.

Use Python 3.11 or later and install `tools/requirements.txt` in an environment
you control. The recorded local run used Linux, Python 3.13.5, and PyYAML 6.0.3;
other runtimes/platforms have not been established by that result.

- `profile_catalog.py`: inspect a PROFILE.md package or discover packages from a
  selected local root; never fetches, installs, or executes profile code.
- `program.py`: check the program ledger; generate or check ROADMAP.md.
- `verify.py`: run the actual local checks and retain outputs/input hashes.

From the repository root:

```bash
python -m pip install -r tools/requirements.txt
python tools/verify.py
```

Use `python tools/program.py render` to deliberately regenerate the roadmap and
`python tools/profile_catalog.py discover profiles --output registry/profiles.generated.json`
to regenerate the development catalog. Verification checks drift; it does not
quietly rewrite the catalog to make a failing check pass.

The generated development catalog is separate from the legacy registry. No
existing app consumes it automatically. Inspect program/PROFILE-PACKAGE.md and
program/PLAN-FORMAT.md for contracts and limits. In particular, a manifest digest
is not a full package digest, and metadata conformance is not instance validity,
factual accuracy, publisher authentication, or a security review.

## Current verification runner

The original program/evidence/local-tests.json is retained as historical evidence.
New runs write tools/.verification/report.json unless --output is supplied.
Use python tools/verify.py --with-sdk in a complete checkout to also request the
existing TypeScript SDK command. Each command's actual exit status is retained;
publication and deployment state are not guessed from local test success.
