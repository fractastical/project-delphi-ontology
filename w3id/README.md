# w3id.org registration for `https://w3id.org/delphi/`

The Project Delphi ontology (`delphi:` = `https://w3id.org/delphi/ontology/`) and
resource namespace (`delphir:` = `https://w3id.org/delphi/resource/`) are meant to
dereference, but the redirect is not registered yet (as of 2026-10 both return
404). This folder holds the ready-to-submit redirect rules.

To register, open a pull request against
<https://github.com/perma-id/w3id.org> adding a `delphi/` directory containing
the `.htaccess` file next to this README plus a short `README.md` naming the
contact person. w3id.org requires a named person as contact for every namespace.

Each release is tagged `v<version>` on the commit that releases it (`v1.3`, `v2.0`, `v2.1`, …), so
that a version IRI keeps serving the file as released after `main` moves on. A version IRI whose
tag does not exist yet returns 404 from GitHub.

What the rules do:

| Request | Redirects to |
| --- | --- |
| `/delphi/ontology` from a browser (`Accept: text/html`) | `ONTOLOGY.md` on `main` |
| the same from anything else (Turtle, RDF tools) | the raw `delphi.ttl` on `main` |
| a version IRI, e.g. `/delphi/ontology/2.1`, from a browser | `ONTOLOGY.md` at the git tag `v2.1` |
| the same from anything else | the raw `delphi.ttl` at tag `v2.1` (`probknow.ttl` for `1.3`, before the rename) |
| `/delphi/ontology/<Term>` (e.g. `/ontology/Claim`) from a browser | `ONTOLOGY.md` on GitHub |
| `/delphi/ontology/<Term>` from anything else | the raw `delphi.ttl` |
| `/delphi/resource/<kind>/<id>` | `https://scienceoracle.com/resource/<kind>/<id>` (the resolver scienceoracle.com needs to serve) |
| anything else under `/delphi/` | this repository |

Term IRIs are slash-based and unversioned (`https://w3id.org/delphi/ontology/Claim`),
which is what lets each term redirect on its own; the ontology's version lives only in
`owl:versionIRI`. Earlier `probknow` IRIs (`https://w3id.org/probknow/ontology/<Term>` and
version 1.0 hash terms under `…/probknow/ontology/1.0#`) are mapped to the current
`delphi` terms with `owl:equivalent*` axioms in the ontology crosswalk.
