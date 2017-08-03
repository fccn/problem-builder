import unittest

from mock import MagicMock, Mock
from xblock.core import XBlock
from xblock.field_data import DictFieldData
from xblock.fields import String, Scope, Boolean, Integer

from problem_builder.mixins import StudentViewUserStateMixin


class NoUserStateFieldsMixin(object):
    scope_settings = String(name="Field1", scope=Scope.settings)
    scope_content = String(name="Field1", scope=Scope.content)
    user_state_summary = String(name="Not in the output", scope=Scope.user_state_summary)


class UserStateFieldsMixin(object):
    answer_1 = String(name="state1", scope=Scope.user_state)
    answer_2 = Boolean(name="state2", scope=Scope.user_state)

    preference_1 = String(name="pref1", scope=Scope.preferences)
    preference_2 = Integer(name="pref2", scope=Scope.preferences)

    user_info_1 = String(name="info1", scope=Scope.user_info)
    user_info_2 = Integer(name="info2", scope=Scope.user_info)


class ChildrenMixin(object):
    # overriding children for ease of testing
    _children = []
    has_children = True

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, value):
        self._children = value


class XBlockWithNoUserState(XBlock, NoUserStateFieldsMixin, StudentViewUserStateMixin):
    pass


class XBlockNoChildrenWithUserState(XBlock, NoUserStateFieldsMixin, UserStateFieldsMixin, StudentViewUserStateMixin):
    pass


class XBlockChildrenNoUserState(XBlock, NoUserStateFieldsMixin, ChildrenMixin, StudentViewUserStateMixin):
    has_children = True


class XBlockChildrenUserState(
    XBlock, NoUserStateFieldsMixin, UserStateFieldsMixin, ChildrenMixin, StudentViewUserStateMixin
):
    has_children = True


class TestStudentViewUserStateMixin(unittest.TestCase):
    def setUp(self):
        self._runtime = MagicMock()

    def _build_block(self, block_type, fields):
        return block_type(self._runtime, DictFieldData(fields), Mock())

    def _set_children(self, block, children):
        block.children = children.keys()
        self._runtime.get_block.side_effect = children.get

    def _merge_dicts(self, dict1, dict2):
        result = dict1.copy()
        result.update(dict2)
        return result

    def test_no_user_state_returns_empty(self):
        block = self._build_block(XBlockWithNoUserState, {"scope_settings": "qwe", "scope_content": "ASD"})

        self.assertEqual(block.student_user_view_user_state(), {})

    def test_no_child_blocks_with_user_state(self):
        user_fields = {
            "answer_1": "AAAA",
            "answer_2": False,
            "preference_1": "Yes",
            "preference_2": 12,
            "user_info_1": "John",
            "user_info_2": 27
        }
        other_fields = {"setting": "setting", "content": "content", "user_state_summary": "Something"}
        block_fields = self._merge_dicts(user_fields, other_fields)
        block = self._build_block(XBlockNoChildrenWithUserState, block_fields)

        self.assertEqual(block.student_user_view_user_state(), user_fields)

    def test_children_empty_no_user_state(self):
        block = self._build_block(XBlockChildrenNoUserState, {"scope_settings": "qwe", "scope_content": "ASD"})
        self.assertEqual(block.children, [])  # precondition

        self.assertEqual(block.student_user_view_user_state(), {"components": []})

    def test_children_no_user_state(self):
        block = self._build_block(XBlockChildrenNoUserState, {"scope_settings": "qwe", "scope_content": "ASD"})
        no_user_state1 = self._build_block(XBlockWithNoUserState, {"scope_settings": "qwe", "scope_content": "ASD"})
        no_user_state2 = self._build_block(XBlockWithNoUserState, {"scope_settings": "ZXC", "scope_content": "VBN"})
        nested = {"child1": no_user_state1, "child2": no_user_state2}
        self._set_children(block, nested)

        # preconditions
        self.assertEqual(block.children, nested.keys())
        self.assertEqual(self._runtime.get_block("child1"), no_user_state1)
        self.assertEqual(self._runtime.get_block("child2"), no_user_state2)

        student_user_state = block.student_user_view_user_state()

        expected = {"components": [{}, {}]}
        self.assertEqual(student_user_state, expected)

    def test_children_with_user_state(self):
        block = self._build_block(XBlockChildrenNoUserState, {"scope_settings": "qwe", "scope_content": "ASD"})

        other_fields = {"setting": "setting", "content": "content", "user_state_summary": "Something"}
        user_fields1 = {
            "answer_1": "AAAA",
            "answer_2": False,
            "preference_1": "Yes",
            "preference_2": 12,
            "user_info_1": "John",
            "user_info_2": 27
        }
        user_fields2 = {
            "answer_1": "BBBB",
            "answer_2": True,
            "preference_1": "No",
            "preference_2": 7,
            "user_info_1": "jane",
            "user_info_2": 19
        }
        user_state1 = self._build_block(XBlockNoChildrenWithUserState, self._merge_dicts(user_fields1, other_fields))
        user_state2 = self._build_block(XBlockNoChildrenWithUserState, self._merge_dicts(user_fields2, other_fields))
        nested = {"child1": user_state1, "child2": user_state2}
        self._set_children(block, nested)

        # preconditions
        self.assertEqual(block.children, nested.keys())
        self.assertEqual(self._runtime.get_block("child1"), user_state1)
        self.assertEqual(self._runtime.get_block("child2"), user_state2)

        student_user_state = block.student_user_view_user_state()

        expected = {"components": [user_fields1, user_fields2]}
        self.assertEqual(student_user_state, expected)

    def test_user_state_at_parent_and_children(self):
        other_fields = {"setting": "setting", "content": "content", "user_state_summary": "Something"}
        user_fields = {
            "answer_1": "OOOO",
            "answer_2": True,
            "preference_1": "IDN",
            "preference_2": 42,
            "user_info_1": "Douglas",
            "user_info_2": 9
        }
        block = self._build_block(XBlockChildrenUserState, self._merge_dicts(user_fields, other_fields))

        nested_user_fields = {
            "answer_1": "AAAA",
            "answer_2": False,
            "preference_1": "Yes",
            "preference_2": 12,
            "user_info_1": "John",
            "user_info_2": 27
        }
        user_state = self._build_block(
            XBlockNoChildrenWithUserState, self._merge_dicts(nested_user_fields, other_fields)
        )
        nested = {"child1": user_state}
        self._set_children(block, nested)

        # preconditions
        self.assertEqual(block.children, nested.keys())
        self.assertEqual(self._runtime.get_block("child1"), user_state)

        student_user_state = block.student_user_view_user_state()

        expected = user_fields.copy()
        expected["components"] = [nested_user_fields]
        self.assertEqual(student_user_state, expected)
