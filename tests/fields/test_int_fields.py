import pytest
from invana.ogm.exceptions import FieldValidationError
from invana.ogm.properties import StringProperty, IntegerProperty, DateTimeProperty
from invana.ogm.models import NodeModel
from datetime import datetime
from invana import settings, graph
import os

settings.GREMLIN_URL = os.environ.get("GREMLIN_SERVER_URL", "ws://megamind-ws:8182/gremlin")

DEFAULT_USERNAME = "rrmerugu"
DEFAULT_POINTS_VALUE = 5


class Person(NodeModel):
    first_name = StringProperty(min_length=3, max_length=30, trim_whitespaces=True)
    last_name = StringProperty(allow_null=True)
    username = StringProperty(default=DEFAULT_USERNAME)
    member_since = IntegerProperty()
    points = IntegerProperty(default=DEFAULT_POINTS_VALUE, max_value=100, min_value=5)
    created_at = DateTimeProperty(default=lambda: datetime.now())


class TestIntegerField:

    def test_field(self):
        graph.g.V().drop()
        project = Person.objects.create(first_name="Ravi Raja", member_since=2022)
        assert isinstance(project.properties.member_since, int)

    def test_field_max_value(self):
        graph.g.V().drop()
        with pytest.raises(FieldValidationError) as exec_info:
            Person.objects.create(first_name="Ravi Raja", points=200, member_since=2022)
        assert "max_value for field" in exec_info.value.__str__()

    def test_field_min_value(self):
        graph.g.V().drop()
        with pytest.raises(FieldValidationError) as exec_info:
            Person.objects.create(first_name="Ravi Raja", points=0, member_since=2022)
        assert "min_value for field " in exec_info.value.__str__()

    def test_string_field_default(self):
        graph.g.V().drop()
        person = Person.objects.create(first_name="Ravi", member_since=2022)
        assert person.properties.points == DEFAULT_POINTS_VALUE
