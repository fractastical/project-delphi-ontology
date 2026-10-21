# w3id.org registration for `https://w3id.org/delphi/`

The Project Delphi ontology (`pk:` = `https://w3id.org/delphi/ontology/`) and
resource namespace (`pkr:` = `https://w3id.org/delphi/resource/`) are meant to
dereference, but the redirect is not registered yet (as of 2026-10 both return
404). This folder holds the ready-to-submit redirect rules.

To register, open a pull request against
<https://github.com/perma-id/w3id.org> adding a `delphi/` directory containing
the `.htaccess` file next to this README plus a short `README.md` naming the
contact person. w3id.org requires a named person as contact for every namespace.

What the rules do:

| Request | Redirects to |
| --- | --- |
| `/delphi/ontology` or `/delphi/ontology/1.3` from a browser (`Accept: text/html`) | `ONTOLOGY.md` on GitHub |
| the same from anything else (Turtle, RDF tools) | the raw `probknow.ttl` on GitHub |
| `/delphi/ontology/<Term>` (e.g. `/ontology/Claim`) from a browser | `ONTOLOGY.md` on GitHub |
| `/delphi/ontology/<Term>` from anything else | the raw `probknow.ttl` |
| `/delphi/resource/<kind>/<id>` | `https://scienceoracle.com/resource/<kind>/<id>` (the resolver scienceoracle.com needs to serve) |
| anything else under `/delphi/` | this repository |

Term IRIs are slash-based and unversioned (`https://w3id.org/delphi/ontology/Claim`),
which is what lets each term redirect on its own; the ontology's version lives only in
`owl:versionIRI`. Earlier `probknow` IRIs (`https://w3id.org/probknow/ontology/<Term>` and
version 1.0 hash terms under `…/probknow/ontology/1.0#`) are mapped to the current
`delphi` terms with `owl:equivalent*` axioms in the ontology crosswalk.
