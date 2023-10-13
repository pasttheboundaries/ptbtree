import unittest
from typing import Callable
from actree.models.actionargs import CallableArg, PropertyArg
from actree.models.action import Action


class TestCallableArg(unittest.TestCase):
    def test_call(self):
        # Define a callable function
        def add(a, b):
            return a + b

        # Create a CallableArg instance
        arg = CallableArg(add, 2, 3)

        # Call the CallableArg
        result = arg()

        # Verify the result
        self.assertEqual(result, 5)

    def test_call_with_args(self):
        # Define a callable function
        def multiply(a, b):
            return a * b

        # Create a CallableArg instance with arguments
        arg = CallableArg(multiply, 2,  b=3)

        # Call the CallableArg
        result = arg()

        # Verify the result
        self.assertEqual(result, 6)


class TestPropertyArg(unittest.TestCase):
    def test_get(self):
        # Define a class with a property
        class Person:
            def __init__(self, name):
                self._name = name

            @property
            def name(self):
                return self._name

        # Create a Person instance
        person = Person("Alice")

        # Create a PropertyArg instance
        arg = PropertyArg(person, "name")

        # Get the property value
        result = arg()

        # Verify the result
        self.assertEqual(result, "Alice")


class TestAction(unittest.TestCase):
    def test_execute(self):
        # Define a test function
        def add(a, b):
            return a + b

        # Create an Action instance
        action = Action(add, 2, 3)

        # Execute the action
        result = action()

        # Verify the result
        self.assertEqual(result, 5)

    def test_execute_with_args(self):
        # Define a test function
        def multiply(a, b):
            return a * b

        # Create an Action instance with arguments
        action = Action(multiply, 4, b=5)

        # Execute the action
        result = action()

        # Verify the result
        self.assertEqual(result, 20)

    def test_execute_with_CallableArgs(self):
        # Define a test function
        def add(a, b):
            return a + b

        # Create a CallableArg instance
        callable_arg = CallableArg(add, 2, 3)

        # Create an Action instance with the CallableArg
        action = Action(callable_arg)

        # Execute the action
        result = action()

        # Verify the result
        self.assertEqual(result, 5)

    def test_execute_with_PropertyArgs(self):
        # Create a test object with a property
        class TestObject:
            def __init__(self):
                self.value = 10

            @property
            def double(self):
                return self.value * 2

        # Create a PropertyArg instance
        property_arg = PropertyArg(TestObject, 'double')

        # Create an Action instance with the PropertyArg
        action = Action(property_arg)

        # Execute the action
        result = action()

        # Verify the result
        self.assertEqual(result, 20)


if __name__ == "__main__":
    unittest.main()