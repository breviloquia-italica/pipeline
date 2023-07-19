# Define helpers to extract and embed entity delimiters as special characters.

# NOTE: U+E000..U+F8FF is Private Use Area of the Basic Multilingual Plane
ENTITY_DELIMITERS_BY_KEY = {
  "hashtags":      ("\uE000", "\uE001"),
  "symbols":       ("\uE011", "\uE011"),
  "user_mentions": ("\uE020", "\uE021"),
  "urls":          ("\uE030", "\uE031"),
  "media":         ("\uE040", "\uE041"),
}

ENTITY_DELIMITERS_BY_IDX = list(ENTITY_DELIMITERS_BY_KEY.values())

def extract_entity_ranges(entities):
  # NOTE: we use a set because we expect duplicates from media entities
  entity_ranges = set()
  for idx, entity_name in enumerate(ENTITY_DELIMITERS_BY_KEY):
    for entity in entities.get(entity_name, []):
      # NOTE: using tuples because 1) more proper 2) they're hashable, so they can live in a set
      entity_ranges.add((*entity['indices'], idx))
  # NOTE: we sort now to simplify future processing
  return sorted(list(entity_ranges), key=lambda l: l[0], reverse=True)

def embed_entity_annotations(row):
  entity_ranges = extract_entity_ranges(row["entities"])
  text = row["full_text"]
  for beg_idx, end_idx, idx in entity_ranges:
    text = text[:beg_idx] + ENTITY_DELIMITERS_BY_IDX[idx][0] + text[beg_idx:end_idx] + ENTITY_DELIMITERS_BY_IDX[idx][1] + text[end_idx:]
  return text