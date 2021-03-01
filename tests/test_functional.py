import pytest


def test_home(app):
    app.get_html('/', status=200)
    with pytest.raises(Exception):
        app.get_html('/notfound', status=302)
    app.get_dt('/functions', status=200)
    app.get_dt('/constructions', status=200)
    app.get_dt('/morphemes', status=200)
    app.get_dt('/unitvalues', status=200)
