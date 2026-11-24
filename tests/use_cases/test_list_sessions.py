from use_cases.list_sessions import ListSessions


def test_lists_only_own_sessions_most_recent_first(open_session, sessions):
    open_session.execute(1, "Antiga")
    open_session.execute(2, "De outro usuário")
    open_session.execute(1, "Recente")

    result = ListSessions(sessions).execute(1)

    assert [s.folder_name for s in result] == ["Recente", "Antiga"]


def test_returns_empty_list_for_new_user(sessions):
    assert ListSessions(sessions).execute(99) == []
