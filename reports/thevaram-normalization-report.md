# Thevaram Normalization Report

## Summary

- Normalization version: `thevaram-normalized-v1`
- Input root: `data/processed/thevaram`
- Output root: `data/processed/thevaram_normalized`
- Raw and parsed source tables were not modified.

## Counts

| Table | Rows |
| --- | ---: |
| `thirumurai_books` | 8 |
| `paadal_thogupugal` | 841 |
| `paadalgal` | 9012 |
| `commentaries` | 9012 |
| `text_spans` | 64073 |

## Preserved Line Structure

Existing `\n` line boundaries are intentionally preserved because they identify poem and commentary line breaks. Normalization only canonicalizes Unicode, removes unsafe invisible/control characters, collapses repeated spaces inside each line, trims line edges, and recomputes span offsets against the normalized text.

| Field group | Before `\n` count | After `\n` count |
| --- | ---: | ---: |
| `paadal_text` | 39766 | 39766 |
| `commentary_text` | 0 | 0 |

## Changed Fields

- `thirumurai_books`: none
- `paadal_thogupugal`: none
- `paadalgal`: `local_song_no`=2, `paadal_text`=3, `tokenized_paadal`=3
- `commentaries`: `kurippurai`=8
- `text_spans`: `rebuilt_from_normalized_text`=64073
