import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import pandas as pd
from pydantic import BaseModel

from src.foundation.llm.llm_provider import LLMProvider


_MAX_RETRIES = 3

_SYSTEM_PROMPT = """
You are an expert resume parser.

Your job is to extract all professional experiences from resumes.

Rules:

1. Return experiences ordered from most recent to oldest.

2. Every experience must contain:
   - company (if not found, infer a plausible name from the industry — never use "Company Name")
   - job_title
   - details
   - start_date
   - end_date

3. Dates MUST use format: DD/MM/YYYY

4. If some information is missing, infer plausible values from context.

5. Inferred dates must always make chronological sense.

6. end_date must always be later than start_date.

7. If the role is ongoing, end_date can be null or "Current".

8. Never return overlapping impossible dates.

9. Ensure career progression is realistic.

10. Return JSON only.
"""


class WorkExperience(BaseModel):
    company: str
    job_title: str
    details: str
    start_date: str
    end_date: Optional[str]


class ParsedExperiences(BaseModel):
    experiences: list[WorkExperience]


class ResumeParser:

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    def parse(self, resume_text: str) -> list[WorkExperience]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                result = self._llm.structured_generate(
                    prompt=resume_text,
                    schema=ParsedExperiences,
                    system_prompt=_SYSTEM_PROMPT,
                )
                return result.experiences
            except Exception as e:
                last_error = e
                print(f"[retry {attempt + 1}/{_MAX_RETRIES}] {type(e).__name__}: {e}")
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** attempt + random.random())
        raise last_error

    def enrich_dataframe(
        self,
        df: pd.DataFrame,
        content_col: str = "content",
        id_col: str = "id",
        output_col: str = "full_experience",
        max_workers: int = 1,
        checkpoint_path: str | None = None,
        checkpoint_every: int = 50,
    ) -> pd.DataFrame:
        df = df.copy()
        total = len(df)

        # Load checkpoint — skip already-processed candidates
        cache: dict[str, list] = {}
        if checkpoint_path and os.path.exists(checkpoint_path):
            with open(checkpoint_path, encoding="utf-8") as f:
                for rec in json.load(f):
                    cache[str(rec[id_col])] = rec[output_col]
            print(f"[checkpoint] {len(cache)}/{total} já processados — retomando")

        def _parse_one(args: tuple) -> tuple[str, list, str]:
            row_idx, candidate_id, content = args
            key = str(candidate_id)
            if key in cache:
                return row_idx, candidate_id, cache[key], "cached"
            try:
                parsed = self.parse(content)
                exp = [e.model_dump() for e in parsed]
                return row_idx, candidate_id, exp, "ok" if exp else "empty"
            except Exception as e:
                return row_idx, candidate_id, [], f"failed: {type(e).__name__}"

        rows = [
            (i, row[id_col], row[content_col])
            for i, (_, row) in enumerate(df.iterrows())
        ]

        result_map: dict[int, list] = {}
        success = failure = cached = 0
        pipeline_start = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_parse_one, r): r[0] for r in rows}

            for done_count, future in enumerate(as_completed(futures), 1):
                row_idx, candidate_id, exp, status = future.result()
                result_map[row_idx] = exp

                if status == "cached":
                    cached += 1
                elif status == "ok":
                    success += 1
                else:
                    failure += 1

                elapsed = time.time() - pipeline_start
                eta = (elapsed / done_count) * (total - done_count)
                print(
                    f"[{done_count}/{total} | {done_count / total * 100:.1f}%] "
                    f"id={candidate_id} | {status} | "
                    f"ok={success} cached={cached} fail={failure} | eta={eta / 60:.1f}m"
                )

                # Save checkpoint periodically
                if checkpoint_path and done_count % checkpoint_every == 0:
                    self._save_checkpoint(checkpoint_path, id_col, output_col, rows, result_map)
                    print(f"  [checkpoint → {checkpoint_path}]")

        # Final checkpoint
        if checkpoint_path:
            self._save_checkpoint(checkpoint_path, id_col, output_col, rows, result_map)

        df[output_col] = [result_map[i] for i in range(total)]
        print(
            f"\n[DONE] total={total} ok={success} cached={cached} fail={failure} "
            f"elapsed={(time.time() - pipeline_start) / 60:.1f}m"
        )
        return df

    @staticmethod
    def _save_checkpoint(
        path: str,
        id_col: str,
        output_col: str,
        rows: list[tuple],
        result_map: dict[int, list],
    ) -> None:
        records = [
            {id_col: str(candidate_id), output_col: result_map[row_idx]}
            for row_idx, candidate_id, _ in rows
            if row_idx in result_map
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False)
