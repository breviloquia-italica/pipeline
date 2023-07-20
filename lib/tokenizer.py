# Setup custom tokenizer.

import re
import spacy
from spacy.lang.it import Italian

tokenizer = Italian().tokenizer

# NOTE: these are the entity delimiters we inserted.
entity_pattern = r'(\ue000.*?\ue001|\ue010.*?\ue011|\ue020.*?\ue021|\ue030.*?\ue031|\ue040.*?\ue041)'
entity_with_whitespace_pattern = re.compile(r'\s*' + entity_pattern + r'\s*')

# NOTE: it's anoying to do this in post, as it doubles the computation time, but at least the original data is isomorphic
def wrap_inlined_entities_with_whitespace(stuff):
  return entity_with_whitespace_pattern.sub(lambda m: ' ' + m.group(1) + ' ', stuff)

if tokenizer.token_match != None:
    raise Exception("We were expecting the tokenizer to have no default token_match!")
tokenizer.token_match = re.compile(entity_pattern).match

# NOTE: we remove the URL matcher because have already delimited them as entities
tokenizer.url_match = None

# We also need this because people use punctuation pretty liberally.
custom_infixes = Italian.Defaults.infixes + [r"[?!;:,\.\"\(\)\[\]{}]+"]
tokenizer.infix_finditer = spacy.util.compile_infix_regex(custom_infixes).finditer



###


is_botched_user_mention = re.compile("^@[A-Za-z0-9_]+$").match
is_entity_hashtag = re.compile(r"^\ue000").match
is_entity_other = re.compile(r"^(\ue010|\ue020|\ue030|\ue040)").match

def is_wform(tok):
    return not (
        tok.is_space
        or tok.is_punct
        or tok.is_digit
        or is_botched_user_mention(tok.text)
        or is_entity_other(tok.text)
    )

def tokenize_and_filter_wforms(text):
    return [
        tok.text[1:-1] if is_entity_hashtag(tok.text) else tok.text
        for tok in tokenizer(wrap_inlined_entities_with_whitespace(text))
        if is_wform(tok)
    ]

