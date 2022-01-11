import pytest
from invana_py.ogm.exceptions import FieldValidationError
from invana_py.ogm.fields import StringProperty, IntegerProperty, DateTimeProperty
from invana_py.ogm.models import VertexModel
from datetime import datetime, timedelta
from invana_py import InvanaGraph

gremlin_url = "ws://megamind-ws:8182/gremlin"
graph = InvanaGraph(gremlin_url)

DEFAULT_USERNAME = "rrmerugu"


class Person(VertexModel):
    graph = graph

    properties = {
        'first_name': StringProperty(min_length=3, max_length=30, trim_whitespaces=True),
        'created_at': DateTimeProperty(default=lambda: datetime.now(),
                                       max_value=(datetime.now() + timedelta(days=30)),
                                       min_value=(datetime.now() - timedelta(days=30))
                                       )

    }


class TestDateTimeField:

    def test_field(self):
        graph.g.V().drop()
        d = (datetime.now() - timedelta(days=3)).replace(microsecond=0)
        project = Person.objects.create(first_name="Ravi Raja", created_at=d)
        assert isinstance(project.properties.created_at, datetime)
        assert project.properties.created_at == d

    def test_field_max_value(self):
        graph.g.V().drop()
        with pytest.raises(FieldValidationError) as exec_info:
            Person.objects.create(first_name="Ravi Raja", created_at=(datetime.now() + timedelta(days=50)))
        assert "max_value for field" in exec_info.value.__str__()

    def test_field_min_value(self):
        graph.g.V().drop()
        with pytest.raises(FieldValidationError) as exec_info:
            Person.objects.create(first_name="Ravi Raja", created_at=(datetime.now() - timedelta(days=80)))
        assert "min_value for field " in exec_info.value.__str__()

    def test_field_default(self):
        graph.g.V().drop()
        project = Person.objects.create(first_name="Ravi Raja")
        assert isinstance(project.properties.created_at, datetime)
