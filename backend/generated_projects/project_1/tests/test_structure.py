def test_application_packages_are_importable():
    import app.api
    import app.models
    import app.services

    assert app.api is not None
    assert app.models is not None
    assert app.services is not None
