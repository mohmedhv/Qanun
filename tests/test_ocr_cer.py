from eval.ocr_cer import evaluate, normalize_whitespace


def test_cer_and_wer_with_whitespace_normalization():
    assert normalize_whitespace("chat\n  noir") == "chat noir"
    character_counts, cer, word_counts, wer, reference_chars, reference_words = evaluate(
        "chat noir", "chat soir"
    )
    assert (character_counts.substitutions, character_counts.deletions, character_counts.insertions) == (1, 0, 0)
    assert cer == 1 / len("chat noir")
    assert (word_counts.substitutions, word_counts.deletions, word_counts.insertions) == (1, 0, 0)
    assert wer == 1 / 2
    assert reference_chars == len("chat noir")
    assert reference_words == 2
