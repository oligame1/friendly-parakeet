from friendly_parakeet.pdf_reader import Page, group_pages_by_project


def test_group_pages_by_project_detects_multiple_projects():
    pages = [
        Page(number=1, text="Projet : Résidence A\nSection 25 - plomberie"),
        Page(number=2, text="Détails section 25"),
        Page(number=3, text="Projet : Résidence B\nSection 25"),
    ]

    grouped = group_pages_by_project(pages)

    assert list(grouped) == ["Général", "Résidence A", "Résidence B"]
    assert [page.number for page in grouped["Résidence A"]] == [1, 2]
    assert [page.number for page in grouped["Résidence B"]] == [3]
