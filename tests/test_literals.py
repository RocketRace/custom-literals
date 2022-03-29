from custom_literals import *

import unittest

class TestLiteral(unittest.TestCase):
    def run_multiple_hooks(self, number):
        import itertools
        for combination in itertools.combinations(ALLOWED_TARGETS, number):

            def foo(self):
                return "correct"

            literal(*combination)(foo)
            try:
                for target in combination:
                    self.assert_(hasattr(target, "foo"), f"target hook failed for {target}")
                
                target_type = lambda target: target if isinstance(target, type) else type(target)
                combination_types = tuple(map(target_type, combination))
                for other in set(ALLOWED_TARGETS) - set(combination):
                    if not issubclass(target_type(other), combination_types):
                        self.assert_(not hasattr(other, "foo"), f"types {other} affected by hooks on {combination}")
            # otherwise the other tests are affected
            # (because builtins are shared)
            finally:
                for target in combination:
                    unliteral(target, "foo")

            for other in ALLOWED_TARGETS:
                if other in combination:
                    self.assert_(not hasattr(other, "foo"), f"unhooking target {other} failed")
                else:
                    self.assert_(not hasattr(other, "foo"), f"unhooking {combination} affected type {other}")
                
    def test_single_literal_hook(self):
        self.run_multiple_hooks(1)

    def test_many_literal_hooks(self):
        for n in range(2, len(ALLOWED_TARGETS)):
            self.run_multiple_hooks(n)
    
    def test_str(self):
        @literal(str)
        def foo_str(self):
            return "correct"
        
        try:
            self.assertEqual("aa".foo_str, "correct", "str hook failed")
        finally:
            unliteral(str, "foo_str")

        with self.assertRaises(AttributeError, msg="str unhook failed"):
            "aa".foo_str
    
    def test_none(self):
        @literal(None)
        def foo_none(self):
            return "correct"
        try:
            self.assertEqual(None.foo_none, "correct", "none hook failed")

        finally:
            unliteral(None, "foo_none")
        with self.assertRaises(AttributeError, msg="none unhook failed"):
            None.foo_none

    def test_int_bool(self):
        @literal(int)
        def foo_int(self):
            return "correct"
        
        try:
            self.assertEqual((1).foo_int, "correct", "int hook failed")
            with self.assertRaises(AttributeError, msg="int hook affects bool"):
                True.foo_int
            
        finally:
            unliteral(int, "foo_int")

        @literal(int, bool)
        def foo_int_bool(self):
            return "true"
        
        self.assertEqual((1).foo_int_bool, "true", "int rehook failed")
        self.assertEqual(False.foo_int_bool, "true", "int+bool hook failed")
        unliteral(int, "foo_int_bool")
        unliteral(bool, "foo_int_bool")

        with self.assertRaises(AttributeError, msg="int unhook failed"):
            (0).foo_int_bool
        
        with self.assertRaises(AttributeError, msg="bool unhook failed"):
            False.foo_int_bool

    def test_float(self):
        @literal(float)
        def foo_float(self):
            return "correct"
        
        try:
            self.assertEqual((1.0).foo_float, "correct", "float hook failed")
        finally:
            unliteral(float, "foo_float")

        with self.assertRaises(AttributeError, msg="float unhook failed"):
            (0.0).foo_float
    
    def test_complex(self):
        @literal(complex)
        def foo_complex(self):
            return "correct"
        
        try:
            self.assertEqual((1j).foo_complex, "correct", "complex hook failed")
        finally:
            unliteral(complex, "foo_complex")

        with self.assertRaises(AttributeError, msg="complex unhook failed"):
            (0j).foo_complex
    
    def test_literally(self):
        from datetime import datetime
        try:
            with literally(int, name="unix", fn=datetime.fromtimestamp):
                self.assertEqual((1647804818).unix, datetime(2022, 3, 20, 21, 33, 38), "context manager hook failed")
        
            with self.assertRaises(AttributeError, msg="context manager unhook failed"):
                (0).unix
        
        finally:
            try:
                unliteral(int, "unix")
            except AttributeError:
                pass # Already unhooked


    def test_class_based(self):
        try:
            @literals(str)
            class Foo:
                def bar(self):
                    return "correct"

            self.assertEqual("aa".bar, "correct", "class based hook failed")
            
        finally:
            unliteral(str, "bar")

        with self.assertRaises(AttributeError, msg="class based unhook failed"):
            "aa".bar
        
    def test_renamed_class_literal(self):
        try:
            @literals(str)
            class Foo:
                @rename("bar")
                def bees(self):
                    return "correct"
            
            self.assertEqual("aa".bar, "correct", "renamed class based hook failed")

        finally:
            unliteral(str, "bar")

        with self.assertRaises(AttributeError, msg="renamed class based unhook failed"):
            "aa".bar

    def test_class_multiple_targets(self):
        try:
            @literals(str, int)
            class Foo:
                def bar(self):
                    return "correct"

            self.assertEqual("aa".bar, "correct", "class based hook failed")
            self.assertEqual((1).bar, "correct", "class based hook failed")
            
        finally:
            unliteral(str, "bar")
            unliteral(int, "bar")

        with self.assertRaises(AttributeError, msg="class based unhook failed"):
            "aa".bar
        with self.assertRaises(AttributeError, msg="class based unhook failed"):
            (1).bar

    def test_class_multiple_literals(self):
        try:
            @literals(str)
            class CaseLiterals:
                @rename("u")
                def uppercase(self):
                    return self.upper()
                @rename("l")
                def lowercase(self):
                    return self.lower()
            
            self.assertEqual("aa".u, "AA", "class based hook failed")
            self.assertEqual("AA".l, "aa", "class based hook failed")

        finally:
            unliteral(str, "u")
            unliteral(str, "l")
