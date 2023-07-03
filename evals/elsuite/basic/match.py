from typing import Any

import evals
import evals.metrics
from evals.api import CompletionFn
from evals.prompt.base import is_chat_prompt
import re

class Match(evals.Eval):
    def __init__(
        self,
        completion_fns: list[CompletionFn],
        samples_jsonl: str,
        *args,
        max_tokens: int = 500,
        num_few_shot: int = 0,
        few_shot_jsonl: str = None,
        **kwargs,
    ):
        super().__init__(completion_fns, *args, **kwargs)
        assert len(completion_fns) == 1, "Match only supports one completion fn"
        self.max_tokens = max_tokens
        self.samples_jsonl = samples_jsonl
        self.num_few_shot = num_few_shot
        if self.num_few_shot > 0:
            assert few_shot_jsonl is not None, "few shot requires few shot sample dataset"
            self.few_shot_jsonl = few_shot_jsonl
            self.few_shot = evals.get_jsonl(self.few_shot_jsonl)

    def eval_sample(self, sample: Any, *_):
        prompt = sample["input"]
        print(prompt)
        if self.num_few_shot > 0:
            assert is_chat_prompt(sample["input"]), "few shot requires chat prompt"
            prompt = sample["input"][:-1]
            for s in self.few_shot[: self.num_few_shot]:
                prompt += s["sample"]
            prompt += sample["input"][-1:]

        result = self.completion_fn(
            prompt=prompt,
            temperature=0.0,
        )
        sampled = result.get_completions()[0]
        
        
        pattern = r"<result>(.*?)<\/result>"
        print(sampled)
        match = re.search(pattern, sampled)

        if match:
            result_word = match.group(1)
            # Convert the word to lowercase
            sampled = result_word.lower()
            # Add the <result> tags to the final word
        else:
            sampled = ""
        q = evals.record_and_check_match(
            prompt=prompt,
            sampled=sampled,
            expected=sample["ideal"],
        )
        #print(q)
        return q

    def run(self, recorder):
        samples = self.get_samples()
        self.eval_all_samples(recorder, samples)
        events = recorder.get_events("match")
        print(events)
        return {
            "accuracy": evals.metrics.get_accuracy(events),
        }
