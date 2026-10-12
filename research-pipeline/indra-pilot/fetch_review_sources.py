"""Cache public paper metadata/abstracts for the frozen pilot; never write imports."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import urlopen


def fetch(sample, out):
    out.mkdir(parents=True, exist_ok=True)
    for paper in sample["papers"]:
        target = out / (paper["id"].split(":")[-1] + ".json")
        if target.exists():
            continue
        refs = dict(r.split(":", 1) for r in paper["references"])
        query = (f'EXT_ID:{refs["PMID"]} AND SRC:MED' if "PMID" in refs else
                 f'PMCID:{refs["PMCID"]}' if "PMCID" in refs else f'DOI:"{refs["DOI"]}"')
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode(
            {"query": query, "format": "json", "resultType": "core"})
        record = {"paperId": paper["id"], "requestedReferences": paper["references"],
                  "url": url, "retrievedAt": datetime.now(timezone.utc).isoformat()}
        try:
            data = urlopen(url, timeout=40).read()
            results = json.loads(data)["resultList"]["result"]
            record.update(responseSha256=hashlib.sha256(data).hexdigest(),
                          results=results, status="retrieved" if results else "not_found")
        except Exception as exc:
            record.update(status="unavailable", error=str(exc))
        target.write_text(json.dumps(record, indent=2))
        print(target.stem[:8], record["status"], flush=True)
        time.sleep(.12)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fetch(json.loads(args.sample.read_text()), args.out)
