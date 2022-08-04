#    Copyright 2021 Invana
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#     http:www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import pytest

from invana.ogm.exceptions import FieldValidationError
from invana.ogm.properties import StringProperty, SingleCharProperty
from invana.ogm.models import NodeModel
from invana.connector.data_types import SingleCharType
from invana.serializer.element_structure import Node
from invana import settings, graph
import os

settings.GREMLIN_URL = os.environ.get("GREMLIN_SERVER_URL", "ws://megamind-ws:8182/gremlin")


DEFAULT_USERNAME = "rrmerugu"


class Person(NodeModel):
    first_name = StringProperty(min_length=3, max_length=30, trim_whitespaces=True)
    gender = SingleCharProperty(allow_null=True, default="m")



class TestStringField:

    def test_field(self):
        graph.g.V().drop()
        project = Person.objects.create(first_name="Ravi Raja", gender='m')
        assert isinstance(project.properties.gender, SingleCharType)

    def test_field_validation(self):
        graph.g.V().drop()
        with pytest.raises(FieldValidationError):
            Person.objects.create(first_name="Ravi Raja", gender='m12')

    def test_field_allow_null(self):
        graph.g.V().drop()
        person = Person.objects.create(first_name="Ravi Raja")
        assert isinstance(person, Node)

    def test_field_default(self):
        graph.g.V().drop()
        person = Person.objects.create(first_name="Ravi Raja")
        assert person.properties.gender == "m"
