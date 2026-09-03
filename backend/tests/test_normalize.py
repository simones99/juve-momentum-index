from app.core.constants import TEAM_NAME
from app.ingestion.normalize import canonicalize_team_name


def test_juventus_aliases_collapse_to_team_name():
    assert canonicalize_team_name("Juventus") == TEAM_NAME
    assert canonicalize_team_name("juventus fc") == TEAM_NAME
    assert canonicalize_team_name("Juve") == TEAM_NAME


def test_punctuation_variants_of_the_same_club_collapse():
    # Same real Wikipedia team-name variants seen across different seasons' articles.
    assert canonicalize_team_name("A.C. Milan") == canonicalize_team_name("AC Milan")
    assert canonicalize_team_name("Atalanta B.C.") == canonicalize_team_name("Atalanta BC")
    assert canonicalize_team_name("S.S.C. Napoli") == canonicalize_team_name("SSC Napoli")
    assert canonicalize_team_name("U.S. Sassuolo Calcio") == canonicalize_team_name("US Sassuolo Calcio")


def test_non_juventus_names_pass_through_unchanged_aside_from_punctuation():
    assert canonicalize_team_name("AC Milan") == "AC Milan"
    assert canonicalize_team_name("Cagliari Calcio") == "Cagliari Calcio"
